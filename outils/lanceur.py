#!/usr/bin/env python3
"""Lancement depuis le raccourci du bureau : met le jeu à jour (git pull), installe les modules Python si la liste a
changé, puis lance le jeu. Tout se passe ici (et pas dans lancer.bat) : la mise à jour peut remplacer lancer.bat
pendant qu'il tourne sans rien casser."""
import filecmp
import os
import shutil
import subprocess
import sys

ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ICI)
SANS_FENETRE = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ICI, capture_output=True, text=True, timeout=60,
                              creationflags=SANS_FENETRE).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def mettre_a_jour():
    if not os.path.isdir(os.path.join(ICI, ".git")):
        return
    print("Mise à jour…", flush=True)
    # seulement le code (branche main) : les plans (branche « plans ») sont lus en ligne, image par image
    git("config", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
    if git("pull", "--ff-only", "--quiet", "origin", "main"):
        return
    if git("fetch", "--quiet", "origin"):                 # historique divergent : la version en ligne gagne
        branche = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ICI, capture_output=True,
                                 text=True, creationflags=SANS_FENETRE).stdout.strip() or "main"
        git("reset", "--hard", "--quiet", f"origin/{branche}")
    else:
        print("Hors ligne : on joue avec la version déjà installée.", flush=True)


def modules():
    req, fait = os.path.join(ICI, "requirements.txt"), os.path.join(ICI, "donnees", "requirements.installe")
    os.makedirs(os.path.dirname(fait), exist_ok=True)
    if os.path.isfile(fait) and filecmp.cmp(req, fait, shallow=False):
        return
    print("Installation des modules Python…", flush=True)
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-r", req])
    if r.returncode == 0:
        shutil.copyfile(req, fait)


if __name__ == "__main__":
    mettre_a_jour()
    modules()
    sys.path.insert(0, ICI)
    import main                                         # après la mise à jour : toujours le code à jour
    main.main()
