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


def icones(forcer=False):
    """Le raccourci du bureau garde son icône en cache, même quand web/icone.ico change. Quand l'icône change, on la
    copie sous un nouveau nom (donnees/icones/twin-picks-<empreinte>.ico) et on fait pointer les raccourcis dessus :
    Windows est obligé de la redessiner. Rien à faire si l'icône n'a pas changé."""
    import glob
    import hashlib
    windows = os.name == "nt"
    source = os.path.join(ICI, "web", "icone.ico" if windows else "icone.png")
    try:
        with open(source, "rb") as f:
            empreinte = hashlib.md5(f.read()).hexdigest()[:8]
    except OSError:
        return
    dossier = os.path.join(ICI, "donnees", "icones")
    os.makedirs(dossier, exist_ok=True)
    cible = os.path.join(dossier, f"twin-picks-{empreinte}{os.path.splitext(source)[1]}")
    if os.path.isfile(cible) and not forcer:
        return
    shutil.copyfile(source, cible)
    for vieux in glob.glob(os.path.join(dossier, "twin-picks-*")):
        if vieux != cible:
            try:
                os.remove(vieux)
            except OSError:
                pass
    if windows:
        echap = lambda t: t.replace("'", "''")                                          # noqa: E731
        ps = ("$w=New-Object -ComObject WScript.Shell;"
              "$d=@([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('CommonDesktopDirectory'),"
              "[Environment]::GetFolderPath('Programs'),[Environment]::GetFolderPath('CommonPrograms'));"
              "foreach($x in $d){$l=Join-Path $x 'Twin Picks.lnk';"
              f"if(Test-Path $l){{$s=$w.CreateShortcut($l);$s.IconLocation='{echap(cible)},0';$s.Save()}}}}")
        try:
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                           timeout=30, creationflags=SANS_FENETRE, capture_output=True)
            subprocess.run(["ie4uinit.exe", "-show"], timeout=15, creationflags=SANS_FENETRE, capture_output=True)
        except (OSError, subprocess.SubprocessError):
            pass
    else:                                                     # Linux : le raccourci .desktop du bureau
        for bureau in ("Desktop", "Bureau"):
            lien = os.path.join(os.path.expanduser("~"), bureau, "twin-picks.desktop")
            try:
                with open(lien, encoding="utf-8") as f:
                    lignes = f.read().splitlines()
                with open(lien, "w", encoding="utf-8") as f:
                    f.write("\n".join(f"Icon={cible}" if l.startswith("Icon=") else l for l in lignes) + "\n")
            except OSError:
                pass
    print("Icône du raccourci mise à jour.", flush=True)


if __name__ == "__main__":
    if "--icones" in sys.argv:                          # outils/mettre_a_jour_icones.bat
        icones(forcer=True)
        raise SystemExit(0)
    mettre_a_jour()
    modules()
    try:
        icones()
    except Exception:  # noqa: BLE001  (jamais bloquant : on joue quand même)
        pass
    sys.path.insert(0, ICI)
    import main                                         # après la mise à jour : toujours le code à jour
    main.main()
