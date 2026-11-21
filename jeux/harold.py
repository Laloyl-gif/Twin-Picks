"""Harold's Orchids (Les pétales) : Harold Smith ne sort jamais de chez lui ; il cultive ses orchidées et les regarde
de très près. Chaque pétale de l'orchidée montre, vu à la loupe, un détail d'une image différente du film : l'affiche,
des plans du film, le visage d'un acteur… Les pétales s'ouvrent l'un après l'autre, puis s'élargissent : le détail
recule et l'on comprend ce que l'on voit. Trouvez le film. L'affiche sans texte est prise quand TMDB en a une (sinon
on évite le haut et le bas, où s'écrit le titre). Indices (réglables) : le genre, puis le titre à trous.
"""
import random

from PIL import Image, ImageFilter, ImageOps, ImageStat

from tmdb import affiches_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

NB = 5                                   # pétales
ZOOMS = (0.03, 0.05, 0.08, 0.125, 0.19, 0.28, 0.4, 0.58)   # taille du détail (part de la largeur), très serré puis de plus en plus large
COTE = 260


def _affiche(api, film):
    """(image, sans_texte)."""
    try:
        for p in affiches_film(api, film)[:6]:
            if p["langue"] is None:
                return api.image(p["chemin"], "original").convert("RGB"), True
    except Exception:  # noqa: BLE001
        pass
    return affiche(api, film, "original").convert("RGB"), False


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


def _empreinte(im):
    return list(ImageOps.fit(im, (16, 16)).convert("L").getdata())


def _pareilles(a, b):
    """Deux images quasi identiques (le même plan, recadré ou dans une autre langue) ?"""
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) < 14


def sources(api, film, d):
    """Les images des pétales : [(étiquette, image, (x, y) du détail ou None, sans_texte)], cinq au plus, variées :
    jamais deux fois le même plan ni le même acteur."""
    out, vues = [], []

    def nouvelle(img):
        e = _empreinte(img)
        if any(_pareilles(e, v) for v in vues):
            return False
        vues.append(e)
        return True
    im, sans_texte = _affiche(api, film)
    nouvelle(im)
    out.append(("Affiche", im, None, sans_texte))
    plans = []
    for chemin in list(dict.fromkeys(d.get("fonds_neutres") or []))[:10]:
        try:
            img = api.image(chemin, "w1280").convert("RGB")
        except Exception:  # noqa: BLE001
            continue
        if nouvelle(img):
            plans.append(img)
        if len(plans) == 3:
            break
    acteurs, gens = [], set()
    try:
        for a in fiche(api, film).get("acteurs", [])[:8]:
            qui = a.get("id") or a.get("nom") or a.get("photo")
            if not a.get("photo") or qui in gens or a["photo"] in gens:
                continue
            gens.update((qui, a["photo"]))
            try:
                acteurs.append(api.image(a["photo"], "h632").convert("RGB"))
            except Exception:  # noqa: BLE001
                continue
            if len(acteurs) == 3:
                break
    except Exception:  # noqa: BLE001
        pass
    # alterner plans et acteurs
    for k in range(3):
        if k < len(plans):
            out.append(("Plan", plans[k], None, True))
        if k < len(acteurs):
            out.append(("Acteur", acteurs[k], (0.5, 0.3), True))       # le visage : vers le haut du portrait
    if len(out) < NB:                                                  # pas assez : d'autres affiches du film
        try:
            for p in affiches_film(api, film)[1:8]:
                img = api.image(p["chemin"], "w780").convert("RGB")
                if nouvelle(img):
                    out.append(("Affiche", img, None, p["langue"] is None))
                if len(out) >= NB:
                    break
        except Exception:  # noqa: BLE001
            pass
    while len(out) < NB:                                             # vraiment rien d'autre : un autre coin de l'affiche
        out.append(("Affiche", im, None, sans_texte))
    return out[:NB]


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_harold"])
    film = tirer([f for f in pool if f.get("poster_path")] or pool, deja)
    d = details_film(api, film)
    srcs = sources(api, film, d)
    pts, deja_pris = [], {}
    for _, img, centre, sans_texte in srcs:
        if centre:
            pts.append(centre)
            continue
        # une même image (l'affiche) peut servir deux fois : deux détails différents
        lst = deja_pris.setdefault(id(img), centres(img, sans_texte, NB))
        pts.append(lst.pop(0))
    images = [en_jpeg(detail(img, x, y, z if not c else min(0.95, z * 1.7 + 0.03)), COTE)
              for z in ZOOMS for (_, img, c, _), (x, y) in zip(srcs, pts)]
    im = srcs[0][1]
    etat = {"petales": [], "ouverts": 0, "zoom": 0, "sources": [x[0] for x in srcs], "indices": [], "trous": ""}

    def ouvrir(k):
        etat["ouverts"] = k + 1
        etat["petales"] = [etat["zoom"] * NB + i for i in range(k + 1)]

    def zoomer(z):
        etat["zoom"] = z
        etat["petales"] = [z * NB + i for i in range(etat["ouverts"])]
    evts = [(round(duree * 0.05 * k, 2), lambda k=k: ouvrir(k)) for k in range(NB)]
    nz = len(ZOOMS)
    evts += [(round(duree * (0.24 + 0.56 * (z - 1) / (nz - 2)), 2), lambda z=z: zoomer(z)) for z in range(1, nz)]
    if cfg.get("harold_indices", True):
        rep = reponse_affichee(cfg, film, d)
        if d.get("genres"):
            evts.append((duree * 0.5, lambda: etat["indices"].append(", ".join(d["genres"][:2]))))
        evts.append((duree * 0.86, lambda: etat.update(trous=trous(rep, 0.2))))
    etapes = chronologie(evts, lambda: {**etat, "petales": list(etat["petales"]), "indices": list(etat["indices"])})
    rev = ImageOps.contain(im, (520, 780))
    return manche_titre("harold", "orchidee", duree, film, d, etapes, images, en_jpeg(rev), cfg)
