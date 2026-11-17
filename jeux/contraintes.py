"""Contraintes sur les films, pour Lucy's Hotline (chrono) et One-Eyed Donna's (bingo).

Une contrainte :
    {"type", "txt", "test": f(film, fiche|None) -> bool, "fiche": True si le test a besoin des détails du film,
     "valides": f() -> films connus qui la respectent (pour les « oubliés » et pour vérifier une grille)}

Les joueurs peuvent répondre avec n'importe quel film de TMDB (pas seulement ceux des listes) : le film tapé
est cherché dans les listes, puis sur TMDB. Les contraintes « personne » (acteur, réalisateur, compositeur)
peuvent proposer plusieurs noms (« Avec A, B ou C ») : un film avec l'un d'eux compte. De même, « le mot … dans le
titre » propose trois mots.
Acteurs : acteurs.txt ; réalisateurs : toujours realisateurs.txt (réglable), limités à ceux que les joueurs
connaissent (profils). « Un nombre dans le titre » : en chiffres ou en lettres (« Wild Horse Nine »), jamais un film
de saga (« Toy Story 2 » ne compte pas).
"""
import os
import random
import re
from collections import Counter

import sagas
from config import CONTRAINTES, DOSSIER, FICHIER_CACHE_REALISATEURS
from recherche import chercher_films, meilleur_film
from texte import cle, correspond, normaliser, suggerer
from tmdb import (GENRES, LANGUES, _film, charger_acteurs, cle_film, cle_txt, decouvrir, fiche, film_de_profil,
                  filmographie, identifiant, ids_personne, libelle, lire_noms, resoudre_personnes)
from .commun import cles_reponses

AVEC_FICHE = {"pays", "duree", "boxoffice", "saga", "theme"}   # le film tapé est vérifié avec ses détails
LENTES = {"pays", "duree", "boxoffice", "saga"}       # pas de vérification rapide : exclues des grilles « lignes »
PAYS = {"FR": "France", "GB": "Royaume-Uni", "JP": "Japon", "KR": "Corée du Sud", "IT": "Italie", "ES": "Espagne",
        "DE": "Allemagne", "CA": "Canada", "AU": "Australie", "IN": "Inde", "MX": "Mexique", "DK": "Danemark",
        "SE": "Suède", "NZ": "Nouvelle-Zélande", "HK": "Hong Kong", "BE": "Belgique", "IE": "Irlande",
        "CN": "Chine", "BR": "Brésil", "NO": "Norvège"}
PAYS_LANGUE = {"fr": "FR", "ja": "JP", "ko": "KR", "it": "IT", "es": "ES", "de": "DE", "hi": "IN", "da": "DK",
               "sv": "SE", "cn": "HK", "zh": "CN", "pt": "BR", "no": "NO"}
MOTS = [("nuit", "night"), ("amour", "love"), ("homme", "man"), ("mort", "dead|death"), ("roi", "king"),
        ("noir", "black"), ("rouge", "red"), ("jour", "day"), ("guerre", "war"), ("monde", "world"),
        ("fille", "girl"), ("vie", "life"), ("dernier", "last"), ("ville", "city"), ("ciel", "sky"),
        ("maison", "house|home"), ("star", "star"), ("dieu", "god"), ("enfer", "hell"), ("sang", "blood")]


def _annee(f):
    try:
        return int((f.get("release_date") or "")[:4])
    except ValueError:
        return None


def _titres(f):
    return [t for t in (f.get("title"), f.get("original_title")) if t]


class Ctx:
    """Ce dont les générateurs ont besoin : l'API, les réglages, les films des listes, les personnes des fichiers."""

    def __init__(self, api, cfg, pool, nb_personnes=1, realisateurs_ok=None, sauf=None):
        self.api, self.cfg, self.pool = api, cfg, [f for f in pool if f]
        self.films = [f for f in self.pool if not f.get("tv")]
        self.nb = max(1, int(nb_personnes))
        # « notes d'un autre joueur » : jamais les notes du joueur à qui la grille est destinée
        self.profils = [p for p in cfg.get("_profils", []) if p.get("nom") != sauf]
        self.realisateurs_ok = realisateurs_ok          # noms (clés) que les joueurs connaissent ; None : tous

    def acteurs(self):
        k = ("ctx", "acteurs")
        if k not in self.api._details:
            try:
                self.api._details[k] = charger_acteurs(self.api)
            except Exception:  # noqa: BLE001
                self.api._details[k] = []
        return self.api._details[k]

    def realisateurs(self):
        """Réalisateurs du fichier (realisateurs.txt par défaut), limités à ceux que les joueurs connaissent."""
        tous = realisateurs_fichier(self.api, self.cfg)
        if self.realisateurs_ok is None:
            return tous
        return [p for p in tous if cle(p["name"]) in self.realisateurs_ok or cle(p.get("nom_fichier", "")) in self.realisateurs_ok]


def chemin_realisateurs(cfg):
    chemin = (cfg.get("realisateurs_fichier") or "").strip().strip('"') or "realisateurs.txt"
    chemin = os.path.expanduser(chemin)
    return chemin if os.path.isabs(chemin) else os.path.join(DOSSIER, chemin)


def noms_realisateurs(cfg):
    """Les noms du fichier de réalisateurs (pour cocher ceux que l'on connaît dans un profil)."""
    return lire_noms(chemin_realisateurs(cfg))


def connus_communs(profils):
    """Réalisateurs connus de TOUS les profils présents qui en ont choisi (clés) ; None si aucun n'a choisi."""
    choix = [{cle(n) for n in p["realisateurs"]} for p in profils if p.get("realisateurs") is not None]
    return set.intersection(*choix) if choix else None


def connus_de(profil):
    return None if not profil or profil.get("realisateurs") is None else {cle(n) for n in profil["realisateurs"]}


def realisateurs_fichier(api, cfg):
    chemin = chemin_realisateurs(cfg)
    k = ("ctx", "realisateurs", chemin)
    if k not in api._details:
        noms = lire_noms(chemin)
        try:
            personnes = resoudre_personnes(api, noms, FICHIER_CACHE_REALISATEURS, "Directing")
        except Exception:  # noqa: BLE001
            personnes = []
        # le nom tel qu'il est écrit dans le fichier (c'est lui que l'on coche dans les profils)
        par_cle = {cle(n): n for n in noms}
        api._details[k] = [dict(p, nom_fichier=par_cle.get(cle(p["name"]), p["name"])) for p in personnes]
    return api._details[k]


def _c(type_, txt, test, valides=lambda: [], fiche=False, **kw):
    return dict(type=type_, txt=txt, test=test, valides=valides, fiche=fiche or type_ in AVEC_FICHE, **kw)


# ---------------- générateurs (None quand impossible) ----------------
def g_genre(x):
    seeds = [f for f in x.films if any(g in GENRES for g in f.get("genre_ids") or [])]
    if not seeds:
        return None
    g = random.choice([g for g in random.choice(seeds)["genre_ids"] if g in GENRES])

    def test(f, fi=None):
        return g in (f.get("genre_ids") or []) or bool(fi) and g in fi.get("genre_ids", [])
    return _c("genre", f"Genre : {GENRES[g]}", test, lambda: [f for f in x.films if test(f)])


def g_decennie(x):
    seeds = [f for f in x.films if _annee(f)]
    if not seeds:
        return None
    d = _annee(random.choice(seeds)) // 10 * 10

    def test(f, fi=None):
        return (_annee(f) or 0) // 10 * 10 == d
    return _c("decennie", f"Sorti dans les années {d}", test, lambda: [f for f in x.films if test(f)])


def g_periode(x):
    seeds = [f for f in x.films if _annee(f)]
    if not seeds:
        return None
    a = _annee(random.choice(seeds))
    if random.random() < 0.5 and sum(1 for f in seeds if _annee(f) == a) >= 3:
        lo, hi, txt = a, a, f"Sorti en {a}"
    else:
        lo = a // 5 * 5
        hi, txt = lo + 4, f"Sorti entre {lo} et {lo + 4}"

    def test(f, fi=None):
        return lo <= (_annee(f) or 0) <= hi
    return _c("periode", txt, test, lambda: [f for f in x.films if test(f)])


def g_note(x):
    notes = [f for f in x.films if f.get("votes", 0) >= 100]
    if not notes:
        return None
    seed = random.choice(notes)["note"]
    if seed >= 7.5:
        txt, test = "Noté 7,5 ou plus sur TMDB", lambda f, fi=None: f.get("note", 0) >= 7.5 and f.get("votes", 0) >= 50
    elif seed < 6.5:
        txt, test = "Noté moins de 6,5 sur TMDB", lambda f, fi=None: 0 < f.get("note", 0) < 6.5 and f.get("votes", 0) >= 50
    else:
        txt, test = "Noté entre 6,5 et 7,5 sur TMDB", lambda f, fi=None: 6.5 <= f.get("note", 0) < 7.5
    return _c("note", txt, test, lambda: [f for f in x.films if test(f)])


def g_langue(x):
    seeds = [f for f in x.films if f.get("langue") and f["langue"] != "en"]
    if not seeds:
        return None
    l = random.choice(seeds)["langue"]

    def test(f, fi=None):
        return (f.get("langue") or (fi or {}).get("langue")) == l
    return _c("langue", f"Langue originale : {LANGUES.get(l, l)}", test, lambda: [f for f in x.films if test(f)])


METIERS = {"acteur": (None, "Avec"), "realisateur": ("Director", "Réalisé par"), "compositeur": ("compositeur", "Musique de")}


def _liste_noms(noms):
    return noms[0] if len(noms) == 1 else ", ".join(noms[:-1]) + " ou " + noms[-1]


def _personnes(x, metier, nb):
    """Contrainte « Avec A, B ou C » (ou réalisateur / compositeur) : nb personnes avec assez de films connus."""
    job, debut = METIERS[metier]
    api = x.api
    cands = []
    if metier == "acteur":
        cands = [{"id": p["id"], "nom": p["name"]} for p in x.acteurs()]
    elif metier == "realisateur":                     # toujours le fichier (jamais les films des listes)
        cands = [{"id": p["id"], "nom": p["name"]} for p in x.realisateurs()]
        if not cands:
            return None
    if not cands:                                     # compositeurs : ceux des films des listes
        for seed in random.sample(x.films, min(8, len(x.films))):
            try:
                fi = fiche(api, seed)
            except Exception:  # noqa: BLE001
                continue
            gens = {"acteur": fi["acteurs"][:3], "realisateur": fi["realisateurs"][:1],
                    "compositeur": fi["compositeurs"][:1]}[metier]
            cands += [{"id": p["id"], "nom": p["nom"]} for p in gens]
    random.shuffle(cands)
    choisis, vus = [], set()
    for p in cands[:nb * 4 + 4]:
        if p["id"] in vus:
            continue
        vus.add(p["id"])
        try:
            films = filmographie(api, p["id"], job)
            ids = ids_personne(api, p["id"], job)
        except Exception:  # noqa: BLE001
            continue
        utiles = [f for f in films if f.get("ordre", 0) <= 20] if metier == "acteur" else films
        if len(utiles) < (4 if metier == "acteur" else 3):
            continue
        choisis.append((p, ids, utiles))
        if len(choisis) == nb:
            break
    if not choisis:
        return None
    tous_ids = set().union(*(ids for _, ids, _ in choisis))
    valides = [f for _, _, films in choisis for f in films]
    return _c(metier, f"{debut} {_liste_noms([p['nom'] for p, _, _ in choisis])}",
              lambda f, fi=None: not f.get("tv") and f["id"] in tous_ids, lambda: valides,
              personnes=[p["nom"] for p, _, _ in choisis])


def g_acteur(x):
    return _personnes(x, "acteur", x.nb)


def g_realisateur(x):
    return _personnes(x, "realisateur", x.nb)


def g_compositeur(x):
    return _personnes(x, "compositeur", x.nb)


def g_pays(x):
    langues = [PAYS_LANGUE[f["langue"]] for f in x.films if f.get("langue") in PAYS_LANGUE]
    code = random.choice(langues) if langues and random.random() < 0.7 else random.choice(list(PAYS))
    return _c("pays", f"Pays de production : {PAYS[code]}", lambda f, fi=None: bool(fi) and code in fi["pays_codes"])


def g_duree(x):
    txt, lo, hi = random.choice([("Dure plus de 2 h 30", 150, 999), ("Dure moins de 1 h 30", 40, 90),
                                 ("Dure plus de 2 h 45", 165, 999)])
    return _c("duree", txt, lambda f, fi=None: bool(fi) and lo <= (fi.get("duree") or 0) <= hi)


def g_boxoffice(x):
    txt, seuil = random.choice([("Plus d'un milliard de dollars au box-office", 1e9),
                                ("Plus de 500 millions de dollars au box-office", 5e8)])
    return _c("boxoffice", txt, lambda f, fi=None: bool(fi) and (fi.get("recettes") or 0) >= seuil)


def g_saga(x):
    return _c("saga", "Un film qui fait partie d'une saga", lambda f, fi=None: bool(fi) and bool(fi.get("collection_id")),
              lambda: [f for f in x.films if sagas.saga(f)])


# Nombres écrits en lettres (anglais, français, quelques autres) : « Wild Horse Nine », « Les Sept Samouraïs »…
# (« un », « une » et « one » sont exclus : ce sont surtout des articles.)
NOMBRES_LETTRES = set("""two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen
seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred hundreds thousand thousands
million millions billion dozen second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth
twentieth hundredth thousandth deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize
vingt vingts trente quarante cinquante soixante cent cents mille million milliard douzaine deuxieme troisieme
quatrieme cinquieme sixieme septieme huitieme neuvieme dixieme centieme millieme
dos tres cuatro cinco seis siete ocho nueve diez cien mil due tre quattro cinque sette otto nove dieci cento
zwei drei vier funf sechs sieben acht neun zehn hundert tausend""".split())


def nombre_dans(titre):
    """Vrai si le titre contient un nombre, en chiffres (« 300 », « 2001 ») ou en lettres (« Nine », « Sept »)."""
    if re.search(r"\d", titre):
        return True
    return any(m in NOMBRES_LETTRES for m in normaliser(titre).split())


def hors_saga(f, fi=None):
    """Vrai si le film n'appartient à aucune saga (détails du film, sinon le cache des sagas)."""
    if fi is not None:
        return not fi.get("collection_id")
    s = sagas.saga(f)
    return s is None or s is False and not re.search(r"\b(\d+|ii|iii|iv|v|vi)\s*$", normaliser(f.get("title") or ""))


def g_titre(x):
    films = x.films
    variantes = []
    premieres = Counter(k[0] for f in films for k in {cle(t) for t in _titres(f)} if k and k[0].isalpha())
    lettres = [l for l, n in premieres.items() if n >= 6]
    if lettres:
        l = random.choice(lettres)
        variantes.append((f"Titre qui commence par « {l.upper()} » (sans compter l'article)",
                          lambda f, fi=None, l=l: any(cle(t).startswith(l) for t in _titres(f)), False))
    variantes.append(("Titre en un seul mot", lambda f, fi=None: any(len(cle(t).split()) == 1 for t in _titres(f)), False))
    variantes.append(("Un nombre dans le titre, en chiffres ou en lettres (hors sagas)",
                      lambda f, fi=None: any(nombre_dans(t) for t in _titres(f)) and hors_saga(f, fi), True))
    # trois mots au choix, comme les trois réalisateurs : « nuit », « roi » ou « sang »
    utiles = [(fr, en, re.compile(rf"\b({fr}s?|{en}s?)\b")) for fr, en in MOTS]
    utiles.sort(key=lambda m: -sum(1 for f in films if any(m[2].search(normaliser(t)) for t in _titres(f))))
    if len(utiles) >= 3:
        trois = random.sample(utiles[:12], 3)
        motifs = [m for _, _, m in trois]
        noms = [f"« {fr} »" + (f" (« {en.split('|')[0]} »)" if en.split("|")[0] != fr else "") for fr, en, _ in trois]
        variantes.append((f"Le mot {noms[0]}, {noms[1]} ou {noms[2]} dans le titre",
                          lambda f, fi=None, ms=motifs: any(m.search(normaliser(t)) for m in ms for t in _titres(f)),
                          False))
    txt, test, avec_fiche = random.choice(variantes)
    return _c("titre", txt, test, lambda: [f for f in films if test(f)], fiche=avec_fiche)


# Thèmes : (libellé français, mot-clé TMDB en anglais)
THEMES = [("des zombies", "zombie"), ("un voyage dans le temps", "time travel"), ("un requin", "shark"),
          ("des vampires", "vampire"), ("des extraterrestres", "alien"), ("des robots", "robot"),
          ("un braquage", "heist"), ("un tueur en série", "serial killer"), ("des dinosaures", "dinosaur"),
          ("des super-héros", "superhero"), ("de la boxe", "boxing"), ("une sorcière", "witch"),
          ("un fantôme", "ghost"), ("une prison", "prison"), ("Noël", "christmas"), ("la mafia", "mafia"),
          ("un espion", "spy"), ("des pirates", "pirate"), ("une boucle temporelle", "time loop"),
          ("un dragon", "dragon"), ("une intelligence artificielle", "artificial intelligence (a.i.)"),
          ("un loup-garou", "werewolf"), ("un clown", "clown"), ("des jumeaux", "twins"), ("un mariage", "wedding"),
          ("un sous-marin", "submarine"), ("l'espace", "outer space"), ("la danse", "dance"), ("un chien", "dog"),
          ("une maison hantée", "haunted house"), ("un road trip", "road trip"), ("un tremblement de terre", "earthquake"),
          ("un naufrage", "shipwreck"), ("la fin du monde", "end of the world"), ("un procès", "trial"),
          ("des chevaliers", "knight"), ("un jeu vidéo", "video game"), ("un casse", "robbery")]


def g_theme(x):
    for fr, en in random.sample(THEMES, len(THEMES))[:4]:
        try:
            kid = identifiant(x.api, "keyword", en)
            films = decouvrir(x.api, 2, with_keywords=kid) if kid else []
        except Exception:  # noqa: BLE001
            continue
        if len(films) < 8:
            continue
        ids = {f["id"] for f in films}
        return _c("theme", f"Un film avec {fr}",
                  lambda f, fi=None, ids=ids, kid=kid: not f.get("tv") and (f["id"] in ids or bool(fi) and kid in (fi.get("mots_cles_ids") or [])),
                  lambda films=films: films)
    return None


VARIANTES_JOUEURS = ["adore", "deteste", "exact"]


def _variante_ok(p, variante):
    """Pour une variante (« adore », « deteste », « exact »), le seuil possible pour ce profil (ou None)."""
    notes = [n for k, n in p["notes"].items() if k.startswith("m:")]
    if variante == "adore":
        return 8 if sum(1 for n in notes if n >= 8) >= 5 else None
    if variante == "deteste":
        return 4 if sum(1 for n in notes if n <= 4) >= 5 else None
    possibles = [v for v, c in Counter(notes).items() if 5 <= v <= 9 and c >= 5]
    return random.choice(possibles) if possibles else None


def pour_profil(p, pool, variante="adore", seuil=None):
    seuil = seuil if seuil is not None else _variante_ok(p, variante)
    if seuil is None:
        return None
    par_cle = {cle_txt(f): f for f in pool}
    notes = p["notes"]
    ok = {"adore": lambda n: n >= seuil, "deteste": lambda n: n <= seuil, "exact": lambda n: n == seuil}[variante]
    txt = {"adore": f"Noté {seuil} ou plus par {p['nom']}", "deteste": f"Noté {seuil} ou moins par {p['nom']}",
           "exact": f"Noté exactement {seuil} par {p['nom']}"}[variante]
    return _c("joueurs", txt, lambda f, fi=None: ok(notes.get(cle_txt(f), -99)),
              lambda: [par_cle.get(k) or film_de_profil(k, p["films"].get(k, {}))
                       for k, n in notes.items() if ok(n)], profil=p["nom"], variante=variante, seuil=seuil)


def g_joueurs(x):
    for variante in random.sample(VARIANTES_JOUEURS, 3):
        ok = [p for p in x.profils if _variante_ok(p, variante) is not None]
        if ok:
            return pour_profil(random.choice(ok), x.pool, variante)
    return None


GENERATEURS = {"genre": g_genre, "decennie": g_decennie, "periode": g_periode, "realisateur": g_realisateur,
               "acteur": g_acteur, "compositeur": g_compositeur, "note": g_note, "langue": g_langue, "pays": g_pays,
               "duree": g_duree, "boxoffice": g_boxoffice, "saga": g_saga, "theme": g_theme,
               "titre": g_titre, "joueurs": g_joueurs}
assert set(GENERATEURS) == set(CONTRAINTES)


def actives(cfg, prefixe, profils, sans_fiche=False):
    ks = [k for k in CONTRAINTES if cfg.get(prefixe + k, True)] or ["genre", "decennie"]
    if prefixe == "lucy_":
        ks = [k for k in ks if k != "saga"] or ["genre", "decennie"]        # Chrono : jamais « film d'une saga »
    ks = [k for k in ks if k != "joueurs" or profils] or ["genre", "decennie"]
    if sans_fiche:
        ks = [k for k in ks if k not in LENTES] or ["genre", "decennie"]
    return ks


def generer(x, prefixe, exclues=(), types=None, sans_fiche=False):
    """Une contrainte d'un type actif, différente de celles déjà prises (types tirés à parts égales)."""
    ks = types or actives(x.cfg, prefixe, x.profils, sans_fiche)
    for k in random.sample(ks, len(ks)) * 2:
        try:
            c = GENERATEURS[k](x)
        except Exception:  # noqa: BLE001
            c = None
        if c and c["txt"] not in exclues:
            return c
    return None


# ---------------- reconnaître un film tapé ----------------
ANNEE_FIN = re.compile(r"^(.*?)\s*\((\d{4})\)\s*$")


def separer(texte):
    """« Dune (2021) » -> ("Dune", 2021)."""
    m = ANNEE_FIN.match(str(texte or "").strip())
    return (m.group(1), int(m.group(2))) if m else (str(texte or "").strip(), None)


def index(films):
    """[(film, clés de ses titres)] pour comparer les réponses."""
    out, vus = [], set()
    for f in films:
        if not f or cle_film(f) in vus:
            continue
        vus.add(cle_film(f))
        out.append((f, cles_reponses(f.get("title") or "", f.get("original_title") or "")))
    return out


def chercher(texte, idx):
    """Le film de l'index qui correspond le mieux au texte (titre exact d'abord, l'année départage)."""
    titre, an = separer(texte)
    k = cle(titre)
    if not k:
        return None

    def meilleur(cands):
        if not cands:
            return None
        if an:
            bons = [f for f in cands if _annee(f) and abs(_annee(f) - an) <= 1]
            if bons:
                return max(bons, key=lambda f: (_annee(f) == an, f.get("votes", 0)))
            return None
        return max(cands, key=lambda f: f.get("votes", 0))
    exacts = meilleur([f for f, cles in idx if k in cles])
    if exacts:
        return exacts
    return meilleur([f for f, cles in idx if any(correspond(titre, c) for c in cles)])


def chercher_tmdb(api, texte):
    """Recherche TMDB (films) quand le titre n'est pas dans les listes."""
    titre, an = separer(texte)
    if not cle(titre):
        return None
    try:
        res = api.get("/search/movie", query=titre, **({"primary_release_year": an} if an else {})).get("results", [])
        if an and not res:
            res = api.get("/search/movie", query=titre).get("results", [])
    except Exception:  # noqa: BLE001
        return None
    films = [_film(dict(r, media_type="movie")) for r in res[:10] if r.get("title")]
    return chercher(texte, index(films))


def resoudre(api, texte, idx, avec_fiche=False):
    """Film tapé par un joueur -> {"film", "fiche"} (listes d'abord, puis TMDB)."""
    texte = str(texte or "").strip()
    if not texte:
        return None
    f = chercher(texte, idx) or chercher_tmdb(api, texte)
    if not f:
        try:
            f = meilleur_film(api, texte)              # saisie partielle ou faute de frappe : le film le plus probable
        except Exception:  # noqa: BLE001
            f = None
    if not f:
        return {"film": None}
    fi = None
    if avec_fiche:
        try:
            fi = fiche(api, f)
        except Exception:  # noqa: BLE001
            fi = None
    return {"film": f, "fiche": fi}


# ---------------- suggestions : films des listes + recherche TMDB ----------------
def entrees_films(films):
    """[(libellé « Titre (année) », [(nom, clé)])] pour suggerer()."""
    out, vus = [], set()
    for f in films:
        if not f or cle_film(f) in vus or f.get("tv"):
            continue
        vus.add(cle_film(f))
        noms = list(dict.fromkeys(n for n in _titres(f)))
        out.append((libelle(f), [(n, cle(n)) for n in noms if cle(n)]))
    return out


def suggerer_films(api, q, entrees, n=8):
    """Suggestions « Titre (année) » : TOUS les films de TMDB (recherche intelligente : « pulp » -> Pulp Fiction),
    les films des listes passant devant à pertinence égale."""
    locaux = suggerer(q, entrees, 6, valeur="libelle")
    try:
        distants = chercher_films(api, q, n + 4)
    except Exception:  # noqa: BLE001
        distants = []
    res, vus = [], set()
    # 1) les films des listes qui commencent vraiment par ce qui est tapé ; 2) TMDB ; 3) le reste des listes
    debut = [r for r in locaux if any(m.startswith(cle(q)) for m in [cle(r["v"])] + cle(r["v"]).split())] if cle(q) else []
    for r in debut[:3] + distants + locaux:
        if r["v"] not in vus:
            vus.add(r["v"])
            res.append(r)
    return res[:n]
