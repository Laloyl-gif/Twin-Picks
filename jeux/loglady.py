"""The Log Lady's Knothole (Ce que la bûche a vu) : « Ma bûche a vu quelque chose. » Une image du film (prise sur
TMDB), vue par le trou d'un nœud de la bûche : le trou se promène au hasard sur l'image et s'agrandit peu à peu.
Indices (réglables) : genre et année à 50 %, titre à trous à 80 %. À la réponse : l'image entière et le titre du film.
"""
import random

from PIL import ImageOps

import images_film as imf
import plans_distants
from tmdb import details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

PAS = 1.6                    # secondes entre deux déplacements du trou


def _seg(p, a, b):
    """Distance (en % de largeur) du point p au segment [a, b] (y converti : l'image est en 16/9)."""
    px, py, ax, ay, bx, by = p[0], p[1] * .5625, a[0], a[1] * .5625, b[0], b[1] * .5625
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** .5


def promenade(n, r0, r1):
    """n positions (x, y en % de l'image, rayon r en % de la largeur). La bûche ne repasse pas au même endroit : chaque
    nouvelle position est choisie parmi des points au hasard, en préférant celles dont le TRAJET (depuis la position
    actuelle) passe le plus loin de tous les endroits déjà vus, et qui restent loin des trajets déjà faits.
    Le trou reste toujours entièrement sur l'image."""
    vus, pts = [], []
    for k in range(n):
        r = r0 + (r1 - r0) * (k / max(1, n - 1)) ** 1.3
        mx, my = r / 2 + 1, min(49, r / 2 / 0.5625 + 1)              # marges en % (largeur / hauteur)
        cands = [(random.uniform(mx, 100 - mx), random.uniform(my, 100 - my)) for _ in range(60)]

        def loin(c):
            if not vus:
                return 100
            d = min(_seg(v, vus[-1], c) for v in vus[:-1]) if len(vus) > 1 else 100     # le trajet évite les endroits vus
            d = min(d, *(_seg(c, vus[i], vus[i + 1]) for i in range(len(vus) - 1))) if len(vus) > 1 else d  # et les trajets faits
            d = min(d, ((c[0] - vus[-1][0]) ** 2 + ((c[1] - vus[-1][1]) * .5625) ** 2) ** .5)                 # et on bouge vraiment
            return d
        cands.sort(key=loin, reverse=True)
        x, y = random.choice(cands[:3])                             # parmi les meilleurs : un peu de hasard
        vus.append((x, y))
        pts.append({"x": round(x, 1), "y": round(y, 1), "r": round(r, 1)})
    return pts


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_loglady"])
    im = None
    try:                                    # les plans triés à la main de Truman's Files (moyens ou faciles)
        cat = plans_distants.catalogue()
    except Exception:  # noqa: BLE001
        cat = None
    a_plans = bool(cat is not None and len(cat) and any(not f.get("tv") and cat.chercher(f) for f in pool))
    for k in range(10):
        avec_plans = a_plans and k < 6 and random.random() < 0.6
        film = tirer(pool, deja, (lambda f: not f.get("tv") and cat.chercher(f) is not None) if avec_plans
                     else (lambda f: not f.get("tv")))
        d = details_film(api, film)
        entree = cat.chercher(film) if cat is not None else None
        if entree:
            ims = entree.images((random.choice(("3_facile", "3_facile", "2_moyen")),))
            if ims:
                im = ims[0]
                break
        try:
            plans = imf.plans_tmdb(api, d, affiche(api, film, "w185"), 3)
        except Exception:  # noqa: BLE001
            plans = None
        if plans:
            im = random.choice(plans[1:] or plans)[0]
            break
    if im is None:                          # aucune image TMDB : l'affiche, recadrée
        im = affiche(api, film, "w500")
    image = en_jpeg(ImageOps.fit(im.convert("RGB"), (1024, 576)), 900)
    n = max(4, int(duree * 0.92 / PAS))
    pts = promenade(n, 10, 34)
    etat = {"img": 0, "trou": dict(pts[0], d=PAS), "indices": [], "trous": ""}
    evts = [(round(PAS * k, 2), lambda k=k: etat.update(trou=dict(pts[k], d=PAS))) for k in range(1, n)]
    if cfg.get("loglady_indices", True):
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            evts.append((duree * 0.5, lambda: etat["indices"].append(depart)))
        evts.append((duree * 0.8, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "trou": dict(etat["trou"]), "indices": list(etat["indices"])})
    m = manche_titre("loglady", "noeud", duree, film, d, etapes, [image], None, cfg)
    return m
