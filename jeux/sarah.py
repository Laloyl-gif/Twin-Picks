"""Sarah Palmer's Visions (La vision) : Sarah Palmer a des visions (le cheval blanc…). Des affiches (six par défaut,
réglable) défilent très vite sur l'écran, comme une vision, deux fois. Puis la vision s'efface et autant d'affiches
reviennent : toutes sauf une étaient dans la vision. Laquelle n'y était pas ? (Un jeu de mémoire : on ne peut
répondre qu'après la vision.) Durée de chaque affiche réglable, jusqu'à 0,1 s. Pour corser, certaines affiches passent
retouchées : couleurs inversées, à l'envers, en miroir, en noir et blanc ou teinte changée.
"""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche, chronologie

MODIFS = ("inv", "env", "mir", "nb", "teinte")       # couleurs inversées, à l'envers, miroir, noir et blanc, teinte


def construire(api, cfg, pool, deja):
    flash = float(cfg["sarah_flash"])
    NB = max(3, min(16, int(cfg.get("sarah_nb", 6))))
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
    sortie = random.sample(range(NB), NB - 1)                    # ceux de la vision qui reviennent
    grille = sortie + [NB]
    random.shuffle(grille)
    bonne = grille.index(NB)
    ordre = list(range(NB))
    random.shuffle(ordre)
    sequence = ordre + random.sample(ordre, NB)                  # deux passages, dans un autre ordre
    # La vision est jouée par chaque écran à son rythme (horloge locale calée sur le chrono de la manche) : même à
    # 0,1 s par affiche, aucune n'est sautée.
    proba = float(cfg.get("sarah_modifs", 35)) / 100
    mods = [random.choice(MODIFS) if random.random() < proba else "" for _ in sequence]
    t0 = 1.2
    fin_vision = t0 + flash * len(sequence)
    etat = {"sequence": sequence, "mods": mods, "t0": t0, "pas": flash, "items": [], "question": "", "indices": [], "nb": NB}
    evts = [(round(fin_vision, 2), lambda: etat.update(sequence=[], mods=[])),
            (round(fin_vision + 1.2, 2), lambda: etat.update(
                question="Lequel n'était pas dans la vision ?",
                items=[{"img": i, "txt": choisis[i]["title"]} for i in grille]))]
    etapes = chronologie(evts, lambda: {**etat, "sequence": list(etat["sequence"]), "mods": list(etat["mods"]), "items": [dict(x) for x in etat["items"]],
                                        "indices": list(etat["indices"])})
    duree = fin_vision + 1.2 + float(cfg["dur_sarah"])
    return dict(jeu="sarah", vue="choix", duree=round(duree, 1), reponse="choix", etapes=etapes, images=images,
                revelation=None, cles=[], bonne="", bonne_i=bonne,
                infos=["n'était pas dans la vision" if i == NB else "" for i in grille],
                solution=f"Pas dans la vision : {intrus['title']}",
                detail="La vision : " + " · ".join(f["title"] for f in vus), films=[cle_film(f) for f in choisis])
