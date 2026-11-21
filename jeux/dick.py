"""Dick Tremayne's Gala (La cérémonie) : Dick Tremayne, en smoking, présente la soirée et ouvre les enveloppes.
« Et l'Oscar du meilleur film est attribué à… » (ou le César, la Palme d'or, le BAFTA, le Golden Globe, le Lion
d'or…) : les vrais nommés de cette année-là s'affichent, chacun choisit le lauréat sur son téléphone pendant le
roulement de tambour, et plus on est rapide, plus on gagne. Chaque enveloppe part d'un film des listes.
Récompenses : Wikidata (voir recompenses.py).

Difficulté : les joueurs « experts » (réglage, Louison par défaut) ont, pour les Oscars, une version plus dure : pas
d'année affichée, tous les nommés (ou : trouver l'intrus qui n'était pas nommé), puis une question bonus sur l'année
de la cérémonie. Les autres récompenses, et les autres joueurs, gardent la version simple (quatre choix au plus).
"""
import random
import re
import time

from PIL import ImageOps

import recompenses
from texte import cle
from tmdb import cle_film
from visuels import en_jpeg
from .commun import affiche
from .enveloppes import experts_de, simplifier


def _film_tmdb(api, ident):
    try:
        d = api.get(f"/movie/{ident}")
    except Exception:  # noqa: BLE001
        return None
    if not d or not d.get("poster_path"):
        return None
    return {"id": ident, "title": d.get("title") or d.get("original_title") or "?", "poster_path": d["poster_path"],
            "release_date": d.get("release_date") or "", "tv": False, "original_title": d.get("original_title")}


def _annonce(nom):
    """« Et l'Oscar du meilleur film est attribué à… », « Et la Palme d'or est attribuée à… »."""
    fem = re.match(r"(palme|coquille|caméra|camera)", nom, re.I)
    art = "l'" if re.match(r"[aeiouyéèh]", nom, re.I) else ("la " if fem else "le ")
    return f"Et {art}{nom} est attribué{'e' if fem else ''} à…"


def _annees(a):
    autres = [x for x in range(a - 7, a + 8) if x != a]
    random.shuffle(autres)
    choix = sorted([a] + autres[:5])
    return choix, choix.index(a)


def construire(api, cfg, pool, deja):
    n = max(2, int(cfg.get("dick_n", 6)))
    films = [f for f in pool if not f.get("tv")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    presents = {cle(p["nom"]) for p in cfg.get("_profils", [])}
    experts_presents = bool(experts_de(cfg) & presents)
    candidats, vus, t0 = [], set(), time.time()
    for f in films[:80]:
        if time.time() - t0 > 40 or len(candidats) >= n * 2:
            break
        for r in recompenses.de_film(api, f):
            if r["film"] and r["annee"] and (r["id"], r["annee"]) not in vus:
                vus.add((r["id"], r["annee"]))
                candidats.append((r, f))
    random.shuffle(candidats)
    candidats.sort(key=lambda x: -x[0]["prestige"] + random.random() * 3)
    images, envs, oscars = [], [], 0
    for r, f in candidats:
        if len(envs) == n:
            break
        noms = recompenses.nommes(api, r["id"], r["annee"])
        gagnants = [x for x in noms if x["gagne"]]
        if len(gagnants) != 1 or len(noms) < 3:
            continue
        autres = [x for x in noms if not x["gagne"]]
        random.shuffle(autres)
        lot = gagnants + autres[:7]
        films_env = []
        for x in lot:
            fx = _film_tmdb(api, x["tmdb"])
            if fx:
                films_env.append((x, fx))
        if not films_env or not films_env[0][0]["gagne"] or len(films_env) < 3:
            continue
        random.shuffle(films_env)
        items = []
        for x, fx in films_env:
            images.append(en_jpeg(ImageOps.fit(affiche(api, fx, "w185"), (160, 240)), 240))
            items.append({"img": len(images) - 1, "txt": fx["title"]})
        bonne = next(i for i, (x, _) in enumerate(films_env) if x["gagne"])
        env = {"titre": r["nom"], "sous": f"Cérémonie de {r['annee']}", "items": items, "bonne": bonne,
               "infos": ["Lauréat" if x["gagne"] else "Nommé" for x, _ in films_env],
               "question": _annonce(r["nom"]),
               "ceremonie": r["ceremonie"]}
        simplifier(env)
        if r["ceremonie"] == "Oscars" and experts_presents:
            annees, ba = _annees(r["annee"])
            if oscars % 2 == 0 or len(films_env) < 5:              # tous les nommés, sans l'année
                env["experts"] = {"items": items, "bonne": bonne, "question": f"{r['nom']} : qui a gagné ?",
                                  "annees": annees, "bonne_annee": ba}
            else:                                                  # l'intrus qui n'était pas nommé
                titres = {cle(it["txt"]) for it in items}
                intrus = next((g for g in films if g.get("poster_path") and cle(g["title"]) not in titres and
                               abs(int((g.get("release_date") or "0")[:4] or 0) - r["annee"]) <= 2), None)
                if intrus:
                    images.append(en_jpeg(ImageOps.fit(affiche(api, intrus, "w185"), (160, 240)), 240))
                    vrais = random.sample(items, min(5, len(items)))
                    lst = vrais + [{"img": len(images) - 1, "txt": intrus["title"]}]
                    random.shuffle(lst)
                    env["experts"] = {"items": lst, "bonne": next(i for i, it in enumerate(lst) if it["txt"] == intrus["title"]),
                                      "question": f"{r['nom']} : lequel n'était PAS nommé ?", "annees": annees,
                                      "bonne_annee": ba}
                    env["cacher_items"] = True
            env["cacher_sous"] = True
            oscars += 1
        envs.append(env)
        deja.add(cle_film(f))
    if len(envs) < 2:
        raise RuntimeError("La cérémonie : pas assez de films récompensés dans les listes (ou pas d'accès à Wikidata).")
    D, R = float(cfg.get("dick_dur", 15)), 4.0
    t0 = 2.0
    duree = t0 + len(envs) * (D + R)
    return dict(jeu="dick", vue="ceremonie", duree=round(duree, 1), reponse="enveloppes",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[],
                bonne="", solution="Le palmarès de la soirée", detail="", films=[], enveloppes=envs,
                dur_question=D, dur_revelation=R, t0=t0, pts=int(cfg.get("dick_pts", 500)),
                bonus=int(cfg.get("dick_bonus", 300)), avec_experts=True, hote_nom="Dick Tremayne",
                signature=tuple(e["titre"] + e["sous"] for e in envs))
