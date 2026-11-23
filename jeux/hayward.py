"""Doc Hayward's Secrets (Les secrets du docteur) : le Dr Will Hayward, médecin de Twin Peaks, connaît les secrets de
tout le monde. Des anecdotes de tournage arrivent l'une après l'autre (Wikipédia en français : « Autour du film »,
« Anecdotes », « Tournage »…), de la plus vague à la plus parlante ; le titre y est masqué, les noms d'acteurs
restent (ce sont des indices). Puis le genre et l'année, puis le titre à trous. Une manche sur cinq environ : trouver
un acteur, à partir d'anecdotes sur sa vie.
"""
import random
import re
import time

import anecdotes
from texte import cle, est_latin
from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, cles_reponses, manche_titre, reponse_affichee, tirer, trous

NB = 3


def specificite(t):
    """Plus une phrase a de noms propres et de chiffres, plus elle en dit."""
    return len(re.findall(r"(?<![.!?]\s)\b[A-ZÀ-Ý][a-zà-ÿ]{2,}", t)) + len(re.findall(r"\d", t)) * 0.5


def choisir(lst, noms):
    """Trois anecdotes utilisables (titre masqué), de la plus vague à la plus parlante."""
    vues, bons = set(), []
    for a in sorted(lst, key=lambda x: -x["p"]):
        t = anecdotes.masquer(a["t"], noms)
        if t.count("…") > 3 or len(t) < 50 or cle(t)[:40] in vues:
            continue
        vues.add(cle(t)[:40])
        bons.append(t)
    if len(bons) < NB:
        return None
    lot = bons[:8]
    random.shuffle(lot)
    return sorted(lot[:NB], key=specificite)


def _etapes(duree, textes, plus=(), trou=""):
    etat = {"secrets": [], "indices": [], "trous": ""}
    evts = [(round(duree * x, 2), lambda t=t: etat["secrets"].append(t)) for x, t in zip((0.0, 0.28, 0.52), textes)]
    for x, t in plus:
        evts.append((round(duree * x, 2), lambda t=t: etat["indices"].append(t)))
    if trou:
        evts.append((round(duree * 0.85, 2), lambda: etat.update(trous=trou)))
    et = chronologie(evts, lambda: {**etat, "secrets": list(etat["secrets"]), "indices": list(etat["indices"])})
    if et and et[0][0] == 0.0 and not et[0][1]["secrets"] and len(et) > 1 and et[1][0] == 0.0:
        et = et[1:]
    return et


def _acteur(api, cfg, deja, duree):
    from tmdb import charger_acteurs
    acteurs = [a for a in charger_acteurs(api) if a.get("profile_path")]
    random.shuffle(acteurs)
    t0 = time.time()
    for a in acteurs[:25]:
        if time.time() - t0 > 25 or ("acteur", a["id"]) in deja:
            continue
        lst = anecdotes.de_personne(api, a["id"])
        noms = [a["name"]] + [m for m in a["name"].split() if len(m) > 2]
        textes = choisir(lst, noms)
        if not textes:
            continue
        deja.add(("acteur", a["id"]))
        etapes = _etapes(duree, textes, trou=trous(a["name"], 0))
        mots = [m for m in a["name"].split() if m.lower().strip(".,") not in ("jr", "sr", "ii", "iii")]
        cles = cles_reponses(a["name"], *(mots[-1:] if len(mots) > 1 else []))
        try:
            photo = en_jpeg(api.image(a["profile_path"], "h632").convert("RGB"))
        except Exception:  # noqa: BLE001
            photo = None
        return dict(jeu="hayward", vue="secrets", duree=duree, etapes=etapes, images=[], revelation=photo,
                    reponse="titre", cles=cles, bonne=a["name"], solution=a["name"], pool="acteurs", detail="",
                    films=[], acteur=True)
    return None


def construire(api, cfg, pool, deja):
    duree = float(cfg.get("dur_hayward", 75))
    if random.random() * 100 < float(cfg.get("hayward_acteurs", 20)):
        try:
            m = _acteur(api, cfg, deja, duree)
            if m:
                return m
        except Exception:  # noqa: BLE001
            pass
    films = [f for f in pool if not f.get("tv")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    t0 = time.time()
    for f in films[:60]:
        if time.time() - t0 > 40:
            break
        lst = anecdotes.de_film(api, f)
        if len(lst) < NB:
            continue
        d = details_film(api, f)
        noms = [f["title"], f.get("original_title"), d.get("en"), d.get("saga")] + [n for n in d.get("noms", [])[:8] if est_latin(n)]
        textes = choisir(lst, noms)
        if not textes:
            continue
        deja.add(cle_film(f))
        plus = []
        depart = " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)
        if depart and cfg.get("hayward_indices", True):
            plus.append((0.7, depart))
        etapes = _etapes(duree, textes, plus, trous(reponse_affichee(cfg, f, d), 0) if cfg.get("hayward_indices", True) else "")
        return manche_titre("hayward", "secrets", duree, f, d, etapes, [], en_jpeg(affiche(api, f, "w500")), cfg)
    raise RuntimeError("Les secrets du docteur : pas d'anecdotes trouvées pour les films des listes "
                       "(il faut Internet ; la base se remplit au fil des parties).")
