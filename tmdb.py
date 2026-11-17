"""Accès à TMDB : client HTTP, listes, compte, acteurs et détails des films."""
import io
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image

from config import FICHIER_ACTEURS, FICHIER_CACHE_ACTEURS, JEUX, SOURCES_COMPTE
import sagas
from texte import cle, est_latin

API_V3 = "https://api.themoviedb.org/3"
API_V4 = "https://api.themoviedb.org/4"
URL_IMG = "https://image.tmdb.org/t/p/"
POOL = {g: ("acteurs" if g in ("filmo", "denise", "phillip") else "notes" if JEUX[g].get("profils") else "films_" + g)
        for g in JEUX}                                     # chaque jeu a son pool (Norma / Shelly : notes des profils)
GENRES = {28: "Action", 12: "Aventure", 16: "Animation", 35: "Comédie", 80: "Crime", 99: "Documentaire",
          18: "Drame", 10751: "Familial", 14: "Fantastique", 36: "Histoire", 27: "Horreur", 10402: "Musique",
          9648: "Mystère", 10749: "Romance", 878: "Science-Fiction", 10770: "Téléfilm", 53: "Thriller",
          10752: "Guerre", 37: "Western", 10759: "Action & Aventure", 10762: "Enfants", 10765: "Science-Fiction & Fantastique",
          10768: "Guerre & Politique", 10764: "Télé-réalité", 10763: "Actualités", 10766: "Feuilleton", 10767: "Talk-show"}
LANGUES = {"en": "anglais", "fr": "français", "es": "espagnol", "it": "italien", "de": "allemand", "ja": "japonais",
           "ko": "coréen", "zh": "chinois", "cn": "cantonais", "hi": "hindi", "ru": "russe", "pt": "portugais",
           "sv": "suédois", "da": "danois", "no": "norvégien", "nl": "néerlandais", "pl": "polonais", "fa": "persan",
           "tr": "turc", "th": "thaï", "ar": "arabe", "he": "hébreu", "fi": "finnois", "el": "grec", "hu": "hongrois",
           "cs": "tchèque", "ro": "roumain", "id": "indonésien", "te": "télougou", "ta": "tamoul", "is": "islandais"}


class TMDB:
    def __init__(self, cle_api, session="", compte=0):
        self.cle = (cle_api or "").strip()
        self.session, self.compte = session, compte
        self.http = requests.Session()
        self._images, self._details = {}, {}
        self._verrou = threading.Lock()

    def _auth(self, params):
        if self.cle.startswith("eyJ"):                    # jeton v4
            return {"Authorization": "Bearer " + self.cle}
        params["api_key"] = self.cle
        return {}

    def get(self, chemin, base=API_V3, **params):
        params.setdefault("language", "fr-FR")
        entetes = self._auth(params)
        r = self.http.get(base + chemin, params=params, headers=entetes, timeout=15)
        r.raise_for_status()
        return r.json()

    def post(self, chemin, corps, base=API_V3, **params):
        entetes = self._auth(params)
        r = self.http.post(base + chemin, params=params, json=corps, headers=entetes, timeout=15)
        r.raise_for_status()
        return r.json()

    def image(self, chemin, taille="w500"):
        k = (chemin, taille)
        im = self._images.get(k)
        if im is None:
            try:
                r = self.http.get(URL_IMG + taille + chemin, timeout=15)
                r.raise_for_status()
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
            except Exception:  # noqa: BLE001
                im = Image.new("RGB", (342, 513), "#333333")
            with self._verrou:
                if len(self._images) > 200:
                    self._images.clear()
                self._images[k] = im
        return im.copy()

    def images(self, chemins, taille="w342"):
        with ThreadPoolExecutor(max_workers=8) as ex:
            return list(ex.map(lambda c: self.image(c, taille), chemins))


# ---------- films et listes ----------
def _film(it):
    return {"id": it["id"], "title": it.get("title") or it.get("name"),
            "original_title": it.get("original_title") or it.get("original_name"),
            "poster_path": it.get("poster_path"),
            "release_date": it.get("release_date") or it.get("first_air_date") or "",
            "tv": it.get("media_type") == "tv",
            "genre_ids": [g["id"] if isinstance(g, dict) else g for g in it.get("genre_ids") or it.get("genres") or []],
            "note": it.get("vote_average") or 0, "votes": it.get("vote_count") or 0,
            "langue": it.get("original_language") or "", "popularite": it.get("popularity") or 0}


def cle_film(f):
    return ("tv" if f["tv"] else "m", f["id"])


def cle_txt(f):
    """Clé d'un film dans les profils : « m:550 » ou « tv:1399 »."""
    return "%s:%s" % cle_film(f)


def film_de_profil(k, e):
    """Film (même format que les listes) à partir d'une entrée de profil."""
    typ, ident = k.split(":")
    return {"id": int(ident), "title": e.get("t") or e.get("o") or "?", "original_title": e.get("o") or e.get("t"),
            "poster_path": e.get("p"), "release_date": f"{e['a']}-01-01" if e.get("a") else "", "tv": typ == "tv",
            "genre_ids": e.get("g") or [], "note": e.get("v") or 0, "votes": e.get("c") or 0,
            "langue": e.get("l") or "", "popularite": 0}


def annee(f):
    return (f.get("release_date") or "")[:4]


def libelle(f):
    a = annee(f)
    return f"{f['title']} ({a})" if a else f["title"]


def id_liste(texte):
    m = re.search(r"\d+", str(texte))
    return int(m.group()) if m else None


def _pages(api, chemin, cle_res="results", base=API_V3, **params):
    items, page = [], 1
    while page <= 50:
        d = api.get(chemin, base=base, page=page, **params)
        items += d.get(cle_res) or []
        if page >= d.get("total_pages", 1):
            break
        page += 1
    return items


def charger_source_compte(api, lid):
    if not api.session or not api.compte:
        raise RuntimeError("Connectez votre compte TMDB (Listes TMDB) pour utiliser favoris, à voir et notés.")
    cat, kind, _ = SOURCES_COMPTE[lid]
    items = _pages(api, f"/account/{api.compte}/{cat}/{kind}", session_id=api.session)
    if kind == "tv":
        items = [dict(it, media_type="tv") for it in items]
    return [_film(it) for it in items if it.get("title") or it.get("name")]


def charger_liste(api, lid):
    if lid in SOURCES_COMPTE:
        return charger_source_compte(api, lid)
    try:
        items = _pages(api, f"/list/{lid}", "items")
    except requests.HTTPError:
        if not api.cle.startswith("eyJ"):
            raise RuntimeError(f"Liste {lid} introuvable. Pour une liste récente, utilisez le jeton v4 "
                               "(« jeton d'accès en lecture ») à la place de la clé v3.")
        items = _pages(api, f"/list/{lid}", "results", base=API_V4)
    return [_film(it) for it in items if it.get("title") or it.get("name")]


def resoudre_liste(api, lid):
    try:
        d = api.get(f"/list/{lid}")
        return {"id": lid, "nom": d.get("name") or f"Liste {lid}",
                "nb": int(d.get("item_count") or len(d.get("items", [])))}
    except Exception:  # noqa: BLE001
        return {"id": lid, "nom": f"Liste {lid}", "nb": 0}


def lire_listes_compte(api, sid):
    compte = api.get("/account", session_id=sid)
    aid = compte["id"]
    listes = [{"id": int(l["id"]), "nom": l.get("name") or f"Liste {l['id']}",
               "nb": int(l.get("number_of_items") or l.get("item_count") or 0)}
              for l in _pages(api, f"/account/{aid}/lists", session_id=sid)]
    for lid, (cat, kind, nom) in SOURCES_COMPTE.items():
        try:
            n = int(api.get(f"/account/{aid}/{cat}/{kind}", session_id=sid, page=1).get("total_results", 0))
        except Exception:  # noqa: BLE001
            n = 0
        listes.append({"id": lid, "nom": nom, "nb": n})
    return {"compte": aid, "nom": compte.get("username") or compte.get("name") or "", "listes": listes}


def connecter(api, jeton):
    sid = api.post("/authentication/session/new", {"request_token": jeton})["session_id"]
    data = lire_listes_compte(api, sid)
    data["session_id"] = sid
    return data


# ---------- acteurs ----------
def lire_noms(fichier):
    """Un nom par ligne ; lignes vides et commentaires (#) ignorés, sans doublon."""
    try:
        with open(fichier, encoding="utf-8-sig") as f:
            lignes = [l.strip().lstrip("-•* ").strip() for l in f]
    except OSError:
        return []
    noms, vus = [], set()
    for n in lignes:
        if n and not n.startswith("#") and cle(n) not in vus:
            vus.add(cle(n))
            noms.append(n)
    return noms


def lire_noms_acteurs():
    return lire_noms(FICHIER_ACTEURS)


VERSION_CACHE_ACTEURS = 2


def _choisir_personne(nom, res, metier="Acting"):
    """Parmi les résultats de /search/person : le même nom, du bon métier, le plus connu."""
    k = cle(nom)
    res = [p for p in res if p.get("profile_path")] or (res if metier != "Acting" else [])
    if not res:
        return None
    du_metier = [p for p in res if p.get("known_for_department") == metier] or res
    exacts = [p for p in du_metier if cle(p["name"]) == k] or [p for p in res if cle(p["name"]) == k]
    return max(exacts or du_metier[:1], key=lambda p: p.get("popularity", 0))


def resoudre_personnes(api, noms, fichier_cache, metier="Acting"):
    """Noms -> personnes TMDB [{id, name, profile_path}] (résultat gardé dans fichier_cache)."""
    try:
        with open(fichier_cache, encoding="utf-8") as f:
            brut = json.load(f)
        cache = brut.get("acteurs", {}) if isinstance(brut, dict) and brut.get("v") == VERSION_CACHE_ACTEURS else {}
    except (OSError, ValueError):
        cache = {}

    def chercher(nom):
        k = cle(nom)
        if k in cache:
            return k, cache[k]
        try:
            p = _choisir_personne(nom, api.get("/search/person", query=nom, language="en-US")["results"], metier)
        except Exception:  # noqa: BLE001
            return k, None
        return k, ({"id": p["id"], "name": p["name"], "profile_path": p.get("profile_path")} if p else None)

    with ThreadPoolExecutor(max_workers=5) as ex:
        trouves = list(ex.map(chercher, noms))
    personnes, vus, neuf = [], set(), False
    for k, p in trouves:
        if p:
            neuf = neuf or k not in cache
            cache[k] = p
            if p["id"] not in vus:
                vus.add(p["id"])
                personnes.append(p)
    if neuf:
        try:
            with open(fichier_cache, "w", encoding="utf-8") as f:
                json.dump({"v": VERSION_CACHE_ACTEURS, "acteurs": cache}, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
    return personnes


def charger_acteurs(api):
    """Acteurs de acteurs.txt (mis en cache) ; sans fichier : acteurs populaires de TMDB."""
    noms = lire_noms_acteurs()
    if not noms:
        res = []
        for page in range(1, 6):
            res += api.get("/person/popular", page=page).get("results", [])
        acteurs = [{"id": p["id"], "name": p["name"], "profile_path": p["profile_path"]}
                   for p in res if p.get("profile_path") and p.get("known_for_department") == "Acting"]
        if not acteurs:
            raise RuntimeError("Aucun acteur trouvé (acteurs.txt absent et TMDB injoignable).")
        return acteurs
    acteurs = resoudre_personnes(api, noms, FICHIER_CACHE_ACTEURS)
    if not acteurs:
        raise RuntimeError("Aucun acteur de acteurs.txt trouvé sur TMDB.")
    return acteurs


# ---------- infos détaillées (casting, équipe) ----------
JOBS_COMPOSITEUR = {"original music composer", "music", "composer", "music director", "main title theme composer"}
JOBS_SCENARISTE = {"Screenplay", "Writer", "Story", "Novel", "Author"}


def fiche(api, f):
    """Détails d'un film ou d'une série avec casting et équipe (mis en cache)."""
    kind = "tv" if f["tv"] else "movie"
    k = ("fiche", kind, f["id"])
    if k in api._details:
        return api._details[k]
    d = api.get(f"/{kind}/{f['id']}", append_to_response=("aggregate_credits" if kind == "tv" else "credits") + ",keywords")
    cr = d.get("aggregate_credits") or d.get("credits") or {}
    acteurs = []
    for c in sorted(cr.get("cast", []), key=lambda c: c.get("order", 99)):
        role = c.get("character") or next((r.get("character") for r in c.get("roles") or [] if r.get("character")), "")
        acteurs.append({"id": c["id"], "nom": c.get("name", ""), "role": role or "", "photo": c.get("profile_path"),
                        "ordre": c.get("order", 99), "sexe": c.get("gender") or 0})

    def jobs(c):
        return [c.get("job") or ""] + [j.get("job") or "" for j in c.get("jobs") or []]

    equipe = cr.get("crew", [])
    reals = [{"id": c["id"], "nom": c["name"]} for c in equipe if "Director" in jobs(c)]
    if kind == "tv":
        reals = [{"id": c["id"], "nom": c["name"]} for c in d.get("created_by") or []] or reals
    compos = [{"id": c["id"], "nom": c["name"]} for c in equipe if any(j.lower() in JOBS_COMPOSITEUR for j in jobs(c))]
    scenar = [{"id": c["id"], "nom": c["name"]} for c in equipe if any(j in JOBS_SCENARISTE for j in jobs(c))]
    chefs_op = [{"id": c["id"], "nom": c["name"]} for c in equipe if "Director of Photography" in jobs(c)]
    kw = d.get("keywords") or {}
    kw = kw.get("keywords") or kw.get("results") or []

    def uniques(lst):
        vus, out = set(), []
        for x in lst:
            if x["id"] not in vus:
                vus.add(x["id"])
                out.append(x)
        return out

    duree = d.get("runtime") or next(iter(d.get("episode_run_time") or []), 0)
    res = dict(id=f["id"], tv=f["tv"], titre=d.get("title") or d.get("name") or f["title"],
               original=d.get("original_title") or d.get("original_name") or f.get("original_title"),
               annee=(d.get("release_date") or d.get("first_air_date") or f.get("release_date") or "")[:4],
               affiche=d.get("poster_path") or f.get("poster_path"), genres=[g["name"] for g in d.get("genres", [])],
               genre_ids=[g["id"] for g in d.get("genres", [])], note=d.get("vote_average") or 0,
               votes=d.get("vote_count") or 0, langue=d.get("original_language") or "", duree=duree or 0,
               pays=[c.get("name") for c in d.get("production_countries") or [] if c.get("name")],
               realisateurs=uniques(reals), compositeurs=uniques(compos), acteurs=uniques(acteurs),
               scenaristes=uniques(scenar), chefs_op=uniques(chefs_op),
               mots_cles=[k.get("name", "") for k in kw if k.get("name")], mots_cles_ids=[k["id"] for k in kw if k.get("id")],
               societes_noms={c.get("id"): c.get("name") for c in d.get("production_companies") or [] if c.get("id")},
               slogan=d.get("tagline") or "",
               collection=sagas.nom_propre((d.get("belongs_to_collection") or {}).get("name") or ""),
               collection_id=(d.get("belongs_to_collection") or {}).get("id") or 0,
               societes=[c.get("id") for c in d.get("production_companies") or [] if c.get("id")],
               pays_codes=[c.get("iso_3166_1") for c in d.get("production_countries") or [] if c.get("iso_3166_1")]
               or list(d.get("origin_country") or []),
               recettes=d.get("revenue") or 0, budget=d.get("budget") or 0)
    if kind == "movie":
        sagas.noter(f, d.get("belongs_to_collection"))
    api._details[k] = res
    return res


def credits_personne(api, pid):
    """Crédits bruts d'une personne (/person/{id}/movie_credits), mis en cache."""
    k = ("credits", pid)
    if k not in api._details:
        api._details[k] = api.get(f"/person/{pid}/movie_credits")
    return api._details[k]


def ids_personne(api, pid, job=None):
    """Identifiants de TOUS les films d'une personne (rôles si job=None, sinon « Director » ou « compositeur »),
    sans filtre : sert à vérifier qu'un film tapé par un joueur respecte la contrainte."""
    d = credits_personne(api, pid)
    if job is None:
        return {c["id"] for c in d.get("cast", []) if not re.search(r"\b(self|himself|herself|archive)\b",
                                                                     c.get("character") or "", re.I)}
    if job == "compositeur":
        return {c["id"] for c in d.get("crew", []) if (c.get("job") or "").lower() in JOBS_COMPOSITEUR}
    if job == "scenariste":
        return {c["id"] for c in d.get("crew", []) if c.get("job") in JOBS_SCENARISTE}
    return {c["id"] for c in d.get("crew", []) if c.get("job") == job}


def filmographie(api, pid, job=None):
    """Films d'une personne : rôles (job=None) ou postes (« Director », « compositeur »), sortis, triés par votes."""
    k = ("filmo", pid, job)
    if k in api._details:
        return api._details[k]
    d = credits_personne(api, pid)
    if job is None:
        brut = [c for c in d.get("cast", []) if not re.search(r"\b(self|himself|herself|archive|uncredited|voice)\b",
                                                               c.get("character") or "", re.I)]
    elif job == "compositeur":
        brut = [c for c in d.get("crew", []) if (c.get("job") or "").lower() in JOBS_COMPOSITEUR]
    elif job == "scenariste":
        brut = [c for c in d.get("crew", []) if c.get("job") in JOBS_SCENARISTE]
    else:
        brut = [c for c in d.get("crew", []) if c.get("job") == job]
    films = {}
    for c in brut:
        if not c.get("release_date") or 99 in (c.get("genre_ids") or []) or not c.get("poster_path"):
            continue
        f = dict(_film(c), ordre=c.get("order", 99), role=c.get("character") or "")
        if f["id"] not in films or f["ordre"] < films[f["id"]]["ordre"]:
            films[f["id"]] = f
    res = sorted(films.values(), key=lambda f: -f["votes"])
    api._details[k] = res
    return res


def completer(api, films, maxi=250):
    """Ajoute affiche, genres, note et langue aux films qui n'en ont pas (films venus d'un fichier importé)."""
    manquants = [f for f in films if not f.get("poster_path") or not f.get("genre_ids")][:maxi]
    if not manquants:
        return

    def lire(f):
        try:
            return f, api.get(f"/{'tv' if f['tv'] else 'movie'}/{f['id']}")
        except Exception:  # noqa: BLE001
            return f, None

    infos = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for f, d in ex.map(lire, manquants):
            if not d:
                continue
            g = _film(dict(d, media_type="tv" if f["tv"] else "movie"))
            for c in ("poster_path", "genre_ids", "note", "votes", "langue", "popularite"):
                if g.get(c):
                    f[c] = g[c]
            f["title"] = g["title"] or f["title"]
            f["release_date"] = g["release_date"] or f["release_date"]
            infos[cle_txt(f)] = {"p": g["poster_path"], "g": g["genre_ids"], "v": g["note"], "c": g["votes"],
                                 "l": g["langue"]}
    try:
        import profils
        profils.memoriser_infos(infos)
    except Exception:  # noqa: BLE001
        pass


# ---------- pools de jeu ----------
def charger_pools(api, cfg, jeux, profils=()):
    """Un pool par jeu : union des listes incluses moins les listes exclues, sans doublon.
    Si des joueurs ont un profil (et « profils_auto ») : les films vus par TOUS ces joueurs (intersection),
    moins les listes exclues du jeu. Norma / Shelly : pool « notes » (films notés dans les profils).
    Retourne (pools, info)."""
    pools, info = {}, ""
    if any(g in jeux for g in ("filmo", "andy", "denise", "phillip")):              # Andy : autocomplétion des manches d'acteur
        pools["acteurs"] = charger_acteurs(api)
    jeux_films = [g for g in jeux if JEUX[g]["listes"]]
    actifs = [p for p in profils if p["listes"] or p["films"]] if cfg.get("profils_auto") and jeux_films else []
    ids = {i for g in jeux_films for i in cfg["listes"][g]["exc"]}
    if actifs:
        ids |= {i for p in actifs for i in p["listes"]}
    else:
        ids |= {i for g in jeux_films for i in cfg["listes"][g]["inc"]}

    def lire(i):
        try:
            return charger_liste(api, i), None
        except Exception as err:  # noqa: BLE001
            return None, str(err)

    with ThreadPoolExecutor(max_workers=4) as ex:
        lus = dict(zip(sorted(ids), ex.map(lire, sorted(ids))))
    base = None
    if actifs:
        connus, vus_par, erreurs = {}, [], []
        for p in actifs:
            vus = set()
            for i in p["listes"]:
                lst, err = lus[i]
                if err:
                    erreurs.append(err)
                    continue
                for f in lst:
                    vus.add(cle_film(f))
                    connus.setdefault(cle_film(f), f)
            if cfg.get("profils_fichier") or not p["listes"]:
                for kt, e in p["films"].items():
                    f = film_de_profil(kt, e)
                    vus.add(cle_film(f))
                    connus.setdefault(cle_film(f), f)
            if vus:
                vus_par.append((p["nom"], vus))
        noms = " et ".join(n for n, _ in vus_par) or " et ".join(p["nom"] for p in actifs)
        commun = set.intersection(*[v for _, v in vus_par]) if vus_par else set()
        if not commun:
            raise RuntimeError(erreurs[0] if erreurs and not vus_par else
                               f"Aucun film vu par {noms} : vérifiez leurs listes (bouton Profils).")
        base = {k: connus[k] for k in commun}
        completer(api, list(base.values()))
        info = f"{len(base)} films vus par {noms}" if len(vus_par) > 1 else f"{len(base)} films de {noms}"
    for g in jeux_films:
        inc = cfg["listes"][g]["inc"]
        exc = [i for i in cfg["listes"][g]["exc"] if base is not None or i not in inc]
        for i in exc:
            if lus[i][1]:
                raise RuntimeError(lus[i][1])
        interdits = {cle_film(f) for i in exc for f in lus[i][0]}
        films, erreurs = {}, []
        if base is not None:
            films = {k: f for k, f in base.items() if k not in interdits}
        else:
            for i in inc:
                lst, err = lus[i]
                if err:
                    erreurs.append(err)
                    continue
                for f in lst:
                    k = cle_film(f)
                    if k not in interdits and k not in films:
                        films[k] = f
        if not films:
            raise RuntimeError(erreurs[0] if erreurs else
                               f"Aucun film pour « {JEUX[g]['nom']} » : listes vides ou entièrement exclues.")
        pools[POOL[g]] = list(films.values())
    if any(JEUX[g].get("profils") for g in jeux):
        notes = {}
        for p in profils:
            for kt, n in p["notes"].items():
                e = p["films"].get(kt) or {}
                if kt not in notes:
                    notes[kt] = dict(film_de_profil(kt, e), notes={})
                notes[kt]["notes"][p["nom"]] = n
        if not notes:
            raise RuntimeError("Aucune note dans les profils des joueurs : importez un fichier (bouton Profils).")
        pools["notes"] = list(notes.values())
    return pools, info


def entrees_pool(pool, kind):
    """Entrées pour l'autocomplétion : [(libellé, [(nom, cle), ...])]."""
    out = []
    for p in pool:
        noms = [p["name"]] if kind == "acteurs" else [n for n in (p["title"], p.get("original_title"))
                                                     if n and est_latin(n)]
        vus, uniques = set(), []
        for n in noms:
            if cle(n) not in vus:
                vus.add(cle(n))
                uniques.append((n, cle(n)))
        if uniques:
            out.append((uniques[0][0], uniques))
    return out


def details_film(api, m):
    """Titres acceptés, titre anglais, résumé, genres, images de scènes (mis en cache)."""
    kind = "tv" if m["tv"] else "movie"
    k = (kind, m["id"])
    if k in api._details:
        return api._details[k]
    try:
        d = api.get(f"/{kind}/{m['id']}", append_to_response="alternative_titles,translations,images",
                    include_image_language="fr,en,null")
    except Exception:  # noqa: BLE001
        d = {}
    noms = [m["title"], m.get("original_title"), d.get("title"), d.get("name"),
            d.get("original_title"), d.get("original_name")]
    alt = d.get("alternative_titles") or {}
    noms += [a.get("title") for a in alt.get("titles") or alt.get("results") or []]
    en, resume_en, slogan_en = None, "", ""
    for t in (d.get("translations") or {}).get("translations", []):
        data = t.get("data") or {}
        titre = data.get("title") or data.get("name")
        noms.append(titre)
        if t.get("iso_639_1") == "en":
            if titre and not en and est_latin(titre):
                en = titre
            resume_en = resume_en or data.get("overview") or ""
            slogan_en = slogan_en or data.get("tagline") or ""
    fonds = sorted((d.get("images") or {}).get("backdrops", []),
                   key=lambda b: (b.get("iso_639_1") is not None, -(b.get("vote_average") or 0)))
    res = dict(noms=[n for n in noms if n and est_latin(n)], en=en,
               resume=d.get("overview") or resume_en, genres=[g["name"] for g in d.get("genres", [])],
               slogan=(d.get("tagline") or "").strip(), slogan_en=slogan_en.strip(),
               fonds=[b["file_path"] for b in fonds], annee=(m["release_date"] or d.get("release_date") or "")[:4],
               affiche=d.get("poster_path") or m.get("poster_path"),
               fonds_neutres=[b["file_path"] for b in fonds if b.get("iso_639_1") is None],   # sans texte
               fonds_votes=[{"p": b["file_path"], "note": b.get("vote_average") or 0, "votes": b.get("vote_count") or 0}
                            for b in fonds if b.get("iso_639_1") is None])
    coll = d.get("belongs_to_collection") if d else None
    res["saga"] = sagas.nom_propre(coll.get("name")) if coll else ""
    res["saga_id"] = coll.get("id") if coll else 0
    if d and kind == "movie":
        sagas.noter(m, coll)
    elif kind == "movie" and sagas.saga(m):                # détails illisibles : le cache peut suffire
        res["saga_id"], res["saga"] = sagas.saga(m)
    api._details[k] = res
    return res


def nom_affiche(titre, annee, en):
    t = f"{titre} ({annee})" if annee else titre
    if en and cle(en) != cle(titre):
        t += f" / {en}"
    return t


# ---------- ajouts : mots-clés, affiches, collections ----------
def mots_cles(api, f):
    """Mots-clés TMDB d'un film ou d'une série (en anglais), mis en cache."""
    kind = "tv" if f["tv"] else "movie"
    k = ("mots_cles", kind, f["id"])
    fi = api._details.get(("fiche", kind, f["id"]))
    if k not in api._details and fi and fi.get("mots_cles"):
        api._details[k] = list(fi["mots_cles"])
    if k not in api._details:
        try:
            d = api.get(f"/{kind}/{f['id']}/keywords")
            api._details[k] = [x.get("name", "") for x in d.get("keywords") or d.get("results") or [] if x.get("name")]
        except Exception:  # noqa: BLE001
            api._details[k] = []
    return api._details[k]


def affiches_film(api, f):
    """Toutes les affiches d'un film : [{chemin, langue, note, votes, largeur, hauteur}], les affiches sans langue
    (le plus souvent sans texte) d'abord, puis par votes."""
    kind = "tv" if f["tv"] else "movie"
    d = api.get(f"/{kind}/{f['id']}/images", include_image_language="null,en,fr")
    out = [{"chemin": p["file_path"], "langue": p.get("iso_639_1"), "note": p.get("vote_average") or 0,
            "votes": p.get("vote_count") or 0, "largeur": p.get("width") or 0, "hauteur": p.get("height") or 0}
           for p in d.get("posters") or [] if p.get("file_path")]
    return sorted(out, key=lambda p: (p["langue"] is not None, -(p["votes"] * (p["note"] or 1)), -p["largeur"]))


def collection(api, cid):
    """Films d'une collection (saga) TMDB, mis en cache."""
    k = ("collection", cid)
    if k not in api._details:
        try:
            api._details[k] = [_film(dict(p, media_type="movie")) for p in api.get(f"/collection/{cid}").get("parts") or []]
        except Exception:  # noqa: BLE001
            api._details[k] = []
    return api._details[k]


# ---------- studios, mots-clés : identifiants TMDB (gardés dans tmdb_ids_cache.json) et films ----------
FICHIER_IDS = __import__("config").donnee("tmdb_ids_cache.json")
_IDS, _IDS_VERROU = None, threading.Lock()


def _ids_cache():
    global _IDS
    if _IDS is None:
        try:
            with open(FICHIER_IDS, encoding="utf-8") as fh:
                _IDS = json.load(fh)
        except (OSError, ValueError):
            _IDS = {}
    return _IDS


def identifiant(api, genre, nom):
    """Identifiant TMDB d'une société (genre « company ») ou d'un mot-clé (« keyword ») d'après son nom exact."""
    k = f"{genre}:{cle(nom)}"
    with _IDS_VERROU:
        if k in _ids_cache():
            return _ids_cache()[k]
    res = api.get(f"/search/{genre}", query=nom).get("results") or []
    exacts = [r for r in res if cle(r.get("name") or "") == cle(nom)]
    choix = (exacts or res[:1])
    ident = choix[0]["id"] if choix else 0
    with _IDS_VERROU:
        _ids_cache()[k] = ident
        try:
            with open(FICHIER_IDS, "w", encoding="utf-8") as fh:
                json.dump(_IDS, fh, ensure_ascii=False, indent=0)
        except OSError:
            pass
    return ident


def decouvrir(api, pages=2, **params):
    """Films de /discover/movie (les plus votés d'abord), mis en cache."""
    params.setdefault("sort_by", "vote_count.desc")
    k = ("discover", tuple(sorted(params.items())), pages)
    if k not in api._details:
        films = []
        for page in range(1, pages + 1):
            d = api.get("/discover/movie", page=page, **params)
            films += [_film(dict(r, media_type="movie")) for r in d.get("results") or [] if r.get("title")]
            if page >= (d.get("total_pages") or 1):
                break
        api._details[k] = films
    return api._details[k]
