"""Norma's Cherry Pie : devinez la note (de 1 à 10) qu'un autre joueur a donnée au film affiché.

Les notes viennent des profils (fichier importé). Comme les devinettes croisées de Complicité : chaque joueur
a une cible, un joueur présent qui a noté le film (jamais lui-même). Le film est toujours un film vu (noté) par TOUS
les joueurs présents qui ont des notes : l'intersection de leurs notes. Points seulement pour la note exacte (et la
cible marque quand on trouve sa note).
"""
import random

from PIL import ImageOps

from tmdb import cle_film, details_film, nom_affiche
from visuels import en_jpeg
from .commun import affiche, tirer



def notants(cfg):
    """Les profils présents qui ont des notes : le film doit avoir été noté par chacun d'eux."""
    return {p["nom"] for p in cfg.get("_profils", []) if p.get("notes")}


def construire(api, cfg, pool, deja):
    presents = notants(cfg)
    if len(presents) < 2:
        raise RuntimeError("Devine la note : il faut au moins 2 joueurs présents avec des notes.")
    if not any(presents <= set(f["notes"]) for f in pool):
        raise RuntimeError("Devine la note : aucun film n'a été noté par tous les joueurs présents ("
                           + ", ".join(sorted(presents)) + ").")
    film = tirer(pool, deja, lambda f: presents <= set(f["notes"]))
    d = details_film(api, film)
    poster = affiche(api, film, "w500")
    genres = ", ".join(d["genres"][:2])
    return dict(jeu="norma", vue="note", duree=float(cfg["dur_norma"]), reponse="note", revelation=None,
                etapes=[(0.0, {"img": 0, "titre": nom_affiche(film["title"], d["annee"], None), "genres": genres})],
                images=[en_jpeg(ImageOps.contain(poster, (400, 600)), 600)], cles=[], bonne="",
                solution=nom_affiche(film["title"], d["annee"], d["en"]), films=[cle_film(film)],
                notes=dict(film["notes"]))


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        J = partie.joueurs
        self.note = {pid: m["notes"][j.profil] for pid, j in J.items() if j.profil in m["notes"]}
        notants = list(self.note)
        random.shuffle(notants)
        self.cibles = {}
        if len(notants) >= 2:
            for i, pid in enumerate(notants):                  # en cercle : personne ne se devine lui-même
                self.cibles[pid] = notants[(i + 1) % len(notants)]
            autres = [pid for pid in J if pid not in self.note]
            for i, pid in enumerate(autres):
                self.cibles[pid] = notants[i % len(notants)]
        self.reponses, self.fracs, self.gains = {}, {}, {}

    def ok(self):
        return "" if self.cibles else "Norma's Cherry Pie : il faut 2 joueurs présents qui ont noté le film."

    def devineurs(self):
        return [d for d in self.cibles if d in self.p.joueurs and self.cibles[d] in self.p.joueurs]

    # ---------- actions ----------
    def action(self, pid, d, frac, info=None):
        if pid not in self.cibles:
            return {"ok": False, "msg": "Vous ne devinez pas cette manche"}
        if pid in self.reponses:
            return {"ok": False, "msg": "Réponse déjà envoyée"}
        n = d.get("i")
        if type(n) is not int or not 1 <= n <= 10:
            return {"ok": False, "msg": "Choisissez une note de 1 à 10"}
        self.reponses[pid], self.fracs[pid] = n, frac
        self.p.joueurs[pid].essais = 1
        return {"ok": True, "msg": f"Réponse enregistrée : {n}/10"}

    def fini(self):
        devs = self.devineurs()
        return bool(devs) and all(d in self.reponses for d in devs)

    def clore(self):
        J = self.p.joueurs
        for d, n in self.reponses.items():
            c = self.cibles.get(d)
            if d not in J or c not in self.note:
                continue
            ecart = abs(n - self.note[c])
            gain = 0
            if ecart == 0:
                gain = self.cfg["norma_pts"] + int(self.cfg["norma_vitesse"] * self.fracs.get(d, 0))
                if c in J:
                    J[c].gain += self.cfg["norma_cible"]
                    J[c].score += self.cfg["norma_cible"]
            J[d].gain += gain
            J[d].score += gain
            J[d].trouve = ecart == 0
            self.gains[d] = gain
        for j in J.values():
            j.serie = j.serie + 1 if j.trouve else 0

    def chaine(self):
        """Ordre de révélation : on suit la chaîne cible → devineur (comme Complicité)."""
        J = self.p.joueurs
        par_cible = {}
        for d, c in self.cibles.items():
            if d in J and c in J:
                par_cible.setdefault(c, []).append(d)
        ordre, vus = [], set()
        file = [p for p in J if p in par_cible]
        while file:
            c = file.pop(0)
            if c in vus:
                continue
            vus.add(c)
            for d in par_cible[c]:
                ordre.append((c, d))
                if d in par_cible and d not in vus:
                    file.insert(0, d)
        return ordre

    def duree_revelation(self, base):
        return max(base, len(self.chaine()) * float(self.cfg.get("comp_rev_pas", 3.5)) + 3)

    def statut(self, pid):
        if pid in self.reponses:
            return {"t": "a répondu", "c": "ok"}
        return {"t": "réfléchit…", "c": "go"} if pid in self.cibles else {"t": "", "c": ""}

    def avancement(self):
        devs = self.devineurs()
        return f"{sum(1 for d in devs if d in self.reponses)} / {len(devs)} ont répondu"

    # ---------- vues ----------
    def _j(self, pid):
        j = self.p.joueurs.get(pid)
        return j.public() if j else None

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"paires": [{"devineur": self._j(d), "cible": self._j(c)} for c, d in self.chaine()],
             "attente": [dict(x, fait=d in self.reponses) for d in self.devineurs() if (x := self._j(d))],
             "pas": float(self.cfg.get("comp_rev_pas", 3.5))}
        if pid:
            v.update(cible=self._j(self.cibles.get(pid)), ma_reponse=self.reponses.get(pid),
                     actif=pid in self.cibles and pid not in self.reponses and not revele and not self.p.pause,
                     ma_note=self.note.get(pid))
        if revele:
            v["resultats"] = [dict(cible=self._j(c), note=self.note.get(c), devineur=self._j(d),
                                   reponse=self.reponses.get(d), gain=self.gains.get(d, 0),
                                   ecart=abs(self.reponses[d] - self.note[c]) if d in self.reponses else None)
                              for c, d in self.chaine() if c in J and d in J]
        return v
