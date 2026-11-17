"""Musique d'ambiance et du blind test.

Sources de la musique d'ambiance (réglables séparément pour le menu et pour la partie) :
  - dossier musique/ du jeu (morceaux complets, vos fichiers) :
        musique/menu/                    musique du menu et du podium (ex. la BO de Twin Peaks)
        musique/partie/                  musique pendant la partie
        musique/films/<Titre (année)>/   BO d'un film : jouée pendant la partie si le film est dans les listes
                                         (jamais pendant sa manche), avec le nom du film en bas de l'écran
  - playlist YouTube (morceaux complets, lue par le lecteur YouTube intégré à l'écran hôte) ;
  - Deezer (extraits officiels de 30 s : l'API de Deezer ne donne pas les morceaux complets, même avec un compte).
Blind test : toujours les extraits Deezer (ci-dessous).

- bande_originale() : retrouve la BO d'un film et vérifie que c'est la bonne (titre de l'album,
  compositeur crédité sur TMDB, genre « Films/Jeux vidéo », année), en écartant les reprises.
- piste_aleatoire() / mp3() : musique d'ambiance (menu : Twin Peaks ; partie : dark jazz / instrumental).
"""
import hashlib
import os
import random
import re
import threading
import time
from collections import OrderedDict

import requests

from config import AMBIANCE_ARTISTES, DOSSIER, MENU_ALBUM, MENU_ARTISTE
from texte import normaliser

DEEZER = "https://api.deezer.com"
GENRE_FILMS = 173                                   # genre Deezer « Films/Jeux vidéo »
HTTP = requests.Session()
HTTP.headers["User-Agent"] = "TwinPicks/1.1"
_VERROU_HTTP = threading.Lock()
_DERNIERS = []                                      # horodatage des derniers appels (limite Deezer : 50 / 5 s)


def deezer(chemin, **params):
    """Appel GET à l'API Deezer ; {} en cas d'erreur."""
    with _VERROU_HTTP:
        maintenant = time.monotonic()
        while _DERNIERS and maintenant - _DERNIERS[0] > 5:
            _DERNIERS.pop(0)
        if len(_DERNIERS) >= 40:
            time.sleep(max(0.0, 5 - (maintenant - _DERNIERS[0])))
        _DERNIERS.append(time.monotonic())
    try:
        d = HTTP.get(DEEZER + chemin, params=params, timeout=10).json()
    except (requests.RequestException, ValueError):
        return {}
    return d if isinstance(d, dict) and not d.get("error") else {}


def telecharger(url):
    r = HTTP.get(url, timeout=15)
    r.raise_for_status()
    if len(r.content) < 20000:
        raise ValueError("extrait vide")
    return r.content


# ====================================================================================
# Bande originale d'un film
# ====================================================================================
MOTS_BO = ("soundtrack", "original score", "motion picture", "music from", "bande originale", "musique du film",
           "musique originale", "ost", "score", "original series", "television series", "music by")
BRUIT = {"original", "motion", "picture", "soundtrack", "score", "music", "musique", "from", "the", "of", "film",
         "du", "de", "la", "le", "bande", "originale", "ost", "series", "serie", "television", "tv", "limited",
         "event", "deluxe", "edition", "expanded", "complete", "remastered", "version", "songs", "official", "and",
         "et", "bo", "netflix", "amazon", "hbo", "apple", "recording"}
# Reprises, réenregistrements, compilations « inspirées de » : jamais la vraie BO.
REPRISE = re.compile(r"\b(covers?|cover version|tribute|hommage|inspired by|inspire[sd]? par|karaoke|lullab(y|ies)|"
                     r"berceuses?|piano versions?|piano covers?|in the style of|made famous|as performed by|"
                     r"rendition|8 ?bit|music box|string quartet|reimagined|re imagined|remix(es)?|lofi|lo fi|"
                     r"the hits|greatest movie|movie themes|film themes|tv themes|best of)\b")
ARTISTES_REPRISE = {normaliser(a) for a in (
    "London Music Works", "Movie Sounds Unlimited", "The Hit Crew", "Pianissimo Brothers", "Global Stage Orchestra",
    "City of Prague Philharmonic Orchestra", "L'Orchestra Cinematique", "Soundtrack Wonder Band", "TV Themes",
    "Hollywood Studio Orchestra", "Rockabye Baby!", "Vitamin String Quartet", "The Piano Guys", "Piano Dreamers",
    "Movie Soundtrack All Stars", "Film Music Orchestra", "Cinematic Orchestra Covers", "Orlando Pops Orchestra",
    "Fandom", "Twinkle Twinkle Little Rock Star", "Graham Plowman", "Brandon Fiechter", "The Soundtrack Studio Stars",
    "Original Soundtrack Players", "Hollywood Film Music Orchestra",
    "Movie Score Masters", "Box Office Orchestra", "Starlite Singers", "Countdown Singers")}
DIVERS = {"various artists", "artistes divers", "multi interpretes", "verschiedene interpreten", "varios artistas"}
PAS_UN_MORCEAU = re.compile(r"\b(dialogue|interview|commentary|commentaire|trailer|radio spot|tv spot|karaoke|"
                            r"spoken|narration|bonus track)\b", re.I)
JOBS_COMPOSITEUR = {"original music composer", "music", "composer", "music director", "main title theme composer",
                    "musical"}
SANS_BO = set()                                    # films déjà cherchés sans succès (inutile de recommencer)


def _sans_bruit(texte):
    mots = [m for m in normaliser(texte).split() if m not in BRUIT]
    return " ".join(mots)


def score_titre(titre_album, titres):
    """2 : l'album porte exactement le titre du film (aux mentions « soundtrack »… près) ; 1 : il le contient ; 0 : non."""
    sans_parentheses = re.sub(r"[\(\[].*?[\)\]]", " ", titre_album)
    coeur = _sans_bruit(sans_parentheses) or normaliser(sans_parentheses)
    complet = f" {normaliser(titre_album)} "
    meilleur = 0
    for t in titres:
        ft = _sans_bruit(t) or normaliser(t)
        if not ft:
            continue
        if coeur == ft or coeur == normaliser(t):
            return 2
        if len(ft) >= 4 and (f" {ft} " in complet or f" {normaliser(t)} " in complet):
            meilleur = 1
    return meilleur


def compositeurs_tmdb(api, film):
    """Compositeurs crédités sur TMDB (noms)."""
    kind = "tv" if film["tv"] else "movie"
    try:
        if kind == "tv":
            crew = api.get(f"/tv/{film['id']}/aggregate_credits").get("crew", [])
            jobs = lambda c: [j.get("job", "") for j in c.get("jobs", [])]   # noqa: E731
        else:
            crew = api.get(f"/movie/{film['id']}/credits").get("crew", [])
            jobs = lambda c: [c.get("job", "")]   # noqa: E731
    except Exception:  # noqa: BLE001
        return []
    noms = []
    for c in crew:
        if any(j.lower() in JOBS_COMPOSITEUR for j in jobs(c)) and c.get("name") and c["name"] not in noms:
            noms.append(c["name"])
    return noms


def _nom_present(nom, textes):
    n = normaliser(nom)
    return bool(n) and any(f" {n} " in f" {normaliser(t)} " for t in textes if t)


def _artistes_album(album):
    noms = [(album.get("artist") or {}).get("name", "")]
    noms += [c.get("name", "") for c in album.get("contributors") or []]
    noms += [(t.get("artist") or {}).get("name", "") for t in (album.get("tracks") or {}).get("data", [])]
    return noms


def evaluer_album(album, titres, annee, compositeurs):
    """Note un album Deezer complet (/album/{id}) ; None s'il n'est pas la BO du film."""
    titre = album.get("title") or ""
    artiste = (album.get("artist") or {}).get("name", "")
    st = score_titre(titre, titres)
    if not st or REPRISE.search(normaliser(titre)) or normaliser(artiste) in ARTISTES_REPRISE:
        return None
    try:
        an_album = int((album.get("release_date") or "0")[:4])
    except ValueError:
        an_album = 0
    try:
        an_film = int(annee or 0)
    except ValueError:
        an_film = 0
    if an_album and an_film and an_album < an_film - 1:          # une BO ne sort pas des années avant le film
        return None
    compo = any(_nom_present(c, _artistes_album(album)) for c in compositeurs)
    genre = album.get("genre_id") == GENRE_FILMS or any(
        g.get("id") == GENRE_FILMS for g in (album.get("genres") or {}).get("data", []))
    bo = genre or any(m in normaliser(titre) for m in MOTS_BO)
    proche = bool(an_album and an_film and an_album <= an_film + 1)
    divers = normaliser(artiste) in DIVERS
    if compo:
        ok = st == 2 or bo
    elif compositeurs:                       # compositeur connu mais absent : seulement une compilation de chansons
        ok = st == 2 and bo and divers and (proche or not an_album)
    else:                                    # aucun compositeur sur TMDB : titre exact, BO, et bonne époque
        ok = st == 2 and bo and (proche or divers)
    if not ok:
        return None
    return (3 * compo + 2 * (st == 2) + bo + proche, album.get("fans") or 0)


def _pistes_album(album):
    pistes = list((album.get("tracks") or {}).get("data", []))
    if album.get("nb_tracks", 0) > len(pistes):
        pistes = deezer(f"/album/{album['id']}/tracks", limit=300).get("data", []) or pistes
    return [t for t in pistes if t.get("preview") and t.get("readable", True)
            and (t.get("duration") or 60) >= 35 and not PAS_UN_MORCEAU.search(t.get("title") or "")]


def bande_originale(titres, annee, compositeurs, top=5):
    """Cherche la BO sur Deezer. Retourne (morceau tiré parmi les `top` plus écoutés, album) ou (None, None)."""
    titres = [t for t in titres if len(normaliser(t)) >= 2]
    requetes = []
    for t in titres:
        requetes += [f'artist:"{c}" album:"{t}"' for c in compositeurs[:3]]
    for t in titres:
        requetes += [f'album:"{t}"', f"{t} soundtrack", f"{t} original motion picture soundtrack"]
    vus, evalues, details = set(), [], 0
    for q in requetes:
        for tr in deezer("/search", q=q, limit=50).get("data", []):
            al = tr.get("album") or {}
            if not al.get("id") or al["id"] in vus or not score_titre(al.get("title", ""), titres):
                continue
            vus.add(al["id"])
            if details >= 10:
                continue
            details += 1
            album = deezer(f"/album/{al['id']}")
            note = evaluer_album(album, titres, annee, compositeurs) if album else None
            if note:
                evalues.append((note, album))
        if any(n[0] >= 6 for n, _ in evalues):          # compositeur + titre exact : inutile de chercher plus
            break
    for _, album in sorted(evalues, key=lambda x: x[0], reverse=True):
        pistes = sorted(_pistes_album(album), key=lambda t: t.get("rank") or 0, reverse=True)
        if pistes:
            return random.choice(pistes[:top]), album
    return None, None


# ====================================================================================
# Musique d'ambiance
# ====================================================================================
DUREE_CACHE = 6 * 3600
_listes, _pistes_connues = {}, {}
_verrou_listes = threading.Lock()
_mp3 = OrderedDict()
_verrou_mp3 = threading.Lock()


def _id_artiste(nom):
    res = deezer("/search/artist", q=nom, limit=5).get("data", [])
    exacts = [a for a in res if normaliser(a.get("name", "")) == normaliser(nom)]
    return (exacts or res or [{}])[0].get("id")


def _piste(t):
    return {"id": t["id"], "titre": t.get("title_short") or t.get("title") or "",
            "artiste": (t.get("artist") or {}).get("name", ""), "album": (t.get("album") or {}).get("title", "")}


def _charger_liste(genre):
    pistes = []
    if genre == "menu":
        aid = _id_artiste(MENU_ARTISTE)
        cand = deezer(f"/artist/{aid}/top", limit=100).get("data", []) if aid else []
        cand += deezer("/search", q=f'artist:"{MENU_ARTISTE}" album:"{MENU_ALBUM}"', limit=100).get("data", [])
        pistes = [t for t in cand if normaliser(MENU_ALBUM) in normaliser((t.get("album") or {}).get("title", ""))]
    else:
        for nom in AMBIANCE_ARTISTES:
            aid = _id_artiste(nom)
            if aid:
                pistes += deezer(f"/artist/{aid}/top", limit=25).get("data", [])
    out, vus = [], set()
    for t in pistes:
        if t.get("preview") and t.get("id") not in vus and (t.get("duration") or 60) >= 60:
            vus.add(t["id"])
            out.append(_piste(t))
    return out


def pistes(genre):
    with _verrou_listes:
        date, liste = _listes.get(genre, (0, []))
        if not liste or time.time() - date > DUREE_CACHE:
            liste = _charger_liste(genre) or liste
            _listes[genre] = (time.time(), liste)
            _pistes_connues.update({p["id"]: p for p in liste})
        return liste


class BOFilms:
    """Pendant la partie : extraits des bandes originales des films des listes (cherchées en arrière-plan).
    Jamais la BO d'un film de la manche en cours ou de la suivante ; un film entendu n'est plus tiré ensuite."""
    PRETS_MIN, PAR_FILM, MAX = 3, 3, 60

    def __init__(self):
        self.pistes, self.essayes, self.encours = [], set(), False
        self.verrou = threading.Lock()

    def _remplir(self, cle_api, films):
        from tmdb import TMDB, cle_film, details_film, libelle   # import ici : tmdb ne dépend pas de musique
        api = TMDB(cle_api)
        try:
            for f in films:
                try:
                    d = details_film(api, f)
                    titres = [t for t in dict.fromkeys((f.get("original_title"), d["en"], f["title"])) if t]
                    _, album = bande_originale(titres, d["annee"], compositeurs_tmdb(api, f), top=self.PAR_FILM)
                except Exception:  # noqa: BLE001
                    continue
                if not album:
                    continue
                meilleures = sorted(_pistes_album(album), key=lambda t: t.get("rank") or 0, reverse=True)
                nom = libelle(f)
                for t in meilleures[:self.PAR_FILM]:
                    p = _piste(dict(t, album=t.get("album") or {"title": album.get("title", "")}))
                    deja_dit = normaliser(f["title"]) in normaliser(p["titre"] + " " + p["album"])
                    p.update(film="" if deja_dit else nom, film_k=list(cle_film(f)))
                    with self.verrou:
                        self.pistes.append(p)
                        self.pistes = self.pistes[-self.MAX:]
                    _pistes_connues[p["id"]] = p
        finally:
            self.encours = False

    def demander(self, partie, sauf=()):
        films = partie.films_musique()
        if not films:
            return None
        permis = {tuple(["tv" if f["tv"] else "m", f["id"]]): f for f in films}
        with self.verrou:
            prets = [p for p in self.pistes if tuple(p["film_k"]) in permis]
        if len({tuple(p["film_k"]) for p in prets}) < self.PRETS_MIN and not self.encours and partie.api:
            frais = [f for k, f in permis.items() if k not in self.essayes]
            lot = random.sample(frais, min(4, len(frais)))
            self.essayes |= {k for k, f in permis.items() if f in lot}
            if lot:
                self.encours = True
                threading.Thread(target=self._remplir, args=(partie.api.cle, lot), daemon=True).start()
        libres = [p for p in prets if p["id"] not in set(sauf)] or prets
        if not libres:
            return None
        p = random.choice(libres)
        partie.marquer_musique(permis[tuple(p["film_k"])])
        return {k: v for k, v in p.items() if k != "film_k"}


BO_FILMS = BOFilms()


def _piste_deezer(genre, sauf=(), partie=None):
    """Menu : Twin Peaks. Partie : BO d'un film des listes si possible, sinon instrumental (extraits de 30 s)."""
    if genre != "menu" and partie is not None:
        p = BO_FILMS.demander(partie, sauf)
        if p:
            return p
    liste = pistes("menu" if genre == "menu" else "jeu")
    if not liste:
        return None
    libres = [p for p in liste if p["id"] not in set(sauf)] or liste
    return random.choice(libres)


# ====================================================================================
# Dossier musique/ (morceaux complets)
# ====================================================================================
DOSSIER_MUSIQUE = os.path.join(DOSSIER, "musique")
EXT_AUDIO = {".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".oga": "audio/ogg", ".opus": "audio/ogg", ".m4a": "audio/mp4",
             ".aac": "audio/aac", ".flac": "audio/flac", ".wav": "audio/wav", ".webm": "audio/webm"}
_NUMERO = re.compile(r"^\s*(?:cd\s*\d+\s*[-_.]\s*)?\d{1,3}\s*[-_.)]?\s+", re.I)


def _decrire(fichier, dossier_parent):
    """« 03 - Angelo Badalamenti - Laura Palmer's Theme.mp3 » -> (titre, artiste)."""
    base = _NUMERO.sub("", os.path.splitext(fichier)[0]).replace("_", " ").strip()
    morceaux = [m.strip() for m in base.split(" - ") if m.strip()]
    if len(morceaux) >= 2:
        return " - ".join(morceaux[1:]), morceaux[0]
    return base or fichier, dossier_parent


class Bibliotheque:
    """Fichiers audio du dossier musique/ (relu toutes les 30 s au plus)."""

    def __init__(self):
        self.lu, self.par_id, self.menu, self.partie, self.films = 0.0, {}, [], [], {}
        self.verrou = threading.Lock()

    def _ajouter(self, chemin, dossier_parent, **extra):
        k = "l" + hashlib.sha1(chemin.encode("utf-8", "surrogateescape")).hexdigest()[:16]
        titre, artiste = _decrire(os.path.basename(chemin), dossier_parent)
        p = dict({"id": k, "titre": titre, "artiste": artiste, "album": "", "source": "local"}, **extra)
        self.par_id[k] = (chemin, p)
        return p

    def _fichiers(self, dossier):
        out = []
        for racine, _, fichiers in os.walk(dossier):
            for f in sorted(fichiers):
                if os.path.splitext(f)[1].lower() in EXT_AUDIO and not f.startswith("."):
                    out.append(os.path.join(racine, f))
        return out

    def relire(self, force=False):
        with self.verrou:
            if not force and time.time() - self.lu < 30:
                return
            from images_film import ID_TMDB, analyser_nom
            self.lu, self.par_id, self.menu, self.partie, self.films = time.time(), {}, [], [], {}
            for sous in ("menu", "partie", "films"):
                os.makedirs(os.path.join(DOSSIER_MUSIQUE, sous), exist_ok=True)
            for c in self._fichiers(os.path.join(DOSSIER_MUSIQUE, "menu")):
                self.menu.append(self._ajouter(c, os.path.basename(os.path.dirname(c))))
            for c in self._fichiers(os.path.join(DOSSIER_MUSIQUE, "partie")):
                self.partie.append(self._ajouter(c, os.path.basename(os.path.dirname(c))))
            racine = os.path.join(DOSSIER_MUSIQUE, "films")
            for nom in sorted(os.listdir(racine)):
                d = os.path.join(racine, nom)
                if not os.path.isdir(d):
                    continue
                m = ID_TMDB.search(nom)
                k, annee = analyser_nom(ID_TMDB.sub("", nom).strip() + ".dossier")
                nom_film = ID_TMDB.sub("", nom).strip()
                pistes_film = [self._ajouter(c, "", film=nom_film) for c in self._fichiers(d)]
                if pistes_film:
                    self.films[nom] = {"cle": k, "annee": annee, "pistes": pistes_film,
                                       "id": ("tv" if m.group(1) else "m", int(m.group(2))) if m else None}

    def pistes_films(self, films):
        """[(film, pistes)] pour les films des listes qui ont un dossier dans musique/films/."""
        from texte import cle
        out = []
        for f in films:
            ck = {cle(f.get("title") or ""), cle(f.get("original_title") or "")} - {""}
            try:
                an = int((f.get("release_date") or "")[:4])
            except ValueError:
                an = None
            for e in self.films.values():
                if e["id"] == ("tv" if f.get("tv") else "m", f["id"]) or (
                        e["id"] is None and e["cle"] in ck and (not (an and e["annee"]) or abs(an - e["annee"]) <= 1)):
                    out.append((f, e["pistes"]))
                    break
        return out

    def chemin(self, ident):
        with self.verrou:
            return (self.par_id.get(ident) or (None,))[0]


BIBLIO = Bibliotheque()


def _piste_locale(genre, sauf, partie, avec_films):
    BIBLIO.relire()
    sauf = set(sauf)
    if genre == "menu":
        libres = [p for p in BIBLIO.menu if p["id"] not in sauf] or BIBLIO.menu
        return dict(random.choice(libres)) if libres else None
    if avec_films and partie is not None and BIBLIO.films:
        candidats = BIBLIO.pistes_films(partie.films_musique())
        if candidats and (not BIBLIO.partie or random.random() < 0.7):
            film, pistes_film = random.choice(candidats)
            libres = [p for p in pistes_film if p["id"] not in sauf] or pistes_film
            partie.marquer_musique(film)
            return dict(random.choice(libres))
    libres = [p for p in BIBLIO.partie if p["id"] not in sauf] or BIBLIO.partie
    return dict(random.choice(libres)) if libres else None


def id_playlist(texte):
    """Identifiant d'une playlist YouTube à partir d'un lien (…?list=PL…) ou de l'identifiant lui-même."""
    texte = (texte or "").strip()
    m = re.search(r"[?&]list=([A-Za-z0-9_-]+)", texte)
    if m:
        return m.group(1)
    return texte if re.fullmatch(r"[A-Za-z0-9_-]{12,}", texte) else ""


def piste_aleatoire(genre, sauf=(), partie=None, reglages=None):
    """Un morceau d'ambiance selon la source réglée (menu ou partie) :
    dossier musique/ -> playlist YouTube -> extraits Deezer (« auto » essaie dans cet ordre)."""
    r = reglages or {}
    menu = genre == "menu"
    source = r.get("musique_menu_source" if menu else "musique_jeu_source", "auto")
    avec_films = bool(r.get("musique_films", True))
    ordre = ["local", "youtube", "deezer"] if source == "auto" else [source, "deezer"]
    for s in ordre:
        if s == "local":
            p = _piste_locale(genre, sauf, partie, avec_films)
        elif s == "youtube":
            pl = id_playlist(r.get("musique_menu_youtube" if menu else "musique_jeu_youtube", ""))
            p = {"id": "yt:" + pl, "source": "youtube", "playlist": pl, "titre": "", "artiste": ""} if pl else None
        else:
            p = _piste_deezer(genre, sauf, partie if avec_films else None)
            if p:
                p = dict(p, source="deezer")
        if p:
            return p
    return None


def fichier_local(ident):
    """(chemin, type MIME) d'un morceau du dossier musique/ (seulement ceux proposés par piste_aleatoire)."""
    chemin = BIBLIO.chemin(ident)
    if not chemin or not os.path.isfile(chemin):
        return None, None
    return chemin, EXT_AUDIO.get(os.path.splitext(chemin)[1].lower(), "application/octet-stream")


def mp3(id_piste):
    """Extrait d'une piste d'ambiance (seulement celles proposées par piste_aleatoire)."""
    if id_piste not in _pistes_connues:
        return None
    with _verrou_mp3:
        if id_piste in _mp3:
            _mp3.move_to_end(id_piste)
            return _mp3[id_piste]
    url = deezer(f"/track/{id_piste}").get("preview")       # lien frais (les liens d'extrait expirent)
    if not url:
        return None
    try:
        data = telecharger(url)
    except (requests.RequestException, ValueError):
        return None
    with _verrou_mp3:
        _mp3[id_piste] = data
        while len(_mp3) > 16:
            _mp3.popitem(last=False)
    return data
