"""Hank's Dominoes (Les dominos de Hank), façon Focus. Une grille de films sur des dominos (cinq par joueur : dix à
deux, quinze à trois…, jamais deux films d'une même saga). Chaque joueur reçoit en secret un film de la grille.
À tour de rôle, le joueur actif retire de la grille un film proche du sien : c'est son indice. À tout moment, chacun
peut deviner le film d'un autre joueur (une fois par joueur) : moins le joueur visé a donné d'indices, plus ça
rapporte, et celui dont le film est trouvé marque aussi. On devine en touchant le nom d'un joueur puis un film, même
pendant son propre tour. Retirer le film d'un autre joueur, c'est perdre : gros malus, et la manche s'arrête net.
"""
import random
import time

from PIL import ImageOps

import sagas
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche

NMAX = 24


def construire(api, cfg, pool, deja):
    films = [f for f in pool if f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    choisis = []
    for f in films:
        if not any(f["id"] == g["id"] or sagas.meme_univers(f, g) for g in choisis):
            choisis.append(f)
        if len(choisis) == NMAX:
            break
    if len(choisis) < 10:
        raise RuntimeError("Les dominos de Hank : pas assez de films (hors sagas) dans les listes choisies.")
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (240, 360)), 360) for f in choisis]
    titres = [f["title"] for f in choisis]
    etat = {"cachees": list(range(len(choisis)))}
    return dict(jeu="hank", vue="focus", duree=float(cfg["dur_hank"]), reponse="focus", etapes=[(0.0, etat)],
                images=images, revelation=None, cles=[], bonne="", titres=titres,
                solution="Les films de chacun", detail="", films=[cle_film(f) for f in choisis])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.ordre = list(partie.joueurs)
        random.shuffle(self.ordre)
        n = min(len(m["titres"]), max(10, 5 * len(self.ordre)))
        self.grille = list(range(n))
        secrets = random.sample(self.grille, min(n, len(self.ordre)))
        self.secret = dict(zip(self.ordre, secrets))
        self.retires = []                       # [(film, pid)]
        self.devines = {}                       # (devin, cible) -> (film proposé, juste, points)
        self.devoiles = set()                   # cibles dont le film a été retiré par un autre
        self.perdant = None                     # qui a retiré le film d'un autre : la manche s'arrête
        self.tour, self.debut_tour = 0, 0.0
        self.gains = {}

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Les dominos de Hank se jouent à 2 joueurs minimum."
        return ""

    # ---- tour de jeu
    def _actif(self):
        if not self.ordre:
            return None
        return self.ordre[self.tour % len(self.ordre)]

    def _reste_tour(self):
        return float(self.cfg["hank_tour"]) - (self.p.ecoule - self.debut_tour)

    def _avancer(self):
        self.tour += 1
        self.debut_tour = self.p.ecoule

    def _maj(self):
        if self.ordre and self._reste_tour() <= 0:          # temps écoulé : au suivant
            self._avancer()

    def _retirables(self):
        pris = {f for f, _ in self.retires}
        return [f for f in self.grille if f not in pris]

    def _indices(self, pid):
        return sum(1 for _, q in self.retires if q == pid)

    def _gagner(self, pid, n):
        j = self.p.joueurs.get(pid)
        if j:
            j.gain += n
            j.score += n
            self.gains[pid] = self.gains.get(pid, 0) + n

    def action(self, pid, d, frac, info=None):
        self._maj()
        if self.perdant:
            return {"ok": False, "msg": "La manche est finie"}
        if "retirer" in d:
            if pid != self._actif():
                return {"ok": False, "msg": "Ce n'est pas votre tour"}
            f = d.get("retirer")
            if type(f) is not int or f not in self._retirables():
                return {"ok": False, "msg": "Choisissez un film de la grille"}
            if f == self.secret.get(pid):
                return {"ok": False, "msg": "C'est votre film ! Retirez-en un autre, proche du vôtre"}
            self.retires.append((f, pid))
            victime = next((q for q, s in self.secret.items() if s == f), None)
            self._avancer()
            if victime:
                self.devoiles.add(victime)
                self.perdant = (pid, victime)
                self._gagner(pid, -int(self.cfg["hank_retire"]))
                nom = self.p.joueurs[victime].nom if victime in self.p.joueurs else "un autre joueur"
                return {"ok": True, "correct": False, "msg": f"Perdu : c'était le film de {nom} ! La manche s'arrête"}
            return {"ok": True, "msg": "Domino retiré"}
        cible, f = d.get("cible"), d.get("i")
        # le téléphone ne connaît que l'identifiant public des joueurs
        cible = next((q for q in self.secret if q in self.p.joueurs and self.p.joueurs[q].id == cible), cible)
        if cible not in self.secret or cible == pid or type(f) is not int or f not in self.grille:
            return {"ok": False, "msg": "Choisissez un joueur, puis un film"}
        if (pid, cible) in self.devines:
            return {"ok": False, "msg": "Vous avez déjà deviné ce joueur"}
        if cible in self.devoiles:
            return {"ok": False, "msg": "Son film est déjà dévoilé"}
        juste = self.secret[cible] == f
        if juste:
            pts = max(int(self.cfg["hank_mini"]), int(self.cfg["hank_pts"]) - int(self.cfg["hank_pas"]) * self._indices(cible))
            self._gagner(pid, pts)
            self._gagner(cible, int(self.cfg["hank_cible"]))
        else:
            pts = -int(self.cfg["hank_erreur"])
            self._gagner(pid, pts)
        self.devines[(pid, cible)] = (f, juste, pts)
        nom = self.p.joueurs[cible].nom if cible in self.p.joueurs else "?"
        return {"ok": True, "correct": juste, "msg": f"Bien vu : c'est le film de {nom} ! +{pts}" if juste else f"Raté ({pts})"}

    def _resolu(self, pid):
        return all((pid, c) in self.devines or c in self.devoiles for c in self.secret if c != pid)

    def fini(self):
        self._maj()
        if self.perdant:
            return True
        J = self.p.joueurs
        secrets = set(self.secret.values())
        plus_rien = not [f for f in self._retirables() if f not in secrets]
        return bool(J) and (all(self._resolu(p) for p in J if p in self.secret) or (plus_rien and self._reste_tour() < 0))

    def clore(self):
        for pid, j in self.p.joueurs.items():
            g = self.gains.get(pid, 0)
            j.trouve = any(ok for (a, _), (_, ok, _) in self.devines.items() if a == pid)
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = g

    def statut(self, pid):
        n = sum(1 for (a, _), (_, ok, _) in self.devines.items() if a == pid and ok)
        return {"t": f"{n} trouvé{'s' if n > 1 else ''}", "c": "ok"} if n else {"t": "", "c": ""}

    def avancement(self):
        a = self.p.joueurs.get(self._actif())
        return f"Au tour de {a.nom}" if a else ""

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        retires = {f: q for f, q in self.retires}
        cases = [{"img": f, "txt": self.m["titres"][f], "retire": f in retires,
                  "par": J[retires[f]].public() if f in retires and retires[f] in J else None} for f in self.grille]
        joueurs = [dict(J[q].public(), indices=self._indices(q), devoile=q in self.devoiles,
                        actif=q == self._actif(), film=self.secret[q] if revele or q in self.devoiles else None)
                   for q in self.ordre if q in J]
        v = {"cases": cases, "joueurs": joueurs, "reste_tour": max(0, round(self._reste_tour(), 1)),
             "dur_tour": float(self.cfg["hank_tour"])}
        if pid:
            v.update(mon_film=self.secret.get(pid), mon_tour=pid == self._actif() and not revele,
                     mes_devines={J[c].id if c in J else c: {"i": f, "ok": ok} for (a, c), (f, ok, _) in self.devines.items() if a == pid},
                     actif=not revele and not self.p.pause)
        if self.perdant:
            a, b = self.perdant
            v["perdant"] = {"qui": J[a].public() if a in J else None, "victime": J[b].public() if b in J else None}
        if revele:
            v["resultats"] = sorted([dict(J[q].public(), gain=self.gains.get(q, 0)) for q in J], key=lambda x: -x["gain"])
        return v
