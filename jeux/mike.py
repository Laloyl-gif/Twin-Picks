"""Mike's Future or Past (L'année) : « Is it future, or is it past? » demande Mike, le manchot. L'affiche d'un film
et son titre : en quelle année est-il sorti ? Chacun tape une année ; l'année exacte rapporte le plus, puis de moins
en moins jusqu'à la tolérance (réglage commun « tolérance des années »). Indices (réglables) : un autre film sorti la
même année, puis la décennie qui se fige sur le compteur.
"""
import random

from PIL import ImageOps

from tmdb import annee, cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_mike"])
    films = [f for f in pool if annee(f).isdigit()]
    if not films:
        raise RuntimeError("L'année : aucun film daté dans les listes choisies.")
    film = tirer(films, deja)
    an = int(annee(film))
    try:
        d = details_film(api, film)
    except Exception:  # noqa: BLE001
        d = {"genres": []}
    voisins = [f for f in pool if annee(f) == str(an) and f["id"] != film["id"]]
    images = [en_jpeg(ImageOps.fit(affiche(api, film, "w500").convert("RGB"), (400, 600)), 600)]
    etat = {"img": 0, "titre": film["title"], "compteur": "????", "indices": []}
    evts = []
    if cfg.get("mike_indices", True):
        if voisins:
            v = random.choice(voisins)
            evts.append((duree * 0.4, lambda: etat["indices"].append(f"La même année sortait : {v['title']}")))
        elif d.get("genres"):
            evts.append((duree * 0.4, lambda: etat["indices"].append("Genre : " + ", ".join(d["genres"][:2]))))
        evts.append((duree * 0.7, lambda: etat.update(compteur=str(an)[:3] + "?")))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    return dict(jeu="mike", vue="annee", duree=duree, reponse="nombre", nombre=an, etapes=etapes, images=images,
                revelation=None, cles=[], bonne=str(an), solution=f"{film['title']} : {an}",
                detail="« Is it future, or is it past? »", films=[cle_film(film)])
