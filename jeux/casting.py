"""Audrey's Dance (Acteurs → film) : les acteurs principaux apparaissent un par un, sans autre indice.
Ce sont toujours les X acteurs principaux du film (ordre du générique), qui arrivent dans un ordre aléatoire
(réglable : au hasard, têtes d'affiche d'abord, ou à l'envers)."""
import random

from PIL import ImageOps

from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, grille, horaires, manche_titre, tirer


def construire(api, cfg, pool, deja):
    nmax, duree = cfg["casting_max"], float(cfg["dur_casting"])
    for _ in range(10):
        film = tirer(pool, deja, lambda f: not f["tv"])
        fi = fiche(api, film)
        cast = sorted([a for a in fi["acteurs"] if a["photo"]], key=lambda a: a.get("ordre", 99))
        if len(cast) < min(nmax, 3):
            continue
        choisis = cast[:nmax]
        ordre = cfg.get("casting_ordre", "hasard")
        if ordre == "hasard":
            random.shuffle(choisis)
        elif ordre == "inverse":
            choisis.reverse()
        photos = api.images([c["photo"] for c in choisis], "w185")
        d = details_film(api, film)
        temps = horaires(len(choisis), 1, cfg["casting_intervalle"])
        etapes = grille(temps, [c["nom"] for c in choisis])
        return manche_titre("casting", "grille", duree, film, d, etapes,
                            [en_jpeg(ImageOps.fit(p, (200, 300)), 300) for p in photos],
                            en_jpeg(affiche(api, film, "w500")), cfg)
    raise RuntimeError("Aucun film avec un casting exploitable (listes trop petites ?).")
