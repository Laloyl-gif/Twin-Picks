"""Hank's Dominoes (L'effet domino) : Hank Jennings aligne ses dominos. Douze affiches sont debout comme des dominos ;
un seul est le film mystère. Hank donne ses indices un par un (le genre, l'époque, la durée, la note, le pays, puis un
acteur ou le réalisateur) : à chaque indice, les films qui ne collent pas tombent. Répondez quand vous voulez en
touchant une affiche : plus tôt on répond, plus ça rapporte (mais il reste plus de dominos debout).
"""
import random

from PIL import ImageOps

import sagas
from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer

NB = 12


def _criteres(fi, an):
    """Les indices vrais pour le film mystère : [(texte, test(fiche, année) -> bool, finesse)]."""
    out = []
    for g in fi.get("genres", [])[:3]:
        out.append((f"Genre : {g.lower()}", lambda x, a, g=g: g in x.get("genres", []), 1))
    if an:
        dec = an // 10 * 10
        out.append((f"Sorti dans les années {dec % 100:02d}" if dec >= 1930 else f"Sorti dans les années {dec}",
                    lambda x, a, dec=dec: a and a // 10 * 10 == dec, 2))
        out.append(("Sorti après l'an 2000" if an > 2000 else "Sorti avant l'an 2000",
                    lambda x, a, apres=an > 2000: a and (a > 2000) == apres, 1))
    d = fi.get("duree") or 0
    if d:
        if d >= 120:
            out.append(("Dure plus de 2 h", lambda x, a: (x.get("duree") or 0) >= 120, 1))
        elif d < 100:
            out.append(("Dure moins de 1 h 40", lambda x, a: 0 < (x.get("duree") or 0) < 100, 1))
        else:
            out.append(("Dure entre 1 h 40 et 2 h", lambda x, a: 100 <= (x.get("duree") or 0) < 120, 1))
    n = fi.get("note") or 0
    if n:
        s = 7.5 if n >= 7.5 else 6.5 if n >= 6.5 else 0
        if s:
            out.append((f"Noté au moins {str(s).replace('.', ',')}/10 sur TMDB", lambda x, a, s=s: (x.get("note") or 0) >= s, 1))
        else:
            out.append(("Noté moins de 6,5/10 sur TMDB", lambda x, a: 0 < (x.get("note") or 0) < 6.5, 1))
    if fi.get("pays"):
        p = fi["pays"][0]
        out.append((f"Produit en partie par : {p}", lambda x, a, p=p: p in x.get("pays", []), 2))
    if fi.get("langue"):
        lg = fi["langue"]
        out.append(("Tourné en anglais" if lg == "en" else "Pas tourné en anglais",
                    lambda x, a, en=lg == "en": (x.get("langue") == "en") == en, 1))
    for a in fi.get("acteurs", [])[:3]:
        out.append((f"Avec {a['nom']}", lambda x, an_, i=a["id"]: any(b["id"] == i for b in x.get("acteurs", [])[:12]), 4))
    for r in fi.get("realisateurs", [])[:1]:
        out.append((f"Réalisé par {r['nom']}", lambda x, a, i=r["id"]: any(b["id"] == i for b in x.get("realisateurs", [])), 5))
    return out


def _annee(f):
    try:
        return int((f.get("release_date") or "")[:4])
    except ValueError:
        return 0


def sequence(cible, autres):
    """Les indices dans l'ordre : chacun fait tomber au moins un domino, les plus vagues d'abord ; à la fin, il ne
    reste que le film mystère. [(texte, [indices des autres qui tombent])] ou None."""
    fc, ac = cible
    crit = [c for c in _criteres(fc, ac) if c[1](fc, ac)]
    debout = set(range(len(autres)))
    seq = []
    while debout and crit and len(seq) < 7:
        options = []
        for c in crit:
            tombe = {i for i in debout if not c[1](*autres[i])}
            if tombe:
                options.append((c, tombe))
        if not options:
            return None
        reste = 7 - len(seq)
        # assez fin pour finir à temps, sinon le plus doux (un à trois dominos) et le plus vague
        if len(debout) > 3 * reste:
            c, tombe = max(options, key=lambda o: (len(o[1]), -o[0][2]))
        else:
            doux = [o for o in options if len(o[1]) <= max(1, len(debout) // 2)]
            c, tombe = min(doux or options, key=lambda o: (o[0][2], -len(o[1]), random.random()))
        seq.append((c[0], sorted(tombe)))
        debout -= tombe
        crit.remove(c)
    return seq if not debout and len(seq) >= 3 else None


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_hank"])
    films = [f for f in pool if f.get("poster_path")]
    for _ in range(12):
        cible = tirer(films, deja)
        autres = [f for f in films if f["id"] != cible["id"] and not sagas.meme_univers(f, cible)]
        random.shuffle(autres)
        fiches = []
        for f in autres[:40]:
            try:
                fiches.append((f, fiche(api, f)))
            except Exception:  # noqa: BLE001
                continue
            if len(fiches) == NB - 1:
                break
        try:
            fcible = fiche(api, cible)
        except Exception:  # noqa: BLE001
            continue
        if len(fiches) < NB - 1:
            continue
        seq = sequence((fcible, _annee(cible)), [(fi, _annee(f)) for f, fi in fiches])
        if seq:
            break
    else:
        raise RuntimeError("L'effet domino : impossible de trouver des indices qui départagent les films des listes.")
    films_m = [f for f, _ in fiches] + [cible]
    ordre = random.sample(range(NB), NB)                       # position à l'écran -> film
    films_m = [films_m[i] for i in ordre]
    bonne = ordre.index(NB - 1)
    pos = {ordre.index(k): k for k in range(NB)}               # position -> indice dans « fiches » (ou la cible)
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (240, 360)), 360) for f in films_m]
    etat = {"items": [{"img": i, "txt": f["title"]} for i, f in enumerate(films_m)], "regles": [],
            "question": "Quel est le film de Hank ?", "indices": []}
    n = len(seq)
    evts = []
    for k, (txt, tombe) in enumerate(seq):
        t = round(duree * (0.04 + 0.78 * k / max(1, n - 1)), 2)
        cases = [p for p, i in pos.items() if i in tombe]

        def jouer(txt=txt, cases=cases):
            etat["regles"].append(txt)
            for p in cases:
                etat["items"][p]["tombe"] = True
        evts.append((t, jouer))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]], "regles": list(etat["regles"]),
                                        "indices": list(etat["indices"])})
    for f in films_m:
        deja.add(cle_film(f))
    return dict(jeu="hank", vue="choix", duree=duree, reponse="choix", etapes=etapes, images=images, revelation=None,
                cles=[], bonne="", bonne_i=bonne, infos=[""] * NB, solution=f"Le film de Hank : {cible['title']}",
                detail=" · ".join(t for t, _ in seq), films=[cle_film(f) for f in films_m])
