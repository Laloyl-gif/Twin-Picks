"""The Giant's Three Clues (Les trois répliques) : comme le Géant qui apparaît à Cooper avec trois indices
énigmatiques (« Il y a un homme dans un sac qui sourit »), trois RÉPLIQUES du film arrivent l'une après l'autre, sur
trois cartons. Les mots du titre y sont cachés. Répliques tirées de Wikiquote (voir repliques.py), en français si la
page existe, sinon en anglais. Titre à trous à la fin (réglable). Il faut Internet (sinon : message d'erreur).
"""
import random

from tmdb import details_film
from texte import normaliser
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous
from .repliques import affichage, masquer, repliques


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_geant"])
    essayes = []
    for _ in range(14):
        film = tirer(pool, deja, lambda f: not f.get("tv"))
        essayes.append(film)
        rep = repliques(api, film)
        d = details_film(api, film)
        mots = {normaliser(m) for t in d["noms"] + [film["title"], d.get("saga") or ""] for m in t.split()
                if len(normaliser(m)) >= 4}
        cands = [t for _, t in rep["repliques"] if 15 <= len(t) <= 170]
        if len(cands) >= 3:
            break
    else:
        raise RuntimeError("Les trois répliques : aucune réplique trouvée sur Wikiquote pour les films des listes "
                           "(il faut Internet).")
    for f in essayes[:-1]:
        deja.discard(("m" if not f.get("tv") else "tv", f["id"]))
    trois = random.sample(cands, 3)
    trois.sort(key=lambda t: -len(t))                    # la plus longue (souvent la moins connue) d'abord
    trois = [{k: masquer(v, mots) for k, v in affichage(cfg, t, rep["langue"]).items()} for t in trois]
    etat = {"indices3": [trois[0]], "trous": ""}
    evts = [(duree * 0.3, lambda: etat["indices3"].append(trois[1])), (duree * 0.6, lambda: etat["indices3"].append(trois[2]))]
    if cfg.get("geant_trous", True):
        evts.append((duree * 0.85, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices3": list(etat["indices3"])})
    return manche_titre("geant", "geant", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
