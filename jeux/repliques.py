"""Répliques de films, tirées de Wikiquote (gratuit, sans clé) : pour le Géant (trois répliques pour trouver le film)
et pour Maddy (qui a dit cette réplique ?).

Pour un film : son identifiant Wikidata (via TMDB), la page Wikiquote liée (français d'abord, sinon anglais), puis
le texte de la page : les répliques sont les lignes « * … » ; le personnage qui parle est le titre de la section
(« === Hannibal Lecter === ») ou le nom en gras d'un dialogue (« :'''Clarice:''' … »).
Tout est gardé dans repliques_cache.json : une page n'est lue qu'une fois. Sans Internet : aucune réplique (le jeu
passe à un autre film, puis abandonne proprement).
"""
import json
import os
import re
import threading

import requests

from texte import normaliser

FICHIER = __import__("config").donnee("repliques_cache.json")
VERSION = 1
ENTETES = {"User-Agent": "TwinPicks/1.0 (jeu de quiz entre amis ; usage personnel)"}
DELAI = 8
_VERROU = threading.Lock()
_CACHE = None

# sections qui ne sont pas des répliques
HORS = re.compile(r"(tagline|accroche|slogan|cast|distribution|external|liens? externes?|see also|voir aussi|about|"
                  r"à propos|a propos|citations? sur|references|références|notes|sources|crédits|credits|misattributed)", re.I)
DIALOGUE = re.compile(r"(dialogue|dialogues|répliques diverses|others?|autres)", re.I)


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


def nettoyer(t):
    """Texte wiki -> texte simple."""
    t = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", t)
    t = re.sub(r"<br\s*/?>", " / ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", t).strip(" :*")


def analyser(wikitexte):
    """[(personnage ou "", réplique)] d'une page Wikiquote de film."""
    out, section, hors = [], "", False
    for ligne in wikitexte.splitlines():
        m = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", ligne)
        if m:
            titre = nettoyer(m.group(2))
            hors = bool(HORS.search(titre))
            section = "" if DIALOGUE.search(titre) or len(m.group(1)) < 2 else titre
            continue
        if hors:
            continue
        c = re.search(r"\{\{\s*[Cc]itation\s*\|\s*(?:citation\s*=\s*)?(.*?)\}\}", ligne)
        if c:                                   # Wikiquote en français : {{citation|citation=…}}
            txt = nettoyer(c.group(1).split("|")[0])
            if 12 <= len(txt) <= 240:
                out.append((section, txt))
            continue
        if ligne.startswith("* ") or (ligne.startswith("*") and not ligne.startswith("**")):
            txt = nettoyer(ligne[1:])
            if section and 12 <= len(txt) <= 240:
                out.append((section, txt))
        elif ligne.startswith(":") or ligne.startswith("*:"):
            m = re.match(r"^\*?:+\s*'''\s*([^':]{2,40}?)\s*:?\s*'''\s*:?\s*(.+)$", ligne)
            if m:
                txt = nettoyer(m.group(2))
                if 12 <= len(txt) <= 240 and not txt.startswith("["):
                    out.append((nettoyer(m.group(1)), txt))
    vus, uniques = set(), []
    for qui, txt in out:
        if normaliser(txt) not in vus:
            vus.add(normaliser(txt))
            uniques.append((qui, txt))
    return uniques


def repliques(api, film):
    """{"langue": "fr"|"en", "repliques": [[personnage, texte], …]} (vide sans Internet ou sans page Wikiquote)."""
    k = f"{'tv' if film.get('tv') else 'm'}:{film['id']}"
    with _VERROU:
        if k in _charger():
            return _CACHE[k]
    res, ok = {"langue": "", "repliques": []}, False
    try:
        kind = "tv" if film.get("tv") else "movie"
        q = (api.get(f"/{kind}/{film['id']}/external_ids") or {}).get("wikidata_id")
        if q:
            ent = (_get(f"https://www.wikidata.org/wiki/Special:EntityData/{q}.json").get("entities") or {}).get(q) or {}
            liens = ent.get("sitelinks") or {}
            for langue in ("fr", "en"):
                titre = (liens.get(f"{langue}wikiquote") or {}).get("title")
                if not titre:
                    continue
                d = _get(f"https://{langue}.wikiquote.org/w/api.php", action="parse", page=titre, prop="wikitext",
                         format="json", formatversion=2, redirects=1)
                rep = analyser(((d.get("parse") or {}).get("wikitext")) or "")
                if len(rep) >= 4:
                    res = {"langue": langue, "repliques": [list(x) for x in rep[:120]]}
                    break
        ok = True
    except Exception:  # noqa: BLE001
        ok = False
    if ok:
        with _VERROU:
            _charger()[k] = res
            _sauver()
    return res


def masquer(texte, mots):
    """Remplace par ▒▒▒ les mots interdits (titre du film…)."""
    return re.sub(r"[\w'’-]+", lambda m: "▒" * len(m.group()) if normaliser(m.group()) in mots else m.group(), texte)


def meme_personne(nom, role):
    """Le personnage de Wikiquote (« Hannibal Lecter ») est-il ce rôle TMDB (« Dr. Hannibal Lecter ») ?"""
    a = {m for m in normaliser(nom).split() if len(m) >= 3}
    b = {m for m in normaliser(role).split() if len(m) >= 3}
    return bool(a and b and (a <= b or b <= a or len(a & b) >= 1 and (min(len(a), len(b)) == 1 or len(a & b) >= 2)))


def affichage(cfg, texte, langue):
    """{"t": la réplique en français, "p": ""} : les répliques sont toujours en français (les répliques anglaises sont
    traduites par traduction.py ; sans traduction possible, l'anglais)."""
    from traduction import traduire
    if langue != "en":
        return {"t": texte, "p": ""}
    return {"t": traduire(texte) or texte, "p": ""}
