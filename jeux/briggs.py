"""Major Briggs' Deep Space Monitor Printouts (Mots-clés) : le relevé s'imprime ligne à ligne, chaque ligne est un
élément de l'histoire, du plus vague au plus précis.

Sources :
  - les mots-clés TMDB (en anglais) et le résumé, traduits par le lexique (briggs_lexique.py) : objets, lieux,
    animaux, rôles, événements, thèmes ;
  - Wikidata et Wikipédia (briggs_web.py) : les références directes au film, bien plus précises qu'un thème :
    les personnages (« Danny »), les lieux de l'action, les lieux inventés et noms propres de l'intrigue
    (« Overlook »), les détails chiffrés (« chambre 237 »), l'époque, le sujet.
Ordre d'impression : thèmes, puis événements, puis objets / lieux / animaux, puis lieux réels, puis noms propres et
détails, et enfin un personnage. Pour Shining : isolement, hiver, hache, labyrinthe, machine à écrire, Colorado,
Overlook, chambre 237, Danny. Jamais un élément qui contient un mot du titre (ou de la saga).
Indices (réglables) : année et genre, puis le titre à trous.
"""
import random
import re

from texte import normaliser
from tmdb import details_film, fiche, mots_cles
from visuels import en_jpeg
from . import briggs_web
from .briggs_lexique import LEXIQUE, LIEUX, SUFFIXES_LIEUX
from .commun import affiche, chronologie, manche_titre, reponse_affichee, tirer, trous

# Importance des catégories : les choses concrètes de l'histoire avant les thèmes.
POIDS = {"objet": 5.0, "lieu": 4.8, "animal": 4.6, "reel": 5.2, "personnage": 4.2, "nature": 3.0,
         "evenement": 3.6, "theme": 1.4}
BANAL = 4.0                     # retiré au score d'un élément trop courant (famille, amour, ville…)
MINIMUM = 4                     # éléments au moins pour jouer un film
MOTS_VIDES = {"le", "la", "les", "un", "une", "des", "du", "de", "the", "of", "and", "et", "a", "an", "in", "on", "to",
              "l", "d", "s", "part", "partie", "chapter", "chapitre", "episode", "vol", "volume", "ii", "iii", "iv",
              "aux", "au", "en", "sur", "dans", "pour", "par", "avec", "qui", "que"}
# mots-clés qui parlent du film plutôt que de son histoire
GENERIQUES = re.compile(r"(stinger|credits|based on|sequel|prequel|remake|reboot|woman director|3d|imax|anime|"
                        r"live action|cgi|black and white|independent film|cult film|biography|spin off|duplicate|"
                        r"lgbt|anthology|non linear|flashback|voice over|narration|title spoken|dark comedy|"
                        r"satire|parody|musical|tragedy|thriller|mockumentary|found footage|^\w$|^\d+s$)", re.I)
# expressions françaises à ignorer dans le résumé (« en train de » n'est pas un train)
EXPRESSIONS = ["en train de", "en train d", "tout a coup", "a la mode", "mode de vie", "en general", "le monde entier"]


# ---------------------------------------------------------------- lexique
def _lire_lexique():
    entrees, cat = [], "objet"
    for ligne in LEXIQUE.splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        if ligne.startswith("[") and ligne.endswith("]"):
            cat = ligne[1:-1]
            continue
        if "=" not in ligne:
            continue
        libelle, declencheurs = (x.strip() for x in ligne.split("=", 1))
        en, _, fr = declencheurs.partition("/")
        banal = libelle.startswith("~")
        libelle = libelle.lstrip("~").strip()
        entrees.append({"l": libelle, "cat": cat, "banal": banal,
                        "en": [x.strip() for x in en.split(",") if x.strip()],
                        "fr": [x.strip() for x in fr.split(",") if x.strip()]})
    return entrees


class Index:
    """Recherche rapide des déclencheurs (expressions, mots exacts, débuts de mots) d'une langue."""

    def __init__(self, entrees, langue):
        self.phrases, self.mots, self.prefixes = {}, {}, []
        for i, e in enumerate(entrees):
            for d in e[langue]:
                prefixe = d.endswith("*")
                d = normaliser(d.rstrip("*"))
                if not d:
                    continue
                if " " in d:
                    self.phrases.setdefault(d, i)
                elif prefixe and len(d) >= 3:
                    self.prefixes.append((d, i))
                else:
                    self.mots.setdefault(d, i)
        self.prefixes.sort(key=lambda p: -len(p[0]))
        self.phrases_triees = sorted(self.phrases, key=len, reverse=True)

    def mot(self, m):
        if m in self.mots:
            return self.mots[m]
        singuliers = [m[:-1] if m[-1:] in "sx" else None, m[:-2] if m.endswith("es") else None,
                      m[:-3] + "y" if m.endswith("ies") else None]
        for v in singuliers:
            if v and len(v) >= 4 and v in self.mots:
                return self.mots[v]
        for p, i in self.prefixes:
            if m.startswith(p):
                return i
        return None

    def chercher(self, texte, mots_seuls=True, ignorer=()):
        """Éléments trouvés dans un texte, dans l'ordre d'apparition (expressions d'abord)."""
        t = f" {normaliser(texte)} "
        for x in ignorer:
            t = t.replace(f" {x} ", " " + "_" * len(x) + " ")
        trouves = []
        for ph in self.phrases_triees:
            pos = t.find(f" {ph} ")
            while pos >= 0:
                trouves.append((pos, self.phrases[ph]))
                t = t[:pos] + " " + "_" * len(ph) + " " + t[pos + len(ph) + 2:]
                pos = t.find(f" {ph} ")
        if mots_seuls:
            pos = 0
            for m in t.split():
                pos = t.find(m, pos)
                i = None if "_" in m else self.mot(m)
                if i is not None:
                    trouves.append((pos, i))
                pos += len(m)
        return [i for _, i in sorted(trouves)]


ENTREES = _lire_lexique()
INDEX_EN, INDEX_FR = Index(ENTREES, "en"), Index(ENTREES, "fr")
LIEUX_N = {normaliser(k): v for k, v in LIEUX.items()}


def lieu_reel(mot_cle):
    """« paris, france » -> « Paris » ; « boulder, colorado » -> « Boulder » ; sinon None."""
    n = normaliser(mot_cle)
    if n in LIEUX_N:
        return LIEUX_N[n]
    if "," in mot_cle:
        ville, _, region = (x.strip().lower() for x in mot_cle.rpartition(","))
        if region in SUFFIXES_LIEUX and ville and not INDEX_EN.chercher(ville):
            return LIEUX_N.get(normaliser(ville)) or " ".join(w.capitalize() for w in ville.split())
    return None


def _francais(texte):
    t = f" {normaliser(texte)} "
    return sum(t.count(f" {m} ") for m in ("le", "la", "les", "et", "des", "est", "une")) >= \
        sum(t.count(f" {m} ") for m in ("the", "and", "of", "is", "his", "her", "with"))


# ---------------------------------------------------------------- références précises (web)
# Précision d'un élément : l'ordre d'impression (du plus vague au plus parlant) et les quotas.
PRECISION = {"theme": 1, "epoque": 2, "evenement": 2, "nature": 2, "sujet": 2, "personnage": 3, "animal": 3, "objet": 3,
             "lieu": 3, "reel": 4, "nom": 5, "detail": 5, "heros": 6}
QUOTAS = {1: 1, 2: 2, 3: 3, 4: 2, 5: 2, 6: 1}
ETIQUETTES = {"theme": "THÈME", "epoque": "ÉPOQUE", "evenement": "ÉVÉNEMENT", "nature": "NATURE", "sujet": "SUJET",
              "personnage": "RÔLE", "animal": "ANIMAL", "objet": "OBJET", "lieu": "LIEU", "reel": "LIEU", "nom": "NOM",
              "detail": "DÉTAIL", "heros": "PERSONNAGE"}
MAJ = "A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ"
MIN = "a-zàâäçéèêëîïôöùûüÿœæ"
NOM_PROPRE = re.compile(rf"(?<![\w])[{MAJ}][{MIN}'’\-]+(?:\s+(?:(?:de|du|des|la|le|of|the|von|van|di|da)\s+)?[{MAJ}][{MIN}'’\-]+){{0,3}}")
VIDES_MAJ = set("""il elle ils elles le la les un une des dans apres avant alors mais quand lorsque pendant tandis puis ce
cette ces cet son sa ses leur leurs en au aux a sur sous pour par avec sans chez entre vers depuis lui eux celui celle
toutefois cependant enfin ensuite plus tard tout tous toute toutes on nous vous je tu ou et donc or ni car si comme
he she they the a an in on after when while his her their as at meanwhile however later then there this that these
those it its one two but with from by to of for into once soon eventually back upon during before since until
monsieur madame mademoiselle mr mrs ms dr docteur professeur capitaine lieutenant sergent agent inspecteur
janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre lundi mardi mercredi jeudi
vendredi samedi dimanche january february march april may june july august september october november december
monday tuesday wednesday thursday friday saturday sunday noel christmas dieu god""".split())
DETAIL = re.compile(r"\b(chambre|appartement|cellule|bureau|vol|route|autoroute|zone|district|secteur|niveau|etage|"
                    r"quai|porte|matricule|numero|code|plateforme|bloc|room|apartment|cell|flight|highway|sector|level|"
                    r"floor|platform|gate|number|unit|ward|block|locker|hangar|base|area|station)\s+(?:n[o°]\s*)?(\d{1,5})\b")
TRAD_DETAIL = {"room": "chambre", "apartment": "appartement", "cell": "cellule", "flight": "vol", "highway": "route",
               "sector": "secteur", "level": "niveau", "floor": "étage", "platform": "quai", "gate": "porte",
               "number": "numéro", "unit": "unité", "ward": "pavillon", "block": "bloc", "locker": "casier",
               "area": "zone", "etage": "étage", "numero": "numéro"}


def _phrase_debut(texte, pos):
    avant = texte[:pos].rstrip()
    return not avant or avant[-1] in ".!?:;«\"“\n"


def references_web(api, film, interdits, acteurs):
    """Éléments précis tirés de Wikidata / Wikipédia : [(score, libellé, catégorie)]."""
    try:
        w = briggs_web.infos(api, film)
    except Exception:  # noqa: BLE001
        return []
    out = []

    def permis(lib):
        mots = {m for m in normaliser(lib).split() if len(m) >= 3 and m not in MOTS_VIDES}
        return bool(mots) and not (mots & interdits) and normaliser(lib) not in acteurs

    intrigue = re.sub(r"\([^)]*\)", " ", w.get("intrigue") or "")
    texte_n = f" {normaliser(intrigue)} "

    def compte(nom):
        n = normaliser(nom)
        return texte_n.count(f" {n} ") if n else 0

    # personnages (Wikidata) : on garde ceux qui comptent dans l'intrigue ; le prénom suffit s'il revient seul
    persos = []
    for p in w.get("personnages", []):
        prenom = p.split()[0] if len(p.split()) > 1 else p
        c = max(compte(p), compte(prenom))
        persos.append((c, p, prenom))
    persos.sort(key=lambda x: -x[0])
    for c, p, prenom in persos[:4]:
        lib = prenom if compte(prenom) > compte(p) and len(prenom) >= 3 else p
        if permis(lib) and (c or not intrigue):
            out.append((5.0 + min(3, c) * 0.6, lib, "heros"))
    deja = {normaliser(x) for _, x, _ in out} | {normaliser(p) for p in w.get("personnages", [])}
    deja |= {normaliser(p.split()[0]) for p in w.get("personnages", []) if p.split()}
    for lieu in w.get("lieux", [])[:3]:
        if permis(lieu):
            out.append((4.5, lieu, "reel"))
    for sujet in w.get("sujets", [])[:2]:
        if permis(sujet) and len(sujet) <= 28:
            out.append((3.0, sujet[:1].lower() + sujet[1:], "sujet"))
    for ep in w.get("epoque", [])[:1]:
        if permis(ep) and len(ep) <= 24:
            out.append((2.6, ep[:1].lower() + ep[1:], "epoque"))
    # noms propres de l'intrigue qui reviennent (lieux inventés, organisations, surnoms…)
    vus = {}
    for m in NOM_PROPRE.finditer(intrigue):
        nom = m.group(0).strip()
        mots = normaliser(nom).split()
        if not mots or mots[0] in VIDES_MAJ:
            if len(mots) > 1 and mots[0] in VIDES_MAJ:
                nom = " ".join(nom.split()[1:])
                mots = mots[1:]
            else:
                continue
        if not mots or all(x in VIDES_MAJ for x in mots):
            continue
        k = " ".join(mots)
        e = vus.setdefault(k, {"nom": nom, "n": 0, "milieu": 0})
        e["n"] += 1
        e["milieu"] += not _phrase_debut(intrigue, m.start())
    lieux_wd = {normaliser(x) for x in w.get("lieux", [])}
    for k, e in sorted(vus.items(), key=lambda kv: -kv[1]["n"]):
        if e["n"] < 2 or not e["milieu"] or k in deja or k in lieux_wd or not permis(e["nom"]):
            continue
        if any(k in d or d in k for d in deja if len(d) >= 4):
            continue
        out.append((3.2 + min(3, e["n"]) * 0.5, e["nom"], "nom"))
        deja.add(k)
        if sum(1 for _, _, c in out if c == "nom") >= 3:
            break
    # détails chiffrés : « chambre 237 », « vol 815 »
    for m in DETAIL.finditer(normaliser(intrigue)):
        mot, num = m.group(1), m.group(2)
        lib = f"{TRAD_DETAIL.get(mot, mot)} {num}"
        if lib not in {x for _, x, _ in out}:
            out.append((4.4, lib, "detail"))
    return out


# ---------------------------------------------------------------- éléments d'un film
def elements(api, film, d):
    """Éléments d'histoire du film, classés : [(score, libellé, catégorie)], du plus parlant au plus vague."""
    kws = mots_cles(api, film)
    titres = [t for t in dict.fromkeys([d.get("en"), film.get("original_title"), film["title"], *d.get("noms", [])])
              if t]
    if d.get("saga"):
        titres.append(d["saga"])
    interdits = {m for t in titres for m in normaliser(t).split() if len(m) >= 3 and m not in MOTS_VIDES}
    du_titre = {i for t in titres for i in INDEX_EN.chercher(t) + INDEX_FR.chercher(t)}

    def revele_titre(e):
        mots = set(normaliser(e["l"]).split())
        for d_ in e["en"] + e["fr"]:
            for m in normaliser(d_.rstrip("*")).split():
                if d_.endswith("*") and any(x.startswith(m) for x in interdits if len(m) >= 4):
                    return True
                mots.add(m)
        return bool({m for m in mots if len(m) >= 3 and m not in MOTS_VIDES} & interdits)

    vus = {}                                          # libellé -> {cat, banal, kw, syn, web}

    def noter(libelle, cat, banal, source):
        x = vus.setdefault(libelle, {"cat": cat, "banal": banal, "kw": False, "syn": False, "web": False})
        x[source] = True

    for k in kws:
        if GENERIQUES.search(k):
            continue
        n = normaliser(k)
        if n in INDEX_EN.phrases or n in INDEX_EN.mots:
            trouves = [INDEX_EN.phrases.get(n, INDEX_EN.mots.get(n))]
        else:
            lieu = lieu_reel(k)
            if lieu:
                if not set(normaliser(lieu).split()) & interdits:
                    noter(lieu, "reel", False, "kw")
                continue
            trouves = INDEX_EN.chercher(k, mots_seuls=len(n.split()) <= 3)
        for i in trouves:
            e = ENTREES[i]
            if i not in du_titre and not revele_titre(e):
                noter(e["l"], e["cat"], e["banal"], "kw")
    resume = d.get("resume") or ""
    if resume:
        index = INDEX_FR if _francais(resume) else INDEX_EN
        for i in index.chercher(resume, ignorer=[normaliser(x) for x in EXPRESSIONS]):
            e = ENTREES[i]
            if i not in du_titre and not revele_titre(e):
                noter(e["l"], e["cat"], e["banal"], "syn")
    # l'intrigue complète (Wikipédia) confirme les éléments du lexique : ceux qu'elle cite sont centraux
    try:
        acteurs = {normaliser(a["nom"]) for a in fiche(api, film)["acteurs"][:30]}
    except Exception:  # noqa: BLE001
        acteurs = set()
    web = references_web(api, film, interdits, acteurs)
    try:
        w = briggs_web.infos(api, film)
    except Exception:  # noqa: BLE001
        w = {}
    if w.get("intrigue"):
        index = INDEX_FR if w.get("langue") == "fr" else INDEX_EN
        for i in index.chercher(w["intrigue"], ignorer=[normaliser(x) for x in EXPRESSIONS]):
            e = ENTREES[i]
            if i not in du_titre and not revele_titre(e):
                noter(e["l"], e["cat"], e["banal"], "web")
    out = []
    for libelle, x in vus.items():
        score = POIDS.get(x["cat"], 2.0)
        sources = x["kw"] + x["syn"] + x["web"]
        if sources >= 2:
            score += 1.5                              # cité par plusieurs sources : central dans l'histoire
        elif not x["kw"]:
            score -= 1.0                              # seulement dans un texte : moins sûr
        if x["banal"]:
            score -= BANAL
        out.append((score + random.random() * 0.3, libelle[:1].upper() + libelle[1:], x["cat"]))
    connus = {normaliser(l) for _, l, _ in out}
    for score, lib, cat in web:
        if normaliser(lib) not in connus:
            connus.add(normaliser(lib))
            out.append((score + random.random() * 0.3, lib[:1].upper() + lib[1:], cat))
    out.sort(reverse=True)
    # toujours le plus précis possible : les éléments banals (famille, amour, ville…) et les thèmes vagues ne
    # servent que s'il n'y a pas assez d'éléments précis
    precis = [e for e in out if e[0] >= POIDS["theme"] + 1.0]
    if len(precis) >= MINIMUM + 2:
        out = precis
    return out


def jouable(elts):
    return len(elts) >= MINIMUM and sum(1 for _, _, c in elts if c != "theme") >= 2


def selection(elts, nmax):
    """Les nmax éléments à imprimer : les plus centraux, avec des quotas par précision (pas que des thèmes, pas
    plus d'un personnage), puis rangés du plus vague au plus précis."""
    pris, compte = [], {}
    e = next((e for e in elts if PRECISION.get(e[2], 3) == 2), None)   # un seul élément un peu vague pour démarrer
    if e and len(pris) < nmax - 3:
        pris.append(e)
        compte[2] = 1
    for e in elts:
        if e in pris:
            continue
        p = PRECISION.get(e[2], 3)
        if compte.get(p, 0) < QUOTAS.get(p, 2):
            pris.append(e)
            compte[p] = compte.get(p, 0) + 1
        if len(pris) == nmax:
            break
    for e in elts:                                    # pas assez : on complète sans quotas (jamais 2 personnages)
        if len(pris) >= nmax:
            break
        if e not in pris and not (e[2] == "heros" and compte.get(6)):
            pris.append(e)
    # du plus vague au plus précis ; à précision égale, le moins central d'abord
    return sorted(pris, key=lambda e: (PRECISION.get(e[2], 3), e[0]))


def construire(api, cfg, pool, deja):
    duree = float(cfg["dur_briggs"])
    nmax = int(cfg.get("briggs_max", 8))
    for _ in range(14):
        film = tirer(pool, deja)
        d = details_film(api, film)
        elts = elements(api, film, d)
        if jouable(elts):
            break
    else:
        raise RuntimeError("Mots-clés : pas assez d'éléments d'histoire pour les films des listes "
                           "(essayez d'autres listes).")
    choisis = selection(elts, nmax)
    fin = 0.62 if cfg.get("briggs_indices", True) else 0.8
    lignes = [(fin * k / max(1, len(choisis) - 1), lib, ETIQUETTES.get(cat, "")) for k, (_, lib, cat) in
              enumerate(choisis)]
    etat = {"mots": [], "cats": [], "total": len(choisis), "indices": [], "trous": "",
            "station": f"{random.randint(1, 9)}-{random.randint(100, 999)}"}
    evts = [(duree * t, lambda l=l, c=c: (etat["mots"].append(l), etat["cats"].append(c))) for t, l, c in lignes]
    if cfg.get("briggs_indices", True):
        depart = " · ".join(x for x in (d["annee"], ", ".join(d["genres"][:2])) if x)
        if depart:
            evts.append((duree * 0.72, lambda: etat["indices"].append(depart)))
        evts.append((duree * 0.85, lambda: etat.update(trous=trous(reponse_affichee(cfg, film, d), 0))))
    etapes = chronologie(evts, lambda: {**etat, "mots": list(etat["mots"]), "cats": list(etat["cats"]),
                                        "indices": list(etat["indices"])})
    return manche_titre("briggs", "briggs", duree, film, d, etapes, [], en_jpeg(affiche(api, film, "w500")), cfg)
