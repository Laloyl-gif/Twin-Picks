"""Desmond's Code (Le code) : l'agent Chet Desmond décode les messages (la danse de Lil). À chaque manche, un joueur
est le donneur (chacun son tour). Une grille de 16 affiches ; sur son téléphone, le donneur voit le code couleur :
des films à faire deviner (en or), des films rouges, un film noir, le reste neutre. Les règles suivent Codenames :
- le donneur envoie un indice (un ou plusieurs mots) et un nombre ;
- chacun des autres touche, sur son téléphone, des films de la grille, un par un (au plus nombre + 1) ;
- un film en or : des points pour lui et pour le donneur, il peut continuer ;
- un film neutre ou rouge : son tour s'arrête (rouge : malus pour le donneur) ; il peut aussi s'arrêter de lui-même ;
- le film noir : il est éliminé de la manche, avec un gros malus pour lui et pour le donneur ;
- quand tout le monde a fini, le donneur envoie l'indice suivant, jusqu'à ce que les films en or soient trouvés ou que
  le temps soit écoulé.
"""
import random
import re

from PIL import ImageOps

import sagas
from texte import normaliser
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche

NB = 16
MOTS_MAX = 4


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
    x = max(2, min(9, int(cfg.get("desmond_or", 6))))
    rouges = max(0, min(NB - x - 2, int(cfg.get("desmond_rouges", 4))))
    roles = ["or"] * x + ["rouge"] * rouges + ["noir"] + ["neutre"] * (NB - x - rouges - 1)
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
        self.indices = []                                   # [{"mot", "n", "t"}]
        self.vus = {}                                       # pid -> [cases touchées, dans l'ordre]
        self.tour = {}                                      # pid -> {"k": n° d'indice, "n": films touchés, "fin": bool}
        self.elimines = set()
        self.gains = {}

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le code se joue à 2 joueurs minimum (un donneur, des devineurs)."
        return ""

    def _devineurs(self):
        return [p for p in self.p.joueurs if p != self.donneur]

    def _ors(self):
        return {i for i, r in enumerate(self.m["roles"]) if r == "or"}

    def _tout_trouve(self, pid):
        return self._ors() <= set(self.vus.get(pid, []))

    def _en_jeu(self, pid):
        return pid not in self.elimines and not self._tout_trouve(pid)

    def _a_fini(self, pid):
        """Le devineur a fini pour l'indice en cours."""
        if not self._en_jeu(pid):
            return True
        t = self.tour.get(pid)
        return not self.indices or (t and t["k"] == len(self.indices) - 1 and t["fin"])

    def _peut_relancer(self):
        if not self.indices:
            return True
        attente = self.p.ecoule - self.indices[-1]["t"]
        return all(self._a_fini(p) for p in self._devineurs()) or attente >= float(self.cfg.get("desmond_attente", 25))

    def action(self, pid, d, frac, info=None):
        if pid == self.donneur:
            if d.get("terminer"):
                if not self.indices:
                    return {"ok": False, "msg": "Donnez au moins un indice"}
                self.fin_demandee = True
                return {"ok": True, "msg": "Fin de la manche"}
            mot = " ".join(str(d.get("texte") or "").split())
            try:
                n = int(d.get("n") or 0)
            except (TypeError, ValueError):
                n = 0
            if not self._peut_relancer():
                return {"ok": False, "msg": "Les autres cherchent encore…"}
            if not mot or len(mot.split()) > MOTS_MAX or len(mot) > 40:
                return {"ok": False, "msg": f"Un indice de 1 à {MOTS_MAX} mots"}
            if not 1 <= n <= len(self._ors()):
                return {"ok": False, "msg": "Choisissez le nombre de films"}
            for w in normaliser(mot).split():
                for t in self.m["titres"]:
                    nt = normaliser(t)
                    if w in nt.split() or (len(w) > 3 and w in nt):
                        return {"ok": False, "msg": f"« {w} » est dans un titre de la grille"}
            self.indices.append({"mot": mot, "n": n, "t": self.p.ecoule})
            k = len(self.indices) - 1
            for p in self._devineurs():
                self.tour[p] = {"k": k, "n": 0, "fin": False}
            return {"ok": True, "msg": "Indice envoyé"}
        if not self.indices:
            return {"ok": False, "msg": "Attendez l'indice du donneur"}
        if pid in self.elimines:
            return {"ok": False, "msg": "Éliminé par le film noir"}
        t = self.tour.setdefault(pid, {"k": len(self.indices) - 1, "n": 0, "fin": False})
        if t["fin"]:
            return {"ok": False, "msg": "Attendez l'indice suivant"}
        if d.get("stop"):
            t["fin"] = True
            return {"ok": True, "msg": "Vous passez la main"}
        i = d.get("i")
        mes = self.vus.setdefault(pid, [])
        if type(i) is not int or not 0 <= i < NB or i in mes:
            return {"ok": False, "msg": "Touchez un autre film"}
        mes.append(i)
        t["n"] += 1
        r = self.m["roles"][i]
        n = self.indices[t["k"]]["n"]
        if r == "noir":
            self.elimines.add(pid)
            t["fin"] = True
            return {"ok": True, "correct": False, "msg": "Le film noir ! Éliminé"}
        if r != "or":
            t["fin"] = True
            return {"ok": True, "correct": False, "msg": "Film rouge : tour fini" if r == "rouge" else "Film neutre : tour fini"}
        if self._tout_trouve(pid):
            t["fin"] = True
            return {"ok": True, "correct": True, "msg": "Tous les films en or !"}
        if t["n"] >= n + 1:
            t["fin"] = True
            return {"ok": True, "correct": True, "msg": "Bon film ! (plus d'essai pour cet indice)"}
        return {"ok": True, "correct": True, "msg": f"Bon film ! Encore {n + 1 - t['n']} essai{'s' if n - t['n'] else ''} au plus"}

    def fini(self):
        dv = self._devineurs()
        if not dv:
            return False
        if getattr(self, "fin_demandee", False) and all(self._a_fini(p) for p in dv):
            return True
        return bool(self.indices) and all(not self._en_jeu(p) for p in dv)

    def clore(self):
        c = self.cfg
        roles = self.m["roles"]
        bilan = {p: 0 for p in self.p.joueurs}
        if not self.indices and self.donneur in bilan:
            bilan[self.donneur] -= int(c["desmond_noir"])          # pas d'indice donné : le donneur paie
        for pid, mes in self.vus.items():
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

    def _n_or(self, pid):
        return len(self._ors() & set(self.vus.get(pid, [])))

    def statut(self, pid):
        if pid == self.donneur:
            return {"t": "donneur", "c": "ok" if self.indices else ""}
        if pid in self.elimines:
            return {"t": "éliminé", "c": "ko"}
        n = self._n_or(pid)
        return {"t": f"{n}/{self.m['x']}", "c": "ok" if n >= self.m["x"] else ""} if n else {"t": "", "c": ""}

    def avancement(self):
        d = self.p.joueurs.get(self.donneur)
        if not self.indices:
            return f"{d.nom if d else '?'} cherche un indice…"
        dv = self._devineurs()
        if all(self._a_fini(p) for p in dv):
            return f"{d.nom if d else '?'} prépare l'indice suivant…"
        return f"{sum(1 for p in dv if self._a_fini(p))} / {len(dv)} ont fini pour cet indice"

    def vue(self, pid, revele):
        J = self.p.joueurs
        dj = J.get(self.donneur)
        v = {"cases": [{"img": i, "txt": t} for i, t in enumerate(self.m["titres"])], "x": self.m["x"],
             "indices": [{"mot": x["mot"], "n": x["n"]} for x in self.indices],
             "indice": self.indices[-1]["mot"] if self.indices else "", "nb": self.indices[-1]["n"] if self.indices else 0,
             "donneur": dj.public() if dj else None,
             "avance": [dict(J[p].public(), n=self._n_or(p), elimine=p in self.elimines, fini=self._a_fini(p))
                        for p in self._devineurs()]}
        if pid:
            moi_d = pid == self.donneur
            t = self.tour.get(pid) or {}
            mes = self.vus.get(pid, [])
            v.update(donneur_moi=moi_d, roles=self.m["roles"] if moi_d or revele else None,
                     mes=mes, mes_roles=[self.m["roles"][i] for i in mes], elimine=pid in self.elimines,
                     essais=(self.indices[t["k"]]["n"] + 1 - t["n"]) if t and self.indices and not t.get("fin") else 0,
                     peut_relancer=moi_d and self._peut_relancer(), reste_or=len(self._ors()),
                     actif=not revele and not self.p.pause and (self._peut_relancer() if moi_d else
                                                               bool(self.indices) and not self._a_fini(pid)))
        if revele:
            touches = {}
            for p, mes in self.vus.items():
                for i in mes:
                    touches.setdefault(i, []).append(J[p].public() if p in J else None)
            v.update(roles=self.m["roles"], touches=touches,
                     resultats=sorted([dict(J[p].public(), gain=self.gains.get(p, 0), donneur=p == self.donneur) for p in J],
                                      key=lambda x: -x["gain"]))
        return v
