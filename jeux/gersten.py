"""Gersten Hayward's Tuning Fork (Le diapason), façon Wavelength : Gersten, la petite pianiste prodige, accorde les
avis. Une jauge entre deux pôles (« Film pour enfants ↔ Film traumatisant », « Navet ↔ Chef-d'œuvre »…). Le
diapason (chacun son tour) voit en secret une cible sur la jauge et tape un film qui, selon lui, tombe pile là. Les
autres placent le curseur sur leur téléphone. Plus on est près, plus on gagne ; le diapason marque la moyenne des
autres. On débat à voix haute : c'est tout le sel du jeu.
"""
import random

from .saisie_film import Saisie, publier

POLES = [("Film pour enfants", "Film traumatisant"), ("Navet", "Chef-d'œuvre"), ("Oublié de tous", "Culte"),
         ("Film d'été", "Film d'hiver"), ("Petit budget", "Superproduction"), ("Feel good", "Déprimant"),
         ("Réaliste", "Complètement barré"), ("À voir seul", "À voir entre potes"), ("Romantique", "Anti-romantique"),
         ("Très bavard", "Presque muet"), ("Lent", "Frénétique"), ("Pour un premier rendez-vous", "Surtout pas en premier rendez-vous"),
         ("Sous-coté", "Surcoté"), ("Film de parents", "Film d'ados"), ("Rassurant", "Flippant"), ("Simple", "Prise de tête"),
         ("Vieillit mal", "Vieillit bien"), ("Bande originale oubliable", "Bande originale culte"), ("Méchant ridicule", "Méchant terrifiant"),
         ("Happy end", "Fin déchirante"), ("Pop-corn", "Film d'auteur"), ("Se regarde en cuisinant", "Exige toute l'attention"),
         ("Kitsch", "Classe"), ("Fait pleurer de rire", "Fait pleurer tout court")]


def construire(api, cfg, pool, deja):
    n = max(1, int(cfg.get("gersten_tours", 2)))
    poles = random.sample(POLES, n)
    tours = [{"g": g, "d": d, "cible": random.randint(8, 92)} for g, d in poles]
    I, P, R = float(cfg.get("gersten_indice", 60)), float(cfg.get("gersten_placer", 30)), 8.0
    return dict(jeu="gersten", vue="diapason", duree=round(n * (I + P + R) + 3, 1), reponse="diapason",
                etapes=[(0.0, {})], images=[], revelation=None, cles=[], bonne="", solution="Le diapason",
                detail="", films=[], tours=tours, dur_indice=I, dur_placer=P, dur_rev=R, api=api, films_pool=pool,
                suggestions=True, signature=tuple(t["g"] for t in tours))


def points(ecart, base):
    return max(0, int(round(base * (1 - ecart / 30))))


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.ordre = list(partie.joueurs)
        self.k, self.etape, self.debut = 0, "indice", 1.0
        self.film = None                          # {"txt", "img"}
        self.places = {}                          # pid -> valeur 0..100
        self.gains = {}
        self.saisie = Saisie(m["api"], m.get("films_pool", []))

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le diapason se joue à 2 joueurs minimum."
        return ""

    def _diapason(self):
        v = [p for p in self.ordre if p in self.p.joueurs]
        return v[(self.p.index + self.k) % len(v)] if v else None

    def _tour(self):
        return self.m["tours"][min(self.k, len(self.m["tours"]) - 1)]

    def _dur(self):
        return {"indice": self.m["dur_indice"], "placer": self.m["dur_placer"], "rev": self.m["dur_rev"]}[self.etape]

    def _autres(self):
        d = self._diapason()
        return [p for p in self.p.joueurs if p != d]

    def _compter(self):
        base = int(self.cfg.get("gersten_pts", 400))
        c = self._tour()["cible"]
        pts = []
        for p in self._autres():
            if p in self.places:
                g = points(abs(self.places[p] - c), base)
                self.gains[p] = self.gains.get(p, 0) + g
                pts.append(g)
        d = self._diapason()
        if d and pts and self.film:
            self.gains[d] = self.gains.get(d, 0) + int(sum(pts) / len(pts))
        self.etape, self.debut = "rev", self.p.ecoule

    def _maj(self):
        t = self.p.ecoule - self.debut
        if self.etape == "indice" and t >= self._dur():
            self._compter()                               # pas de film à temps : on passe (personne ne marque)
        elif self.etape == "placer" and (t >= self._dur() or all(p in self.places for p in self._autres())):
            self._compter()
        elif self.etape == "rev" and t >= self._dur() and self.k < len(self.m["tours"]) - 1:
            self.k += 1
            self.film, self.places = None, {}
            self.etape, self.debut = "indice", self.p.ecoule

    def resoudre(self, d):
        return self.saisie.resoudre(d.get("texte"), avec_fiche=False)

    def suggerer(self, q):
        return self.saisie.suggerer(q)

    def action(self, pid, d, frac, info=None):
        self._maj()
        if self.etape == "indice":
            if pid != self._diapason():
                return {"ok": False, "msg": "Le diapason cherche son film…"}
            f = (info or {}).get("film")
            if not f:
                return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
            self.film = {"txt": info["libelle"], "img": publier(self.p, self.m, info.get("img"))}
            self.etape, self.debut = "placer", self.p.ecoule
            return {"ok": True, "correct": True, "msg": f"Film envoyé : {info['libelle']}"}
        if self.etape == "placer":
            if pid == self._diapason():
                return {"ok": False, "msg": "Les autres placent le curseur…"}
            try:
                x = max(0, min(100, int(d.get("valeur"))))
            except (TypeError, ValueError):
                return {"ok": False, "msg": ""}
            if pid in self.places:
                return {"ok": False, "msg": "Déjà placé"}
            self.places[pid] = x
            return {"ok": True, "msg": "Curseur placé"}
        return {"ok": False, "msg": ""}

    def fini(self):
        self._maj()
        return self.etape == "rev" and self.k >= len(self.m["tours"]) - 1 and self.p.ecoule - self.debut >= self._dur()

    def clore(self):
        if self.etape == "placer":
            self._compter()
        for pid, j in self.p.joueurs.items():
            gain = self.gains.get(pid, 0)
            j.gain += gain
            j.score += gain
            j.trouve = gain > 0
            j.serie = j.serie + 1 if j.trouve else 0

    def duree_revelation(self, base):
        return base

    def statut(self, pid):
        if pid == self._diapason():
            return {"t": "diapason", "c": "ok" if self.film else ""}
        return {"t": "placé" if pid in self.places else "", "c": "ok" if pid in self.places else ""}

    def avancement(self):
        d = self.p.joueurs.get(self._diapason())
        if self.etape == "indice":
            return f"{d.nom if d else '?'} cherche un film…"
        if self.etape == "placer":
            return f"{len(self.places)} / {len(self._autres())} ont placé le curseur"
        return ""

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        t = self._tour()
        d = J.get(self._diapason())
        rev = self.etape == "rev" or revele
        v = {"k": self.k, "n": len(self.m["tours"]), "gauche": t["g"], "droite": t["d"], "etape": "rev" if revele else self.etape,
             "diapason": d.public() if d else None, "film": self.film,
             "reste": round(max(0.0, self._dur() - (self.p.ecoule - self.debut)), 1)}
        if rev:
            v["cible"] = t["cible"]
            v["places"] = [dict(J[p].public(), x=x) for p, x in self.places.items() if p in J]
        if pid:
            moi = pid == self._diapason()
            v.update(diapason_moi=moi, ma_cible=t["cible"] if moi else None, ma_place=self.places.get(pid),
                     actif=not revele and not self.p.pause and ((self.etape == "indice" and moi) or
                                                                 (self.etape == "placer" and not moi and pid not in self.places)))
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0)) for p in J], key=lambda x: -x["gain"])
        return v
