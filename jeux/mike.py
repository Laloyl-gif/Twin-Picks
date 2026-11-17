"""Mike's Missing Arm (La pièce manquante) : Mike, le manchot, a perdu son bras… ici, c'est l'affiche qui a perdu un
morceau. Quatre pièces sont proposées, découpées au même endroit dans quatre affiches : laquelle complète l'affiche ?
Indice (réglable) : une mauvaise pièce est barrée à mi-temps.
"""
import random

from PIL import ImageDraw, ImageOps

from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer

L, H = 400, 600


def construire(api, cfg, pool, deja):
    duree, n = float(cfg["dur_mike"]), 4
    film = tirer(pool, deja, lambda f: not f.get("tv") and f.get("poster_path"))
    d = details_film(api, film)
    poster = ImageOps.fit(affiche(api, film, "w500").convert("RGB"), (L, H))
    genres = set(film.get("genre_ids") or [])
    autres = [f for f in pool if f["id"] != film["id"] and f.get("poster_path")]
    autres.sort(key=lambda f: (-len(genres & set(f.get("genre_ids") or [])), random.random()))
    w, h = random.randint(120, 160), random.randint(150, 210)
    x, y = random.randint(30, L - w - 30), random.randint(60, H - h - 60)
    pieces = [poster.crop((x, y, x + w, y + h))]
    for f in autres[:8]:
        if len(pieces) == n:
            break
        try:
            p = ImageOps.fit(affiche(api, f, "w342").convert("RGB"), (L, H))
        except Exception:  # noqa: BLE001
            continue
        pieces.append(p.crop((x, y, x + w, y + h)))
    if len(pieces) < n:
        raise RuntimeError("La pièce manquante : pas assez d'affiches dans les listes choisies.")
    ordre = list(range(n))
    random.shuffle(ordre)
    bonne = ordre.index(0)
    trou = poster.copy()
    dr = ImageDraw.Draw(trou)
    dr.rectangle((x, y, x + w, y + h), fill=(14, 12, 17))
    dr.rectangle((x, y, x + w, y + h), outline=(233, 220, 192), width=3)
    images = [en_jpeg(trou, H)] + [en_jpeg(pieces[i], 300) for i in ordre]
    etat = {"film": {"img": 0, "txt": film["title"], "sous": " · ".join(v for v in (", ".join(d["genres"][:2]), d["annee"]) if v)},
            "question": "Quelle pièce manque à l'affiche ?", "pieces": True,
            "items": [{"img": k + 1, "txt": "ABCD"[k]} for k in range(n)], "indices": []}
    evts = []
    if cfg.get("mike_indice", True):
        faux = random.choice([k for k in range(n) if k != bonne])
        evts.append((duree * 0.55, lambda: etat.update(
            items=[dict(it, barre=True) if k == faux else it for k, it in enumerate(etat["items"])])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]], "indices": list(etat["indices"])})
    return dict(jeu="mike", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=en_jpeg(poster, H),
                images=images, cles=[], bonne="", bonne_i=bonne,
                infos=["la bonne pièce" if k == bonne else "une autre affiche" for k in range(n)],
                solution=f"La pièce {'ABCD'[bonne]}", detail=film["title"], films=[cle_film(film)])
