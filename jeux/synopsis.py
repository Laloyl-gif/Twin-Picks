"""Synopsis : le résumé du film, mots du titre masqués, qui se dévoile mot à mot."""
import math
import re

from texte import normaliser
from tmdb import details_film
from visuels import en_jpeg
from .commun import affiche, manche_titre, reponse_affichee, tirer

MOTS_VIDES = {"le", "la", "les", "un", "une", "des", "du", "de", "the", "of", "and", "et",
              "an", "in", "on", "to", "en", "au", "aux"}


def masquer(texte, titres):
    interdits = {m for t in titres for m in normaliser(t).split() if len(m) >= 3 and m not in MOTS_VIDES}
    return "".join("▒" * len(m) if normaliser(m) in interdits else m for m in re.split(r"(\w+)", texte))


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_synopsis"])
    for _ in range(15):
        film = tirer(pool, deja)
        d = details_film(api, film)
        mots = masquer(d["resume"] or "", d["noms"] + [film["title"]] + ([d["saga"]] if d.get("saga") else [])).split()
        if len(mots) < 12:
            continue
        n = len(mots)
        debut = max(1, math.ceil(n * cfg["syn_debut"] / 100))
        indices = ["Genre : " + ", ".join(d["genres"][:2])] if d["genres"] else []
        etapes = []
        for k in range(9):                               # le texte se complète jusqu'à 65 % du temps
            vis = min(n, debut + round((n - debut) * k / 8))
            etapes.append((duree * 0.65 * k / 8, {"texte": " ".join(mots[:vis]) + (" …" if vis < n else ""),
                                                  "indices": list(indices)}))
        texte = etapes[-1][1]["texte"]
        if d["annee"]:
            indices.append(f"Sortie : {d['annee']}")
            etapes.append((duree * 0.72, {"texte": texte, "indices": list(indices)}))
        rep = reponse_affichee(cfg, film, d)
        nb_mots = len(normaliser(rep).split())
        indices.append(f"{'Saga' if rep != film['title'] else 'Titre'} en {nb_mots} mot{'s' if nb_mots > 1 else ''}, "
                       f"commence par « {rep[0].upper()} »")
        etapes.append((duree * 0.85, {"texte": texte, "indices": list(indices)}))
        return manche_titre("synopsis", "texte", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    raise RuntimeError("Aucun résumé exploitable (films sans synopsis ?).")
