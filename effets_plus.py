"""Effets supplémentaires, ajoutés aux familles de effets.py (qui n'est pas modifié)."""
import math
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import effets
from effets import deformer_maillage, limiter


def effet_hexagones(image, puissance):
    """Pixelisation en nid d'abeille (couleur moyenne de chaque hexagone)."""
    largeur, hauteur = image.size
    r = max(5, int(largeur / limiter(48 - puissance * 3.5, 12, 48)))
    w, h = math.sqrt(3) * r, 1.5 * r
    sortie = Image.new("RGB", image.size)
    dessin = ImageDraw.Draw(sortie)
    y, ligne = 0.0, 0
    while y < hauteur + r:
        x = (w / 2 if ligne % 2 else 0) - w
        while x < largeur + w:
            boite = (max(0, int(x - w / 2)), max(0, int(y - r)), min(largeur, int(x + w / 2)), min(hauteur, int(y + r)))
            if boite[2] > boite[0] and boite[3] > boite[1]:
                couleur = image.crop(boite).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
                points = [(x + r * math.cos(math.radians(60 * k + 30)), y + r * math.sin(math.radians(60 * k + 30)))
                          for k in range(6)]
                dessin.polygon(points, fill=couleur)
            x += w
        y += h
        ligne += 1
    return sortie


def effet_fisheye(image, puissance):
    """Objectif fish-eye : le centre gonfle, les bords se compriment."""
    largeur, hauteur = image.size
    cx, cy = largeur / 2, hauteur / 2
    rmax = math.hypot(cx, cy)
    k = limiter(0.4 + puissance * 0.12, 0.4, 1.6)

    def f(x, y, _c=None):
        dx, dy = (x - cx) / rmax, (y - cy) / rmax
        r = math.hypot(dx, dy)
        if r == 0:
            return x, y
        fac = r ** k
        return cx + dx * fac * rmax, cy + dy * fac * rmax

    return deformer_maillage(image, f)


def effet_anneaux(image, puissance):
    """Anneaux concentriques tournés alternativement dans un sens puis dans l'autre."""
    largeur, hauteur = image.size
    cx, cy = largeur / 2, hauteur / 2
    rlim = min(cx, cy)
    n = int(limiter(4 + puissance // 2, 4, 9))
    angle = 6 + puissance * 3
    resultat = image.copy()
    for i in range(n):
        r = rlim * (1 - i / n)
        a = angle * (i + 1) * (1 if i % 2 == 0 else -1)
        masque = Image.new("L", image.size, 0)
        ImageDraw.Draw(masque).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        resultat.paste(image.rotate(a, resample=Image.Resampling.BICUBIC, center=(cx, cy)), mask=masque)
    return resultat


def effet_bandes_melangees(image, puissance):
    """L'affiche découpée en bandes remises dans le désordre."""
    largeur, hauteur = image.size
    n = int(limiter(4 + puissance, 5, 16))
    vertical = random.choice((True, False))
    cote = largeur if vertical else hauteur
    bords = [i * cote // n for i in range(n + 1)]
    ordre = list(range(n))
    while ordre == sorted(ordre):
        random.shuffle(ordre)
    resultat, pos = Image.new("RGB", image.size), 0
    for i in ordre:
        a, b = bords[i], bords[i + 1]
        boite = (a, 0, b, hauteur) if vertical else (0, a, largeur, b)
        resultat.paste(image.crop(boite), (pos, 0) if vertical else (0, pos))
        pos += b - a
    return resultat


def effet_serrure(image, puissance):
    """Vue par le trou d'une serrure."""
    largeur, hauteur = image.size
    r = min(largeur, hauteur) * max(0.10, 0.26 - puissance * 0.015)
    cx = random.uniform(r, largeur - r)
    cy = random.uniform(r, max(r, hauteur - 2.6 * r))
    masque = Image.new("L", image.size, 0)
    d = ImageDraw.Draw(masque)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    d.polygon([(cx - r * 0.45, cy), (cx + r * 0.45, cy), (cx + r * 0.9, cy + 2.4 * r), (cx - r * 0.9, cy + 2.4 * r)],
              fill=255)
    masque = masque.filter(ImageFilter.GaussianBlur(r * 0.05))
    return Image.composite(image, Image.new("RGB", image.size, (6, 6, 8)), masque)


def effet_vision_nocturne(image, puissance):
    """Caméra de vision nocturne : vert, grain et coins sombres."""
    gris = ImageEnhance.Brightness(ImageOps.autocontrast(ImageOps.grayscale(image))).enhance(1.2)
    vert = ImageOps.colorize(gris, black=(0, 15, 0), white=(170, 255, 140))
    bruit = Image.effect_noise(image.size, 30 + puissance * 4).convert("L")
    vert = Image.blend(vert, Image.merge("RGB", (bruit, bruit, bruit)), 0.12)
    return effets.effet_vignettage(vert, 4)


def effet_ombre_chinoise(image, puissance):
    """Silhouettes noires sur un dégradé tiré des couleurs de l'affiche."""
    gris = ImageOps.autocontrast(ImageOps.grayscale(image)).filter(ImageFilter.GaussianBlur(1))
    seuil = random.randint(70, 120)
    masque = gris.point(lambda p: 255 if p < seuil else 0)
    fond = image.resize((1, 2), Image.Resampling.BOX).resize(image.size, Image.Resampling.BILINEAR)
    fond = ImageEnhance.Brightness(ImageEnhance.Color(fond).enhance(2.2)).enhance(1.4)
    return Image.composite(Image.new("RGB", image.size, (8, 8, 12)), fond, masque)


def effet_pluie(image, puissance):
    """Pluie battante devant l'affiche."""
    largeur, hauteur = image.size
    calque = Image.new("L", image.size, 0)
    d = ImageDraw.Draw(calque)
    pente = random.uniform(0.15, 0.35) * random.choice((-1, 1))
    for _ in range(int((150 + puissance * 60) * largeur / 480)):
        x, y = random.uniform(0, largeur), random.uniform(0, hauteur)
        l = random.uniform(hauteur * 0.03, hauteur * 0.08)
        d.line((x, y, x + pente * l, y + l), fill=random.randint(120, 220), width=1)
    sombre = ImageEnhance.Brightness(image).enhance(0.8)
    return Image.composite(Image.new("RGB", image.size, (220, 225, 235)), sombre, calque)


effets.EFFETS_DEFORMATION += [effet_hexagones, effet_fisheye, effet_anneaux, effet_bandes_melangees, effet_serrure]
effets.EFFETS_COULEUR += [effet_vision_nocturne, effet_ombre_chinoise]
effets.EFFETS_COMPLEMENTAIRES += [effet_pluie]
effets.DESTRUCTEURS |= {"effet_hexagones"}
effets.OCCULTANTS |= {"effet_serrure"}
effets.STYLES_DESSIN |= {"effet_ombre_chinoise", "effet_vision_nocturne"}
