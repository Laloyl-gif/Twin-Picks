"""Maddy's Impersonation (Qui l'a dit ?) : Maddy se fait passer pour sa cousine Laura, perruque blonde comprise.
Ici, une réplique du film (Wikiquote) : qui l'a dite ? Quatre personnages du film (photo de l'acteur, nom du
personnage) ; un seul est le bon. Le film est montré. Il faut Internet.
Indice à mi-temps (réglable) : un des mauvais personnages s'efface.
"""
import random

from PIL import ImageOps

from tmdb import cle_film, details_film, fiche
from texte import normaliser
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer
from .repliques import affichage, masquer, meme_personne, repliques


def _role(a):
    return (a.get("role") or "").split("/")[0].strip()


def construire(api, cfg, pool, deja):
    duree, n = float(cfg["dur_maddy"]), int(cfg.get("maddy_choix", 4))
    for _ in range(14):
        film = tirer(pool, deja, lambda f: not f.get("tv") and f.get("poster_path"))
        rep = repliques(api, film)
        if not rep["repliques"]:
            continue
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        cast = [a for a in fi["acteurs"][:14] if a.get("photo") and _role(a)]
        possibles = []
        for qui, txt in rep["repliques"]:
            if not qui or not 15 <= len(txt) <= 200:
                continue
            bons = [a for a in cast if meme_personne(qui, _role(a))]
            if len(bons) != 1:
                continue
            a = bons[0]
            if any(m in normaliser(txt).split() for m in normaliser(_role(a)).split() if len(m) >= 4):
                continue                                  # la réplique cite le nom de celui qui parle
            autres = [b for b in cast if b is not a and not meme_personne(qui, _role(b))]
            if len(autres) >= n - 1:
                possibles.append((a, txt, autres))
        if possibles:
            break
    else:
        raise RuntimeError("Qui l'a dit ? : aucune réplique attribuée trouvée sur Wikiquote pour les films des listes "
                           "(il faut Internet).")
    a, txt, autres = random.choice(possibles)
    choix = random.sample(autres[:8], n - 1) + [a]
    random.shuffle(choix)
    bonne = choix.index(a)
    d = details_film(api, film)
    titre_mots = {normaliser(m) for m in film["title"].split() if len(normaliser(m)) >= 4}
    aff = affichage(cfg, txt, rep["langue"])
    photos = api.images([c["photo"] for c in choix], "w185")
    images = [en_jpeg(ImageOps.fit(affiche(api, film, "w342"), (300, 450)), 450)] + \
             [en_jpeg(ImageOps.fit(p, (200, 300)), 300) for p in photos]
    etat = {"film": {"img": 0, "txt": film["title"], "sous": " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)},
            "question": "« " + masquer(aff["t"], titre_mots) + " »", "question_petit": masquer(aff["p"], titre_mots),
            "citation": True, "personnes": True,
            "items": [{"img": i + 1, "txt": _role(c), "sous": c["nom"]} for i, c in enumerate(choix)], "indices": []}
    evts = []
    if cfg.get("maddy_indice", True) and n > 2:
        faux = random.choice([i for i in range(n) if i != bonne])
        evts.append((duree * 0.55, lambda: etat.update(
            items=[dict(it, barre=True) if i == faux else it for i, it in enumerate(etat["items"])])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]], "indices": list(etat["indices"])})
    infos = [f"joué par {c['nom']}" for c in choix]
    return dict(jeu="maddy", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None, images=images,
                cles=[], bonne="", bonne_i=bonne, infos=infos, solution=f"C'est {_role(a)} ({a['nom']})",
                detail=film["title"],
                films=[cle_film(film)])
