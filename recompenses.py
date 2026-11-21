"""Les récompenses des films (Oscars, Césars, Palme d'or, BAFTA, Golden Globes, Lion d'or, Ours d'or…), d'après
Wikidata (TMDB ne les donne pas). Le lien TMDB -> Wikidata passe par /movie/{id}/external_ids.

Chaque récompense : {"id": "Q102427", "nom": "Oscar du meilleur film", "ceremonie": "Oscars", "annee": 1995,
"gagne": True|False (False : seulement nommé), "film": True si la catégorie récompense le film lui-même (meilleur
film, Palme d'or…) plutôt qu'une personne}.

Tout est mis en cache sur le disque (donnees/recompenses.json) : une partie sans réseau garde ce qu'elle a déjà vu.
Sans réseau et sans cache, il n'y a simplement pas de récompense (les jeux s'en passent).
"""
import json
import os
import re
import threading
import time

from config import DOSSIER_DONNEES

URL = "https://query.wikidata.org/sparql"
ENTETES = {"User-Agent": "TwinPicks/11 (quiz cinema entre amis; https://github.com/Laloyl-gif/Twin-Picks)",
           "Accept": "application/sparql-results+json"}
FICHIER = os.path.join(DOSSIER_DONNEES, "recompenses.json")
DELAI = 8

# (motif sur le nom, cérémonie, prestige) : seules ces récompenses comptent
CEREMONIES = [
    (r"palme d.or", "Cannes", 10),
    (r"\boscar\b|academy award", "Oscars", 9),
    (r"lion d.or|golden lion", "Venise", 8),
    (r"ours d.or|golden bear", "Berlin", 8),
    (r"\bc[ée]sar\b", "Césars", 7),
    (r"british academy|bafta", "BAFTA", 6),
    (r"golden globe", "Golden Globes", 6),
    (r"festival de cannes|cannes", "Cannes", 6),
    (r"lion d.argent|silver lion|ours d.argent|silver bear|grand prix du jury", "Festivals", 5),
]
# catégories qui récompensent le film lui-même (les nommés sont des films)
FILM = re.compile(r"meilleur film|best (motion )?picture|best film|palme d.or|lion d.or|golden lion|ours d.or|"
                  r"golden bear|meilleur long[- ]m[ée]trage|best animated feature|best international|"
                  r"grand prix|prix du jury", re.I)

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
        _cache.setdefault("films", {})
        _cache.setdefault("nommes", {})
    return _cache


def _sauver():
    try:
        with open(FICHIER + ".tmp", "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False)
        os.replace(FICHIER + ".tmp", FICHIER)
    except OSError:
        pass


def classer(nom):
    """(cérémonie, prestige) d'une récompense, ou None si elle ne fait pas partie des grandes."""
    n = (nom or "").lower()
    for motif, cer, prestige in CEREMONIES:
        if re.search(motif, n):
            return cer, prestige
    return None


def _sparql(api, requete):
    http = getattr(api, "http", None)
    if http is None:
        raise RuntimeError("pas d'accès réseau")
    r = http.get(URL, params={"query": requete, "format": "json"}, headers=ENTETES, timeout=DELAI)
    r.raise_for_status()
    return r.json()["results"]["bindings"]


def _val(b, k):
    return (b.get(k) or {}).get("value", "")


def _annee(s):
    m = re.match(r"(-?\d{4})", s or "")
    return int(m.group(1)) if m else 0


def wikidata_id(api, film):
    if film.get("tv"):
        return ""
    try:
        return (api.get(f"/movie/{film['id']}/external_ids") or {}).get("wikidata_id") or ""
    except Exception:  # noqa: BLE001
        return ""


def de_film(api, film):
    """Les grandes récompenses d'un film (gagnées et nominations), triées de la plus prestigieuse à la moins."""
    if film.get("tv"):
        return []
    cle = str(film["id"])
    with _verrou:
        c = _charger()["films"]
        if cle in c:
            return c[cle]
    qid = wikidata_id(api, film)
    if not re.fullmatch(r"Q\d+", qid or ""):
        return []
    requete = """SELECT ?type ?award ?awardLabel ?date ?cerDate WHERE {
  { wd:%s p:P166 ?st . ?st ps:P166 ?award . BIND("g" AS ?type) }
  UNION { wd:%s p:P1411 ?st . ?st ps:P1411 ?award . BIND("n" AS ?type) }
  OPTIONAL { ?st pq:P585 ?date }
  OPTIONAL { ?st pq:P805 ?cer . ?cer wdt:P585 ?cerDate }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
}""" % (qid, qid)
    try:
        lignes = _sparql(api, requete)
    except Exception:  # noqa: BLE001
        return []                               # pas de réseau : rien (et rien en cache, on réessaiera)
    out = {}
    for b in lignes:
        nom = _val(b, "awardLabel")
        cl = classer(nom)
        if not cl:
            continue
        aid = _val(b, "award").rsplit("/", 1)[-1]
        annee = _annee(_val(b, "date")) or _annee(_val(b, "cerDate"))
        k = (aid, annee)
        gagne = _val(b, "type") == "g"
        if k in out:
            out[k]["gagne"] = out[k]["gagne"] or gagne
            continue
        out[k] = {"id": aid, "nom": nom[:1].upper() + nom[1:], "ceremonie": cl[0], "prestige": cl[1], "annee": annee,
                  "gagne": gagne, "film": bool(FILM.search(nom))}
    res = sorted(out.values(), key=lambda r: (-r["gagne"], -r["prestige"], -r["film"], r["annee"]))
    with _verrou:
        _charger()["films"][cle] = res
        _sauver()
    return res


def nommes(api, award, annee):
    """Les films nommés pour une récompense une année donnée : [{"tmdb", "titre", "gagne"}] (le lauréat inclus)."""
    cle = f"{award}|{annee}"
    with _verrou:
        c = _charger()["nommes"]
        if cle in c:
            return c[cle]
    if not re.fullmatch(r"Q\d+", award or ""):
        return []
    requete = """SELECT ?film ?filmLabel ?tmdb ?type WHERE {
  { ?film p:P1411 ?st . ?st ps:P1411 wd:%s . BIND("n" AS ?type) }
  UNION { ?film p:P166 ?st . ?st ps:P166 wd:%s . BIND("g" AS ?type) }
  { ?st pq:P585 ?d } UNION { ?st pq:P805 ?cer . ?cer wdt:P585 ?d }
  FILTER(YEAR(?d) = %d)
  ?film wdt:P4947 ?tmdb .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
}""" % (award, award, int(annee))
    try:
        lignes = _sparql(api, requete)
    except Exception:  # noqa: BLE001
        return []
    films = {}
    for b in lignes:
        t = _val(b, "tmdb")
        if not t.isdigit():
            continue
        f = films.setdefault(t, {"tmdb": int(t), "titre": _val(b, "filmLabel"), "gagne": False})
        f["gagne"] = f["gagne"] or _val(b, "type") == "g"
    res = list(films.values())
    with _verrou:
        _charger()["nommes"][cle] = res
        _sauver()
    return res


def libelle(r):
    return f"{r['nom']} ({r['annee']})" if r.get("annee") else r["nom"]


def indice(api, film):
    """Le texte d'indice « récompenses » d'un film, ou "" : la plus belle victoire (et le nombre de statuettes de
    la même cérémonie), sinon la plus belle nomination."""
    try:
        rs = de_film(api, film)
    except Exception:  # noqa: BLE001
        return ""
    if not rs:
        return ""
    gagnes = [r for r in rs if r["gagne"]]
    if gagnes:
        r = gagnes[0]
        meme = sum(1 for x in gagnes if x["ceremonie"] == r["ceremonie"])
        plus = f" · {meme} {r['ceremonie'] if r['ceremonie'] not in ('Cannes', 'Festivals') else 'prix'} en tout" if meme > 1 else ""
        return f"🏆 {libelle(r)}{plus}"
    r = rs[0]
    return f"Nommé : {libelle(r)}"


def prefetch(api, films, limite=40, budget=20.0):
    """Remplit le cache pour quelques films (au chargement des listes), sans dépasser le budget de temps."""
    t0 = time.time()
    for f in films[:limite]:
        if time.time() - t0 > budget:
            break
        de_film(api, f)


def ajouter_indice(m, api, cfg):
    """Ajoute l'indice « récompenses » aux manches où l'on cherche UN film et qui ont des indices : il arrive avec
    le premier indice (ou vers 45 % de la manche), et reste jusqu'au bout."""
    if not cfg.get("indices_recompenses", True) or m.get("reponse") != "titre" or len(m.get("films") or []) != 1:
        return m
    etapes = m.get("etapes") or []
    if not etapes or not all(isinstance(e, dict) and "indices" in e for _, e in etapes):
        return m
    k = m["films"][0]
    k = tuple(k) if isinstance(k, list) else k
    if not (isinstance(k, tuple) and k[0] == "m"):
        return m
    texte = indice(api, {"id": k[1], "tv": False})
    if not texte:
        return m
    premier = next((i for i, (_, e) in enumerate(etapes) if e["indices"]), None)
    if premier is None:
        t = round(float(m.get("duree") or 30) * 0.45, 2)
        premier = next((i for i, (ti, _) in enumerate(etapes) if ti >= t), len(etapes))
        if premier == len(etapes) or etapes[premier][0] != t:
            etapes.insert(premier, (t, dict(etapes[premier - 1][1])))
    m["etapes"] = [(t, dict(e, indices=list(e["indices"]) + [texte]) if i >= premier else e)
                   for i, (t, e) in enumerate(etapes)]
    m["recompense"] = texte
    return m
