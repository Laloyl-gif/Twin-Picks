"""Annie's Miss Twin Peaks (L'absente) : Annie Blackburn concourt pour Miss Twin Peaks. Sept candidates défilent, et
chacune porte une écharpe : sur l'écharpe, deux mots qui évoquent un film (ses mots-clés TMDB, en français : « requin ·
plage »). Huit affiches sont proposées : laquelle n'a pas d'écharpe ? Indice (réglable) : deux affiches qui ont leur
écharpe sont barrées à mi-temps.
"""
import random
import re

from PIL import ImageOps

from texte import normaliser
from tmdb import cle_film, fiche
from traduction import traduire
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer

NB = 8
GENERIQUES = {"based on novel or book", "duringcreditsstinger", "aftercreditsstinger", "woman director", "biography",
              "independent film", "remake", "sequel", "based on comic", "based on true story", "anime", "live action",
              "based on young adult novel", "based on play or musical", "lgbt", "friendship", "love", "murder",
              "relationship", "new york city", "family", "revenge", "duty", "death", "dying and death", "husband wife relationship",
              "father son relationship", "mother daughter relationship", "father daughter relationship", "loss of loved one",
              "based on short story", "violence", "suspense", "black and white", "sex", "nudity", "flashback"}


def _mots_cles(api, film):
    """Les mots-clés TMDB parlants du film (en anglais), sans les mots de son titre."""
    try:
        fi = fiche(api, film)
    except Exception:  # noqa: BLE001
        return []
    titre = {normaliser(m) for m in re.findall(r"\w+", film["title"] + " " + (film.get("original_title") or "")) if len(m) > 3}
    out = []
    for kw in fi.get("mots_cles", [])[:15]:
        if kw.lower() in GENERIQUES or len(kw) > 26 or any(normaliser(m) in titre for m in re.findall(r"\w+", kw)):
            continue
        out.append(kw)
        if len(out) == 3:
            break
    return out


def _traduire_tous(mots):
    """Toutes les traductions en une seule requête (une ligne par mot-clé) ; sinon une par une ; sinon l'anglais."""
    if not mots:
        return {}
    bloc = traduire("\n".join(mots), "en", "fr")
    if bloc is None:                                  # pas d'Internet : les mots-clés restent en anglais
        return {m: m for m in mots}
    lignes = [x.strip() for x in (bloc or "").split("\n")]
    if len(lignes) == len(mots) and all(lignes):
        return dict(zip(mots, lignes))
    return {m: (traduire(m, "en", "fr") or m) for m in mots}


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_annie"])
    cands = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(cands)
    films = []
    for f in cands[:40]:
        kws = _mots_cles(api, f)
        if len(kws) >= 2:
            films.append((f, kws))
        if len(films) == NB + 4:
            break
    fr = _traduire_tous(sorted({k for _, kws in films for k in kws}))
    choisis = []
    for f, kws in films:
        titre = {normaliser(m) for m in re.findall(r"\w+", f["title"]) if len(m) > 3}
        mots = []
        for k in kws:
            t = (fr.get(k) or k).strip().lower()
            if t not in mots and not any(normaliser(m) in titre for m in re.findall(r"\w+", t)):
                mots.append(t)
        txt = " · ".join(mots[:2])
        if len(mots) >= 2 and all(txt != t for _, t in choisis):
            choisis.append((f, txt))
        if len(choisis) == NB:
            break
    if len(choisis) < NB:
        raise RuntimeError("L'absente : pas assez de films avec des mots-clés dans les listes choisies.")
    absent = tirer([f for f, _ in choisis], deja)
    bonne = next(i for i, (f, _) in enumerate(choisis) if f["id"] == absent["id"])
    echarpes = [t for i, (_, t) in enumerate(choisis) if i != bonne]
    random.shuffle(echarpes)
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (200, 300)), 300) for f, _ in choisis]
    etat = {"echarpes": echarpes, "question": "Quel film n'a pas son écharpe ?",
            "items": [{"img": i, "txt": f["title"]} for i, (f, _) in enumerate(choisis)], "indices": []}
    evts = []
    if cfg.get("annie_indice", True):
        faux = random.sample([i for i in range(NB) if i != bonne], 2)
        evts.append((duree * 0.55, lambda: etat.update(
            items=[dict(it, barre=True) if i in faux else it for i, it in enumerate(etat["items"])])))
    etapes = chronologie(evts, lambda: {**etat, "items": [dict(i) for i in etat["items"]], "indices": list(etat["indices"])})
    infos = ["sans écharpe" if i == bonne else t for i, (_, t) in enumerate(choisis)]
    return dict(jeu="annie", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None, images=images,
                cles=[], bonne="", bonne_i=bonne, infos=infos, solution=f"L'absente : {absent['title']}",
                detail=" / ".join(f"{f['title']} : {t}" for f, t in choisis if f["id"] != absent["id"]),
                films=[cle_film(f) for f, _ in choisis])
