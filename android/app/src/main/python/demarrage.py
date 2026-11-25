"""Démarrage de l'application Android Twin Picks (appelé par MainActivity).

1. Mise à jour : la dernière version du jeu est téléchargée depuis le dépôt GitHub si elle a changé (le code est gardé
   dans le dossier de l'application : hors ligne, on rejoue la dernière version téléchargée).
2. Partie : on cherche une partie sur le Wi-Fi (celle de l'ordinateur d'abord) et on la rejoint ; sinon ce téléphone
   ouvre la partie et en devient l'administrateur.
Les réglages, profils et caches sont dans donnees/ : une mise à jour ne les efface jamais.
"""
import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile

MESSAGE = "Démarrage…"
_SERVEUR = None                     # l'adresse de la partie ouverte sur ce téléphone (une seule fois)


def message():
    return MESSAGE


def _dire(m):
    global MESSAGE
    MESSAGE = m


def _lire(url, delai):
    req = urllib.request.Request(url, headers={"User-Agent": "TwinPicks-Android"})
    with urllib.request.urlopen(req, timeout=delai) as r:
        return r.read()


def _derniere_version(depot):
    """Identifiant de la dernière version en ligne (le commit de main), ou None hors ligne."""
    try:
        return json.loads(_lire(f"https://api.github.com/repos/{depot}/commits/main", 8))["sha"]
    except Exception:  # noqa: BLE001  (limite de l'API GitHub, pas d'Internet…)
        pass
    try:
        return "v:" + _lire(f"https://raw.githubusercontent.com/{depot}/main/VERSION", 8).decode().strip()
    except Exception:  # noqa: BLE001
        return None


def mettre_a_jour(base, depot):
    code = os.path.join(base, "code")
    fichier = os.path.join(base, "version.json")
    try:
        with open(fichier, encoding="utf-8") as f:
            actuelle = json.load(f).get("version")
    except (OSError, ValueError):
        actuelle = None
    present = os.path.isfile(os.path.join(code, "main.py"))
    if not depot:
        if present:
            return code
        raise RuntimeError("Application construite sans adresse de dépôt : reconstruisez-la avec GitHub Actions.")
    _dire("Recherche de la dernière version…")
    version = _derniere_version(depot)
    if version is None:
        if present:
            _dire("Hors ligne : dernière version téléchargée")
            return code
        raise RuntimeError("Pas d'Internet : la première ouverture a besoin d'Internet pour télécharger le jeu.")
    if present and version == actuelle:
        return code
    _dire("Téléchargement de la dernière version…")
    ref = version if not version.startswith("v:") else "refs/heads/main"
    data = _lire(f"https://codeload.github.com/{depot}/zip/{ref}", 90)
    _dire("Installation de la nouvelle version…")
    tmp = code + ".nouveau"
    shutil.rmtree(tmp, ignore_errors=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(tmp)
    dossiers = [d for d in os.listdir(tmp) if os.path.isdir(os.path.join(tmp, d))]
    racine = os.path.join(tmp, dossiers[0]) if len(dossiers) == 1 else tmp
    shutil.rmtree(code, ignore_errors=True)
    shutil.move(racine, code)
    shutil.rmtree(tmp, ignore_errors=True)
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump({"version": version}, f)
    return code


def nouvelle_appli(depot, numero):
    """L'adresse de la nouvelle application (APK) si GitHub en a construit une plus récente que celle-ci, sinon « ».
    Le jeu se met à jour tout seul, mais l'application elle-même (son icône…) doit être réinstallée."""
    if not depot:
        return ""
    base = f"https://github.com/{depot}/releases/download/application"
    try:
        en_ligne = int(_lire(f"{base}/version.txt", 6).decode().strip())
    except Exception:  # noqa: BLE001  (hors ligne, pas encore publiée…)
        return ""
    return f"{base}/twin-picks.apk" if en_ligne > int(numero) else ""


def demarrer(base, depot, libs=""):
    """L'adresse de la page à ouvrir : une partie du Wi-Fi, ou celle ouverte ici (avec la clé d'administrateur)."""
    if _SERVEUR:
        return _SERVEUR
    os.environ["TP_DONNEES"] = os.path.join(base, "donnees")
    os.environ["TP_DEPOT"] = depot or ""
    cf = os.path.join(libs or "", "libcloudflared.so")
    if libs and os.path.isfile(cf):                     # tunnel Internet (code de la partie hors du Wi-Fi)
        os.environ["TP_CLOUDFLARED"] = cf
    code = mettre_a_jour(base, depot)
    if code not in sys.path:
        sys.path.insert(0, code)
    os.chdir(code)
    _dire("Recherche d'une partie sur le Wi-Fi…")
    import reseau_local
    parties = reseau_local.chercher(2.0)
    if parties:
        p = parties[0]
        _dire(f"Partie trouvée : {p.get('nom', '')}")
        return f"http://{p['ip']}:{p['port']}/"
    return ouvrir_partie()


# ---------- l'hôte s'éteint : la partie continue sur un téléphone ----------
_VEILLE = {"url": "", "snap": None, "v": "", "echecs": 0, "bascule": "", "actif": False}


def _mon_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return ""


def veiller(url):
    """Pendant qu'on joue dans la partie d'un autre appareil : on garde sa dernière sauvegarde. S'il ne répond plus,
    on cherche si un autre téléphone a déjà repris la partie (même code) ; sinon, chacun son tour (ordre d'arrivée
    dans la partie), ce téléphone la reprend lui-même. bascule() dit alors à l'application où aller."""
    import threading
    import time
    if _VEILLE["actif"] or not url or "127.0.0.1" in url:
        return
    _VEILLE.update(url=url.rstrip("/"), actif=True, snap=None, v="", echecs=0, bascule="")

    def boucle():
        while _VEILLE["actif"] and not _VEILLE["bascule"]:
            time.sleep(4)
            try:
                d = json.loads(_lire(f"{_VEILLE['url']}/api/reprise?v={_VEILLE['v']}", 4))
                _VEILLE["echecs"] = 0
                if d.get("snap"):
                    _VEILLE["snap"], _VEILLE["v"] = d["snap"], d.get("v", "")
                elif d.get("aucune"):
                    _VEILLE["snap"], _VEILLE["v"] = None, ""
                continue
            except Exception:  # noqa: BLE001  (l'hôte ne répond plus… ou un raté du Wi-Fi)
                _VEILLE["echecs"] += 1
            snap = _VEILLE["snap"]
            if _VEILLE["echecs"] < 3 or not snap:
                continue
            try:
                _relayer(snap)
            except Exception:  # noqa: BLE001
                pass
    threading.Thread(target=boucle, daemon=True).start()


def _relayer(snap):
    import time
    import reseau_local
    moi = f"http://{_mon_ip()}:"
    relais = [r for r in snap.get("relais", [])]
    rang = next((i for i, r in enumerate(relais) if r.startswith(moi)), len(relais))
    fin = time.time() + 6 * rang + 1
    while True:                                   # quelqu'un a-t-il déjà repris la partie (même code) ?
        for p in reseau_local.chercher(1.5):
            if p.get("code") == snap.get("code"):
                _VEILLE["bascule"] = f"http://{p['ip']}:{p['port']}/"
                return
        if time.time() >= fin:
            break
    try:                                          # l'ancien hôte est revenu ?
        _lire(f"{_VEILLE['url']}/api/salle", 3)
        _VEILLE["echecs"] = 0
        return
    except Exception:  # noqa: BLE001
        pass
    _VEILLE["bascule"] = ouvrir_partie(snap)


def bascule():
    """L'adresse où l'application doit aller (la partie a changé d'hôte), une seule fois ; sinon « »."""
    b = _VEILLE["bascule"]
    if b:
        _VEILLE["bascule"], _VEILLE["actif"] = "", False
    return b or ""


def ouvrir_partie(reprise=None):
    global _SERVEUR
    if _SERVEUR:
        return _SERVEUR
    _dire("Reprise de la partie…" if reprise else "Ouverture d'une nouvelle partie…")
    import main
    res = main.demarrer_serveur("telephone", reprise)
    if res is None:
        raise RuntimeError("Impossible d'ouvrir la partie (port réseau occupé).")
    app, port, _ = res
    _SERVEUR = f"http://127.0.0.1:{port}/?admin={app.jeton}"
    return _SERVEUR
