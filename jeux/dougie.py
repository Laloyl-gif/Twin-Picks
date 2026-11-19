"""Dougie's Jackpots (Le jackpot) : au Silver Mustang Casino, Dougie Jones touche le jackpot à chaque machine
(« Hellooo! »). Ici, la machine à sous tourne : ses trois rouleaux font défiler les affiches de cinq films (les cinq
sur chaque rouleau, dans un ordre différent), très vite puis de plus en plus lentement. Il faut retrouver les cinq
films pendant que la machine tourne : chaque film trouvé rapporte des points (plus tôt = plus), les cinq : un bonus.
Indices : les années, puis les initiales. À la réponse : les cinq affiches.
"""
import random

from PIL import Image, ImageOps

import sagas
from tmdb import cle_film, details_film
from visuels import en_jpeg
from .commun import affiche, chronologie, cles_reponses, reponse_affichee, saga_de

NB, ETAPES = 5, 6
L, H = 240, 360


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_dougie"])
    cands = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(cands)
    neufs = [f for f in cands if cle_film(f) not in deja] or cands
    choisis = []
    for f in neufs + cands:
        if len(choisis) == NB:
            break
        if any(f["id"] == g["id"] or sagas.meme_univers(f, g) for g, _ in choisis):
            continue
        try:
            choisis.append((f, details_film(api, f)))
        except Exception:  # noqa: BLE001
            continue
    if len(choisis) < NB:
        raise RuntimeError("Le jackpot : pas assez de films dans les listes choisies.")
    for f, _ in choisis:
        deja.add(cle_film(f))
    posters = [ImageOps.fit(affiche(api, f, "w342").convert("RGB"), (L, H)) for f, _ in choisis]
    images = [en_jpeg(p, H) for p in posters]
    tous = Image.new("RGB", (NB * L + (NB + 1) * 10, H + 20), (14, 12, 17))
    for k, p in enumerate(posters):
        tous.paste(p, (10 + k * (L + 10), 10))
    titres = [reponse_affichee(cfg, f, d) for f, d in choisis]
    bandes = []
    for _ in range(3):                                   # les cinq films sur chaque rouleau, dans un autre ordre
        b = random.sample(range(NB), NB)
        while any(b == x or b[0] == x[0] for x in bandes):
            random.shuffle(b)
        bandes.append(b)
    etat = {"bandes": bandes, "vitesse": 0, "indices": []}
    evts = [(round(duree * 0.75 * k / ETAPES, 2), lambda k=k: etat.update(vitesse=k)) for k in range(1, ETAPES + 1)]
    if cfg.get("dougie_indices", True):
        evts.append((duree * 0.45, lambda: etat["indices"].append(
            "Années : " + ", ".join(sorted(d["annee"] or "?" for _, d in choisis)))))
        evts.append((duree * 0.72, lambda: etat["indices"].append(
            "Initiales : " + "  ".join(sorted("".join(m[0].upper() for m in t.split()[:4]) for t in titres)))))
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    return dict(jeu="dougie", vue="jackpot", duree=duree, etapes=etapes, images=images, revelation=en_jpeg(tous, 380),
                reponse="plusieurs", suggestions=True,
                films_cles=[cles_reponses(f["title"], f.get("original_title"), *d["noms"],
                                          *([saga_de(cfg, d)] if saga_de(cfg, d) else [])) for f, d in choisis],
                films_titres=titres, cles=[], bonne="", solution=" · ".join(titres),
                detail="« Hellooo! » — Dougie Jones", films=[cle_film(f) for f, _ in choisis])
