#!/usr/bin/env python3
"""Twin Picks : lance le serveur et ouvre l'écran hôte dans le navigateur.

Installation : voir INSTALLATION.md (raccourci du bureau toujours à jour)   ou   pip install -r requirements.txt
Lancement    : python main.py
"""
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer

import config
import reseau_local
from serveur import App, fabriquer_handler


def demarrer_serveur(type_="ordinateur"):
    """Ouvre le serveur du jeu (sans le bloquer) : (app, port, serveur) ou None si aucun port n'est libre.
    type_ : « ordinateur » (l'écran hôte est l'administrateur) ou « telephone » (application Android)."""
    app = App(type_)
    serveur = None
    for port in range(config.PORT, config.PORT + 10):
        try:
            serveur = ThreadingHTTPServer(("0.0.0.0", port), fabriquer_handler(app))
            break
        except OSError:
            continue
    if serveur is None:
        return None
    app.definir_port(port)
    reseau_local.repondre(port, type_)                      # les téléphones du Wi-Fi trouvent cette partie
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    return app, port, serveur


def main():
    res = demarrer_serveur("ordinateur")
    if res is None:
        print("Impossible d'ouvrir un port reseau.")
        return
    app, port, serveur = res
    hote = f"http://localhost:{port}/hote?k={app.jeton}"
    print("Twin Picks")
    print("  Ecran hote : " + hote)
    print("  Telephones : " + app.url_locale + "   (ou l'application Twin Picks : elle trouve la partie toute seule)")
    print("  (Ctrl+C ou fermer cette fenetre pour quitter)")
    threading.Timer(0.8, webbrowser.open, args=(hote,)).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        app.tunnel.arreter()
        serveur.shutdown()
        serveur.server_close()


if __name__ == "__main__":
    main()
