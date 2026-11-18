"""Hank's Dominoes (L'alignement) : Hank Jennings aligne ses dominos. Cinq films sont posés comme des dominos, dans le
désordre ; chacun les range selon le critère de la manche (du plus gros box-office au plus petit, du plus long au plus
court, du mieux noté au moins bien noté, du plus cher au moins cher). À la réponse, les dominos se remettent en ordre
et leurs valeurs s'affichent. Points par domino à la bonne place, bonus si tout l'alignement est juste.
(Même mécanique de réponse que La frise de Nadine : touchez les films dans l'ordre.)
"""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie


def millions(x):
    m = x / 1e6
    return (f"{m / 1000:.2f}".replace(".", ",") + " Md$") if m >= 1000 else f"{m:.0f} M$"


CRITERES = {
    "recettes": ("Du plus gros box-office au plus petit", lambda fi: fi.get("recettes", 0), millions, 0.25),
    "budget": ("Du plus gros budget au plus petit", lambda fi: fi.get("budget", 0), millions, 0.25),
    "duree": ("Du plus long au plus court", lambda fi: fi.get("duree", 0), lambda v: f"{v // 60} h {v % 60:02d}", 0.06),
    "note": ("Du mieux noté au moins bien noté (TMDB)", lambda fi: round(fi.get("note", 0), 1),
             lambda v: f"★ {v:.1f}".replace(".", ","), 0.04),
}


def construire(api, cfg, pool, deja):
    nb, duree = 5, float(cfg["dur_hank"])
    crits = [c for c in CRITERES if cfg.get("hank_" + c, True)] or list(CRITERES)
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(films)
    for _ in range(6):
        crit = random.choice(crits)
        titre, val, fmt, ecart = CRITERES[crit]
        choisis = []
        for f in ([x for x in films if cle_film(x) not in deja] or films)[:45]:
            if len(choisis) == nb:
                break
            try:
                v = val(fiche(api, f))
            except Exception:  # noqa: BLE001
                continue
            if not v or any(abs(v - w) <= ecart * max(v, w) for _, w in choisis):
                continue                                 # deux valeurs trop proches : impossible à départager
            if any(sagas.meme_univers(f, g) for g, _ in choisis):
                continue
            choisis.append((f, v))
        if len(choisis) == nb:
            break
    else:
        raise RuntimeError("L'alignement : pas assez de films aux valeurs connues dans les listes.")
    for f, _ in choisis:
        deja.add(cle_film(f))
    ordre = sorted(range(nb), key=lambda i: -choisis[i][1])            # du plus grand au plus petit
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f, _ in choisis]
    valeurs = [fmt(v) for _, v in choisis]
    etat = {"items": [{"img": i, "txt": f["title"]} for i, (f, _) in enumerate(choisis)], "annees": {},
            "consigne": titre, "indices": []}
    evts = []
    if cfg.get("hank_indice", True):
        i = ordre[0]
        evts.append((duree * 0.5, lambda i=i: etat["annees"].update({str(i): valeurs[i]})))
    etapes = chronologie(evts, lambda: {**etat, "annees": dict(etat["annees"]), "indices": list(etat["indices"])})
    return dict(jeu="hank", vue="frise", duree=duree, reponse="ordre", etapes=etapes, revelation=None, images=images,
                cles=[], bonne="", solution=titre, detail=" → ".join(f"{choisis[i][0]['title']} ({valeurs[i]})" for i in ordre),
                ordre=ordre, annees=valeurs, films=[cle_film(f) for f, _ in choisis])
