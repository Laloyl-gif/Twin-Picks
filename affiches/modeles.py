"""Téléchargement des modèles (une seule fois) dans le dossier modeles/ du jeu.

Le téléchargement reprend là où il s'était arrêté (fichier .part) ; le fichier final n'apparaît qu'une fois
complet. Si le téléchargement est désactivé ou impossible, l'outil suivant de la liste est utilisé.
"""
import os
import threading

import requests

from . import reglages

_VERROU = threading.Lock()


class OutilManquant(RuntimeError):
    """Outil ou modèle indisponible pour une étape : ce n'est pas la faute du film traité (pas compté en échec)."""


def dossier():
    r = reglages.charger()["modeles"]
    d = reglages.chemin(r["dossier"])
    os.makedirs(d, exist_ok=True)
    return d


def obtenir(url, nom, journal=print):
    """Chemin local du modèle (téléchargé si besoin). Lève RuntimeError si indisponible."""
    chemin = os.path.join(dossier(), nom)
    if os.path.isfile(chemin) and os.path.getsize(chemin) > 0:
        return chemin
    if not reglages.charger()["modeles"]["telechargement_auto"]:
        raise OutilManquant(f"modèle {nom} absent (téléchargement automatique désactivé dans affiches/config.json)")
    with _VERROU:
        if os.path.isfile(chemin):
            return chemin
        part = chemin + ".part"
        deja = os.path.getsize(part) if os.path.isfile(part) else 0
        entetes = {"Range": f"bytes={deja}-"} if deja else {}
        journal(f"Téléchargement du modèle {nom}…")
        try:
            with requests.get(url, headers=entetes, stream=True, timeout=30) as r:
                if r.status_code == 416:             # déjà complet
                    os.replace(part, chemin)
                    return chemin
                r.raise_for_status()
                mode = "ab" if deja and r.status_code == 206 else "wb"
                with open(part, mode) as f:
                    for bloc in r.iter_content(1 << 20):
                        f.write(bloc)
        except requests.RequestException as err:
            raise OutilManquant(f"téléchargement du modèle {nom} impossible : {err}") from err
        os.replace(part, chemin)
        journal(f"Modèle {nom} prêt.")
        return chemin
