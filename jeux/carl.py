"""Carl's Fat Trout Trailers (Les deux films) : au camping de caravanes « Fat Trout » de Carl Rodd, on regarde par
la fenêtre d'une caravane… mais derrière le store vénitien, deux films se mélangent : une lame sur deux montre une
image du film A, l'autre une image du film B. Les lames s'ouvrent une à une, dans le désordre. Il faut trouver les
DEUX films : chacun rapporte des points, les deux ensemble un bonus. À la réponse : les deux affiches.
"""
import random

from PIL import Image, ImageOps

import images_film as imf
from texte import correspond, proche
from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, cles_reponses, reponse_affichee, tirer, trous

LAMES = 12
L, H = 1024, 576


def _image(api, film, d):
    try:
        plans = imf.plans_tmdb(api, d, affiche(api, film, "w185"), 3)
    except Exception:  # noqa: BLE001
        plans = None
    if plans:
        return random.choice(plans[1:] or plans)[0]
    try:                                                 # pas d'image du film : le haut de l'affiche
        return affiche(api, film, "w500")
    except Exception:  # noqa: BLE001
        return None


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_carl"])
    choisis = []
    for _ in range(16):
        film = tirer(pool, deja, lambda f: not f.get("tv") and all(f["id"] != c[0]["id"] for c in choisis))
        d = details_film(api, film)
        if choisis and set(d["genres"][:1]) == set(choisis[0][1]["genres"][:1]) and random.random() < 0.7:
            continue                                     # deux genres différents : on les distingue mieux
        im = _image(api, film, d)
        if im is None:
            continue
        choisis.append((film, d, ImageOps.fit(im.convert("RGB"), (L, H))))
        if len(choisis) == 2:
            break
    if len(choisis) < 2:
        raise RuntimeError("Les deux films : pas assez de films avec des images dans les listes choisies.")
    (fa, da, ia), (fb, db, ib) = choisis
    melange = Image.new("RGB", (L, H))                   # une lame sur deux : A, B, A, B…
    for k in range(LAMES):
        y0, y1 = round(k * H / LAMES), round((k + 1) * H / LAMES)
        melange.paste((ia if k % 2 == 0 else ib).crop((0, y0, L, y1)), (0, y0))
    poster_a, poster_b = affiche(api, fa, "w342"), affiche(api, fb, "w342")
    duo = Image.new("RGB", (700, 520), (14, 12, 17))
    duo.paste(ImageOps.fit(poster_a.convert("RGB"), (330, 495)), (12, 12))
    duo.paste(ImageOps.fit(poster_b.convert("RGB"), (330, 495)), (358, 12))
    ordre = list(range(LAMES))
    random.shuffle(ordre)
    etat = {"img": 0, "lames": [], "total": LAMES, "indices": [], "trous": "", "deux": True}
    evts = [(round(duree * 0.8 * (k + 1) / LAMES, 2), lambda k=k: etat.update(lames=ordre[:k + 1])) for k in range(LAMES - 1)]
    if cfg.get("carl_indices", True):
        genres = " / ".join(x for x in (da["genres"][:1] + db["genres"][:1]) if x)
        if genres:
            evts.append((duree * 0.45, lambda: etat["indices"].append(genres)))
        annees = " et ".join(x for x in (da["annee"], db["annee"]) if x)
        if annees:
            evts.append((duree * 0.6, lambda: etat["indices"].append("Sortis en " + annees)))
        evts.append((duree * 0.8, lambda: etat.update(
            trous=trous(reponse_affichee(cfg, fa, da), 0) + "   +   " + trous(reponse_affichee(cfg, fb, db), 0))))
    etapes = chronologie(evts, lambda: {**etat, "lames": list(etat["lames"]), "indices": list(etat["indices"])})
    titres = [reponse_affichee(cfg, fa, da), reponse_affichee(cfg, fb, db)]
    return dict(jeu="carl", vue="caravane", duree=duree, etapes=etapes, images=[en_jpeg(melange, 900)],
                revelation=en_jpeg(duo), reponse="paire", suggestions=True,
                paire_cles=[cles_reponses(fa["title"], fa.get("original_title"), *da["noms"]),
                            cles_reponses(fb["title"], fb.get("original_title"), *db["noms"])],
                paire_titres=titres, cles=[], bonne="", solution=" + ".join(titres),
                detail="Une lame sur deux : " + " · ".join(titres), films=[cle_film(fa), cle_film(fb)])


class Moteur:
    """Les deux films : chacun tape des titres ; chaque film trouvé rapporte des points (plus tôt = plus)."""
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.trouves, self.essais, self.gains = {}, {}, {}

    def ok(self):
        return ""

    def _max(self):
        return 2 * int(self.cfg.get("max_essais", 3))

    def action(self, pid, d, frac, info=None):
        texte = str(d.get("texte", "")).strip()
        if not texte:
            return {"ok": False, "msg": "Tapez un titre"}
        tr = self.trouves.setdefault(pid, {})
        if len(tr) == 2:
            return {"ok": False, "msg": "Les deux films sont trouvés !"}
        if self.essais.get(pid, 0) >= self._max():
            return {"ok": False, "msg": "Plus d'essais"}
        for k, cles in enumerate(self.m["paire_cles"]):
            if any(correspond(texte, c) for c in cles):
                if k in tr:
                    return {"ok": False, "msg": "Celui-là est déjà trouvé : l'autre !"}
                tr[k] = frac
                self.p.joueurs[pid].essais = 1
                reste = "Les deux, bravo !" if len(tr) == 2 else "Plus qu'un !"
                return {"ok": True, "correct": len(tr) == 2, "msg": f"{self.m['paire_titres'][k]} : trouvé. {reste}"}
        self.essais[pid] = self.essais.get(pid, 0) + 1
        reste = self._max() - self.essais[pid]
        presque = any(proche(texte, c) for cles in self.m["paire_cles"] for c in cles)
        return {"ok": False, "msg": ("Presque ! Vérifiez l'orthographe. " if presque else "Raté. ") +
                (f"{reste} essai(s) restant(s)" if reste else "Plus d'essais.")}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(len(self.trouves.get(p, {})) == 2 or self.essais.get(p, 0) >= self._max() for p in J)

    def clore(self):
        pts, deux = int(self.cfg.get("carl_pts", 600)), int(self.cfg.get("carl_deux", 300))
        for pid, j in self.p.joueurs.items():
            tr = self.trouves.get(pid, {})
            gain = sum(pts + int(self.cfg["bonus_vitesse"] * f) for f in tr.values())
            if len(tr) == 2:
                gain += deux
            j.gain += gain
            j.score += gain
            j.trouve = len(tr) == 2
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        n = len(self.trouves.get(pid, {}))
        return {"t": f"{n}/2", "c": "ok" if n == 2 else ""} if n else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if len(self.trouves.get(p, {})) == 2)} / {len(J)} ont trouvé les deux films"

    def vue(self, pid, revele):
        v = {"titres": self.m["paire_titres"] if revele else []}
        if pid:
            tr = self.trouves.get(pid, {})
            v.update(mes_films=[self.m["paire_titres"][k] for k in sorted(tr)],
                     actif=len(tr) < 2 and self.essais.get(pid, 0) < self._max() and not revele and not self.p.pause)
        if revele:
            v["resultats"] = sorted([dict(j.public(), n=len(self.trouves.get(p, {})), gain=self.gains.get(p, 0))
                                     for p, j in self.p.joueurs.items()], key=lambda x: -x["gain"])
        return v
