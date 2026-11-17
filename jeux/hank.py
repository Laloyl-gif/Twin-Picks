"""Hank's Dominoes (Le domino manquant) : Hank Jennings et ses dominos. Une chaîne de dominos relie deux films par
leurs acteurs, mais le domino du milieu manque : c'est le film mystère. À gauche, un film A ; à droite, un film C.
Le film du milieu partage un acteur avec A et un autre acteur avec C : quel film fait le pont ?
Les deux acteurs « charnières » se dévoilent l'un après l'autre (photo sur le domino), puis genre et année, puis le
titre à trous. Rien à voir avec le casting : il faut trouver le film qui raccorde deux autres films.
"""
import random

from PIL import ImageOps

from tmdb import cle_film, details_film, fiche, filmographie
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

CONNU = 300                  # votes TMDB minimum des films A et C (des films que l'on connaît)


def _bout(api, acteur, autre, interdits):
    """Un film connu de l'acteur où l'autre acteur charnière n'a pas joué (sinon le pont serait ambigu)."""
    films = [f for f in filmographie(api, acteur["id"])[:25]
             if f["id"] not in interdits and f["votes"] >= CONNU and f.get("poster_path")]
    random.shuffle(films)
    films.sort(key=lambda f: -f["votes"] // 4000)                 # les plus connus d'abord, un peu de hasard
    for f in films[:6]:
        try:
            fi = fiche(api, dict(f, tv=False))
        except Exception:  # noqa: BLE001
            continue
        if all(a["id"] != autre["id"] for a in fi["acteurs"]):
            return f
    return None


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_hank"])
    for _ in range(14):
        film = tirer(pool, deja, lambda f: not f.get("tv"))
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        cast = [a for a in fi["acteurs"][:10] if a.get("photo")]
        if len(cast) < 2:
            continue
        random.shuffle(cast)
        trouve = None
        for i, x in enumerate(cast[:6]):
            for y in cast[i + 1:7]:
                a = _bout(api, x, y, {film["id"]})
                if not a:
                    continue
                c = _bout(api, y, x, {film["id"], a["id"]})
                if c:
                    trouve = (x, a, y, c)
                    break
            if trouve:
                break
        if trouve:
            break
    else:
        raise RuntimeError("Le domino manquant : pas assez de films reliés aux films des listes.")
    x, a, y, c = trouve
    d = details_film(api, film)
    photos = api.images([x["photo"], y["photo"]], "w185")
    images = [en_jpeg(ImageOps.fit(affiche(api, a, "w342"), (200, 300)), 300),
              en_jpeg(ImageOps.fit(photos[0].convert("RGB"), (200, 260)), 260),
              en_jpeg(ImageOps.fit(photos[1].convert("RGB"), (200, 260)), 260),
              en_jpeg(ImageOps.fit(affiche(api, c, "w342"), (200, 300)), 300)]
    etat = {"chaine": [{"film": a["title"], "img_f": 0, "acteur": "", "img_a": None},
                       {"film": c["title"], "img_f": 3, "acteur": "", "img_a": None}],
            "indices": [], "trous": ""}
    dev = [(x["nom"], 1), (y["nom"], 2)]

    def devoiler(k):
        etat["chaine"][k].update(acteur=dev[k][0], img_a=dev[k][1])
    evts = [(duree * 0.3, lambda: devoiler(0)), (duree * 0.5, lambda: devoiler(1))]
    depart = " · ".join(v for v in (", ".join(d["genres"][:2]), d["annee"]) if v)
    if depart:
        evts.append((duree * 0.66, lambda: etat["indices"].append(depart)))
    evts.append((duree * 0.82, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "chaine": [dict(v) for v in etat["chaine"]], "indices": list(etat["indices"])})
    m = manche_titre("hank", "dominos", duree, film, d, etapes, images, en_jpeg(affiche(api, film, "w500")), cfg)
    m["films"] = [cle_film(film)]
    m["detail"] = f"{a['title']} —{x['nom']}— {film['title']} —{y['nom']}— {c['title']}"
    return m
