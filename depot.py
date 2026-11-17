"""Le dépôt Git du jeu (GitHub) : d'où viennent les mises à jour et les plans de Truman's Files.

Le dépôt se trouve tout seul :
  1. variable d'environnement TP_DEPOT (« compte/depot » : l'application Android la reçoit à sa construction) ;
  2. depot.json (à la racine du jeu) : {"github": "compte/depot"} ;
  3. sinon l'adresse « origin » du clone git (le raccourci du bureau lance toujours un clone à jour).
Les plans sont sur la branche « plans » du même dépôt (voir plans_distants.py) : une seule adresse à connaître.
"""
import json
import os
import re
import subprocess

DOSSIER = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(DOSSIER, "depot.json")
_INFOS = None


def _depuis_git():
    try:
        url = subprocess.run(["git", "-C", DOSSIER, "config", "--get", "remote.origin.url"], capture_output=True,
                             text=True, timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    m = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?\s*$", url.strip())
    return m.group(1) if m else ""


def infos():
    """{"github": "compte/depot" ou "", "branche": "main", "branche_plans": "plans"}"""
    global _INFOS
    if _INFOS is None:
        d = {}
        try:
            with open(FICHIER, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = {}
        github = (os.environ.get("TP_DEPOT") or d.get("github") or "").strip().strip("/")
        if not github or "/" not in github or github.startswith("COMPTE/"):
            github = _depuis_git()
        _INFOS = {"github": github, "branche": d.get("branche") or "main",
                  "branche_plans": d.get("branche_plans") or "plans"}
    return _INFOS


def url_brute(chemin, branche=None):
    """Adresse d'un fichier du dépôt (raw.githubusercontent.com) ; "" si le dépôt n'est pas connu."""
    i = infos()
    if not i["github"]:
        return ""
    from urllib.parse import quote
    return f"https://raw.githubusercontent.com/{i['github']}/{branche or i['branche']}/{quote(chemin)}"
