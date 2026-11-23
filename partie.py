"""Moteur de partie : joueurs, déroulement des manches, règles et points.
Tout passe par un verrou ; une boucle (thread) fait avancer le temps toutes les 0,1 s."""
import copy
import json
import math
import random
import secrets
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import profils as profils_mod
from affiches.preparation import PREPARATEUR
import sagas
from config import COULEURS, JEUX, avatars
from jeux import CONSTRUCTEURS, MOTEURS
from jeux.complicite import Complicite
from texte import cle, correspond, est_latin, proche, suggerer
import historique
import palmares
import recompenses
from tmdb import POOL, TMDB, charger_pools, cle_film, entrees_pool

BAREME = [1000, 750, 550, 400, 300, 200, 150, 100]   # points selon le rang d'arrivée
SERIE_MAX = 4
MAIN_MAX = 15                                         # secondes pour répondre après le buzzer


class Joueur:
    def __init__(self, pid, nom, couleur, avatar=""):
        self.pid, self.id = pid, secrets.token_hex(3)    # pid secret (téléphone), id public
        self.nom, self.couleur, self.avatar = nom, couleur, avatar
        self.profil = ""                                 # nom du profil relié
        self.profil_choix = None                         # profil choisi sur le téléphone (None : celui du pseudo)
        self.score = self.serie = 0
        self.reset()

    def reset(self):
        self.essais, self.trouve, self.gain, self.bonus = 0, False, 0, 0
        self.bloque, self.reponse, self.frac = 0.0, None, 0.0

    def public(self):
        return {"id": self.id, "nom": self.nom, "couleur": self.couleur, "avatar": self.avatar, "score": self.score,
                "gain": self.gain, "bonus": self.bonus, "serie": self.serie, "trouve": self.trouve,
                "profil": self.profil}


def images_de(etat):
    """Numéros d'images présents dans une étape (pour ne servir que les images dévoilées)."""
    ids = {etat["img"]} if "img" in etat else set()
    for liste in ("cartes", "films", "items", "paire"):
        ids.update(c["img"] for c in etat.get(liste, []) if isinstance(c, dict) and c.get("img") is not None)
    for cle_ in ("tiers", "film"):
        if isinstance(etat.get(cle_), dict) and etat[cle_].get("img") is not None:
            ids.add(etat[cle_]["img"])
    ids.update(etat.get("plans", []))
    if etat.get("pochette") is not None:                       # James : la pochette floue
        ids.add(etat["pochette"])
    for du in etat.get("duels", []):                           # Leo : les deux films de chaque duel
        ids.update(x["img"] for x in (du.get("a"), du.get("b")) if x)
    for c in etat.get("complices", []):                        # Phillip : le portrait, la petite affiche du film
        ids.update(x for x in (c.get("img"), c.get("img_f")) if x is not None)
    ids.update(etat.get("petales", []))                        # Harold : les pétales de l'orchidée
    ids.update(etat.get("sequence", []))                       # Sarah : les affiches de la vision
    ids.update(etat.get("cachees", []))                        # images propres à chaque joueur (Hank, Mitchum…)
    ids.update(etat.get("photos", []))                         # Jean Renault : les photos de l'otage
    for b in etat.get("bandes", []):                           # Dougie : les affiches de chaque rouleau
        ids.update(b)
    return ids


class Partie:
    def __init__(self):
        self.lock = threading.RLock()
        self.joueurs = {}
        self.cfg, self.api = {}, None
        self.phase, self.pause = "lobby", False
        self.message = self.erreur = self.info = ""
        self.pools, self.entrees, self.noms, self.deja = {}, {}, {}, {}
        self.signatures = set()                             # manches déjà construites (jamais deux fois la même)
        self.recap, self.series_max, self.joues = [], {}, set()   # récap de fin de partie ; films joués (historique)
        self.plan, self.index, self.tour, self.seq = [], 0, 0, 0
        self.fabrique = ThreadPoolExecutor(max_workers=2)   # construit les manches à l'avance (deux d'avance)
        self.futurs, self.attente = {}, None
        self.profils_partie = []
        self.utilises = {}                                  # pid -> films déjà donnés (Chrono, Bingo)
        self._entrees_saga = {}
        self._vider_manche()
        threading.Thread(target=self._boucle, daemon=True).start()

    def _vider_manche(self):
        self.manche, self.etape, self.publies = None, -1, set()
        self.ecoule, self.duree, self.reste_reponse, self.duree_reponse = 0.0, 1.0, 0.0, 1.0
        self.ordre, self.main, self.main_depuis = [], None, 0.0
        self.qcm, self.qcm_bonne, self.complice, self.moteur = [], -1, None, None

    # ============ joueurs ============
    def _nom_libre(self, nom, sauf=None):
        base = " ".join(str(nom or "").split())[:16] or "Joueur"
        nom, n = base, 2
        while any(j.nom.lower() == nom.lower() and j.pid != sauf for j in self.joueurs.values()):
            nom, n = f"{base[:13]} {n}", n + 1
        return nom

    def _couleur_prise(self, c, sauf=None):
        return any(j.couleur == c and j.pid != sauf for j in self.joueurs.values())

    def _avatar_pris(self, a, sauf=None):
        return any(j.avatar == a and j.pid != sauf for j in self.joueurs.values())

    def _relier_profil(self, j):
        """Le joueur est relié au profil choisi sur son téléphone, sinon à celui qui porte son pseudo
        (s'il n'est pas déjà pris par un autre joueur)."""
        if j.profil_choix is not None:
            p = profils_mod.trouver(j.profil_choix) if j.profil_choix else None
        else:
            p = profils_mod.trouver(j.nom)
        pris = any(o.profil == (p or {}).get("nom") and o is not j for o in self.joueurs.values())
        j.profil = p["nom"] if p and not pris else ""
        if p and not pris and not j.avatar and p.get("avatar") and p["avatar"] in avatars() \
                and not self._avatar_pris(p["avatar"], j.pid):
            j.avatar = p["avatar"]

    def couleurs(self):
        with self.lock:
            profils = profils_mod.charger()
            return {"couleurs": COULEURS, "prises": [j.couleur for j in self.joueurs.values()],
                    "avatars": avatars(), "avatars_pris": [j.avatar for j in self.joueurs.values() if j.avatar],
                    "profils": [{"nom": p["nom"], "avatar": p["avatar"]} for p in profils],
                    "profils_pris": [j.profil for j in self.joueurs.values() if j.profil]}

    def rejoindre(self, nom, couleur, avatar="", profil=None):
        with self.lock:
            if profil is not None:
                profil = str(profil).strip()[:16]
                nom = nom if str(nom or "").strip() else profil
            if couleur not in COULEURS or self._couleur_prise(couleur):
                libres = [c for c in COULEURS if not self._couleur_prise(c)]
                couleur = random.choice(libres or COULEURS)
            if avatar not in avatars() or self._avatar_pris(avatar):
                avatar = ""
            pid = secrets.token_hex(8)
            j = Joueur(pid, self._nom_libre(nom), couleur, avatar)
            j.profil_choix = profil
            self.joueurs[pid] = j
            self._relier_profil(j)
            return pid

    def profil(self, pid, nom=None, couleur=None, avatar=None, profil=None):
        with self.lock:
            j = self.joueurs.get(pid)
            if not j:
                return {"ok": False, "msg": "Joueur inconnu"}
            if couleur and couleur != j.couleur:
                if couleur not in COULEURS or self._couleur_prise(couleur, pid):
                    return {"ok": False, "msg": "Couleur déjà prise"}
                j.couleur = couleur
            if avatar is not None and avatar != j.avatar:
                if avatar and (avatar not in avatars() or self._avatar_pris(avatar, pid)):
                    return {"ok": False, "msg": "Photo déjà prise"}
                j.avatar = avatar
            if nom and nom.strip():
                j.nom = self._nom_libre(nom, pid)
            ancien = j.profil_choix
            if profil is not None:
                j.profil_choix = str(profil).strip()[:16]
            self._relier_profil(j)
            if profil and not j.profil:
                j.profil_choix = ancien
                self._relier_profil(j)
                return {"ok": False, "msg": f"Le profil {profil} est déjà pris par un autre joueur"}
            return {"ok": True, "msg": "Profil enregistré" + (f" · relié au profil {j.profil}" if j.profil else "")}

    def _retirer(self, pid):
        self.joueurs.pop(pid, None)
        if self.main == pid:
            self.main = None

    def quitter(self, pid):
        with self.lock:
            self._retirer(pid)
            return {"ok": True}

    def exclure(self, id_public):
        with self.lock:
            for pid, j in list(self.joueurs.items()):
                if j.id == id_public:
                    self._retirer(pid)

    def profils_presents(self):
        with self.lock:
            return [j.profil for j in self.joueurs.values() if j.profil]

    # ============ lancement ============
    def demarrer(self, reglages, listes_connues=()):
        """Retourne un message d'erreur, ou "" si la partie démarre."""
        with self.lock:
            if self.phase not in ("lobby", "fin"):
                return "Une partie est déjà en cours."
            cfg = copy.deepcopy(reglages)
            if not cfg["api_key"]:
                return "Entrez une clé API TMDB (Réglages › Général)."
            for j in self.joueurs.values():                # les profils ont pu changer depuis l'arrivée
                self._relier_profil(j)
            tous = {p["nom"]: p for p in profils_mod.charger()}
            presents = [profils_mod.pour_partie(tous[n], listes_connues)
                        for n in dict.fromkeys(j.profil for j in self.joueurs.values() if j.profil) if n in tous]
            jeux = [g for g, v in cfg["jeux"].items() if v["on"]]
            par_profils = cfg["profils_auto"] and any(p["listes"] or p["films"] for p in presents)
            for g in jeux:
                if JEUX[g]["listes"] and not cfg["listes"][g]["inc"] and not par_profils:
                    return f"Incluez au moins une liste TMDB pour « {JEUX[g]['nom']} » (bouton Listes)."
                besoin = JEUX[g].get("profils", 0)
                notes = [p for p in presents if p["notes"]]
                if len(notes) < besoin:
                    return (f"« {JEUX[g]['nom']} » se joue avec au moins {besoin} joueur{'s' if besoin > 1 else ''} "
                            f"qui ont un profil avec des notes (pseudo = nom du profil ; "
                            f"{len(notes)} pour l'instant). Importez leurs notes avec le bouton Profils.")
            if "complice" in jeux and len(self.joueurs) < 2:
                return "Complicité se joue à 2 joueurs minimum : scannez le QR code."
            if ("complice" in jeux and cfg["comp_mode"] == "fixe"
                    and cfg["comp_meneur"] not in [j.nom for j in self.joueurs.values()]):
                return "Mode « Meneur fixe » : choisissez un joueur connecté (Réglages › Complicité)."
            cfg["_profils"] = presents
            self.cfg, self.profils_partie = cfg, presents
            if cfg.get("hasard"):                    # jeux au hasard parmi ceux choisis : juste un nombre de manches
                self.plan = []
                for _ in range(int(cfg.get("hasard_n", 15))):
                    choix = [g for g in jeux if not self.plan or g != self.plan[-1]] or jeux
                    self.plan.append(random.choice(choix))
            else:
                self.plan = [g for g in jeux for _ in range(cfg["jeux"][g]["n"])]
                random.shuffle(self.plan)
            self.api = TMDB(cfg["api_key"], cfg["session_id"], cfg["account_id"])
            self.futurs, self.deja, self.info = {}, {}, ""
            self.recap, self.series_max, self.joues = [], {}, set()
            self.recap_sauve = False
            if cfg.get("anti_repetition", True):          # les films des dernières parties passent après les autres
                try:
                    self.deja["films"] = historique.recents(int(cfg.get("anti_repetition_n", 3)))
                except Exception:  # noqa: BLE001
                    traceback.print_exc()
            self.signatures = set()
            self.utilises, self._entrees_saga = {}, {}
            self.index = self.tour = 0
            self.pause, self.erreur = False, ""
            for j in self.joueurs.values():
                j.score = j.serie = 0
                j.reset()
            self._vider_manche()
            self.phase = "chargement"
            self.message = "Chargement des films vus par " + " et ".join(p["nom"] for p in presents) + "…" \
                if par_profils else "Chargement des listes TMDB…"
            self.attente = ("pools", self.fabrique.submit(charger_pools, self.api, cfg, set(jeux), presents))
            return ""

    def _deja(self, pool):
        """Films déjà joués : UN seul ensemble pour tous les jeux de films (un film tiré dans un jeu ne revient pas
        dans un autre), à part pour les acteurs (Filmographie)."""
        return self.deja.setdefault("acteurs" if pool == "acteurs" else "films", set())

    @staticmethod
    def _signature(m):
        """Ce qui rend une manche unique : son jeu et son contenu (films, conditions, solution)."""
        if m.get("signature"):
            return (m["jeu"], m["signature"])
        return (m["jeu"], m.get("solution", ""), tuple(sorted(str(f) for f in m.get("films", []))),
                json.dumps(m["etapes"][0][1], sort_keys=True, default=str)[:400] if m.get("etapes") else "")

    def _construire(self, jeu):
        """Construit une manche ; jamais deux fois la même manche dans une partie (même jeu et même contenu)."""
        pool, erreur, doublon = POOL[jeu], None, None
        for essai in range(8):
            try:
                deja = self._deja(pool)
                m = CONSTRUCTEURS[jeu](self.api, self.cfg, self.pools[pool], deja)
                m["jeu"], m["pool"] = jeu, m.get("pool") or pool     # Andy : une manche d'acteur → pool « acteurs »
                sig = self._signature(m)
                with self.lock:
                    deja_vue = sig in self.signatures
                    if not deja_vue or essai == 7:
                        self.signatures.add(sig)
                        for k in m.get("films", []):          # les films de la manche ne reviennent plus
                            deja.add(tuple(k) if isinstance(k, list) else k)
                if deja_vue and essai < 7:
                    doublon = sig
                    continue
                if m.get("saga_id"):
                    deja.add(("saga", m["saga_id"]))            # pas un autre film de cette saga ensuite
                try:                                             # l'indice « récompenses » (Wikidata)
                    recompenses.ajouter_indice(m, self.api, self.cfg)
                except Exception:  # noqa: BLE001
                    traceback.print_exc()
                return m
            except Exception as err:  # noqa: BLE001
                erreur = err
                traceback.print_exc()
                if essai >= 2:
                    break
        raise erreur or RuntimeError(f"manche en double ({doublon[0] if doublon else jeu})")

    def _prechauffer(self):
        """Jeux qui demandent un long travail (traductions de Catherine) : préparé en tâche de fond, pendant que l'on
        joue les autres manches, pour qu'il n'y ait jamais d'attente au lancement."""
        nb = self.plan.count("catherine")
        if nb and self.pools.get(POOL["catherine"]):
            from jeux.catherine import prechauffer
            prechauffer(self.pools[POOL["catherine"]], nb + 2)

    def _preparer(self, i):
        if i < len(self.plan) and i not in self.futurs:
            self.futurs[i] = self.fabrique.submit(self._construire, self.plan[i])

    def _ouvrir(self, i):
        """Lance la manche i dès qu'elle est prête (sinon écran « Préparation… »)."""
        if i >= len(self.plan):
            return self._terminer()
        self._preparer(i)
        self.phase = "chargement"
        self.message = "Préparation de la manche…" + (f"\n{self.info}" if self.info and i == 0 else "")
        self.attente = ("manche", self.futurs[i])
        self._tic_chargement()

    def _tic_chargement(self):
        if not self.attente or not self.attente[1].done():
            return
        quoi, fut = self.attente
        self.attente = None
        try:
            res = fut.result()
        except Exception as err:  # noqa: BLE001
            if quoi == "pools":
                self.phase, self.message, self.erreur = "lobby", "", str(err)
                return
            self.erreur = f"Manche ignorée : {err}"
            self.futurs.pop(self.index, None)
            self.index += 1
            return self._ouvrir(self.index)
        if quoi == "pools":
            self.pools, self.info = res
            self.entrees = {k: entrees_pool(p, k) for k, p in self.pools.items()}
            self.noms = {k: [e[0] for e in ent] for k, ent in self.entrees.items()}
            sagas.prechauffer(self.api, [f for k, p in self.pools.items() if k != "acteurs" for f in p])
            self._preparer(0)
            self._preparer(1)
            self._prechauffer()
            return self._ouvrir(0)
        self.futurs.pop(self.index, None)
        try:
            self._commencer(res)
        except Exception as err:  # noqa: BLE001
            traceback.print_exc()
            self._vider_manche()
            self._sauter(f"Manche ignorée : {err}")

    def _sauter(self, msg):
        self.erreur = msg
        self.index += 1
        return self._ouvrir(self.index)

    def _commencer(self, m):
        meneur = None
        if m["reponse"] == "complice":
            ids = list(self.joueurs)
            if len(ids) < 2:
                return self._sauter("Manche Complicité ignorée : il faut au moins 2 joueurs.")
            mode = self.cfg["comp_mode"]
            if mode == "fixe":
                meneur = next((p for p, j in self.joueurs.items() if j.nom == self.cfg["comp_meneur"]), ids[0])
            elif mode == "tour":
                meneur = ids[self.tour % len(ids)]
                self.tour += 1
        moteur = None
        if m["reponse"] in MOTEURS:
            moteur = MOTEURS[m["reponse"]](self, self.cfg, m)
            refus = moteur.ok()
            if refus:
                return self._sauter(f"Manche ignorée : {refus}")
        self._vider_manche()
        self.seq += 1
        self.manche, self.duree, self.moteur = m, m["duree"], moteur
        self.scores_debut = {pid: j.score for pid, j in self.joueurs.items()}
        self.series_debut = {pid: j.serie for pid, j in self.joueurs.items()}
        for j in self.joueurs.values():
            j.reset()
        if m["reponse"] == "titre" and self.cfg["reponse"] == "qcm":
            self.qcm, self.qcm_bonne = self._propositions(m)
        if m["reponse"] == "complice":
            self.complice = Complicite(self, self.cfg, self.cfg["comp_mode"], meneur, m)
        self.phase, self.message = "manche", ""
        self._maj_etape()
        self._preparer(self.index + 1)
        self._preparer(self.index + 2)

    def _sagas_actives(self, m):
        return bool(m.get("saga_ok")) and self.cfg.get("sagas", True)

    def _entrees(self, m):
        """Entrées de l'autocomplétion. Jeux où l'on devine un film : une seule entrée par saga (« Harry Potter »)."""
        pool = m["pool"]
        if not self._sagas_actives(m):
            return self.entrees.get(pool, [])
        cle_cache = sagas.taille()
        if self._entrees_saga.get(pool, (None,))[0] != cle_cache:
            out, vus = [], set()
            for f in self.pools.get(pool, []):
                s = sagas.nom(f)
                if s:
                    if ("s", cle(s)) not in vus:
                        vus.add(("s", cle(s)))
                        out.append((s, [(s, cle(s))]))
                    continue
                noms = [n for n in dict.fromkeys((f["title"], f.get("original_title"))) if n and est_latin(n)]
                if noms:
                    out.append((noms[0], [(n, cle(n)) for n in noms]))
            self._entrees_saga[pool] = (cle_cache, out)
        return self._entrees_saga[pool][1]

    def _propositions(self, m):
        vus, autres = {cle(m["bonne"]), *m["cles"]}, []
        noms = [e[0] for e in self._entrees(m)] if self._sagas_actives(m) else self.noms.get(m["pool"], [])
        for n in random.sample(noms, len(noms)):
            if cle(n) not in vus:
                vus.add(cle(n))
                autres.append(n)
            if len(autres) >= self.cfg["qcm_choix"] - 1:
                break
        tout = autres + [m["bonne"]]
        random.shuffle(tout)
        return tout, tout.index(m["bonne"])

    # ============ boucle ============
    def _boucle(self):
        avant = time.monotonic()
        while True:
            time.sleep(0.1)
            now = time.monotonic()
            dt, avant = now - avant, now
            with self.lock:
                try:
                    if self.phase == "chargement":
                        self._tic_chargement()
                    elif self.phase == "manche" and not self.pause:
                        self._tic_manche(dt)
                    elif self.phase == "reponse" and not self.pause:
                        self.reste_reponse -= dt
                        if self.reste_reponse <= 0:
                            self.index += 1
                            self._ouvrir(self.index)
                except Exception:  # noqa: BLE001
                    traceback.print_exc()

    def _tic_manche(self, dt):
        if self.main is not None:                      # chrono gelé pendant qu'un joueur a la main
            if time.monotonic() - self.main_depuis > MAIN_MAX:
                self._perdre_main(self.joueurs.get(self.main))
            return
        self.ecoule += dt
        c = self.complice
        if c and c.sous == "choix":
            if self.ecoule >= self.duree or c.choix_complets():
                if not c.lancer_devine():
                    return self._vers_reponse()
                self.ecoule, self.duree = 0.0, float(self.cfg["comp_dur_devine"])
            return
        self._maj_etape()
        if self.ecoule >= self.duree or self._tous_finis():
            self._vers_reponse()

    def _maj_etape(self):
        n = max(0, sum(1 for t, _ in self.manche["etapes"] if t <= self.ecoule + 1e-6) - 1)
        for k in range(self.etape + 1, n + 1):
            self.publies |= images_de(self.manche["etapes"][k][1])
        self.etape = max(self.etape, n)

    def _tous_finis(self):
        js = list(self.joueurs.values())
        if not js:
            return False
        m = self.manche
        if m["reponse"] == "complice":
            return self.complice.fini()
        if self.moteur:
            return self.moteur.fini()
        if m["reponse"] in ("nombre", "choix"):
            return all(j.essais for j in js)
        mode = self.cfg["reponse"]
        if mode == "buzzer":
            return bool(self.ordre)
        limite = 1 if mode == "qcm" else self.cfg["max_essais"]
        return all(j.trouve or j.essais >= limite for j in js)

    def _vers_reponse(self):
        m = self.manche
        base = float(self.cfg["reveal_secs"])
        duree = base
        if self.complice:
            self.complice.clore()
            duree = self.complice.duree_revelation(base)
        elif self.moteur:
            self.moteur.clore()
            if hasattr(self.moteur, "duree_revelation"):
                duree = self.moteur.duree_revelation(base)
            else:
                duree = base + 3
        elif m["reponse"] == "nombre":
            self._noter_annees()
        else:
            for j in self.joueurs.values():
                if not j.trouve:
                    j.serie = 0
            if m["reponse"] == "choix":
                duree = base + 2
        self._rattrapage()
        self._noter_recap(m)
        self.main = None
        self.phase = "reponse"
        self.reste_reponse = self.duree_reponse = duree
        if m.get("revelation"):
            self.publies.add("r")
        if m["reponse"] == "choix":
            self.publies |= set(range(len(m["images"])))

    def _noter_annees(self):
        cible, tol = self.manche["nombre"], self.cfg.get("annee_tolerance", 10)
        reps = [(j, abs(j.reponse - cible)) for j in self.joueurs.values() if j.reponse is not None]
        meilleur = min((e for _, e in reps), default=None)
        for j, e in reps:
            if e > tol:
                continue
            base = 1000 if e == 0 else int(600 * (1 - (e - 1) / tol))
            j.gain = base + int(self.cfg["bonus_vitesse"] * j.frac) + (200 if e == meilleur else 0)
            j.score += j.gain
            j.trouve = e == 0

    def _noter_recap(self, m):
        """Ce qu'il faut pour le récap de fin : les gains de chacun à chaque manche, les séries."""
        try:
            self.recap.append({"jeu": m["jeu"], "solution": m.get("solution", ""), "type": m.get("reponse"),
                               "detail": m.get("detail", ""),
                               "gains": {pid: j.gain for pid, j in self.joueurs.items()},
                               "trouves": [pid for pid, j in self.joueurs.items() if j.trouve]})
            for pid, j in self.joueurs.items():
                self.series_max[pid] = max(self.series_max.get(pid, 0), j.serie)
            for k in m.get("films", []):
                self.joues.add(tuple(k) if isinstance(k, list) else k)
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    def _sauver_historique(self, inachevee=False):
        if self.joues or self.recap:
            J = self.joueurs
            details = {"inachevee": inachevee,
                       "joueurs": sorted([{"nom": j.nom, "score": j.score, "couleur": j.couleur} for j in J.values()],
                                         key=lambda x: -x["score"]),
                       "manches": [{"jeu": JEUX[r["jeu"]]["nom"] if r["jeu"] in JEUX else r["jeu"], "solution": r["solution"],
                                    "detail": r.get("detail", ""),
                                    "gagnants": [J[p].nom for p in r["trouves"] if p in J]} for r in self.recap]}
            historique.ajouter(self.joues, details)
            self.joues = set()
            self.recap_sauve = True

    def recap_fin(self):
        """Le récap de fin : podium, et pour chacun son meilleur jeu, sa meilleure manche, sa plus longue série ;
        les films qui ont résisté à tout le monde."""
        J = self.joueurs
        par_joueur = []
        for pid, j in J.items():
            par_jeu = {}
            meilleure = None
            for r in self.recap:
                g = r["gains"].get(pid, 0)
                par_jeu[r["jeu"]] = par_jeu.get(r["jeu"], 0) + g
                if g > 0 and (meilleure is None or g > meilleure[0]):
                    meilleure = (g, r["jeu"])
            top = max(par_jeu.items(), key=lambda x: x[1], default=(None, 0))
            par_joueur.append(dict(j.public(), par_jeu={k: v for k, v in par_jeu.items() if v > 0}, meilleur_jeu=JEUX[top[0]]["nom"] if top[0] and top[1] > 0 else "",
                                   meilleur_jeu_pts=top[1] if top[0] else 0,
                                   meilleure_manche=meilleure[0] if meilleure else 0,
                                   meilleure_manche_jeu=JEUX[meilleure[1]]["nom"] if meilleure else "",
                                   serie=self.series_max.get(pid, 0),
                                   trouves=sum(1 for r in self.recap if pid in r["trouves"])))
        par_joueur.sort(key=lambda x: -x["score"])
        rates = [r["solution"] for r in self.recap if r["type"] == "titre" and not r["trouves"] and r["solution"]][:4]
        jeux = {}
        for r in self.recap:
            jeux[r["jeu"]] = jeux.get(r["jeu"], 0) + sum(max(0, g) for g in r["gains"].values())
        jeu_or, pts_or = max(jeux.items(), key=lambda x: x[1], default=(None, 0))
        jeu_or = jeu_or if pts_or > 0 else None
        return {"joueurs": par_joueur, "rates": rates, "manches": len(self.recap),
                "jeu_or": JEUX[jeu_or]["nom"] if jeu_or else ""}

    def _terminer(self):
        self._vider_manche()
        self._sauver_historique()
        try:                                             # le palmarès à vie (profils, sinon pseudos)
            palmares.enregistrer(self.recap_fin(), {j.id: j.profil or j.nom for j in self.joueurs.values()})
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        self.phase, self.message = "fin", ""

    # ============ commandes de l'hôte ============
    def rejouer(self):
        """Relance la manche en cours avec d'autres films (manche ratée ou buggée) : ses points sont annulés."""
        with self.lock:
            if self.phase not in ("manche", "reponse") or not self.manche:
                return
            if self.phase == "reponse" and self.recap:
                self.recap.pop()
            for pid, j in self.joueurs.items():
                if pid in getattr(self, "scores_debut", {}):
                    j.score = self.scores_debut[pid]
                if pid in getattr(self, "series_debut", {}):
                    j.serie = self.series_debut[pid]
                j.reset()
            jeu = self.manche["jeu"]
            if self.index < len(self.plan):
                self.plan[self.index] = jeu
            self.futurs.pop(self.index, None)
            self._vider_manche()
            self.pause = False
            self._ouvrir(self.index)

    def basculer_pause(self):
        with self.lock:
            if self.phase in ("manche", "reponse", "chargement"):
                self.pause = not self.pause

    def passer(self):
        with self.lock:
            if self.phase == "manche":
                c = self.complice
                if c and c.sous == "choix" and c.lancer_devine():
                    self.ecoule, self.duree = 0.0, float(self.cfg["comp_dur_devine"])
                    return
                self._vers_reponse()
            elif self.phase == "reponse":
                self.reste_reponse = 0

    def menu(self):
        with self.lock:
            for f in self.futurs.values():
                f.cancel()
            self.futurs, self.attente = {}, None
            self._vider_manche()
            if self.phase not in ("lobby", "fin") and not getattr(self, "recap_sauve", False):
                self._sauver_historique(inachevee=True)
            self.phase, self.pause, self.message = "lobby", False, ""

    # ============ musique d'ambiance ============
    def films_musique(self):
        """Films dont la BO peut servir de musique d'ambiance : ceux des listes de la partie, sauf les films
        de la manche en cours et de la suivante (pour ne rien dévoiler)."""
        with self.lock:
            if self.phase not in ("chargement", "manche", "reponse") or not self.pools:
                return []
            bloques = set(self.manche.get("films", [])) if self.manche else set()
            for f in self.futurs.values():
                if f.done() and not f.cancelled() and not f.exception():
                    bloques |= set(f.result().get("films", []))
            films = {cle_film(f): f for k, p in self.pools.items() if k != "acteurs" for f in p}
            return [f for k, f in films.items() if k not in bloques]

    def marquer_musique(self, film):
        """Une BO jouée en ambiance : son film ne sera plus tiré dans cette partie (sinon le titre affiché
        en bas de l'écran donnerait la réponse)."""
        with self.lock:
            for k, deja in self.deja.items():
                if k != "acteurs":
                    deja.add(cle_film(film))

    # ============ réponses des joueurs ============
    def _refus(self, j):
        if not j:
            return "Joueur inconnu"
        if self.phase != "manche" or not self.manche:
            return "La manche est terminée"
        if self.pause:
            return "Jeu en pause"
        return ""

    def _frac(self):
        return max(0.0, min(1.0, 1 - self.ecoule / max(1.0, self.duree)))

    def _rattrapage(self):
        """Tous les jeux : un joueur en retard qui marque pendant la manche gagne en plus une part de son retard
        sur le premier (retard compté au début de la manche), pour pouvoir remonter plus vite."""
        if not self.cfg.get("rattrapage", True) or self.complice:
            return
        debut = getattr(self, "scores_debut", {})
        if not debut:
            return
        tete = max(debut.values())
        pct, maxi = self.cfg.get("rattrapage_pct", 15) / 100, self.cfg.get("rattrapage_max", 500)
        for pid, j in self.joueurs.items():
            retard = tete - debut.get(pid, tete)
            if j.gain > 0 and retard > 0:
                j.bonus = min(maxi, int(round(retard * pct / 10)) * 10)
                j.gain += j.bonus
                j.score += j.bonus

    def _reussite(self, j):
        rang = len(self.ordre)
        self.ordre.append(j.pid)
        j.serie += 1
        j.gain = (BAREME[min(rang, len(BAREME) - 1)] + int(self.cfg["bonus_vitesse"] * self._frac())
                  + self.cfg["serie_bonus"] * min(j.serie - 1, SERIE_MAX))
        j.score += j.gain
        j.trouve = True
        self.main = None
        return {"ok": True, "correct": True, "msg": f"Bravo ! +{j.gain} points"}

    def _perdre_main(self, j):
        self.main = None
        if j:
            j.bloque = time.monotonic() + self.cfg["blocage"]

    def _jouer_moteur(self, pid, d):
        """Action d'un joueur dans un jeu à moteur (la recherche du film se fait hors verrou si besoin)."""
        moteur = self.moteur
        info = None
        if moteur and hasattr(moteur, "resoudre") and d.get("texte"):
            try:
                info = moteur.resoudre(d)
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        with self.lock:
            j = self.joueurs.get(pid)
            refus = self._refus(j)
            if refus:
                return {"ok": False, "msg": refus}
            if self.moteur is not moteur or not moteur:
                return {"ok": False, "msg": "La manche est terminée"}
            return moteur.action(pid, d, self._frac(), info)

    def jouer(self, pid, d):
        return self._jouer_moteur(pid, d if isinstance(d, dict) else {})

    def repondre(self, pid, texte, extra=None):
        if self.moteur:
            return self._jouer_moteur(pid, dict(extra or {}, texte=texte))
        with self.lock:
            j = self.joueurs.get(pid)
            refus = self._refus(j)
            if refus:
                return {"ok": False, "msg": refus}
            m, mode = self.manche, self.cfg["reponse"]
            if m["reponse"] == "nombre":
                if j.essais:
                    return {"ok": False, "msg": "Réponse déjà envoyée"}
                try:
                    n = int(str(texte).strip())
                except ValueError:
                    return {"ok": False, "msg": "Entrez une année, par exemple 1994"}
                if not 1870 <= n <= 2100:
                    return {"ok": False, "msg": "Année invalide"}
                j.essais, j.reponse, j.frac = 1, n, self._frac()
                return {"ok": True, "msg": f"Réponse enregistrée : {n}"}
            if m["reponse"] != "titre":
                return {"ok": False, "msg": "Touchez une réponse"}
            if j.trouve:
                return {"ok": False, "msg": "Déjà trouvé !"}
            if mode == "qcm":
                return {"ok": False, "msg": "Choisissez une proposition"}
            if mode == "buzzer" and self.main != pid:
                return {"ok": False, "msg": "Buzzez d'abord"}
            if mode == "texte" and j.essais >= self.cfg["max_essais"]:
                return {"ok": False, "msg": "Plus d'essais"}
            if any(correspond(texte, c) for c in m["cles"]):
                return self._reussite(j)
            if mode == "buzzer":
                self._perdre_main(j)
                return {"ok": False, "msg": f"Raté ! Bloqué {self.cfg['blocage']} s"}
            j.essais += 1
            presque = any(proche(texte, c) for c in m["cles"])
            reste = self.cfg["max_essais"] - j.essais
            msg = "Presque ! Vérifiez l'orthographe. " if presque else "Raté. "
            return {"ok": False, "msg": msg + (f"{reste} essai(s) restant(s)" if reste else "Plus d'essais.")}

    def choisir(self, pid, i):
        if self.moteur:
            return self._jouer_moteur(pid, {"i": i})
        with self.lock:
            j = self.joueurs.get(pid)
            refus = self._refus(j)
            if refus:
                return {"ok": False, "msg": refus}
            if type(i) is not int:
                return {"ok": False, "msg": "Réponse refusée"}
            if self.complice:
                return self.complice.jouer(pid, i, self._frac())
            m = self.manche
            if m["reponse"] == "choix":
                if not 0 <= i < len(m["etapes"][max(0, self.etape)][1].get("items", [])):
                    return {"ok": False, "msg": "Réponse refusée"}
                if j.essais:
                    return {"ok": False, "msg": "Une seule réponse"}
                j.essais, j.reponse = 1, i
                if i == m["bonne_i"]:
                    self._reussite(j)
                return {"ok": True, "msg": "Réponse enregistrée"}
            if self.cfg["reponse"] != "qcm" or m["reponse"] != "titre" or not 0 <= i < len(self.qcm):
                return {"ok": False, "msg": "Réponse refusée"}
            if j.essais:
                return {"ok": False, "msg": "Une seule réponse en QCM"}
            j.essais, j.reponse = 1, i
            return self._reussite(j) if i == self.qcm_bonne else {"ok": False, "msg": "Raté !"}

    def buzz(self, pid):
        with self.lock:
            j = self.joueurs.get(pid)
            refus = self._refus(j)
            if refus:
                return {"ok": False, "msg": refus}
            if self.cfg["reponse"] != "buzzer" or self.manche["reponse"] != "titre":
                return {"ok": False, "msg": "Pas de buzzer dans ce jeu"}
            if j.trouve:
                return {"ok": False, "msg": "Déjà trouvé !"}
            if self.main is not None:
                return {"ok": False, "msg": f"{self.joueurs[self.main].nom} a la main"}
            now = time.monotonic()
            if now < j.bloque:
                return {"ok": False, "msg": f"Bloqué encore {math.ceil(j.bloque - now)} s"}
            self.main, self.main_depuis = pid, now
            return {"ok": True, "msg": "À vous ! Tapez votre réponse"}

    def suggestions(self, q):
        with self.lock:
            m, moteur = self.manche, self.moteur
            if self.phase != "manche" or not m:
                return []
            if moteur and hasattr(moteur, "suggerer"):      # Chrono, Bingo : films des listes + TMDB
                fn, entrees = moteur.suggerer, None
            elif m.get("suggestions") or (m["reponse"] == "titre" and self.cfg["reponse"] != "qcm"):
                fn, entrees = None, self._entrees(m)
            else:
                return []
        return fn(q) if fn else suggerer(q, entrees)

    def image(self, seq, i, hote=False):
        with self.lock:
            m = self.manche
            if not m or seq != str(self.seq):
                return None
            if i == "r":
                return m.get("revelation") if (hote or "r" in self.publies) else None
            if not i.isdigit():
                return None
            n = int(i)
            return m["images"][n] if (hote or n in self.publies) and n < len(m["images"]) else None

    def audio(self, seq, hote=False):
        """Extrait du blind test : réservé à l'écran hôte (les téléphones ne doivent pas l'entendre)."""
        with self.lock:
            m = self.manche
            return m.get("audio") if hote and m and seq == str(self.seq) else None

    # ============ vues ============
    def _statut(self, j):
        vide = {"t": "", "c": ""}
        if self.phase == "reponse":
            return {"t": f"+{j.gain}", "c": "ok"} if j.gain else vide
        if self.phase != "manche" or not self.manche:
            return vide
        c = self.complice
        if c:
            if c.sous == "choix":
                if j.pid not in c.choisisseurs():
                    return vide
                return {"t": "a choisi", "c": "ok"} if j.pid in c.favoris else {"t": "choisit…", "c": "go"}
            if j.pid in c.devineurs():
                return {"t": "a répondu", "c": "ok"} if j.pid in c.votes else {"t": "réfléchit…", "c": "go"}
            return {"t": "cible", "c": "go"}
        if self.moteur:
            return self.moteur.statut(j.pid)
        if self.main == j.pid:
            return {"t": "a la main", "c": "go"}
        if j.bloque > time.monotonic():
            return {"t": "bloqué", "c": "bad"}
        if self.manche["reponse"] == "choix":
            return {"t": "a répondu", "c": "ok"} if j.essais else vide
        if j.trouve:
            return {"t": "trouvé", "c": "ok"}
        if j.essais:
            if self.manche["reponse"] == "nombre" or self.cfg["reponse"] == "qcm":
                return {"t": "a répondu", "c": "ok"}
            return {"t": f"raté ×{j.essais}", "c": "bad"}
        return vide

    def _classement(self):
        js = sorted(self.joueurs.values(), key=lambda j: -j.score)
        return [dict(j.public(), statut=self._statut(j)) for j in js]

    def _avancement(self):
        js, m = list(self.joueurs.values()), self.manche
        if not js:
            return "Aucun joueur connecté"
        if self.moteur:
            return self.moteur.avancement()
        if m["reponse"] in ("nombre", "choix") or (m["reponse"] == "titre" and self.cfg["reponse"] == "qcm"):
            return f"{sum(1 for j in js if j.essais)} / {len(js)} ont répondu"
        if m["reponse"] == "titre":
            if self.cfg["reponse"] == "buzzer":
                return ""
            return f"{len(self.ordre)} / {len(js)} ont trouvé"
        return ""

    def _resultats(self):
        m = self.manche
        if m["reponse"] == "nombre":
            r = [dict(j.public(), reponse=j.reponse, ecart=abs(j.reponse - m["nombre"]))
                 for j in self.joueurs.values() if j.reponse is not None]
            return sorted(r, key=lambda x: x["ecart"])
        if m["reponse"] in ("titre", "choix"):
            return [self.joueurs[p].public() for p in self.ordre if p in self.joueurs]
        return []

    def _commun(self):
        m, ph = self.manche, self.phase
        v = {"phase": ph, "pause": self.pause, "manche": self.index + 1, "total": len(self.plan),
             "seq": self.seq, "classement": self._classement(), "nb": len(self.joueurs), "message": self.message}
        if not m or ph not in ("manche", "reponse"):
            return v
        info = JEUX[m["jeu"]]
        v.update(jeu=m["jeu"], jeu_nom=info["nom"], jeu_titre=info["titre"], sous=info["qui"], perso=info["perso"], vue=m["vue"], type=m["reponse"],
                 mode=self.cfg["reponse"], duree=round(self.duree, 1), ecoule=round(self.ecoule, 1),
                 etat=m["etapes"][max(0, self.etape)][1], suggestions=bool(m.get("suggestions")))
        if ph == "manche":
            v["avancement"] = self._avancement()
            if self.main in self.joueurs:
                v["main"] = self.joueurs[self.main].public()
            if self.qcm:
                v["qcm"] = self.qcm
        else:
            v.update(solution=m["solution"], detail=m.get("detail", ""), revelation="r" in self.publies,
                     morceau=m.get("morceau", ""), nombre=m.get("nombre"),
                     resultats=self._resultats(), rev_t=round(self.duree_reponse - self.reste_reponse, 1),
                     rev_duree=round(self.duree_reponse, 1))
            if self.qcm:
                v.update(qcm=self.qcm, qcm_bonne=self.qcm_bonne)
            if m["reponse"] == "choix":
                votes = {}
                for j in self.joueurs.values():
                    if j.reponse is not None:
                        votes.setdefault(j.reponse, []).append(dict(j.public(), ok=j.reponse == m["bonne_i"]))
                v["choix"] = {"bonne": m["bonne_i"], "infos": m.get("infos", []), "votes": votes}
        return v

    def vue_joueur(self, pid):
        with self.lock:
            j = self.joueurs.get(pid)
            if not j:
                return {"inconnu": True}
            v = self._commun()
            v["moi"] = dict(j.public(), rang=1 + sum(1 for c in v["classement"] if c["score"] > j.score),
                            essais=max(0, self.cfg.get("max_essais", 3) - j.essais), repondu=j.essais >= 1,
                            reponse=j.reponse, bloque=max(0, math.ceil(j.bloque - time.monotonic())),
                            moi_main=self.main == pid)
            if self.phase == "fin":
                v["mon_recap"] = next((x for x in self.recap_fin()["joueurs"] if x["id"] == j.id), None)
            if self.phase in ("manche", "reponse"):
                if self.complice:
                    v["complice"] = self.complice.vue(pid, self.phase == "reponse")
                if self.moteur:
                    v["moteur"] = self.moteur.vue(pid, self.phase == "reponse")
            return v

    def vue_hote(self):
        with self.lock:
            v = self._commun()
            if self.phase == "chargement" and PREPARATEUR.actif():
                v["message"] = (v.get("message") or "") + "\nAffiches vidées : " + PREPARATEUR.etat()["message"]
            v["erreur"] = self.erreur
            v["audio"] = bool(self.manche and self.manche.get("audio") and self.phase in ("manche", "reponse"))
            if self.phase == "fin":
                v["recap"] = self.recap_fin()
            if self.phase in ("manche", "reponse"):
                if self.complice:
                    v["complice"] = self.complice.vue(None, self.phase == "reponse")
                if self.moteur:
                    v["moteur"] = self.moteur.vue(None, self.phase == "reponse")
            return v
