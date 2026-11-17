"""
Bibliothèque d'effets visuels pour le quiz des affiches.

Ce module ne contient aucune interface : il est utilisé par jeu_affiches.py.
Dépendance obligatoire : pillow. Dépendance facultative : numpy
(accélère la torsion circulaire et active le vitrail et le tri de pixels).

Nouveautés par rapport à la version précédente :
- 15 nouvelles déformations (lentille, ondes, petite planète, vitrail,
  caléidoscope, tri de pixels, coulures, halftone...) ;
- 8 nouveaux effets de couleur ;
- 11 nouveaux effets complémentaires ;
- règle « un seul destructeur de détails » pour que l'affiche reste devinable ;
- graine facultative (parties reproductibles) et noms des effets appliqués ;
- generer_indices() : versions de plus en plus lisibles pour un système d'indices.
"""
import math
import random
from pathlib import Path

from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageOps,
)

try:
    import numpy as np
except ImportError:  # numpy est facultatif
    np = None


# ============================================================
# CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
DOSSIER_IMAGES = SCRIPT_DIR

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# Limite de traitement : évite de faire travailler Pillow
# sur des affiches gigantesques.
TAILLE_MAX_TRAITEMENT = 1200


# ============================================================
# OUTILS
# ============================================================

def limiter(valeur, minimum, maximum):
    return max(minimum, min(maximum, valeur))


def convertir_rgb(image):
    """Convertit proprement toute image en RGB."""
    if image.mode != "RGB":
        return image.convert("RGB")
    return image.copy()


def redimensionner_pour_traitement(image):
    """Réduit une très grande affiche avant les effets."""
    image = convertir_rgb(image)
    largeur, hauteur = image.size
    facteur = min(1.0, TAILLE_MAX_TRAITEMENT / max(largeur, hauteur))
    if facteur >= 1.0:
        return image
    taille = (max(1, int(largeur * facteur)), max(1, int(hauteur * facteur)))
    return image.resize(taille, Image.Resampling.LANCZOS)


def decalage_sans_bord(image, dx, dy):
    """
    Décale une image (tout mode) sans zone vide : la partie qui
    n'est plus recouverte conserve l'image d'origine.
    """
    largeur, hauteur = image.size
    dx, dy = int(dx), int(dy)
    resultat = image.copy()
    source = image.crop((
        max(0, -dx),
        max(0, -dy),
        min(largeur, largeur - dx),
        min(hauteur, hauteur - dy),
    ))
    if source.width > 0 and source.height > 0:
        resultat.paste(source, (max(0, dx), max(0, dy)))
    return resultat


def deformer_maillage(image, fonction, pas=None):
    """
    Déformation libre sans numpy : pour chaque point (x, y) de l'image
    d'arrivée, fonction(x, y, centre_cellule) donne le point de l'image
    source à copier. S'appuie sur la transformation MESH de Pillow.
    """
    largeur, hauteur = image.size
    pas = pas or max(8, min(largeur, hauteur) // 40)
    xs = list(range(0, largeur, pas)) + [largeur]
    ys = list(range(0, hauteur, pas)) + [hauteur]

    def source(x, y, centre):
        sx, sy = fonction(x, y, centre)
        return (limiter(sx, 0, largeur - 1), limiter(sy, 0, hauteur - 1))

    maillage = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
            centre = ((x0 + x1) / 2, (y0 + y1) / 2)
            quad = (
                source(x0, y0, centre) + source(x0, y1, centre)
                + source(x1, y1, centre) + source(x1, y0, centre)
            )
            maillage.append(((x0, y0, x1, y1), quad))
    return image.transform(
        image.size, Image.Transform.MESH, maillage, Image.Resampling.BILINEAR
    )


# ============================================================
# DEFORMATIONS : PIXELISATION, FLOUS
# ============================================================

def effet_pixelisation(image, puissance):
    largeur, hauteur = image.size
    facteur = int(limiter(4 + puissance * 1.8, 4, 22))
    petite = image.resize(
        (max(8, largeur // facteur), max(8, hauteur // facteur)),
        Image.Resampling.BILINEAR,
    )
    return petite.resize((largeur, hauteur), Image.Resampling.NEAREST)


def effet_flou_gaussien(image, puissance):
    return image.filter(ImageFilter.GaussianBlur(1.5 + puissance * 0.9))


def effet_flou_mouvement(image, puissance):
    """Flou de mouvement horizontal : moyenne de plusieurs décalages."""
    force = int(3 + puissance * 2)
    images = [image]
    for i in range(1, 5):
        d = int(force * i / 4)
        images.append(decalage_sans_bord(image, d, 0))
        images.append(decalage_sans_bord(image, -d, 0))
    resultat = images[0]
    for rang, img in enumerate(images[1:], start=2):
        resultat = Image.blend(resultat, img, 1.0 / rang)  # vraie moyenne
    return resultat


def effet_flou_radial(image, puissance):
    """Flou obtenu par un léger redimensionnement mélangé à l'original."""
    largeur, hauteur = image.size
    echelle = 1.0 + puissance * 0.012
    petite = image.resize(
        (max(10, int(largeur / echelle)), max(10, int(hauteur / echelle))),
        Image.Resampling.BICUBIC,
    ).resize((largeur, hauteur), Image.Resampling.BICUBIC)
    return Image.blend(image, petite, min(0.85, 0.35 + puissance * 0.05))


def effet_flou_fort(image, puissance):
    return image.filter(ImageFilter.GaussianBlur(4 + puissance * 1.6))


def effet_flou(image, puissance):
    type_flou = random.choice(["gaussien", "mouvement", "radial", "fort"])
    if type_flou == "gaussien":
        return effet_flou_gaussien(image, puissance)
    if type_flou == "mouvement":
        return effet_flou_mouvement(image, puissance)
    if type_flou == "radial":
        return effet_flou_radial(image, puissance)
    return effet_flou_fort(image, puissance)


# ============================================================
# DEFORMATIONS : MOSAIQUE, CABOSSAGE, CRISTALLISATION...
# ============================================================

def effet_mosaique(image, puissance):
    """
    Vraie mosaïque : l'affiche est recomposée en carreaux (rangées décalées
    comme des briques). Chaque carreau est un aplat de la couleur MOYENNE de
    la zone correspondante de l'affiche : aucune couleur n'est inventée et
    l'affiche reste identifiable (formes, répartition des couleurs).

    Cet effet ne s'applique qu'en PREMIER (voir PREMIERE_SEULEMENT) : l'image
    reçue est alors l'affiche d'origine, donc les couleurs sont celles de la
    vraie affiche. Plus la puissance est forte, plus les carreaux sont gros.
    """
    largeur, hauteur = image.size
    colonnes = int(limiter(42 - puissance * 2.8, 14, 40))
    cote = largeur / colonnes
    lignes = max(2, int(round(hauteur / cote)))
    haut_carreau = hauteur / lignes
    resultat = Image.new("RGB", (largeur, hauteur))
    dessin = ImageDraw.Draw(resultat)
    for j in range(lignes):
        y1 = int(round(j * haut_carreau))
        y2 = int(round((j + 1) * haut_carreau))
        if y2 <= y1:
            continue
        debut = -cote / 2 if j % 2 else 0.0
        while debut < largeur:
            x1 = int(round(max(0.0, debut)))
            x2 = int(round(min(float(largeur), debut + cote)))
            debut += cote
            if x2 <= x1:
                continue
            # moyenne exacte de la zone (filtre BOX sur toute la zone)
            moyenne = image.crop((x1, y1, x2, y2)).resize(
                (1, 1), Image.Resampling.BOX
            ).getpixel((0, 0))
            dessin.rectangle((x1, y1, x2 - 1, y2 - 1), fill=moyenne)
    return resultat


def effet_cabossage(image, puissance):
    """Déformation par bandes horizontales décalées et inclinées."""
    resultat = image.copy()
    largeur, hauteur = image.size
    nombre_bandes = int(limiter(8 + puissance * 2, 8, 30))
    hauteur_bande = max(2, hauteur // nombre_bandes)
    amplitude = 2 + puissance * 2.2
    for index in range(nombre_bandes):
        y = index * hauteur_bande
        angle = math.sin(index * 1.7) * amplitude
        bande = image.crop((0, y, largeur, min(hauteur, y + hauteur_bande)))
        dx = int(math.sin(index * 2.3) * amplitude * 2)
        bande = decalage_sans_bord(bande, dx, 0)
        bande = bande.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False)
        resultat.paste(bande, (0, y))
    relief = resultat.filter(ImageFilter.EDGE_ENHANCE)
    return Image.blend(resultat, relief, min(0.35, 0.10 + puissance * 0.025))


def effet_cristallisation(image, puissance):
    largeur, hauteur = image.size
    facteur = int(limiter(10 + puissance * 2, 10, 30))
    petite = image.resize(
        (max(12, largeur // facteur), max(12, hauteur // facteur)),
        Image.Resampling.BILINEAR,
    )
    cristaux = petite.resize((largeur, hauteur), Image.Resampling.NEAREST)
    cristaux = cristaux.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return Image.blend(image, cristaux, min(0.95, 0.45 + puissance * 0.055))


def effet_torsion_circulaire(image, puissance):
    """Tourbillon autour d'un point aléatoire (vectorisé si numpy est présent)."""
    largeur, hauteur = image.size
    facteur = min(1.0, 700 / max(largeur, hauteur))
    if facteur < 1.0:
        petite = image.resize(
            (max(2, int(largeur * facteur)), max(2, int(hauteur * facteur))),
            Image.Resampling.BILINEAR,
        )
    else:
        petite = image.copy()

    w, h = petite.size
    centre_x = random.uniform(w * 0.30, w * 0.70)
    centre_y = random.uniform(h * 0.30, h * 0.70)
    rayon_max = min(w, h) * random.uniform(0.28, 0.48)
    sens = random.choice((-1, 1))
    angle_max = sens * math.radians(
        random.uniform(35 + puissance * 2, 80 + puissance * 7)
    )
    rayon_carre = rayon_max * rayon_max

    if np is not None:
        src = np.asarray(petite)
        ys, xs = np.mgrid[0:h, 0:w]
        dx = xs - centre_x
        dy = ys - centre_y
        d2 = dx * dx + dy * dy
        masque = d2 < rayon_carre
        force = np.where(masque, (1.0 - np.sqrt(d2) / rayon_max) ** 2, 0.0)
        angle = angle_max * force
        c, s = np.cos(angle), np.sin(angle)
        sx = np.rint(centre_x + dx * c - dy * s).astype(np.int32)
        sy = np.rint(centre_y + dx * s + dy * c).astype(np.int32)
        ok = masque & (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
        sortie = src.copy()
        sortie[ok] = src[sy[ok], sx[ok]]
        resultat = Image.fromarray(sortie)
    else:
        pixels_source = petite.load()
        resultat = petite.copy()
        pixels_resultat = resultat.load()
        for y in range(h):
            dy = y - centre_y
            for x in range(w):
                dx = x - centre_x
                d2 = dx * dx + dy * dy
                if d2 >= rayon_carre:
                    continue
                force = 1.0 - (math.sqrt(d2) / rayon_max)
                angle = angle_max * force * force
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                sx = int(round(centre_x + dx * cos_a - dy * sin_a))
                sy = int(round(centre_y + dx * sin_a + dy * cos_a))
                if 0 <= sx < w and 0 <= sy < h:
                    pixels_resultat[x, y] = pixels_source[sx, sy]

    if facteur < 1.0:
        resultat = resultat.resize((largeur, hauteur), Image.Resampling.BICUBIC)
    return resultat


def effet_fragmentation(image, puissance):
    """
    Découpe l'affiche en fragments mélangés et légèrement décalés.
    Déformation exclusive : aucune autre déformation n'est ajoutée.
    """
    largeur, hauteur = image.size
    colonnes = int(limiter(4 + puissance // 2, 4, 9))
    lignes = int(limiter(5 + puissance // 2, 5, 11))
    fragments = []
    for ligne in range(lignes):
        for colonne in range(colonnes):
            x1, y1 = colonne * largeur // colonnes, ligne * hauteur // lignes
            x2, y2 = (colonne + 1) * largeur // colonnes, (ligne + 1) * hauteur // lignes
            fragments.append((image.crop((x1, y1, x2, y2)), x1, y1))
    random.shuffle(fragments)
    resultat = Image.new("RGB", image.size)
    amplitude = int(3 + puissance * 2)
    for fragment, x, y in fragments:
        dx = random.randint(-amplitude, amplitude)
        dy = random.randint(-amplitude, amplitude)
        resultat.paste(fragment, (
            max(0, min(largeur - fragment.width, x + dx)),
            max(0, min(hauteur - fragment.height, y + dy)),
        ))
    return resultat


def effet_torsion(image, puissance):
    """Torsion horizontale par bandes."""
    largeur, hauteur = image.size
    resultat = Image.new("RGB", image.size)
    bandes = int(limiter(35 + puissance * 5, 35, 90))
    hauteur_bande = max(1, hauteur // bandes)
    amplitude = 4 + puissance * 2.5
    for i in range(bandes):
        y1 = i * hauteur_bande
        y2 = hauteur if i == bandes - 1 else min(hauteur, (i + 1) * hauteur_bande)
        bande = image.crop((0, y1, largeur, y2))
        bande = decalage_sans_bord(bande, int(math.sin(i * 0.42) * amplitude), 0)
        resultat.paste(bande, (0, y1))
    return resultat


def effet_verre_depoli(image, puissance):
    """Flou + déplacements locaux + grain."""
    flou = image.filter(ImageFilter.GaussianBlur(1.5 + puissance * 0.55))
    largeur, hauteur = image.size
    resultat = flou.copy()
    for _ in range(int(6 + puissance * 2)):
        dx = random.randint(-puissance * 2, puissance * 2)
        dy = random.randint(-puissance, puissance)
        resultat = Image.blend(resultat, decalage_sans_bord(flou, dx, dy), 0.12)
    bruit = Image.effect_noise((largeur, hauteur), 25 + puissance * 4).convert("L")
    bruit_rgb = Image.merge("RGB", (bruit, bruit, bruit))
    return Image.blend(resultat, bruit_rgb, min(0.18, 0.04 + puissance * 0.012))


# ============================================================
# DEFORMATIONS : SECONDE GENERATION
# ============================================================

def effet_ondulation(image, puissance):
    """Vagues verticales : chaque colonne est décalée selon une sinusoïde."""
    largeur, hauteur = image.size
    resultat = image.copy()
    pas = max(2, largeur // 220)
    amplitude = 3 + puissance * 2.2
    frequence = random.uniform(0.02, 0.07)
    phase = random.uniform(0, 2 * math.pi)
    for x in range(0, largeur, pas):
        dy = int(math.sin(x * frequence + phase) * amplitude)
        bande = image.crop((x, 0, min(largeur, x + pas), hauteur))
        resultat.paste(decalage_sans_bord(bande, 0, dy), (x, 0))
    return resultat


def effet_glitch(image, puissance):
    """Bandes décalées et canaux permutés, façon signal vidéo corrompu."""
    largeur, hauteur = image.size
    resultat = image.copy()
    for _ in range(int(4 + puissance * 2.5)):
        y = random.randint(0, hauteur - 1)
        hb = random.randint(max(1, hauteur // 60), max(2, hauteur // 12))
        bande = image.crop((0, y, largeur, min(hauteur, y + hb)))
        dx = random.randint(-largeur // 6, largeur // 6)
        bande = decalage_sans_bord(bande, dx, 0)
        if random.random() < 0.4:
            r, g, b = bande.split()
            bande = Image.merge("RGB", (b, r, g))
        resultat.paste(bande, (0, y))
    return resultat


def effet_miroir(image, puissance):
    """Une moitié de l'affiche est écrasée par le reflet de l'autre."""
    largeur, hauteur = image.size
    resultat = image.copy()

    def miroir_vertical(img):
        if random.choice((True, False)):
            moitie = ImageOps.mirror(img.crop((0, 0, largeur // 2, hauteur)))
            img.paste(moitie, (largeur - moitie.width, 0))
        else:
            moitie = ImageOps.mirror(img.crop((largeur - largeur // 2, 0, largeur, hauteur)))
            img.paste(moitie, (0, 0))
        return img

    def miroir_horizontal(img):
        if random.choice((True, False)):
            moitie = ImageOps.flip(img.crop((0, 0, largeur, hauteur // 2)))
            img.paste(moitie, (0, hauteur - moitie.height))
        else:
            moitie = ImageOps.flip(img.crop((0, hauteur - hauteur // 2, largeur, hauteur)))
            img.paste(moitie, (0, 0))
        return img

    if puissance >= 7:  # caléidoscope : les deux axes
        resultat = miroir_vertical(resultat)
        return miroir_horizontal(resultat)
    if random.choice((True, False)):
        return miroir_vertical(resultat)
    return miroir_horizontal(resultat)


def effet_zoom(image, puissance):
    """Ne montre qu'un fragment agrandi de l'affiche."""
    largeur, hauteur = image.size
    fraction = max(0.12, 0.5 - puissance * 0.04)
    cw, ch = max(8, int(largeur * fraction)), max(8, int(hauteur * fraction))
    x = random.randint(0, largeur - cw)
    y = random.randint(0, hauteur - ch)
    return image.crop((x, y, x + cw, y + ch)).resize(
        (largeur, hauteur), Image.Resampling.LANCZOS
    )


def effet_projecteur(image, puissance):
    """Tout est quasi noir sauf un disque lumineux à position aléatoire."""
    largeur, hauteur = image.size
    rayon = min(largeur, hauteur) * max(0.12, 0.42 - puissance * 0.03)
    cx = random.uniform(rayon, largeur - rayon)
    cy = random.uniform(rayon, hauteur - rayon)
    masque = Image.new("L", image.size, 0)
    ImageDraw.Draw(masque).ellipse((cx - rayon, cy - rayon, cx + rayon, cy + rayon), fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(rayon * 0.12))
    sombre = ImageEnhance.Brightness(image).enhance(0.05)
    return Image.composite(image, sombre, masque)


def effet_volets(image, puissance):
    """Barres sombres façon stores vénitiens, horizontales ou verticales."""
    largeur, hauteur = image.size
    resultat = image.copy()
    dessin = ImageDraw.Draw(resultat)
    nombre = int(6 + puissance * 1.5)
    couverture = min(0.8, 0.35 + puissance * 0.04)
    couleur = (10, 10, 10)
    if random.choice((True, False)):
        pas = largeur / nombre
        for i in range(nombre):
            x1 = i * pas
            dessin.rectangle((x1, 0, x1 + pas * couverture, hauteur), fill=couleur)
    else:
        pas = hauteur / nombre
        for i in range(nombre):
            y1 = i * pas
            dessin.rectangle((0, y1, largeur, y1 + pas * couverture), fill=couleur)
    return resultat


# ============================================================
# DEFORMATIONS : TROISIEME GENERATION (NOUVEAUTES)
# ============================================================

def effet_lentille(image, puissance):
    """Bombement (loupe) ou pincement (trou noir) autour d'un point."""
    largeur, hauteur = image.size
    cx = random.uniform(largeur * 0.30, largeur * 0.70)
    cy = random.uniform(hauteur * 0.30, hauteur * 0.70)
    rayon = min(largeur, hauteur) * random.uniform(0.35, 0.55)
    force = limiter(0.40 + puissance * 0.05, 0.40, 0.90)
    sens = random.choice((-1, 1))  # 1 = bombé, -1 = pincé

    def f(x, y, _centre=None):
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d >= rayon or d == 0:
            return x, y
        t = d / rayon
        facteur = 1 - sens * force * (1 - t) ** 2
        return cx + dx * facteur, cy + dy * facteur

    return deformer_maillage(image, f)


def effet_ondes_concentriques(image, puissance):
    """Ondes circulaires, comme un caillou jeté dans l'eau."""
    largeur, hauteur = image.size
    echelle = min(largeur, hauteur) / 600
    cx = random.uniform(largeur * 0.25, largeur * 0.75)
    cy = random.uniform(hauteur * 0.25, hauteur * 0.75)
    amplitude = (3 + puissance * 1.6) * echelle
    longueur = min(largeur, hauteur) * random.uniform(0.05, 0.10)
    phase = random.uniform(0, 2 * math.pi)

    def f(x, y, _centre=None):
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d < 1e-6:
            return x, y
        deplacement = amplitude * math.sin(2 * math.pi * d / longueur + phase)
        return x + dx / d * deplacement, y + dy / d * deplacement

    return deformer_maillage(image, f, pas=max(4, min(largeur, hauteur) // 70))


def effet_vagues_2d(image, puissance):
    """Turbulence : l'image ondule dans les deux directions (effet eau / chaleur)."""
    largeur, hauteur = image.size
    echelle = min(largeur, hauteur) / 600
    amplitude = (4 + puissance * 1.8) * echelle
    lx = min(largeur, hauteur) * random.uniform(0.08, 0.20)
    ly = min(largeur, hauteur) * random.uniform(0.08, 0.20)
    p1, p2 = random.uniform(0, 6.28), random.uniform(0, 6.28)

    def f(x, y, _centre=None):
        return (
            x + amplitude * math.sin(2 * math.pi * y / ly + p1),
            y + amplitude * math.sin(2 * math.pi * x / lx + p2),
        )

    return deformer_maillage(image, f, pas=max(4, min(largeur, hauteur) // 60))


def effet_trapeze(image, puissance):
    """Perspective forcée : l'affiche est vue de travers, comme penchée."""
    largeur, hauteur = image.size
    m = limiter(0.03 + puissance * 0.03, 0.03, 0.33)

    def dx():
        return random.uniform(0, m) * largeur

    def dy():
        return random.uniform(0, m) * hauteur

    quad = (
        dx(), dy(),                          # haut-gauche
        dx(), hauteur - dy(),                # bas-gauche
        largeur - dx(), hauteur - dy(),      # bas-droit
        largeur - dx(), dy(),                # haut-droit
    )
    return image.transform(
        image.size, Image.Transform.QUAD, quad, Image.Resampling.BICUBIC
    )


def effet_petite_planete(image, puissance):
    """Projection polaire : l'affiche s'enroule autour du centre."""
    largeur, hauteur = image.size
    cx, cy = largeur / 2, hauteur / 2
    rayon_max = min(largeur, hauteur) * 0.65

    def f(x, y, centre):
        dx, dy = x - cx, y - cy
        theta = math.atan2(dy, dx)
        theta_ref = math.atan2(centre[1] - cy, centre[0] - cx)
        # évite le saut de ±π entre les coins d'une même cellule
        theta = theta_ref + ((theta - theta_ref + math.pi) % (2 * math.pi) - math.pi)
        r = math.hypot(dx, dy)
        sx = (theta / (2 * math.pi) + 0.5) * largeur
        sy = hauteur * (1 - min(1.0, r / rayon_max))
        return sx, sy

    return deformer_maillage(image, f, pas=max(4, min(largeur, hauteur) // 70))


def effet_decalage_cyclique(image, puissance):
    """Bandes qui « sortent » d'un côté et rentrent de l'autre."""
    largeur, hauteur = image.size
    resultat = image.copy()
    nombre = random.randint(10, 40)
    hauteur_bande = max(2, hauteur // nombre)
    amplitude = largeur * limiter(0.03 + puissance * 0.02, 0.03, 0.30)
    progressif = random.choice((True, False))
    for i in range(nombre):
        y = i * hauteur_bande
        bande = image.crop((0, y, largeur, min(hauteur, y + hauteur_bande)))
        if progressif:
            dx = int((i / nombre) * amplitude * 2 - amplitude)
        else:
            dx = random.randint(-int(amplitude), int(amplitude))
        resultat.paste(ImageChops.offset(bande, dx, 0), (0, y))
    return resultat


def effet_caleidoscope(image, puissance):
    """Un seul quart de l'affiche est répété en miroir sur les quatre coins."""
    largeur, hauteur = image.size
    hl, hh = largeur // 2, hauteur // 2
    zones = [
        (0, 0, hl, hh),
        (largeur - hl, 0, largeur, hh),
        (0, hauteur - hh, hl, hauteur),
        (largeur - hl, hauteur - hh, largeur, hauteur),
    ]
    quart = image.crop(random.choice(zones))
    resultat = image.copy()
    resultat.paste(quart, (0, 0))
    resultat.paste(ImageOps.mirror(quart), (largeur - hl, 0))
    resultat.paste(ImageOps.flip(quart), (0, hauteur - hh))
    resultat.paste(quart.rotate(180), (largeur - hl, hauteur - hh))
    return resultat


def effet_tuiles_retournees(image, puissance):
    """Grille de tuiles dont certaines sont miroitées, retournées ou pivotées."""
    largeur, hauteur = image.size
    grille = int(limiter(3 + puissance * 0.6, 3, 9))
    resultat = image.copy()
    for ligne in range(grille):
        for colonne in range(grille):
            if random.random() > 0.65:
                continue
            x1, y1 = colonne * largeur // grille, ligne * hauteur // grille
            x2, y2 = (colonne + 1) * largeur // grille, (ligne + 1) * hauteur // grille
            tuile = image.crop((x1, y1, x2, y2))
            operation = random.choice(("miroir", "flip", "180"))
            if operation == "miroir":
                tuile = ImageOps.mirror(tuile)
            elif operation == "flip":
                tuile = ImageOps.flip(tuile)
            else:
                tuile = tuile.rotate(180)
            resultat.paste(tuile, (x1, y1))
    return resultat


def effet_dispersion(image, puissance):
    """Chaque pixel est remplacé par un voisin aléatoire (poussière / sable)."""
    return image.effect_spread(int(2 + puissance * 2.5))


def effet_blocs_pixelises(image, puissance):
    """Quelques zones très pixelisées (censure), le reste reste net."""
    largeur, hauteur = image.size
    resultat = image.copy()
    for _ in range(int(3 + puissance // 2)):
        bw = int(largeur * random.uniform(0.15, 0.35))
        bh = int(hauteur * random.uniform(0.10, 0.30))
        x = random.randint(0, max(0, largeur - bw))
        y = random.randint(0, max(0, hauteur - bh))
        zone = image.crop((x, y, x + bw, y + bh))
        facteur = random.randint(10, 26)
        petite = zone.resize(
            (max(2, bw // facteur), max(2, bh // facteur)), Image.Resampling.BILINEAR
        )
        resultat.paste(petite.resize((bw, bh), Image.Resampling.NEAREST), (x, y))
    return resultat


def effet_coulures(image, puissance):
    """Des traînées de peinture : un pixel est étiré vers le bas."""
    largeur, hauteur = image.size
    resultat = image.copy()
    for _ in range(int(10 + puissance * 6)):
        lb = random.randint(largeur // 80 + 1, largeur // 25 + 2)
        x = random.randint(0, max(0, largeur - lb))
        y0 = random.randint(int(hauteur * 0.10), int(hauteur * 0.70))
        longueur = random.randint(int(hauteur * 0.15), max(int(hauteur * 0.16), hauteur - y0))
        ligne = image.crop((x, y0, x + lb, y0 + 1))
        resultat.paste(ligne.resize((lb, longueur), Image.Resampling.NEAREST), (x, y0))
    return resultat


def effet_tri_pixels(image, puissance):
    """Pixel sorting : des zones de pixels triées par luminosité (art glitch)."""
    if np is None:
        return effet_glitch(image, puissance)
    largeur, hauteur = image.size
    tableau = np.array(image)
    for _ in range(int(2 + puissance * 1.2)):
        y1 = random.randint(0, max(0, hauteur - 2))
        y2 = min(hauteur, y1 + random.randint(hauteur // 40 + 1, hauteur // 10 + 2))
        x1 = random.randint(0, largeur // 2)
        x2 = min(largeur, x1 + random.randint(largeur // 5, largeur))
        bloc = tableau[y1:y2, x1:x2].astype(np.int32)
        luminosite = bloc[..., 0] * 299 + bloc[..., 1] * 587 + bloc[..., 2] * 114
        ordre = np.argsort(luminosite, axis=1)
        ordre3 = np.repeat(ordre[..., None], 3, axis=2)
        tableau[y1:y2, x1:x2] = np.take_along_axis(
            tableau[y1:y2, x1:x2], ordre3, axis=1
        )
    return Image.fromarray(tableau)


def effet_vitrail(image, puissance):
    """Cellules de Voronoï colorées en aplat, avec des joints sombres."""
    if np is None:
        return effet_cristallisation(image, puissance)
    largeur, hauteur = image.size
    f = min(1.0, 320 / max(largeur, hauteur))
    petite = image.resize(
        (max(8, int(largeur * f)), max(8, int(hauteur * f))),
        Image.Resampling.BILINEAR,
    )
    sl, sh = petite.size
    n = int(limiter(420 - puissance * 32, 80, 420))
    px = np.array([random.uniform(0, sl) for _ in range(n)], dtype=np.float32)
    py = np.array([random.uniform(0, sh) for _ in range(n)], dtype=np.float32)
    gy, gx = np.mgrid[0:sh, 0:sl]
    gx = gx.ravel().astype(np.float32)
    gy = gy.ravel().astype(np.float32)
    etiquettes = np.empty(gx.size, dtype=np.int32)
    for debut in range(0, gx.size, 6000):
        fin = debut + 6000
        dx = gx[debut:fin, None] - px[None, :]
        dy = gy[debut:fin, None] - py[None, :]
        etiquettes[debut:fin] = np.argmin(dx * dx + dy * dy, axis=1)
    pixels = np.asarray(petite, dtype=np.float32).reshape(-1, 3)
    effectifs = np.maximum(np.bincount(etiquettes, minlength=n), 1).astype(np.float32)
    moyennes = np.stack(
        [np.bincount(etiquettes, weights=pixels[:, c], minlength=n) / effectifs
         for c in range(3)],
        axis=1,
    )
    sortie = moyennes[etiquettes].reshape(sh, sl, 3).astype(np.float32)
    carte = etiquettes.reshape(sh, sl)
    bord = np.zeros((sh, sl), dtype=bool)
    bord[:, :-1] |= carte[:, :-1] != carte[:, 1:]
    bord[:-1, :] |= carte[:-1, :] != carte[1:, :]
    sortie[bord] *= 0.30
    resultat = Image.fromarray(np.clip(sortie, 0, 255).astype(np.uint8))
    return resultat.resize((largeur, hauteur), Image.Resampling.BILINEAR)


def effet_halftone(image, puissance):
    """Trame de points façon impression pop-art."""
    largeur, hauteur = image.size
    colonnes = int(limiter(75 - puissance * 5, 25, 75))
    cellule = max(4, largeur // colonnes)
    nx, ny = largeur // cellule + 1, hauteur // cellule + 1
    petite = image.resize((nx, ny), Image.Resampling.BOX)
    clair = random.choice((True, False))
    fond = (244, 240, 230) if clair else (12, 12, 12)
    sortie = Image.new("RGB", (largeur, hauteur), fond)
    dessin = ImageDraw.Draw(sortie)
    pixels = petite.load()
    for j in range(ny):
        for i in range(nx):
            r, g, b = pixels[i, j]
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            taille = (1 - lum) if clair else lum
            rayon = cellule * 0.75 * math.sqrt(max(0.0, taille))
            cx, cy = (i + 0.5) * cellule, (j + 0.5) * cellule
            dessin.ellipse((cx - rayon, cy - rayon, cx + rayon, cy + rayon), fill=(r, g, b))
    return sortie


def effet_flou_selectif(image, puissance):
    """Seule une bande reste nette (effet maquette / tilt-shift)."""
    largeur, hauteur = image.size
    flou = image.filter(ImageFilter.GaussianBlur(3 + puissance * 1.8))
    masque = Image.new("L", (largeur, hauteur), 0)
    dessin = ImageDraw.Draw(masque)
    epaisseur = max(0.15, 0.45 - puissance * 0.03)
    if random.choice((True, False)):
        y = random.uniform(0, hauteur * (1 - epaisseur))
        dessin.rectangle((0, y, largeur, y + hauteur * epaisseur), fill=255)
    else:
        x = random.uniform(0, largeur * (1 - epaisseur))
        dessin.rectangle((x, 0, x + largeur * epaisseur, hauteur), fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(min(largeur, hauteur) * 0.04))
    return Image.composite(image, flou, masque)


def effet_damier(image, puissance):
    """Des cases de la grille sont masquées au hasard."""
    largeur, hauteur = image.size
    resultat = image.copy()
    dessin = ImageDraw.Draw(resultat)
    colonnes = int(limiter(5 + puissance, 6, 14))
    lignes = max(4, int(colonnes * hauteur / largeur))
    proba = min(0.65, 0.25 + puissance * 0.04)
    couleur = random.choice(((15, 15, 15), (235, 235, 235)))
    for ligne in range(lignes):
        for colonne in range(colonnes):
            if random.random() < proba:
                dessin.rectangle((
                    colonne * largeur // colonnes, ligne * hauteur // lignes,
                    (colonne + 1) * largeur // colonnes - 1,
                    (ligne + 1) * hauteur // lignes - 1,
                ), fill=couleur)
    return resultat


def effet_taches_encre(image, puissance):
    """Des taches d'encre noire recouvrent l'affiche."""
    largeur, hauteur = image.size
    masque = Image.new("L", (largeur, hauteur), 0)
    dessin = ImageDraw.Draw(masque)
    petit_cote = min(largeur, hauteur)
    for _ in range(int(4 + puissance)):
        rx = petit_cote * random.uniform(0.05, 0.13)
        ry = petit_cote * random.uniform(0.05, 0.13)
        cx, cy = random.uniform(0, largeur), random.uniform(0, hauteur)
        dessin.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(petit_cote * 0.015))
    masque = masque.point(lambda p: 255 if p > 110 else int(p * 2.3))
    encre = Image.new("RGB", (largeur, hauteur), (12, 8, 14))
    return Image.composite(encre, image, masque)


def effet_lampes(image, puissance):
    """Plusieurs petits disques lumineux dans le noir (lampes torches)."""
    largeur, hauteur = image.size
    rayon = min(largeur, hauteur) * max(0.07, 0.20 - puissance * 0.012)
    masque = Image.new("L", image.size, 0)
    dessin = ImageDraw.Draw(masque)
    for _ in range(random.randint(3, 6)):
        cx = random.uniform(rayon, largeur - rayon)
        cy = random.uniform(rayon, hauteur - rayon)
        dessin.ellipse((cx - rayon, cy - rayon, cx + rayon, cy + rayon), fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(rayon * 0.15))
    sombre = ImageEnhance.Brightness(image).enhance(0.05)
    return Image.composite(image, sombre, masque)


def effet_trapeze_double(image, puissance):
    """Perspective + miroir central : l'affiche se replie sur elle-même."""
    return effet_trapeze(effet_miroir(image, min(6, puissance)), puissance)


# ============================================================
# EFFETS DE COULEUR
# ============================================================

def effet_noir_blanc(image, puissance):
    gris = ImageOps.grayscale(image)
    contraste = ImageEnhance.Contrast(gris).enhance(1.0 + puissance * 0.10)
    return Image.merge("RGB", (contraste, contraste, contraste))


def effet_canal_rouge(image, puissance):
    rouge, _, _ = image.split()
    zero = Image.new("L", image.size, 0)
    return Image.merge("RGB", (rouge, zero, zero))


def effet_canal_vert(image, puissance):
    _, vert, _ = image.split()
    zero = Image.new("L", image.size, 0)
    return Image.merge("RGB", (zero, vert, zero))


def effet_canal_bleu(image, puissance):
    _, _, bleu = image.split()
    zero = Image.new("L", image.size, 0)
    return Image.merge("RGB", (zero, zero, bleu))


def effet_changement_couleur(image, puissance):
    """Décalage de teinte, de saturation et de luminosité aléatoires."""
    h, s, v = image.convert("HSV").split()
    decalage_teinte = random.randint(20 + puissance * 2, 110 + puissance * 8) % 256
    facteur_saturation = random.uniform(
        max(0.25, 0.75 - puissance * 0.025), 1.55 + puissance * 0.08
    )
    facteur_luminosite = random.uniform(
        max(0.45, 0.80 - puissance * 0.035), 1.20 + puissance * 0.05
    )
    h = h.point(lambda valeur: (valeur + decalage_teinte) % 256)
    s = s.point(lambda valeur: limiter(int(valeur * facteur_saturation), 0, 255))
    v = v.point(lambda valeur: limiter(int(valeur * facteur_luminosite), 0, 255))
    return Image.merge("HSV", (h, s, v)).convert("RGB")


def effet_saturation(image, puissance):
    if random.choice([True, False]):
        facteur = max(0.03, 1.0 - puissance * 0.11)
    else:
        facteur = 1.0 + puissance * 0.28
    return ImageEnhance.Color(image).enhance(facteur)


def effet_inversion(image, puissance):
    return ImageOps.invert(image)


def effet_posterisation(image, puissance):
    """Réduit le nombre de niveaux de couleur (aplats façon sérigraphie)."""
    bits = int(limiter(5 - puissance // 2, 1, 4))
    resultat = ImageOps.posterize(image, bits)
    return ImageEnhance.Contrast(resultat).enhance(1.2)


def effet_solarisation(image, puissance):
    """Inverse les tons clairs : rendu proche d'un négatif partiel."""
    seuil = int(limiter(200 - puissance * 12, 60, 200))
    return ImageOps.solarize(image, seuil)


PALETTES_DUOTONE = [
    ((20, 0, 60), (255, 120, 0)),
    ((0, 40, 40), (255, 230, 120)),
    ((60, 0, 20), (120, 255, 230)),
    ((0, 0, 0), (255, 0, 120)),
    ((0, 20, 80), (255, 255, 255)),
]


def effet_duotone(image, puissance):
    """Deux couleurs seulement, choisies au hasard."""
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    sombre, clair = random.choice(PALETTES_DUOTONE)
    return ImageOps.colorize(gris, black=sombre, white=clair)


# --- nouveautés couleur ---

PALETTES_TRICOLORES = [
    ((0, 0, 40), (220, 40, 0), (255, 255, 200)),     # thermique
    ((10, 0, 30), (200, 30, 120), (255, 220, 120)),  # crépuscule
    ((0, 20, 20), (0, 160, 150), (250, 250, 200)),   # lagon
    ((20, 0, 0), (230, 130, 20), (255, 250, 220)),   # braise
    ((0, 0, 0), (80, 200, 60), (230, 255, 200)),     # vision nocturne
]


def effet_degrade_couleurs(image, puissance):
    """Carte de dégradé à trois couleurs (caméra thermique, crépuscule...)."""
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    if random.random() < 0.25:
        gris = ImageOps.invert(gris)
    noir, milieu, blanc = random.choice(PALETTES_TRICOLORES)
    return ImageOps.colorize(gris, black=noir, white=blanc, mid=milieu)


def effet_permutation_canaux(image, puissance):
    """Les canaux rouge, vert et bleu sont mélangés (visage bleu, ciel rouge...)."""
    canaux = list(image.split())
    ordre = [0, 1, 2]
    while ordre == [0, 1, 2]:
        random.shuffle(ordre)
    return Image.merge("RGB", [canaux[i] for i in ordre])


def effet_seuil(image, puissance):
    """Noir et blanc pur (ou deux couleurs), sans aucune nuance intermédiaire."""
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    seuil = random.randint(95, 165)
    binaire = gris.point(lambda p: 255 if p >= seuil else 0)
    if random.random() < 0.5:
        return binaire.convert("RGB")
    sombre, clair = random.choice(PALETTES_DUOTONE)
    return ImageOps.colorize(binaire, black=sombre, white=clair)


def effet_isolation_couleur(image, puissance):
    """Tout passe en gris sauf une teinte (celle de l'affiche la plus saturée)."""
    largeur, hauteur = image.size
    hsv = image.convert("HSV")
    teinte_canal, sat_canal, _ = hsv.split()
    meilleur = (0, 0, 0)
    for _ in range(40):
        pixel = hsv.getpixel((random.randrange(largeur), random.randrange(hauteur)))
        if pixel[1] > meilleur[1]:
            meilleur = pixel
    teinte = meilleur[0]
    ecart = int(limiter(40 - puissance * 2.5, 10, 40))
    masque_t = teinte_canal.point(
        lambda v: 255 if min((v - teinte) % 256, (teinte - v) % 256) <= ecart else 0
    )
    masque_s = sat_canal.point(lambda v: 255 if v > 40 else 0)
    masque = ImageChops.multiply(masque_t, masque_s).filter(ImageFilter.GaussianBlur(1.5))
    gris = ImageOps.grayscale(image).convert("RGB")
    return Image.composite(image, gris, masque)


def effet_exposition(image, puissance):
    """Photo brûlée (surexposée) ou presque noire (sous-exposée)."""
    if random.choice((True, False)):
        resultat = ImageEnhance.Brightness(image).enhance(1.5 + puissance * 0.18)
        return ImageEnhance.Contrast(resultat).enhance(0.8)
    resultat = ImageEnhance.Brightness(image).enhance(max(0.12, 0.70 - puissance * 0.06))
    return ImageEnhance.Contrast(resultat).enhance(1.5)


def effet_dominante(image, puissance):
    """Voile de couleur franche sur toute l'affiche."""
    couleur = random.choice(
        ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 190, 0))
    )
    alpha = limiter(0.25 + puissance * 0.045, 0.25, 0.70)
    return Image.blend(image, Image.new("RGB", image.size, couleur), alpha)


def effet_contraste_extreme(image, puissance):
    """Contraste poussé à l'extrême : ombres bouchées, hautes lumières brûlées."""
    resultat = ImageOps.autocontrast(image, cutoff=2)
    return ImageEnhance.Contrast(resultat).enhance(1.6 + puissance * 0.30)


def effet_croquis(image, puissance):
    """Dessin au trait : uniquement les contours sombres sur fond blanc."""
    gris = ImageOps.grayscale(image).filter(ImageFilter.GaussianBlur(1))
    contours = ImageOps.invert(gris.filter(ImageFilter.FIND_EDGES))
    contours = ImageOps.autocontrast(contours, cutoff=2)
    contours = ImageEnhance.Contrast(contours).enhance(1.5 + puissance * 0.20)
    return Image.merge("RGB", (contours, contours, contours))


# ============================================================
# EFFETS COMPLEMENTAIRES
# ============================================================

def effet_rotation_180(image, puissance):
    return image.rotate(180, expand=False)


def effet_bruit(image, puissance):
    largeur, hauteur = image.size
    intensite = int(6 + puissance * 5)
    bruit = Image.effect_noise((largeur, hauteur), 35 + puissance * 7).convert("L")
    bruit = bruit.point(
        lambda p: limiter(128 + int((p - 128) * intensite / 35), 0, 255)
    )
    return ImageChops.add(
        image, Image.merge("RGB", (bruit, bruit, bruit)), scale=2.0, offset=-128
    )


def effet_bosse(image, puissance):
    relief = image.filter(ImageFilter.EMBOSS)
    contraste = ImageEnhance.Contrast(relief).enhance(1.0 + puissance * 0.10)
    return Image.blend(image, contraste, min(0.95, 0.45 + puissance * 0.05))


def effet_contour_amplifie(image, puissance):
    contours = image.filter(ImageFilter.FIND_EDGES)
    contours = ImageEnhance.Contrast(contours).enhance(1.5 + puissance * 0.45)
    contours = ImageEnhance.Sharpness(contours).enhance(1.5)
    return Image.blend(image, contours, min(0.82, 0.25 + puissance * 0.055))


def effet_aberration_chromatique(image, puissance):
    """Les canaux rouge et bleu sont décalés en sens opposés."""
    r, g, b = image.split()
    d = int(3 + puissance * 2.2)
    dx = random.choice((-1, 1)) * d
    dy = random.randint(-d // 2, d // 2)
    r = decalage_sans_bord(r, dx, dy)
    b = decalage_sans_bord(b, -dx, -dy)
    return Image.merge("RGB", (r, g, b))


# --- nouveautés complémentaires ---

def effet_retournement(image, puissance):
    """Miroir gauche-droite ou haut-bas de toute l'affiche."""
    if random.choice((True, False)):
        return ImageOps.mirror(image)
    return ImageOps.flip(image)


def effet_rotation_legere(image, puissance):
    """Affiche penchée ; les coins vides sont comblés par une version floue."""
    largeur, hauteur = image.size
    angle = random.choice((-1, 1)) * random.uniform(8, 12 + puissance * 3)
    tournee = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
    masque = Image.new("L", image.size, 255).rotate(angle, expand=False)
    fond = image.filter(ImageFilter.GaussianBlur(min(largeur, hauteur) / 20))
    return Image.composite(tournee, fond, masque)


def effet_double_vision(image, puissance):
    """Image fantôme : l'affiche est dédoublée avec un décalage."""
    largeur, hauteur = image.size
    d = int(max(largeur, hauteur) * (0.01 + puissance * 0.006))
    dx = random.choice((-1, 1)) * d
    dy = random.choice((-1, 1)) * random.randint(0, d)
    return Image.blend(image, decalage_sans_bord(image, dx, dy), 0.5)


def effet_vignettage(image, puissance):
    """Les bords s'assombrissent fortement."""
    largeur, hauteur = image.size
    marge = limiter(0.05 + puissance * 0.02, 0.07, 0.25)
    masque = Image.new("L", image.size, 0)
    ImageDraw.Draw(masque).ellipse((
        largeur * marge, hauteur * marge,
        largeur * (1 - marge), hauteur * (1 - marge),
    ), fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(min(largeur, hauteur) * 0.15))
    return Image.composite(image, Image.new("RGB", image.size, (0, 0, 0)), masque)


def effet_lignes_balayage(image, puissance):
    """Lignes de balayage façon vieil écran cathodique."""
    largeur, hauteur = image.size
    pas = max(2, hauteur // 200)
    masque = Image.new("L", image.size, 0)
    dessin = ImageDraw.Draw(masque)
    opacite = int(limiter(80 + puissance * 10, 80, 190))
    for y in range(0, hauteur, pas * 2):
        dessin.rectangle((0, y, largeur, y + pas - 1), fill=opacite)
    return Image.composite(Image.new("RGB", image.size, (0, 0, 0)), image, masque)


def effet_sel_poivre(image, puissance):
    """Pixels blancs et noirs éparpillés (neige de télévision)."""
    largeur, hauteur = image.size
    z = limiter(2.3 - puissance * 0.11, 1.2, 2.3)
    bruit = Image.effect_noise((largeur, hauteur), 127 / z).convert("L")
    blancs = bruit.point(lambda p: 255 if p >= 253 else 0)
    noirs = bruit.point(lambda p: 255 if p <= 2 else 0)
    resultat = image.copy()
    resultat.paste((255, 255, 255), mask=blancs)
    resultat.paste((0, 0, 0), mask=noirs)
    return resultat


def effet_pellicule_abimee(image, puissance):
    """Rayures verticales claires, comme un vieux film."""
    largeur, hauteur = image.size
    resultat = image.copy()
    dessin = ImageDraw.Draw(resultat)
    for _ in range(int(6 + puissance * 4)):
        x = random.randint(0, largeur - 1)
        y1 = random.randint(0, hauteur // 2)
        y2 = random.randint(y1 + hauteur // 5, hauteur)
        gris = random.randint(200, 255)
        dessin.line((x, y1, x + random.randint(-3, 3), y2),
                    fill=(gris, gris, gris), width=random.randint(1, 2))
    return resultat


def effet_nettete_extreme(image, puissance):
    """Hyper-netteté : grain agressif et halos autour des contours."""
    resultat = ImageEnhance.Sharpness(image).enhance(3 + puissance * 1.5)
    return resultat.filter(ImageFilter.UnsharpMask(radius=3, percent=150 + puissance * 25, threshold=2))


def effet_lueur(image, puissance):
    """Halo lumineux (bloom) autour des zones claires."""
    flou = image.filter(ImageFilter.GaussianBlur(4 + puissance * 1.6))
    flou = ImageEnhance.Brightness(flou).enhance(1.3)
    return ImageChops.screen(image, Image.blend(Image.new("RGB", image.size, (0, 0, 0)), flou, 0.8))


def effet_tremblement(image, puissance):
    """Triple exposition horizontale, comme un appareil photo qui bouge."""
    d = int(4 + puissance * 3)
    a = decalage_sans_bord(image, d, 0)
    b = decalage_sans_bord(image, -d, 0)
    return Image.blend(Image.blend(image, a, 1 / 3), b, 1 / 3)


def effet_cadre_noir(image, puissance):
    """Épais cadre noir qui mange les bords de l'affiche."""
    largeur, hauteur = image.size
    epaisseur = int(min(largeur, hauteur) * limiter(0.03 + puissance * 0.012, 0.04, 0.15))
    resultat = image.copy()
    dessin = ImageDraw.Draw(resultat)
    dessin.rectangle((0, 0, largeur, epaisseur), fill=(0, 0, 0))
    dessin.rectangle((0, hauteur - epaisseur, largeur, hauteur), fill=(0, 0, 0))
    dessin.rectangle((0, 0, epaisseur, hauteur), fill=(0, 0, 0))
    dessin.rectangle((largeur - epaisseur, 0, largeur, hauteur), fill=(0, 0, 0))
    return resultat


# ============================================================
# EFFETS SUPPLEMENTAIRES
# ============================================================

# ------------------------------------------------------------
# COULEUR : canaux et inversions
# ------------------------------------------------------------

def effet_deux_canaux(image, puissance):
    """Ne garde que deux canaux : rouge+vert, rouge+bleu ou vert+bleu."""
    r, g, b = image.split()
    zero = Image.new("L", image.size, 0)
    garde = random.choice(("rv", "rb", "vb"))
    if garde == "rv":
        return Image.merge("RGB", (r, g, zero))
    if garde == "rb":
        return Image.merge("RGB", (r, zero, b))
    return Image.merge("RGB", (zero, g, b))


def effet_canal_en_gris(image, puissance):
    """Un seul canal (R, V ou B) affiché en niveaux de gris : contrastes inattendus."""
    canal = ImageOps.autocontrast(random.choice(image.split()), cutoff=1)
    return Image.merge("RGB", (canal, canal, canal))


def effet_inversion_canaux(image, puissance):
    """Inverse seulement un ou deux canaux (ciel orange, peau verte...)."""
    canaux = list(image.split())
    for i in random.sample(range(3), random.choice((1, 2))):
        canaux[i] = ImageOps.invert(canaux[i])
    return Image.merge("RGB", canaux)


def effet_inversion_luminosite(image, puissance):
    """Les clairs deviennent sombres mais les teintes restent les mêmes."""
    h, s, v = image.convert("HSV").split()
    return Image.merge("HSV", (h, s, ImageOps.invert(v))).convert("RGB")


def effet_teintes_complementaires(image, puissance):
    """Chaque couleur est remplacée par sa complémentaire (luminosité conservée)."""
    h, s, v = image.convert("HSV").split()
    h = h.point(lambda x: (x + 128) % 256)
    return Image.merge("HSV", (h, s, v)).convert("RGB")


def effet_sepia(image, puissance):
    """Vieille photo brune."""
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    return ImageOps.colorize(
        gris, black=(25, 10, 0), white=(255, 235, 190), mid=(140, 95, 50)
    )


# ------------------------------------------------------------
# COULEUR : styles « dessin »
# ------------------------------------------------------------

def _contours(image, flou=1.0):
    """Carte de contours (clairs sur fond sombre), normalisée."""
    gris = ImageOps.grayscale(image).filter(ImageFilter.GaussianBlur(flou))
    return ImageOps.autocontrast(gris.filter(ImageFilter.FIND_EDGES), cutoff=1)


def effet_neon(image, puissance):
    """Contours lumineux aux couleurs de l'affiche sur fond noir."""
    contours = ImageEnhance.Brightness(_contours(image)).enhance(1.6 + puissance * 0.15)
    vives = ImageEnhance.Color(image).enhance(2.0)
    trait = ImageChops.multiply(vives, Image.merge("RGB", (contours,) * 3))
    lueur = trait.filter(ImageFilter.GaussianBlur(3 + puissance * 0.3))
    return ImageChops.screen(trait, lueur)


def effet_blueprint(image, puissance):
    """Plan d'architecte : traits blancs sur fond bleu."""
    contours = ImageEnhance.Contrast(_contours(image)).enhance(1.4 + puissance * 0.15)
    return ImageOps.colorize(contours, black=(15, 50, 140), white=(235, 245, 255))


def effet_fusain(image, puissance):
    """Dessin au fusain : traits gras, ombres estompées, grain de papier."""
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    traits = ImageOps.invert(_contours(image, 1.5))
    estompe = gris.filter(ImageFilter.GaussianBlur(2)).point(lambda p: 90 + int(p * 0.65))
    dessin = ImageChops.multiply(traits, estompe)
    grain = Image.effect_noise(image.size, 40).convert("L")
    dessin = Image.blend(dessin, grain, 0.10)
    dessin = ImageEnhance.Contrast(dessin).enhance(1.2 + puissance * 0.12)
    return ImageOps.colorize(ImageOps.autocontrast(dessin), black=(15, 15, 15), white=(238, 232, 220))


def effet_gravure(image, puissance):
    """Gravure : lignes horizontales dont l'épaisseur dépend de la luminosité."""
    largeur, hauteur = image.size
    gris = ImageOps.autocontrast(ImageOps.grayscale(image))
    lignes = int(limiter(110 - puissance * 6, 40, 110))
    pas = max(3, hauteur // lignes)
    binaire = Image.new("L", image.size, 255)
    for k in range(pas):
        distance = abs(2 * (k + 0.5) / pas - 1)   # 0 au centre du trait, 1 au bord
        seuil = int(255 * (1 - distance))
        phase = gris.point(lambda p, s=seuil: 0 if p < s else 255)
        for y in range(k, hauteur, pas):
            binaire.paste(phase.crop((0, y, largeur, y + 1)), (0, y))
    return ImageOps.colorize(binaire, black=(20, 15, 10), white=(240, 232, 215))


def effet_aquarelle(image, puissance):
    """Aplats adoucis, couleurs délavées et léger contour crayonné."""
    base = image.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MedianFilter(5))
    base = base.filter(ImageFilter.GaussianBlur(0.8 + puissance * 0.1))
    base = ImageEnhance.Color(base).enhance(0.9)
    base = Image.blend(base, Image.new("RGB", image.size, (255, 253, 245)), 0.18)
    trait = ImageOps.invert(_contours(image, 1.2)).point(lambda p: 150 + p * 105 // 255)
    return ImageChops.multiply(base, Image.merge("RGB", (trait,) * 3))


def effet_cartoon(image, puissance):
    """Bande dessinée : couleurs en aplats et contours noirs."""
    lisse = image.filter(ImageFilter.MedianFilter(5))
    poster = ImageOps.posterize(ImageEnhance.Color(lisse).enhance(1.4), 3)
    gris = ImageOps.grayscale(image).filter(ImageFilter.GaussianBlur(1.2))
    seuil = int(limiter(40 - puissance * 2.5, 12, 40))
    trait = gris.filter(ImageFilter.FIND_EDGES).point(lambda p: 0 if p > seuil else 255)
    return ImageChops.multiply(poster, Image.merge("RGB", (trait,) * 3))


# ------------------------------------------------------------
# DEFORMATIONS : nouvelles
# ------------------------------------------------------------

def effet_pop_art(image, puissance):
    """Quatre exemplaires de l'affiche, chacun dans une palette différente."""
    largeur, hauteur = image.size
    w2, h2 = largeur // 2, hauteur // 2
    resultat = Image.new("RGB", image.size)
    palettes = random.sample(PALETTES_DUOTONE, 4)
    for idx, (sombre, clair) in enumerate(palettes):
        x = (idx % 2) * w2
        y = (idx // 2) * h2
        tw = w2 if idx % 2 == 0 else largeur - w2
        th = h2 if idx // 2 == 0 else hauteur - h2
        gris = ImageOps.autocontrast(ImageOps.grayscale(
            image.resize((tw, th), Image.Resampling.LANCZOS)))
        resultat.paste(ImageOps.colorize(gris, black=sombre, white=clair), (x, y))
    return resultat


def effet_cisaillement(image, puissance):
    """Affiche penchée comme un parallélogramme (cisaillement horizontal ou vertical)."""
    largeur, hauteur = image.size
    f = random.choice((-1, 1)) * limiter(0.08 + puissance * 0.03, 0.08, 0.40)
    if random.choice((True, False)):
        donnees = (1, f, -f * hauteur / 2, 0, 1, 0)
    else:
        donnees = (1, 0, 0, f, 1, -f * largeur / 2)
    transformee = image.transform(image.size, Image.Transform.AFFINE, donnees,
                                  Image.Resampling.BICUBIC)
    masque = Image.new("L", image.size, 255).transform(
        image.size, Image.Transform.AFFINE, donnees, Image.Resampling.BILINEAR)
    fond = image.filter(ImageFilter.GaussianBlur(min(largeur, hauteur) / 20))
    return Image.composite(transformee, fond, masque)


def effet_bandes_inversees(image, puissance):
    """Une bande sur deux est en négatif (horizontale ou verticale)."""
    largeur, hauteur = image.size
    nombre = random.randint(4, 8 + puissance)
    resultat = image.copy()
    vertical = random.choice((True, False))
    for i in range(nombre):
        if i % 2 == 0:
            continue
        if vertical:
            x1, x2 = i * largeur // nombre, (i + 1) * largeur // nombre
            boite = (x1, 0, x2, hauteur)
        else:
            y1, y2 = i * hauteur // nombre, (i + 1) * hauteur // nombre
            boite = (0, y1, largeur, y2)
        resultat.paste(ImageOps.invert(image.crop(boite)), boite[:2])
    return resultat


def effet_bandes_canaux(image, puissance):
    """Chaque bande a ses canaux de couleur permutés différemment."""
    largeur, hauteur = image.size
    nombre = random.randint(5, 10 + puissance)
    resultat = image.copy()
    vertical = random.choice((True, False))
    for i in range(nombre):
        if vertical:
            boite = (i * largeur // nombre, 0, (i + 1) * largeur // nombre, hauteur)
        else:
            boite = (0, i * hauteur // nombre, largeur, (i + 1) * hauteur // nombre)
        canaux = list(image.crop(boite).split())
        random.shuffle(canaux)
        resultat.paste(Image.merge("RGB", canaux), boite[:2])
    return resultat


def effet_tuiles_pivotees(image, puissance):
    """Grille de tuiles légèrement tournées, façon puzzle mal assemblé."""
    largeur, hauteur = image.size
    grille = int(limiter(3 + puissance * 0.4, 3, 7))
    resultat = image.copy()
    for ligne in range(grille):
        for colonne in range(grille):
            x1, y1 = colonne * largeur // grille, ligne * hauteur // grille
            x2, y2 = (colonne + 1) * largeur // grille, (ligne + 1) * hauteur // grille
            tuile = image.crop((x1, y1, x2, y2))
            angle = random.uniform(-6 - puissance * 2, 6 + puissance * 2)
            tournee = tuile.rotate(angle, resample=Image.Resampling.BICUBIC)
            masque = Image.new("L", tuile.size, 255).rotate(angle)
            resultat.paste(Image.composite(tournee, tuile, masque), (x1, y1))
    return resultat


def effet_ecran_lcd(image, puissance):
    """Gros pixels d'écran avec sous-pixels rouge / vert / bleu visibles."""
    largeur, hauteur = image.size
    pas = max(3, int(largeur / limiter(150 - puissance * 8, 60, 150)))
    petite = image.resize((max(1, largeur // pas), max(1, hauteur // pas)), Image.Resampling.BOX)
    gros = petite.resize((petite.width * pas, petite.height * pas), Image.Resampling.NEAREST)
    tuile = Image.new("RGB", (pas, pas), (0, 0, 0))
    dessin = ImageDraw.Draw(tuile)
    cw = max(1, pas // 3)
    hauteur_utile = pas - 1 if pas >= 4 else pas
    for i, couleur in enumerate(((255, 70, 70), (70, 255, 70), (70, 70, 255))):
        dessin.rectangle((i * cw, 0, min(pas - 1, (i + 1) * cw - 1), hauteur_utile - 1), fill=couleur)
    bande = Image.new("RGB", (gros.width, pas))
    for x in range(0, gros.width, pas):
        bande.paste(tuile, (x, 0))
    grille = Image.new("RGB", gros.size)
    for y in range(0, gros.height, pas):
        grille.paste(bande, (0, y))
    resultat = ImageEnhance.Brightness(ImageChops.multiply(gros, grille)).enhance(1.7)
    if resultat.size != image.size:
        fond = Image.new("RGB", image.size, (0, 0, 0))
        fond.paste(resultat, (0, 0))
        resultat = fond
    return resultat




# ============================================================
# FAMILLES D'EFFETS
# ============================================================

# Une déformation / un obscurcissement est TOUJOURS appliqué en premier.
EFFETS_DEFORMATION = [
    effet_pixelisation,
    effet_flou,
    effet_mosaique,
    effet_cabossage,
    effet_cristallisation,
    effet_torsion,
    effet_verre_depoli,
    effet_torsion_circulaire,
    effet_fragmentation,
    effet_ondulation,
    effet_glitch,
    effet_miroir,
    effet_zoom,
    effet_projecteur,
    effet_volets,
    # nouveautés
    effet_lentille,
    effet_ondes_concentriques,
    effet_vagues_2d,
    effet_trapeze,
    effet_petite_planete,
    effet_decalage_cyclique,
    effet_caleidoscope,
    effet_tuiles_retournees,
    effet_dispersion,
    effet_blocs_pixelises,
    effet_coulures,
    effet_tri_pixels,
    effet_vitrail,
    effet_halftone,
    effet_flou_selectif,
    effet_damier,
    effet_taches_encre,
    effet_lampes,
    effet_trapeze_double,
    effet_pop_art,
    effet_cisaillement,
    effet_bandes_inversees,
    effet_bandes_canaux,
    effet_tuiles_pivotees,
    effet_ecran_lcd,
]

# Jusqu'à deux effets de couleur peuvent être appliqués par affiche.
EFFETS_COULEUR = [
    effet_noir_blanc,
    effet_canal_rouge,
    effet_canal_vert,
    effet_canal_bleu,
    effet_changement_couleur,
    effet_saturation,
    effet_inversion,
    effet_posterisation,
    effet_solarisation,
    effet_duotone,
    # nouveautés
    effet_degrade_couleurs,
    effet_permutation_canaux,
    effet_seuil,
    effet_isolation_couleur,
    effet_exposition,
    effet_dominante,
    effet_contraste_extreme,
    effet_croquis,
    effet_deux_canaux,
    effet_canal_en_gris,
    effet_inversion_canaux,
    effet_inversion_luminosite,
    effet_teintes_complementaires,
    effet_sepia,
    effet_neon,
    effet_blueprint,
    effet_fusain,
    effet_gravure,
    effet_aquarelle,
    effet_cartoon,
]

EFFETS_COMPLEMENTAIRES = [
    effet_rotation_180,
    effet_bruit,
    effet_bosse,
    effet_contour_amplifie,
    effet_aberration_chromatique,
    # nouveautés
    effet_retournement,
    effet_rotation_legere,
    effet_double_vision,
    effet_vignettage,
    effet_lignes_balayage,
    effet_sel_poivre,
    effet_pellicule_abimee,
    effet_nettete_extreme,
    effet_lueur,
    effet_tremblement,
    effet_cadre_noir,
]

# Quand l'une de ces déformations est choisie, aucune autre
# déformation n'est ajoutée.
DEFORMATIONS_EXCLUSIVES = {"effet_fragmentation", "effet_petite_planete"}

# Effets qui cachent une grande partie de l'affiche : un seul à la fois,
# pour que l'affiche reste devinable.
OCCULTANTS = {
    "effet_zoom", "effet_projecteur", "effet_volets", "effet_miroir",
    "effet_caleidoscope", "effet_damier", "effet_taches_encre",
    "effet_lampes", "effet_flou_selectif", "effet_trapeze_double",
}

# Effets qui détruisent les détails fins : un seul à la fois.
DESTRUCTEURS = {
    "effet_pixelisation", "effet_flou", "effet_cristallisation",
    "effet_verre_depoli", "effet_halftone", "effet_vitrail",
    "effet_dispersion", "effet_petite_planete", "effet_mosaique",
    "effet_ecran_lcd", "effet_aquarelle",
}

# Un seul style graphique lourd par affiche.
STYLES_DESSIN = {
    "effet_croquis", "effet_neon", "effet_blueprint", "effet_fusain",
    "effet_gravure", "effet_aquarelle", "effet_cartoon", "effet_pop_art",
}

# Effets qui doivent travailler sur l'affiche d'origine (pour en garder les
# vraies couleurs) : ils ne peuvent être choisis qu'en première position.
PREMIERE_SEULEMENT = {"effet_mosaique"}


def lister_effets():
    """Retourne les noms des effets par famille (utile pour l'interface)."""
    return {
        "deformation": [e.__name__ for e in EFFETS_DEFORMATION],
        "couleur": [e.__name__ for e in EFFETS_COULEUR],
        "complementaire": [e.__name__ for e in EFFETS_COMPLEMENTAIRES],
    }


# ============================================================
# TRANSFORMATION COMPLETE
# ============================================================

def transformer_image(image_originale, nombre_effets, puissance,
                      graine=None, retourner_noms=False):
    """
    Applique au moins 2 opérations.

    Règles :
    - une déformation est toujours appliquée en premier ;
    - la fragmentation et la petite planète sont des déformations exclusives ;
    - un seul effet d'occultation (zoom, projecteur, volets, miroir, damier...) ;
    - un seul destructeur de détails (pixelisation, flou, vitrail, halftone, mosaïque...) ;
    - la mosaïque n'est possible qu'en première position (couleurs de l'affiche) ;
    - jusqu'à deux effets de couleur maximum ;
    - les effets de couleur sont mélangés au même pool aléatoire que les autres effets.

    graine          : entier facultatif, pour rejouer exactement la même affiche.
    retourner_noms  : si True, retourne (image, [noms des effets appliqués]).
    """
    if graine is not None:
        random.seed(graine)

    nombre_effets = int(limiter(nombre_effets, 2, 12))
    puissance = int(limiter(puissance, 1, 10))

    premiere = random.choice(EFFETS_DEFORMATION)
    resultat = premiere(convertir_rgb(image_originale), puissance)
    utilises = {premiere.__name__}
    ordre = [premiere.__name__]

    exclusif = premiere.__name__ in DEFORMATIONS_EXCLUSIVES
    occultation = premiere.__name__ in OCCULTANTS
    destructeur = premiere.__name__ in DESTRUCTEURS
    style_dessin = premiere.__name__ in STYLES_DESSIN

    # Tous les effets disponibles sont placés dans le même pool.
    # Après mélange, chaque effet individuel a donc la même chance
    # d'être rencontré lors de la sélection.
    candidats = []

    if not exclusif:
        candidats += [
            e for e in EFFETS_DEFORMATION
            if e.__name__ not in DEFORMATIONS_EXCLUSIVES
            and e.__name__ not in PREMIERE_SEULEMENT
        ]

    candidats += EFFETS_COULEUR
    candidats += EFFETS_COMPLEMENTAIRES

    random.shuffle(candidats)

    # Maximum 2 effets de couleur.
    couleur_count = 0
    noms_couleur = {e.__name__ for e in EFFETS_COULEUR}

    for effet in candidats:
        if len(utilises) >= nombre_effets:
            break

        nom = effet.__name__

        # Évite de sélectionner deux fois le même effet.
        if nom in utilises:
            continue

        # Vérifie d'abord les incompatibilités, sans modifier les compteurs.
        if nom in OCCULTANTS and occultation:
            continue
        if nom in DESTRUCTEURS and destructeur:
            continue
        if nom in STYLES_DESSIN and style_dessin:
            continue
        if nom in noms_couleur and couleur_count >= 2:
            continue

        # L'effet est accepté : on met maintenant à jour les compteurs.
        if nom in OCCULTANTS:
            occultation = True
        if nom in DESTRUCTEURS:
            destructeur = True
        if nom in STYLES_DESSIN:
            style_dessin = True
        if nom in noms_couleur:
            couleur_count += 1

        resultat = effet(resultat, puissance)
        utilises.add(nom)
        ordre.append(nom)

    if retourner_noms:
        return resultat, ordre
    return resultat

def generer_indices(image_originale, etapes=4, nombre_effets=3,
                    puissance_max=10, graine=None):
    """
    Système d'indices : retourne `etapes` versions de la même affiche,
    de la plus déformée à la plus lisible (mêmes effets, puissance décroissante).
    La version originale n'est pas incluse : à ajouter à la fin si besoin.
    """
    if graine is None:
        graine = random.randrange(2 ** 31)
    versions = []
    for k in range(etapes):
        puissance = max(1, round(puissance_max * (etapes - k) / etapes))
        versions.append(
            transformer_image(image_originale, nombre_effets, puissance, graine=graine)
        )
    return versions


# ============================================================
# RECHERCHE DES AFFICHES
# ============================================================

def trouver_images():
    return sorted(
        f for f in DOSSIER_IMAGES.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONS
    )

