"""Mike's Shoe Samples (Les paires) : Mike, le manchot, est représentant en chaussures ; il ouvre sa valise
d'échantillons. Quatre boîtes à chaussures portent chacune le nom d'un personnage ; quatre affiches de films. Les
chaussures vont par paires : rendez à chaque personnage son film. Chaque paire juste rapporte des points, les quatre
un bonus (plus tôt = plus). Indice (réglable) : l'acteur qui joue chaque personnage, à mi-temps.
"""
import random
import re

from PIL import ImageOps

import sagas
from texte import normaliser
from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie

NB = 4
GENERIQUES = {"himself", "herself", "narrator", "voice", "man", "woman", "boy", "girl", "doctor", "nurse", "cop",
              "police officer", "reporter", "waiter", "waitress", "bartender", "driver", "soldier", "guard", "host",
              "self", "lui-meme", "elle-meme", "narrateur", "uncredited", "dancer", "singer", "student", "teacher"}


def personnage(film, fi):
    """Le personnage principal du film (nettoyé), ou "" s'il est inutilisable (générique, ou porte le titre)."""
    titre = {normaliser(m) for m in re.findall(r"\w+", film["title"] + " " + (film.get("original_title") or "")) if len(m) > 2}
    for a in fi.get("acteurs", [])[:2]:
        r = re.sub(r"\(.*?\)", "", (a.get("role") or "").split("/")[0]).strip(" .'\"")
        n = normaliser(r)
        if not r or len(r) > 28 or n in GENERIQUES or any(g in n.split() for g in ("himself", "herself", "voice")):
            continue
        if set(n.split()) & titre:                                  # « Rocky » dans Rocky : trop facile
            continue
        return r, a.get("nom", "")
    return "", ""


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_mike"])
    films = [f for f in pool if f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    choisis = []
    for f in films[:60]:
        if any(sagas.meme_univers(f, g) for g, _, _ in choisis):
            continue
        try:
            r, acteur = personnage(f, fiche(api, f))
        except Exception:  # noqa: BLE001
            continue
        if r and all(normaliser(r) != normaliser(x) for _, x, _ in choisis):
            choisis.append((f, r, acteur))
        if len(choisis) == NB:
            break
    if len(choisis) < NB:
        raise RuntimeError("Les paires : pas assez de personnages connus dans les listes choisies.")
    for f, _, _ in choisis:
        deja.add(cle_film(f))
    ordre = random.sample(range(NB), NB)              # boîte k -> le film ordre[k] (les affiches restent dans l'ordre)
    while ordre == list(range(NB)):
        random.shuffle(ordre)
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f, _, _ in choisis]
    boites = [{"nom": choisis[ordre[k]][1], "acteur": ""} for k in range(NB)]
    etat = {"items": [{"img": i, "txt": f["title"]} for i, (f, _, _) in enumerate(choisis)], "boites": boites,
            "indices": []}
    evts = []
    if cfg.get("mike_indice", True):
        evts.append((duree * 0.5, lambda: [b.update(acteur=choisis[ordre[k]][2]) for k, b in enumerate(boites)]))
    etapes = chronologie(evts, lambda: {**etat, "boites": [dict(b) for b in etat["boites"]], "indices": list(etat["indices"])})
    return dict(jeu="mike", vue="paires", duree=duree, reponse="paires", etapes=etapes, images=images, revelation=None,
                cles=[], bonne="", ordre=ordre, solution="Chaque personnage dans son film",
                detail=" · ".join(f"{choisis[ordre[k]][1]} : {choisis[ordre[k]][0]['title']}" for k in range(NB)),
                films=[cle_film(f) for f, _, _ in choisis])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.reponses, self.fracs, self.gains, self.justes = {}, {}, {}, {}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        if pid in self.reponses:
            return {"ok": False, "msg": "Paires déjà envoyées"}
        r = d.get("paires")
        if not isinstance(r, list) or sorted(r) != list(range(NB)) or any(type(x) is not int for x in r):
            return {"ok": False, "msg": "Donnez un film à chaque personnage"}
        self.reponses[pid], self.fracs[pid] = list(r), frac
        self.p.joueurs[pid].essais = 1
        return {"ok": True, "msg": "Paires envoyées !"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(p in self.reponses for p in J)

    def clore(self):
        bonne = self.m["ordre"]
        for pid, j in self.p.joueurs.items():
            r = self.reponses.get(pid)
            if r is None:
                j.serie = 0
                continue
            justes = [a == b for a, b in zip(r, bonne)]
            self.justes[pid] = justes
            tout = all(justes)
            gain = int(self.cfg["mike_pts"]) * sum(justes)
            if tout:
                gain += int(self.cfg["mike_tous"]) + int(self.cfg["bonus_vitesse"] * self.fracs.get(pid, 0))
            j.gain += gain
            j.score += gain
            j.trouve = tout
            j.serie = j.serie + 1 if tout else 0
            self.gains[pid] = gain

    def statut(self, pid):
        return {"t": "a répondu", "c": "ok"} if pid in self.reponses else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if p in self.reponses)} / {len(J)} ont fait leurs paires"

    def vue(self, pid, revele):
        v = {"n": NB}
        if pid:
            v.update(ma_reponse=self.reponses.get(pid), actif=pid not in self.reponses and not revele and not self.p.pause)
        if revele:
            v.update(ordre=self.m["ordre"],
                     resultats=sorted([dict(self.p.joueurs[p].public(), justes=sum(self.justes.get(p, [])),
                                            gain=self.gains.get(p, 0)) for p in self.p.joueurs], key=lambda x: -x["gain"]))
            if pid:
                v["mes_justes"] = self.justes.get(pid)
        return v
