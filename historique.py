"""L'historique des parties : les films joués lors des dernières parties, pour ne pas les ressortir tout de suite
(réglage « Écarter les films joués lors des dernières parties »). Quand une liste est trop courte, les jeux
reprennent quand même ces films (tirer() repart de zéro quand tout a été joué)."""
import json
import os
import threading
import time

from config import DOSSIER_DONNEES

FICHIER = os.path.join(DOSSIER_DONNEES, "historique.json")
GARDE = 30                                   # parties gardées au plus
_verrou = threading.Lock()


def _lire():
    try:
        with open(FICHIER, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def recents(n):
    """Les clés des films joués lors des n dernières parties."""
    with _verrou:
        parties = _lire()[-max(0, int(n)):] if n else []
    out = set()
    for p in parties:
        for k in p.get("films", []):
            if isinstance(k, list) and len(k) == 2:
                out.add((k[0], k[1]))
    return out


def ajouter(films):
    """Enregistre une partie (les clés de ses films)."""
    films = sorted({tuple(k) for k in films if isinstance(k, (list, tuple)) and len(k) == 2}, key=str)
    if not films:
        return
    with _verrou:
        parties = _lire()
        parties.append({"date": time.strftime("%Y-%m-%d %H:%M"), "films": [list(k) for k in films]})
        try:
            with open(FICHIER + ".tmp", "w", encoding="utf-8") as f:
                json.dump(parties[-GARDE:], f, ensure_ascii=False)
            os.replace(FICHIER + ".tmp", FICHIER)
        except OSError:
            pass
