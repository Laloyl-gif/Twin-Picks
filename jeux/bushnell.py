"""Bushnell Mullins' Rain (La pluie d'affiches) : Bushnell, l'ancien boxeur, entraîne vos réflexes. Une condition
simple s'affiche (« années 90 », « comédie », « noté plus de 7 »…) et des affiches tombent, les mêmes pour tous, sur
l'écran et sur chaque téléphone, de plus en plus vite. Touchez celles qui respectent la condition : des points.
Laisser tomber une affiche qui la respectait, ou toucher une affiche qui ne la respecte pas : des points en moins.
Trois conditions par manche (environ 20 s chacune) ; les scores montent en direct.
"""
import random

from PIL import ImageOps

from tmdb import GENRES, cle_film
from visuels import en_jpeg
from .commun import affiche

FAMILLES = {"Comédie": {35}, "Horreur": {27}, "Action": {28, 12}, "Science-fiction": {878}, "Drame": {18},
            "Animation": {16}, "Thriller ou crime": {53, 80}, "Romance": {10749}}


def _an(f):
    try:
        return int((f.get("release_date") or "")[:4])
    except ValueError:
        return 0


def conditions(films):
    """Les conditions possibles : (texte, test), chacune avec assez de films qui la respectent ET qui ne la
    respectent pas."""
    out = []
    for d in (1970, 1980, 1990, 2000, 2010, 2020):
        out.append((f"Années {str(d)[2:]}" if d < 2000 else f"Années {d}", lambda f, d=d: d <= _an(f) < d + 10))
    out.append(("Sortis avant 1990", lambda f: 0 < _an(f) < 1990))
    out.append(("Sortis après 2010", lambda f: _an(f) > 2010))
    for nom, ids in FAMILLES.items():
        out.append((nom, lambda f, ids=ids: bool(ids & set(f.get("genre_ids") or []))))
    out.append(("Notés plus de 7,5 sur TMDB", lambda f: (f.get("note") or 0) >= 7.5))
    out.append(("Notés moins de 6,5 sur TMDB", lambda f: 0 < (f.get("note") or 0) < 6.5))
    out.append(("Un seul mot dans le titre", lambda f: len((f.get("title") or "").split()) == 1))
    bons = []
    for txt, t in out:
        n = sum(1 for f in films if t(f))
        if n >= 6 and len(films) - n >= 6:
            bons.append((txt, t))
    return bons


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)[:160]
    conds = conditions(films)
    if len(conds) < 2:
        raise RuntimeError("La pluie d'affiches : pas assez de films variés dans les listes choisies.")
    nb = max(1, int(cfg.get("bushnell_conditions", 3)))
    choisies = random.sample(conds, min(nb, len(conds)))
    D = float(cfg.get("bushnell_dur", 20))
    t0 = 3.0
    images, idx_img, gouttes, etapes_c = [], {}, [], []
    t = t0
    for k, (txt, test) in enumerate(choisies):
        debut, fin = t, t + D
        etapes_c.append({"txt": txt, "t0": round(debut, 2), "t1": round(fin, 2)})
        oui = [f for f in films if test(f)]
        non = [f for f in films if not test(f)]
        random.shuffle(oui); random.shuffle(non)
        x = debut + 1.0
        i = 0
        while x < fin - 1.0:
            avance = (x - t0) / max(1.0, len(choisies) * D)          # 0 → 1 sur la manche : de plus en plus vite
            chute = 3.2 - 1.6 * avance                                  # de 3,2 s à 1,6 s pour traverser l'écran
            if not oui:
                oui = [f for f in films if test(f)]; random.shuffle(oui)
            if not non:
                non = [f for f in films if not test(f)]; random.shuffle(non)
            f = (oui if random.random() < 0.45 else non).pop()
            if cle_film(f) not in idx_img:
                idx_img[cle_film(f)] = len(images)
                images.append(en_jpeg(ImageOps.fit(affiche(api, f, "w185"), (140, 210)), 210))
            gouttes.append({"id": len(gouttes), "img": idx_img[cle_film(f)], "t0": round(x, 2), "dur": round(chute, 2),
                            "x": round(random.uniform(0.04, 0.74), 3), "ok": bool(test(f)), "c": k, "txt": f["title"]})
            x += 0.8 - 0.38 * avance + random.uniform(-0.1, 0.1)       # de plus en plus d'affiches à la fois
            i += 1
        t = fin + 1.5
    duree = t + 2
    for f in films:
        if cle_film(f) in idx_img:
            deja.add(cle_film(f))
    return dict(jeu="bushnell", vue="pluie", duree=round(duree, 1), reponse="pluie",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[],
                bonne="", solution="Fin de l'averse", detail="", films=list(idx_img)[:10], gouttes=gouttes,
                conditions=etapes_c, signature=tuple(c["txt"] for c in etapes_c) + (len(gouttes),))


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.touches = {}                       # pid -> {id goutte: juste ?}
        self.gains = {}
        self.par_id = {g["id"]: g for g in m["gouttes"]}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        g = self.par_id.get(d.get("goutte"))
        if not g:
            return {"ok": False, "msg": ""}
        t = self.p.ecoule
        if not (g["t0"] - 0.2 <= t <= g["t0"] + g["dur"] + 0.6):          # un peu de marge (réseau)
            return {"ok": False, "msg": "Trop tard"}
        mes = self.touches.setdefault(pid, {})
        if g["id"] in mes:
            return {"ok": False, "msg": ""}
        mes[g["id"]] = g["ok"]
        return {"ok": True, "correct": g["ok"], "msg": "✓" if g["ok"] else "✗ ne colle pas"}

    def fini(self):
        return False

    def _score(self, pid, jusqua=None):
        c = self.cfg
        mes = self.touches.get(pid, {})
        s = 0
        for g in self.m["gouttes"]:
            tombe = jusqua is None or g["t0"] + g["dur"] <= jusqua
            if g["id"] in mes:
                s += int(c.get("bushnell_pts", 100)) if mes[g["id"]] else -int(c.get("bushnell_faux", 60))
            elif g["ok"] and tombe:
                s -= int(c.get("bushnell_rate", 40))
        return s

    def clore(self):
        for pid, j in self.p.joueurs.items():
            gain = max(self._score(pid), -j.score)
            self.gains[pid] = gain
            j.gain += gain
            j.score += gain
            j.trouve = gain > 0
            j.serie = j.serie + 1 if j.trouve else 0

    def statut(self, pid):
        s = self._score(pid, self.p.ecoule)
        return {"t": f"{s:+d}", "c": "ok" if s > 0 else ""}

    def avancement(self):
        c = self._cond()
        return c["txt"] if c else ""

    def _cond(self):
        t = self.p.ecoule
        for c in self.m["conditions"]:
            if c["t0"] - 1.5 <= t < c["t1"] + 1.5:
                return c
        return None

    def vue(self, pid, revele):
        J = self.p.joueurs
        t = self.p.ecoule
        c = self._cond()
        # les gouttes visibles bientôt ou en cours (le client anime la chute avec son horloge)
        gouttes = [{"id": g["id"], "img": g["img"], "t0": g["t0"], "dur": g["dur"], "x": g["x"],
                    "ok": g["ok"] if g["t0"] + g["dur"] <= t or revele else None}
                   for g in self.m["gouttes"] if g["t0"] - 3 <= t <= g["t0"] + g["dur"] + 1]
        v = {"condition": c["txt"] if c else "", "n_cond": len(self.m["conditions"]),
             "k_cond": next((k for k, x in enumerate(self.m["conditions"]) if x is c), -1), "gouttes": gouttes,
             "scores": sorted([dict(J[p].public(), live=self._score(p, None if revele else t)) for p in J],
                              key=lambda x: -x["live"])}
        if pid:
            v.update(mes={str(k): x for k, x in self.touches.get(pid, {}).items()}, actif=not revele and not self.p.pause)
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0)) for p in J], key=lambda x: -x["gain"])
        return v
