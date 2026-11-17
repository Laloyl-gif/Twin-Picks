"""Andy's Police Sketch (Le croquis) : comme Andy qui dessine le portrait-robot de BOB, l'affiche du film est
redessinée au crayon, trait après trait : d'abord les grands contours, puis les détails, puis les ombres au crayon.
L'affiche dessinée est une affiche SANS TEXTE (TMDB, langue « aucune ») : le titre n'apparaît jamais dans le dessin.
S'il n'y en a pas, un autre film est tiré (en dernier recours : l'affiche habituelle).
À la réponse : l'affiche d'origine. Indices (réglables) : genre et année, puis titre à trous.
Une part des manches (réglable, 30 % par défaut) dessine le portrait d'un acteur de acteurs.txt : trouvez l'acteur.
"""
import random

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from tmdb import affiches_film, cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, cles_reponses, manche_titre, reponse_affichee, tirer, trous

try:
    import cv2
except ImportError:
    cv2 = None

PAPIER = (238, 232, 216)
MINE = np.array([58, 54, 50], np.float32)


def _papier(h, w, graine):
    rng = np.random.default_rng(graine)
    grain = rng.normal(0, 5, (h, w, 1)).astype(np.float32)
    return np.clip(np.array(PAPIER, np.float32)[None, None, :] + grain, 0, 255)


def _contours(gris, force):
    """Contours de l'affiche : force 0 = seulement les grands traits, 1 = presque tout."""
    if cv2 is not None:
        flou = cv2.GaussianBlur(gris, (0, 0), 2.6 - 1.8 * force)
        haut = int(220 - 150 * force)
        bords = cv2.Canny(flou, haut // 2, haut)
        if force < 0.5:                                  # premiers traits : seuls les longs contours restent
            n, et, st, _ = cv2.connectedComponentsWithStats(bords, 8)
            mini = int(60 - 80 * force)
            garde = np.zeros(n, bool)
            garde[1:] = st[1:, cv2.CC_STAT_AREA] >= max(8, mini)
            bords = np.where(garde[et], 255, 0).astype(np.uint8)
        return cv2.dilate(bords, np.ones((2, 2), np.uint8)) if force < 0.7 else bords
    im = Image.fromarray(gris).filter(ImageFilter.GaussianBlur(2.6 - 1.8 * force)).filter(ImageFilter.FIND_EDGES)
    a = np.asarray(im)
    return np.where(a > (90 - 70 * force), 255, 0).astype(np.uint8)


def _crayon(gris):
    """Ombres au crayon (division du gris par son négatif flouté)."""
    g = gris.astype(np.float32)
    flou = np.asarray(Image.fromarray(255 - gris).filter(ImageFilter.GaussianBlur(10))).astype(np.float32)
    return np.clip(g * 255 / np.maximum(1, 255 - flou), 0, 255)


def croquis(img, etapes):
    """Les étapes du portrait-robot, des premiers traits au dessin ombré."""
    img = ImageOps.contain(img.convert("RGB"), (480, 720))
    gris = np.asarray(ImageOps.autocontrast(img.convert("L"), cutoff=1))
    h, w = gris.shape
    fond = _papier(h, w, int(gris.mean() * 1000) % 9999)
    ombres = _crayon(gris)
    vues = []
    for k in range(etapes):
        t = k / max(1, etapes - 1)
        traits = _contours(gris, min(1.0, 0.05 + t * 1.1)).astype(np.float32)[..., None] / 255
        a = fond * (1 - traits * 0.85) + MINE * traits * 0.85
        if t > 0.45:                                     # les ombres arrivent dans la seconde moitié
            o = 0.4 + 0.6 * (ombres[..., None] / 255)        # ombres légères : jamais d'aplat noir
            poids = min(1.0, (t - 0.45) / 0.45) * 0.75
            a = a * (1 - poids) + (a * o) * poids
        vues.append(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return vues


def affiche_sans_texte(api, film):
    """La meilleure affiche sans langue (donc sans titre écrit) au format affiche, sinon None."""
    try:
        for p in affiches_film(api, film):
            if p["langue"] is not None:
                break
            r = p["largeur"] / p["hauteur"] if p["hauteur"] else 0.67
            if 0.6 <= r <= 0.75:
                return api.image(p["chemin"], "w500")
    except Exception:  # noqa: BLE001
        pass
    return None


def portrait_acteur(api, cfg, deja, realisateur=False):
    """Manche « portrait-robot d'une personne » : un acteur de acteurs.txt (ou un réalisateur du fichier), à reconnaître."""
    from tmdb import charger_acteurs, filmographie
    from texte import est_latin
    from .contraintes import realisateurs_fichier
    from .filmo import films_connus
    if realisateur:
        acteurs = [{"id": p["id"], "name": p["name"], "profile_path": p.get("profile_path")}
                   for p in realisateurs_fichier(api, cfg) if p.get("profile_path")]
    else:
        acteurs = [a for a in charger_acteurs(api) if a.get("profile_path")]
    duree = float(cfg["dur_andy"])
    for _ in range(8):
        a = tirer(acteurs, deja, ident=lambda x: ("acteur", x["id"]))
        try:
            photo = api.image(a["profile_path"], "h632")
            connus = ([dict(f, release_date=f.get("release_date")) for f in filmographie(api, a["id"], "Director")[:3]]
                      if realisateur else films_connus(api.get(f"/person/{a['id']}/movie_credits").get("cast", []), 3))
        except Exception:  # noqa: BLE001
            continue
        break
    else:
        raise RuntimeError("Le croquis : aucun acteur exploitable.")
    vues = croquis(photo, max(4, int(cfg.get("andy_etapes", 10))))
    n = len(vues)
    etat = {"img": 0, "indices": [], "trous": "", "acteur": True}
    evts = [(round(duree * 0.85 * k / (n - 1), 2), lambda k=k: etat.update(img=k)) for k in range(1, n)]
    if cfg.get("andy_indices", True):
        if connus:
            f = connus[0]
            film = f"{f.get('title')} ({f['release_date'][:4]})" if f.get("release_date") else f.get("title", "")
            evts.append((duree * 0.55, lambda: etat["indices"].append(f"A réalisé {film}" if realisateur else f"A joué dans {film}")))
        evts.append((duree * 0.8, lambda: etat.update(trous=trous(a["name"], 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    noms = [a["name"]]
    try:
        noms += [x for x in api.get(f"/person/{a['id']}").get("also_known_as", []) if est_latin(x)]
    except Exception:  # noqa: BLE001
        pass
    mots = [m for m in a["name"].split() if m.lower().strip(".,") not in ("jr", "sr", "ii", "iii")]
    if len(mots) > 1:
        noms.append(mots[-1])
    return dict(jeu="andy", vue="croquis", duree=duree, etapes=etapes, images=[en_jpeg(v) for v in vues],
                revelation=en_jpeg(ImageOps.contain(photo.convert("RGB"), (480, 720))), reponse="titre",
                cles=cles_reponses(*noms), bonne=a["name"], solution=a["name"], pool="acteurs",
                detail=", ".join(c.get("title", "") for c in connus[:2]))


def construire(api, cfg, pool, deja):
    tirage = random.random() * 100
    if tirage < float(cfg.get("andy_realisateurs", 10)):
        try:
            return portrait_acteur(api, cfg, deja, realisateur=True)
        except Exception:  # noqa: BLE001
            pass
    elif tirage < float(cfg.get("andy_realisateurs", 10)) + float(cfg.get("andy_acteurs", 30)):
        try:
            return portrait_acteur(api, cfg, deja)
        except Exception:  # noqa: BLE001
            pass                                   # pas d'acteur : un film
    image, essayes = None, []
    for _ in range(8):
        film = tirer(pool, deja, lambda f: f.get("poster_path"))
        essayes.append(cle_film(film))
        image = affiche_sans_texte(api, film)
        if image is not None:
            break
    for c in essayes[:-1]:                    # les films sans affiche sans texte restent jouables ailleurs
        deja.discard(c)
    d = details_film(api, film)
    duree = float(cfg["dur_andy"])
    vues = croquis(image if image is not None else affiche(api, film, "w500"), max(4, int(cfg.get("andy_etapes", 10))))
    n = len(vues)
    etat = {"img": 0, "indices": [], "trous": ""}
    evts = [(round(duree * 0.85 * k / (n - 1), 2), lambda k=k: etat.update(img=k)) for k in range(1, n)]
    if cfg.get("andy_indices", True):
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart:
            evts.append((duree * 0.55, lambda: etat["indices"].append(depart)))
        evts.append((duree * 0.8, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    return manche_titre("andy", "croquis", duree, film, d, etapes, [en_jpeg(v) for v in vues],
                        en_jpeg(affiche(api, film, "w500")), cfg)
