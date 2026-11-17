#!/usr/bin/env python3
"""Range des plans de film en trois niveaux de difficulté, prêts à être mis en ligne (branche « plans » du dépôt).

    python outils/preparer_plans.py  <dossier ou fichier .zip>  [dossier de sortie]

Entrée : un dossier par film (« Alien (1979) [tmdb-348] », ou simplement « Alien (1979) »), avec ses images :
  - déjà rangées dans 1_difficile/ 2_moyen/ 3_facile/ : gardées telles quelles ;
  - numérotées (01.jpg, 02.jpg… du plus difficile au plus facile) : coupées en trois tranches ;
  - sinon : la difficulté de chaque image est estimée (gros plans, visages, couleurs…), puis coupée en trois.
Les images sont réduites (1280 px de large au plus) pour garder un dépôt léger. Sortie (par défaut
donnees/plans_tries/) : les dossiers rangés et index.json. Ensuite : python outils/publier_plans.py
"""
import json
import os
import shutil
import sys
import tempfile
import zipfile

ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ICI)

from PIL import Image  # noqa: E402

import config  # noqa: E402
import images_film as imf  # noqa: E402
from plans_distants import IMAGES, NIVEAUX, ranger  # noqa: E402

LARGEUR = 1280


def films(racine):
    """Les dossiers de film : ceux qui contiennent des images (directement ou dans leurs dossiers de niveau)."""
    for dossier, sous, fichiers in os.walk(racine):
        sous[:] = sorted(d for d in sous if not d.startswith((".", "__MACOSX")))
        if os.path.basename(dossier) in NIVEAUX:
            continue
        a_images = any(os.path.splitext(f)[1].lower() in IMAGES for f in fichiers)
        a_niveaux = any(d in NIVEAUX for d in sous)
        if a_images or a_niveaux:
            sous[:] = [d for d in sous if d in NIVEAUX] if a_niveaux else []
            yield dossier


def images_de(dossier):
    out = []
    for racine, _, fs in os.walk(dossier):
        rel = os.path.relpath(racine, dossier)
        for f in sorted(fs):
            if os.path.splitext(f)[1].lower() in IMAGES:
                out.append(f if rel == "." else f"{rel.replace(os.sep, '/')}/{f}")
    return out


def niveaux(dossier):
    fichiers = images_de(dossier)
    rangees = ranger(fichiers) if all(f[:1].isdigit() or "/" in f for f in fichiers) else None
    if rangees:
        return rangees
    if len(fichiers) < 3:
        return None
    ims = []
    for f in fichiers:
        try:
            ims.append((Image.open(os.path.join(dossier, *f.split("/"))).convert("RGB"), f))
        except OSError:
            pass
    notes = sorted(imf.noter(ims), key=lambda c: c[0])             # du plus difficile au plus facile
    ordre = [info for _, _, info in notes]
    if len(ordre) < 3:
        return None
    k = len(ordre)
    return {n: ordre[round(i * k / 3):round((i + 1) * k / 3)] for i, n in enumerate(NIVEAUX)}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    source = sys.argv[1]
    sortie = sys.argv[2] if len(sys.argv) > 2 else os.path.join(config.DOSSIER_DONNEES, "plans_tries")
    tmp = None
    if zipfile.is_zipfile(source):
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(source) as z:
            z.extractall(tmp)
        source = tmp
    os.makedirs(sortie, exist_ok=True)
    index = {"version": 1, "films": []}
    for dossier in films(source):
        nom = os.path.basename(dossier)
        nv = niveaux(dossier)
        if not nv:
            print("  ignoré (moins de 3 images) :", nom)
            continue
        entree = {"dossier": nom, "niveaux": {}}
        for n in NIVEAUX:
            liste = []
            for i, f in enumerate(nv[n], 1):
                try:
                    im = Image.open(os.path.join(dossier, *f.split("/"))).convert("RGB")
                except OSError:
                    continue
                if im.width > LARGEUR:
                    im = im.resize((LARGEUR, round(im.height * LARGEUR / im.width)), Image.LANCZOS)
                rel = f"{n}/{i:02d}.jpg"
                os.makedirs(os.path.join(sortie, nom, n), exist_ok=True)
                im.save(os.path.join(sortie, nom, *rel.split("/")), quality=86, optimize=True)
                liste.append(rel)
            entree["niveaux"][n] = liste
        if all(entree["niveaux"].values()):
            index["films"].append(entree)
            print(f"  {nom} : " + " / ".join(str(len(entree['niveaux'][n])) for n in NIVEAUX))
    with open(os.path.join(sortie, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(index['films'])} films rangés dans {sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
