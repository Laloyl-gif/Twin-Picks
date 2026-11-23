"""Le palmarès à vie : pour chaque profil (ou pseudo), sur toutes les parties terminées : parties jouées, victoires,
points cumulés, record d'une partie, manches gagnées, plus longue série, jeu le plus payant. Consultable depuis le
menu (bouton « Palmarès »). Fichier : donnees/palmares.json."""
import json
import os
import threading
import time

from config import DOSSIER_DONNEES, JEUX
from texte import cle

FICHIER = os.path.join(DOSSIER_DONNEES, "palmares.json")
_verrou = threading.Lock()


def _lire():
    try:
        with open(FICHIER, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def enregistrer(recap, profils_joueurs):
    """recap : Partie.recap_fin() ; profils_joueurs : {id public: nom du profil ou pseudo}."""
    js = recap.get("joueurs") or []
    if not js or not recap.get("manches"):
        return
    meilleur = max(j["score"] for j in js)
    with _verrou:
        d = _lire()
        d.setdefault("joueurs", {})
        d["parties"] = d.get("parties", 0) + 1
        d["derniere"] = time.strftime("%Y-%m-%d %H:%M")
        for j in js:
            nom = profils_joueurs.get(j["id"]) or j["nom"]
            k = cle(nom) or nom
            p = d["joueurs"].setdefault(k, {"nom": nom, "parties": 0, "victoires": 0, "points": 0, "record": 0,
                                             "manches": 0, "serie": 0, "par_jeu": {}})
            p["nom"] = nom
            p["parties"] += 1
            p["victoires"] += 1 if j["score"] == meilleur and meilleur > 0 and len(js) > 1 else 0
            p["points"] += j["score"]
            p["record"] = max(p["record"], j["score"])
            p["manches"] += j.get("trouves", 0)
            p["serie"] = max(p["serie"], j.get("serie", 0))
            for jeu, pts in (j.get("par_jeu") or {}).items():
                p["par_jeu"][jeu] = p["par_jeu"].get(jeu, 0) + pts
        try:
            with open(FICHIER + ".tmp", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
            os.replace(FICHIER + ".tmp", FICHIER)
        except OSError:
            pass


def resume():
    """Le palmarès, prêt à afficher : les joueurs du plus titré au moins titré."""
    d = _lire()
    out = []
    for p in (d.get("joueurs") or {}).values():
        top = max((p.get("par_jeu") or {}).items(), key=lambda x: x[1], default=(None, 0))
        out.append({"nom": p["nom"], "parties": p["parties"], "victoires": p["victoires"], "points": p["points"],
                    "record": p["record"], "manches": p["manches"], "serie": p["serie"],
                    "moyenne": round(p["points"] / p["parties"]) if p["parties"] else 0,
                    "jeu": JEUX[top[0]]["nom"] if top[0] in JEUX and top[1] > 0 else ""})
    out.sort(key=lambda x: (-x["victoires"], -x["points"]))
    return {"joueurs": out, "parties": d.get("parties", 0), "derniere": d.get("derniere", "")}
