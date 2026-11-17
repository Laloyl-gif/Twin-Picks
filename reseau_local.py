"""Les parties du Wi-Fi : chaque jeu lancé (ordinateur ou téléphone) répond aux appels sur le réseau local, et
l'application Android cherche une partie avant d'en ouvrir une. Tout le monde sur le même Wi-Fi arrive donc dans la
même partie : celle de l'ordinateur s'il y en a un (il est toujours l'administrateur), sinon celle du premier
téléphone (qui devient l'administrateur)."""
import json
import socket
import threading
import time

PORT_RECHERCHE = 47474
QUESTION = b"TWINPICKS?"


def repondre(port_jeu, type_, nom=""):
    """En tâche de fond : répond « je suis une partie Twin Picks » aux appels du réseau local."""
    def boucle():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", PORT_RECHERCHE))
        except OSError:
            return                                       # déjà une partie sur cet appareil : elle répond pour nous
        rep = json.dumps({"jeu": "twinpicks", "port": port_jeu, "type": type_,
                          "nom": nom or socket.gethostname(), "debut": time.time()}).encode()
        while True:
            try:
                data, adr = s.recvfrom(256)
                if data.startswith(QUESTION):
                    s.sendto(rep, adr)
            except OSError:
                time.sleep(0.5)
    threading.Thread(target=boucle, daemon=True).start()


def _diffusions():
    adresses = {"255.255.255.255"}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        adresses.add(".".join(ip.split(".")[:3]) + ".255")       # réseau /24 (le cas des box)
    except OSError:
        pass
    return adresses


def chercher(delai=1.6):
    """Les parties du Wi-Fi : [{"ip", "port", "type", "nom"}], les ordinateurs d'abord, puis la plus ancienne."""
    trouvees = {}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(0.25)
    except OSError:
        return []
    fin = time.time() + delai
    prochain = 0
    while time.time() < fin:
        if time.time() >= prochain:                      # on répète l'appel (un paquet peut se perdre en Wi-Fi)
            for a in _diffusions():
                try:
                    s.sendto(QUESTION, (a, PORT_RECHERCHE))
                except OSError:
                    pass
            prochain = time.time() + 0.5
        try:
            data, (ip, _) = s.recvfrom(1024)
            d = json.loads(data.decode())
            if d.get("jeu") == "twinpicks":
                trouvees[(ip, d["port"])] = dict(d, ip=ip)
        except (OSError, ValueError, KeyError):
            continue
    s.close()
    return sorted(trouvees.values(), key=lambda d: (d.get("type") != "ordinateur", d.get("debut", 0)))
