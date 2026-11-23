"""Les anecdotes de tournage des films (et quelques-unes sur les acteurs), d'après Wikipédia en français : rubriques
« Autour du film », « Anecdotes », « Tournage », « Production »… Le lien TMDB -> Wikidata -> article fr.wikipedia
passe par recompenses.wikidata_id. Tout est mis en cache (donnees/anecdotes.json), y compris les films sans
anecdote (pour ne pas les redemander) : la base se constitue au fil des parties, à partir de vos listes.
"""
import html
import json
import os
import re
import threading
import time

from config import DOSSIER_DONNEES

FICHIER = os.path.join(DOSSIER_DONNEES, "anecdotes.json")
ENTETES = {"User-Agent": "TwinPicks/12 (quiz cinema entre amis; https://github.com/Laloyl-gif/Twin-Picks)"}
API_WD = "https://www.wikidata.org/w/api.php"
API_FR = "https://fr.wikipedia.org/w/api.php"
DELAI = 8
# rubriques, de la plus « anecdotique » à la moins
RUBRIQUES = [(r"anecdote|autour du film|le saviez|à noter|trivia", 3), (r"tournage", 2),
             (r"production|genèse|développement|conception|casting|distribution des rôles|musique", 1)]
RUBRIQUES_PERSONNE = [(r"anecdote|vie privée|autour", 3), (r"jeunesse|enfance|débuts|formation", 2),
                      (r"biographie|carrière", 1)]

_verrou = threading.Lock()
_cache = None


def _charger():
    global _cache
    if _cache is None:
        try:
            with open(FICHIER, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _sauver():
    try:
        with open(FICHIER + ".tmp", "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False)
        os.replace(FICHIER + ".tmp", FICHIER)
    except OSError:
        pass


def _get(api, url, **params):
    http = getattr(api, "http", None)
    if http is None:
        raise RuntimeError("pas d'accès réseau")
    params.setdefault("format", "json")
    r = http.get(url, params=params, headers=ENTETES, timeout=DELAI)
    r.raise_for_status()
    return r.json()


def page_fr(api, qid):
    """Le titre de l'article fr.wikipedia d'un élément Wikidata."""
    d = _get(api, API_WD, action="wbgetentities", ids=qid, props="sitelinks", sitefilter="frwiki")
    return (((d.get("entities") or {}).get(qid) or {}).get("sitelinks") or {}).get("frwiki", {}).get("title", "")


def nettoyer(h):
    """HTML d'une section -> texte brut (références, tableaux, légendes retirés)."""
    h = re.sub(r"<sup[^>]*>.*?</sup>", "", h, flags=re.S)
    h = re.sub(r"<(table|style|figure)[^>]*>.*?</\1>", "", h, flags=re.S)
    h = re.sub(r'<div class="thumbcaption[^"]*">.*?</div>', "", h, flags=re.S)
    h = re.sub(r"<(h\d)[^>]*>.*?</\1>", "\n", h, flags=re.S)
    h = re.sub(r"</(p|li)>", "\n", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    h = re.sub(r"\[\s*\d+\s*\]|\[réf\. nécessaire\]|\[modifier[^\]]*\]", "", h)
    return re.sub(r"[ \t ]+", " ", h)


def phrases(texte):
    out = []
    for para in texte.split("\n"):
        para = para.strip()
        if len(para) < 40:
            continue
        for p in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«])", para):
            p = p.strip()
            if 50 <= len(p) <= 260 and not p.endswith(":") and p.count("(") == p.count(")"):
                out.append(p)
    return out


def _extraire(api, titre, rubriques):
    d = _get(api, API_FR, action="parse", page=titre, prop="sections", redirects=1)
    secs = (d.get("parse") or {}).get("sections") or []
    choix = []
    for s in secs:
        nom = html.unescape(re.sub(r"<[^>]+>", "", s.get("line") or "")).lower()
        for motif, poids in rubriques:
            if re.search(motif, nom):
                choix.append((poids, s["index"]))
                break
    choix.sort(key=lambda x: -x[0])
    out = []
    for poids, idx in choix[:4]:
        try:
            t = _get(api, API_FR, action="parse", page=titre, prop="text", section=idx, redirects=1, disabletoc=1)
        except Exception:  # noqa: BLE001
            continue
        texte = nettoyer(((t.get("parse") or {}).get("text") or {}).get("*", ""))
        out += [{"t": p, "p": poids} for p in phrases(texte)]
        if len(out) >= 14:
            break
    return out[:20]


def de_film(api, film):
    """[{"t": phrase, "p": poids}] : les anecdotes d'un film (cache ; [] si rien)."""
    if film.get("tv"):
        return []
    cle = f"m{film['id']}"
    with _verrou:
        c = _charger()
        if cle in c:
            return c[cle]
    import recompenses
    qid = recompenses.wikidata_id(api, film)
    if not re.fullmatch(r"Q\d+", qid or ""):
        return []
    try:
        titre = page_fr(api, qid)
        res = _extraire(api, titre, RUBRIQUES) if titre else []
    except Exception:  # noqa: BLE001
        return []                                   # réseau : on réessaiera
    with _verrou:
        _charger()[cle] = res
        _sauver()
    return res


def de_personne(api, pid):
    cle = f"p{pid}"
    with _verrou:
        c = _charger()
        if cle in c:
            return c[cle]
    try:
        qid = (api.get(f"/person/{pid}/external_ids") or {}).get("wikidata_id") or ""
        titre = page_fr(api, qid) if re.fullmatch(r"Q\d+", qid) else ""
        res = _extraire(api, titre, RUBRIQUES_PERSONNE) if titre else []
    except Exception:  # noqa: BLE001
        return []
    with _verrou:
        _charger()[cle] = res
        _sauver()
    return res


def masquer(texte, noms):
    """Remplace dans le texte les noms à cacher (titres, nom de l'acteur) par « … »."""
    for n in sorted({n for n in noms if n and len(n) > 1}, key=len, reverse=True):
        texte = re.sub(r"(?i)(?<![\w])" + re.escape(n) + r"(?![\w])", "…", texte)
    return re.sub(r"(…\s*){2,}", "… ", texte)


def prefetch(api, films, budget=25.0, limite=30):
    """Remplit le cache en tâche de fond (au chargement des listes)."""
    t0 = time.time()
    for f in films[:limite]:
        if time.time() - t0 > budget:
            break
        try:
            de_film(api, f)
        except Exception:  # noqa: BLE001
            pass
