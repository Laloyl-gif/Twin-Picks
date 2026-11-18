"""Réseau : adresse locale, QR code, tunnel Internet (cloudflared ou ngrok) et code de la partie.

Code de la partie : chaque partie a un code court (« KXT4P »), affiché en grand. Le jeu publie, sous ce code, ses
adresses (Wi-Fi et Internet) sur un relais public gratuit sans compte (ntfy.sh). Un joueur qui tape le code, d'où
qu'il soit, retrouve ainsi la partie : par le Wi-Fi s'il est sur le même, sinon par Internet (tunnel cloudflared,
téléchargé tout seul la première fois s'il manque)."""
import io
import json
import os
import platform
import random
import re
import shutil
import socket
import subprocess
import threading
import time

try:
    import qrcode
except ImportError:
    qrcode = None

MSG_TUNNEL = ("Le mode Internet nécessite un outil de tunnel gratuit :\n"
              "- cloudflared (recommandé, sans compte) : winget install Cloudflare.cloudflared\n"
              "  puis relancez le quiz ;\n"
              "- ou ngrok : pip install pyngrok (et configurez votre jeton ngrok).\n"
              "Sans cela, seuls les téléphones du même Wi-Fi peuvent rejoindre.")


def ip_locale():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def qr_png(url):
    if qrcode is None:
        return None
    qr = qrcode.QRCode(border=2, box_size=10)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = getattr(img, "get_image", lambda: img)()
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"            # sans 0/O ni 1/I : faciles à lire et à taper
RELAIS = "https://ntfy.sh/twinpicks-partie-"


def nouveau_code(n=5):
    return "".join(random.choice(ALPHABET) for _ in range(n))


def normaliser_code(code):
    return "".join(c for c in str(code).upper().replace("0", "O").replace("1", "I") if c in ALPHABET)[:8]


def publier_salle(code, infos):
    """Publie les adresses de la partie sous son code (gardées 12 h par le relais)."""
    import requests
    requests.post(RELAIS + code, data=json.dumps(infos).encode(), timeout=8,
                  headers={"Title": "Twin Picks", "Cache": "yes"}).raise_for_status()


def resoudre_salle(code):
    """Les dernières adresses publiées sous ce code : {"lan", "net", "nom"} ou None."""
    import requests
    code = normaliser_code(code)
    if len(code) < 4:
        return None
    r = requests.get(RELAIS + code + "/json", params={"poll": "1", "since": "12h"}, timeout=8)
    r.raise_for_status()
    dernier = None
    for ligne in r.text.splitlines():
        try:
            m = json.loads(ligne)
        except ValueError:
            continue
        if m.get("event") == "message":
            try:
                dernier = json.loads(m.get("message") or "")
            except ValueError:
                pass
    return dernier


def chemin_cloudflared(telecharger=True):
    """cloudflared : installé, fourni par l'application Android (TP_CLOUDFLARED), ou téléchargé une fois depuis les
    versions officielles de Cloudflare dans donnees/outils/."""
    exe = os.environ.get("TP_CLOUDFLARED") or shutil.which("cloudflared")
    if exe and os.path.isfile(exe):
        return exe
    import config
    systeme, archi = platform.system(), platform.machine().lower()
    arch = "arm64" if archi in ("arm64", "aarch64") else "amd64"
    noms = {"Windows": f"cloudflared-windows-{arch}.exe", "Linux": f"cloudflared-linux-{arch}",
            "Darwin": f"cloudflared-darwin-{arch}.tgz"}
    if systeme not in noms:
        return None
    dossier = os.path.join(config.DOSSIER_DONNEES, "outils")
    local = os.path.join(dossier, "cloudflared.exe" if systeme == "Windows" else "cloudflared")
    if os.path.isfile(local):
        return local
    if not telecharger:
        return None
    import requests
    os.makedirs(dossier, exist_ok=True)
    r = requests.get("https://github.com/cloudflare/cloudflared/releases/latest/download/" + noms[systeme], timeout=120)
    r.raise_for_status()
    if noms[systeme].endswith(".tgz"):
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(r.content)) as t:
            membre = next(m for m in t.getmembers() if m.name.endswith("cloudflared"))
            with open(local, "wb") as f:
                f.write(t.extractfile(membre).read())
    else:
        with open(local, "wb") as f:
            f.write(r.content)
    os.chmod(local, 0o755)
    return local


class Tunnel:
    def __init__(self, port):
        self.port, self.proc, self.ngrok, self.url = port, None, False, None

    def demarrer(self):
        try:
            exe = chemin_cloudflared()
        except Exception:  # noqa: BLE001  (pas d'Internet pour le télécharger)
            exe = None
        if exe:
            return self._cloudflared(exe)
        try:
            from pyngrok import ngrok
        except ImportError:
            raise RuntimeError(MSG_TUNNEL)
        try:
            tunnel = ngrok.connect(self.port, "http")
        except Exception as err:  # noqa: BLE001
            raise RuntimeError(f"ngrok n'a pas pu démarrer : {err}")
        self.ngrok = True
        self.url = tunnel.public_url.replace("http://", "https://")
        return self.url

    def _cloudflared(self, exe):
        self.proc = subprocess.Popen(
            [exe, "tunnel", "--url", f"http://127.0.0.1:{self.port}", "--no-autoupdate"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        proc, trouve = self.proc, []

        def lire():
            for ligne in proc.stdout:
                if trouve:
                    continue
                for m in re.finditer(r"https://[a-z0-9-]+\.trycloudflare\.com", ligne):
                    if m.group() != "https://api.trycloudflare.com":
                        trouve.append(m.group())
                        break

        threading.Thread(target=lire, daemon=True).start()
        fin = time.monotonic() + 40
        while not trouve and time.monotonic() < fin and proc.poll() is None:
            time.sleep(0.2)
        if not trouve:
            self.arreter()
            raise RuntimeError("cloudflared n'a pas fourni d'adresse publique. Vérifiez votre connexion.")
        self.url = trouve[0]
        return self.url

    def arreter(self):
        proc, self.proc = self.proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        if self.ngrok:
            try:
                from pyngrok import ngrok
                ngrok.kill()
            except Exception:  # noqa: BLE001
                pass
            self.ngrok = False
        self.url = None
