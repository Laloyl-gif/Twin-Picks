"""Recherche intelligente de films sur TMDB, pour les suggestions des téléphones (Chrono, Bingo…).

N'importe quel film de TMDB peut être proposé, même s'il n'est dans aucune liste : « pulp » propose Pulp Fiction,
« seigneur » propose Le Seigneur des anneaux, « amelie » propose Le Fabuleux Destin d'Amélie Poulain.
  - deux recherches en parallèle (titres français et anglais / originaux) ;
  - si rien ne sort (faute de frappe), on recherche sur le mot le plus long puis on compare à peu près ;
  - classement : la ressemblance du titre (exact > début du titre > début d'un mot > contenu > approchant), puis la
    notoriété du film (nombre de votes), pour que le film que tout le monde connaît passe devant les homonymes.
Les résultats sont gardés en mémoire (une même saisie ne refait pas de requête).
"""
import difflib
import math
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from texte import cle
from tmdb import _film, libelle

_CACHE, _VERROU = OrderedDict(), threading.Lock()
_TAILLE_CACHE = 400
_POOL = ThreadPoolExecutor(max_workers=4)


def _requete(api, q, langue):
    try:
        d = api.get("/search/movie", query=q, language=langue, include_adult="false")
        return d.get("results") or []
    except Exception:  # noqa: BLE001
        return []


def _score_titre(qk, titre):
    k = cle(titre)
    if not k:
        return 0.0
    if k == qk:
        return 100.0
    if k.startswith(qk):
        return 82.0
    mots_q, mots = qk.split(), k.split()
    # chaque mot tapé est le début d'un mot du titre, dans l'ordre (« seigneur anneaux »)
    i = 0
    for m in mots:
        if i < len(mots_q) and m.startswith(mots_q[i]):
            i += 1
    if i == len(mots_q):
        return 68.0
    if qk in k:
        return 55.0
    return 45.0 * difflib.SequenceMatcher(None, qk, k).ratio()


def _classer(qk, resultats):
    films = {}
    for r in resultats:
        if not r.get("id") or not (r.get("title") or r.get("original_title")):
            continue
        e = films.setdefault(r["id"], {"r": r, "titres": set()})
        e["titres"].update(t for t in (r.get("title"), r.get("original_title")) if t)
    classes = []
    for e in films.values():
        r = e["r"]
        texte = max(_score_titre(qk, t) for t in e["titres"])
        if texte < 20:
            continue
        votes = r.get("vote_count") or 0
        classes.append((texte + 15 * math.log10(1 + votes) + min(5.0, (r.get("popularity") or 0) / 20), r, e["titres"],
                        texte))
    classes.sort(key=lambda x: -x[0])
    return classes


def chercher_films(api, q, n=10):
    """[{"v": « Titre (année) », "l": libellé affiché (titre original en plus s'il diffère)}], du plus probable au
    moins probable."""
    qk = cle(q)
    if len(qk) < 2:
        return []
    with _VERROU:
        if qk in _CACHE:
            _CACHE.move_to_end(qk)
            return [{"v": o["v"], "l": o["l"]} for o in _CACHE[qk][:n]]
    texte = " ".join(str(q).split())
    futurs = [_POOL.submit(_requete, api, texte, "fr-FR"), _POOL.submit(_requete, api, texte, "en-US")]
    brut = [r for f in futurs for r in f.result()]
    if not brut:                                       # faute de frappe : on cherche le mot le plus long
        mots = sorted((m for m in qk.split() if len(m) >= 3), key=len, reverse=True)
        for m in mots[:2]:
            brut = _requete(api, m, "fr-FR") + _requete(api, m, "en-US")
            if brut:
                break
    out, vus = [], set()
    for _, r, titres, texte_score in _classer(qk, brut):
        f = _film(dict(r, media_type="movie"))
        lib = libelle(f)
        if lib in vus:
            continue
        vus.add(lib)
        autre = next((t for t in titres if cle(t) != cle(f["title"])), None)
        out.append({"v": lib, "l": lib + (f"  ({autre})" if autre else ""), "film": f, "texte": texte_score})
    with _VERROU:
        _CACHE[qk] = out
        while len(_CACHE) > _TAILLE_CACHE:
            _CACHE.popitem(last=False)
    return [{"v": o["v"], "l": o["l"]} for o in out[:n]]


def meilleur_film(api, q):
    """Le film le plus probable pour une saisie partielle (« pulp » -> Pulp Fiction), ou None si rien de net."""
    qk = cle(q)
    if len(qk) < 3:
        return None
    chercher_films(api, q)
    with _VERROU:
        res = _CACHE.get(qk) or []
    return res[0]["film"] if res and res[0]["texte"] >= 60 else None
