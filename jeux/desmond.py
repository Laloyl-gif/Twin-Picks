"""Desmond's Code (Le code) : l'agent Chet Desmond décode les messages (la danse de Lil). À chaque manche, un joueur
est le donneur (chacun son tour). Une grille de 16 affiches ; sur son téléphone, le donneur voit le code couleur :
X films à faire deviner (en or), trois films rouges, un film noir, le reste neutre. Il tape un seul mot ; les autres
touchent, chacun de son côté, X films de la grille, un par un. Un bon film : des points pour celui qui l'a touché et
pour le donneur. Un film rouge : malus pour le donneur. Le film noir : gros malus pour le donneur et pour celui qui
l'a touché. La manche s'arrête quand tout le monde a fini.
"""
import random
import re

from PIL import ImageOps

import sagas
from texte import normaliser
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche

NB, ROUGES = 16, 3


def construire(api, cfg, pool, deja):
    films = [f for f in pool if f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    choisis = []
    for f in films:
        if not any(f["id"] == g["id"] or sagas.meme_univers(f, g) for g in choisis):
            choisis.append(f)
        if len(choisis) == NB:
            break
    if len(choisis) < NB:
        raise RuntimeError("Le code : pas assez de films dans les listes choisies.")
    for f in choisis:
        deja.add(cle_film(f))
    x = random.randint(int(cfg["desmond_min"]), int(cfg["desmond_max"]))
    roles = ["or"] * x + ["rouge"] * ROUGES + ["noir"] + ["neutre"] * (NB - x - ROUGES - 1)
    random.shuffle(roles)
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (240, 360)), 360) for f in choisis]
    return dict(jeu="desmond", vue="code", duree=float(cfg["dur_desmond"]), reponse="code",
                etapes=[(0.0, {"cachees": list(range(NB))})], images=images, revelation=None, cles=[], bonne="",
                titres=[f["title"] for f in choisis], roles=roles, x=x, solution="Le code de Desmond", detail="",
                films=[cle_film(f) for f in choisis])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        ids = list(partie.joueurs)
        self.donneur = ids[partie.index % len(ids)] if ids else None
        self.indice, self.debut_devine = "", None
        self.choix = {}                                     # pid -> [cases touchées]
        self.gains = {}

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le code se joue à 2 joueurs minimum (un donneur, des devineurs)."
        return ""

    def _devineurs(self):
        return [p for p in self.p.joueurs if p != self.donneur]

    def action(self, pid, d, frac, info=None):
        if pid == self.donneur:
            if self.indice:
                return {"ok": False, "msg": "Indice déjà donné"}
            mot = " ".join(str(d.get("texte") or "").split())
            if not mot or len(mot.split()) > 1 or len(mot) > 24:
                return {"ok": False, "msg": "Un seul mot !"}
            n = normaliser(mot)
            for t in self.m["titres"]:
                if n in normaliser(t).split() or (len(n) > 3 and n in normaliser(t)):
                    return {"ok": False, "msg": "Ce mot est dans un titre de la grille"}
            self.indice = mot
            self.debut_devine = self.p.ecoule
            return {"ok": True, "msg": "Indice envoyé"}
        if not self.indice:
            return {"ok": False, "msg": "Attendez l'indice du donneur"}
        i = d.get("i")
        mes = self.choix.setdefault(pid, [])
        if type(i) is not int or not 0 <= i < NB or i in mes:
            return {"ok": False, "msg": "Touchez un autre film"}
        if len(mes) >= self.m["x"]:
            return {"ok": False, "msg": "Vous avez fini"}
        mes.append(i)
        r = self.m["roles"][i]
        if len(mes) >= self.m["x"]:
            self.p.joueurs[pid].essais = 1
        return {"ok": True, "correct": r == "or", "msg": {"or": "Bon film !", "rouge": "Film rouge…", "noir": "Le film noir !",
                                                          "neutre": "Film neutre"}[r]}

    def fini(self):
        dv = self._devineurs()
        return bool(self.indice) and bool(dv) and all(len(self.choix.get(p, [])) >= self.m["x"] for p in dv)

    def clore(self):
        c = self.cfg
        roles = self.m["roles"]
        bilan = {p: 0 for p in self.p.joueurs}
        if not self.indice and self.donneur in bilan:
            bilan[self.donneur] -= int(c["desmond_noir"])          # pas d'indice donné : le donneur paie
        for pid, mes in self.choix.items():
            if pid not in bilan:
                continue
            for i in mes:
                r = roles[i]
                if r == "or":
                    bilan[pid] += int(c["desmond_pts"])
                    if self.donneur in bilan:
                        bilan[self.donneur] += int(c["desmond_donneur"])
                elif r == "rouge" and self.donneur in bilan:
                    bilan[self.donneur] -= int(c["desmond_rouge"])
                elif r == "noir":
                    bilan[pid] -= int(c["desmond_noir"])
                    if self.donneur in bilan:
                        bilan[self.donneur] -= int(c["desmond_noir"])
        for pid, j in self.p.joueurs.items():
            gain = max(bilan.get(pid, 0), -j.score)
            j.gain += gain
            j.score += gain
            j.trouve = gain > 0
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        if pid == self.donneur:
            return {"t": "donneur", "c": "ok" if self.indice else ""}
        n = len(self.choix.get(pid, []))
        return {"t": f"{n}/{self.m['x']}", "c": "ok" if n >= self.m["x"] else ""} if n else {"t": "", "c": ""}

    def avancement(self):
        d = self.p.joueurs.get(self.donneur)
        if not self.indice:
            return f"{d.nom if d else '?'} cherche un mot…"
        dv = self._devineurs()
        return f"{sum(1 for p in dv if len(self.choix.get(p, [])) >= self.m['x'])} / {len(dv)} ont fini"

    def vue(self, pid, revele):
        J = self.p.joueurs
        dj = J.get(self.donneur)
        v = {"cases": [{"img": i, "txt": t} for i, t in enumerate(self.m["titres"])], "x": self.m["x"], "indice": self.indice,
             "donneur": dj.public() if dj else None,
             "avance": [dict(J[p].public(), n=len(self.choix.get(p, []))) for p in self._devineurs()]}
        if pid:
            moi_d = pid == self.donneur
            v.update(donneur_moi=moi_d, roles=self.m["roles"] if moi_d or revele else None,
                     mes=self.choix.get(pid, []), mes_roles=[self.m["roles"][i] for i in self.choix.get(pid, [])],
                     actif=not revele and not self.p.pause and (not self.indice if moi_d else
                                                               bool(self.indice) and len(self.choix.get(pid, [])) < self.m["x"]))
        if revele:
            touches = {}
            for p, mes in self.choix.items():
                for i in mes:
                    touches.setdefault(i, []).append(J[p].public() if p in J else None)
            v.update(roles=self.m["roles"], touches=touches,
                     resultats=sorted([dict(J[p].public(), gain=self.gains.get(p, 0), donneur=p == self.donneur) for p in J],
                                      key=lambda x: -x["gain"]))
        return v
