"""Lucy's Hotline (chrono) : une condition s'affiche (genre, période, acteurs, réalisateurs, pays, durée,
box-office, titre, note d'un autre joueur…) ; chacun tape le plus de films possible qui la respectent.

N'importe quel film de TMDB compte (pas seulement ceux des listes). Acteur / réalisateur / compositeur :
plusieurs noms proposés (« Avec A, B ou C »), pour pouvoir jouer même sans connaître l'un d'eux.
« Notes d'un autre joueur » : devinettes croisées, chacun cherche les films notés d'une certaine façon par sa cible.
Bouton « Changer » sur les téléphones : quand tous les joueurs l'ont touché, une nouvelle condition arrive, le chrono
repart au début et les films déjà donnés sont retirés (avec leurs points).
Points : un nombre fixe par film ; à la fin, bonus pour le 1er (le plus de films), la moitié pour le 2e, le quart
pour le 3e. Réalisateurs : toujours realisateurs.txt, limités à ceux que TOUS les joueurs présents connaissent.
Jamais de condition « film d'une saga ». Un film déjà donné lors d'une manche précédente ne compte plus (réglable).
"""
import random

from tmdb import cle_film, libelle
from .contraintes import Ctx, connus_communs, entrees_films, generer, index, pour_profil, resoudre, suggerer_films

RESERVES = 3
RANGS = [1.0, 0.5, 0.25]                      # bonus du 1er, du 2e, du 3e (part de lucy_premier)


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_lucy"])
    x = Ctx(api, cfg, pool, cfg.get("lucy_personnes", 3), realisateurs_ok=connus_communs(cfg.get("_profils", [])))
    c = generer(x, "lucy_")
    if not c:
        raise RuntimeError("Chrono : aucune condition possible avec les films des listes.")
    reserves = []
    if cfg.get("lucy_changer", True):
        types = [k for k in ("genre", "decennie", "periode", "acteur", "realisateur", "compositeur", "note", "langue",
                             "pays", "duree", "boxoffice", "theme", "titre") if cfg.get("lucy_" + k, True)]
        for _ in range(RESERVES + 2):
            r = generer(x, "lucy_", exclues={c["txt"]} | {r["txt"] for r in reserves}, types=types or None)
            if r and r["type"] != "joueurs":
                reserves.append(r)
            if len(reserves) == RESERVES:
                break
    m = dict(jeu="lucy", vue="chrono", duree=duree, reponse="chrono", revelation=None, images=[], cles=[], bonne="",
             solution=c["txt"], detail="", films=[], suggestions=True, contrainte=c, reserves=reserves, api=api,
             films_pool=pool)
    if c["type"] == "joueurs":                    # devinettes croisées : une condition par profil, même variante
        m["croisees"] = {}
        for p in cfg.get("_profils", []):
            cp = pour_profil(p, pool, c["variante"])
            if cp:
                m["croisees"][p["nom"]] = cp
        m["solution"] = "Les films des autres"
    texte = "Les films de votre cible" if c["type"] == "joueurs" else c["txt"]
    m["etapes"] = [(0.0, {"contrainte": texte})]
    return m


class Moteur:
    suggestions = True
    films_tmdb = True                             # suggestions : films des listes + recherche TMDB

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.trouves = {pid: [] for pid in partie.joueurs}        # [(n° de condition, clé, libellé)]
        self.cibles = {}
        self.ci = 0                                               # condition en cours (0, puis les réserves)
        self.votes = set()
        croisees = m.get("croisees")
        if croisees:
            profils = list(croisees)
            random.shuffle(profils)
            for i, pid in enumerate(partie.joueurs):
                mien = partie.joueurs[pid].profil
                autres = [n for n in profils if n != mien]
                if autres:
                    self.cibles[pid] = autres[i % len(autres)]
        toutes = [m["contrainte"], *m.get("reserves", []), *(croisees or {}).values()]
        self.idx = index([f for f in m.get("films_pool", [])] + [f for c in toutes for f in c["valides"]()])
        self.entrees = entrees_films([f for f, _ in self.idx])
        self.gains_seul = {}

    def ok(self):
        if self.m.get("croisees") and not self.cibles:
            return "Chrono : il faut au moins 2 joueurs avec un profil pour les notes croisées."
        return ""

    # ---------- condition de chacun ----------
    def croise(self):
        return bool(self.m.get("croisees")) and self.ci == 0

    def condition(self, pid):
        if self.croise():
            c = self.cibles.get(pid)
            return self.m["croisees"].get(c) if c else None
        return self.m["contrainte"] if self.ci == 0 else self.m["reserves"][self.ci - 1]

    def contrainte(self, pid):
        if self.croise() and pid:
            c = self.condition(pid)
            return c["txt"] if c else "Vous êtes la cible : aidez-les… en silence"
        if self.croise():
            return "Les films de votre cible"
        return self.condition(None)["txt"]

    def peut_changer(self):
        return bool(self.cfg.get("lucy_changer", True)) and self.ci < len(self.m.get("reserves", []))

    # ---------- hors verrou : retrouver le film tapé (listes, puis TMDB) ----------
    def resoudre(self, d):
        conds = [self.condition(pid) for pid in self.p.joueurs] if self.croise() else [self.condition(None)]
        avec_fiche = any(c and c.get("fiche") for c in conds)
        return resoudre(self.m["api"], d.get("texte"), self.idx, avec_fiche)

    def suggerer(self, q):
        return suggerer_films(self.m["api"], q, self.entrees)

    # ---------- actions ----------
    def action(self, pid, d, frac, info=None):
        J = self.p.joueurs
        if d.get("type") == "changer":
            if not self.peut_changer():
                return {"ok": False, "msg": "Plus d'autre condition pour cette manche"}
            if pid in self.votes:
                self.votes.discard(pid)
                return {"ok": True, "msg": "Vote retiré"}
            self.votes.add(pid)
            if self.votes >= set(J):
                self._retirer_films()
                self.ci += 1
                self.votes = set()
                self.p.ecoule = 0.0                       # nouvelle condition : le chrono repart du début
                return {"ok": True, "msg": "Nouvelle condition ! Le chrono repart, les films donnés sont retirés"}
            return {"ok": True, "msg": f"Changer : {len(self.votes & set(J))}/{len(J)} joueurs"}
        texte = str(d.get("texte") or "").strip()
        c = self.condition(pid)
        if not texte:
            return {"ok": False, "msg": "Tapez un titre"}
        if c is None:
            return {"ok": False, "msg": "Pas de cible pour vous cette manche"}
        f = (info or {}).get("film")
        if not f:
            return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
        if c.get("fiche") and not (info or {}).get("fiche"):
            info = resoudre(self.m["api"], libelle(f), self.idx, True) or {}
        if not c["test"](f, (info or {}).get("fiche")):
            return {"ok": False, "msg": f"Raté : {libelle(f)} ne colle pas"}
        mes = self.trouves.setdefault(pid, [])
        k = cle_film(f)
        if k in {kk for ci, kk, _ in mes if ci == self.ci}:
            return {"ok": False, "msg": f"Déjà trouvé : {libelle(f)}"}
        utilises = self.p.utilises.setdefault(pid, set())
        if self.cfg.get("films_uniques", True) and k in utilises and k not in {kk for _, kk, _ in mes}:
            return {"ok": False, "msg": f"{libelle(f)} : déjà donné dans une manche précédente"}
        mes.append((self.ci, k, libelle(f)))
        utilises.add(k)
        j = J[pid]
        pts = self.cfg["lucy_pts"]
        j.gain += pts
        j.score += pts
        j.essais += 1
        return {"ok": True, "correct": True, "msg": f"✓ {libelle(f)} (+{pts})"}

    def _retirer_films(self):
        """Changement de condition : on reprend au début, les films déjà donnés sont retirés avec leurs points."""
        J = self.p.joueurs
        for pid, mes in self.trouves.items():
            perdus = [x for x in mes if x[0] == self.ci]
            if not perdus:
                continue
            self.trouves[pid] = [x for x in mes if x[0] != self.ci]
            utilises = self.p.utilises.get(pid, set())
            for _, k, _ in perdus:
                utilises.discard(k)
            if pid in J:
                pts = self.cfg["lucy_pts"] * len(perdus)
                J[pid].gain -= pts
                J[pid].score -= pts
                J[pid].essais = max(0, J[pid].essais - len(perdus))

    def fini(self):
        return False

    def _groupe(self, pid, ci):
        """Films comparés entre joueurs : même condition (et même cible en croisé)."""
        return (ci, self.cibles.get(pid, "") if ci == 0 and self.m.get("croisees") else "")

    def clore(self):
        """Bonus de classement : le 1er (le plus de films) gagne lucy_premier, le 2e la moitié, le 3e le quart
        (ex æquo : même bonus)."""
        J = self.p.joueurs
        nombres = sorted({len(l) for p, l in self.trouves.items() if p in J and l}, reverse=True)
        for pid, l in self.trouves.items():
            if pid not in J:
                continue
            J[pid].trouve = bool(l)
            if not l:
                continue
            rang = nombres.index(len(l))
            bonus = int(self.cfg.get("lucy_premier", 400) * RANGS[rang]) if rang < len(RANGS) else 0
            self.gains_seul[pid] = bonus
            J[pid].gain += bonus
            J[pid].score += bonus
        meilleur = max((len(l) for l in self.trouves.values()), default=0)
        for pid, j in J.items():
            j.serie = j.serie + 1 if meilleur and len(self.trouves.get(pid, [])) == meilleur else 0

    def statut(self, pid):
        n = len(self.trouves.get(pid, []))
        return {"t": f"{n} film{'s' if n > 1 else ''}", "c": "ok"} if n else {"t": "", "c": ""}

    def avancement(self):
        n = sum(len(l) for l in self.trouves.values())
        return f"{n} film{'s' if n > 1 else ''} trouvé{'s' if n > 1 else ''}"

    def _j(self, pid):
        j = self.p.joueurs.get(pid)
        return j.public() if j else None

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"compteurs": sorted([dict(x, n=len(self.trouves.get(p, []))) for p in J if (x := self._j(p))],
                                 key=lambda x: -x["n"]),
             "croisees": self.croise(), "contrainte": self.contrainte(pid), "ci": self.ci,
             "changer": {"possible": self.peut_changer() and not revele, "votes": len(self.votes & set(J)),
                         "total": len(J), "moi": pid in self.votes}}
        if self.croise():
            v["paires"] = [{"devineur": self._j(p), "cible": c} for p, c in self.cibles.items() if p in J]
        if pid:
            v.update(mes_films=[l for ci, _, l in self.trouves.get(pid, []) if ci == self.ci],
                     avant=sum(1 for ci, _, _ in self.trouves.get(pid, []) if ci != self.ci),
                     actif=not revele and not self.p.pause and self.condition(pid) is not None)
        if revele:
            trouves_tous = {k for l in self.trouves.values() for _, k, _ in l}
            res = []
            for p in J:
                if self.trouves.get(p) or p in self.cibles or not self.m.get("croisees"):
                    res.append(dict(self._j(p), films=[l for _, _, l in self.trouves.get(p, [])],
                                    bonus=self.gains_seul.get(p, 0), cible=self.cibles.get(p)))
            v["resultats"] = sorted(res, key=lambda x: -len(x["films"]))
            if self.croise():
                conds = [c for c in self.m["croisees"].values()]
            else:
                conds = [self.condition(None)]
            oublies = [f for c in conds for f in c["valides"]() if f and cle_film(f) not in trouves_tous]
            oublies = list({cle_film(f): f for f in oublies}.values())
            oublies.sort(key=lambda f: -(f.get("votes") or 0))
            v["oublies"] = [libelle(f) for f in oublies[:8]]
        return v
