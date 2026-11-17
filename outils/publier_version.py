#!/usr/bin/env python3
"""Publie une nouvelle version du jeu sur GitHub à partir du .zip reçu.

    python outils/publier_version.py  twin_picks_sans_plans.zip

Le code du clone est remplacé par celui du zip (sauf donnees/, plans/ et .git), puis git commit + push : tous les
ordinateurs (raccourci du bureau) et toutes les applications Android se mettent à jour au prochain lancement.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GARDER = {".git", "donnees", "plans", "affiches_pete", "modeles"}


def git(*args):
    r = subprocess.run(["git", *args], cwd=ICI)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)} : échec")


def main():
    if len(sys.argv) < 2 or not zipfile.is_zipfile(sys.argv[1]):
        raise SystemExit(__doc__)
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(sys.argv[1]) as z:
        z.extractall(tmp)
    racine = tmp
    while len(os.listdir(racine)) == 1 and os.path.isdir(os.path.join(racine, os.listdir(racine)[0])):
        racine = os.path.join(racine, os.listdir(racine)[0])            # le dossier twin_picks/ du zip
    if not os.path.isfile(os.path.join(racine, "main.py")):
        raise SystemExit("Ce zip ne contient pas le jeu (main.py introuvable).")
    for nom in os.listdir(ICI):
        if nom not in GARDER:
            chemin = os.path.join(ICI, nom)
            shutil.rmtree(chemin) if os.path.isdir(chemin) else os.remove(chemin)
    for nom in os.listdir(racine):
        if nom not in GARDER:
            a, b = os.path.join(racine, nom), os.path.join(ICI, nom)
            shutil.copytree(a, b) if os.path.isdir(a) else shutil.copyfile(a, b)
    shutil.rmtree(tmp, ignore_errors=True)
    git("add", "-A")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ICI).returncode == 0:
        print("Rien de nouveau.")
        return
    version = "nouvelle version"
    try:
        with open(os.path.join(ICI, "VERSION"), encoding="utf-8") as f:
            version = "version " + f.read().strip()
    except OSError:
        pass
    git("commit", "-m", f"Twin Picks : {version}")
    git("push")
    print("Publié : ordinateurs et téléphones se mettront à jour au prochain lancement.")


if __name__ == "__main__":
    main()
