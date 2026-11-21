"""Jean Renault's Blackjack (Le blackjack) : Jean Renault tient la table de blackjack du One Eyed Jack's. Chaque carte
est un film (son affiche) ; sa valeur, cachée, est sa note TMDB (« Le Parrain » vaut 8,7). Il faut s'approcher de
21 sans dépasser, en demandant une carte ou en restant, sans jamais voir les valeurs : seule la culture ciné aide à
estimer. On mise d'abord ; Jean, le croupier, montre une carte et tire jusqu'à 17. À la fin, les notes se révèlent :
qui bat Jean double sa mise (et gagne quelques points même sans miser) ; qui dépasse 21 ou fait moins que Jean
perd sa mise ; égalité : la mise est rendue.
"""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche

MISES = (0, 100, 250, 500, 1000, 2000)    # on peut miser sans avoir les points : on ne descend jamais sous 0
CARTES_MAX = 5
JEAN_RESTE = 17.0


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path") and (f.get("note") or 0) >= 1
             and (f.get("votes") or 0) >= int(cfg.get("jean_votes", 200))]
    if len(films) < 30:
        films = [f for f in pool if not f.get("tv") and f.get("poster_path") and (f.get("note") or 0) >= 1]
    if len(films) < 20:
        raise RuntimeError("Le blackjack : pas assez de films notés dans les listes choisies.")
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    sabot = []
    for f in films:                                   # pas deux films d'une même saga sur la table
        if not any(sagas.meme_univers(f, g) for g in sabot):
            sabot.append(f)
        if len(sabot) == 60:
            break
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w185"), (160, 240)), 240) for f in sabot]
    cartes = [{"img": i, "txt": f["title"], "v": round(float(f["note"]), 1)} for i, f in enumerate(sabot)]
    dm, dj = float(cfg["jean_dur_mise"]), float(cfg["dur_jean"])
    return dict(jeu="jean", vue="blackjack", duree=dm + dj, reponse="blackjack",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[], bonne="",
                solution="Les cartes de Jean", detail="", films=[cle_film(f) for f in sabot[:12]], cartes=cartes,
                dur_mise=dm)


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.sabot = list(range(len(m["cartes"])))
        random.shuffle(self.sabot)
        self.jean = [self.sabot.pop(), self.sabot.pop()]
        self.mains, self.mises, self.restes = {}, {}, set()
        for pid in partie.joueurs:
            self.mains[pid] = [self.sabot.pop(), self.sabot.pop()]
        self.gains, self.fin_jean = {}, None

    def ok(self):
        return ""

    def _val(self, main):
        return round(sum(self.m["cartes"][i]["v"] for i in main), 1)

    def _etape(self):
        return "mise" if self.p.ecoule < self.m["dur_mise"] and len(self.mises) < len(self.p.joueurs) else "jeu"

    def _main(self, pid):
        if pid not in self.mains:                     # arrivé en cours de manche
            self.mains[pid] = [self.sabot.pop(), self.sabot.pop()] if len(self.sabot) > 2 else []
        return self.mains[pid]

    def action(self, pid, d, frac, info=None):
        if "mise" in d:
            if pid in self.mises:
                return {"ok": False, "msg": "Mise déjà posée"}
            x = d.get("mise")
            if x not in MISES:
                return {"ok": False, "msg": "Mise refusée"}
            self.mises[pid] = x
            return {"ok": True, "msg": f"Mise : {x}" if x else "Pas de mise"}
        if self._etape() == "mise":
            return {"ok": False, "msg": "Misez d'abord"}
        main = self._main(pid)
        if pid in self.restes:
            return {"ok": False, "msg": "Vous êtes resté"}
        if d.get("rester"):
            self.restes.add(pid)
            return {"ok": True, "msg": "Vous restez"}
        if d.get("carte"):
            if not self.sabot:
                self.restes.add(pid)
                return {"ok": False, "msg": "Plus de cartes"}
            main.append(self.sabot.pop())
            if len(main) >= CARTES_MAX:
                self.restes.add(pid)
                return {"ok": True, "msg": "Cinq cartes : vous restez"}
            return {"ok": True, "msg": "Une carte de plus…"}
        return {"ok": False, "msg": ""}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and self._etape() == "jeu" and all(p in self.restes for p in J)

    def _jouer_jean(self):
        if self.fin_jean is None:
            while self._val(self.jean) < JEAN_RESTE and self.sabot and len(self.jean) < CARTES_MAX + 1:
                self.jean.append(self.sabot.pop())
            self.fin_jean = self._val(self.jean)
        return self.fin_jean

    def clore(self):
        vj = self._jouer_jean()
        for pid, j in self.p.joueurs.items():
            v = self._val(self._main(pid))
            mise = self.mises.get(pid, 0)
            if v > 21:
                gain, res = -mise, "saute"
            elif vj > 21 or v > vj:
                gain, res = mise + int(self.cfg["jean_pts"]), "gagne"
            elif v == vj:
                gain, res = 0, "egal"
            else:
                gain, res = -mise, "perd"
            gain = max(gain, -j.score)
            self.gains[pid] = (gain, res)
            j.gain += gain
            j.score += gain
            j.trouve = res == "gagne"
            j.serie = j.serie + 1 if j.trouve else 0

    def statut(self, pid):
        if self._etape() == "mise":
            return {"t": "a misé", "c": "ok"} if pid in self.mises else {"t": "", "c": ""}
        n = len(self.mains.get(pid, []))
        return {"t": f"{n} cartes" + (" · reste" if pid in self.restes else ""), "c": "ok" if pid in self.restes else ""}

    def avancement(self):
        J = self.p.joueurs
        if self._etape() == "mise":
            return f"{len(self.mises)} / {len(J)} ont misé"
        return f"{sum(1 for p in J if p in self.restes)} / {len(J)} restent"

    def _cartes(self, main, montrer):
        return [dict(self.m["cartes"][i], v=self.m["cartes"][i]["v"] if montrer else None) for i in main]

    def vue(self, pid, revele):
        J = self.p.joueurs
        et = self._etape()
        if revele:
            self._jouer_jean()
        v = {"etape": et, "dur_mise": self.m["dur_mise"], "mises_possibles": list(MISES),
             "jean": self._cartes(self.jean, revele) if revele else
             [dict(self.m["cartes"][self.jean[0]], v=None), {"img": None, "txt": "", "v": None}],
             "jean_total": self.fin_jean if revele else None,
             "joueurs": [dict(J[p].public(), mise=self.mises.get(p) if et == "jeu" or revele else None,
                              a_mise=p in self.mises, cartes=self._cartes(self._main(p), revele) if et == "jeu" or revele else [],
                              reste=p in self.restes, total=self._val(self._main(p)) if revele else None,
                              res=self.gains.get(p, (0, ""))[1] if revele else "") for p in J]}
        if pid:
            v.update(ma_mise=self.mises.get(pid), mes_cartes=self._cartes(self._main(pid), revele) if et == "jeu" or revele else [],
                     reste=pid in self.restes, mon_score=J[pid].score if pid in J else 0,
                     actif=not revele and not self.p.pause and (pid not in self.mises if et == "mise" else pid not in self.restes))
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, (0, ""))[0], res=self.gains.get(p, (0, ""))[1],
                                          total=self._val(self._main(p)), mise=self.mises.get(p, 0)) for p in J],
                                    key=lambda x: -x["gain"])
        return v
