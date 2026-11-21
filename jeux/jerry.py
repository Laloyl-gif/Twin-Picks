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
from .phonetique import francais, texte as sons_du_texte
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


MORCEAU_MAX = 3            # un bout écrit en lettres : trois sons au plus, sinon le rébus ne vaut rien…
MOT_MAX = 4                # … ou un petit mot entier du titre (« chez », « vers »)


def rebus(titre, rng=random):
    """[{"t": "emoji", "v": émoji, "mot": mot} | {"t": "son", "v": lettres}] et la part des sons dessinés.
    Phonétique française : un titre qui se lit à l'anglaise ne fait pas de rébus (None)."""
    if not francais(titre):
        return None, 0.0
    mots = sons_du_texte(titre)
    sons, fins, debuts, k = "", set(), set(), 0
    ecrits = {}                                     # (début, fin) d'un mot entier -> son orthographe
    for ecrit, s in mots:
        debuts.add(k)
        ecrits[(k, k + len(s))] = ecrit
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
            ecrit = _ecrit(ecrits, i, j)                  # un mot entier sans image : on l'écrit comme dans le titre
            v = ecrit.lower() if ecrit else "".join(LETTRES.get(c, c) for c in frag)
            if out and out[-1]["t"] == "son":
                out[-1]["v"] += (" " if ecrit and out[-1]["entier"] else "") + v
                out[-1]["n"] += j - i
                out[-1]["entier"] = out[-1]["entier"] and bool(ecrit)
            else:
                out.append({"t": "son", "v": v, "n": j - i, "entier": bool(ecrit)})
            # robustesse : un bout en lettres reste court (un petit mot entier, ou trois sons au plus)
            if out[-1]["n"] > (MOT_MAX if out[-1]["entier"] else MORCEAU_MAX):
                return None, 0.0
    for x in out:
        x.pop("n", None)
        x.pop("entier", None)
    return out, dessines / len(sons)


def _ecrit(ecrits, i, j):
    """L'orthographe des mots entiers qui couvrent exactement les sons [i, j), sinon None."""
    morceaux, k = [], i
    while k < j:
        suite = [(a, b) for (a, b) in ecrits if a == k and b <= j]
        if not suite:
            return None
        a, b = max(suite, key=lambda x: x[1])
        morceaux.append(ecrits[(a, b)])
        k = b
    return " ".join(morceaux)


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_jerry"])
    rng = random.Random()
    notes = []
    for f in [x for x in pool if not x.get("tv")]:
        r, part = rebus(f["title"], rng)
        if r and 2 <= len(r) <= 7 and sum(1 for x in r if x["t"] == "emoji") >= 2 and part >= 0.5:
            notes.append((part, f))
    if not notes:
        raise RuntimeError("Le rébus : aucun titre des listes ne se dessine.")
    # plus de variété : tous les titres qui se dessinent bien (au moins 55 % des sons en images), les mieux
    # dessinés un peu plus souvent ; jamais le même deux fois de suite (tirer garde la mémoire de la partie)
    bons = [(p, f) for p, f in notes if p >= 0.65] or notes
    neufs = [(p, f) for p, f in bons if cle_film(f) not in deja] or bons
    film = random.choices([f for _, f in neufs], weights=[0.4 + p for p, _ in neufs])[0]
    deja.add(cle_film(film))
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
