"""Comparaison tolérante des réponses (accents, ponctuation, articles, fautes légères) et suggestions."""
import difflib
import re
import unicodedata

ARTICLES = {"le", "la", "les", "l", "un", "une", "the", "a", "an"}
SPECIAUX = {"ø": "o", "æ": "ae", "œ": "oe", "ß": "ss", "đ": "d", "ł": "l", "ð": "d", "þ": "th", "ı": "i"}
_TABLE = str.maketrans(SPECIAUX)


def normaliser(t):
    """Minuscules, sans accents ni ponctuation."""
    t = unicodedata.normalize("NFD", str(t).lower().translate(_TABLE))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def cle(texte):
    """Forme de comparaison : sans (année), sans « et / and », sans article initial."""
    k = normaliser(re.sub(r"[\(\[].*?[\)\]]", "", str(texte))) or normaliser(texte)
    mots = [m for m in k.split() if m not in ("and", "et")] or k.split()
    if len(mots) > 1 and mots[0] in ARTICLES:
        mots = mots[1:]
    return " ".join(mots)


def est_latin(t):
    """Vrai si le texte est tapable sur un clavier français (alphabet latin, accents compris)."""
    if not t or not cle(t):
        return False
    for c in t:
        if c.isalpha() and not c.isascii():
            if c.lower() in SPECIAUX:
                continue
            base = unicodedata.normalize("NFD", c)[0]
            if not (base.isascii() and base.isalpha()):
                return False
    return True


def correspond(reponse, cible):
    a = cle(reponse)
    if not a:
        return False
    if a == cible or a.replace(" ", "") == cible.replace(" ", ""):
        return True
    return (len(cible) >= 6 and re.findall(r"\d+", a) == re.findall(r"\d+", cible)
            and difflib.SequenceMatcher(None, a, cible).ratio() >= 0.88)


def proche(reponse, cible):
    a = cle(reponse)
    return bool(a) and difflib.SequenceMatcher(None, a, cible).ratio() >= 0.75


def variantes_titre(*titres):
    """Les titres fournis, avec et sans sous-titre, sans doublon."""
    out, vus = [], set()
    for t in titres:
        if not t:
            continue
        for v in (t, re.split(r"\s*[:\-–]\s+", t)[0]):
            k = cle(v)
            if k and (v is t or len(k) >= 3) and k not in vus:
                vus.add(k)
                out.append(v)
    return out


def suggerer(requete, entrees, n=6, valeur="nom"):
    """entrees : [(libellé, [(nom, cle), ...])]. Un résultat par entrée, le nom le plus proche.
    valeur="libelle" : la valeur proposée est le libellé de l'entrée (ex. « Dune (2021) »)."""
    q = cle(requete)
    if not q:
        return []
    res = []
    for lib_entree, noms in entrees:
        meilleur = None
        for nom, k in noms:
            s = difflib.SequenceMatcher(None, q, k).ratio()
            if q in k:
                s += 0.5
            elif any(m.startswith(q) for m in k.split()):
                s += 0.3
            if meilleur is None or s > meilleur[0]:
                meilleur = (s, nom, k)
        if meilleur:
            s, nom, k = meilleur
            if valeur == "libelle":
                autre = nom if cle(nom) not in cle(lib_entree) else None
                res.append((s, lib_entree, lib_entree if autre is None else f"{lib_entree}  ({autre})"))
                continue
            autre = next((x for x, kx in noms if kx != k), None)
            res.append((s, nom, nom if autre is None else f"{nom}  ({autre})"))
    res.sort(key=lambda r: -r[0])
    return [{"v": nom, "l": lib} for s, nom, lib in res[:n] if s > 0.35]
