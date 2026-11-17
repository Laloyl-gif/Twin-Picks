"""Josie's Double Ledger (Le mensonge) : comme les deux livres de comptes de la scierie Packard (le vrai et le
faux), quatre affirmations sur un film : une seule est fausse. Trouvez le mensonge.

Affirmations : réalisateur, année, acteur, compositeur, scénariste, durée, pays, genre. Le mensonge reprend une
vraie valeur d'un autre film (un autre réalisateur, une autre année proche…) pour être crédible. Indice (réglable) :
à mi-temps, une affirmation vraie est barrée.
"""
import random

from PIL import ImageOps

from tmdb import GENRES, cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer

PAYS = {"US": "aux États-Unis", "FR": "en France", "GB": "au Royaume-Uni", "JP": "au Japon", "KR": "en Corée du Sud",
        "IT": "en Italie", "ES": "en Espagne", "DE": "en Allemagne", "CA": "au Canada", "AU": "en Australie",
        "IN": "en Inde", "MX": "au Mexique", "NZ": "en Nouvelle-Zélande", "HK": "à Hong Kong", "CN": "en Chine",
        "DK": "au Danemark", "SE": "en Suède", "BE": "en Belgique", "IE": "en Irlande", "BR": "au Brésil"}


def duree_txt(m):
    return f"{m // 60} h {m % 60:02d}"


def affirmations(fi, d):
    """{catégorie: (texte, valeur)} : ce que l'on sait de vrai sur le film."""
    out = {}
    if fi.get("realisateurs"):
        out["realisateur"] = (f"Réalisé par {fi['realisateurs'][0]['nom']}", fi["realisateurs"][0]["id"])
    an = fi.get("annee") or d.get("annee")
    if an and an[:4].isdigit():
        out["annee"] = (f"Sorti en {an[:4]}", int(an[:4]))
    acteurs = [a for a in fi.get("acteurs", []) if a.get("ordre", 99) <= 5]
    random.shuffle(acteurs)
    if acteurs:
        out["acteur"] = (f"Avec {acteurs[0]['nom']}", acteurs[0]["id"])
    if len(acteurs) > 1:
        out["acteur2"] = (f"Avec {acteurs[1]['nom']}", acteurs[1]["id"])
    if fi.get("compositeurs"):
        out["compositeur"] = (f"Musique de {fi['compositeurs'][0]['nom']}", fi["compositeurs"][0]["id"])
    if fi.get("scenaristes"):
        out["scenariste"] = (f"Écrit par {fi['scenaristes'][0]['nom']}", fi["scenaristes"][0]["id"])
    if fi.get("duree"):
        out["duree"] = (f"Dure {duree_txt(fi['duree'])}", fi["duree"])
    pays = [p for p in fi.get("pays_codes") or [] if p in PAYS]
    if pays:
        out["pays"] = (f"Produit {PAYS[pays[0]]}", pays[0])
    genres = [g for g in fi.get("genre_ids") or [] if g in GENRES]
    if genres:
        out["genre"] = (f"Genre : {GENRES[genres[0]]}", genres[0])
    return out


def mensonge(cat, vrai, fi, autres):
    """Une affirmation fausse mais crédible dans la catégorie cat (None si impossible)."""
    if cat == "annee":
        an = vrai[1] + random.choice([-1, 1]) * random.randint(3, 9)
        return f"Sorti en {an}"
    if cat == "duree":
        m = max(70, vrai[1] + random.choice([-1, 1]) * random.randint(18, 40))
        return f"Dure {duree_txt(m)}"
    if cat == "genre":
        siens = set(fi.get("genre_ids") or [])
        cands = [g for g in (28, 35, 18, 27, 878, 10749, 53, 16, 14, 80, 37, 10752) if g not in siens]
        return f"Genre : {GENRES[random.choice(cands)]}" if cands else None
    if cat == "pays":
        siens = set(fi.get("pays_codes") or [])
        cands = [p for p in PAYS if p not in siens]
        return f"Produit {PAYS[random.choice(cands)]}" if cands else None
    # personnes : une vraie personne d'un autre film, du même métier
    cat = cat.rstrip("2")
    gens = {"realisateur": "realisateurs", "acteur": "acteurs", "compositeur": "compositeurs",
            "scenariste": "scenaristes"}[cat]
    siens = {p["id"] for p in fi.get(gens, [])}
    for a in random.sample(autres, len(autres)):
        cands = [p for p in a.get(gens, [])[:3] if p["id"] not in siens]
        if cands:
            p = cands[0]
            debut = {"realisateur": "Réalisé par", "acteur": "Avec", "compositeur": "Musique de",
                     "scenariste": "Écrit par"}[cat]
            return f"{debut} {p['nom']}"
    return None


def construire(api, cfg, pool, deja):
    duree, n = float(cfg["dur_josie"]), int(cfg.get("josie_nb", 6))
    films = [f for f in pool if not f.get("tv")]
    autres = []
    for f in random.sample(films, min(8, len(films))):
        try:
            autres.append(fiche(api, f))
        except Exception:  # noqa: BLE001
            pass
    for _ in range(20):
        film = tirer(pool, deja, lambda f: not f.get("tv") and f.get("poster_path"))
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        d = details_film(api, film)
        vraies = affirmations(fi, d)
        if len(vraies) < min(n, 4):
            continue
        cats = random.sample(list(vraies), min(n, len(vraies)))
        faux_cat = random.choice(cats)
        faux = mensonge(faux_cat, vraies[faux_cat], fi, [a for a in autres if a.get("id") != film["id"]])
        if faux and faux != vraies[faux_cat][0]:
            break
    else:
        raise RuntimeError("Le mensonge : pas assez d'informations sur les films des listes.")
    items = [{"txt": faux if c == faux_cat else vraies[c][0]} for c in cats]
    bonne = cats.index(faux_cat)
    n = len(cats)
    image = en_jpeg(ImageOps.contain(affiche(api, film, "w500"), (400, 600)), 600)
    etat = {"film": {"img": 0, "txt": film["title"], "sous": ""}, "items": items,
            "question": "Lequel est le mensonge ?", "indices": []}
    evts = []
    if cfg.get("josie_indice", True) and n > 2:
        vraies_i = [i for i in range(n) if i != bonne]
        barrees = random.sample(vraies_i, 2 if n >= 6 else 1)
        evts.append((duree * 0.55, lambda: etat.update(
            items=[dict(it, barre=True) if i in barrees else it for i, it in enumerate(etat["items"])])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]],
                                        "indices": list(etat["indices"])})
    vrai_txt = vraies[faux_cat][0]
    infos = [f"faux : {vrai_txt[:1].lower() + vrai_txt[1:]}" if i == bonne else "vrai" for i in range(n)]
    return dict(jeu="josie", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None, images=[image],
                cles=[], bonne="", bonne_i=bonne, infos=infos, solution=f"Le mensonge : « {faux} »",
                detail=f"En vrai : {vraies[faux_cat][0]}", films=[cle_film(film)])
