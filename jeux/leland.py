"""L'intrus : trouvez l'intrus parmi plusieurs films (ou acteurs).

Catégories (désactivables dans les réglages) : même réalisateur, même compositeur, même scénariste, même directeur
de la photo, même acteur, même duo d'acteurs, acteurs d'un même film (l'intrus n'y a pas joué), même genre, même
décennie, même année, même langue originale, même pays de production, même thème (mot-clé TMDB),
durée (très longs ou très courts), note TMDB (les bien notés contre un mal noté), notes des joueurs.
Les films s'affichent sans leur année. Au bout de 5 s : la nature de la différence (« Décennie différente »…),
puis un indice plus précis ; à la fin, on révèle le sujet.
Jamais deux films de la même saga ou du même univers (sinon trois Spider-Man et un intrus, c'est trop facile).
Acteurs et réalisateurs : toujours des personnes des listes de référence (acteurs.txt, réalisateurs du fichier ;
et, si les joueurs présents ont coché les réalisateurs qu'ils connaissent, seulement ceux-là).
"""
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from PIL import ImageOps

import sagas
from config import INTRUS
from tmdb import (GENRES, LANGUES, charger_acteurs, cle, cle_film, cle_txt, decouvrir, fiche, film_de_profil, filmographie,
                  identifiant)
from .contraintes import THEMES, connus_communs, realisateurs_fichier
from visuels import en_jpeg
from .commun import affiche, chronologie

CONNU = 300                     # votes TMDB minimum pour un film « connu »
NATURE_DELAI = 5.0              # la nature de la différence s'affiche au bout de 5 s
NATURES = {"realisateur": "Réalisateur différent", "compositeur": "Compositeur différent",
           "scenariste": "Scénariste différent", "photo": "Directeur de la photo différent",
           "acteur": "Un acteur absent", "duo": "Un duo d'acteurs séparé", "casting": "Pas dans le même film",
           "genre": "Genre différent", "decennie": "Décennie différente", "annee": "Année de sortie différente",
           "langue": "Langue différente", "pays": "Pays de production différent",
           "theme": "Thème différent", "duree": "Durée différente", "note": "Note TMDB différente",
           "joueurs": "Note d'un joueur différente"}
PAYS_NOMS = {"FR": "France", "GB": "Royaume-Uni", "JP": "Japon", "KR": "Corée du Sud", "IT": "Italie", "ES": "Espagne",
             "DE": "Allemagne", "CA": "Canada", "AU": "Australie", "IN": "Inde", "MX": "Mexique", "DK": "Danemark",
             "SE": "Suède", "NZ": "Nouvelle-Zélande", "HK": "Hong Kong", "BE": "Belgique", "IE": "Irlande",
             "CN": "Chine", "BR": "Brésil", "NO": "Norvège", "US": "États-Unis"}


def initiales(nom):
    return " ".join(m[0].upper() + "." for m in nom.replace("-", " ").split() if m[:1].isalpha())


def note_txt(x):
    return f"{x:.1f}".replace(".", ",")


def proches(cands, groupe):
    """Les intrus possibles les plus « crédibles » : même époque ou genre que le groupe."""
    annees = [int(f["release_date"][:4]) for f in groupe if f.get("release_date")]
    genres = {g for f in groupe for g in f.get("genre_ids") or []}

    def score(f):
        s = 0
        if annees and f.get("release_date"):
            s += abs(int(f["release_date"][:4]) - sum(annees) / len(annees)) <= 10
        s += bool(set(f.get("genre_ids") or []) & genres)
        return s
    if not cands:
        return None
    meilleur = max(map(score, cands))
    return random.choice([f for f in cands if score(f) == meilleur])


def _fiche(x, f):
    if f.get("tv"):
        return None
    try:
        return fiche(x.api, f)
    except Exception:  # noqa: BLE001
        return None


def distincts(x, cands, k, avec=()):
    """k films de cands, deux à deux de sagas et d'univers différents (et différents des films de `avec`).
    None si on n'en trouve pas assez."""
    pris = [(f, _fiche(x, f)) for f in avec]
    choisis, lus = [], 0
    for f in random.sample(cands, len(cands)):
        if any(sagas.meme_univers(f, g) for g, _ in pris):           # test rapide (cache, titres)
            continue
        if lus > k + 12:
            break
        lus += 1
        fi = _fiche(x, f)
        if any(sagas.meme_univers(f, g, fi, gi) for g, gi in pris):
            continue
        pris.append((f, fi))
        choisis.append(f)
        if len(choisis) == k:
            return choisis
    return None


def intrus_de(x, cands, groupe):
    """Un intrus crédible (même époque / genre) qui n'est d'aucune saga ni univers du groupe."""
    ok = [f for f in cands if not any(sagas.meme_univers(f, g) for g in groupe)]
    for _ in range(4):
        f = proches(ok, groupe)
        if not f:
            return None
        fi = _fiche(x, f)
        if not any(sagas.meme_univers(f, g, fi, _fiche(x, g)) for g in groupe):
            return f
        ok = [g for g in ok if g is not f]
    return None


class Ctx:
    def __init__(self, api, cfg, pool):
        self.api, self.cfg, self.n = api, cfg, cfg["leland_nb"]
        self.films = [f for f in pool if not f["tv"] and f.get("poster_path")]
        self.ids = {f["id"] for f in self.films}
        self.profils = cfg.get("_profils", [])
        self._fiches = None
        self._acteurs = self._realisateurs = None

    def acteurs_ok(self):
        """Identifiants TMDB des acteurs de acteurs.txt (les seuls que l'on fait deviner)."""
        if self._acteurs is None:
            k = ("leland", "acteurs")
            if k not in self.api._details:
                try:
                    self.api._details[k] = {a["id"] for a in charger_acteurs(self.api)}
                except Exception:  # noqa: BLE001
                    self.api._details[k] = set()
            self._acteurs = self.api._details[k]
        return self._acteurs

    def realisateurs_ok(self):
        """Identifiants des réalisateurs du fichier (restreints à ceux que connaissent tous les profils, s'ils en ont coché)."""
        if self._realisateurs is None:
            try:
                connus = connus_communs(self.profils)
                self._realisateurs = {p["id"] for p in realisateurs_fichier(self.api, self.cfg)
                                      if connus is None or cle(p["nom_fichier"]) in connus}
            except Exception:  # noqa: BLE001
                self._realisateurs = set()
        return self._realisateurs

    def fiches(self, k=36):
        """Détails d'un échantillon des films des listes (lus en parallèle, une fois par manche)."""
        if self._fiches is None:
            ech = random.sample(self.films, min(k, len(self.films)))
            with ThreadPoolExecutor(max_workers=8) as ex:
                self._fiches = [(f, fi) for f, fi in zip(ech, ex.map(lambda f: _fiche(self, f), ech)) if fi]
        return self._fiches


def graines(x, test, k):
    """Films de départ : d'abord ceux de l'échantillon dont la fiche passe le test (une personne des listes de
    référence), puis quelques films au hasard."""
    bons = [f for f, fi in x.fiches() if test(fi)]
    random.shuffle(bons)
    vus = {f["id"] for f in bons}
    return bons[:k] + [f for f in random.sample(x.films, min(k, len(x.films))) if f["id"] not in vus][:max(0, k - len(bons))]


# ---------------- catégories (chacune retourne None si elle ne trouve rien) ----------------
def c_genre(x):
    n, films = x.n, x.films
    compte = Counter(g for f in films for g in set(f["genre_ids"]))
    genres = [g for g, c in compte.items() if g in GENRES and n - 1 <= c < len(films)]
    random.shuffle(genres)
    for g in genres:
        avec = [f for f in films if g in f["genre_ids"]]
        sans = [f for f in films if f["genre_ids"] and g not in f["genre_ids"]]
        groupe = distincts(x, avec, n - 1) if len(avec) >= n - 1 and sans else None
        intrus = intrus_de(x, sans, groupe) if groupe else None
        if intrus:
            nom = GENRES[g]
            return dict(groupe=groupe, intrus=intrus, sujet=f"{n - 1} films « {nom} »… sauf l'intrus",
                        indices=["Une histoire de genre", f"Le genre commun commence par « {nom[0]} »"],
                        info=lambda f: ", ".join(GENRES[i] for i in f["genre_ids"][:3] if i in GENRES))
    return None


def c_decennie(x):
    n, films = x.n, [f for f in x.films if f.get("release_date")]
    dec = lambda f: int(f["release_date"][:3]) * 10     # noqa: E731
    compte = Counter(map(dec, films))
    choix = [d for d, c in compte.items() if c >= n - 1]
    random.shuffle(choix)
    for d in choix:
        sans = [f for f in films if dec(f) != d]
        voisins = [f for f in sans if abs(dec(f) - d) == 10] or sans
        groupe = distincts(x, [f for f in films if dec(f) == d], n - 1) if voisins else None
        intrus = intrus_de(x, voisins, groupe) if groupe else None
        if intrus:
            return dict(groupe=groupe, intrus=intrus,
                        sujet=f"{n - 1} films des années {d}… sauf l'intrus",
                        indices=["Une question d'époque", "Regardez les dates de sortie"],
                        info=lambda f: f["release_date"][:4])
    return None


def c_langue(x):
    n, films = x.n, [f for f in x.films if f.get("langue")]
    compte = Counter(f["langue"] for f in films)
    choix = [l for l, c in compte.items() if c >= n - 1 and l != "en"]
    random.shuffle(choix)
    for l in choix + (["en"] if compte.get("en", 0) >= n - 1 else []):
        sans = [f for f in films if f["langue"] != l]
        groupe = distincts(x, [f for f in films if f["langue"] == l], n - 1) if sans else None
        intrus = intrus_de(x, sans, groupe) if groupe else None
        if intrus:
            nom = LANGUES.get(l, l)
            return dict(groupe=groupe, intrus=intrus,
                        sujet=f"{n - 1} films tournés en {nom}… sauf l'intrus", indices=["Écoutez bien",
                                                                                         "Pensez à la langue originale"],
                        info=lambda f: LANGUES.get(f["langue"], f["langue"]))
    return None


def c_note(x):
    n = x.n
    films = [f for f in x.films if f["votes"] >= 200]
    hauts = [f for f in films if f["note"] >= 7.6]
    bas = [f for f in films if f["note"] <= 6.2]
    variantes = []
    if len(hauts) >= n - 1 and bas:
        variantes.append((hauts, bas, f"{n - 1} films notés plus de 7,5 sur TMDB… sauf l'intrus"))
    if len(bas) >= n - 1 and hauts:
        variantes.append((bas, hauts, f"{n - 1} films notés moins de 6,3 sur TMDB… sauf l'intrus"))
    if not variantes:
        return None
    groupe, autres, sujet = random.choice(variantes)
    groupe = distincts(x, groupe, n - 1)
    intrus = intrus_de(x, autres, groupe) if groupe else None
    if not intrus:
        return None
    return dict(groupe=groupe, intrus=intrus, sujet=sujet,
                indices=["Les critiques ne sont pas d'accord", "Regardez du côté des notes TMDB"],
                info=lambda f: f"★ {note_txt(f['note'])}")


def c_joueurs(x):
    n = x.n
    par_cle = {cle_txt(f): f for f in x.films}
    for p in random.sample(x.profils, len(x.profils)):
        aimes = [k for k, v in p["notes"].items() if v >= 8 and k.startswith("m:")]
        detestes = [k for k, v in p["notes"].items() if v <= 4 and k.startswith("m:")]
        variantes = []
        if len(aimes) >= n - 1 and detestes:
            variantes.append((aimes, detestes, f"{p['nom']} a adoré {n - 1} de ces films… pas l'intrus",
                              f"{p['nom']} a mis 8 ou plus à {n - 1} de ces films"))
        if len(detestes) >= n - 1 and aimes:
            variantes.append((detestes, aimes, f"{p['nom']} n'a pas aimé {n - 1} de ces films… sauf l'intrus",
                              f"{p['nom']} a mis 4 ou moins à {n - 1} de ces films"))
        if not variantes:
            continue
        groupe, autres, sujet, indice = random.choice(variantes)
        film = lambda k: par_cle.get(k) or film_de_profil(k, p["films"].get(k, {}))     # noqa: E731
        notes = p["notes"]
        groupe = distincts(x, [film(k) for k in groupe], n - 1)
        intrus = intrus_de(x, [film(k) for k in autres], groupe) if groupe else None
        if not intrus:
            continue
        return dict(groupe=groupe, intrus=intrus,
                    sujet=sujet, indices=[f"Demandez à {p['nom']}", indice],
                    info=lambda f: f"{p['nom']} : {notes.get(cle_txt(f), '?')}/10")
    return None


def _personne(x, job):
    """Même réalisateur (job « Director ») ou même compositeur (job « compositeur »)."""
    n, api = x.n, x.api
    ok = x.realisateurs_ok() if job == "Director" else None
    if ok is not None and not ok:
        return None
    seeds = (graines(x, lambda fi: any(r["id"] in ok for r in fi["realisateurs"]), 10) if ok
             else random.sample(x.films, min(6, len(x.films))))
    for seed in seeds:
        fi = fiche(api, seed)
        for p in (fi["realisateurs"] if job == "Director" else fi["compositeurs"])[:2]:
            if ok is not None and p["id"] not in ok:
                continue
            filmo = filmographie(api, p["id"], job)
            ids = {f["id"] for f in filmo}
            connus = [f for f in filmo if f["votes"] >= CONNU and f["id"] != seed["id"]][:16]
            if len(connus) < n - 2:
                continue
            autres_films = distincts(x, connus, n - 2, avec=[seed])
            if not autres_films:
                continue
            groupe = [seed] + autres_films
            intrus = intrus_de(x, [f for f in x.films if f["id"] not in ids], groupe)
            if not intrus:
                continue
            autre = fiche(api, intrus)
            autres = autre["realisateurs"] if job == "Director" else autre["compositeurs"]
            de = (lambda f: f"de {p['nom']}") if job == "Director" else (lambda f: f"musique de {p['nom']}")
            intrus_txt = ("de " if job == "Director" else "musique de ") + (autres[0]["nom"] if autres else "?")
            return dict(groupe=groupe, intrus=intrus,
                        sujet=(f"{n - 1} films de {p['nom']}" if job == "Director" else
                               f"{n - 1} musiques de {p['nom']}") + "… sauf l'intrus",
                        indices=["Derrière la caméra" if job == "Director" else "Tendez l'oreille",
                                 f"Initiales : {initiales(p['nom'])}"],
                        info=lambda f, i=intrus["id"]: intrus_txt if f["id"] == i else de(f))
    return None


def c_realisateur(x):
    return _personne(x, "Director")


def c_compositeur(x):
    return _personne(x, "compositeur")


def c_acteur(x):
    n, api, ok = x.n, x.api, x.acteurs_ok()
    if not ok:
        return None
    for seed in graines(x, lambda fi: any(a["id"] in ok for a in fi["acteurs"][:8]), 10):
        fi = fiche(api, seed)
        cands = [a for a in fi["acteurs"][:8] if a["id"] in ok]
        for a in random.sample(cands, min(3, len(cands))):
            filmo = filmographie(api, a["id"])
            ids = {f["id"] for f in filmo}
            connus = [f for f in filmo if f["votes"] >= CONNU and f["ordre"] <= 5 and f["id"] != seed["id"]][:18]
            if len(connus) < n - 2:
                continue
            autres_films = distincts(x, connus, n - 2, avec=[seed])
            if not autres_films:
                continue
            groupe = [seed] + autres_films
            intrus = intrus_de(x, [f for f in x.films if f["id"] not in ids], groupe)
            if not intrus:
                continue
            roles = {f["id"]: f.get("role") for f in filmo}
            roles[seed["id"]] = a["role"]
            return dict(groupe=groupe, intrus=intrus, sujet=f"{a['nom']} joue dans {n - 1} de ces films… pas dans l'intrus",
                        indices=["Un visage familier", f"Initiales : {initiales(a['nom'])}"],
                        info=lambda f, i=intrus["id"]: f"sans {a['nom']}" if f["id"] == i else
                        f"{a['nom']}" + (f" ({roles.get(f['id'])})" if roles.get(f["id"]) else ""))
    return None


def c_duo(x):
    n, api, ok = x.n, x.api, x.acteurs_ok()
    if not ok:
        return None
    for seed in graines(x, lambda fi: sum(a["id"] in ok for a in fi["acteurs"][:8]) >= 2, 10):
        acteurs = [a for a in fiche(api, seed)["acteurs"][:8] if a["id"] in ok][:4]
        paires = [(a, b) for i, a in enumerate(acteurs) for b in acteurs[i + 1:]]
        random.shuffle(paires)
        for a, b in paires[:3]:
            fa, fb = filmographie(api, a["id"]), filmographie(api, b["id"])
            ib = {f["id"] for f in fb}
            communs = [f for f in fa if f["id"] in ib and f["votes"] >= 100 and f["id"] != seed["id"]]
            if len(communs) < n - 2:
                continue
            sans_b = [f for f in fa if f["id"] not in ib and f["votes"] >= CONNU and f["ordre"] <= 5]
            if not sans_b:
                continue
            autres_films = distincts(x, communs, n - 2, avec=[seed])
            intrus = intrus_de(x, sans_b, [seed] + autres_films) if autres_films else None
            if not intrus:
                continue
            groupe = [seed] + autres_films
            duo = f"{a['nom']} et {b['nom']}"
            return dict(groupe=groupe, intrus=intrus, sujet=f"{duo} ensemble… sauf dans l'intrus",
                        indices=["Ils vont bien ensemble", f"Initiales : {initiales(a['nom'])} & {initiales(b['nom'])}"],
                        info=lambda f, i=intrus["id"]: f"{a['nom']} sans {b['nom']}" if f["id"] == i else duo)
    return None


def c_casting(x):
    """Acteurs d'un même film, sauf un (l'intrus n'y a pas joué)."""
    n, api, ok = x.n, x.api, x.acteurs_ok()
    if not ok:
        return None
    for seed in graines(x, lambda fi: sum(a["id"] in ok for a in fi["acteurs"] if a["ordre"] <= 15) >= n - 1, 10):
        fi = fiche(api, seed)
        cast = [a for a in fi["acteurs"] if a["photo"] and a["ordre"] <= 15 and a["id"] in ok][:7]
        if len(cast) < n - 1:
            continue
        groupe = random.sample(cast, n - 1)
        exclus = {a["id"] for a in fi["acteurs"]}
        sexes = Counter(a["sexe"] for a in groupe)
        for autre in random.sample(x.films, min(10, len(x.films))):
            if autre["id"] == seed["id"]:
                continue
            cands = [a for a in fiche(api, autre)["acteurs"][:8] if a["photo"] and a["id"] not in exclus and a["id"] in ok]
            if not cands:
                continue
            memes = [a for a in cands if a["sexe"] == sexes.most_common(1)[0][0]] or cands
            intrus = dict(random.choice(memes), film=autre["title"])
            roles = {a["id"]: a["role"] for a in fi["acteurs"]}
            return dict(personnes=True, groupe=groupe, intrus=intrus, sujet=f"Le casting de {seed['title']}",
                        indices=["Ils ont tourné ensemble", f"Le film est sorti en {fi['annee']}" if fi["annee"] else
                                 f"Le film : {len(seed['title'].split())} mot(s)"],
                        info=lambda a, i=intrus["id"]: f"vu dans {intrus['film']}" if a["id"] == i else
                        (roles.get(a["id"]) or "dans le film"), films=[cle_film(seed)])
    return None


def _metier(x, cle_liste, job, libelles):
    """Même scénariste ou même directeur de la photo (comme le réalisateur)."""
    n, api = x.n, x.api
    for seed in random.sample(x.films, min(6, len(x.films))):
        fi = fiche(api, seed)
        for p in fi.get(cle_liste, [])[:2]:
            filmo = filmographie(api, p["id"], job)
            ids = {f["id"] for f in filmo}
            connus = [f for f in filmo if f["votes"] >= CONNU and f["id"] != seed["id"]][:16]
            if len(connus) < n - 2:
                continue
            autres_films = distincts(x, connus, n - 2, avec=[seed])
            if not autres_films:
                continue
            groupe = [seed] + autres_films
            intrus = intrus_de(x, [f for f in x.films if f["id"] not in ids], groupe)
            if not intrus:
                continue
            autres = fiche(api, intrus).get(cle_liste) or []
            sujet, indice, de = libelles
            nom_intrus = autres[0]["nom"] if autres else "?"
            return dict(groupe=groupe, intrus=intrus, sujet=sujet.format(n=n - 1, nom=p["nom"]),
                        indices=[indice, f"Initiales : {initiales(p['nom'])}"],
                        info=lambda f, i=intrus["id"], p=p: de.format(nom=nom_intrus) if f["id"] == i
                        else de.format(nom=p["nom"]))
    return None


def c_scenariste(x):
    return _metier(x, "scenaristes", "scenariste",
                   ("{n} films écrits par {nom}… sauf l'intrus", "Tout part du scénario", "écrit par {nom}"))


def c_photo(x):
    return _metier(x, "chefs_op", "Director of Photography",
                   ("{n} films éclairés par {nom}… sauf l'intrus", "Question de lumière", "image de {nom}"))


def c_annee(x):
    n, films = x.n, [f for f in x.films if (f.get("release_date") or "")[:4].isdigit()]
    an = lambda f: int(f["release_date"][:4])                    # noqa: E731
    compte = Counter(map(an, films))
    choix = [a for a, c in compte.items() if c >= n - 1]
    random.shuffle(choix)
    for a in choix:
        voisins = [f for f in films if 1 <= abs(an(f) - a) <= 3]
        groupe = distincts(x, [f for f in films if an(f) == a], n - 1) if voisins else None
        intrus = intrus_de(x, voisins, groupe) if groupe else None
        if intrus:
            return dict(groupe=groupe, intrus=intrus, sujet=f"{n - 1} films sortis en {a}… sauf l'intrus",
                        indices=["Une question de calendrier", f"Une année des années {a // 10 * 10}"],
                        info=lambda f: f["release_date"][:4])
    return None


def c_pays(x):
    n = x.n
    fiches = x.fiches()
    par_pays = {}
    for f, fi in fiches:
        for p in set(fi.get("pays_codes") or []):
            par_pays.setdefault(p, []).append(f)
    choix = [p for p, l in par_pays.items() if p != "US" and len(l) >= n - 1]
    random.shuffle(choix)
    for p in choix:
        avec = {cle_film(f) for f in par_pays[p]}
        sans = [f for f, fi in fiches if cle_film(f) not in avec]
        groupe = distincts(x, par_pays[p], n - 1) if sans else None
        intrus = intrus_de(x, sans, groupe) if groupe else None
        if intrus:
            pays = {cle_film(f): fi.get("pays_codes") or [] for f, fi in fiches}
            nom = PAYS_NOMS.get(p, p)
            return dict(groupe=groupe, intrus=intrus, sujet=f"{n - 1} films produits en {nom}… sauf l'intrus",
                        indices=["Prenez l'avion", f"Le pays commence par « {nom[0]} »"],
                        info=lambda f: ", ".join(PAYS_NOMS.get(c, c) for c in pays.get(cle_film(f), [])[:2]))
    return None


def c_duree(x):
    n = x.n
    fiches = [(f, fi) for f, fi in x.fiches() if fi.get("duree")]
    longs = [f for f, fi in fiches if fi["duree"] >= 150]
    courts = [f for f, fi in fiches if fi["duree"] <= 95]
    moyens = [f for f, fi in fiches if 110 <= fi["duree"] <= 130]
    duree = {cle_film(f): fi["duree"] for f, fi in fiches}
    variantes = []
    if len(longs) >= n - 1 and (moyens or courts):
        variantes.append((longs, moyens or courts, f"{n - 1} films de plus de 2 h 30… sauf l'intrus"))
    if len(courts) >= n - 1 and (moyens or longs):
        variantes.append((courts, moyens or longs, f"{n - 1} films de moins d'1 h 35… sauf l'intrus"))
    random.shuffle(variantes)
    for groupe, autres, sujet in variantes:
        groupe = distincts(x, groupe, n - 1)
        intrus = intrus_de(x, autres, groupe) if groupe else None
        if intrus:
            return dict(groupe=groupe, intrus=intrus, sujet=sujet,
                        indices=["Prévoyez le pop-corn", "Regardez l'horloge"],
                        info=lambda f: f"{duree.get(cle_film(f), 0) // 60} h {duree.get(cle_film(f), 0) % 60:02d}")
    return None


def c_theme(x):
    n, api = x.n, x.api
    for fr, en in random.sample(THEMES, len(THEMES))[:5]:
        try:
            kid = identifiant(api, "keyword", en)
            connus = [f for f in decouvrir(api, 2, with_keywords=kid) if f["votes"] >= CONNU] if kid else []
        except Exception:  # noqa: BLE001
            continue
        if len(connus) < n - 1:
            continue
        groupe = distincts(x, connus, n - 1)
        if not groupe:
            continue
        ids = {f["id"] for f in connus}
        for _ in range(3):
            intrus = intrus_de(x, [f for f in x.films if f["id"] not in ids], groupe)
            if intrus and kid not in (fiche(api, intrus).get("mots_cles_ids") or []):
                return dict(groupe=groupe, intrus=intrus, sujet=f"{n - 1} films avec {fr}… sauf l'intrus",
                            indices=["Un même ingrédient dans l'histoire", f"Le thème : {len(fr.split())} mot(s)"],
                            info=lambda f, i=intrus["id"], fr=fr: f"sans {fr}" if f["id"] == i else f"avec {fr}")
            if intrus:
                ids.add(intrus["id"])
    return None


CATEGORIES = {"realisateur": c_realisateur, "compositeur": c_compositeur, "acteur": c_acteur, "duo": c_duo,
              "casting": c_casting, "genre": c_genre, "decennie": c_decennie, "annee": c_annee, "langue": c_langue,
              "pays": c_pays, "scenariste": c_scenariste, "photo": c_photo, "theme": c_theme,
              "duree": c_duree, "note": c_note, "joueurs": c_joueurs}
assert set(CATEGORIES) == set(INTRUS)


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_leland"])
    x = Ctx(api, cfg, pool)
    if len(x.films) < x.n:
        raise RuntimeError("L'intrus : pas assez de films avec affiche dans les listes.")
    actives = [k for k in INTRUS if cfg.get("leland_" + k, True)] or list(INTRUS)
    if not x.profils:
        actives = [k for k in actives if k != "joueurs"] or ["genre"]
    for k in random.sample(actives, len(actives)) * 2:
        try:
            r = CATEGORIES[k](x)
        except Exception:  # noqa: BLE001
            r = None
        if r and r["intrus"]:
            r["nature"] = NATURES.get(k, "")
            break
    else:
        raise RuntimeError("L'intrus : aucun intrus trouvé avec les catégories activées.")
    elements = r["groupe"] + [r["intrus"]]
    ordre = list(range(len(elements)))
    random.shuffle(ordre)
    elements = [elements[i] for i in ordre]
    bonne = ordre.index(len(ordre) - 1)
    if r.get("personnes"):
        photos = api.images([a["photo"] for a in elements], "w185")
        images = [en_jpeg(ImageOps.fit(p, (200, 300)), 300) for p in photos]
        items = [{"img": i, "txt": a["nom"]} for i, a in enumerate(elements)]
        nom_intrus = elements[bonne]["nom"]
    else:
        images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450) for f in elements]
        items = [{"img": i, "txt": f["title"]} for i, f in enumerate(elements)]       # sans l'année
        nom_intrus = elements[bonne]["title"]
    etat = {"items": items, "question": "Qui est l'intrus ?", "indices": [], "personnes": bool(r.get("personnes"))}
    # 5 s : la nature de la différence (« Décennie différente ») ; à mi-temps : l'indice le plus précis
    prevus = [(min(NATURE_DELAI, duree * 0.4), r.get("nature") or r["indices"][0]), (duree * 0.55, r["indices"][-1])]
    evts = [(t, lambda i=i: etat["indices"].append(i)) for t, i in prevus]
    etapes = chronologie(evts, lambda: {**etat, "indices": list(etat["indices"])})
    return dict(jeu="leland", vue="choix", duree=duree, reponse="choix", etapes=etapes, revelation=None,
                images=images, cles=[], bonne="", bonne_i=bonne, infos=[r["info"](e) for e in elements],
                solution=f"L'intrus : {nom_intrus}", detail=r["sujet"],
                films=r.get("films") or [cle_film(f) for f in elements if "id" in f and "tv" in f])
