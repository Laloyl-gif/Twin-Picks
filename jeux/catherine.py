"""Catherine's Disguise (Le titre déguisé) : Catherine Martell revient à Twin Peaks déguisée en « Mr. Tojamura ». Ici,
c'est le titre du film qui est déguisé : il est traduit en chaîne dans plusieurs langues (Google Traduction), puis
retraduit en français. Trois cartes de visite arrivent l'une après l'autre : d'abord le titre qui a fait le plus long
voyage (12 langues, le plus déformé), puis 6, puis 3. Chaque carte montre la dernière langue traversée
avant le retour au français. Les trois titres sont différents entre eux et du vrai titre.

Les traductions prennent du temps : elles sont préparées à l'avance, pendant les autres manches (prechauffer, lancé
dès le chargement de la partie) et gardées dans catherine_cache.json. Il faut Internet.
"""
import json
import os
import random
import threading

from tmdb import cle_film, cle_txt, details_film
from texte import normaliser
from traduction import sauver, traduire
from visuels import en_jpeg
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

FICHIER = __import__("config").donnee("catherine_cache2.json")      # v2 : voyages de 12, 6 et 3 langues
LANGUES = {"ja": "japonais", "ru": "russe", "ko": "coréen", "zh-CN": "chinois", "ar": "arabe", "fi": "finnois",
           "hu": "hongrois", "tr": "turc", "el": "grec", "pl": "polonais", "he": "hébreu", "th": "thaï",
           "vi": "vietnamien", "id": "indonésien", "sw": "swahili", "is": "islandais", "hi": "hindi", "uk": "ukrainien",
           "nl": "néerlandais", "sv": "suédois", "cs": "tchèque", "ro": "roumain", "de": "allemand", "it": "italien",
           "pt": "portugais", "es": "espagnol"}
# le tampon rouge de chaque carte : le pays de la dernière langue traversée avant le français
PAYS = {"ja": "JP", "ru": "RU", "ko": "KR", "zh-CN": "CN", "ar": "EG", "fi": "FI", "hu": "HU", "tr": "TR", "el": "GR",
        "pl": "PL", "he": "IL", "th": "TH", "vi": "VN", "id": "ID", "sw": "KE", "is": "IS", "hi": "IN", "uk": "UA",
        "nl": "NL", "sv": "SE", "cs": "CZ", "ro": "RO", "de": "DE", "it": "IT", "pt": "PT", "es": "ES"}
_VERROU = threading.Lock()
_CACHE = None


def _cache():
    global _CACHE
    if _CACHE is None:
        try:
            with open(FICHIER, encoding="utf-8") as f:
                _CACHE = json.load(f)
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def _sauver():
    try:
        with open(FICHIER, "w", encoding="utf-8") as f:
            json.dump(_cache(), f, ensure_ascii=False)
    except OSError:
        pass


def voyage(titre, langues):
    """Le titre traduit de langue en langue, puis en français. None si une traduction échoue.
    Départ en langue détectée (« auto ») : beaucoup de titres français restent en anglais (Mulholland Drive…)."""
    t, src = titre, "auto"
    for l in langues:
        t = traduire(t, src, l)
        if not t:
            return None
        src = l
    return traduire(t, src, "fr")


class HorsLigne(Exception):
    """La traduction ne répond pas (pas d'Internet, service indisponible)."""


# Longueurs de voyage possibles pour chaque carte : toujours de moins en moins de langues d'une carte à l'autre.
LONGUEURS = ((12, 13, 14), (6, 7, 8), (3, 4, 2))
ESSAIS = 2                            # tirages de langues par longueur


def deguiser(titre):
    """[{"titre", "langue", "etapes"}] : trois titres déformés, tous différents entre eux et du vrai titre ; [] si ce
    titre ne se laisse pas déformer (un nom propre que toutes les langues gardent tel quel). HorsLigne si la traduction
    ne répond pas."""
    vus = {normaliser(titre) or titre.lower()}
    cartes = []
    for longueurs in LONGUEURS:
        trouve = None
        for n in longueurs:
            for _ in range(ESSAIS):
                langues = random.sample(list(LANGUES), n)
                res = voyage(titre, langues)
                if res is None:
                    raise HorsLigne()
                n_res = normaliser(res) or res.lower()
                if res.strip() and n_res not in vus:
                    trouve = {"titre": res.strip(), "langue": LANGUES[langues[-1]], "pays": PAYS.get(langues[-1], ""),
                              "etapes": n}
                    vus.add(n_res)
                    break
            if trouve:
                break
        if not trouve:
            sauver()
            return []
        cartes.append(trouve)
    sauver()
    return cartes


def _pret(f):
    """Les cartes d'un film déjà préparé (None : pas encore préparé ; [] : titre impossible à déguiser)."""
    with _VERROU:
        return _cache().get(cle_txt(f))


def _preparer(f):
    cartes = deguiser(f["title"])
    with _VERROU:
        _cache()[cle_txt(f)] = cartes
        _sauver()
    return cartes


_EN_COURS = threading.Event()


def prechauffer(films, nb):
    """En tâche de fond : prépare les titres déguisés de nb films de plus (pas encore préparés), pendant que l'on joue.
    Un titre impossible à déguiser est noté (et ne sera plus essayé) ; on ne s'arrête que si Internet manque."""
    if _EN_COURS.is_set():
        return
    _EN_COURS.set()

    def travail():
        try:
            a_faire = [f for f in films if not f.get("tv") and _pret(f) is None]
            random.shuffle(a_faire)
            faits = 0
            for f in a_faire[:nb * 4]:
                if faits >= nb:
                    break
                try:
                    if _preparer(f):
                        faits += 1
                except HorsLigne:
                    return
                except Exception:  # noqa: BLE001
                    continue
        finally:
            _EN_COURS.clear()
    threading.Thread(target=travail, daemon=True).start()


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_catherine"])
    films = [f for f in pool if not f.get("tv")]
    if not films:
        raise RuntimeError("Le titre déguisé : aucun film dans les listes choisies.")
    cartes, film = None, None
    for _ in range(12):
        # d'abord un film déjà préparé et pas encore joué dans cette partie ; sinon un autre film, préparé tout de suite
        prets = [f for f in films if _pret(f) and cle_film(f) not in deja]
        film = tirer(prets, deja) if prets else tirer(films, deja)
        cartes = _pret(film)
        if cartes is None:
            try:
                cartes = _preparer(film)
            except HorsLigne:
                raise RuntimeError("Le titre déguisé : la traduction automatique ne répond pas (il faut Internet).")
        if cartes:
            break
    if not cartes:
        raise RuntimeError("Le titre déguisé : aucun titre des listes ne se laisse déguiser.")
    prechauffer(films, 3)                       # on garde toujours quelques films d'avance
    d = details_film(api, film)
    n = len(cartes)
    etat = {"cartes": [], "total": n, "indices": [], "trous": ""}
    evts = [(round(duree * 0.6 * k / max(1, n - 1), 2), lambda k=k: etat.update(cartes=cartes[:k + 1])) for k in range(n)]
    if cfg.get("catherine_trous", True):
        evts.append((duree * 0.8, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "cartes": [dict(c) for c in etat["cartes"]], "indices": list(etat["indices"])})
    m = manche_titre("catherine", "titres", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
    m["detail"] = " · ".join(f"{c['titre']} ({c['etapes']} langues)" for c in cartes)
    return m
