"""Affiche vidée (Pete) : « There was a fish in the percolator! »

L'affiche d'un film des listes, sans son titre, ses textes, ses logos, ses personnages ni son sujet principal
(zones reconstruites) : il ne reste que le décor, il faut retrouver le film. Les affiches sont préparées à
l'avance, en arrière-plan, et gardées dans affiches_pete/ (voir le paquet affiches/) ; une manche ne fait que
lire une affiche prête. S'il n'y en a aucune, la préparation démarre et la manche attend la première.
Indices (réglables) : genre et année, réalisateur, puis le titre à trous. À la réponse : l'affiche originale.
"""
from PIL import Image, ImageOps

from affiches.catalogue import cle as cle_catalogue
from affiches.preparation import PREPARATEUR
from tmdb import cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous


def options(cfg):
    return {"textes": cfg.get("pete_textes", True), "personnages": cfg.get("pete_personnages", True),
            "objets": cfg.get("pete_objets", True)}


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_pete"])
    prets = PREPARATEUR.pretes(pool)
    if not [f for f in prets if cle_film(f) not in deja]:
        if not PREPARATEUR.actif():
            PREPARATEUR.lancer(api, pool, options(cfg), cfg.get("pete_ordre", "connus"))
        exclus = {cle_catalogue(f) for f in prets}
        prets = PREPARATEUR.attendre(pool, 1.0, exclus) or prets
    if not prets:
        etat = PREPARATEUR.etat()
        raise RuntimeError("Affiche vidée : aucune affiche prête. " + (etat.get("erreur") or etat.get("message") or ""))
    film = tirer(prets, deja)
    cat = PREPARATEUR.catalogue()
    e = cat.entree(film)
    videe = Image.open(cat.chemin(e["videe"])).convert("RGB")
    try:
        originale = Image.open(cat.chemin(e["originale"])).convert("RGB")
    except OSError:
        originale = affiche(api, film, "w500")
    d = details_film(api, film)
    etat = {"img": 0, "indices": [], "trous": ""}
    evts = []
    if cfg.get("pete_indices", True):
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            evts.append((duree * 0.35, lambda: etat["indices"].append(depart)))
        try:
            reals = " et ".join(r["nom"] for r in fiche(api, film)["realisateurs"][:2])
        except Exception:  # noqa: BLE001
            reals = ""
        if reals:
            evts.append((duree * 0.55, lambda: etat["indices"].append(f"Réalisé par {reals}")))
        evts.append((duree * 0.8, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    image = en_jpeg(ImageOps.contain(videe, (600, 900)), 900, 90)
    return manche_titre("pete", "videe", duree, film, d, etapes, [image],
                        en_jpeg(ImageOps.contain(originale, (600, 900)), 900), cfg)
