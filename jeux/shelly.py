"""Shelly's Black Coffee : retrouvez le film à partir des notes des joueurs présents (profils).

Le film est toujours un film noté par TOUS les joueurs présents qui ont des notes (intersection des profils).
Dès le début : la moyenne des notes, leur étendue (la plus basse et la plus haute, sans dire qui les a données)
et le genre.
Puis des indices de plus en plus parlants : décennie, pays, durée, année, réalisateur, acteurs (du second rôle
à la tête d'affiche), et enfin le titre à trous.
"""
from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous


def duree_txt(minutes):
    return f"{minutes // 60} h {minutes % 60:02d}" if minutes >= 60 else f"{minutes} min"


def construire(api, cfg, pool, deja):
    # le film a été vu (noté) par TOUS les joueurs présents qui ont des notes : l'intersection de leurs notes
    presents = {p["nom"] for p in cfg.get("_profils", []) if p.get("notes")}
    if not presents:
        raise RuntimeError("La moyenne : aucun joueur présent n'a de notes.")
    if not any(presents <= set(f["notes"]) for f in pool):
        raise RuntimeError("La moyenne : aucun film n'a été noté par tous les joueurs présents ("
                           + ", ".join(sorted(presents)) + ").")
    film = tirer(pool, deja, lambda f: presents <= set(f["notes"]))
    notes = {n: v for n, v in film["notes"].items() if n in presents}
    d, fi = details_film(api, film), fiche(api, film)
    duree = float(cfg["dur_shelly"])
    valeurs = sorted(notes.values())
    jauge = {"moyenne": round(sum(valeurs) / len(valeurs), 1), "min": valeurs[0], "max": valeurs[-1],
             "nb": len(valeurs), "ecart": valeurs[-1] - valeurs[0]}
    etat = {"jauge": jauge, "indices": [], "trous": ""}
    prevus = []
    if fi["genres"]:
        etat["indices"].append("Genre : " + ", ".join(fi["genres"][:2]))
    an = fi["annee"] or d["annee"]
    if an:
        prevus.append((0.14, f"Années {an[:3]}0"))
    if fi["pays"]:
        prevus.append((0.26, "Pays : " + ", ".join(fi["pays"][:2])))
    if fi["duree"]:
        prevus.append((0.36, ("Épisodes de " if fi["tv"] else "Durée : ") + duree_txt(fi["duree"])))
    if an:
        prevus.append((0.46, f"Sorti en {an}"))
    if fi["realisateurs"]:
        prevus.append((0.56, ("Créé par " if fi["tv"] else "Réalisé par ") + " et ".join(r["nom"] for r in fi["realisateurs"][:2])))
    acteurs = [a["nom"] for a in fi["acteurs"][:3]]
    for k, nom in enumerate(reversed(acteurs)):                 # du 3e rôle à la tête d'affiche
        prevus.append((0.65 + 0.08 * k, f"Avec {nom}"))
    evts = [(duree * t, lambda txt=txt: etat["indices"].append(txt)) for t, txt in prevus]
    if cfg.get("shelly_titre", True):
        evts.append((duree * 0.9, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    m = manche_titre("shelly", "fiche", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    m["detail"] = " · ".join(x for x in [m.get("detail", "")] + [f"{n} {v}/10" for n, v in
                                                                sorted(notes.items(), key=lambda x: -x[1])] if x)
    return m
