"""Réseau : adresse locale, QR code et tunnel Internet (cloudflared ou ngrok)."""
import io
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


class Tunnel:
    def __init__(self, port):
        self.port, self.proc, self.ngrok, self.url = port, None, False, None

    def demarrer(self):
        exe = shutil.which("cloudflared")
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
