"""Big Ed's Gas Farm (La durée) : à la station-service de Big Ed, on fait le plein… de minutes. Combien de temps dure
le film ? Chacun tape sa réponse en minutes ; la jauge d'essence (vide = 1 h, plein = 4 h) révèle la vraie durée.

Points : la réponse la plus proche gagne toujours (bonus, partagé en cas d'égalité) ; bonus à 5 minutes près ; pour
tout le monde, des points qui baissent avec l'écart (réglable). Indice à mi-temps (réglable) : une fourchette de 40 min.
"""
import random

from PIL import ImageOps

from tmdb import cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_ed"])
    for _ in range(25):
        film = tirer(pool, deja, lambda f: not f.get("tv") and f.get("poster_path"))
        try:
            minutes = int(fiche(api, film).get("duree") or 0)
        except Exception:  # noqa: BLE001
            continue
        if 40 <= minutes <= 300:
            break
    else:
        raise RuntimeError("La durée : aucun film des listes n'a de durée connue sur TMDB.")
    d = details_film(api, film)
    image = en_jpeg(ImageOps.contain(affiche(api, film, "w500"), (400, 600)), 600)
    etat = {"img": 0, "titre": film["title"], "sous": " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x),
            "indices": []}
    evts = []
    if cfg.get("ed_indice", True):
        bas = max(30, minutes - random.randint(5, 35))
        evts.append((duree * 0.5, lambda: etat["indices"].append(f"Entre {hm(bas)} et {hm(bas + 40)}")))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    return dict(jeu="ed", vue="ed", duree=duree, reponse="duree", etapes=etapes, revelation=None, images=[image],
                cles=[], bonne="", minutes=minutes, solution=hm(minutes),
                detail=f"{film['title']} : {minutes} minutes", films=[cle_film(film)])


def hm(minutes):
    """138 -> « 2 h 18 min »."""
    h, mn = divmod(int(minutes), 60)
    return f"{h} h {mn:02d} min" if h else f"{mn} min"


def lire_duree(texte):
    """« 2h18 », « 2 h 18 min », « 2:18 », et au pavé numérique « 218 » (heures puis minutes : 2 h 18) -> minutes.
    Un seul chiffre : des heures (« 2 » = 2 h). None si illisible. Le téléphone affiche la durée comprise en direct."""
    import re
    brut = str(texte).strip().lower()
    t = brut.replace("min", "").replace("mn", "").strip()
    if t.isdigit() and ("min" in brut or "mn" in brut):
        return int(t)                                        # « 138 min » : des minutes
    m = re.fullmatch(r"(\d{1,2})\s*(?:h|:|\.|,)\s*(\d{0,2})", t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    if not t.isdigit():
        return None
    if len(t) == 1:
        return int(t) * 60
    if len(t) == 2:
        return int(t[0]) * 60 + int(t[1]) * 10               # « 14 » en cours de frappe : 1 h 40
    if len(t) == 3 and int(t[1:]) < 60:
        return int(t[0]) * 60 + int(t[1:])
    return int(t)


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.reponses, self.fracs, self.gains = {}, {}, {}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        if pid in self.reponses:
            return {"ok": False, "msg": "Réponse déjà envoyée"}
        n = lire_duree(d.get("texte", ""))
        if n is None:
            return {"ok": False, "msg": "Entrez une durée, par exemple 1h58 ou 118"}
        if not 20 <= n <= 600:
            return {"ok": False, "msg": "Entre 20 minutes et 10 heures"}
        self.reponses[pid], self.fracs[pid] = n, frac
        self.p.joueurs[pid].essais = 1
        return {"ok": True, "msg": f"Réponse enregistrée : {hm(n)}"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(p in self.reponses for p in J)

    def clore(self):
        vrai, tol, pts = self.m["minutes"], max(1, int(self.cfg.get("ed_tolerance", 60))), self.cfg.get("ed_pts", 800)
        ecarts = {p: abs(r - vrai) for p, r in self.reponses.items() if p in self.p.joueurs}
        meilleur = min(ecarts.values(), default=None)
        for pid, j in self.p.joueurs.items():
            e = ecarts.get(pid)
            gain = 0
            if e is not None:
                gain = int(pts * max(0.0, 1 - e / tol) ** 1.5)          # décroît avec l'écart
                if e == meilleur:
                    gain += self.cfg.get("ed_proche", 400)             # le plus proche gagne toujours
                if e <= 5:
                    gain += self.cfg.get("ed_cinq", 200) + int(self.cfg["bonus_vitesse"] * self.fracs.get(pid, 0))
            j.gain += gain
            j.score += gain
            j.trouve = e is not None and e == meilleur
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def duree_revelation(self, base):
        return base + 3                       # le temps que l'aiguille monte

    def statut(self, pid):
        return {"t": "a répondu", "c": "ok"} if pid in self.reponses else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if p in self.reponses)} / {len(J)} ont fait le plein"

    def vue(self, pid, revele):
        v = {}
        if pid:
            v.update(ma_reponse=self.reponses.get(pid), ma_reponse_hm=hm(self.reponses[pid]) if pid in self.reponses else "", actif=pid not in self.reponses and not revele and not self.p.pause)
        if revele:
            vrai = self.m["minutes"]
            v.update(duree=vrai, resultats=sorted(
                [dict(self.p.joueurs[p].public(), reponse=r, reponse_hm=hm(r), ecart=abs(r - vrai), gain=self.gains.get(p, 0))
                 for p, r in self.reponses.items() if p in self.p.joueurs], key=lambda x: x["ecart"]))
        return v
