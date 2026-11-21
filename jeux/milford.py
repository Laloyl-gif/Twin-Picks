"""Mayor Milford's Golden Owl (Le Hibou d'or) : le maire Dwayne Milford, qui préside l'élection de Miss Twin Peaks,
remet ce soir le Hibou d'or : l'« Oscar » des joueurs eux-mêmes. Chaque enveloppe nomme cinq films notés par TOUS
les profils présents (on est l'académie) : lequel a été sacré dans la catégorie ? Meilleur film (la meilleure
moyenne), le plus clivant (le plus gros écart de notes), le plus sous-coté (au-dessus de TMDB), le plus surcoté, le
Hibou de plomb (la plus basse moyenne). Les nommés ont des valeurs proches (c'est plus dur) et jamais d'égalité.
"""
import random

from PIL import ImageOps

from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche

# (titre, critère, valeur à maximiser, valeur minimale du lauréat pour que la catégorie ait un sens)
CATEGORIES = [
    ("Hibou d'or du meilleur film", "la meilleure moyenne de vos notes", lambda s: s["moy"], -99),
    ("Hibou d'or du film le plus clivant", "le plus gros écart entre vos notes", lambda s: s["ecart"], 1.5),
    ("Hibou d'or du film le plus sous-coté", "vos notes, bien au-dessus de la note TMDB", lambda s: s["moy"] - s["tmdb"], 0.5),
    ("Hibou d'or du film le plus surcoté", "vos notes, bien en dessous de la note TMDB", lambda s: s["tmdb"] - s["moy"], 0.5),
    ("Hibou de plomb", "la plus basse moyenne de vos notes", lambda s: -s["moy"], -99),
]


def construire(api, cfg, pool, deja):
    presents = sorted({p["nom"] for p in cfg.get("_profils", []) if p.get("notes")})
    if len(presents) < 2:
        raise RuntimeError("Le Hibou d'or : il faut au moins 2 joueurs présents avec des notes (profils).")
    films = [f for f in pool if not f.get("tv") and set(presents) <= set(f["notes"]) and f.get("poster_path")]
    if len(films) < 8:
        raise RuntimeError("Le Hibou d'or : pas assez de films notés par tous les joueurs présents.")
    stats = {}
    for f in films:
        ns = [float(f["notes"][p]) for p in presents]
        stats[cle_film(f)] = {"moy": sum(ns) / len(ns), "ecart": max(ns) - min(ns), "tmdb": float(f.get("note") or 0),
                              "notes": {p: f["notes"][p] for p in presents}}
    n = max(2, int(cfg.get("milford_n", 5)))
    cats = CATEGORIES[:]
    random.shuffle(cats)
    if not cfg.get("_tmdb_ok", True):
        cats = [c for c in cats if "TMDB" not in c[1]]
    images, envs, utilises = [], [], set()
    for titre, crit, val, mini in (cats * 2)[:n * 2]:
        if len(envs) == n:
            break
        lot = [f for f in films if cle_film(f) not in utilises]
        if "TMDB" in crit:
            lot = [f for f in lot if stats[cle_film(f)]["tmdb"] > 0]
        lot.sort(key=lambda f: -val(stats[cle_film(f)]))
        fenetres = []
        for i in range(0, max(0, len(lot) - 4)):
            w = lot[i:i + 5]
            vs = [round(val(stats[cle_film(f)]), 2) for f in w]
            if vs[0] > vs[1] and vs[0] >= mini:                       # un seul lauréat : pas d'égalité en tête
                fenetres.append((vs[0] - vs[-1], i, w))
        if not fenetres:
            continue
        fenetres.sort(key=lambda x: x[0])                           # les plus serrées d'abord
        _, _, w = random.choice(fenetres[:max(1, len(fenetres) // 3)])
        gagnant = w[0]
        ordre = w[:]
        random.shuffle(ordre)
        items, infos = [], []
        for f in ordre:
            images.append(en_jpeg(ImageOps.fit(affiche(api, f, "w185"), (160, 240)), 240))
            items.append({"img": len(images) - 1, "txt": f["title"]})
            s = stats[cle_film(f)]
            det = " · ".join(f"{p} {v}" for p, v in s["notes"].items())
            plus = (f" · TMDB {s['tmdb']:.1f}" if "TMDB" in crit else f" · écart {s['ecart']:g}" if "écart" in crit else "")
            infos.append((f"moyenne {s['moy']:.1f}" + plus).replace(".", ",") + f" ({det})")
        for f in w:
            utilises.add(cle_film(f))
        env = {"titre": titre, "sous": crit, "items": items, "bonne": ordre.index(gagnant), "infos": infos,
               "question": f"Le {titre} est attribué à…" if not titre.startswith("Hibou de plomb") else "Le Hibou de plomb est attribué à…"}
        env["simple"] = {"items": items, "bonne": env["bonne"]}         # cinq nommés pour tout le monde
        envs.append(env)
        deja.add(cle_film(gagnant))
    if len(envs) < 2:
        raise RuntimeError("Le Hibou d'or : pas assez de films pour des catégories sans égalité.")
    D, R = float(cfg.get("milford_dur", 15)), 5.0
    t0 = 2.0
    return dict(jeu="milford", vue="ceremonie", duree=round(t0 + len(envs) * (D + R), 1), reponse="enveloppes",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[],
                bonne="", solution="Le palmarès du Hibou d'or", detail="", films=[], enveloppes=envs,
                dur_question=D, dur_revelation=R, t0=t0, pts=int(cfg.get("milford_pts", 500)), bonus=0,
                hote_nom="Dwayne Milford", signature=tuple(e["titre"] + str(e["bonne"]) for e in envs))
