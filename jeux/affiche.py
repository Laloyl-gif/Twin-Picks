"""Affiche déformée (Cooper's Investigation) : l'affiche redevient nette peu à peu.

La simplification est linéaire sur TOUTE la manche : les effets diminuent régulièrement, du départ jusqu'à la fin,
où il ne reste que aff_final % des effets (10 % par défaut). L'affiche n'est donc presque nette qu'à la toute fin.
"""
from PIL import ImageOps

from tmdb import details_film
from visuels import en_jpeg, etapes_effets
from .commun import manche_titre, tirer


def construire(api, cfg, pool, deja):
    film = tirer(pool, deja, lambda f: f.get("poster_path"))
    orig = ImageOps.contain(api.image(film["poster_path"], "w500"), (480, 720))
    duree = float(cfg["dur_affiche"])
    n = max(4, int(cfg["aff_etapes"]))
    vues = etapes_effets(orig, cfg["aff_effets"], cfg["aff_puissance"], n, cfg["aff_final"] / 100)
    n = len(vues)
    # étape k affichée à k/(n-1) de la manche : la dernière (aff_final %) arrive juste avant la fin
    fin = max(1.0, duree - 1.0)
    etapes = [(round(fin * k / (n - 1), 2), {"img": k}) for k in range(n)]
    return manche_titre("affiche", "image", duree, film, details_film(api, film),
                        etapes, [en_jpeg(v) for v in vues], en_jpeg(orig), cfg)
