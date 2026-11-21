"""Windom Earle's Chess Clock (La pendule) : Windom Earle joue aux échecs contre Cooper, et chaque coup peut tuer.
Une partie de blitz : l'écran montre un film de départ ; à tour de rôle, chacun cite un film qui a un lien avec le
précédent : un acteur, le réalisateur, le compositeur, le scénariste, le directeur de la photographie ou la même
année de sortie. Le lien doit changer à chaque coup (pas Brad Pitt puis encore Brad Pitt), un même lien ne sert que
trois fois, un film ne sert qu'une fois et une saga aussi (un seul film par saga). Chacun a sa pendule d'échecs
(40 s pour toute la partie), qui ne tourne que pendant son tour ; répondre en moins de 10 s rend 5 s. Quand la
pendule tombe : échec et mat. Le dernier en lice gagne. Le coup d'avance : choisir un film qui coince le suivant.
"""
import random

import sagas
from tmdb import cle_film, fiche, libelle
from .contraintes import entrees_films, index, resoudre, suggerer_films

LIENS = (("acteurs", "acteur", 15), ("realisateurs", "réalisateur", 3), ("compositeurs", "compositeur", 3),
         ("scenaristes", "scénariste", 4), ("chefs_op", "directeur photo", 2))


def liens(fi):
    """{(type, id): libellé} des liens possibles d'un film (et son année)."""
    out = {}
    for champ, nom, n in LIENS:
        for x in (fi.get(champ) or [])[:n]:
            out[(nom, x["id"])] = x["nom"]
    if fi.get("annee"):
        out[("année", fi["annee"])] = f"Sorti en {fi['annee']}"
    return out


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    if len(films) < 5:
        raise RuntimeError("La pendule : pas assez de films dans les listes choisies.")
    films.sort(key=lambda f: -(f.get("votes") or 0))
    connus = films[:max(10, len(films) // 4)]
    random.shuffle(connus)
    depart = next((f for f in connus if cle_film(f) not in deja), connus[0])
    try:
        fi = fiche(api, depart)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"La pendule : film de départ illisible ({e})")
    from PIL import ImageOps
    from visuels import en_jpeg
    from .commun import affiche
    img = en_jpeg(ImageOps.fit(affiche(api, depart, "w342"), (240, 360)), 360)
    duree = float(cfg.get("dur_windom", 420))
    return dict(jeu="windom", vue="pendule", duree=duree, reponse="pendule", etapes=[(0.0, {"cachees": [0]})],
                images=[img], revelation=None, cles=[], bonne="", solution="Échec et mat", detail="",
                films=[cle_film(depart)], depart=depart, depart_fiche=fi, api=api, films_pool=pool, suggestions=True)


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.ordre = list(partie.joueurs)
        random.shuffle(self.ordre)
        T = float(cfg.get("windom_temps", 40))
        self.temps = {p: T for p in self.ordre}
        self.mats = []                                  # éliminés, dans l'ordre
        self.tour, self.debut = 0, float(m.get("t0", 3.0))
        d = m["depart"]
        self.chaine = [{"film": d, "fiche": m["depart_fiche"], "lien": None, "qui": None, "img": 0}]
        self.usages = {}                                # lien -> nombre d'utilisations
        self.coups = {}                                 # pid -> films cités
        self.gains = {}
        self.idx = index(list(m.get("films_pool", [])))
        self.entrees = entrees_films([f for f, _ in self.idx])

    def ok(self):
        return ""

    # ---- la pendule
    def _vivants(self):
        return [p for p in self.ordre if p in self.p.joueurs and p not in self.mats]

    def _actif(self):
        v = self._vivants()
        return v[self.tour % len(v)] if v else None

    def _ecoule_tour(self):
        return max(0.0, self.p.ecoule - self.debut)

    def _reste(self, pid):
        t = self.temps.get(pid, 0)
        return t - self._ecoule_tour() if pid == self._actif() else t

    def _maj(self):
        while True:
            a = self._actif()
            if a is None or len(self._vivants()) <= (1 if len(self.ordre) > 1 else 0):
                return
            if self._reste(a) > 0:
                return
            # la pendule tombe : mat ; le suivant joue à partir du moment où elle est tombée
            self.debut = self.debut + self.temps.get(a, 0)
            self.temps[a] = 0
            v = self._vivants()
            k = v.index(a)
            self.mats.append(a)
            v2 = self._vivants()
            self.tour = k % len(v2) if v2 else 0

    def resoudre(self, d):
        return resoudre(self.m["api"], d.get("texte"), self.idx, True)

    def suggerer(self, q):
        return suggerer_films(self.m["api"], q, self.entrees)

    def action(self, pid, d, frac, info=None):
        self._maj()
        if pid != self._actif():
            return {"ok": False, "msg": "Échec et mat" if pid in self.mats else "Ce n'est pas votre tour"}
        f = (info or {}).get("film")
        if not f:
            return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
        if f.get("tv"):
            return {"ok": False, "msg": "Un film, pas une série"}
        fi = (info or {}).get("fiche")
        if not fi:
            try:
                fi = fiche(self.m["api"], f)
            except Exception:  # noqa: BLE001
                return {"ok": False, "msg": "Film illisible, essayez-en un autre"}
        if any(cle_film(c["film"]) == cle_film(f) for c in self.chaine):
            return {"ok": False, "msg": f"{libelle(f)} a déjà été joué"}
        if any(sagas.meme_univers(c["film"], f) for c in self.chaine):
            return {"ok": False, "msg": "Un seul film par saga"}
        prec = self.chaine[-1]
        communs = set(liens(prec["fiche"])) & set(liens(fi))
        if not communs:
            return {"ok": False, "msg": f"Aucun lien entre {libelle(f)} et {prec['film']['title']}"}
        dernier = prec["lien"]["k"] if prec["lien"] else None
        maxi = int(self.cfg.get("windom_max_lien", 3))
        permis = [k for k in communs if k != dernier and self.usages.get(k, 0) < maxi]
        if not permis:
            raison = "le même lien que le coup d'avant" if dernier in communs else f"un lien déjà utilisé {maxi} fois"
            return {"ok": False, "msg": f"Refusé : {raison}"}
        k = min(permis, key=lambda x: (x[0] == "année", self.usages.get(x, 0), random.random()))
        nom = liens(fi)[k]
        self.usages[k] = self.usages.get(k, 0) + 1
        t = self._ecoule_tour()
        self.temps[pid] -= t
        bonus = t < float(self.cfg.get("windom_rapide", 10))
        if bonus:
            self.temps[pid] += float(self.cfg.get("windom_bonus", 5))
        self.chaine.append({"film": f, "fiche": fi, "lien": {"k": k, "type": k[0], "nom": nom}, "qui": pid, "img": None})
        self.coups[pid] = self.coups.get(pid, 0) + 1
        self.tour += 1
        self.debut = self.p.ecoule
        return {"ok": True, "correct": True, "msg": f"✓ {libelle(f)} — {nom if k[0] == 'année' else k[0] + ' : ' + nom}"
                + (" · +5 s" if bonus else "")}

    def fini(self):
        self._maj()
        v = self._vivants()
        return len(v) == 0 or (len(self.ordre) > 1 and len(v) <= 1)

    def clore(self):
        self._maj()
        rang = self._vivants() + list(reversed(self.mats))
        pts = int(self.cfg.get("windom_pts", 1000))
        for i, pid in enumerate(rang):
            j = self.p.joueurs.get(pid)
            if not j:
                continue
            gain = (pts >> i if i < 6 else 0) + int(self.cfg.get("windom_film", 50)) * self.coups.get(pid, 0)
            if len(self.ordre) > 1 and i == len(rang) - 1:
                gain = int(self.cfg.get("windom_film", 50)) * self.coups.get(pid, 0)
            self.gains[pid] = gain
            j.gain += gain
            j.score += gain
            j.trouve = i == 0
            j.serie = j.serie + 1 if j.trouve else 0

    def statut(self, pid):
        if pid in self.mats:
            return {"t": "mat", "c": "ko"}
        return {"t": f"{max(0, round(self._reste(pid)))} s", "c": "ok" if pid == self._actif() else ""}

    def avancement(self):
        a = self.p.joueurs.get(self._actif())
        return f"Au tour de {a.nom}" if a else ""

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        a = self._actif()
        chaine = [{"titre": c["film"]["title"], "annee": (c["film"].get("release_date") or "")[:4], "img": c["img"],
                   "lien": {"type": c["lien"]["type"], "nom": c["lien"]["nom"]} if c["lien"] else None,
                   "qui": J[c["qui"]].public() if c["qui"] in J else None} for c in self.chaine]
        dernier = self.chaine[-1]["lien"]
        v = {"chaine": chaine[-8:], "n": len(chaine),
             "pendules": [dict(J[p].public(), reste=round(max(0.0, self._reste(p)), 1), mat=p in self.mats,
                               actif=p == a and not revele, coups=self.coups.get(p, 0)) for p in self.ordre if p in J],
             "interdit": dernier["nom"] if dernier else "", "temps": float(self.cfg.get("windom_temps", 40))}
        if pid:
            v.update(mon_tour=pid == a and not revele, mat=pid in self.mats,
                     actif=not revele and not self.p.pause and pid == a)
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0), coups=self.coups.get(p, 0),
                                          mat=p in self.mats) for p in J], key=lambda x: -x["gain"])
        return v
