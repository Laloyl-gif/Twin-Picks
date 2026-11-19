"""Sarah Palmer's Visions (La vision) : Sarah Palmer a des visions (le cheval blanc…). Six affiches défilent très vite
sur l'écran, comme une vision, deux fois. Puis la vision s'efface et six affiches reviennent : cinq étaient dans la
vision, une n'y était pas. Laquelle ? (Un jeu de mémoire : on ne peut répondre qu'après la vision.)
"""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche, chronologie

NB = 6


def construire(api, cfg, pool, deja):
    flash = float(cfg["sarah_flash"])
    films = [f for f in pool if f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    choisis = []
    for f in films:
        if not any(f["id"] == g["id"] or sagas.meme_univers(f, g) for g in choisis):
            choisis.append(f)
        if len(choisis) == NB + 1:
            break
    if len(choisis) < NB + 1:
        raise RuntimeError("La vision : pas assez de films dans les listes choisies.")
    for f in choisis:
        deja.add(cle_film(f))
    vus, intrus = choisis[:NB], choisis[NB]
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f in choisis]
    sortie = random.sample(range(NB), NB - 1)                    # les cinq vus qui reviennent
    grille = sortie + [NB]
    random.shuffle(grille)
    bonne = grille.index(NB)
    ordre = list(range(NB))
    random.shuffle(ordre)
    sequence = ordre + random.sample(ordre, NB)                  # deux passages, dans un autre ordre
    etat = {"flash": None, "cheval": True, "items": [], "question": "", "indices": []}
    evts = []
    t = 1.2
    for i in sequence:
        evts.append((round(t, 2), lambda i=i: etat.update(flash=i, cheval=False)))
        t += flash
    fin_vision = t
    evts.append((round(t, 2), lambda: etat.update(flash=None, cheval=True)))
    evts.append((round(t + 1.2, 2), lambda: etat.update(
        cheval=False, question="Lequel n'était pas dans la vision ?",
        items=[{"img": i, "txt": choisis[i]["title"]} for i in grille])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(x) for x in etat["items"]], "indices": list(etat["indices"])})
    duree = fin_vision + 1.2 + float(cfg["dur_sarah"])
    return dict(jeu="sarah", vue="choix", duree=round(duree, 1), reponse="choix", etapes=etapes, images=images,
                revelation=None, cles=[], bonne="", bonne_i=bonne,
                infos=["n'était pas dans la vision" if i == NB else "" for i in grille],
                solution=f"Pas dans la vision : {intrus['title']}",
                detail="La vision : " + " · ".join(f["title"] for f in vus), films=[cle_film(f) for f in choisis])
