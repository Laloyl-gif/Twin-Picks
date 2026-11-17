"""Sagas (collections TMDB) : « Harry Potter à l'école des sorciers » appartient à la saga « Harry Potter ».

Dans les jeux où il faut deviner un film, le nom de la saga suffit (et c'est lui qui s'affiche).
Les listes TMDB ne disent pas à quelle saga appartient un film : l'information est lue avec les détails du film
puis gardée dans sagas_cache.json. Au lancement d'une partie, les films des listes encore inconnus sont lus en
arrière-plan (une seule fois : le cache sert aux parties suivantes).

Univers : quelques sagas distinctes qui racontent le même monde (Terre du Milieu, Wizarding World…), et les
studios qui en sont un à eux seuls (Marvel Studios, DC), pour ne pas mettre deux films du même univers
côte à côte dans Leland's Smile.
"""
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from texte import cle, normaliser

FICHIER = __import__("config").donnee("sagas_cache.json")
_VERROU = threading.RLock()
_CACHE = None                 # {"m:120": [119, "Le Seigneur des anneaux"] ou 0 (pas de saga)}
_SALE = [False, 0.0]          # modifié ? / dernière sauvegarde
_EN_COURS = set()

# Sagas distinctes d'un même univers (identifiants de collections TMDB)
UNIVERS_SAGAS = {119: "terre-du-milieu", 121938: "terre-du-milieu", 1241: "wizarding", 435259: "wizarding",
                 556: "spider-man", 125574: "spider-man", 531241: "spider-man", 573436: "spider-man"}
# Studios qui forment un univers (identifiants de sociétés de production TMDB)
UNIVERS_STUDIOS = {420: "marvel", 9993: "dc", 128064: "dc", 429: "dc", 1: "lucasfilm"}

_SUFFIXE = re.compile(r"\s*[-–:]?\s*\(?\b(la |the )?(saga|collection|trilogie|trilogy|anthologie)\)?\s*$", re.I)
_PREFIXE = re.compile(r"^(la |the )?(saga|collection|trilogie|trilogy)\s+(de |des |du |d'|of )?", re.I)


def nom_propre(nom):
    """« Harry Potter - Saga » -> « Harry Potter »."""
    n = " ".join(str(nom or "").split())
    for _ in range(2):
        n = _SUFFIXE.sub("", n).strip(" -–:")
        n = _PREFIXE.sub("", n).strip(" -–:")
    return n or str(nom or "").strip()


def _charger():
    global _CACHE
    if _CACHE is None:
        try:
            with open(FICHIER, encoding="utf-8") as f:
                brut = json.load(f)
            _CACHE = brut if isinstance(brut, dict) else {}
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def sauver(force=False):
    with _VERROU:
        if not _SALE[0] or (not force and time.time() - _SALE[1] < 5):
            return
        try:
            with open(FICHIER, "w", encoding="utf-8") as f:
                json.dump(_charger(), f, ensure_ascii=False)
            _SALE[:] = [False, time.time()]
        except OSError:
            pass


def _cle(f):
    return "%s:%s" % ("tv" if f.get("tv") else "m", f["id"])


def noter(f, collection):
    """Mémorise la saga d'un film (collection = dict TMDB « belongs_to_collection » ou None)."""
    if f.get("tv"):
        return
    with _VERROU:
        val = [int(collection["id"]), nom_propre(collection.get("name"))] if collection and collection.get("id") else 0
        c = _charger()
        if c.get(_cle(f)) != val:
            c[_cle(f)] = val
            _SALE[0] = True
    sauver()


def saga(f):
    """(id, nom) de la saga du film ; None s'il n'en a pas ; False si on ne sait pas encore."""
    if f.get("tv"):
        return None
    with _VERROU:
        v = _charger().get(_cle(f), False)
    if v is False:
        return False
    return tuple(v) if v else None


def nom(f):
    s = saga(f)
    return s[1] if s else ""


def taille():
    with _VERROU:
        return len(_charger())


def prechauffer(api, films, maxi=1500):
    """Lit en arrière-plan la saga des films encore inconnus (une requête par film, gardée dans le cache)."""
    inconnus = [f for f in films if not f.get("tv") and saga(f) is False and _cle(f) not in _EN_COURS][:maxi]
    if not inconnus:
        return
    with _VERROU:
        _EN_COURS.update(_cle(f) for f in inconnus)

    def lire(f):
        try:
            d = api.get(f"/movie/{f['id']}")
            noter(f, d.get("belongs_to_collection"))
        except Exception:  # noqa: BLE001
            pass
        finally:
            with _VERROU:
                _EN_COURS.discard(_cle(f))

    def tout():
        with ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(lire, inconnus))
        sauver(force=True)

    threading.Thread(target=tout, daemon=True).start()


# ---------------- même saga / même univers ----------------
_NUMERO = re.compile(r"\s+(\d+|i{1,3}|iv|v|vi{0,3}|ix|x)$")


def racines(f):
    """Titre « de base » d'un film : avant les deux-points, sans numéro (« spider man », « avengers »)."""
    out = set()
    for t in (f.get("title"), f.get("original_title")):
        if not t:
            continue
        base = re.split(r"\s*[:–]\s+|\s+-\s+", t)[0]
        r = _NUMERO.sub("", cle(base))
        if len(r) >= 5 or " " in r:
            out.add(r)
    return out


def titres_normalises(f):
    return {f" {normaliser(t)} " for t in (f.get("title"), f.get("original_title")) if t}


def cles_univers(f, fi=None):
    """Sagas et univers connus d'un film (fi : sa fiche, si elle a été lue)."""
    out = set()
    s = saga(f)
    if fi and fi.get("collection_id"):
        s = (fi["collection_id"], fi.get("collection"))
    if s:
        out.add(f"saga:{s[0]}")
        if s[0] in UNIVERS_SAGAS:
            out.add("univers:" + UNIVERS_SAGAS[s[0]])
    for soc in (fi or {}).get("societes") or []:
        if soc in UNIVERS_STUDIOS:
            out.add("univers:" + UNIVERS_STUDIOS[soc])
    return out


def meme_univers(a, b, fa=None, fb=None):
    """Vrai si deux films sont de la même saga, du même univers, ou si le titre de l'un contient l'autre
    (« Spider-Man » / « The Amazing Spider-Man 2 »)."""
    if a.get("id") == b.get("id") and a.get("tv") == b.get("tv"):
        return True
    if cles_univers(a, fa) & cles_univers(b, fb):
        return True
    ta, tb = titres_normalises(a), titres_normalises(b)
    return any(f" {r} " in t for r in racines(a) for t in tb) or any(f" {r} " in t for r in racines(b) for t in ta)
