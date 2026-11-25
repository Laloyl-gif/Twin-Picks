"""Le palmarès à vie : pour chaque profil (ou pseudo), sur toutes les parties terminées : parties jouées, victoires,
points cumulés, record d'une partie, manches gagnées, plus longue série, jeu le plus payant, succès débloqués et
films « signature » (trouvés quand personne d'autre ne les a trouvés). Et pour toute la bande : les films qui ont le
plus résisté. Consultable depuis le menu (bouton « Palmarès »). Fichier : donnees/palmares.json."""
import json
import os
import threading
import time

from config import DOSSIER_DONNEES, JEUX
from texte import cle

FICHIER = os.path.join(DOSSIER_DONNEES, "palmares.json")
_verrou = threading.Lock()

# Les succès : (identifiant, nom, ce qu'il faut faire). Débloqués une fois pour toutes, à la fin d'une partie.
SUCCES = [
    ("cafe", "Damn fine coffee", "Gagner sa première partie"),
    ("agent", "Agent spécial", "Gagner 10 parties"),
    ("fidele", "Habitué du Double R", "Jouer 10 parties"),
    ("marathon", "Twin Peaks, 25 ans plus tard", "Jouer 25 parties"),
    ("sans_faute", "Sans faute", "Gagner toutes les manches d'une partie (5 manches au moins)"),
    ("eclair", "Plus rapide que BOB", "Être le premier à trouver 5 fois dans une même partie"),
    ("serie", "En feu", "Gagner 5 manches d'affilée"),
    ("remontada", "Le retour de Cooper", "Gagner une partie en étant dernier à la mi-partie"),
    ("photo", "Photo finish", "Gagner une partie avec moins de 150 points d'avance"),
    ("chelem", "Le grand chelem", "Marquer 10 000 points dans une partie"),
    ("chouette", "Les chouettes ne sont pas ce qu'elles semblent", "Trouver 10 films que personne d'autre n'a trouvés"),
    ("cinephile", "Cinéphile", "Gagner 100 manches en tout"),
    ("touche", "Touche-à-tout", "Marquer des points dans 15 jeux différents"),
    ("specialiste", "Spécialiste", "Cumuler 10 000 points dans un même jeu"),
]
NOMS_SUCCES = {k: (n, d) for k, n, d in SUCCES}


def _lire():
    try:
        with open(FICHIER, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _remontada(manches, jid, ids):
    """Dernier à la mi-partie (scores cumulés), premier à la fin ?"""
    if len(manches) < 4 or len(ids) < 2:
        return False
    mi = len(manches) // 2
    cumul = {i: 0 for i in ids}
    for r in manches[:mi]:
        for i, g in (r.get("gains") or {}).items():
            if i in cumul:
                cumul[i] += g
    bas = min(cumul.values())
    return cumul[jid] == bas and sum(1 for v in cumul.values() if v == bas) == 1


def _serie_max(manches, jid):
    n = best = 0
    for r in manches:
        n = n + 1 if jid in (r.get("trouves") or []) else 0
        best = max(best, n)
    return best


def enregistrer(recap, profils_joueurs, manches=None):
    """recap : Partie.recap_fin() ; profils_joueurs : {id public: nom du profil ou pseudo} ;
    manches : [{jeu, solution, type, gains: {id public: points}, trouves: [id public], premier: id public}].
    Retourne les succès débloqués par cette partie : {id public: [{id, nom, desc}]}."""
    js = recap.get("joueurs") or []
    manches = manches or []
    if not js or not recap.get("manches"):
        return {}
    meilleur = max(j["score"] for j in js)
    second = sorted((j["score"] for j in js), reverse=True)[1] if len(js) > 1 else 0
    ids = [j["id"] for j in js]
    nouveaux = {}
    with _verrou:
        d = _lire()
        d.setdefault("joueurs", {})
        films = d.setdefault("films", {})
        d["parties"] = d.get("parties", 0) + 1
        d["derniere"] = time.strftime("%Y-%m-%d %H:%M")
        for r in manches:                                  # les films de la partie, pour toute la bande
            sol = str(r.get("solution") or "").strip() if r.get("type") == "titre" else ""
            if not sol or len(sol) > 80:
                continue
            f = films.setdefault(sol, {"joues": 0, "rates": 0})
            f["joues"] += 1
            f["rates"] += 0 if r.get("trouves") else 1
        for j in js:
            nom = profils_joueurs.get(j["id"]) or j["nom"]
            k = cle(nom) or nom
            p = d["joueurs"].setdefault(k, {"nom": nom, "parties": 0, "victoires": 0, "points": 0, "record": 0,
                                             "manches": 0, "serie": 0, "par_jeu": {}})
            for champ, defaut in (("succes", {}), ("signature", []), ("solos", 0)):
                p.setdefault(champ, defaut)
            gagne = j["score"] == meilleur and meilleur > 0 and len(js) > 1
            p["nom"] = nom
            p["parties"] += 1
            p["victoires"] += 1 if gagne else 0
            p["points"] += j["score"]
            p["record"] = max(p["record"], j["score"])
            p["manches"] += j.get("trouves", 0)
            p["serie"] = max(p["serie"], j.get("serie", 0), _serie_max(manches, j["id"]))
            for jeu, pts in (j.get("par_jeu") or {}).items():
                p["par_jeu"][jeu] = p["par_jeu"].get(jeu, 0) + pts
            solos = [r for r in manches if r.get("trouves") == [j["id"]] and len(js) > 1 and r.get("solution")
                     and r.get("type") == "titre"]
            p["solos"] += len(solos)
            for r in solos:                                # films « signature » : trouvés seul contre tous
                s = str(r["solution"])[:80]
                if s in p["signature"]:
                    p["signature"].remove(s)
                p["signature"].insert(0, s)
            p["signature"] = p["signature"][:12]
            # les succès
            n_manches = len(manches)
            premiers = sum(1 for r in manches if r.get("premier") == j["id"])
            ok = {
                "cafe": p["victoires"] >= 1, "agent": p["victoires"] >= 10,
                "fidele": p["parties"] >= 10, "marathon": p["parties"] >= 25,
                "sans_faute": n_manches >= 5 and j.get("trouves", 0) >= n_manches,
                "eclair": premiers >= 5, "serie": p["serie"] >= 5,
                "remontada": gagne and _remontada(manches, j["id"], ids),
                "photo": gagne and meilleur - second < 150,
                "chelem": j["score"] >= 10000, "chouette": p["solos"] >= 10,
                "cinephile": p["manches"] >= 100,
                "touche": sum(1 for v in p["par_jeu"].values() if v > 0) >= 15,
                "specialiste": any(v >= 10000 for v in p["par_jeu"].values()),
            }
            for s, atteint in ok.items():
                if atteint and s not in p["succes"]:
                    p["succes"][s] = time.strftime("%Y-%m-%d")
                    nom_s, desc = NOMS_SUCCES[s]
                    nouveaux.setdefault(j["id"], []).append({"id": s, "nom": nom_s, "desc": desc})
        try:
            with open(FICHIER + ".tmp", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
            os.replace(FICHIER + ".tmp", FICHIER)
        except OSError:
            pass
    return nouveaux


def resume():
    """Le palmarès, prêt à afficher : les joueurs du plus titré au moins titré, leurs succès et films signature,
    et les films qui ont le plus résisté à la bande."""
    d = _lire()
    out = []
    for p in (d.get("joueurs") or {}).values():
        top = max((p.get("par_jeu") or {}).items(), key=lambda x: x[1], default=(None, 0))
        out.append({"nom": p["nom"], "parties": p["parties"], "victoires": p["victoires"], "points": p["points"],
                    "record": p["record"], "manches": p["manches"], "serie": p["serie"],
                    "moyenne": round(p["points"] / p["parties"]) if p["parties"] else 0,
                    "jeu": JEUX[top[0]]["nom"] if top[0] in JEUX and top[1] > 0 else "",
                    "succes": [{"id": s, "nom": NOMS_SUCCES[s][0], "desc": NOMS_SUCCES[s][1], "date": date}
                               for s, date in (p.get("succes") or {}).items() if s in NOMS_SUCCES],
                    "signature": (p.get("signature") or [])[:5], "solos": p.get("solos", 0)})
    out.sort(key=lambda x: (-x["victoires"], -x["points"]))
    films = d.get("films") or {}
    rates = sorted(((t, f) for t, f in films.items() if f.get("rates")),
                   key=lambda x: (-x[1]["rates"], -x[1]["rates"] / max(1, x[1]["joues"]), x[0]))[:10]
    joues = sorted(((t, f) for t, f in films.items() if f.get("joues", 0) > 1), key=lambda x: -x[1]["joues"])[:6]
    return {"joueurs": out, "parties": d.get("parties", 0), "derniere": d.get("derniere", ""),
            "succes": [{"id": k, "nom": n, "desc": de} for k, n, de in SUCCES],
            "rates": [{"titre": t, "rates": f["rates"], "joues": f["joues"]} for t, f in rates],
            "revenants": [{"titre": t, "joues": f["joues"]} for t, f in joues]}
