"""Windom Earle's Chessboard (L'échiquier) : Windom Earle joue sa partie d'échecs, et chaque pièce qu'il avance est un
membre de l'équipe d'un film. D'abord les pions (des seconds rôles), puis le cavalier (le directeur de la photo), la
tour (le compositeur), le fou (le scénariste), la dame (la tête d'affiche) et enfin le roi (le réalisateur).
Trouvez le film. Indices (réglables) : l'année, puis le titre à trous.
"""
import random

from texte import normaliser
from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

# (pièce, symbole, métier) dans l'ordre où Windom les avance
PIECES = [("Pion", "♟", "Second rôle"), ("Pion", "♟", "Second rôle"), ("Pion", "♟", "Second rôle"),
          ("Cavalier", "♞", "Directeur de la photo"), ("Tour", "♜", "Compositeur"), ("Fou", "♝", "Scénariste"),
          ("Dame", "♛", "Tête d'affiche"), ("Roi", "♚", "Réalisateur")]
CASES = ["c2", "e2", "g2", "b1", "h1", "f1", "d1", "e1"]          # où se pose chaque pièce sur l'échiquier


def equipe(fi):
    """[(pièce, symbole, métier, nom, rôle)] ; les pièces sans personne connue sont retirées."""
    acteurs = [a for a in fi.get("acteurs", []) if a.get("nom")]
    reals = [r["nom"] for r in fi.get("realisateurs", [])]
    pris = set(reals)
    out = []

    def poser(k, nom, role=""):
        if nom and nom not in pris:
            pris.add(nom)
            p, sym, metier = PIECES[k]
            out.append(dict(piece=p, sym=sym, metier=metier, nom=nom, role=role, case=CASES[k]))
    seconds = acteurs[3:9]
    random.shuffle(seconds)
    for k in range(3):
        if k < len(seconds):
            poser(k, seconds[k]["nom"], seconds[k].get("role", ""))
    poser(3, next(iter(c["nom"] for c in fi.get("chefs_op", [])), ""))
    poser(4, next(iter(c["nom"] for c in fi.get("compositeurs", [])), ""))
    poser(5, next(iter(c["nom"] for c in fi.get("scenaristes", []) if c["nom"] not in reals), ""))
    if acteurs:
        poser(6, acteurs[0]["nom"], acteurs[0].get("role", ""))
    if reals:
        p, sym, metier = PIECES[7]
        out.append(dict(piece=p, sym=sym, metier=metier, nom=" & ".join(reals[:2]), role="", case=CASES[7]))
    return out


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_windom"])
    for _ in range(25):
        film = tirer(pool, deja)
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        pieces = equipe(fi)
        if len(pieces) >= 6 and any(p["piece"] == "Roi" for p in pieces):
            break
    else:
        raise RuntimeError("L'échiquier : pas assez d'équipes de films connues dans les listes choisies.")
    d = details_film(api, film)
    titres = {normaliser(t) for t in d["noms"]}
    for p in pieces:                      # un personnage qui porte le titre du film (« Rocky ») ne s'affiche pas
        if p["role"] and normaliser(p["role"].split("/")[0]) in titres | {normaliser(w) for t in titres for w in t.split()}:
            p["role"] = ""
    n = len(pieces)
    etat = {"pieces": [], "total": n, "indices": [], "trous": ""}
    fin = 0.78
    evts = [(round(duree * fin * k / max(1, n - 1), 2) if k else 0.0,
             lambda p=p: etat["pieces"].append(p)) for k, p in enumerate(pieces)]
    if cfg.get("windom_indices", True):
        rep = reponse_affichee(cfg, film, d)
        if d.get("annee"):
            evts.append((duree * 0.5, lambda: etat["indices"].append(d["annee"])))
        evts.append((duree * 0.86, lambda: etat.update(trous=trous(rep, 0.25))))
    etapes = chronologie(evts, lambda: {**etat, "pieces": [dict(p) for p in etat["pieces"]],
                                        "indices": list(etat["indices"])})
    return manche_titre("windom", "echiquier", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
