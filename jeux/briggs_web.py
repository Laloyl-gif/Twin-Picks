"""Sources précises pour Major Briggs : Wikidata et Wikipédia (gratuits, sans clé).

Pour un film : son identifiant Wikidata (via TMDB), puis
  - Wikidata : les personnages (P674), les lieux de l'action (P840), le sujet principal (P921), l'époque (P2408) ;
  - Wikipédia (français, sinon anglais) : la section « Synopsis » / « Résumé » / « Plot », d'où l'on tire les noms
    propres qui reviennent (personnages, lieux inventés : l'hôtel Overlook…) et les détails chiffrés
    (« chambre 237 », « vol 815 »).
Tout est gardé dans briggs_cache.json : un film n'est lu sur le web qu'une fois. Sans Internet, rien ne casse :
le jeu se contente des mots-clés TMDB et du résumé.
"""
import json
import os
import re
import threading

import requests

FICHIER = __import__("config").donnee("briggs_cache.json")
VERSION = 2
ENTETES = {"User-Agent": "TwinPicks/1.0 (jeu de quiz entre amis ; usage personnel)"}
DELAI = 8
_VERROU = threading.Lock()
_CACHE = None

SECTIONS_FR = ("synopsis", "résumé", "resume", "intrigue", "histoire", "scénario", "scenario", "argument")
SECTIONS_EN = ("plot", "synopsis", "story", "premise")


def _charger():
    global _CACHE
    if _CACHE is None:
        try:
            with open(FICHIER, encoding="utf-8") as f:
                brut = json.load(f)
            _CACHE = brut.get("films", {}) if isinstance(brut, dict) and brut.get("v") == VERSION else {}
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def _sauver():
    try:
        with open(FICHIER, "w", encoding="utf-8") as f:
            json.dump({"v": VERSION, "films": _CACHE}, f, ensure_ascii=False)
    except OSError:
        pass


def _get(url, **params):
    r = requests.get(url, params=params, headers=ENTETES, timeout=DELAI)
    r.raise_for_status()
    return r.json()


def _labels(ids):
    """Libellés (français, sinon anglais) d'entités Wikidata."""
    out = {}
    ids = [i for i in dict.fromkeys(ids) if i]
    for k in range(0, len(ids), 40):
        d = _get("https://www.wikidata.org/w/api.php", action="wbgetentities", ids="|".join(ids[k:k + 40]),
                 props="labels", languages="fr|en", format="json")
        for q, e in (d.get("entities") or {}).items():
            lab = e.get("labels") or {}
            v = (lab.get("fr") or lab.get("en") or {}).get("value")
            if v:
                out[q] = v
    return out


def _valeurs(claims, prop):
    out = []
    for c in claims.get(prop) or []:
        v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if isinstance(v, dict) and v.get("id"):
            out.append(v["id"])
    return out


def _section(texte, noms):
    """La section du résumé dans un article en texte brut (titres « == Synopsis == »)."""
    morceaux = re.split(r"\n(={2,4})\s*([^=\n]+?)\s*\1\n", "\n" + texte)
    # morceaux : [intro, '==', titre1, contenu1, '==', titre2, contenu2, …]
    for i in range(1, len(morceaux) - 2, 3):
        titre = morceaux[i + 1].strip().lower()
        if any(titre.startswith(n) for n in noms):
            contenu = morceaux[i + 2]
            # sous-sections éventuelles : on garde tout jusqu'au prochain titre de même niveau
            j = i + 3
            while j < len(morceaux) - 2 and len(morceaux[j]) > len(morceaux[i]):
                contenu += "\n" + morceaux[j + 2]
                j += 3
            return contenu.strip()
    return ""


def _article(langue, titre, noms):
    d = _get(f"https://{langue}.wikipedia.org/w/api.php", action="query", prop="extracts", explaintext=1,
             redirects=1, titles=titre, format="json")
    for page in (d.get("query") or {}).get("pages", {}).values():
        texte = page.get("extract") or ""
        s = _section(texte, noms)
        if s:
            return s
    return ""


def infos(api, film):
    """{"personnages": [...], "lieux": [...], "sujets": [...], "epoque": [...], "intrigue": texte, "langue": "fr"|"en"}
    (vide si rien n'a été trouvé ou sans Internet). Lu une fois, puis gardé dans briggs_cache.json."""
    k = f"{'tv' if film.get('tv') else 'm'}:{film['id']}"
    with _VERROU:
        if k in _charger():
            return _CACHE[k]
    res = {"personnages": [], "lieux": [], "sujets": [], "epoque": [], "intrigue": "", "langue": ""}
    ok = False
    try:
        kind = "tv" if film.get("tv") else "movie"
        q = (api.get(f"/{kind}/{film['id']}/external_ids") or {}).get("wikidata_id")
        if q:
            ent = (_get(f"https://www.wikidata.org/wiki/Special:EntityData/{q}.json").get("entities") or {}).get(q) or {}
            claims = ent.get("claims") or {}
            p674, p840, p921, p2408 = (_valeurs(claims, p) for p in ("P674", "P840", "P921", "P2408"))
            lab = _labels(p674[:25] + p840[:8] + p921[:6] + p2408[:3])
            res.update(personnages=[lab[i] for i in p674[:25] if i in lab], lieux=[lab[i] for i in p840[:8] if i in lab],
                       sujets=[lab[i] for i in p921[:6] if i in lab], epoque=[lab[i] for i in p2408[:3] if i in lab])
            liens = ent.get("sitelinks") or {}
            for langue, noms in (("fr", SECTIONS_FR), ("en", SECTIONS_EN)):
                titre = (liens.get(f"{langue}wiki") or {}).get("title")
                if not titre:
                    continue
                texte = _article(langue, titre, noms)
                if len(texte) > 200:
                    res.update(intrigue=texte[:12000], langue=langue)
                    break
        ok = True
    except Exception:  # noqa: BLE001  (pas d'Internet, Wikipédia injoignable… : on réessaiera une autre fois)
        ok = False
    if ok:
        with _VERROU:
            _charger()[k] = res
            _sauver()
    return res
