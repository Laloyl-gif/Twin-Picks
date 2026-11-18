"""Phillip's Associates (Les complices) : « Qui crois-tu que c'est, celui-là ? » demande Phillip Jeffries. Ici, une
personne mystère (un acteur de acteurs.txt ou un réalisateur du fichier) se devine à ses complices : les gens avec qui
elle a le plus tourné (acteurs et réalisateurs), qui arrivent un par un, du moins fréquent au plus fréquent, avec le
nombre de films faits ensemble. Son nom en blancs à la fin. Trouvez la personne.
"""
import random
from collections import Counter

from PIL import ImageOps

from tmdb import charger_acteurs, fiche, filmographie
from texte import est_latin
from visuels import en_jpeg
from .commun import chronologie, cles_reponses, tirer, trous
from .contraintes import realisateurs_fichier


def complices(api, pid, realisateur, nmax=6):
    films = filmographie(api, pid, "Director" if realisateur else None)[:14]
    compte, qui, ensemble = Counter(), {}, {}
    for f in sorted(films, key=lambda x: -x.get("votes", 0)):
        try:
            fi = fiche(api, dict(f, tv=False))
        except Exception:  # noqa: BLE001
            continue
        for a in fi["acteurs"][:8]:
            if a["id"] != pid:
                compte[a["id"]] += 1
                qui.setdefault(a["id"], {"nom": a["nom"], "photo": a.get("photo"), "metier": "acteur"})
                ensemble.setdefault(a["id"], f)                          # leur film commun le plus connu
        for r in fi["realisateurs"][:2]:
            if r["id"] != pid:
                compte[r["id"]] += 1
                qui.setdefault(r["id"], {"nom": r["nom"], "photo": None, "metier": "réalisateur"})
                ensemble.setdefault(r["id"], f)
    top = [(i, n) for i, n in compte.most_common(nmax * 2) if n >= 2][:nmax]
    return [dict(qui[i], n=n, id=i, film=ensemble.get(i)) for i, n in top], films


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_phillip"])
    for _ in range(10):
        real = random.random() * 100 < float(cfg.get("phillip_realisateurs", 25))
        if real:
            gens = [{"id": p["id"], "name": p["name"], "profile_path": p.get("profile_path")} for p in realisateurs_fichier(api, cfg)]
        else:
            gens = list(pool or charger_acteurs(api))
        if not gens:
            continue
        p = tirer(gens, deja, ident=lambda x: ("personne", x["id"]))
        try:
            liste, films = complices(api, p["id"], real)
        except Exception:  # noqa: BLE001
            continue
        if len(liste) >= 4:
            break
    else:
        raise RuntimeError("Les complices : pas assez de collaborateurs fréquents trouvés.")
    liste = list(reversed(liste))                         # du moins fréquent au plus fréquent
    photos = [api.image(c["photo"], "w185") if c.get("photo") else None for c in liste]
    images, items = [], []
    for c, ph in zip(liste, photos):
        if ph is not None:
            images.append(en_jpeg(ImageOps.fit(ph.convert("RGB"), (200, 260)), 260))
        items.append({"nom": c["nom"], "n": c["n"], "metier": c["metier"], "img": len(images) - 1 if ph is not None else None})
    n = len(items)
    # Pas toujours (le jeu garde son sens) : un ou deux complices disent aussi un film fait ensemble, en indice
    if random.random() < float(cfg.get("phillip_lien", 60)) / 100:
        for k in random.sample(range(n), min(n, random.choice((1, 2)))):
            f = liste[k].get("film")
            if f:
                items[k]["film"] = f.get("title", "")
                if f.get("poster_path"):                 # la petite affiche du film, à côté du complice
                    try:
                        images.append(en_jpeg(ImageOps.fit(api.image(f["poster_path"], "w154").convert("RGB"), (120, 180)), 180))
                        items[k]["img_f"] = len(images) - 1
                    except Exception:  # noqa: BLE001
                        pass
    etat = {"complices": [], "total": n, "metier": "Réalisateur" if real else "Acteur ou actrice", "trous": ""}
    evts = [(round(duree * 0.72 * k / max(1, n - 1), 2), lambda k=k: etat.update(complices=items[:k + 1])) for k in range(n)]
    evts.append((duree * 0.85, lambda: etat.update(trous=trous(p["name"], 0))))
    etapes = chronologie(evts, lambda: {**etat, "complices": [dict(x) for x in etat["complices"]]})
    noms = [p["name"]]
    try:
        noms += [x for x in api.get(f"/person/{p['id']}").get("also_known_as", []) if est_latin(x)]
    except Exception:  # noqa: BLE001
        pass
    mots = [m for m in p["name"].split() if m.lower().strip(".,") not in ("jr", "sr", "ii", "iii")]
    if len(mots) > 1:
        noms.append(mots[-1])
    rev = None
    if p.get("profile_path"):
        rev = en_jpeg(ImageOps.fit(api.image(p["profile_path"], "h632").convert("RGB"), (420, 560)))
    return dict(jeu="phillip", vue="complices", duree=duree, etapes=etapes, images=images, revelation=rev,
                reponse="titre", pool="acteurs", cles=cles_reponses(*noms), bonne=p["name"], solution=p["name"],
                detail=", ".join(f["title"] for f in films[:3]))
