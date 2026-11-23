"""Naido's Words (Entre les mots), façon Top Ten / Wavelength : Naido, la femme sans yeux, vit entre deux mondes.
Une règle de 1 à 100 porte quatre mots (1 = maison, 33 = chat, 66 = plateau, 100 = nuit…). Chacun reçoit en secret
un nombre, et tape un film qui mélange les deux mots les plus proches de son nombre, dans la bonne proportion (13 :
un film très « maison » et un peu « chat »). Puis les films s'affichent un par un : les autres placent sur la règle
le nombre qu'ils devinent. Points selon la précision, pour le devineur et pour l'auteur.
"""
import random

from .saisie_film import Saisie, publier

MOTS = ["maison", "chat", "nuit", "plage", "guerre", "amour", "robot", "enfant", "neige", "argent", "sang", "train",
        "mer", "forêt", "prison", "rêve", "école", "espace", "mariage", "vengeance", "musique", "voiture", "chien",
        "fantôme", "famille", "ville", "désert", "police", "sport", "magie", "cuisine", "hôpital", "avion", "trésor",
        "roi", "monstre", "fête", "secret", "mensonge", "montagne", "été", "Noël", "pluie", "feu", "temps", "miroir",
        "danse", "zombie", "cheval", "téléphone", "île", "bateau", "prison", "ordinateur", "bébé", "vampire", "cow-boy"]
POS = (1, 33, 66, 100)


def construire(api, cfg, pool, deja):
    mots = random.sample(sorted(set(MOTS)), 4)
    regle = [{"x": x, "mot": m} for x, m in zip(POS, mots)]
    E, G, R = float(cfg.get("naido_ecrire", 75)), float(cfg.get("naido_deviner", 25)), 6.0
    return dict(jeu="naido", vue="entremots", duree=round(E + 10 * (G + R) + 5, 1), reponse="entremots",
                etapes=[(0.0, {})], images=[], revelation=None, cles=[], bonne="", solution="Entre les mots",
                detail="", films=[], regle=regle, dur_ecrire=E, dur_deviner=G, dur_rev=R, api=api, films_pool=pool,
                suggestions=True, signature=tuple(mots))


def voisins(regle, n):
    """Les deux mots qui encadrent le nombre n."""
    for a, b in zip(regle, regle[1:]):
        if a["x"] <= n <= b["x"]:
            return a, b
    return regle[-2], regle[-1]


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.secrets = {}
        pris = set()
        for pid in partie.joueurs:
            n = random.choice([x for x in range(3, 99) if x not in POS and all(abs(x - y) > 4 for y in pris)] or [50])
            pris.add(n)
            self.secrets[pid] = n
        self.films = {}                          # pid -> {"txt", "img"}
        self.ordre = []                          # auteurs, dans l'ordre de passage
        self.k, self.etape, self.debut = 0, "ecrire", 1.0
        self.devines = {}                        # (auteur, pid) -> valeur
        self.gains = {}
        self.saisie = Saisie(m["api"], m.get("films_pool", []))

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Entre les mots se joue à 2 joueurs minimum."
        return ""

    def _dur(self):
        return {"ecrire": self.m["dur_ecrire"], "deviner": self.m["dur_deviner"], "rev": self.m["dur_rev"]}[self.etape]

    def _auteur(self):
        return self.ordre[self.k] if self.k < len(self.ordre) else None

    def _devineurs(self):
        a = self._auteur()
        return [p for p in self.p.joueurs if p != a]

    def _compter(self):
        a = self._auteur()
        base = int(self.cfg.get("naido_pts", 300))
        n = self.secrets.get(a, 50)
        pts = []
        for p in self._devineurs():
            x = self.devines.get((a, p))
            if x is not None:
                g = max(0, int(round(base * (1 - abs(x - n) / 30))))
                self.gains[p] = self.gains.get(p, 0) + g
                pts.append(g)
        if pts:
            self.gains[a] = self.gains.get(a, 0) + int(sum(pts) / len(pts))
        self.etape, self.debut = "rev", self.p.ecoule

    def _maj(self):
        t = self.p.ecoule - self.debut
        J = self.p.joueurs
        if self.etape == "ecrire" and (t >= self._dur() or (J and all(p in self.films for p in J))):
            self.ordre = [p for p in self.secrets if p in self.films]
            random.shuffle(self.ordre)
            self.k = 0
            if self.ordre:
                self.etape, self.debut = "deviner", self.p.ecoule
            else:
                self.etape, self.debut, self.k = "rev", self.p.ecoule, 0
        elif self.etape == "deviner" and (t >= self._dur() or all((self._auteur(), p) in self.devines for p in self._devineurs())):
            self._compter()
        elif self.etape == "rev" and t >= self._dur() and self.k < len(self.ordre) - 1:
            self.k += 1
            self.etape, self.debut = "deviner", self.p.ecoule

    def resoudre(self, d):
        return self.saisie.resoudre(d.get("texte"), avec_fiche=False)

    def suggerer(self, q):
        return self.saisie.suggerer(q)

    def action(self, pid, d, frac, info=None):
        self._maj()
        if self.etape == "ecrire":
            if pid in self.films:
                return {"ok": False, "msg": "Film déjà envoyé"}
            if pid not in self.secrets:
                return {"ok": False, "msg": "Vous arrivez en cours de manche"}
            f = (info or {}).get("film")
            if not f:
                return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
            self.films[pid] = {"txt": info["libelle"], "img": publier(self.p, self.m, info.get("img"))}
            return {"ok": True, "correct": True, "msg": f"Film envoyé : {info['libelle']}"}
        if self.etape == "deviner":
            a = self._auteur()
            if pid == a:
                return {"ok": False, "msg": "C'est votre film : les autres devinent"}
            try:
                x = max(1, min(100, int(d.get("valeur"))))
            except (TypeError, ValueError):
                return {"ok": False, "msg": ""}
            if (a, pid) in self.devines:
                return {"ok": False, "msg": "Déjà placé"}
            self.devines[(a, pid)] = x
            return {"ok": True, "msg": "Nombre placé"}
        return {"ok": False, "msg": ""}

    def fini(self):
        self._maj()
        return self.etape == "rev" and self.k >= len(self.ordre) - 1 and self.p.ecoule - self.debut >= self._dur()

    def clore(self):
        if self.etape == "deviner":
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
        if self.etape == "ecrire":
            return {"t": "a son film" if pid in self.films else "", "c": "ok" if pid in self.films else ""}
        if self.etape == "deviner":
            ok = (self._auteur(), pid) in self.devines
            return {"t": "auteur" if pid == self._auteur() else ("placé" if ok else ""), "c": "ok" if ok else ""}
        return {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        if self.etape == "ecrire":
            return f"{len(self.films)} / {len(J)} ont trouvé leur film"
        if self.etape == "deviner":
            return f"Film {self.k + 1}/{len(self.ordre)} · {sum(1 for p in self._devineurs() if (self._auteur(), p) in self.devines)} / {len(self._devineurs())} ont placé"
        return ""

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        a = self._auteur()
        rev = self.etape == "rev" or revele
        v = {"regle": self.m["regle"], "etape": "rev" if revele else self.etape, "k": self.k, "n": len(self.ordre),
             "reste": round(max(0.0, self._dur() - (self.p.ecoule - self.debut)), 1)}
        if self.etape in ("deviner", "rev") and a:
            v["film"] = dict(self.films[a], auteur=J[a].public() if a in J else None)
            if rev:
                v["nombre"] = self.secrets.get(a)
                v["places"] = [dict(J[p].public(), x=x) for (au, p), x in self.devines.items() if au == a and p in J]
        if revele:
            v["tous"] = [dict(self.films[p], auteur=J[p].public(), nombre=self.secrets[p]) for p in self.ordre if p in J]
        if pid:
            n = self.secrets.get(pid)
            av = voisins(self.m["regle"], n) if n else None
            v.update(mon_nombre=n, mes_mots=[av[0]["mot"], av[1]["mot"]] if av else [], mon_film=self.films.get(pid),
                     auteur_moi=pid == a, ma_place=self.devines.get((a, pid)),
                     actif=not revele and not self.p.pause and ((self.etape == "ecrire" and pid not in self.films and pid in self.secrets)
                                                                 or (self.etape == "deviner" and pid != a and (a, pid) not in self.devines)))
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0)) for p in J], key=lambda x: -x["gain"])
        return v
