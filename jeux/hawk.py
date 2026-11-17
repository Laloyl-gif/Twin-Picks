"""Hawk's Missing Pages (L'accroche) : comme les pages du journal de Laura que Hawk retrouve cachées dans la porte
des toilettes, des fragments de papier réapparaissent : l'accroche (le slogan de l'affiche) du film, mot à mot.

Le slogan vient de TMDB (en français, sinon en anglais) et s'affiche EN ENTIER dès le début (les mots du titre ou de
la saga sont masqués). Puis des indices arrivent petit à petit (réglables) : genre et année, réalisateur, acteur
principal, personnage principal, titre à trous, et enfin quelques lettres en plus.
"""
import random
import re

from texte import normaliser
from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

MOTS_VIDES = {"le", "la", "les", "un", "une", "des", "du", "de", "the", "of", "and", "et", "an", "in", "on", "to",
              "en", "au", "aux", "a"}


def decouper(slogan, titres):
    """[(mot, masqué)] ; les mots du titre deviennent ▒▒▒."""
    interdits = {m for t in titres for m in normaliser(t).split() if len(m) >= 3 and m not in MOTS_VIDES}
    out = []
    for m in slogan.split():
        coeur = normaliser(re.sub(r"[^\w'’-]", "", m))
        masque = bool(coeur) and any(x in interdits for x in coeur.split())
        out.append(("▒" * max(3, len(m)) if masque else m, masque))
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_hawk"])
    for _ in range(20):
        film = tirer(pool, deja)
        d = details_film(api, film)
        slogan, langue = d.get("slogan") or "", "fr"
        if len(slogan.split()) < 3:
            slogan, langue = d.get("slogan_en") or "", "en"
        if len(slogan.split()) < 3 or len(slogan) > 160:
            continue
        titres = d["noms"] + [film["title"]] + ([d["saga"]] if d.get("saga") else [])
        mots = decouper(slogan, titres)
        if sum(1 for _, m in mots if not m) < 3:
            continue
        break
    else:
        raise RuntimeError("L'accroche : aucun film des listes n'a de slogan sur TMDB.")
    etat = {"mots": [m for m, _ in mots], "masques": [m for _, m in mots], "longs": [len(m) for m, _ in mots],
            "langue": langue, "indices": [], "trous": ""}
    evts = []
    if cfg.get("hawk_indices", True):
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            fi = {"realisateurs": [], "acteurs": []}
        prevus = []
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            prevus.append((0.18, depart))
        if fi.get("realisateurs"):
            prevus.append((0.34, "Réalisé par " + fi["realisateurs"][0]["nom"]))
        acteurs = fi.get("acteurs") or []
        if acteurs:
            prevus.append((0.48, "Avec " + acteurs[0]["nom"]))
            role = (acteurs[0].get("role") or "").split("/")[0].strip()
            if role and not set(normaliser(role).split()) & {m for t in titres for m in normaliser(t).split() if len(m) >= 3}:
                prevus.append((0.6, f"Personnage principal : {role}"))
        evts += [(duree * t, lambda txt=txt: etat["indices"].append(txt)) for t, txt in prevus]
        rep = reponse_affichee(cfg, film, d)
        evts.append((duree * 0.72, lambda: etat.update(trous=trous(rep, 0))))
        evts.append((duree * 0.86, lambda: etat.update(trous=trous(rep, 0.35))))
    etapes = chronologie(evts, lambda: {**etat, "mots": list(etat["mots"]), "indices": list(etat["indices"])})
    m = manche_titre("hawk", "pages", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    m["detail"] = (m.get("detail", "") + " · " if m.get("detail") else "") + f"« {slogan} »"
    return m
