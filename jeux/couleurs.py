"""Couleurs (L'Homme d'ailleurs) : l'affiche réduite à ses couleurs.

Au départ, chaque colonne de l'affiche prend la couleur moyenne de toute la colonne (un « code-barres »).
Puis l'affiche se coupe en bandes horizontales de plus en plus nombreuses (2, 3, 5…), chaque morceau de colonne
gardant sa couleur moyenne : les formes apparaissent peu à peu. Indices (réglables) : genre et année,
réalisateur, puis le titre à trous.
"""
import numpy as np
from PIL import Image, ImageOps

from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

LARGEUR, HAUTEUR = 320, 480


def bandes(img, n):
    """Chaque colonne coupée en n bandes horizontales, chacune de sa couleur moyenne."""
    a = np.asarray(img, dtype=np.float32)
    h = a.shape[0]
    bords = np.linspace(0, h, n + 1).round().astype(int)
    out = np.empty_like(a)
    for y0, y1 in zip(bords[:-1], bords[1:]):
        if y1 > y0:
            out[y0:y1] = a[y0:y1].mean(axis=0, keepdims=True)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def paliers(final):
    """1, 2, 3, 5, 8… jusqu'à `final` bandes (6 étapes au plus)."""
    out, x = [1], 1.0
    while out[-1] < final:
        x = max(x * 1.65, out[-1] + 1)
        out.append(min(final, round(x)))
    if len(out) > 6:
        idx = np.linspace(0, len(out) - 1, 6).round().astype(int)
        out = [out[i] for i in idx]
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_couleurs"])
    film = tirer(pool, deja, lambda f: f.get("poster_path") or not f.get("title"))
    d = details_film(api, film)
    poster = ImageOps.fit(affiche(api, film, "w342").convert("RGB"), (LARGEUR, HAUTEUR))
    niveaux = paliers(int(cfg.get("couleurs_bandes", 12)))
    images = [en_jpeg(bandes(poster, n).resize((LARGEUR * 2, HAUTEUR * 2), Image.Resampling.NEAREST), 960, 92)
              for n in niveaux]
    etat = {"img": 0, "indices": [], "trous": ""}
    fin = duree * 0.8
    evts = [(fin * k / max(1, len(niveaux) - 1), lambda k=k: etat.update(img=k)) for k in range(len(niveaux))]
    if cfg.get("couleurs_indices", True):
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            evts.append((duree * 0.3, lambda: etat["indices"].append(depart)))
        try:
            reals = " et ".join(r["nom"] for r in fiche(api, film)["realisateurs"][:2])
        except Exception:  # noqa: BLE001
            reals = ""
        if reals:
            evts.append((duree * 0.55, lambda: etat["indices"].append(f"Réalisé par {reals}")))
        evts.append((duree * 0.78, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    return manche_titre("couleurs", "couleurs", duree, film, d, etapes, images, en_jpeg(poster, 600), cfg)
