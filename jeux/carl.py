"""Carl's Fat Trout Trailers (Les deux films) : au camping de caravanes « Fat Trout » de Carl Rodd, on regarde par
la fenêtre d'une caravane… mais derrière le store vénitien, deux films se mélangent : une lame sur deux montre une
image du film A, l'autre une image du film B. Les lames s'ouvrent une à une, dans le désordre. Il faut trouver les
DEUX films : chacun rapporte des points, les deux ensemble un bonus. À la réponse : les deux affiches.
"""
import random

from PIL import Image, ImageOps

import images_film as imf
from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, cles_reponses, reponse_affichee, saga_de, tirer, trous

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
                revelation=en_jpeg(duo), reponse="plusieurs", suggestions=True,
                films_cles=[cles_reponses(fa["title"], fa.get("original_title"), *da["noms"],
                                          *([saga_de(cfg, da)] if saga_de(cfg, da) else [])),
                            cles_reponses(fb["title"], fb.get("original_title"), *db["noms"],
                                          *([saga_de(cfg, db)] if saga_de(cfg, db) else []))],
                films_titres=titres, cles=[], bonne="", solution=" + ".join(titres),
                detail="Une lame sur deux : " + " · ".join(titres), films=[cle_film(fa), cle_film(fb)])


from .plusieurs import Moteur  # noqa: E402,F401  (les deux films : le moteur « plusieurs films à trouver »)
