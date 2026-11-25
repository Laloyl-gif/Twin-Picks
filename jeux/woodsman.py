"""The Woodsman's Light (Got a light?) : l'écran de la partie est plongé dans le noir. Une quarantaine d'affiches y
sont éparpillées, et quatre indices écrits (en gros, sur des bouts de papier) sont cachés parmi elles. Chacun promène
une lumière avec son téléphone (le doigt glisse sur un pavé) : son rond de lumière, à sa couleur, éclaire l'écran, et
tout le monde profite de la lumière des autres. Un indice éclairé reste allumé pour tous. Les ronds grandissent peu à
peu. Quand votre lumière est sur le film décrit par les indices : « C'est lui ! ». Un seul essai : un mauvais film,
et vous êtes hors jeu pour la manche. Plus tôt = plus de points ; le premier a un bonus.
"""
import math
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, tirer

COLS, ROWS = 9, 5
LARGEUR = 0.064                 # largeur d'une affiche (part de la largeur de l'écran, format 16/9)
RATIO = 16 / 9


def indices(api, film, d, fi):
    """Quatre indices sur le film, du plus vague au plus précis."""
    out = []
    an = d.get("annee") or ""
    if d.get("genres") and an:
        dec = f"des années {an[2]}0" if an[:2] == "19" else f"des années {an[:3]}0"
        out.append(f"Un film {dec}, genre : {d['genres'][0].lower()}")
    elif d.get("genres"):
        out.append(f"Genre : {', '.join(g.lower() for g in d['genres'][:2])}")
    if fi.get("pays"):
        out.append(f"Produit en partie par : {fi['pays'][0]}")
    elif fi.get("duree"):
        out.append(f"Il dure {fi['duree'] // 60} h {fi['duree'] % 60:02d}")
    acteurs = fi.get("acteurs", [])
    if acteurs:
        out.append(f"Avec {acteurs[min(1, len(acteurs) - 1)]['nom']}")
    if fi.get("realisateurs"):
        out.append(f"Réalisé par {fi['realisateurs'][0]['nom']}")
    elif acteurs:
        out.append(f"Avec {acteurs[0]['nom']}")
    return out[:4]


def construire(api, cfg, pool, deja):
    films = [f for f in pool if f.get("poster_path")]
    for _ in range(12):
        cible = tirer(films, deja)
        d = details_film(api, cible)
        try:
            fi = fiche(api, cible)
        except Exception:  # noqa: BLE001
            continue
        ind = indices(api, cible, d, fi)
        if len(ind) >= 3:
            break
    else:
        raise RuntimeError("Got a light? : pas assez d'informations sur les films des listes choisies.")
    if cfg.get("indices_recompenses", True):              # une note de plus : ses récompenses (Wikidata)
        try:
            import recompenses
            r = recompenses.indice(api, cible)
        except Exception:  # noqa: BLE001
            r = ""
        if r:
            ind = ind[:3] + [r] + ind[3:]
    autres = [f for f in films if f["id"] != cible["id"] and not sagas.meme_univers(f, cible)]
    random.shuffle(autres)
    n_aff = COLS * ROWS - len(ind)
    choisis = [cible] + autres[:n_aff - 1]
    random.shuffle(choisis)
    cases = random.sample(range(COLS * ROWS), COLS * ROWS)
    w, h = LARGEUR, LARGEUR * 1.5 * RATIO
    aff = []
    for k, f in enumerate(choisis):
        c = cases[k]
        cx = (c % COLS + 0.5) / COLS + random.uniform(-0.25, 0.25) / COLS
        cy = (c // COLS + 0.5) / ROWS + random.uniform(-0.12, 0.12) / ROWS
        aff.append({"img": k, "x": round(cx, 4), "y": round(cy, 4), "r": random.randint(-12, 12)})
    notes = []
    for k, t in enumerate(ind):
        c = cases[len(choisis) + k]
        notes.append({"texte": t, "x": round((c % COLS + 0.5) / COLS, 4), "y": round((c // COLS + 0.5) / ROWS, 4),
                      "r": random.randint(-8, 8)})
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w185"), (160, 240)), 240) for f in choisis]
    bonne = next(i for i, f in enumerate(choisis) if f["id"] == cible["id"])
    etat = {"affiches": aff, "cachees": list(range(len(images))), "w": w, "h": h}
    return dict(jeu="woodsman", vue="lumiere", duree=float(cfg["dur_woodsman"]), reponse="lumiere", etapes=[(0.0, etat)],
                images=images, revelation=None, cles=[], bonne="", bonne_i=bonne, notes=notes,
                solution=f"Le film : {cible['title']}", detail=" · ".join(ind), films=[cle_film(f) for f in choisis[:1]])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.pos, self.trouves, self.elimines = {}, {}, {}
        self.vus = set()                         # indices déjà éclairés (pour tous)
        self.premier = None

    def ok(self):
        return ""

    def rayon(self):
        k = min(1.0, self.p.ecoule / max(1.0, self.p.duree))
        return 0.055 + 0.075 * k                 # part de la largeur de l'écran

    def _dist(self, a, b):
        return math.hypot(a[0] - b[0], (a[1] - b[1]) / RATIO)

    def action(self, pid, d, frac, info=None):
        if pid in self.trouves or pid in self.elimines:
            return {"ok": False, "msg": "Manche finie pour vous"}
        if "pos" in d:
            try:
                x, y = (min(1.0, max(0.0, float(v))) for v in d["pos"][:2])
            except (TypeError, ValueError):
                return {"ok": False, "msg": ""}
            self.pos[pid] = (x, y)
            r = self.rayon()
            for k, n in enumerate(self.m["notes"]):
                if k not in self.vus and self._dist((x, y), (n["x"], n["y"])) < r:
                    self.vus.add(k)
            return {"ok": True, "msg": ""}
        if d.get("cest_lui"):
            p = self.pos.get(pid)
            if not p:
                return {"ok": False, "msg": "Allumez d'abord votre lumière"}
            r = self.rayon()
            aff = self.m["etapes"][0][1]["affiches"]
            proche = min(aff, key=lambda a: self._dist(p, (a["x"], a["y"])))
            if self._dist(p, (proche["x"], proche["y"])) > max(r, 0.05):
                return {"ok": False, "msg": "Pas d'affiche sous votre lumière"}
            self.p.joueurs[pid].essais = 1
            if proche["img"] == self.m["bonne_i"]:
                self.trouves[pid] = frac
                if self.premier is None:
                    self.premier = pid
                return {"ok": True, "correct": True, "msg": "C'est lui !"}
            self.elimines[pid] = proche["img"]
            return {"ok": True, "correct": False, "msg": "Ce n'est pas lui… hors jeu pour cette manche"}
        return {"ok": False, "msg": ""}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(p in self.trouves or p in self.elimines for p in J)

    def clore(self):
        for pid, j in self.p.joueurs.items():
            gain = 0
            if pid in self.trouves:
                gain = int(self.cfg["woodsman_pts"]) + int(self.cfg["bonus_vitesse"] * self.trouves[pid])
                if pid == self.premier:
                    gain += int(self.cfg["woodsman_premier"])
            j.gain += gain
            j.score += gain
            j.trouve = pid in self.trouves
            j.serie = j.serie + 1 if j.trouve else 0

    def statut(self, pid):
        if pid in self.trouves:
            return {"t": "trouvé", "c": "ok"}
        if pid in self.elimines:
            return {"t": "hors jeu", "c": "bad"}
        return {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if p in self.trouves)} / {len(J)} ont trouvé"

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"rayon": round(self.rayon(), 4),
             "lumieres": [dict(J[p].public(), x=xy[0], y=xy[1]) for p, xy in self.pos.items()
                          if p in J and p not in self.trouves and p not in self.elimines],
             "notes": [n for k, n in enumerate(self.m["notes"]) if k in self.vus or revele],
             "trouves": [J[p].public() for p in self.trouves if p in J]}
        if revele:
            v.update(bonne=self.m["bonne_i"], elimines={p: i for p, i in self.elimines.items()})
        if not pid:                                   # l'écran de la partie : tous les indices (éclairés ou non)
            v["toutes_notes"] = [dict(n, vu=k in self.vus or revele) for k, n in enumerate(self.m["notes"])]
        if pid:
            v.update(ma_pos=self.pos.get(pid), fini=pid in self.trouves or pid in self.elimines,
                     trouve=pid in self.trouves, actif=not revele and not self.p.pause and pid not in self.trouves
                     and pid not in self.elimines)
        return v
