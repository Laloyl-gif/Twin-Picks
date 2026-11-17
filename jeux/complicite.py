"""Complicité : un joueur choisit en secret son film préféré parmi N, les autres le devinent.
Modes : « tour » (meneur à tour de rôle), « fixe » (toujours le même), « tous » (devinettes croisées)."""
import random

from PIL import ImageOps

from tmdb import cle_film
from visuels import en_jpeg
from .commun import tirer

FACT_RANG = [1.0, 0.6, 0.4, 0.25, 0.15, 0.1]
REMONTADA_MAX = 300


def construire(api, cfg, pool, deja):
    n = cfg["comp_films"]
    avec = [f for f in pool if f.get("poster_path")]
    if len(avec) < n:
        raise RuntimeError(f"Complicité : il faut au moins {n} films avec affiche dans les listes choisies.")
    choisis = []
    for _ in range(n * 20):
        f = tirer(avec, deja)
        if f not in choisis:
            choisis.append(f)
        if len(choisis) == n:
            break
    affiches = api.images([f["poster_path"] for f in choisis], "w342")
    films = [{"img": i, "txt": f"{f['title']} ({f['release_date'][:4]})" if f.get("release_date") else f["title"]}
             for i, f in enumerate(choisis)]
    return dict(jeu="complice", vue="complice", duree=float(cfg["comp_dur_choix"]),
                etapes=[(0.0, {"films": films})], revelation=None,
                images=[en_jpeg(ImageOps.fit(a, (300, 450)), 450) for a in affiches],
                reponse="complice", cles=[], bonne="", solution="", films=[cle_film(f) for f in choisis])


class Complicite:
    def __init__(self, partie, cfg, mode, meneur, manche):
        self.p, self.cfg, self.mode, self.meneur = partie, cfg, mode, meneur
        self.films = manche["etapes"][0][1]["films"]
        self.sous = "choix"                 # « choix » puis « devine »
        self.favoris, self.votes, self.cibles, self.ordre = {}, {}, {}, []

    # ---------- qui fait quoi ----------
    def choisisseurs(self):
        if self.mode == "tous":
            return set(self.p.joueurs)
        return {self.meneur} if self.meneur in self.p.joueurs else set()

    def devineurs(self):
        if self.mode == "tous":
            return [d for d in self.cibles if d in self.p.joueurs]
        return [p for p in self.p.joueurs if p != self.meneur]

    def cible(self, pid):
        return self.cibles.get(pid) if self.mode == "tous" else self.meneur

    def bonne(self, pid):
        return self.favoris.get(self.cible(pid), -1)

    def choix_complets(self):
        att = self.choisisseurs()
        return bool(att) and att <= set(self.favoris)

    def fini(self):
        devs = self.devineurs()
        return self.sous == "devine" and all(d in self.votes for d in devs)

    def lancer_devine(self):
        """Passe à l'étape « devine ». False si pas assez de choix (la manche s'arrête alors)."""
        if self.sous == "devine":
            return True
        if self.mode == "tous":
            joueurs = [p for p in self.p.joueurs if p in self.favoris]
            if len(joueurs) < 2:
                return False
            melange = joueurs[:]
            for _ in range(100):                   # personne ne doit deviner son propre film
                random.shuffle(melange)
                if all(a != b for a, b in zip(joueurs, melange)):
                    break
            else:
                melange = joueurs[1:] + joueurs[:1]
            self.cibles = dict(zip(joueurs, melange))
        elif self.meneur not in self.favoris:
            return False
        self.sous = "devine"
        return True

    # ---------- actions ----------
    def remontada(self, pid):
        autres = [j.score for p, j in self.p.joueurs.items() if p != pid]
        if not autres:
            return 0
        ecart = max(autres) - self.p.joueurs[pid].score
        return min(REMONTADA_MAX, int(ecart * self.cfg["comp_remontada"] / 100)) if ecart > 0 else 0

    def jouer(self, pid, i, frac):
        if not 0 <= i < len(self.films):
            return {"ok": False, "msg": "Réponse refusée"}
        if self.sous == "choix":
            if pid not in self.choisisseurs():
                return {"ok": False, "msg": "Ce n'est pas à vous de choisir"}
            if pid in self.favoris:
                return {"ok": False, "msg": "Choix déjà enregistré"}
            self.favoris[pid] = i
            return {"ok": True, "msg": "Choix enregistré"}
        if pid not in self.devineurs():
            return {"ok": False, "msg": "Les autres devinent votre film"}
        if pid in self.votes:
            return {"ok": False, "msg": "Réponse déjà envoyée"}
        self.votes[pid] = i
        j = self.p.joueurs[pid]
        j.essais = 1
        if i == self.bonne(pid):
            rang = len(self.ordre)
            self.ordre.append(pid)
            j.bonus = self.remontada(pid)
            j.gain = (self.cfg["comp_pts_devin"] + int(self.cfg["comp_bonus_rang"] * FACT_RANG[min(rang, 5)])
                      + int(self.cfg["comp_bonus_vitesse"] * frac) + j.bonus)
            j.score += j.gain
            j.trouve = True
        return {"ok": True, "msg": "Réponse enregistrée"}

    def clore(self):
        """Points du meneur / des cibles (une seule fois, au passage à la réponse)."""
        if self.sous != "devine":
            return
        J = self.p.joueurs
        if self.mode == "tous":
            for d, c in self.cibles.items():
                if c in J and self.votes.get(d, -1) == self.favoris.get(c):
                    J[c].gain += self.cfg["comp_pts_meneur"]
                    J[c].score += self.cfg["comp_pts_meneur"]
            return
        chef = J.get(self.meneur)
        if not chef:
            return
        ok, devs = len(self.ordre), self.devineurs()
        gain = self.cfg["comp_pts_meneur"] * ok + (self.cfg["comp_pts_tous"] if devs and ok == len(devs) else 0)
        chef.gain += gain
        chef.score += gain

    def chaine(self):
        """Paires (cible, devineur) dans l'ordre de la révélation : on suit la chaîne, le devineur d'une
        paire devient la cible de la suivante (Louison → trouvée par Lily, puis Lily → Etienne…)."""
        J = self.p.joueurs
        par_cible = {c: d for d, c in self.cibles.items() if d in J and c in J}
        reste = [p for p in J if p in par_cible]
        ordre = []
        while reste:
            c = reste[0]
            while c in reste:
                reste.remove(c)
                ordre.append((c, par_cible[c]))
                c = par_cible[c]
        return ordre

    def duree_revelation(self, base):
        if self.mode == "tous" and self.sous == "devine":
            return max(base, len(self.chaine()) * float(self.cfg.get("comp_rev_pas", 3.5)) + 3)
        return base + 3

    # ---------- vues ----------
    def _j(self, pid):
        j = self.p.joueurs.get(pid) if pid else None
        return j.public() if j else None

    def resultats(self):
        if self.sous != "devine":
            return {"aucun": True}
        J = self.p.joueurs
        films = [{"favori_de": [], "votes": []} for _ in self.films]
        cibles = set(self.cibles.values()) if self.mode == "tous" else {self.meneur}
        for c in cibles:
            if c in J and c in self.favoris:
                films[self.favoris[c]]["favori_de"].append(self._j(c))
        for d, i in self.votes.items():
            if d in J:
                films[i]["votes"].append(dict(self._j(d), ok=i == self.bonne(d), cible=self._j(self.cible(d))))
        paires = [dict(devineur=self._j(d), cible=self._j(c), film=self.favoris.get(c, -1),
                       vote=self.votes.get(d, -1), ok=self.votes.get(d, -1) == self.favoris.get(c, -2),
                       gain=J[d].gain) for c, d in self.chaine()]
        chef = J.get(self.meneur)
        return {"films": films, "paires": paires, "pas": float(self.cfg.get("comp_rev_pas", 3.5)),
                "bonne": self.favoris.get(self.meneur, -1) if self.mode != "tous" else -1,
                "gain_meneur": chef.gain if chef and self.mode != "tous" else 0}

    def vue(self, pid, revele):
        v = {"mode": self.mode, "sous": self.sous, "films": self.films,
             "confirmer": bool(self.cfg["comp_confirmer"]),
             "meneur": self._j(self.meneur) if self.mode != "tous" else None}
        if self.sous == "choix":
            v["attente"] = [dict(x, fait=p in self.favoris) for p in self.choisisseurs() if (x := self._j(p))]
        else:
            v["attente"] = [dict(x, fait=p in self.votes) for p in self.devineurs() if (x := self._j(p))]
            if self.mode == "tous":
                v["paires"] = [{"devineur": self._j(d), "cible": self._j(c)} for d, c in self.cibles.items()
                               if d in self.p.joueurs and c in self.p.joueurs]
        if pid:
            choisit = self.sous == "choix" and pid in self.choisisseurs()
            devine = self.sous == "devine" and pid in self.devineurs()
            v.update(moi_choisit=choisit, moi_devine=devine, mon_favori=self.favoris.get(pid, -1),
                     mon_choix=self.favoris.get(pid, -1) if self.sous == "choix" else self.votes.get(pid, -1),
                     cible=self._j(self.cible(pid)),
                     actif=not self.p.pause and not revele and ((choisit and pid not in self.favoris)
                                                                or (devine and pid not in self.votes)))
        if revele:
            v["resultats"] = self.resultats()
        return v
