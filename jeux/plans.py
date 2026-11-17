"""Truman's Files : trois vraies images du film apparaissent l'une après l'autre, de la plus difficile
à la plus facile. Le film est tiré au hasard parmi tous les films des listes choisies. Sources, dans l'ordre :
les plans choisis et triés à la main (en ligne sur le dépôt du jeu, ou dans le dossier plans/ : plans_distants.py),
vos fichiers vidéo (voir images_film.py), sinon les images de TMDB."""
import traceback

from PIL import ImageOps

import images_film as imf
import plans_distants
from tmdb import details_film
from visuels import en_jpeg
from .commun import affiche, manche_titre, tirer

NB = 3


def _noms(film, d=None):
    return [film["title"], film.get("original_title")] + (d["noms"] if d else [])


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_plans"])
    pas = min(float(cfg["plans_intervalle"]), duree * 0.4)
    source = cfg.get("plans_source", "auto")
    vt, alerte = None, ""
    pt = plans_distants.catalogue() if source != "tmdb" else None
    if source != "tmdb":
        try:
            vt = imf.videotheque(cfg.get("plans_dossier", ""))
        except RuntimeError as err:
            if source == "local" and not pt:
                raise
            alerte = str(err)                                    # mode auto : on continue avec TMDB

    def a_dossier(f):
        return bool(pt) and pt.chercher(f, _noms(f)) is not None

    def a_video(f):
        return bool(vt) and not f["tv"] and vt.chercher(_noms(f), f["release_date"][:4]) is not None

    if source == "local" and not any(a_dossier(f) or a_video(f) for f in pool):
        lieux = f"les plans ({len(pt) if pt else 0} films)" + (f" ni dans {vt.dossier}" if vt else "")
        raise RuntimeError(f"Truman's Files : aucun film des listes dans {lieux}.")
    for _ in range(12):
        film = tirer(pool, deja, (lambda f: a_dossier(f) or a_video(f)) if source == "local" else (lambda f: True))
        d = details_film(api, film)
        poster = affiche(api, film, "w185")
        plans, detail = None, ""
        dossier = pt.chercher(film, _noms(film, d), d["annee"]) if pt else None
        if dossier:
            try:
                ims = dossier.images()                       # une image par niveau : difficile, moyen, facile
                plans = [(im, "") for im in ims] if ims else None
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        chemin = vt.chercher(_noms(film, d), d["annee"]) if vt and not film["tv"] and not plans else None
        if chemin:
            try:
                plans = imf.plans_video(chemin, poster, NB)
                if plans:
                    detail = "Plans à " + " · ".join(info for _, info in plans)
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        if not plans and source != "local":
            if film["tv"]:
                plans = imf.plans_serie(api, film, poster, NB)
                if plans:
                    detail = "Épisodes " + " · ".join(info for _, info in plans)
            if not plans:
                plans = imf.plans_tmdb(api, d, poster, NB)
        if not plans:
            continue
        # format 16:9 : les plans en cinémascope gardent tout le cadre (bandes noires)
        images = [en_jpeg(ImageOps.pad(im, (768, 432), color="black") if im.width / im.height > 2.0
                          else ImageOps.fit(im, (768, 432)), 800) for im, _ in plans]
        etapes = [(pas * k, {"plans": list(range(k + 1)), "total": NB}) for k in range(NB)]
        m = manche_titre("plans", "plans", duree, film, d, etapes, images, en_jpeg(affiche(api, film, "w500")), cfg)
        m["detail"] = " · ".join(x for x in (m.get("detail", ""), detail or ("" if dossier else alerte)) if x)
        return m
    raise RuntimeError("Aucun film avec assez d'images exploitables dans les listes choisies.")
