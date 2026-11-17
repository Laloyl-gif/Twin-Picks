"""Dougie's Jackpots (Le jackpot) : au casino, Dougie Jones touche le jackpot à chaque machine (« Hellooo ! »). Ici, la
machine à sous a trois rouleaux ; ils tournent sur des morceaux d'affiches, puis s'arrêtent un à un : chacun sur un
tiers de l'affiche du film mystère. Quand les trois sont arrêtés : jackpot, l'affiche est entière.
Indices : genre et année, puis titre à trous.
"""
import random

from PIL import ImageFilter, ImageOps

from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

L, H = 360, 540


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_dougie"])
    film = tirer(pool, deja, lambda f: not f.get("tv") and f.get("poster_path"))
    d = details_film(api, film)
    poster = ImageOps.fit(affiche(api, film, "w500").convert("RGB"), (L, H))
    tiers = [poster.crop((k * L // 3, 0, (k + 1) * L // 3, H)) for k in range(3)]
    leurres = [f for f in pool if f["id"] != film["id"] and f.get("poster_path")]
    random.shuffle(leurres)
    flous = []
    for f in leurres[:6]:
        try:
            p = ImageOps.fit(affiche(api, f, "w342").convert("RGB"), (L, H))
        except Exception:  # noqa: BLE001
            continue
        k = random.randrange(3)
        flous.append(p.crop((k * L // 3, 0, (k + 1) * L // 3, H)).filter(ImageFilter.GaussianBlur(1.2)))
    images = [en_jpeg(t, H) for t in tiers] + [en_jpeg(f, H) for f in flous]
    etat = {"rouleaux": [False, False, False], "leurres": list(range(3, 3 + len(flous))), "indices": [], "trous": ""}

    def arreter(k):
        etat["rouleaux"][k] = True
    evts = [(duree * t, lambda k=k: arreter(k)) for k, t in enumerate((0.22, 0.42, 0.62))]
    depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
    if depart:
        evts.append((duree * 0.5, lambda: etat["indices"].append(depart)))
    evts.append((duree * 0.8, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "rouleaux": list(etat["rouleaux"]), "indices": list(etat["indices"])})
    m = manche_titre("dougie", "jackpot", duree, film, d, etapes, images, en_jpeg(affiche(api, film, "w500")), cfg)
    m["films"] = [cle_film(film)]
    return m
