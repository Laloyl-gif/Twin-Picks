"""One-Eyed Donna's (bingo) : une grille 2 × 2 ou 3 × 3 à remplir avec un film différent par case.

Deux façons de poser les conditions (réglages) :
  - « lignes » : une condition par ligne et une par colonne ; chaque case doit respecter les deux (comme une grille
    de mots croisés). La grille est TOUJOURS vérifiée à la construction : chaque case a au moins deux films connus
    qui respectent ses deux conditions (sinon une autre grille est tirée ; jamais de case impossible) ;
  - « cases » : chaque case a sa propre condition.
Grilles : une par joueur (par défaut) ou la même pour tous. Avec une grille par joueur, les conditions
« réalisateur » ne portent que sur des réalisateurs que le joueur connaît (profil › réalisateurs connus) ; en grille
commune, sur ceux que tous les joueurs présents connaissent.
Changer une condition : le joueur touche la condition (en-tête de ligne ou de colonne, ou la condition de sa case),
confirme, et elle est remplacée par une autre qui garde la grille faisable ; ses cases rapportent alors moins.
Points : par case remplie ; bonus grille complète ; bonus du 1er à finir (la moitié pour le 2e, le quart pour le 3e).
N'importe quel film de TMDB compte. Un film déjà donné lors d'une manche précédente ne compte plus (réglable).
"""
import random
from concurrent.futures import ThreadPoolExecutor

from tmdb import cle_film, libelle
from .contraintes import (LENTES, Ctx, actives, connus_communs, connus_de, entrees_films, generer, index,
                          resoudre, suggerer_films)

RESERVE = 14
MINI_CASE = 2                      # films connus au minimum par case (mode « lignes »)
CONNU = 300                        # votes TMDB minimum d'un film hors des listes pour compter comme « connu »
# conditions qui ne se croisent jamais (souvent impossibles ou absurdes : « années 1990 » × « sorti en 2004 »)
INCOMPATIBLES = {frozenset(p) for p in (("decennie", "periode"), ("decennie",), ("periode",), ("langue", "pays"),
                                        ("note",), ("titre",), ("duree",), ("boxoffice",), ("joueurs",))}


def compatibles(a, b):
    """Deux conditions peuvent-elles se croiser (ligne × colonne) ?"""
    return frozenset((a["type"], b["type"])) not in INCOMPATIBLES
RANGS = [1.0, 0.5, 0.25]           # bonus du 1er, du 2e, du 3e à finir (part de donna_premier)
GENERIQUES = 2                     # grilles pour les joueurs sans profil (une grille par joueur)


def _teste(c, f):
    try:
        return bool(c["test"](f, None))
    except Exception:  # noqa: BLE001
        return False


def _candidats(x, nb, types=None):
    cands = []
    for _ in range(nb * 2):
        c = generer(x, "donna_", exclues={c["txt"] for c in cands}, types=types)
        if c:
            cands.append(c)
        if len(cands) >= nb:
            break
    return cands


def _ensembles(x, cands):
    """Pour chaque condition : les films CONNUS qui la respectent : ceux des listes des joueurs, plus les films très
    connus (CONNU votes) parmi ceux qui servent à vérifier la condition. Une case n'est acceptée que si de vrais films
    connus y répondent."""
    connus = {cle_film(f): f for f in x.films}
    for c in cands:
        try:
            for f in c["valides"]():
                if f and not f.get("tv") and (f.get("votes") or 0) >= CONNU:
                    connus.setdefault(cle_film(f), f)
        except Exception:  # noqa: BLE001
            pass
    return [{k for k, f in connus.items() if _teste(c, f)} for c in cands]


def faisable(cases, interdits=frozenset()):
    """Vrai s'il existe un film DIFFÉRENT pour chaque case (couplage parfait cases -> films connus).
    cases : [ensemble de films possibles pour chaque case vide] ; interdits : films déjà placés dans la grille."""
    cases = [c - interdits for c in cases]
    if any(not c for c in cases):
        return False
    pris = {}

    def placer(i, vus):
        for f in cases[i]:
            if f in vus:
                continue
            vus.add(f)
            if f not in pris or placer(pris[f], vus):
                pris[f] = i
                return True
        return False
    ordre = sorted(range(len(cases)), key=lambda i: len(cases[i]))
    return all(placer(i, set()) for i in ordre)


def _grille_lignes(x, n):
    """Grille « lignes × colonnes » vérifiée : chaque croisement a au moins MINI_CASE films connus."""
    types = actives(x.cfg, "donna_", x.profils, sans_fiche=True)
    for essai in range(4):
        cands = _candidats(x, 6 * n + 12, types)
        if len(cands) < 2 * n:
            continue
        ok = _ensembles(x, cands)
        mini = MINI_CASE if essai < 3 else 1
        rang = [i for i in range(len(cands)) if len(ok[i]) >= mini * n]
        for _ in range(500):
            if len(rang) < 2 * n:
                break
            lignes = random.sample(rang, n)
            tl = [cands[i]["type"] for i in lignes]
            if max(tl.count(t) for t in tl) > 2:
                continue
            possibles = [c for c in rang if c not in lignes and all(
                compatibles(cands[a], cands[c]) and len(ok[a] & ok[c]) >= mini for a in lignes)]
            random.shuffle(possibles)
            colonnes = []
            for c in possibles:
                t = [cands[i]["type"] for i in lignes + colonnes + [c]]
                if t.count(cands[c]["type"]) <= 2:
                    colonnes.append(c)
                if len(colonnes) == n:
                    # toute la grille doit pouvoir être remplie avec des films tous différents
                    if faisable([ok[l] & ok[c] for l in lignes for c in colonnes]):
                        return {"mode": "lignes", "cands": cands, "ok": ok, "lignes": lignes, "colonnes": colonnes}
                    break
    return None


def _grille_cases(x, n):
    """Une condition par case ; chacune doit avoir des films connus qui y répondent (sauf les conditions qu'on ne
    peut vérifier qu'avec les détails du film : pays, durée, box-office, saga, qui ont toujours des réponses)."""
    cands = _candidats(x, n * n + RESERVE + 6)
    ok = _ensembles(x, cands)
    cands = [c for c, o in zip(cands, ok) if c["type"] in LENTES or len(o) >= MINI_CASE]
    if len(cands) < n * n:
        return None
    return {"mode": "cases", "cands": cands, "ok": None, "cases": list(range(n * n))}


def construire(api, cfg, pool, deja):
    n = 3 if str(cfg.get("donna_taille", "2")) == "3" else 2
    mode = "lignes" if cfg.get("donna_mode") == "lignes" else "cases"
    duree = float(cfg["dur_donna"]) * (2 if n == 3 else 1)
    profils = cfg.get("_profils", [])

    def fabriquer(connus, sauf=None):
        x = Ctx(api, cfg, pool, 1, realisateurs_ok=connus, sauf=sauf)
        return _grille_lignes(x, n) if mode == "lignes" else _grille_cases(x, n)

    if cfg.get("donna_grilles", "joueur") == "joueur":
        # une grille par profil (ses réalisateurs, jamais ses propres notes) + des grilles pour les joueurs sans profil
        taches = {f"_{k}": (None, None) for k in range(GENERIQUES)}
        taches.update({"p:" + p["nom"]: (connus_de(p), p["nom"]) for p in profils})
    else:
        taches = {"commune": (connus_communs(profils), None)}
    with ThreadPoolExecutor(max_workers=4) as ex:                 # les grilles se construisent en parallèle
        faites = dict(zip(taches, ex.map(lambda t: fabriquer(*t), taches.values())))
    grilles = {k: g for k, g in faites.items() if g}
    if not grilles:
        raise RuntimeError("Bingo : impossible de construire une grille dont chaque case a une réponse "
                           "(activez plus de conditions ou d'autres listes).")
    une = next(iter(grilles.values()))
    etat = {"taille": n, "mode": mode, "par_joueur": "commune" not in grilles}
    if "commune" in grilles:
        g = grilles["commune"]
        if mode == "lignes":
            etat.update(lignes=[g["cands"][i]["txt"] for i in g["lignes"]],
                        colonnes=[g["cands"][i]["txt"] for i in g["colonnes"]])
        else:
            etat["cases"] = [g["cands"][i]["txt"] for i in g["cases"]]
    return dict(jeu="donna", vue="bingo", duree=duree, reponse="bingo", revelation=None, images=[], cles=[], bonne="",
                solution="Grille de bingo", detail="", films=[], suggestions=True, films_pool=pool, api=api, taille=n,
                mode=mode, grilles=grilles, contraintes=une["cands"], etapes=[(0.0, etat)],
                signature=tuple(sorted(c["txt"] for g in grilles.values()
                                       for i in (g.get("lignes", []) + g.get("colonnes", []) + g.get("cases", []))
                                       for c in [g["cands"][i]])))


class Moteur:
    suggestions = True
    films_tmdb = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.n, self.mode, self.grilles = m["taille"], m["mode"], m["grilles"]
        self.joueurs = {}                          # pid -> sa grille (copie modifiable)
        self.generiques = 0
        toutes = [c for g in self.grilles.values() for c in g["cands"]]
        self.avec_fiche = any(c.get("fiche") for c in toutes)
        valides = []
        for c in toutes:
            try:
                valides += c["valides"]()
            except Exception:  # noqa: BLE001
                pass
        self.idx = index(list(m["films_pool"]) + valides)
        self.entrees = entrees_films([f for f, _ in self.idx])
        self.finis = []
        for pid in partie.joueurs:
            self._etat(pid)

    def ok(self):
        return ""

    # ---------- grille de chaque joueur ----------
    def _cle_grille(self, pid):
        j = self.p.joueurs.get(pid)
        if "commune" in self.grilles:
            return "commune"
        if j and j.profil and "p:" + j.profil in self.grilles:
            return "p:" + j.profil
        gen = [k for k in self.grilles if k.startswith("_")] or list(self.grilles)
        k = gen[self.generiques % len(gen)]
        self.generiques += 1
        return k

    def _etat(self, pid):
        if pid not in self.joueurs:
            k = self._cle_grille(pid)
            g = self.grilles[k]
            e = {"g": k, "cases": [{"film": None, "k": None, "f": None, "relances": 0} for _ in range(self.n * self.n)],
                 "deja": set()}
            if self.mode == "lignes":
                e.update(lignes=list(g["lignes"]), colonnes=list(g["colonnes"]), rel_l=[0] * self.n,
                         rel_c=[0] * self.n)
                e["deja"] |= set(g["lignes"]) | set(g["colonnes"])
            else:
                for i, c in enumerate(g["cases"]):
                    e["cases"][i]["c"] = c
                e["deja"] |= set(g["cases"])
            self.joueurs[pid] = e
        return self.joueurs[pid]

    def _cands(self, e):
        return self.grilles[e["g"]]["cands"]

    def conditions(self, e, i):
        """Conditions d'une case : celles de sa ligne et de sa colonne, ou la sienne (mode cases)."""
        cands = self._cands(e)
        if self.mode == "lignes":
            return [cands[e["lignes"][i // self.n]], cands[e["colonnes"][i % self.n]]]
        return [cands[e["cases"][i]["c"]]]

    def relances(self, e, i):
        if self.mode == "lignes":
            return e["rel_l"][i // self.n] + e["rel_c"][i % self.n]
        return e["cases"][i]["relances"]

    def valeur(self, e, i):
        return max(10, int(self.cfg["donna_pts"] * (1 - self.cfg["donna_malus"] / 100) ** self.relances(e, i)))

    # ---------- hors verrou : retrouver le film tapé (peut interroger TMDB) ----------
    def resoudre(self, d):
        return resoudre(self.m["api"], d.get("texte"), self.idx, self.avec_fiche)

    def suggerer(self, q):
        return suggerer_films(self.m["api"], q, self.entrees)

    # ---------- changer une condition ----------
    def _changer(self, e, cible):
        cands, g = self._cands(e), self.grilles[e["g"]]
        n = self.n
        if self.mode == "cases":
            try:
                i = int(cible[1:])
            except (TypeError, ValueError):
                return {"ok": False, "msg": "Case inconnue"}
            if not 0 <= i < n * n:
                return {"ok": False, "msg": "Case inconnue"}
            case = e["cases"][i]
            if case["film"]:
                return {"ok": False, "msg": "Case déjà remplie"}
            prises = {x["c"] for x in e["cases"]}
            libres = [k for k in range(len(cands)) if k not in prises and k not in e["deja"]] or \
                     [k for k in range(len(cands)) if k not in prises]
            if not libres:
                return {"ok": False, "msg": "Plus d'autre condition disponible"}
            case["c"] = random.choice(libres)
            e["deja"].add(case["c"])
            case["relances"] += 1
            return {"ok": True, "msg": f"Nouvelle condition : {cands[case['c']]['txt']} ({self.valeur(e, i)} pts)"}
        sens, num = cible[:1], cible[1:]
        try:
            r = int(num)
        except ValueError:
            return {"ok": False, "msg": "Condition inconnue"}
        if sens not in ("l", "c") or not 0 <= r < n:
            return {"ok": False, "msg": "Condition inconnue"}
        ok = g["ok"]
        cases_lig = [r * n + c for c in range(n)] if sens == "l" else [c * n + r for c in range(n)]
        if all(e["cases"][i]["film"] for i in cases_lig):
            return {"ok": False, "msg": "Toutes ses cases sont déjà remplies"}
        autres = e["colonnes"] if sens == "l" else e["lignes"]       # les conditions qu'elle croise
        prises = set(e["lignes"]) | set(e["colonnes"])
        places = frozenset(x["k"] for x in e["cases"] if x["k"])
        vides = [autres[c] for c, i in enumerate(cases_lig) if not e["cases"][i]["film"]]

        def grille_faisable(k):
            """Avec la condition k à la place : chaque case vide de la grille a encore un film différent possible."""
            lig = list(e["lignes"]); col = list(e["colonnes"])
            (lig if sens == "l" else col)[r] = k
            return faisable([ok[lig[i // n]] & ok[col[i % n]] for i in range(n * n) if not e["cases"][i]["film"]],
                            places)
        cands_ok = []
        for mini in (MINI_CASE, 1):
            for k in range(len(cands)):
                if k in prises or k in e["deja"]:
                    continue
                if all(compatibles(cands[k], cands[a]) for a in autres) and \
                        all(len(ok[k] & ok[a]) >= mini for a in vides) and grille_faisable(k):
                    cands_ok.append(k)
            if cands_ok:
                break
        if not cands_ok:
            return {"ok": False, "msg": "Aucune autre condition ne garde la grille faisable"}
        k = random.choice(cands_ok)
        e["deja"].add(k)
        if sens == "l":
            e["lignes"][r] = k
            e["rel_l"][r] += 1
        else:
            e["colonnes"][r] = k
            e["rel_c"][r] += 1
        return {"ok": True, "msg": f"Nouvelle condition : {cands[k]['txt']}"}

    # ---------- actions ----------
    def action(self, pid, d, frac, info=None):
        e = self._etat(pid)
        if pid in self.finis:
            return {"ok": False, "msg": "Grille déjà complète !"}
        if d.get("type") in ("changer", "relancer"):
            cible = d.get("cible") or (f"k{d.get('case')}" if d.get("case") is not None else "")
            return self._changer(e, str(cible))
        try:
            i = int(d.get("case"))
        except (TypeError, ValueError):
            return {"ok": False, "msg": "Touchez d'abord une case"}
        if not 0 <= i < self.n * self.n:
            return {"ok": False, "msg": "Case inconnue"}
        case = e["cases"][i]
        if case["film"]:
            return {"ok": False, "msg": "Case déjà remplie"}
        if not info or not info.get("film"):
            return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
        f, fi = info["film"], info.get("fiche")
        if f.get("tv"):
            return {"ok": False, "msg": "Un film, pas une série"}
        k = cle_film(f)
        if k in {x["k"] for x in e["cases"]}:
            return {"ok": False, "msg": "Ce film est déjà dans votre grille"}
        utilises = self.p.utilises.setdefault(pid, set())
        if self.cfg.get("films_uniques", True) and k in utilises:
            return {"ok": False, "msg": f"{libelle(f)} : déjà donné dans une manche précédente"}
        rates = []
        for c in self.conditions(e, i):
            try:
                if not c["test"](f, fi):
                    rates.append(c["txt"])
            except Exception:  # noqa: BLE001
                rates.append(c["txt"])
        if rates:
            return {"ok": False, "msg": f"Raté : {libelle(f)} ne colle pas à « {rates[0]} »"}
        case.update(film=libelle(f), k=k, f=f)
        utilises.add(k)
        j = self.p.joueurs[pid]
        pts = self.valeur(e, i)
        j.gain += pts
        j.score += pts
        j.essais += 1
        msg = f"✓ {libelle(f)} (+{pts})"
        if all(x["film"] for x in e["cases"]):
            rang = len(self.finis)
            bonus = self.cfg["donna_bingo"] + (int(self.cfg.get("donna_premier", 400) * RANGS[rang])
                                               if rang < len(RANGS) else 0)
            self.finis.append(pid)
            j.gain += bonus
            j.score += bonus
            j.trouve = True
            msg += f" — Bingo{' (1er !)' if rang == 0 else ''} +{bonus}"
        return {"ok": True, "correct": True, "msg": msg}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(p in self.finis for p in J)

    def clore(self):
        for pid, j in self.p.joueurs.items():
            j.serie = j.serie + 1 if pid in self.finis else 0

    def statut(self, pid):
        if pid in self.finis:
            return {"t": "bingo !", "c": "ok"}
        n = sum(1 for x in self._etat(pid)["cases"] if x["film"])
        return {"t": f"{n}/{self.n * self.n}", "c": "go" if n else ""}

    def avancement(self):
        n = len(self.finis)
        return f"{n} grille{'s' if n > 1 else ''} complète{'s' if n > 1 else ''}"

    # ---------- vues ----------
    def _j(self, pid):
        j = self.p.joueurs.get(pid)
        return j.public() if j else None

    def _grille_vue(self, pid):
        e = self._etat(pid)
        cands = self._cands(e)
        v = {"cases": [{"txt": cands[x["c"]]["txt"] if self.mode == "cases" else "", "film": x["film"],
                        "relances": self.relances(e, i), "valeur": self.valeur(e, i)} for i, x in enumerate(e["cases"])]}
        if self.mode == "lignes":
            v.update(lignes=[cands[k]["txt"] for k in e["lignes"]], colonnes=[cands[k]["txt"] for k in e["colonnes"]],
                     rel_l=list(e["rel_l"]), rel_c=list(e["rel_c"]))
        return v

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"taille": self.n, "mode": self.mode, "par_joueur": "commune" not in self.grilles,
             "progres": [dict(x, cases=[bool(c["film"]) for c in self._etat(p)["cases"]], bingo=p in self.finis,
                              rang=self.finis.index(p) + 1 if p in self.finis else 0)
                         for p in J if (x := self._j(p))]}
        if "commune" in self.grilles and self.mode == "lignes":
            g = self.grilles["commune"]
            v.update(lignes=[g["cands"][k]["txt"] for k in g["lignes"]],
                     colonnes=[g["cands"][k]["txt"] for k in g["colonnes"]])
        if pid:
            v.update(self._grille_vue(pid), actif=not revele and not self.p.pause and pid not in self.finis,
                     malus=self.cfg["donna_malus"])
        if revele:
            v["resultats"] = sorted([dict(self._j(p), bingo=p in self.finis, **self._grille_vue(p)) for p in J],
                                    key=lambda x: -sum(1 for c in x["cases"] if c["film"]))
        return v
