"""Les anecdotes de tournage des films (et quelques-unes sur les acteurs), d'après Wikipédia en français ET en anglais
(rubriques « Autour du film », « Anecdotes », « Tournage », « Production », « Casting », « Filming »…). Les phrases
anglaises sont traduites (traduction.py) quand elles sont choisies. Chaque phrase reçoit une note « insolite » :
accidents, improvisations, blessures, refus, faux départs, objets vrais, paris, superstitions… passent devant les
dates de sortie et les chiffres du box-office. (IMDb interdit la récupération automatique de ses pages : Wikipédia
est la source libre la plus riche.)
Tout est mis en cache (donnees/anecdotes.json), y compris les films sans anecdote : la base se constitue au fil des
parties, à partir de vos listes.
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
API_EN = "https://en.wikipedia.org/w/api.php"
VERSION = "v2"
# ce qui rend une anecdote insolite (français et anglais) ; et ce qui la rend banale
INSOLITE = re.compile(r"improvis|ad-lib|accident|bless[ée]|injur|cass[ée]|\bbroke\b|fractur|hôpital|hospital|refus|"
                      r"turned down|declined|rejected|à l'origine|originally|initialement|failli|\balmost\b|nearly|"
                      r"\bréel|véritable|\breal\b|actually|en réalité|\bvrai\b|\bvraie\b|secret|par hasard|by chance|"
                      r"insist|exigé|demanded|renvoy|\bfired\b|remplac|replaced|caméo|cameo|clin d'œil|easter egg|"
                      r"\bparié|\bpari\b|\bbet\b|superstiti|\bivre\b|drunk|malade|\bsick\b|vomi|terrifi|\bscared|"
                      r"frightened|détest|\bhated\b|furieux|furious|en colère|\bangry\b|vrai sang|real blood|"
                      r"\btomb[ée]|\bfell\b|blague|\bjoke|prank|farce|surpris|sans le savoir|without knowing|unaware|"
                      r"interdit|banned|censur|au lieu de|instead of|en échange|in exchange|gratuitement|for free|"
                      r"\bchien|\bdog\b|\bchats?\b|\bcats?\b|cheval|\bhorse|serpent|snake|\bours\b|\bbear\b|"
                      r"insecte|araignée|spider|cascade|stunt|doublure|\bnu\b|naked|nude|perruque|wig|prothèse|"
                      r"\bdent|tooth|teeth|cicatrice|scar|tatou|tattoo|maquillage|make-up|makeup", re.I)
BANAL = re.compile(r"box-office|box office|recett|gross|budget de|millions? de dollars|million dollars|sorti[e]? en salles?|"
                   r"released|distribu|critique|review|festival|nomin|récompens|award|oscar|césar|entrées|admissions|"
                   r"dvd|blu-ray|vhs|bande-annonce|trailer|première mondiale|premiere", re.I)
RUBRIQUES_EN = [(r"trivia|behind|anecdote", 3), (r"filming|shooting|principal photography", 2),
                (r"production|development|casting|pre-production|writing|music", 1)]
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


def pages(api, qid):
    """Les titres des articles fr et en.wikipedia d'un élément Wikidata."""
    d = _get(api, API_WD, action="wbgetentities", ids=qid, props="sitelinks", sitefilter="frwiki|enwiki")
    sl = ((d.get("entities") or {}).get(qid) or {}).get("sitelinks") or {}
    return sl.get("frwiki", {}).get("title", ""), sl.get("enwiki", {}).get("title", "")


def page_fr(api, qid):
    return pages(api, qid)[0]


def insolite(t):
    """La note « insolite » d'une phrase : mots qui sentent l'anecdote, moins ceux qui sentent la fiche technique."""
    n = len(INSOLITE.findall(t))
    return n - 2 * len(BANAL.findall(t))


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
        for p in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«\"“])", para):
            p = p.strip()
            if 50 <= len(p) <= 260 and not p.endswith(":") and p.count("(") == p.count(")"):
                out.append(p)
    return out


def _extraire(api, titre, rubriques, url=API_FR):
    d = _get(api, url, action="parse", page=titre, prop="sections", redirects=1)
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
            t = _get(api, url, action="parse", page=titre, prop="text", section=idx, redirects=1, disabletoc=1)
        except Exception:  # noqa: BLE001
            continue
        texte = nettoyer(((t.get("parse") or {}).get("text") or {}).get("*", ""))
        en = url == API_EN
        out += [{"t": p, "p": poids, "s": insolite(p), "en": en} for p in phrases(texte)]
        if len(out) >= 40:
            break
    out.sort(key=lambda a: (-a["s"], -a["p"]))
    return out[:24]


def de_film(api, film):
    """[{"t": phrase, "p": poids}] : les anecdotes d'un film (cache ; [] si rien)."""
    if film.get("tv"):
        return []
    cle = f"{VERSION}:m{film['id']}"
    with _verrou:
        c = _charger()
        if cle in c:
            return c[cle]
    import recompenses
    qid = recompenses.wikidata_id(api, film)
    if not re.fullmatch(r"Q\d+", qid or ""):
        return []
    try:
        fr, en = pages(api, qid)
        res = (_extraire(api, fr, RUBRIQUES) if fr else []) + (_extraire(api, en, RUBRIQUES_EN, API_EN) if en else [])
    except Exception:  # noqa: BLE001
        return []                                   # réseau : on réessaiera
    res.sort(key=lambda a: (-a["s"], -a["p"], a.get("en", False)))
    with _verrou:
        _charger()[cle] = res
        _sauver()
    return res


def de_personne(api, pid):
    cle = f"{VERSION}:p{pid}"
    with _verrou:
        c = _charger()
        if cle in c:
            return c[cle]
    try:
        qid = (api.get(f"/person/{pid}/external_ids") or {}).get("wikidata_id") or ""
        fr, en = pages(api, qid) if re.fullmatch(r"Q\d+", qid) else ("", "")
        res = (_extraire(api, fr, RUBRIQUES_PERSONNE) if fr else []) + \
            (_extraire(api, en, [(r"personal life|trivia|early life", 3), (r"career", 1)], API_EN) if en else [])
        res.sort(key=lambda a: (-a["s"], -a["p"], a.get("en", False)))
    except Exception:  # noqa: BLE001
        return []
    with _verrou:
        _charger()[cle] = res
        _sauver()
    return res


def en_francais(a):
    """Le texte d'une anecdote, traduit en français si elle vient de la Wikipédia anglaise (None si impossible)."""
    if not a.get("en"):
        return a["t"]
    try:
        from traduction import traduire
        return traduire(a["t"], "en", "fr")
    except Exception:  # noqa: BLE001
        return None


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
