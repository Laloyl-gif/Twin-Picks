"""Mr. C's Coordinates (Les coordonnées) : Mr. C, le double maléfique de Cooper, cherche des coordonnées (des
nombres). Ici, le film n'est donné que par ses nombres, un à un, sur le papier de Mr. C : année, durée, note TMDB,
budget, recettes, nombre de mots du titre… Indices à la fin : genre, puis titre à trous.
"""
import random
import re

from tmdb import cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous


def millions(x):
    m = x / 1e6
    return f"{m / 1000:.2f}".replace(".", ",") + " Md$" if m >= 1000 else f"{m:.0f} M$"


def nombres(film, fi, d):
    titre = film["title"]
    out = []
    if d["annee"]:
        out.append((d["annee"], "année de sortie"))
    if fi.get("duree"):
        out.append((str(fi["duree"]), "minutes"))
    if fi.get("note"):
        out.append((f"{fi['note']:.1f}".replace(".", ","), "note TMDB sur 10"))
    if fi.get("budget", 0) >= 1e6:
        out.append((millions(fi["budget"]), "budget"))
    if fi.get("recettes", 0) >= 1e6:
        out.append((millions(fi["recettes"]), "recettes dans le monde"))
    mots = re.findall(r"\w+", titre)
    out.append((str(len(mots)), "mot" + ("s" if len(mots) > 1 else "") + " dans le titre"))
    out.append((str(sum(len(m) for m in mots)), "lettres dans le titre"))
    if fi.get("acteurs"):
        a = fi["acteurs"][0]["nom"]
        out.append((str(len(a.replace(" ", ""))), "lettres dans le nom de l'acteur principal"))
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_mrc"])
    for _ in range(10):
        film = tirer(pool, deja, lambda f: not f.get("tv"))
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        d = details_film(api, film)
        ns = nombres(film, fi, d)
        if len(ns) >= 5:
            break
    else:
        raise RuntimeError("Les coordonnées : pas assez de nombres connus pour les films des listes.")
    debut = ns[:2]                                    # l'année et la durée d'abord, le reste au hasard
    reste = ns[2:]
    random.shuffle(reste)
    ns = (debut + reste)[:7]
    n = len(ns)
    etat = {"nombres": [], "total": n, "indices": [], "trous": ""}
    evts = [(round(duree * 0.6 * k / max(1, n - 1), 2), lambda k=k: etat.update(nombres=[list(x) for x in ns[:k + 1]]))
            for k in range(n)]
    if d["genres"]:
        evts.append((duree * 0.68, lambda: etat["indices"].append(", ".join(d["genres"][:2]))))
    evts.append((duree * 0.82, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "nombres": [list(x) for x in etat["nombres"]], "indices": list(etat["indices"])})
    m = manche_titre("mrc", "coordonnees", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    m["films"] = [cle_film(film)]
    return m
