"""Lil's Coded Dress (L'absent) : dans Fire Walk with Me, Lil danse devant les agents ; chaque détail de sa tenue est
un message codé (la rose bleue épinglée sur sa robe…). Ici, neuf objets sont épinglés sur la robe : chacun fait
référence à un film (le requin des Dents de la mer, la bague du Seigneur des anneaux…). Dix affiches sont proposées :
laquelle n'est PAS sur la robe ? Indice (réglable) : deux affiches représentées sont barrées à mi-temps.
"""
import random
import re

from PIL import ImageOps

from texte import normaliser
from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer
from .rebus_dico import EMOJI

NB = 10
VIDES = {"based", "novel", "book", "film", "movie", "sequel", "remake", "duringcreditsstinger", "aftercreditsstinger",
         "woman", "director", "independent", "biography", "relationship", "male", "female", "character", "life"}


def references(api, film):
    """Les objets (émojis) qui évoquent ce film : ses mots-clés TMDB d'abord, puis les mots de son titre."""
    try:
        fi = fiche(api, film)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for kw in fi.get("mots_cles", [])[:20]:
        for m in re.findall(r"[a-z]+", kw.lower()):
            if m not in VIDES and m in EMOJI and EMOJI[m] not in out:
                out.append(EMOJI[m])
    for m in re.findall(r"\w+", film["title"]):
        e = EMOJI.get(normaliser(m))
        if e and e not in out and len(m) > 2:
            out.append(e)
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_lil"])
    cands = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(cands)
    choisis, pris = [], set()
    for f in cands[:60]:
        refs = [e for e in references(api, f) if e not in pris]
        if refs:
            e = refs[0] if random.random() < 0.7 else random.choice(refs)
            choisis.append((f, e))
            pris.add(e)
        if len(choisis) == NB:
            break
    if len(choisis) < NB:
        raise RuntimeError("L'absent : pas assez de films faciles à représenter dans les listes choisies.")
    absent = tirer([f for f, _ in choisis], deja)
    bonne = next(i for i, (f, _) in enumerate(choisis) if f["id"] == absent["id"])
    objets = [e for i, (_, e) in enumerate(choisis) if i != bonne]
    random.shuffle(objets)
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (200, 300)), 300) for f, _ in choisis]
    robe = [{"v": e, "r": random.randint(-18, 18)} for e in objets]
    etat = {"robe": robe, "question": "Quel film n'est pas sur la robe de Lil ?",
            "items": [{"img": i, "txt": f["title"]} for i, (f, _) in enumerate(choisis)], "indices": []}
    evts = []
    if cfg.get("lil_indice", True):
        faux = random.sample([i for i in range(NB) if i != bonne], 2)
        evts.append((duree * 0.55, lambda: etat.update(
            items=[dict(it, barre=True) if i in faux else it for i, it in enumerate(etat["items"])])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]], "indices": list(etat["indices"])})
    infos = [("absent" if i == bonne else f"sur la robe : {e}") for i, (_, e) in enumerate(choisis)]
    return dict(jeu="lil", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None, images=images,
                cles=[], bonne="", bonne_i=bonne, infos=infos, solution=f"L'absent : {absent['title']}",
                detail=" · ".join(f"{e} {f['title']}" for f, e in choisis if f["id"] != absent["id"]),
                films=[cle_film(f) for f, _ in choisis])
