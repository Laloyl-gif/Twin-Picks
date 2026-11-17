"""Profils des joueurs : listes TMDB à utiliser automatiquement, films vus et notes (fichier importé).

Fichier profils.json (à côté de main.py) :
    [{"id", "nom", "avatar", "listes": [ids TMDB], "listes_noms": [noms de listes], "source", "importe",
      "films": {"m:550": {"t": titre, "o": titre original, "a": année, "n": note 1-10 ou null, "p": affiche}}}]

"realisateurs" : les réalisateurs de realisateurs.txt que le joueur connaît (null : tous). Chrono et Bingo ne posent
des conditions « réalisateur » que sur eux.
Un joueur est relié à un profil quand son pseudo est le nom du profil (accents et majuscules ignorés).
Import : export IMDb (ratings.csv), TMDB (CSV), Letterboxd (zip ou ratings.csv / watched.csv),
Refract (zip de sauvegarde ou ses CSV), ou tout CSV avec un titre, une année et une note.
"""
import csv
import datetime
import io
import json
import re
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor

from config import FICHIER_PROFILS
from texte import cle, normaliser

VERROU = threading.RLock()
DEFAUTS = [
    {"nom": "Louison", "listes_noms": ["Evaluations"]},
    {"nom": "Lily", "listes_noms": ["Jeu - Vu avec Lily", "Commun Lily"]},
    {"nom": "Etienne", "listes_noms": ["Commun Etienne", "Vu avec Etienne"]},
]
MAX_FILMS = 20000


# ====================================================================================
# Stockage
# ====================================================================================
def _slug(nom):
    return re.sub(r"[^a-z0-9]+", "-", normaliser(nom)).strip("-") or "profil"


def _neuf(nom, **kw):
    p = {"id": _slug(nom), "nom": " ".join(str(nom).split())[:16], "avatar": "", "listes": [], "listes_noms": [],
         "source": "", "importe": "", "films": {}, "realisateurs": None}
    p.update(kw)
    return p


def _propre(p):
    """Profil lu sur le disque : champs manquants complétés, valeurs vérifiées."""
    if not isinstance(p, dict) or not str(p.get("nom") or "").strip():
        return None
    q = _neuf(p["nom"])
    q["id"] = str(p.get("id") or q["id"])
    q["avatar"] = str(p.get("avatar") or "")
    q["listes"] = [int(i) for i in p.get("listes") or [] if str(i).lstrip("-").isdigit()]
    q["listes_noms"] = [str(n) for n in p.get("listes_noms") or [] if str(n).strip()]
    q["source"], q["importe"] = str(p.get("source") or ""), str(p.get("importe") or "")
    r = p.get("realisateurs")                 # réalisateurs connus (noms de realisateurs.txt) ; None : tous
    q["realisateurs"] = [str(n)[:80] for n in r if str(n).strip()] if isinstance(r, list) else None
    films = p.get("films") if isinstance(p.get("films"), dict) else {}
    q["films"] = {k: v for k, v in films.items() if isinstance(v, dict) and re.fullmatch(r"(m|tv):\d+", k)}
    return q


def charger():
    with VERROU:
        try:
            with open(FICHIER_PROFILS, encoding="utf-8") as f:
                brut = json.load(f)
        except FileNotFoundError:
            profils = [_neuf(d["nom"], listes_noms=d["listes_noms"]) for d in DEFAUTS]
            sauver(profils)
            return profils
        except (OSError, ValueError):
            return []
        return [p for p in map(_propre, brut if isinstance(brut, list) else []) if p]


def sauver(profils):
    with VERROU:
        try:
            with open(FICHIER_PROFILS, "w", encoding="utf-8") as f:
                json.dump(profils, f, ensure_ascii=False, indent=1)
        except OSError:
            pass


def trouver(nom, profils=None):
    """Profil dont le nom correspond au pseudo (ou à l'identifiant)."""
    k = cle(nom or "")
    if not k:
        return None
    for p in profils if profils is not None else charger():
        if cle(p["nom"]) == k or p["id"] == nom:
            return p
    return None


def listes_ids(p, listes_connues):
    """Identifiants des listes du profil : choisies à la main + celles reconnues par leur nom."""
    ids = list(p["listes"])
    noms = {cle(n) for n in p["listes_noms"]}
    for l in listes_connues:
        if cle(l["nom"]) in noms and l["id"] not in ids:
            ids.append(l["id"])
    return ids


def listes_manquantes(p, listes_connues):
    connus = {cle(l["nom"]) for l in listes_connues}
    return [n for n in p["listes_noms"] if cle(n) not in connus]


def resume(p, listes_connues):
    connues = {l["id"]: l for l in listes_connues}
    notes = [f["n"] for f in p["films"].values() if f.get("n")]
    return {"id": p["id"], "nom": p["nom"], "avatar": p["avatar"],
            "listes": [{"id": i, "nom": connues.get(i, {}).get("nom", f"Liste {i}"), "nb": connues.get(i, {}).get("nb", 0)}
                       for i in listes_ids(p, listes_connues)],
            "manquantes": listes_manquantes(p, listes_connues), "nb_films": len(p["films"]), "nb_notes": len(notes),
            "moyenne": round(sum(notes) / len(notes), 1) if notes else None, "source": p["source"],
            "importe": p["importe"], "realisateurs": p["realisateurs"]}


def pour_partie(p, listes_connues):
    """Ce dont la partie a besoin : nom, listes, films du fichier, notes."""
    return {"id": p["id"], "nom": p["nom"], "listes": listes_ids(p, listes_connues), "films": p["films"],
            "notes": {k: f["n"] for k, f in p["films"].items() if f.get("n")}, "realisateurs": p["realisateurs"]}


def modifier(action, d, listes_connues):
    """Actions de l'écran hôte sur les profils. Retourne la liste des profils (résumés)."""
    with VERROU:
        profils = charger()
        par_id = {p["id"]: p for p in profils}
        p = par_id.get(str(d.get("id") or ""))
        if action == "ajouter":
            nom = " ".join(str(d.get("nom") or "").split())[:16]
            if not nom:
                raise RuntimeError("Donnez un nom au profil.")
            if trouver(nom, profils):
                raise RuntimeError(f"Le profil « {nom} » existe déjà.")
            p = _neuf(nom)
            while p["id"] in par_id:
                p["id"] += "-2"
            profils.append(p)
        elif not p:
            raise RuntimeError("Profil introuvable.")
        elif action == "supprimer":
            profils.remove(p)
        elif action == "renommer":
            nom = " ".join(str(d.get("nom") or "").split())[:16]
            autre = trouver(nom, profils)
            if not nom or (autre and autre is not p):
                raise RuntimeError("Nom vide ou déjà pris.")
            p["nom"] = nom
        elif action == "avatar":
            p["avatar"] = str(d.get("avatar") or "")[:40]
        elif action == "listes":
            ids = [int(i) for i in d.get("listes") or [] if str(i).lstrip("-").isdigit()]
            p["listes"], p["listes_noms"] = ids, []                # choix explicite : remplace les noms
        elif action == "vider":
            p["films"], p["source"], p["importe"] = {}, "", ""
        elif action == "realisateurs":                         # réalisateurs connus (None : tous)
            r = d.get("realisateurs")
            p["realisateurs"] = [str(n)[:80] for n in r if str(n).strip()] if isinstance(r, list) else None
        sauver(profils)
        return [resume(x, listes_connues) for x in profils]


def memoriser_infos(infos):
    """Ajoute aux profils les affiches / infos trouvées en cours de partie : {"m:550": {"p": ..., ...}}."""
    if not infos:
        return
    with VERROU:
        profils = charger()
        change = False
        for p in profils:
            for k, extra in infos.items():
                f = p["films"].get(k)
                if f is not None:
                    for c, v in extra.items():
                        if v and not f.get(c):
                            f[c] = v
                            change = True
        if change:
            sauver(profils)


# ====================================================================================
# Lecture des fichiers exportés
# ====================================================================================
def _texte(data):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def _lignes_csv(texte):
    try:
        dialecte = csv.Sniffer().sniff(texte[:4096], delimiters=",;\t")
    except csv.Error:
        dialecte = csv.excel
    lignes = list(csv.reader(io.StringIO(texte), dialecte))
    if not lignes:
        return [], []
    entetes = [normaliser(h) for h in lignes[0]]
    return entetes, [l for l in lignes[1:] if any(c.strip() for c in l)]


def _colonne(entetes, *candidats, contient=None):
    for c in candidats:
        if c in entetes:
            return entetes.index(c)
    if contient:
        for i, h in enumerate(entetes):
            if all(m in h.split() for m in contient):
                return i
    return None


def _nombre(x):
    try:
        return float(str(x).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _annee(x):
    m = re.search(r"(18|19|20)\d{2}", str(x or ""))
    return m.group() if m else ""


def _type(x):
    x = normaliser(x or "")
    if not x:
        return None
    if "episode" in x:
        return "episode"
    if any(m in x for m in ("movie", "film", "short", "video")):
        return "m"
    if any(m in x for m in ("tv", "serie", "show", "mini")):
        return "tv"
    return "m"


def lire_csv(texte, nom=""):
    """Entrées d'un CSV : [{tmdb, imdb, type, titre, original, annee, note, vu}], échelle des notes."""
    entetes, lignes = _lignes_csv(texte)
    nom = normaliser(nom)
    c_tmdb = _colonne(entetes, "tmdb id", "tmdb", "tmdbid", "tmdb_id", "id tmdb", "tmdb id movie")
    c_imdb = _colonne(entetes, "const", "imdb id", "imdbid", "imdb", "imdb_id", "tconst")
    c_titre = _colonne(entetes, "title", "titre", "name", "nom", "film", "movie", "display title")
    c_orig = _colonne(entetes, "original title", "original_title", "titre original")
    c_annee = _colonne(entetes, "year", "annee", "release year", "release date", "date de sortie", "released")
    c_note = _colonne(entetes, "your rating", "my rating", "ma note", "user rating", "rating", "note", "value",
                      "score", "rating10")
    c_type = _colonne(entetes, "title type", "type", "media type", "media_type", "kind")
    c_statut = _colonne(entetes, "status", "statut")
    c_cible = _colonne(entetes, "target type")                       # Refract : notes d'épisodes
    c_episode = _colonne(entetes, "episode number", "episode")       # TMDB : notes d'épisodes
    letterboxd = any("letterboxd" in h for h in entetes)
    if c_note is not None and entetes[c_note] in ("imdb rating", "tmdb rating"):
        c_note = None
    entrees = []
    for l in lignes:
        val = lambda c: l[c].strip() if c is not None and c < len(l) else ""   # noqa: E731
        if c_statut is not None and normaliser(val(c_statut)) not in ("completed", "up to date", "watched", "vu", ""):
            continue
        typ = _type(val(c_type)) if c_type is not None else None
        if typ == "episode" or (c_cible is not None and _type(val(c_cible)) == "episode") or val(c_episode):
            continue
        imdb = re.search(r"tt\d+", val(c_imdb)) if c_imdb is not None else None
        tmdb = val(c_tmdb)
        e = {"tmdb": int(tmdb) if tmdb.isdigit() else None, "imdb": imdb.group() if imdb else None, "type": typ,
             "titre": val(c_titre), "original": val(c_orig), "annee": _annee(val(c_annee)),
             "note": _nombre(val(c_note)) if c_note is not None else None, "vu": True}
        if e["tmdb"] or e["imdb"] or e["titre"]:
            entrees.append(e)
    notes = [e["note"] for e in entrees if e["note"]]
    echelle = 2.0 if letterboxd or "letterboxd" in nom or (notes and max(notes) <= 5) else 1.0
    if letterboxd or "letterboxd" in nom:
        source = "Letterboxd"
    elif c_imdb is not None and c_tmdb is None:
        source = "IMDb"
    elif c_tmdb is not None:
        source = "TMDB" if "refract" not in nom else "Refract"
    else:
        source = "CSV"
    return entrees, echelle, source


def lire_refract(z):
    """Sauvegarde Refract (zip) : data/ratings.jsonl (notes 1-10) et data/library.jsonl (films vus)."""
    entrees = []

    def jsonl(chemin):
        try:
            return [json.loads(l) for l in _texte(z.read(chemin)).splitlines() if l.strip()]
        except (KeyError, ValueError):
            return []

    def entree(it, note=None):
        typ = "tv" if it.get("mediaType") == "tv" else "m" if it.get("mediaType") == "movie" else None
        if not typ or not it.get("tmdbId"):
            return None
        return {"tmdb": int(it["tmdbId"]), "imdb": it.get("imdbId"), "type": typ,
                "titre": it.get("displayTitle") or it.get("title") or "", "original": it.get("title") or "",
                "annee": str(it.get("year") or ""), "note": note, "vu": True}

    for r in jsonl("data/ratings.jsonl"):
        if r.get("targetType") in ("movie", "tv") and isinstance(r.get("value"), (int, float)):
            e = entree(r.get("item") or {}, r["value"])
            if e:
                entrees.append(e)
    for r in jsonl("data/library.jsonl"):
        if r.get("status") in ("completed", "up_to_date"):
            e = entree(r.get("item") or {}, r.get("rating") if isinstance(r.get("rating"), (int, float)) else None)
            if e:
                entrees.append(e)
    compte = ""
    try:
        compte = json.loads(z.read("manifest.json")).get("account", {}).get("username", "")
    except (KeyError, ValueError):
        pass
    return entrees, 1.0, "Refract" + (f" ({compte})" if compte else "")


def lire_fichier(nom, data):
    """(entrées, échelle, source) d'un fichier importé (CSV, zip Letterboxd / Refract, JSON)."""
    if data[:2] == b"PK":
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            raise RuntimeError("Archive zip illisible.")
        noms = z.namelist()
        if "data/ratings.jsonl" in noms or "data/library.jsonl" in noms:
            return lire_refract(z)
        csvs = [n for n in noms if n.lower().endswith(".csv") and "/._" not in n]
        if not csvs:
            raise RuntimeError("Aucun fichier CSV dans l'archive.")
        # Letterboxd : ratings.csv (notes) + watched.csv (vus) ; sinon tous les CSV
        prefere = [n for n in csvs if n.split("/")[-1].lower() in ("ratings.csv", "watched.csv")]
        entrees, echelle, source = [], 1.0, ""
        for n in prefere or csvs:
            e, ech, src = lire_csv(_texte(z.read(n)), nom + " " + n + (" letterboxd" if prefere else ""))
            if "rating" in n.lower():
                echelle = ech
            entrees += e
            source = source or src
        return entrees, echelle, source
    texte = _texte(data)
    if texte.lstrip().startswith(("[", "{")):
        try:
            brut = json.loads(texte)
        except ValueError:
            raise RuntimeError("JSON illisible.")
        lignes = brut if isinstance(brut, list) else brut.get("results") or brut.get("items") or []
        sortie = io.StringIO()
        champs = sorted({k for l in lignes if isinstance(l, dict) for k in l})
        w = csv.DictWriter(sortie, champs)
        w.writeheader()
        for l in lignes:
            if isinstance(l, dict):
                w.writerow({k: v for k, v in l.items() if not isinstance(v, (dict, list))})
        return lire_csv(sortie.getvalue(), nom)
    return lire_csv(texte, nom)


def note_sur_10(note, echelle):
    if note is None or note <= 0:
        return None
    return max(1, min(10, int(note * echelle + 0.5)))


# ====================================================================================
# Import (résolution des identifiants TMDB) et enregistrement
# ====================================================================================
def _resoudre(api, e):
    """Complète une entrée sans identifiant TMDB : par l'identifiant IMDb, sinon par titre + année."""
    if e["tmdb"] and e["type"] in ("m", "tv"):
        return e
    try:
        if e["imdb"]:
            r = api.get(f"/find/{e['imdb']}", external_source="imdb_id")
            for cle_res, typ in (("movie_results", "m"), ("tv_results", "tv")):
                if r.get(cle_res):
                    it = r[cle_res][0]
                    return dict(e, tmdb=it["id"], type=typ, poster=it.get("poster_path"),
                                titre=it.get("title") or it.get("name") or e["titre"],
                                original=it.get("original_title") or it.get("original_name") or e["original"],
                                annee=e["annee"] or (it.get("release_date") or it.get("first_air_date") or "")[:4])
        if e["titre"]:
            chemin = "/search/tv" if e["type"] == "tv" else "/search/movie"
            params = {"query": e["original"] or e["titre"]}
            if e["annee"]:
                params["first_air_date_year" if e["type"] == "tv" else "year"] = e["annee"]
            res = api.get(chemin, **params).get("results", [])
            if not res and e["annee"]:
                res = api.get(chemin, query=params["query"]).get("results", [])
            k = cle(e["titre"]), cle(e["original"] or e["titre"])
            exacts = [it for it in res if {cle(it.get("title") or it.get("name") or ""),
                                           cle(it.get("original_title") or it.get("original_name") or "")} & set(k)]
            it = (exacts or res or [None])[0]
            if it:
                return dict(e, tmdb=it["id"], type="tv" if e["type"] == "tv" else "m", poster=it.get("poster_path"),
                            original=it.get("original_title") or it.get("original_name") or e["original"],
                            annee=e["annee"] or (it.get("release_date") or it.get("first_air_date") or "")[:4])
    except Exception:  # noqa: BLE001
        return None
    return None


def importer(api, id_profil, nom_fichier, data, listes_connues):
    """Importe un fichier dans un profil (fusion : les films déjà connus sont mis à jour)."""
    entrees, echelle, source = lire_fichier(nom_fichier or "", data)
    if not entrees:
        raise RuntimeError("Aucun film reconnu dans ce fichier.")
    a_resoudre = [e for e in entrees if not (e["tmdb"] and e["type"] in ("m", "tv"))]
    if a_resoudre:
        if api is None:
            raise RuntimeError("Clé TMDB nécessaire pour retrouver les films de ce fichier.")
        with ThreadPoolExecutor(max_workers=8) as ex:
            resolues = dict(zip(map(id, a_resoudre), ex.map(lambda e: _resoudre(api, e), a_resoudre)))
        entrees = [resolues.get(id(e), e) if id(e) in resolues else e for e in entrees]
    films, ignores = {}, 0
    for e in entrees:
        if not e or not e.get("tmdb"):
            ignores += 1
            continue
        k = f"{e['type'] if e['type'] in ('m', 'tv') else 'm'}:{e['tmdb']}"
        f = films.setdefault(k, {"t": e["titre"] or e["original"], "o": e["original"] or e["titre"], "a": e["annee"],
                                 "n": None})
        n = note_sur_10(e["note"], echelle)
        if n:
            f["n"] = n
        if e.get("poster"):
            f["p"] = e["poster"]
    with VERROU:
        profils = charger()
        p = next((x for x in profils if x["id"] == id_profil), None)
        if not p:
            raise RuntimeError("Profil introuvable.")
        for k, f in films.items():
            ancien = p["films"].get(k, {})
            if f["n"] is None and ancien.get("n"):
                f["n"] = ancien["n"]
            p["films"][k] = {**ancien, **{c: v for c, v in f.items() if v is not None}, "n": f["n"]}
        if len(p["films"]) > MAX_FILMS:
            p["films"] = dict(list(p["films"].items())[-MAX_FILMS:])
        p["source"] = source
        p["importe"] = datetime.date.today().isoformat()
        sauver(profils)
        nb_notes = sum(1 for f in films.values() if f["n"])
        return {"profils": [resume(x, listes_connues) for x in profils],
                "msg": f"{len(films)} films importés ({nb_notes} notés)" + (f", {ignores} non reconnus" if ignores else "")}
