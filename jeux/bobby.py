"""Bobby in the Ghostwood : plusieurs films, lequel est le mieux noté sur TMDB (ou le moins bien, réglable) ?
Une seule réponse par joueur. Indice à mi-temps : la note d'un des autres films."""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film, libelle
from visuels import en_jpeg
from .commun import affiche, chronologie

VOTES_MIN = 150


def note_txt(f):
    return f"★ {f['note']:.1f}".replace(".", ",")


def construire(api, cfg, pool, deja):
    n, duree = cfg["bobby_nb"], float(cfg["dur_bobby"])
    sens = cfg.get("bobby_sens", "mieux")
    if sens == "hasard":
        sens = random.choice(["mieux", "moins"])
    ok = [f for f in pool if f["votes"] >= VOTES_MIN and f["note"] > 0]
    if len(ok) < n:
        raise RuntimeError(f"Bobby in the Ghostwood : il faut {n} films notés sur TMDB (≥ {VOTES_MIN} votes) "
                           "dans les listes choisies.")
    for _ in range(40):
        frais = [f for f in ok if cle_film(f) not in deja]
        if len(frais) < 2 * n:                    # presque tout a été joué : on reprend tous les films
            frais = ok
        choisis = []
        for f in random.sample(frais, len(frais)):
            if all(abs(round(f["note"], 1) - round(g["note"], 1)) >= 0.1 and not sagas.meme_univers(f, g)
                   for g in choisis):
                choisis.append(f)
            if len(choisis) == n:
                break
        if len(choisis) < n:
            continue
        notes = [round(f["note"], 1) for f in choisis]
        bonne = notes.index(max(notes) if sens == "mieux" else min(notes))
        ecart = sorted(notes, reverse=sens == "mieux")
        if abs(ecart[0] - ecart[1]) > 1.8 and len(ok) > 2 * n:          # trop facile : on retente
            continue
        for f in choisis:
            deja.add(cle_film(f))
        affiches = [affiche(api, f, "w342") for f in choisis]
        items = [{"img": i, "txt": libelle(f)} for i, f in enumerate(choisis)]
        etat = {"items": items, "question": "Le mieux noté sur TMDB ?" if sens == "mieux" else
                "Le moins bien noté sur TMDB ?", "indices": []}
        evts = []
        if cfg.get("bobby_indice", True):
            autres = [i for i in range(n) if i != bonne]
            k = random.choice(autres)

            def reveler(k=k):
                etat["items"] = [dict(it, sous=note_txt(choisis[k])) if i == k else it for i, it in enumerate(etat["items"])]
            evts.append((duree * 0.5, reveler))
        etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]]})
        return dict(jeu="bobby", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None,
                    images=[en_jpeg(ImageOps.fit(a, (300, 450)), 450) for a in affiches], cles=[], bonne="",
                    bonne_i=bonne, infos=[f"{note_txt(f)} · {f['votes']} votes" for f in choisis],
                    solution=f"{'Le mieux' if sens == 'mieux' else 'Le moins bien'} noté : {libelle(choisis[bonne])}",
                    detail="Notes TMDB", films=[cle_film(f) for f in choisis])
    raise RuntimeError("Bobby in the Ghostwood : pas assez de films aux notes différentes.")
