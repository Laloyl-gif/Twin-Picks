"""Questions éclair à six choix, tirées des films des listes (pour Le contrat des frères Mitchum).

Une question : {"q": texte, "choix": [6 textes], "bonne": indice, "img": numéro d'image ou None}.
Toutes les réponses fausses sont vérifiées (un acteur proposé ne joue pas dans le film, deux années ne se suivent
pas, etc.) : il n'y a jamais deux bonnes réponses.
"""
import random

from PIL import ImageOps

from tmdb import fiche
from visuels import en_jpeg
from .commun import affiche

NB_CHOIX = 6


def _annee(x):
    try:
        return int(x.get("annee") or 0)
    except ValueError:
        return 0


def _melanger(bonne, fausses):
    uniques = []
    for x in fausses:
        if x and x != bonne and x not in uniques:
            uniques.append(x)
    choix = [bonne] + uniques[:NB_CHOIX - 1]
    if len(choix) < NB_CHOIX:
        return None
    random.shuffle(choix)
    return choix, choix.index(bonne)


def _q(texte, bonne, fausses, img=None):
    r = _melanger(bonne, fausses)
    if not r:
        return None
    choix, k = r
    return {"q": texte, "choix": choix, "bonne": k, "img": img}


def preparer(api, pool, n_films=24):
    """Les fiches (casting, équipe) de films des listes, pour fabriquer les questions."""
    films = [f for f in pool if not f.get("tv")]
    random.shuffle(films)
    out = []
    for f in films:
        try:
            fi = fiche(api, f)
        except Exception:  # noqa: BLE001
            continue
        if fi.get("titre"):
            out.append((f, fi))
        if len(out) >= n_films:
            break
    return out


def q_realisateur(fs):
    f, fi = random.choice(fs)
    if not fi.get("realisateurs"):
        return None
    bonne = fi["realisateurs"][0]["nom"]
    siens = {r["nom"] for r in fi["realisateurs"]}
    autres = list({r["nom"] for _, g in fs for r in g.get("realisateurs", [])[:1]} - siens)
    random.shuffle(autres)
    return _q(f"Qui a réalisé « {fi['titre']} » ?", bonne, autres)


def q_compositeur(fs):
    f, fi = random.choice(fs)
    if not fi.get("compositeurs"):
        return None
    bonne = fi["compositeurs"][0]["nom"]
    siens = {r["nom"] for r in fi["compositeurs"]}
    autres = list({r["nom"] for _, g in fs for r in g.get("compositeurs", [])[:1]} - siens)
    random.shuffle(autres)
    return _q(f"Qui a composé la musique de « {fi['titre']} » ?", bonne, autres)


def q_acteur_film(fs):
    """Dans quel film joue cet acteur ? (les cinq autres films ne l'ont pas au casting)"""
    f, fi = random.choice(fs)
    tete = [a for a in fi.get("acteurs", [])[:3] if a.get("nom")]
    if not tete:
        return None
    a = random.choice(tete)
    autres = [g["titre"] for _, g in fs if g["titre"] != fi["titre"] and all(b["id"] != a["id"] for b in g.get("acteurs", []))]
    random.shuffle(autres)
    return _q(f"Dans quel film joue {a['nom']} ?", fi["titre"], autres)


def q_qui_joue(fs):
    f, fi = random.choice(fs)
    tete = [a for a in fi.get("acteurs", [])[:2] if a.get("nom")]
    if not tete:
        return None
    ids = {a["id"] for a in fi.get("acteurs", [])}
    autres = list({a["nom"] for _, g in fs for a in g.get("acteurs", [])[:2] if a["id"] not in ids})
    random.shuffle(autres)
    return _q(f"Qui joue dans « {fi['titre']} » ?", random.choice(tete)["nom"], autres)


def q_annee(fs):
    f, fi = random.choice(fs)
    a = _annee(fi)
    if not a:
        return None
    autres = [x for x in range(a - 12, a + 13) if x != a and abs(x - a) >= 2 and x <= 2026]
    random.shuffle(autres)
    fausses, pris = [], {a}
    for x in autres:                                   # pas deux années collées : une seule réponse possible
        if all(abs(x - y) >= 2 for y in pris):
            fausses.append(x)
            pris.add(x)
    return _q(f"En quelle année est sorti « {fi['titre']} » ?", str(a), [str(x) for x in fausses])


def _extreme(fs, cle, plus, texte, ecart):
    lot = [(f, fi) for f, fi in fs if cle(fi)]
    random.shuffle(lot)
    choisis = []
    for x in lot:
        if all(abs(cle(x[1]) - cle(y[1])) >= ecart for y in choisis):
            choisis.append(x)
        if len(choisis) == NB_CHOIX:
            break
    if len(choisis) < NB_CHOIX:
        return None
    meilleur = (max if plus else min)(choisis, key=lambda x: cle(x[1]))
    return _q(texte, meilleur[1]["titre"], [x[1]["titre"] for x in choisis if x is not meilleur])


def q_premier(fs):
    return _extreme(fs, _annee, False, "Lequel est sorti en premier ?", 1)


def q_long(fs):
    return _extreme(fs, lambda fi: fi.get("duree") or 0, True, "Lequel est le plus long ?", 6)


def q_note(fs):
    return _extreme(fs, lambda fi: round((fi.get("note") or 0) * 10), True, "Lequel est le mieux noté sur TMDB ?", 3)


GENERATEURS = [(q_realisateur, 3), (q_acteur_film, 3), (q_qui_joue, 2), (q_annee, 2), (q_premier, 1), (q_long, 1),
               (q_compositeur, 1), (q_note, 1)]


def questions(api, fs, n, images, avec_affiches=True):
    """n questions variées (images : la liste où ranger les détails d'affiche des questions « Quel film ? »)."""
    out, vues = [], set()
    gens, poids = zip(*GENERATEURS)
    essais = 0
    while len(out) < n and essais < n * 12:
        essais += 1
        if avec_affiches and random.random() < 0.25:
            q = q_affiche(api, fs, images)
        else:
            q = random.choices(gens, weights=poids)[0](fs)
        if q and q["q"] not in vues:
            vues.add(q["q"])
            out.append(q)
    return out


def q_affiche(api, fs, images):
    """Quel film ? un gros plan d'affiche (le titre n'y figure pas : le milieu de l'affiche)."""
    f, fi = random.choice(fs)
    try:
        im = affiche(api, f, "w500").convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    W, H = im.size
    c = int(W * random.uniform(0.42, 0.55))
    x0 = random.randint(0, max(0, W - c))
    y0 = random.randint(int(H * 0.25), max(int(H * 0.25), int(H * 0.72) - c))
    images.append(en_jpeg(ImageOps.fit(im.crop((x0, y0, x0 + c, y0 + c)), (360, 360)), 360))
    autres = [g["titre"] for _, g in fs if g["titre"] != fi["titre"]]
    random.shuffle(autres)
    return _q("Quel film ?", fi["titre"], autres, img=len(images) - 1)
