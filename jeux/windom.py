"""Windom Earle's Chessboard (Le cavalier) : Windom Earle joue aux échecs avec des lettres. Sur l'échiquier, 64 cases,
une lettre par case (les lettres reviennent : il n'y en a que 26). Le titre du film y est caché, lettre après lettre :
on passe d'une lettre à la suivante par un déplacement de pièce d'échecs (cavalier en « L », tour en ligne, fou en
diagonale, roi d'une case, dame). La pièce qui va jouer est posée sur la dernière case lue : les plus malins devancent
Windom (la lettre suivante est forcément à portée de cette pièce). La fin du titre reste à deviner.
Indice (réglable) : l'année.
"""
import random
import re

from texte import normaliser
from tmdb import details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer

SAUTS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
# lettres de remplissage, à la fréquence du français (les cases vides ne doivent pas se repérer)
FREQ = "EEEEEEEEEEEEAAAAAAAAIIIIIIISSSSSSSNNNNNNNRRRRRRRTTTTTTTOOOOOOLLLLLUUUUUDDDCCCMMMPPGBVHFQYXJKWZ"


def lettres(titre):
    return re.sub(r"[^A-Z0-9]", "", normaliser(titre).upper())


PIECES = {"cavalier": "♞", "tour": "♜", "fou": "♝", "roi": "♚", "dame": "♛"}
POIDS = {"cavalier": 5, "tour": 2, "fou": 2, "roi": 2, "dame": 1}


def portee(piece, case, libres):
    """Les cases libres qu'atteint la pièce depuis case (portée limitée à 3 cases pour la tour, le fou et la dame)."""
    x, y = case % 8, case // 8
    if piece == "cavalier":
        dirs, loin = SAUTS, 1
    elif piece == "roi":
        dirs, loin = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b], 1
    else:
        droites, diag = [(1, 0), (-1, 0), (0, 1), (0, -1)], [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        dirs = droites if piece == "tour" else diag if piece == "fou" else droites + diag
        loin = 3
    out = []
    for dx, dy in dirs:
        for k in range(1, loin + 1):
            a, b = x + dx * k, y + dy * k
            if not (0 <= a < 8 and 0 <= b < 8):
                break
            if (b * 8 + a) in libres:
                out.append(b * 8 + a)
    return out


def chemin(n, essais=300):
    """[(case, pièce qui part de cette case vers la suivante)] : n cases sans repasser."""
    noms = list(POIDS)
    for _ in range(essais):
        c = random.randrange(64)
        libres = set(range(64)) - {c}
        cases, pieces = [c], []
        while len(cases) < n:
            essai = random.choices(noms, [POIDS[x] for x in noms], k=len(noms))
            for p in essai + noms:
                vs = portee(p, cases[-1], libres)
                if vs:
                    break
            else:
                break
            nxt = random.choice(vs)
            pieces.append(p)
            cases.append(nxt)
            libres.discard(nxt)
        if len(cases) == n:
            return cases, pieces + [random.choice(noms)]
    return None


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_windom"])
    for _ in range(25):
        film = tirer(pool, deja)
        d = details_film(api, film)
        rep = reponse_affichee(cfg, film, d)
        lt = lettres(rep)
        if 4 <= len(lt) <= 24:
            r = chemin(len(lt))
            if r:
                ch, pieces = r
                break
    else:
        raise RuntimeError("Le cavalier : aucun titre de la bonne longueur dans les listes choisies.")
    grille = [random.choice(FREQ) for _ in range(64)]
    for c, l in zip(ch, lt):
        grille[c] = l
    n = len(lt)
    montrees = max(2, round(n * 0.7))                 # le cavalier ne montre pas tout : la fin reste à deviner
    etat = {"grille": grille, "chemin": [], "piece": "", "indices": [], "n": n}
    evts = [(round(duree * 0.8 * k / max(1, montrees - 1), 2), lambda k=k: etat.update(chemin=ch[:k + 1], piece=PIECES[pieces[k]]))
            for k in range(montrees)]
    if cfg.get("windom_indices", True) and d.get("annee"):
        evts.append((duree * 0.45, lambda: etat["indices"].append(d["annee"])))
    etapes = chronologie(evts, lambda: {**etat, "chemin": list(etat["chemin"]), "indices": list(etat["indices"])})
    m = manche_titre("windom", "cavalier", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    m["detail"] = "Le parcours : " + " → ".join(lt)
    return m
