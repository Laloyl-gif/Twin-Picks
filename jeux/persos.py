"""Janey-E's Owls : les noms des personnages apparaissent un à un (du second rôle au premier).

On commence avec un seul personnage. Indices de plus en plus parlants (réglable) : l'année et le genre,
le réalisateur, puis le nom de l'acteur sous chaque personnage, et enfin le titre à trous.
"""
import re

from texte import normaliser
from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, horaires, manche_titre, reponse_affichee, tirer, trous

EXCLUS = re.compile(r"\b(self|himself|herself|narrator|narrateur|voice|voices|voix|uncredited|archive|additional|"
                    r"various|lui-m[eê]me|elle-m[eê]me|cameo)\b", re.I)
MOTS_VIDES = {"le", "la", "les", "un", "une", "des", "du", "de", "the", "of", "and", "et", "mr", "mrs", "dr", "an"}


def nettoyer(nom):
    nom = re.sub(r"[\(\[].*?[\)\]]", "", nom or "").split("/")[0]
    return " ".join(nom.split()).strip(" -'\"")


def construire(api, cfg, pool, deja):
    nmax, duree = cfg["persos_max"], float(cfg["dur_persos"])
    for _ in range(12):
        film = tirer(pool, deja, lambda f: not f["tv"])
        d = details_film(api, film)
        interdits = d["noms"] + [film["title"]] + ([d["saga"]] if d.get("saga") else [])
        titre = {m for t in interdits for m in normaliser(t).split() if len(m) >= 3 and m not in MOTS_VIDES}
        fi = fiche(api, film)
        persos, vus = [], set()
        for a in fi["acteurs"]:
            brut = a["role"] or ""
            nom = nettoyer(brut)
            k = normaliser(nom)
            if not k or len(nom) > 40 or EXCLUS.search(brut) or k in vus or set(k.split()) & titre:
                continue                                  # vide, figurant, doublon, ou personnage qui donne le titre
            vus.add(k)
            persos.append({"n": nom, "acteur": a["nom"]})
            if len(persos) == nmax:
                break
        if len(persos) < min(3, nmax):
            continue
        persos.reverse()                                  # du second rôle au premier
        temps = horaires(len(persos), 1, cfg["persos_intervalle"])
        etat = {"nb": 0, "acteurs": False, "indices": [], "trous": ""}
        evts = [(t, lambda k=k: etat.update(nb=k + 1)) for k, t in enumerate(temps)]
        if cfg.get("persos_indices", True):
            reponse = reponse_affichee(cfg, film, d)
            depart = " · ".join(x for x in (d["annee"], ", ".join(d["genres"][:2])) if x)
            if depart:
                evts.append((duree * 0.25, lambda: etat["indices"].append(depart)))
            if fi["realisateurs"]:
                reals = " et ".join(r["nom"] for r in fi["realisateurs"][:2])
                evts.append((duree * 0.42, lambda: etat["indices"].append(f"Réalisé par {reals}")))
            evts.append((duree * 0.58, lambda: etat.update(acteurs=True)))
            evts.append((duree * 0.76, lambda: etat.update(trous=trous(reponse, 0))))
            evts.append((duree * 0.88, lambda: etat.update(trous=trous(reponse, 0.35))))

        def photo():
            noms = [dict({"n": p["n"]}, **({"sous": p["acteur"]} if etat["acteurs"] else {}))
                    for p in persos[:etat["nb"]]]
            return {"noms": noms, "total": len(persos), "indices": list(etat["indices"]), "trous": etat["trous"]}

        etapes = chronologie(evts, photo)
        return manche_titre("persos", "noms", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    raise RuntimeError("Aucun film avec assez de personnages nommés (listes trop petites ?).")
