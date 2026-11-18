"""Harold's Orchids (Les pétales) : Harold Smith ne sort jamais de chez lui ; il cultive ses orchidées et les regarde
de très près. Chaque pétale de l'orchidée montre un détail de l'affiche du film, vu à la loupe ; les pétales
s'ouvrent l'un après l'autre, puis s'élargissent : le détail recule et l'on comprend ce que l'on voit. Trouvez le film.
L'affiche sans texte est prise quand TMDB en a une (sinon on évite le haut et le bas, où s'écrit le titre).
Indices (réglables) : le genre, puis le titre à trous.
"""
import random

from PIL import Image, ImageFilter, ImageOps, ImageStat

from tmdb import affiches_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

NB = 5                                   # pétales
ZOOMS = (0.13, 0.21, 0.33, 0.5)          # taille du détail (part de la largeur de l'affiche), du plus serré au plus large
COTE = 260


def _affiche(api, film):
    """(image, sans_texte)."""
    try:
        for p in affiches_film(api, film)[:6]:
            if p["langue"] is None:
                return api.image(p["chemin"], "w780").convert("RGB"), True
    except Exception:  # noqa: BLE001
        pass
    return affiche(api, film, "w780").convert("RGB"), False


def centres(im, sans_texte, n=NB):
    """n centres de détails (là où l'image a le plus de contours), bien écartés les uns des autres."""
    W, H = im.size
    bords = im.convert("L").filter(ImageFilter.FIND_EDGES)
    gx, gy = 9, 14
    haut, bas = (0.12, 0.88) if sans_texte else (0.24, 0.74)
    cases = []
    for i in range(gx):
        for j in range(gy):
            cy = (j + 0.5) / gy
            if not haut <= cy <= bas:
                continue
            box = (int(i * W / gx), int(j * H / gy), int((i + 1) * W / gx), int((j + 1) * H / gy))
            zone = bords.crop(box)
            e = ImageStat.Stat(zone).mean[0]
            v = ImageStat.Stat(im.crop(box).convert("L")).stddev[0]
            cases.append((e + 0.4 * v + random.random() * 3, (i + 0.5) / gx, cy))
    cases.sort(reverse=True)
    choisis = []
    for _, x, y in cases:
        if all((x - a) ** 2 + ((y - b) * H / W) ** 2 > 0.22 ** 2 for a, b in choisis):
            choisis.append((x, y))
        if len(choisis) == n:
            break
    while len(choisis) < n:
        choisis.append((random.uniform(0.25, 0.75), random.uniform(haut + 0.05, bas - 0.05)))
    return choisis


def detail(im, x, y, z):
    W, H = im.size
    c = z * W
    x0 = min(max(0, x * W - c / 2), W - c)
    y0 = min(max(0, y * H - c / 2), H - c)
    return im.crop((int(x0), int(y0), int(x0 + c), int(y0 + c))).resize((COTE, COTE), Image.LANCZOS)


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_harold"])
    film = tirer([f for f in pool if f.get("poster_path")] or pool, deja)
    d = details_film(api, film)
    im, sans_texte = _affiche(api, film)
    pts = centres(im, sans_texte)
    images = [en_jpeg(detail(im, x, y, z), COTE) for z in ZOOMS for x, y in pts]
    etat = {"petales": [], "ouverts": 0, "zoom": 0, "indices": [], "trous": ""}

    def ouvrir(k):
        etat["ouverts"] = k + 1
        etat["petales"] = [etat["zoom"] * NB + i for i in range(k + 1)]

    def zoomer(z):
        etat["zoom"] = z
        etat["petales"] = [z * NB + i for i in range(etat["ouverts"])]
    evts = [(round(duree * 0.07 * k, 2), lambda k=k: ouvrir(k)) for k in range(NB)]
    evts += [(round(duree * t, 2), lambda z=z: zoomer(z)) for z, t in ((1, 0.38), (2, 0.58), (3, 0.76))]
    if cfg.get("harold_indices", True):
        rep = reponse_affichee(cfg, film, d)
        if d.get("genres"):
            evts.append((duree * 0.5, lambda: etat["indices"].append(", ".join(d["genres"][:2]))))
        evts.append((duree * 0.86, lambda: etat.update(trous=trous(rep, 0.2))))
    etapes = chronologie(evts, lambda: {**etat, "petales": list(etat["petales"]), "indices": list(etat["indices"])})
    rev = ImageOps.contain(im, (520, 780))
    return manche_titre("harold", "orchidee", duree, film, d, etapes, images, en_jpeg(rev), cfg)
