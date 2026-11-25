"""The Woodsman's Light (Le dessin de lumière), façon Pictionary : à chaque manche, un joueur est le Woodsman (chacun
son tour). Son téléphone lui montre un film connu et quelques idées de choses à dessiner (objets, lieux, animaux tirés
des mots-clés et du résumé, comme chez Major Briggs). Il dessine du bout du doigt : sur l'écran de la partie, dans le
noir, son trait s'allume comme une lumière… et s'éteint au bout de quelques secondes (réglable). Il faut donc
redessiner sans cesse : pas de lettres, pas de chiffres, juste la lumière.

Les autres tapent le titre sur leur téléphone (autant d'essais qu'ils veulent). Plus tôt = plus de points, bonus pour
le premier ; le Woodsman marque pour chaque joueur qui trouve. La manche s'arrête quand tout le monde a trouvé.
"""
import random
import time

from tmdb import cle_film, details_film
from visuels import en_jpeg
from texte import correspond, proche
from .commun import affiche, manche_titre

MAX_POINTS = 60                 # points par envoi (le téléphone envoie quelques fois par seconde)
CATS_DESSIN = ("objet", "animal", "lieu", "nature", "reel", "personnage")


def idees(api, film, d, n=4):
    """Quelques choses concrètes à dessiner (lexique de Major Briggs) ; [] si rien de sûr."""
    try:
        from . import briggs
        elts = briggs.elements(api, film, d)
    except Exception:  # noqa: BLE001
        return []
    concrets = [lib for _, lib, cat in elts if cat in CATS_DESSIN]
    autres = [lib for _, lib, cat in elts if cat == "evenement"]
    return (concrets + autres)[:n]


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    if not films:
        raise RuntimeError("Le dessin de lumière : pas de film avec affiche dans les listes choisies.")
    films.sort(key=lambda f: -(f.get("votes") or 0))          # des films connus : il faut pouvoir les dessiner
    connus = films[:max(15, len(films) // 3)]
    random.shuffle(connus)
    connus.sort(key=lambda f: cle_film(f) in deja)
    film = connus[0]
    deja.add(cle_film(film))
    d = details_film(api, film)
    aff = en_jpeg(affiche(api, film, "w342"))
    # pas d'image pendant la manche (les téléphones des devineurs ne doivent rien pouvoir charger) : l'affiche
    # n'apparaît qu'à la réponse
    m = manche_titre("woodsman", "dessin", float(cfg["dur_woodsman"]), film, d, [(0.0, {})], [], aff, cfg)
    m.update(reponse="dessin", suggestions=True, idees=idees(api, film, d),
             annee=d.get("annee") or "", resume=(d.get("resume") or "")[:260])
    return m


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        ids = list(partie.joueurs)
        self.dessinateur = ids[partie.index % len(ids)] if ids else None
        self.traits = []                         # [{k: n° du trait, i: n° du morceau, pts: [[x, y]…], t: instant}]
        self.trouves, self.essais, self.gains = {}, {}, {}
        self.premier = None
        self.n_traits = 0
        self.n_morceaux = 0                      # numéro unique de chaque morceau envoyé (clé pour l'écran)

    def vie(self):
        return float(self.cfg.get("woodsman_vie", 2.5))

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le dessin de lumière se joue à 2 joueurs minimum (un qui dessine, les autres devinent)."
        return ""

    def devineurs(self):
        return [p for p in self.p.joueurs if p != self.dessinateur]

    def _nettoyer(self):
        limite = time.monotonic() - self.vie() - 0.5
        self.traits = [t for t in self.traits if t["t"] >= limite]

    def action(self, pid, d, frac, info=None):
        if pid == self.dessinateur:
            if "trait" not in d:
                return {"ok": False, "msg": "Vous dessinez : les autres devinent"}
            try:
                pts = [[round(min(1.0, max(0.0, float(x))), 4), round(min(1.0, max(0.0, float(y))), 4)]
                       for x, y in d["trait"][:MAX_POINTS]]
            except (TypeError, ValueError):
                return {"ok": False, "msg": ""}
            if not pts:
                return {"ok": True, "msg": ""}
            if d.get("nouveau"):
                self.n_traits += 1
            self._nettoyer()
            self.n_morceaux += 1
            self.traits.append({"k": self.n_traits, "i": self.n_morceaux, "pts": pts, "t": time.monotonic()})
            return {"ok": True, "msg": ""}
        texte = str(d.get("texte") or "").strip()
        if not texte:
            return {"ok": False, "msg": "Tapez le titre du film"}
        if pid in self.trouves:
            return {"ok": False, "msg": "Déjà trouvé !"}
        self.essais[pid] = self.essais.get(pid, 0) + 1
        if any(correspond(texte, c) for c in self.m["cles"]):
            self.trouves[pid] = frac
            if self.premier is None:
                self.premier = pid
            return {"ok": True, "correct": True, "msg": "C'est lui !"}
        presque = any(proche(texte, c) for c in self.m["cles"])
        return {"ok": True, "correct": False, "msg": "Presque ! Vérifiez l'orthographe" if presque else "Non…"}

    def fini(self):
        dev = self.devineurs()
        return bool(dev) and all(p in self.trouves for p in dev)

    def clore(self):
        c = self.cfg
        for pid, j in self.p.joueurs.items():
            gain = 0
            if pid == self.dessinateur:
                gain = int(c.get("woodsman_dessin", 300)) * len(self.trouves)
            elif pid in self.trouves:
                gain = int(c["woodsman_pts"] * (0.5 + 0.5 * self.trouves[pid]))
                if pid == self.premier:
                    gain += int(c["woodsman_premier"])
            j.gain += gain
            j.score += gain
            j.trouve = pid in self.trouves or (pid == self.dessinateur and bool(self.trouves))
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        if pid == self.dessinateur:
            return {"t": "dessine", "c": "go"}
        if pid in self.trouves:
            return {"t": "trouvé", "c": "ok"}
        return {"t": "", "c": ""}

    def avancement(self):
        return f"{len(self.trouves)} / {len(self.devineurs())} ont trouvé"

    def vue(self, pid, revele):
        J = self.p.joueurs
        self._nettoyer()
        now = time.monotonic()
        d = J.get(self.dessinateur)
        v = {"dessinateur": d.public() if d else None, "vie": self.vie(),
             "traits": [] if revele else [dict(k=t["k"], i=t["i"], pts=t["pts"], age=round(now - t["t"], 2)) for t in self.traits],
             "trouves": [J[p].public() for p in self.trouves if p in J]}
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0), dessine=p == self.dessinateur,
                                          trouve=p in self.trouves) for p in J], key=lambda x: -x["gain"])
        if pid:
            moi = pid == self.dessinateur
            v.update(moi_dessine=moi, trouve=pid in self.trouves, essais=self.essais.get(pid, 0),
                     actif=not revele and not self.p.pause)
            if moi and not revele:
                v.update(film=self.m["bonne"], annee=self.m.get("annee", ""), idees=self.m.get("idees", []),
                         resume=self.m.get("resume", ""), n_trouves=len(self.trouves), n_devineurs=len(self.devineurs()))
        return v
