"""Phonétique française simplifiée, pour les rébus (Jerry's Trip) : un texte -> une suite de sons, un caractère par son.

Voyelles : a  e (é, è, ai…)  2 (eu, e muet prononcé)  i  o (o, au, eau)  u (ou)  y (u)  A (an, en)  O (on)  I (in, un)
Consonnes : p b t d k g f v s z S (ch) Z (j, ge) m n N (gn) l r w j (y de « yeux », ill)
Ce n'est pas un vrai dictionnaire de prononciation : des règles d'orthographe française, assez bonnes pour
rapprocher des mots qui se prononcent pareil (« roi » = « rwa », « lait » = « le », « dé » = « de »).
"""
import re
import unicodedata

VOYELLES = set("ae2ioyuAOI")
_MUETTES_FIN = "stdxzpg"
_ER_OUVERT = {"mer", "fer", "ver", "hiver", "enfer", "cher", "amer", "hier", "fier", "super", "laser", "poster", "hamster",
              "cancer", "master", "monster", "joker", "power", "never", "ever", "winter", "killer", "hunter", "water",
              "river", "father", "mother", "brother", "sister", "after", "under", "over", "summer", "dinner", "tiger",
              "ranger", "danger", "soldier", "lover", "silver", "spider", "joker", "terminator", "blader", "runner",
              "rider", "driver", "player", "matter", "letter", "her", "der", "per", "ter", "cher", "ether"}
_SPECIAUX = {"et": "e", "est": "e", "les": "le", "des": "de", "mes": "me", "tes": "te", "ses": "se", "ces": "se",
             "un": "I", "une": "yn", "the": "z2", "of": "of", "and": "And", "a": "a", "à": "a", "y": "i", "eu": "y",
             "monsieur": "m2sj2", "femme": "fam", "femmes": "fam", "oignon": "oNO", "second": "s2gO", "seconde": "s2gOd",
             "sept": "set", "huit": "wit", "dix": "dis", "six": "sis", "os": "os", "fils": "fis", "temps": "tA",
             "corps": "kor", "oeil": "2j", "oeufs": "2", "œufs": "2", "boeufs": "b2", "bœufs": "b2", "août": "ut", "yeux": "j2", "pied": "pje", "pieds": "pje", "clef": "kle", "nez": "ne", "chez": "Se", "assez": "ase",
             "doigt": "dwa", "doigts": "dwa", "cinq": "sIk", "tronc": "trO", "clown": "klun", "jean": "dZin",
             "yoyo": "jojo", "cerf": "ser", "fusil": "fyzi", "gens": "ZA", "paon": "pA", "b": "be", "m": "em", "p": "pe",
             "o": "o", "i": "i", "huit": "yit", "coq": "kok", "porc": "por", "banc": "bA", "blanc": "blA", "franc": "frA",
             "estomac": "estoma", "tabac": "taba", "croc": "kro", "broc": "bro", "escroc": "eskro", "joker": "Zok2r"}


_S_PRONONCE = {"os", "bus", "ours", "fils", "as", "sens", "tennis", "bis", "lis", "vis", "maïs", "mais", "hélas", "atlas",
               "cactus", "virus", "bonus", "campus", "papyrus", "iris", "jadis", "oasis", "ananas", "tournevis",
               "rhinoceros", "rhinocéros", "albatros", "cosmos", "pathos", "chaos", "tétanos", "lotus", "blocus", "humus", "fœtus"}
_X_MUETS = {"prix", "paix", "choix", "voix", "croix", "noix", "deux", "yeux", "faix", "perdrix", "flux"}


def _sans_accents_sauf_e(mot):
    out = []
    for c in mot:
        if c in "éèêë":
            out.append(c)
            continue
        d = unicodedata.normalize("NFD", c)
        out.append("".join(x for x in d if unicodedata.category(x) != "Mn"))
    return "".join(out)


def mot(m):
    """Un mot (minuscules) -> ses sons."""
    m = m.lower().strip("'’-")
    if not m:
        return ""
    if m in _SPECIAUX:
        return _SPECIAUX[m]
    m = m.replace("ï", "\x01").replace("ü", "\x02")
    m = _sans_accents_sauf_e(m).replace("œ", "oe").replace("æ", "e")
    if not m:
        return ""
    x_muet = m.endswith(("eux", "aux", "oux")) or m in _X_MUETS
    if m.endswith("ille") and m not in ("ville", "mille", "tranquille", "village"):
        m = m[:-4] + "\x03"                              # fille, feuille : « ij »
    elif "ill" in m[1:] and m[:m.index("ill", 1)][-1:] in "aeiou":
        m = m.replace("ill", "\x03")
    # terminaisons muettes
    if m in _ER_OUVERT or (m.endswith("er") and len(m) <= 3):
        m = m[:-2] + "èr"
    elif m.endswith("er") and len(m) > 3:
        m = m[:-2] + "é"
    elif m.endswith("ez"):
        m = m[:-2] + "é"
    elif m.endswith("et") and len(m) > 2:
        m = m[:-2] + "è"
    e_final = False
    if len(m) > 3 and m.endswith("es") and m[-3] not in "é":
        m, e_final = m[:-2] + "\x04", True
    elif len(m) > 2 and m.endswith("e"):
        m, e_final = m[:-1] + "\x04", True               # e muet final (« belle » -> bel, « amie » -> ami)
    if not e_final:
        if len(m) > 3 and m[-1] == "s" and m not in _S_PRONONCE and m[-2] != "s":
            m = m[:-1]                                    # le pluriel : dents, chats
            if m.endswith("e") and len(m) > 2:
                m, e_final = m[:-1] + "\x04", True
    if not e_final:
        while len(m) > 2 and m[-1] in _MUETTES_FIN and m[-2] not in _MUETTES_FIN:
            if m in _S_PRONONCE:
                break
            if m[-1] == "x" and not x_muet:
                break
            m = m[:-1]
        if len(m) > 3 and m[-2:] in ("nt", "nd", "mp") and m[-3] in "aeiouy":
            m = m[:-1]                                    # dents, grands, temps : la nasale seule
    m = re.sub(r"e([bcdfghjklmnpqrstvz])\1", r"è\1", m)       # e devant une consonne doublée : è (belle, ennemi)
    m = m.replace("ss", "\x06")                           # « ss » reste [s] entre deux voyelles (tasse, poisson)
    m = re.sub(r"(.)\1", r"\1", m)                         # lettres doublées
    for fin, son in (("euil", "2\x05"), ("ouil", "u\x05"), ("ail", "a\x05"), ("eil", "e\x05"), ("oeil", "2\x05")):
        if m.endswith(fin):
            m = m[:-len(fin)] + son
    regles = [
        ("eaux", "o"), ("eau", "o"), ("au", "o"),
        ("oi", "wa"), ("oy", "waj"), ("ou", "u"), ("où", "u"), ("oû", "u"), ("oeu", "2"), ("oe", "2"), ("eu", "2"),
        ("ai", "e"), ("ei", "e"), ("ay", "ej"), ("ey", "e"), ("tion", "sjO"), ("ph", "f"), ("th", "t"), ("gn", "N"),
        ("ch", "S"), ("sh", "S"), ("qu", "k"), ("ck", "k"), ("gu", "g"), ("ill", "ij"), ("ee", "i"), ("oo", "u"),
    ]
    out, i = [], 0
    while i < len(m):
        c = m[i]
        reste = m[i:]
        suivant = m[i + 1] if i + 1 < len(m) else ""
        apres = m[i + 2] if i + 2 < len(m) else ""
        fait = False
        for g, s in (("aim", "I"), ("ain", "I"), ("ein", "I"), ("oin", "wI"), ("ien", "jI")):
            if reste.startswith(g) and (len(reste) == len(g) or reste[len(g)] not in "aeiouyéèêmn\x01\x04"):
                out.append(s)
                i += len(g)
                fait = True
                break
        if fait:
            continue
        for g, s in regles:
            if reste.startswith(g):
                out.append(s)
                i += len(g)
                fait = True
                break
        if fait:
            continue
        # voyelles nasales : voyelle + n/m, puis consonne ou fin de mot
        if c in "aeiouy" and suivant and suivant in "nm" and (not apres or apres not in "aeiouyéèênm\x01\x03\x04"):
            out.append({"a": "A", "e": "A", "i": "I", "y": "I", "o": "O", "u": "I"}[c])
            i += 2
            continue
        if c == "\x04":
            pass
        elif c == "\x06":
            out.append("s")
        elif c == "\x05":
            out.append("j")
        elif c == "\x01":
            out.append("i")
        elif c == "\x02":
            out.append("y")
        elif c == "\x03":
            out.append("ij" if out and out[-1][-1:] not in VOYELLES else "j")
        elif c in "éè":
            out.append("e")
        elif c in "êë":
            out.append("e")
        elif c == "e":
            # e devant deux consonnes ou une consonne finale : è ; sinon e muet (eu)
            nb = 0
            while i + 1 + nb < len(m) and m[i + 1 + nb] not in "aeiouyéèêë\x04":
                nb += 1
            out.append("e" if nb >= 2 or (nb == 1 and i + 2 == len(m)) else "2")
        elif c == "y":
            out.append("j" if suivant and suivant in "aeiouéè" else "i")
        elif c == "u":
            out.append("y")
        elif c == "i" and suivant and suivant in "aeouéèê" and out and out[-1][-1:] not in VOYELLES and i > 0 \
                and not (suivant == "e" and (i + 2 == len(m) or m[i + 2] in "\x04")):
            out.append("j")                               # pion, mission, piano : le i devient « y »
        elif c in "aio":
            out.append(c)
        elif c == "c":
            out.append("s" if suivant and suivant in "eiyéèê\x04" else "k")
        elif c == "ç":
            out.append("s")
        elif c == "g":
            out.append("Z" if suivant and suivant in "eiyéèê\x04" else "g")
        elif c == "j":
            out.append("Z")
        elif c == "s":
            entre = out and out[-1][-1] in "ae2ioyu" and suivant and suivant in "aeiouyéèê\x04"
            out.append("z" if entre else "s")
        elif c == "x":
            out.append("ks")
        elif c == "h":
            pass
        elif c == "w":
            out.append("w")
        elif c == "q":
            out.append("k")
        elif c in "bdfklmnprtvz":
            out.append(c)
        i += 1
    s = "".join(out)
    s = re.sub(r"(.)\1", r"\1", s)
    return s


def texte(t):
    """Un titre -> [(mot écrit, sons)] (les élisions l', d', qu' sont collées au mot suivant)."""
    t = t.replace("’", "'")
    mots = re.findall(r"[^\W\d_]+'?|\d+", t)
    out, colle = [], ""
    for m in mots:
        if m.endswith("'"):
            colle += mot(m[:-1].rstrip("e") or m[:-1])
            continue
        out.append((m, colle + (_nombre(m) if m.isdigit() else mot(m))))
        colle = ""
    return out


def _nombre(n):
    return {"1": "I", "2": "d2", "3": "trwa", "4": "katr", "5": "sIk", "6": "sis", "7": "set", "8": "wit", "9": "n2f",
            "10": "dis", "12": "duz", "13": "trez", "20": "vI", "100": "sA", "1000": "mil"}.get(n, n)


# --- Les titres qui se prononcent « à l'anglaise » : pas de rébus en phonétique française pour eux ---
_ANGLAIS = set("""the of and in on at to for with from by my your his her our their this that these those is are was be
of man men woman night day dark light star wars story club fight street king queen love life death dead world war
city house home girl boy kid kids game games time road way back down up out over under black white red blue green
gold silver iron big little last first new old good bad wild free fast furious mission impossible shining
lord rings ring knight dawn rise fall return revenge empire strikes hope force awakens jedi galaxy guardians
avengers spider batman superman wonder hunger games harry potter stone chamber prisoner goblet order prince blood
hallows deathly social network wolf wall wolf jack jones indiana raiders lost ark temple doom crusade crystal
skull pulp fiction kill bill django unchained inglourious basterds reservoir dogs hateful eight hollywood once upon
pirates caribbean pearl chest end tides tales toy finding nemo dory monsters inc incredibles cars up inside coco
soul luca turning frozen tangled moana brave shrek cast away forrest gump green mile saving private ryan schindler
list jurassic park world jaws catch me if you can terminal ready player one minority report war of worlds
avatar titanic aliens alien abyss true lies matrix reloaded revolutions john wick speed point break sweet
heat collateral miami vice drive only god forgives neon demon blade runner gladiator hannibal american beauty psycho
vertigo rear window north northwest birds rope fight club seven se7en zodiac gone girl social benjamin button
interstellar inception memento prestige dunkirk tenet oppenheimer dark knight batman begins insomnia following
joker taxi driver raging bull goodfellas casino departed irishman wolf street shutter island aviator gangs new
york silence killers flower moon""".split())
_FRANCAIS_OK = {"taxi", "ski", "kiwi", "titanic", "matrix", "avatar", "gladiator", "joker", "alien", "aliens", "psycho",
                "casino", "zodiac", "coco", "luca", "moana", "shrek", "nemo", "dory", "tenet", "camping", "parking",
                "interstellar", "inception", "memento", "insomnia", "vertigo", "brave", "abyss", "speed"}
_MOTIFS_ANGLAIS = re.compile(r"(th|ght|sh|oo|ee|ck|wh|ing$|^w|ay$|ey$|ow$|aw|ew|ea|y[^aeiouy]|^y[aeiou]|k)")


def francais(t):
    """Le titre se lit-il « à la française » ? (sinon : un titre anglais, que la phonétique française massacrerait)"""
    mots = [m.lower() for m in re.findall(r"[^\W\d_]+", t.replace("’", "'"))]
    if not mots:
        return False
    anglais = 0
    for m in mots:
        if m in _FRANCAIS_OK or len(m) <= 1:
            continue
        if m in _ANGLAIS or _MOTIFS_ANGLAIS.search(_sans_accents_sauf_e(m)):
            anglais += 1
    return anglais == 0
