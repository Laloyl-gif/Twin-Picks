"""Traduction automatique (gratuite, sans compte) : Google Traduction (point d'accès public « gtx »), sinon MyMemory.
Sert aux répliques de films (anglais -> français) et au jeu de Catherine (le titre traduit en chaîne).
Chaque traduction est gardée dans traductions_cache.json : une phrase n'est traduite qu'une fois. Sans Internet :
None (le jeu fait sans)."""
import json
import os
import threading

import requests

FICHIER = __import__("config").donnee("traductions_cache.json")
ENTETES = {"User-Agent": "Mozilla/5.0 (TwinPicks, jeu entre amis)"}
_VERROU = threading.Lock()
_CACHE = None
_SAUVER_TOUS = 20
_NON_SAUVES = 0


def _charger():
    global _CACHE
    if _CACHE is None:
        try:
            with open(FICHIER, encoding="utf-8") as f:
                _CACHE = json.load(f)
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def sauver():
    with _VERROU:
        try:
            with open(FICHIER, "w", encoding="utf-8") as f:
                json.dump(_charger(), f, ensure_ascii=False)
        except OSError:
            pass


def _google(texte, source, cible):
    r = requests.get("https://translate.googleapis.com/translate_a/single", headers=ENTETES, timeout=8,
                     params={"client": "gtx", "sl": source or "auto", "tl": cible, "dt": "t", "q": texte})
    r.raise_for_status()
    d = r.json()
    return "".join(p[0] for p in (d[0] or []) if p and p[0]).strip()


def _mymemory(texte, source, cible):
    r = requests.get("https://api.mymemory.translated.net/get", headers=ENTETES, timeout=8,
                     params={"q": texte[:480], "langpair": f"{'en' if source in ('auto', None, '') else source}|{cible}"})
    r.raise_for_status()
    d = r.json()
    t = ((d.get("responseData") or {}).get("translatedText") or "").strip()
    if d.get("responseStatus") not in (200, "200") or "MYMEMORY WARNING" in t.upper():
        return ""
    return t


def traduire(texte, source="en", cible="fr"):
    global _NON_SAUVES
    texte = (texte or "").strip()
    if not texte or source == cible:
        return texte
    cle = f"{source}>{cible}:{texte}"
    with _VERROU:
        if cle in _charger():
            return _CACHE[cle]
    t = ""
    for f in (_google, _mymemory):
        try:
            t = f(texte, source, cible)
        except Exception:  # noqa: BLE001
            t = ""
        if t:
            break
    if not t:
        return None
    with _VERROU:
        _charger()[cle] = t
        _NON_SAUVES += 1
        a_sauver = _NON_SAUVES >= _SAUVER_TOUS
        if a_sauver:
            _NON_SAUVES = 0
    if a_sauver:
        sauver()
    return t
