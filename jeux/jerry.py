"""Jerry's Trip (Le rébus) : perdu dans les bois, Jerry Horne voit des choses (« Tu n'es pas mon pied ! »). Ici, le
titre du film est un vrai rébus phonétique : il est découpé en sons, et chaque morceau est dessiné par un mot qui se
prononce pareil (ou presque), articles et noms propres compris (« Le Roi lion » : 🥛 👑 🦁 = lait-roi-lion). Un même son
peut avoir plusieurs images (« de » : 🎲 ou 2️⃣ ? tiré au sort à chaque manche). Indices : genre et année, puis les mots
sous les images, puis le titre à trous.
"""
import itertools
import random

from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous
from .phonetique import texte as sons_du_texte
from .rebus_sons import LONGUEUR_MAX, PRESQUE, VOCAB

PROCHES = {"2": "e", "e": "2", "i": "j", "j": "i", "u": "w", "w": "u"}     # sons interchangeables (coût en plus)
LETTRES = {"a": "a", "e": "é", "2": "e", "i": "i", "o": "o", "u": "ou", "y": "u", "A": "an", "O": "on", "I": "in",
           "S": "ch", "Z": "j", "N": "gn", "j": "y", "w": "w"}


def _variantes(frag):
    """Le fragment et ses variantes proches (« l2 » ≈ « le »), avec leur coût."""
    pos = [i for i, c in enumerate(frag) if c in PROCHES]
    yield frag, 0.0
    for k in range(1, min(2, len(pos)) + 1):
        for choix in itertools.combinations(pos, k):
            v = list(frag)
            for i in choix:
                v[i] = PROCHES[v[i]]
            yield "".join(v), 0.45 * k


def _proches(frag):
    """Les sons du vocabulaire qui dessinent ce fragment : le même son, ou à une consonne près."""
    if frag in VOCAB:
        yield frag, 0.0
    for k in PRESQUE.get(frag, ()):                       # l'image a une consonne de plus (« tour » pour « tou »)
        yield k, 0.7
    if len(frag) > 2:
        for i, c in enumerate(frag):                      # le titre a une consonne de plus (« dent » pour « dents »)
            if c not in "ae2ioyuAOI":
                v = frag[:i] + frag[i + 1:]
                if v in VOCAB:
                    yield v, 0.8


def decouper(sons):
    """Le découpage du texte en mots-images qui coûte le moins : [(début, fin, son du vocabulaire ou None)]."""
    n = len(sons)
    inf = float("inf")
    cout, prec = [0.0] + [inf] * n, [None] * (n + 1)
    for i in range(n):
        if cout[i] == inf:
            continue
        if sons[i] == "2" and cout[i] + 0.35 < cout[i + 1]:                       # e muet qu'on peut avaler
            cout[i + 1], prec[i + 1] = cout[i] + 0.35, (i, "")
        for L in range(1, min(LONGUEUR_MAX, n - i) + 1):
            for v, extra in _variantes(sons[i:i + L]):
                for k, e2 in _proches(v):
                    c = cout[i] + 1 + extra + e2
                    if c < cout[i + L]:
                        cout[i + L], prec[i + L] = c, (i, k)
        c = cout[i] + 2.6                                                          # un son écrit en lettres
        if c < cout[i + 1]:
            cout[i + 1], prec[i + 1] = c, (i, None)
    morceaux, j = [], n
    while j > 0:
        i, v = prec[j]
        if v != "":
            morceaux.append((i, j, v))
        j = i
    return list(reversed(morceaux))


def rebus(titre, rng=random):
    """[{"t": "emoji", "v": émoji, "mot": mot} | {"t": "son", "v": lettres}] et la part des sons dessinés."""
    sons = "".join(s for _, s in sons_du_texte(titre))
    if not sons:
        return None, 0.0
    out, dessines = [], 0
    for i, j, v in decouper(sons):
        if v:
            mot, emo = rng.choice(VOCAB[v])
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
        if r and 2 <= len(r) <= 8:
            notes.append((part, f))
    if not notes:
        raise RuntimeError("Le rébus : aucun titre des listes ne se dessine.")
    meilleurs = [f for p, f in notes if p >= 0.999] or [f for p, f in notes if p >= 0.85] or [f for _, f in notes]
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
