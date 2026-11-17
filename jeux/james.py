"""James' Just You (La bande originale) : James enregistre sa chanson sur une cassette. Ici, c'est la jaquette de
la cassette : la liste des morceaux de la bande originale du film (album vérifié sur Deezer, comme Diane's Tape),
écrite à la main, une piste après l'autre. Les mots du titre du film (et de la saga) sont cachés.
Le compositeur est écrit sur la jaquette dès le début. Indices (réglables) : genre et année à 30 %, puis la pochette
de l'album, d'abord très floue (50 %), puis un peu moins (70 %) ; titre à trous à 85 %. À la réponse : l'affiche.
"""
import io
import re

from PIL import Image, ImageFilter, ImageOps

from musique import SANS_BO, bande_originale, compositeurs_tmdb, deezer, telecharger
from texte import normaliser
from tmdb import cle_film, details_film
from visuels import en_jpeg
from .blindtest import _titres
from .commun import affiche, chronologie, manche_titre, reponse_affichee, saga_de, tirer, trous

MOT = re.compile(r"[\w'’]+", re.U)
BRUIT = re.compile(r"\s*[\(\[][^)\]]*(soundtrack|motion picture|from the|version|remaster|bande originale|"
                   r"score|ost|edit|mix)[^)\]]*[\)\]]\s*", re.I)


def cacher(titre, interdits):
    """Remplace par ▒▒▒ les mots du titre de la piste qui appartiennent au titre du film."""
    return MOT.sub(lambda m: "▒" * len(m.group()) if normaliser(m.group()) in interdits else m.group(), titre)


def pistes_album(album, interdits, nmax):
    pistes = list((album.get("tracks") or {}).get("data", []))
    if album.get("nb_tracks", 0) > len(pistes):
        try:
            pistes = deezer(f"/album/{album['id']}/tracks", limit=300).get("data", []) or pistes
        except Exception:  # noqa: BLE001
            pass
    out, vus = [], set()
    for t in pistes:
        titre = BRUIT.sub(" ", t.get("title") or "").strip(" -–")
        if not titre or normaliser(titre) in vus:
            continue
        vus.add(normaliser(titre))
        out.append(cacher(titre, interdits)[:60])
        if len(out) >= nmax:
            break
    return out


def construire(api, cfg, pool, deja):
    duree, nmax = float(cfg["dur_james"]), int(cfg.get("james_pistes", 10))
    for _ in range(10):
        try:
            film = tirer(pool, deja, lambda f: cle_film(f) not in SANS_BO)
        except RuntimeError:
            break
        d = details_film(api, film)
        compositeurs = compositeurs_tmdb(api, film)
        try:
            piste, album = bande_originale(_titres(film, d), d["annee"], compositeurs, 5)
        except Exception:  # noqa: BLE001
            piste, album = None, None
        if not album:
            SANS_BO.add(cle_film(film))
            continue
        interdits = {normaliser(m) for t in d["noms"] + [film["title"], saga_de(cfg, d)] for m in MOT.findall(t or "")
                     if len(normaliser(m)) >= 3}
        pistes = pistes_album(album, interdits, nmax)
        if len(pistes) < 4:
            continue
        break
    else:
        raise RuntimeError("La bande originale : aucune BO trouvée sur Deezer pour les films des listes.")
    n = len(pistes)
    artiste = (album.get("artist") or {}).get("name", "")
    compo = ", ".join(compositeurs[:2]) or (artiste if normaliser(artiste) not in ("various artists", "artistes divers") else "")
    images = []
    try:                                             # la pochette, floutée (elle porte souvent le titre)
        brut = telecharger(album.get("cover_xl") or album.get("cover_big") or "") if (album.get("cover_xl") or album.get("cover_big")) else b""
        pochette = ImageOps.fit(Image.open(io.BytesIO(brut)).convert("RGB"), (400, 400)) if brut else None
    except Exception:  # noqa: BLE001
        pochette = None
    if pochette is not None:
        images = [en_jpeg(pochette.filter(ImageFilter.GaussianBlur(r)), 400) for r in (26, 13)]
    etat = {"pistes": [], "total": n, "indices": [], "trous": "", "compo": compo}
    evts = [(round(duree * 0.75 * k / max(1, n - 1), 2), lambda k=k: etat.update(pistes=pistes[:k + 1])) for k in range(n)]
    if cfg.get("james_indices", True):
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            evts.append((duree * 0.3, lambda: etat["indices"].append(depart)))
        if images:
            evts.append((duree * 0.5, lambda: etat.update(pochette=0)))
            evts.append((duree * 0.7, lambda: etat.update(pochette=1)))
        evts.append((duree * 0.85, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "pistes": list(etat["pistes"]), "indices": list(etat["indices"])})
    return manche_titre("james", "tracklist", duree, film, d, etapes, images, en_jpeg(affiche(api, film, "w500")), cfg)
