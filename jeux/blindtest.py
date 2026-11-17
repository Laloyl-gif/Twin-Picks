"""Diane's Tape : blind test sur la bande originale du film (extrait Deezer de 30 s).

La BO est vérifiée avant d'être jouée (voir musique.bande_originale) : titre de l'album, compositeur crédité
sur TMDB présent parmi les artistes de l'album, genre « Films/Jeux vidéo », année, reprises écartées.
Si rien de sûr n'est trouvé, on passe à un autre film. Le morceau est tiré au hasard parmi les plus écoutés.

Indices discrets (la musique doit rester le cœur du jeu) : genre et année dès le début, puis l'affiche très floue
qui se précise un peu (elle ne devient jamais nette), le compositeur, un acteur, et à la fin les premières lettres.
"""
import requests
from PIL import ImageFilter

from musique import SANS_BO, bande_originale, compositeurs_tmdb, telecharger
from texte import normaliser
from tmdb import cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

FLOUS = [0.16, 0.12, 0.09, 0.065, 0.045]     # rayon du flou (en part de la largeur), du plus flou au moins flou


def _titres(film, d):
    """Titres à chercher : original, anglais, français (sans doublon)."""
    titres = []
    for t in (film.get("original_title"), d["en"], film["title"]):
        if t and normaliser(t) not in map(normaliser, titres) and t in d["noms"] + [film["title"]]:
            titres.append(t)
    return titres


def flouter(img, part):
    """Affiche très floue (jamais nette) : seules les grandes masses de couleur restent."""
    return img.filter(ImageFilter.GaussianBlur(max(2.0, img.width * part)))


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_blind"])
    for _ in range(10):
        try:
            film = tirer(pool, deja, lambda f: cle_film(f) not in SANS_BO)
        except RuntimeError:
            break                                         # tous les films ont été essayés sans succès
        d = details_film(api, film)
        compositeurs = compositeurs_tmdb(api, film)
        piste, album = bande_originale(_titres(film, d), d["annee"], compositeurs, int(cfg.get("blind_top", 5)))
        if not piste:
            SANS_BO.add(cle_film(film))
            continue
        try:
            audio = telecharger(piste["preview"])
        except (requests.RequestException, ValueError):
            continue
        artiste_album = (album.get("artist") or {}).get("name", "")
        compositeur = ", ".join(compositeurs[:2]) or (
            artiste_album if normaliser(artiste_album) not in ("various artists", "artistes divers") else "")
        try:
            acteur = next((a["nom"] for a in fiche(api, film)["acteurs"][:2]), "")
        except Exception:  # noqa: BLE001
            acteur = ""
        poster = affiche(api, film, "w342")
        etat, evts, images = {"indices": []}, [], []

        def indice(texte):
            return lambda: etat["indices"].append(texte)

        if cfg["blind_indices"]:
            depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
            if depart:
                etat["indices"].append(depart)
            if compositeur:
                evts.append((duree * 0.5, indice(f"Musique : {compositeur}")))
            if acteur:
                evts.append((duree * 0.66, indice(f"Avec {acteur}")))
        if cfg.get("blind_affiche", True):
            images = [en_jpeg(flouter(poster, f), 420) for f in FLOUS]
            for k in range(len(FLOUS)):
                evts.append((duree * (0.25 + 0.6 * k / (len(FLOUS) - 1)), lambda k=k: etat.update(img=k)))
        if cfg.get("blind_titre", True):
            evts.append((duree * 0.8, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
        etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
        m = manche_titre("blindtest", "cassette", duree, film, d, etapes, images, en_jpeg(affiche(api, film, "w500")),
                         cfg)
        artiste = (piste.get("artist") or {}).get("name", "")
        titre = piste.get("title_short") or piste.get("title") or ""
        m.update(audio=audio, detail=" · ".join(x for x in (m.get("detail", ""), f"« {titre} »", artiste,
                                                              album.get("title", "")) if x),
                 morceau=" ".join(x for x in (titre, artiste) if x))
        return m
    raise RuntimeError("Aucune bande originale fiable trouvée sur Deezer pour les films tirés.")
