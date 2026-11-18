"""Jerry's Trip (Le rébus) : perdu dans les bois, Jerry Horne voit des choses (« Tu n'es pas mon pied ! »). Ici, le
titre du film est un vrai rébus phonétique : il est découpé en sons, et chaque morceau est dessiné par un mot qui a
exactement les mêmes sons (« Le Roi lion » : le + 🤴 + 🦁). Les images montrent directement le mot (jamais une girafe
pour « zoo » : un cadre avec une girafe, un lion et un tigre). Un son sans image s'écrit en lettres. Un même son
peut avoir plusieurs images (« dé » : 🎲 ; « deux » : 2️⃣…, tiré au sort à chaque manche). Indices : genre et année, puis les mots
sous les images, puis le titre à trous.
"""
import random

from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous
from .phonetique import texte as sons_du_texte
from .rebus_sons import LONGUEUR_MAX, VOCAB

LETTRES = {"a": "a", "e": "é", "2": "e", "i": "i", "o": "o", "u": "ou", "y": "u", "A": "an", "O": "on", "I": "in",
           "S": "ch", "Z": "j", "N": "gn", "j": "y", "w": "w"}


LETTRES_IMAGES = {"a", "be", "o", "i", "em", "pe"}           # 🅰️ 🅱️ … : des lettres, moins jolies qu'une vraie image


def decouper(sons, fins=(), debuts=(0,)):
    """Le découpage du texte en mots-images qui coûte le moins : [(début, fin, son du vocabulaire ou None)].
    Les images ont exactement les sons du titre (pas de « lait » pour « le ») ; ce qui n'a pas d'image s'écrit en
    lettres. Une image qui tombe pile sur un mot du titre est préférée (fins, debuts : les bornes des mots)."""
    n = len(sons)
    inf = float("inf")
    cout, prec = [0.0] + [inf] * n, [None] * (n + 1)
    bornes = set(fins) | set(debuts) | {0, n}
    for i in range(n):
        if cout[i] == inf:
            continue
        for L in range(1, min(LONGUEUR_MAX, n - i) + 1):
            v = sons[i:i + L]
            if v in VOCAB:
                c = cout[i] + (1.25 if v in LETTRES_IMAGES or len(v) == 1 else 1.0) - \
                    (0.3 if i in bornes and i + L in bornes else 0)
                if c < cout[i + L]:
                    cout[i + L], prec[i + L] = c, (i, v)
            c = cout[i] + 0.6 + 1.0 * L                                    # un morceau écrit en lettres
            if c < cout[i + L]:
                cout[i + L], prec[i + L] = c, (i, None)
    morceaux, j = [], n
    while j > 0:
        i, v = prec[j]
        if v != "":
            morceaux.append((i, j, v))
        j = i
    return list(reversed(morceaux))


def rebus(titre, rng=random):
    """[{"t": "emoji", "v": émoji, "mot": mot} | {"t": "son", "v": lettres}] et la part des sons dessinés."""
    mots = sons_du_texte(titre)
    sons, fins, debuts, k = "", set(), set(), 0
    for _, s in mots:
        debuts.add(k)
        sons += s
        k += len(s)
        fins.add(k)
    if not sons:
        return None, 0.0
    out, dessines = [], 0
    for i, j, v in decouper(sons, fins, debuts):
        if v:
            mot, emo = rng.choice(VOCAB[v])
            if emo.startswith("["):                       # plusieurs images dans un cadre (« zoo » : girafe, lion, tigre)
                out.append({"t": "emoji", "v": emo.strip("[]"), "mot": mot, "cadre": True})
            else:
                out.append({"t": "emoji", "v": emo, "mot": mot})
            dessines += j - i
        else:
            frag = sons[i:j]
            if out and out[-1]["t"] == "son":
                out[-1]["v"] += "".join(LETTRES.get(c, c) for c in frag)
            else:
                out.append({"t": "son", "v": "".join(LETTRES.get(c, c) for c in frag)})
    return out, dessines / len(sons)


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_jerry"])
    rng = random.Random()
    notes = []
    for f in [x for x in pool if not x.get("tv")]:
        r, part = rebus(f["title"], rng)
        if r and 2 <= len(r) <= 8 and sum(1 for x in r if x["t"] == "emoji") >= 2:
            notes.append((part, f))
    if not notes:
        raise RuntimeError("Le rébus : aucun titre des listes ne se dessine.")
    meilleurs = ([f for p, f in notes if p >= 0.85] or [f for p, f in notes if p >= 0.6] or
                 [f for _, f in notes])
    film = tirer(meilleurs, deja)
    r, _ = rebus(film["title"], rng)
    d = details_film(api, film)
    etat = {"rebus": r, "mots": False, "indices": [], "trous": ""}
    evts = []
    if cfg.get("jerry_indices", True):
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            evts.append((duree * 0.4, lambda: etat["indices"].append(depart)))
        evts.append((duree * 0.6, lambda: etat.update(mots=True)))
    evts.append((duree * 0.82, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    m = manche_titre("jerry", "rebus", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    m["films"] = [cle_film(film)]
    m["detail"] = " + ".join(x["mot"] if x["t"] == "emoji" else x["v"] for x in r)
    return m
