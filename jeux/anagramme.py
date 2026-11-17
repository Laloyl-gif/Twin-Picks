"""Anagramme : lettres mélangées dans chaque mot ; indices puis vraies lettres placées au fil du temps."""
import random

from texte import est_latin, normaliser
from tmdb import details_film
from visuels import en_jpeg
from .commun import affiche, manche_titre, tirer


def melanger(mot):
    lettres = list(mot)
    if len(set(lettres)) > 1:
        for _ in range(30):
            random.shuffle(lettres)
            if lettres != list(mot):
                break
    return lettres


def affichage(mots, melanges, fixes):
    """Tuiles de chaque mot : les positions fixées montrent la bonne lettre (ok), les autres
    gardent les lettres restantes dans l'ordre du mélange."""
    out = []
    for w, (mot, mel) in enumerate(zip(mots, melanges)):
        reste = list(mel)
        for i in range(len(mot)):
            if (w, i) in fixes:
                reste.remove(mot[i])
        libres = iter(reste)
        out.append([{"c": mot[i], "ok": True} if (w, i) in fixes else {"c": next(libres), "ok": False}
                    for i in range(len(mot))])
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_anagramme"])
    for _ in range(30):
        film = tirer(pool, deja, lambda f: est_latin(f["title"]))
        mots = [m.upper() for m in normaliser(film["title"]).split()]
        total = sum(map(len, mots))
        if not 3 <= total <= 32:
            continue
        melanges = [melanger(m) for m in mots]
        d = details_film(api, film)
        evts = []
        if d["genres"]:
            evts.append((duree * 0.15, "indice", "Genre : " + ", ".join(d["genres"][:2])))
        if d["annee"]:
            evts.append((duree * 0.30, "indice", f"Sortie : {d['annee']}"))
        premieres = [(w, 0) for w in range(len(mots))]
        autres = [(w, i) for w, m in enumerate(mots) for i in range(1, len(m))]
        random.shuffle(premieres)
        random.shuffle(autres)
        ordre = premieres + autres                       # d'abord la 1re lettre de chaque mot
        nb = min(total - 1, round(total * cfg["ana_lettres"] / 100))
        t1 = duree * 0.92
        t0 = min(t1, duree * cfg["ana_debut"] / 100)
        for k in range(nb):
            evts.append((t0 + (t1 - t0) * k / max(1, nb - 1), "lettre", ordre[k]))
        evts.sort(key=lambda e: e[0])

        indices, fixes = [], set()

        def etat():
            return {"mots": affichage(mots, melanges, fixes), "indices": list(indices)}

        etapes = [(0.0, etat())]
        for t, genre, val in evts:
            if genre == "indice":
                indices.append(val)
            else:
                fixes.add(val)
            if etapes[-1][0] == t:
                etapes[-1] = (t, etat())
            else:
                etapes.append((t, etat()))
        return manche_titre("anagramme", "anagramme", duree, film, d, etapes, [],
                            en_jpeg(affiche(api, film, "w500")))
    raise RuntimeError("Aucun titre exploitable pour l'anagramme (listes trop petites ?).")
