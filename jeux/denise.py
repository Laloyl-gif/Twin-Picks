"""Denise's Undercover (Qui suis-je ?) : Denise Bryson, agent de la DEA, sait tout des identités d'emprunt. Ici, la
carte d'identité d'un acteur (acteurs.txt) ou d'un réalisateur (réalisateurs du fichier, réglable) se remplit sans
son nom : les indices difficiles d'emblée (métier, date et lieu de naissance), puis de plus en plus simples : débuts,
signe particulier (une phrase de sa biographie, noms masqués), portrait (homme ou femme, âge, pays), genre de
prédilection, complice habituel, rôle le plus connu, autres films, et enfin son affaire la plus célèbre. Le nom est écrit en blancs
dès le début (une case par lettre) et des lettres s'y révèlent peu à peu. À la réponse : sa photo.
"""
import datetime
import random
import re
from collections import Counter

from PIL import ImageOps

from tmdb import charger_acteurs, fiche, filmographie
from texte import est_latin, normaliser
from visuels import en_jpeg
from .commun import chronologie, cles_reponses, tirer
from .contraintes import realisateurs_fichier
from .filmo import films_connus
from .repliques import masquer

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
        "décembre"]
SIGNES = [(1, 20, "Capricorne"), (2, 19, "Verseau"), (3, 21, "Poissons"), (4, 20, "Bélier"), (5, 21, "Taureau"),
          (6, 21, "Gémeaux"), (7, 23, "Cancer"), (8, 23, "Lion"), (9, 23, "Vierge"), (10, 23, "Balance"),
          (11, 22, "Scorpion"), (12, 22, "Sagittaire"), (12, 32, "Capricorne")]


def date_fr(iso):
    try:
        a, m, j = iso.split("-")
        return f"{int(j)} {MOIS[int(m) - 1]} {a}"
    except (ValueError, IndexError, AttributeError):
        return ""


def signe_astro(iso):
    try:
        _, m, j = (int(x) for x in iso.split("-"))
    except (ValueError, AttributeError):
        return ""
    for mm, jj, nom in SIGNES:
        if (m, j) < (mm, jj):
            return nom
    return "Capricorne"


def age(naissance, deces):
    try:
        n = datetime.date.fromisoformat(naissance)
        f = datetime.date.fromisoformat(deces) if deces else datetime.date.today()
    except (ValueError, TypeError):
        return ""
    a = f.year - n.year - ((f.month, f.day) < (n.month, n.day))
    return f"mort à {a} ans" if deces else f"{a} ans"


def signe(bio, noms):
    """Une phrase de la biographie, sans nom propre de la personne (ni la première, qui la présente souvent)."""
    phrases = [p.strip() for p in re.split(r"(?<=[.!?])\s+", bio or "") if 40 <= len(p.strip()) <= 200]
    mots = {normaliser(m) for n in noms for m in n.split() if len(normaliser(m)) >= 3}
    phrases = phrases[1:5] or phrases[:1]
    return masquer(random.choice(phrases), mots) if phrases else ""


def collaborateur(api, films, pid, realisateur):
    """La personne avec qui elle a le plus travaillé (un réalisateur pour un acteur, un acteur pour un réalisateur)."""
    compte = Counter()
    for f in films[:8]:
        try:
            fi = fiche(api, dict(f, tv=False))
        except Exception:  # noqa: BLE001
            continue
        gens = fi["acteurs"][:6] if realisateur else fi["realisateurs"][:2]
        for p in gens:
            if p["id"] != pid:
                compte[p["nom"]] += 1
    nom, n = compte.most_common(1)[0] if compte else ("", 0)
    return (nom, n) if n >= 2 else ("", 0)


def personne(api, cfg, pool, deja):
    if random.random() * 100 < float(cfg.get("denise_realisateurs", 25)):
        try:
            reals = [{"id": p["id"], "name": p["name"], "profile_path": p.get("profile_path"), "real": True}
                     for p in realisateurs_fichier(api, cfg) if p.get("profile_path")]
        except Exception:  # noqa: BLE001
            reals = []
        if reals:
            return tirer(reals, deja, ident=lambda x: ("personne", x["id"]))
    acteurs = [a for a in (pool or charger_acteurs(api)) if a.get("profile_path")]
    return tirer(acteurs, deja, ident=lambda x: ("personne", x["id"]))


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_denise"])
    for _ in range(12):
        a = personne(api, cfg, pool, deja)
        real = bool(a.get("real"))
        try:
            p = api.get(f"/person/{a['id']}")
            if not p.get("biography"):
                p["biography"] = api.get(f"/person/{a['id']}", language="en-US").get("biography", "")
            films = [f for f in filmographie(api, a["id"], "Director")] if real else \
                films_connus(api.get(f"/person/{a['id']}/movie_credits").get("cast", []), 4)
        except Exception:  # noqa: BLE001
            continue
        if len(films) >= 2 and p.get("birthday"):
            break
    else:
        raise RuntimeError("Qui suis-je ? : aucune personne exploitable.")
    noms = [a["name"]] + [x for x in p.get("also_known_as", []) if est_latin(x)]
    film = lambda c: f"{c.get('title')} ({(c.get('release_date') or '')[:4]})" if c.get("release_date") else c.get("title", "")
    datees = sorted([c for c in films if c.get("release_date")], key=lambda c: c["release_date"])
    celebre = max(films, key=lambda c: c.get("votes") or c.get("vote_count") or 0)
    premier = next((c for c in datees if c is not celebre), datees[0])
    feminin = p.get("gender") == 1
    e = "e" if feminin else ""
    # Les indices difficiles d'emblée (naissance), puis de plus en plus simples ; le plus facile à la fin.
    debut = [{"k": "Métier", "v": ("Réalisatrice" if feminin else "Réalisateur") if real else ("Actrice" if feminin else "Acteur")},
             {"k": f"Né{e} le", "v": date_fr(p["birthday"])}]
    if p.get("place_of_birth"):
        debut.append({"k": "À", "v": p["place_of_birth"]})
    plus = []
    if datees:
        plus.append({"k": "Débuts" if real else "Premier rôle connu",
                     "v": film(premier) + (f", rôle : {premier['role']}" if not real and premier.get("role") else
                                           f", rôle : {premier['character']}" if not real and premier.get("character") else "")})
    s_ = signe(p.get("biography"), noms)
    if s_:
        plus.append({"k": "Signe particulier", "v": s_})
    pays = (p.get("place_of_birth") or "").split(",")[-1].strip()
    portrait = ("une femme" if feminin else "un homme") + (f", {age(p['birthday'], p.get('deathday'))}" if age(p["birthday"], p.get("deathday")) else "")
    plus.append({"k": "Portrait", "v": portrait[0].upper() + portrait[1:] + (f", originaire de {pays}" if pays else "")})
    genres = Counter(g for c in films[:20] for g in (c.get("genre_ids") or []))
    if genres:
        from tmdb import GENRES
        g = GENRES.get(genres.most_common(1)[0][0])
        if g:
            plus.append({"k": "Genre de prédilection", "v": g})
    nom_c, n_c = collaborateur(api, films, a["id"], real)
    if nom_c:
        plus.append({"k": "Complice habituel", "v": f"{nom_c} ({n_c} films ensemble)"})
    role = celebre.get("role") or celebre.get("character")
    if role and not real:
        plus.append({"k": "Rôle le plus connu", "v": role})
    autres = [c for c in sorted(films, key=lambda c: -(c.get("votes") or c.get("vote_count") or 0)) if c is not celebre][:2]
    if autres:
        plus.append({"k": "Autres affaires", "v": " · ".join(film(c) for c in autres)})
    lignes = debut + plus + [{"k": "Affaire la plus célèbre", "v": film(celebre)}]
    nd = len(debut)
    n = len(lignes)
    # le nom : des blancs dès le début, puis des lettres qui se révèlent
    vrai = a["name"]
    vide = "".join("_" if c.isalnum() else c for c in vrai)
    etat = {"fiche": [], "total": n, "nom": vide, "indices": []}
    evts = [(0, lambda: etat.update(fiche=lignes[:nd]))] + \
        [(round(duree * 0.8 * (k - nd + 1) / max(1, n - nd), 2), lambda k=k: etat.update(fiche=lignes[:k + 1])) for k in range(nd, n)]
    lettres = [i for i, c in enumerate(vrai) if c.isalnum()]
    random.shuffle(lettres)
    montrees = set()
    for t, part in ((0.45, 0.15), (0.65, 0.3), (0.85, 0.45)):
        montrees |= set(lettres[:max(1, round(len(lettres) * part))])
        txt = "".join(c if (not c.isalnum() or i in montrees) else "_" for i, c in enumerate(vrai))
        evts.append((duree * t, lambda txt=txt: etat.update(nom=txt)))
    etapes = chronologie(evts, lambda: {**etat, "fiche": [dict(x) for x in etat["fiche"]], "indices": list(etat["indices"])})
    mots = [m for m in vrai.split() if m.lower().strip(".,") not in ("jr", "sr", "ii", "iii")]
    if len(mots) > 1:
        noms.append(mots[-1])
    photo = api.image(a["profile_path"], "h632")
    return dict(jeu="denise", vue="identite", duree=duree, etapes=etapes, images=[],
                revelation=en_jpeg(ImageOps.fit(photo.convert("RGB"), (420, 560))), reponse="titre", pool="acteurs",
                cles=cles_reponses(*noms), bonne=vrai, solution=vrai, detail=film(celebre))
