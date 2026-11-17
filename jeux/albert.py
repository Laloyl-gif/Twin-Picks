"""Le lien (Albert) : qu'ont ces deux films en commun ?

Deux films s'affichent (sans leur année) ; il faut trouver ce qui les relie parmi plusieurs propositions (une seule
est vraie) : acteur commun, réalisateur, compositeur, scénariste, directeur de la photo, thème (mot-clé TMDB),
genre, décennie, année, langue ou ordre de budget (« Budget de 15 à 40 M$ »).
Jamais deux films d'une même saga ou d'un même univers (ni le troisième film de l'indice), et la saga n'est
jamais le lien : ce serait trop facile.
Les fausses pistes sont tirées des deux films eux-mêmes (un acteur d'un seul des deux films, le réalisateur
de l'un…) pour qu'on ne puisse pas répondre au hasard. Indices (réglables) : un troisième film qui partage
le même lien, puis la moitié des fausses pistes s'efface.
"""
import random
from concurrent.futures import ThreadPoolExecutor

from PIL import ImageOps

import sagas
from config import LIENS_ALBERT
from texte import normaliser
from tmdb import LANGUES, cle_film, decouvrir, fiche, filmographie
from visuels import en_jpeg
from .commun import affiche, chronologie

LIENS = LIENS_ALBERT
POIDS = {"acteur": 30, "realisateur": 22, "compositeur": 12, "scenariste": 12, "photo": 7,
         "theme": 12, "genre": 6, "decennie": 8, "annee": 6, "langue": 4, "budget": 6}
JOBS = {"acteur": None, "realisateur": "Director", "compositeur": "compositeur", "scenariste": "scenariste",
        "photo": "Director of Photography"}


def _themes():
    """Mots-clés TMDB (anglais) -> libellé français : thèmes des conditions + lexique de Major Briggs."""
    from .briggs_lexique import LEXIQUE
    from .contraintes import THEMES
    out = {normaliser(en): fr for fr, en in THEMES}
    cat = ""
    for ligne in LEXIQUE.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("[") and ligne.endswith("]"):
            cat = ligne[1:-1]
            continue
        if "=" not in ligne or ligne.startswith("#") or ligne.startswith("~") or cat == "theme":
            continue
        lib, decl = (x.strip() for x in ligne.split("=", 1))
        for en in decl.partition("/")[0].split(","):
            en = normaliser(en.strip().rstrip("*"))
            if en and " " in en:                  # expressions précises seulement (« time travel », « haunted house »)
                out.setdefault(en, lib)
    return out


THEMES_FR = _themes()
PAYS = {"FR": "France", "GB": "Royaume-Uni", "DE": "Allemagne", "IT": "Italie", "ES": "Espagne", "JP": "Japon",
        "KR": "Corée du Sud", "CN": "Chine", "HK": "Hong Kong", "IN": "Inde", "CA": "Canada", "AU": "Australie",
        "NZ": "Nouvelle-Zélande", "MX": "Mexique", "BR": "Brésil", "AR": "Argentine", "SE": "Suède", "DK": "Danemark",
        "NO": "Norvège", "BE": "Belgique", "IE": "Irlande", "RU": "Russie", "PL": "Pologne", "TW": "Taïwan",
        "IR": "Iran", "TR": "Turquie", "NL": "Pays-Bas", "AT": "Autriche", "CH": "Suisse", "CZ": "Tchéquie",
        "FI": "Finlande", "IS": "Islande", "HU": "Hongrie", "ZA": "Afrique du Sud", "TH": "Thaïlande"}
ECHANTILLON = 70
BUDGETS = [(0, 1e6, "Budget de moins d'1 M$"), (1e6, 5e6, "Budget de 1 à 5 M$"), (5e6, 15e6, "Budget de 5 à 15 M$"),
           (15e6, 40e6, "Budget de 15 à 40 M$"), (40e6, 80e6, "Budget de 40 à 80 M$"),
           (80e6, 150e6, "Budget de 80 à 150 M$"), (150e6, 250e6, "Budget de 150 à 250 M$"),
           (250e6, 1e12, "Budget de plus de 250 M$")]


def _liens(fi):
    """Toutes les clés de lien d'un film : {(catégorie, valeur): libellé}."""
    out = {}
    for a in fi["acteurs"]:
        if a["ordre"] <= 9:
            out[("acteur", a["id"])] = f"Acteur : {a['nom']}"
    for r in fi["realisateurs"][:3]:
        out[("realisateur", r["id"])] = f"Réalisé par {r['nom']}"
    for c in fi["compositeurs"][:2]:
        out[("compositeur", c["id"])] = f"Musique de {c['nom']}"
    for c in fi.get("scenaristes", [])[:3]:
        out[("scenariste", c["id"])] = f"Écrit par {c['nom']}"
    for c in fi.get("chefs_op", [])[:2]:
        out[("photo", c["id"])] = f"Image (photo) de {c['nom']}"
    for kid, nom in zip(fi.get("mots_cles_ids", []), fi.get("mots_cles", [])):
        fr = THEMES_FR.get(normaliser(nom))
        if fr:
            out[("theme", kid)] = f"Thème : {fr}"
    for gid, g in zip(fi["genre_ids"], fi["genres"]):
        out[("genre", gid)] = f"Genre : {g}"
    if fi["annee"][:4].isdigit():
        a = int(fi["annee"][:4])
        out[("decennie", a // 10 * 10)] = f"Années {a // 10 * 10}"
        out[("annee", a)] = f"Sortis en {a}"
    if fi["langue"] and fi["langue"] != "en":
        out[("langue", fi["langue"])] = f"Tournés en {LANGUES.get(fi['langue'], fi['langue'])}"
    b = fi.get("budget") or 0
    if b >= 1e5:
        for i, (bas, haut, txt) in enumerate(BUDGETS):
            if bas <= b < haut:
                out[("budget", i)] = txt
                break
    return out


def _troisieme(api, cle, fiches, a, b, fia, fib):
    """Un autre film qui partage le lien (indice), d'une autre saga que les deux premiers."""
    cat, val = cle
    exclus = {cle_film(a), cle_film(b)}
    cands = []
    try:
        if cat in JOBS:
            cands = [f for f in filmographie(api, val, JOBS[cat])[:15] if f["votes"] >= 150]
        elif cat == "theme":
            cands = [f for f in decouvrir(api, 1, with_keywords=val) if f["votes"] >= 150]
    except Exception:  # noqa: BLE001
        cands = []
    if not cands:
        cands = [f for f, _, li in fiches if cle in li]
    cands = [f for f in cands if cle_film(f) not in exclus and f.get("poster_path")
             and not sagas.meme_univers(f, a, None, fia) and not sagas.meme_univers(f, b, None, fib)]
    return random.choice(cands[:8]) if cands else None


def construire(api, cfg, pool, deja):
    duree, n = float(cfg["dur_albert"]), int(cfg["albert_choix"])
    actives = [k for k in LIENS if cfg.get("albert_" + k, True)] or list(LIENS)
    films = [f for f in pool if f.get("poster_path") or f.get("title")]
    if len(films) < 2:
        raise RuntimeError("Albert : il faut au moins deux films dans les listes choisies.")
    echantillon = random.sample(films, min(ECHANTILLON, len(films)))

    def lire(f):
        try:
            fi = fiche(api, f)
            return f, fi, _liens(fi)
        except Exception:  # noqa: BLE001
            return f, None, None

    with ThreadPoolExecutor(max_workers=8) as ex:
        fiches = [(f, fi, li) for f, fi, li in ex.map(lire, echantillon) if li]
    index = {}
    for f, fi, li in fiches:
        for k in li:
            index.setdefault(k, []).append((f, fi, li))
    ordre = sorted(actives, key=lambda c: random.random() ** (1 / POIDS[c]), reverse=True)
    choix = None
    for cat in ordre:
        cles = [k for k, v in index.items() if k[0] == cat and len(v) >= 2]
        random.shuffle(cles)
        for k in cles:
            paires = [(x, y) for i, x in enumerate(index[k]) for y in index[k][i + 1:]]
            random.shuffle(paires)
            for (fa, fia, la), (fb, fib, lb) in paires[:30]:
                if ("albert", frozenset((cle_film(fa), cle_film(fb)))) in deja:
                    continue
                if sagas.meme_univers(fa, fb, fia, fib):
                    continue                          # deux films d'une même saga ou d'un même univers
                choix = (k, fa, fia, la, fb, fib, lb)
                break
            if choix:
                break
        if choix:
            break
    if not choix:
        raise RuntimeError("Albert : aucun lien trouvé entre les films des listes (catégories activées trop "
                           "restreintes ou listes trop petites).")
    k, fa, fia, la, fb, fib, lb = choix
    deja.add(("albert", frozenset((cle_film(fa), cle_film(fb)))))
    vrais = set(la) & set(lb)
    bonne_txt = la[k]

    # fausses pistes : d'abord des liens d'un seul des deux films (même catégorie en priorité), puis d'autres films
    def origine(x):
        return fa["title"] if x in la else fb["title"] if x in lb else ""

    faux = [x for x in (set(la) | set(lb)) - vrais]
    meme = [x for x in faux if x[0] == k[0]]
    autres = [x for x in faux if x[0] != k[0] and x[0] in actives]
    random.shuffle(meme)
    random.shuffle(autres)
    pistes = meme[:max(2, (n - 1) // 2)]
    for x in autres:
        if len(pistes) >= n - 1:
            break
        if all(x[0] != p[0] or x[0] in ("acteur", "genre") for p in pistes):
            pistes.append(x)
    for x in meme[len(pistes):] + autres:
        if len(pistes) >= n - 1:
            break
        if x not in pistes:
            pistes.append(x)
    libelles = {x: la.get(x) or lb.get(x) for x in pistes}
    if len(pistes) < n - 1:                            # petits films : liens d'autres films de l'échantillon
        for f, _, li in random.sample(fiches, len(fiches)):
            for x in li:
                if x not in vrais and x not in libelles and x[0] in actives:
                    pistes.append(x)
                    libelles[x] = li[x]
                    break
            if len(pistes) >= n - 1:
                break
    items = [{"txt": bonne_txt, "k": k}] + [{"txt": libelles[x], "k": x} for x in pistes if libelles[x]]
    vus, uniques = set(), []
    for it in items:
        if it["txt"] not in vus:
            vus.add(it["txt"])
            uniques.append(it)
    items = uniques[:n]
    random.shuffle(items)
    bonne = next(i for i, it in enumerate(items) if it["k"] == k)
    infos = []
    for it in items:
        if it["k"] == k:
            infos.append("le lien")
        else:
            o = origine(it["k"])
            infos.append(f"seulement {o}" if o else "aucun des deux")

    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f in (fa, fb)]
    etat = {"paire": [{"img": 0, "txt": fa["title"]}, {"img": 1, "txt": fb["title"]}],         # sans l'année
            "items": [{"txt": it["txt"]} for it in items], "question": "Quel est le lien ?", "indices": []}
    evts = []
    if cfg.get("albert_tiers", True):
        tiers = _troisieme(api, k, fiches, fa, fb, fia, fib)
        if tiers:
            images.append(en_jpeg(ImageOps.fit(affiche(api, tiers, "w342"), (300, 450)), 450))
            evts.append((duree * 0.45, lambda t=tiers: etat.update(tiers={"img": 2, "txt": t["title"]})))
    if cfg.get("albert_elimine", True):
        fausses = [i for i in range(len(items)) if i != bonne]
        barrees = set(random.sample(fausses, len(fausses) // 2))
        evts.append((duree * 0.7, lambda: etat.update(
            items=[dict(it, barre=True) if i in barrees else it for i, it in enumerate(etat["items"])])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]],
                                        "indices": list(etat["indices"])})
    autres_liens = [t for t in dict.fromkeys(la[x] for x in sorted(vrais, key=str) if x != k) if t != bonne_txt][:4]
    return dict(jeu="albert", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None,
                images=images, cles=[], bonne="", bonne_i=bonne, infos=infos,
                solution=f"Le lien : {bonne_txt}",
                detail=("Aussi en commun : " + " · ".join(autres_liens)) if autres_liens else
                f"{fa['title']} et {fb['title']}",
                films=[cle_film(fa), cle_film(fb)])
