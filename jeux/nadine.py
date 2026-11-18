"""Nadine's Silent Drape Runners (La frise) : les films sont accrochés à une tringle, dans le désordre ; chacun les
remet dans l'ordre de sortie, du plus ancien au plus récent (sur son téléphone : touchez-les dans l'ordre).
À la réponse, les affiches glissent sans bruit sur la tringle jusqu'à leur place, comme les rideaux de Nadine.

Points : par film à la bonne place, bonus si toute la frise est juste (plus un bonus de rapidité). Jamais deux films
de la même année (écart réglable), ni deux films d'une même saga ou d'un même univers. Indice à mi-temps
(réglable) : l'année d'un des films.
"""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche, chronologie


def _date(f):
    return f.get("release_date") or ""


def construire(api, cfg, pool, deja):
    nb, ecart = int(cfg.get("nadine_nb", 5)), int(cfg.get("nadine_ecart", 2))
    duree = float(cfg["dur_nadine"])
    films = [f for f in pool if (_date(f)[:4]).isdigit() and (f.get("poster_path") or f.get("title"))]
    if len(films) < nb:
        raise RuntimeError("La frise : pas assez de films datés dans les listes.")
    for essai in range(40):
        neufs = [f for f in films if cle_film(f) not in deja]
        if len(neufs) < nb * 3:                   # presque tout a été joué : on reprend tous les films
            neufs = list(films)
        random.shuffle(neufs)
        choisis = []
        for f in neufs:                           # au hasard parmi tous les films sélectionnés
            an = int(_date(f)[:4])
            if any(abs(an - int(_date(g)[:4])) < max(1, ecart if essai < 30 else 1) for g in choisis):
                continue
            if any(sagas.meme_univers(f, g) for g in choisis):
                continue
            choisis.append(f)
            if len(choisis) == nb:
                break
        if len(choisis) == nb:
            break
    else:
        raise RuntimeError("La frise : impossible de trouver des films d'années différentes.")
    random.shuffle(choisis)
    for f in choisis:
        deja.add(cle_film(f))
    ordre = sorted(range(nb), key=lambda i: _date(choisis[i]))     # bonne frise : indices du plus ancien au plus récent
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f in choisis]
    annees = [_date(f)[:4] for f in choisis]
    etat = {"items": [{"img": i, "txt": f["title"]} for i, f in enumerate(choisis)], "annees": {}, "indices": []}
    evts = []
    if cfg.get("nadine_indice", True):
        i = ordre[len(ordre) // 2]
        evts.append((duree * 0.5, lambda i=i: etat["annees"].update({str(i): annees[i]})))
    etapes = chronologie(evts, lambda: {**etat, "annees": dict(etat["annees"]), "indices": list(etat["indices"])})
    solution = " → ".join(f"{choisis[i]['title']} ({annees[i]})" for i in ordre)
    return dict(jeu="nadine", vue="frise", duree=duree, reponse="ordre", etapes=etapes, revelation=None, images=images,
                cles=[], bonne="", solution="Du plus ancien au plus récent", detail=solution, ordre=ordre,
                annees=annees, films=[cle_film(f) for f in choisis])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.n = len(m["ordre"])
        self.reponses, self.fracs, self.gains, self.justes = {}, {}, {}, {}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        if pid in self.reponses:
            return {"ok": False, "msg": "Frise déjà envoyée"}
        o = d.get("ordre")
        if not isinstance(o, list) or sorted(o) != list(range(self.n)) or any(type(x) is not int for x in o):
            return {"ok": False, "msg": "Touchez tous les films, dans l'ordre demandé"}
        self.reponses[pid], self.fracs[pid] = list(o), frac
        self.p.joueurs[pid].essais = 1
        return {"ok": True, "msg": "Frise accrochée !"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(p in self.reponses for p in J)

    def clore(self):
        bonne = self.m["ordre"]
        for pid, j in self.p.joueurs.items():
            o = self.reponses.get(pid)
            if o is None:
                j.serie = 0
                continue
            justes = [a == b for a, b in zip(o, bonne)]
            self.justes[pid] = justes
            parfait = all(justes)
            jeu = self.m.get("jeu", "nadine")
            gain = self.cfg.get(f"{jeu}_pts", self.cfg["nadine_pts"]) * sum(justes)
            if parfait:
                gain += self.cfg.get(f"{jeu}_parfait", self.cfg["nadine_parfait"]) + int(self.cfg["bonus_vitesse"] * self.fracs.get(pid, 0))
            j.gain += gain
            j.score += gain
            j.trouve = parfait
            j.serie = j.serie + 1 if parfait else 0
            self.gains[pid] = gain

    def duree_revelation(self, base):
        return base + 4                       # le temps que les affiches glissent à leur place

    def statut(self, pid):
        return {"t": "a accroché", "c": "ok"} if pid in self.reponses else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if p in self.reponses)} / {len(J)} ont accroché leur frise"

    def _j(self, pid):
        j = self.p.joueurs.get(pid)
        return j.public() if j else None

    def vue(self, pid, revele):
        v = {"n": self.n}
        if pid:
            v.update(ma_reponse=self.reponses.get(pid), actif=pid not in self.reponses and not revele and not self.p.pause)
        if revele:
            v.update(ordre=self.m["ordre"], annees=self.m["annees"],
                     resultats=sorted([dict(self._j(p), justes=sum(self.justes.get(p, [])), gain=self.gains.get(p, 0),
                                            reponse=self.reponses.get(p), parfait=all(self.justes.get(p, [False])))
                                       for p in self.p.joueurs], key=lambda x: -x["gain"]))
            if pid:
                v["mes_justes"] = self.justes.get(pid)
        return v
