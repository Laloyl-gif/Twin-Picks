#!/usr/bin/env python3
"""Met en ligne les plans rangés (outils/preparer_plans.py) sur la branche « plans » du dépôt GitHub du jeu.

    python outils/publier_plans.py  [dossier rangé ou .zip]   (par défaut : donnees/plans_tries/)
    (ou glisser le .zip des plans sur outils\publier_plans.bat)

Il faut que le jeu soit un clone git du dépôt (c'est le cas après installer.bat / installer.sh) et que git sache
pousser sur GitHub (identifiants enregistrés). Les plans ne sont jamais mêlés au code : la branche « plans » est à
part, l'application et les mises à jour ne téléchargent que ce qui sert.
"""
import os
import shutil
import subprocess
import sys

ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ICI)
import config  # noqa: E402
import depot  # noqa: E402


def git(*args, cwd=None, ok=False):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode and not ok:
        print(r.stdout + r.stderr)
        raise SystemExit(f"git {' '.join(args)} : échec")
    return r


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else os.path.join(config.DOSSIER_DONNEES, "plans_tries")
    if os.path.isfile(source) and source.lower().endswith(".zip"):            # le zip des plans rangés
        import tempfile
        import zipfile
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(source) as z:
            z.extractall(tmp)
        source = tmp
        for racine, _, fichiers in os.walk(tmp):
            if "index.json" in fichiers:
                source = racine
                break
    if not os.path.isfile(os.path.join(source, "index.json")):
        raise SystemExit(f"Pas d'index.json dans {source} : lancez d'abord outils/preparer_plans.py")
    url = git("config", "--get", "remote.origin.url", cwd=ICI).stdout.strip()
    branche = depot.infos()["branche_plans"]
    travail = os.path.join(config.DOSSIER_DONNEES, "_plans_git")
    if not os.path.isdir(os.path.join(travail, ".git")):
        shutil.rmtree(travail, ignore_errors=True)
        if git("clone", "--branch", branche, "--single-branch", url, travail, ok=True).returncode:
            os.makedirs(travail, exist_ok=True)                       # première fois : branche vide, à part
            git("init", cwd=travail)
            git("checkout", "--orphan", branche, cwd=travail)
            git("remote", "add", "origin", url, cwd=travail)
    else:
        git("pull", "--ff-only", "origin", branche, cwd=travail, ok=True)
    for nom in os.listdir(travail):                                   # on remplace tout par la version rangée
        if nom != ".git":
            chemin = os.path.join(travail, nom)
            shutil.rmtree(chemin) if os.path.isdir(chemin) else os.remove(chemin)
    for nom in os.listdir(source):
        a, b = os.path.join(source, nom), os.path.join(travail, nom)
        shutil.copytree(a, b) if os.path.isdir(a) else shutil.copyfile(a, b)
    git("add", "-A", cwd=travail)
    if git("diff", "--cached", "--quiet", cwd=travail, ok=True).returncode == 0:
        print("Rien de nouveau à publier.")
        return
    git("commit", "-m", "Plans de Truman's Files", cwd=travail)
    git("push", "-u", "origin", branche, cwd=travail)
    print("Plans en ligne : le jeu les trouvera tout seul (branche « %s »)." % branche)


if __name__ == "__main__":
    main()
