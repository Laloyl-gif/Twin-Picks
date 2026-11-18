"""Jacques Renault's Card Table (Le brelan) : Jacques Renault, croupier au One Eyed Jack's, distribue cinq cartes : cinq
affiches. Trois d'entre elles forment un brelan : elles ont une même personne au générique (un acteur, un réalisateur,
un compositeur, un scénariste ou un directeur de la photo). Les deux autres ne l'ont pas. Touchez les trois cartes du
brelan. Indice (réglable) : le métier de la personne commune. À la réponse : son nom.
Points : le brelan exact rapporte tout (plus un bonus de vitesse) ; deux cartes justes sur trois, une partie.
"""
import itertools
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie

NB = 5
METIERS = {"acteur": "Un acteur ou une actrice", "real": "Un réalisateur ou une réalisatrice",
           "compo": "Un compositeur ou une compositrice", "scenar": "Un scénariste", "photo": "Un directeur de la photo"}


def personnes(fi):
    """{(id, métier): nom} des gens marquants du film."""
    out = {}
    for a in fi.get("acteurs", [])[:8]:
        out[(a["id"], "acteur")] = a["nom"]
    for cle, met in (("realisateurs", "real"), ("compositeurs", "compo"), ("scenaristes", "scenar"),
                     ("chefs_op", "photo")):
        for p in fi.get(cle, [])[:3]:
            out.setdefault((p["id"], met), p["nom"])
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_jacques"])
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)[:70]
    gens, fiches = {}, {}
    for f in films:
        try:
            fiches[f["id"]] = personnes(fiche(api, f))
        except Exception:  # noqa: BLE001
            continue
        for k in fiches[f["id"]]:
            gens.setdefault(k, []).append(f)
    cands = [(k, fs) for k, fs in gens.items() if len(fs) >= 3]
    random.shuffle(cands)
    cands.sort(key=lambda c: c[0][1] == "acteur" and random.random() < 0.4)      # un peu de variété des métiers
    for (pid, met), fs in cands:
        trio = []
        for f in fs:
            if not any(sagas.meme_univers(f, g) for g in trio):
                trio.append(f)
            if len(trio) == 3:
                break
        if len(trio) < 3:
            continue
        autres = [f for f in films if f["id"] in fiches and (pid, met) not in fiches[f["id"]]
                  and not any(f["id"] == g["id"] or sagas.meme_univers(f, g) for g in trio)]
        random.shuffle(autres)
        main = None
        for a, b in itertools.combinations(autres[:14], 2):
            cinq = trio + [a, b]
            # aucun autre brelan possible parmi les cinq cartes
            if any(set.intersection(*(set(fiches[x["id"]]) for x in t))
                   for t in itertools.combinations(cinq, 3) if set(x["id"] for x in t) != {x["id"] for x in trio}):
                continue
            main = cinq
            break
        if main:
            nom = fiches[trio[0]["id"]][(pid, met)]
            break
    else:
        raise RuntimeError("Le brelan : pas assez de films qui partagent quelqu'un dans les listes choisies.")
    random.shuffle(main)
    bons = sorted(i for i, f in enumerate(main) if f in trio)
    for f in main:
        deja.add(cle_film(f))
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f in main]
    etat = {"items": [{"img": i, "txt": f["title"]} for i, f in enumerate(main)], "donnes": 0, "indices": []}
    evts = [(round(0.6 * k, 2), lambda k=k: etat.update(donnes=k + 1)) for k in range(NB)]
    if cfg.get("jacques_indice", True):
        evts.append((duree * 0.5, lambda: etat["indices"].append("Point commun : " + METIERS[met].lower())))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    role = {"acteur": "joue dans", "real": "a réalisé", "compo": "a composé la musique de", "scenar": "a écrit",
            "photo": "a éclairé"}[met]
    return dict(jeu="jacques", vue="brelan", duree=duree, reponse="brelan", etapes=etapes, images=images,
                revelation=None, cles=[], bonne="", bons=bons, commun=nom, metier=METIERS[met],
                solution=f"{nom} {role} les trois", detail=" · ".join(main[i]["title"] for i in bons),
                films=[cle_film(f) for f in main])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.reponses, self.fracs, self.gains = {}, {}, {}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        if pid in self.reponses:
            return {"ok": False, "msg": "Mise déjà posée"}
        c = d.get("cartes")
        if not isinstance(c, list) or len(set(c)) != 3 or any(type(x) is not int or not 0 <= x < NB for x in c):
            return {"ok": False, "msg": "Touchez trois cartes"}
        self.reponses[pid], self.fracs[pid] = sorted(set(c)), frac
        self.p.joueurs[pid].essais = 1
        return {"ok": True, "msg": "Mise posée !"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(p in self.reponses for p in J)

    def clore(self):
        bons = set(self.m["bons"])
        for pid, j in self.p.joueurs.items():
            r = self.reponses.get(pid)
            if r is None:
                j.serie = 0
                continue
            justes = len(bons & set(r))
            gain = 0
            if justes == 3:
                gain = int(self.cfg["jacques_pts"]) + int(self.cfg["bonus_vitesse"] * self.fracs.get(pid, 0))
            elif justes == 2:
                gain = int(self.cfg["jacques_deux"])
            j.gain += gain
            j.score += gain
            j.trouve = justes == 3
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        return {"t": "a misé", "c": "ok"} if pid in self.reponses else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if p in self.reponses)} / {len(J)} ont misé"

    def vue(self, pid, revele):
        v = {"n": NB}
        if pid:
            v.update(ma_reponse=self.reponses.get(pid), actif=pid not in self.reponses and not revele and not self.p.pause)
        if revele:
            bons = set(self.m["bons"])
            v.update(bons=self.m["bons"], commun=self.m["commun"], metier=self.m["metier"],
                     resultats=sorted([dict(self.p.joueurs[p].public(), justes=len(bons & set(self.reponses.get(p) or [])),
                                            gain=self.gains.get(p, 0)) for p in self.p.joueurs], key=lambda x: -x["gain"]))
        return v
