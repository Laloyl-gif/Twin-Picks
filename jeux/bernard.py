"""Bernard Renault's Poker (Le poker) : Bernard, le dernier des frères Renault, tient une table de Texas Hold'em où
les cartes sont des films. Chaque manche, la table a ses propres règles, cachées au départ :
- la couleur (♠ ♥ ♦ ♣) d'un film dépend d'une chose (sa décennie, sa famille de genre, sa note, sa durée) ;
- les chiffres (2 à 10) suivent une autre (l'année, la note, la durée, le nombre de votants TMDB) ;
- les figures (valet, dame, roi, as) sont des conditions : « as = film avec Samuel L. Jackson »…
On ne voit que les affiches et les titres. À chaque tour, les cartes du milieu montrent leur valeur et leur couleur,
et une partie des règles se dévoile : à chacun de deviner ce que valent ses propres cartes.
Déroulement : deux cartes secrètes chacun ; tour de mise ; trois cartes au milieu ; tour ; une carte ; tour ; une
carte ; dernier tour ; abattage. À chaque tour, on peut défausser une de ses cartes (elle est remplacée), mais
chaque défausse retire un pourcentage du gain final. On reste, on relance (+100, +250, +500) ou on se couche, tous
en même temps. Bernard suit toujours. Les pots suivent les règles du poker : plus on a misé, plus on peut gagner.
"""
import random
from collections import Counter
from itertools import combinations

from PIL import ImageOps

from tmdb import GENRES, cle_film, fiche
from visuels import en_jpeg
from .commun import affiche

COULEURS = "♠♥♦♣"
FIGURES = {11: "Valet", 12: "Dame", 13: "Roi", 14: "As"}
NOM_RANG = {**{k: str(k) for k in range(2, 11)}, 11: "V", 12: "D", 13: "R", 14: "A"}
MAINS = ["Hauteur", "Paire", "Double paire", "Brelan", "Suite", "Couleur", "Full", "Carré", "Quinte flush"]
RELANCES = (0, 100, 250, 500)
FAMILLES = [("action, aventure, SF ou fantastique", {28, 12, 878, 14}), ("drame, romance, histoire ou guerre", {18, 10749, 36, 10752}),
            ("comédie, animation, famille ou musique", {35, 16, 10751, 10402}), ("thriller, crime, horreur ou mystère", {53, 80, 27, 9648, 37})]


def _an(fi):
    try:
        return int(fi.get("annee") or 0)
    except ValueError:
        return 0


def _quantiles(vals, n):
    s = sorted(vals)
    return [s[min(len(s) - 1, int(len(s) * k / n))] for k in range(1, n)]


def _bucket(x, seuils):
    return sum(1 for s in seuils if x >= s)


def regles(cartes):
    """Les règles de la table : (couleur, chiffres, figures) et leurs textes."""
    dims = {
        "décennie": (lambda fi: _an(fi), "l'année de sortie"),
        "note": (lambda fi: fi.get("note") or 0, "la note TMDB"),
        "durée": (lambda fi: fi.get("duree") or 0, "la durée"),
        "votants": (lambda fi: fi.get("votes") or 0, "le nombre de votants TMDB"),
    }
    choix_c = random.choice(["décennie", "genre", "note", "durée"])
    if choix_c == "genre":
        def coul(fi):
            for k, (_, ids) in enumerate(FAMILLES):
                if ids & set(fi.get("genre_ids") or []):
                    return k
            return 3
        txt_c = "Couleur = la famille de genre : " + " · ".join(f"{COULEURS[k]} {nom}" for k, (nom, _) in enumerate(FAMILLES))
        court_c = "Couleur : selon le genre"
    else:
        f_c = dims[choix_c][0]
        seuils_c = _quantiles([f_c(fi) for _, fi in cartes], 4)
        def coul(fi, f_c=f_c, s=seuils_c):
            return _bucket(f_c(fi), s)
        unite = {"décennie": "", "note": "", "durée": " min"}.get(choix_c, "")
        bornes = [f"{x:g}{unite}".replace(".", ",") for x in seuils_c]
        txt_c = (f"Couleur = {dims[choix_c][1]} : {COULEURS[0]} moins de {bornes[0]} · {COULEURS[1]} jusqu'à {bornes[1]} · "
                 f"{COULEURS[2]} jusqu'à {bornes[2]} · {COULEURS[3]} au-delà")
        court_c = f"Couleur : selon {dims[choix_c][1]}"
    autres = [k for k in dims if k != choix_c]
    choix_v = random.choice(autres)
    f_v = dims[choix_v][0]
    seuils_v = _quantiles([f_v(fi) for _, fi in cartes], 9)
    txt_v = f"Chiffres = {dims[choix_v][1]} : 2 pour les plus petits, 10 pour les plus grands"
    court_v = f"Chiffres : selon {dims[choix_v][1]}"
    # les figures : des conditions qui touchent 2 à 6 cartes du paquet (des personnes d'abord)
    cands = []
    acteurs, reals = Counter(), Counter()
    noms = {}
    for _, fi in cartes:
        for a in fi.get("acteurs", [])[:8]:
            acteurs[a["id"]] += 1
            noms[("a", a["id"])] = a["nom"]
        for r in fi.get("realisateurs", [])[:2]:
            reals[r["id"]] += 1
            noms[("r", r["id"])] = r["nom"]
    for i, n in acteurs.items():
        if 2 <= n <= 6:
            cands.append((3, f"film avec {noms[('a', i)]}", "un acteur", lambda fi, i=i: any(a["id"] == i for a in fi.get("acteurs", [])[:8])))
    for i, n in reals.items():
        if 2 <= n <= 6:
            cands.append((3, f"film de {noms[('r', i)]}", "un réalisateur", lambda fi, i=i: any(r["id"] == i for r in fi.get("realisateurs", [])[:2])))
    for g, nom in GENRES.items():
        n = sum(1 for _, fi in cartes if g in (fi.get("genre_ids") or []))
        if 2 <= n <= 6:
            cands.append((1, f"film de genre {nom.lower()}", "un genre", lambda fi, g=g: g in (fi.get("genre_ids") or [])))
    cands.append((1, "film de plus de 2 h 20", "la durée", lambda fi: (fi.get("duree") or 0) > 140))
    cands.append((1, "titre en un seul mot", "le titre", lambda fi: len((fi.get("titre") or "").split()) == 1))
    cands = [c for c in cands if 2 <= sum(1 for _, fi in cartes if c[3](fi)) <= 6]
    random.shuffle(cands)
    cands.sort(key=lambda c: -c[0])
    figures = cands[:4]
    random.shuffle(figures)
    figs = {14 - k: (txt, t, court) for k, (_, txt, court, t) in enumerate(figures)}    # as, roi, dame, valet

    def evaluer(fi):
        rang = next((r for r in (14, 13, 12, 11) if r in figs and figs[r][1](fi)), None)
        if rang is None:
            rang = 2 + _bucket(f_v(fi), seuils_v)
        return rang, coul(fi)
    # pendant la partie, on ne dit que SUR QUOI portent les règles ; le détail se dévoile à l'abattage
    textes = {"couleur": court_c, "chiffres": court_v,
              "figures": [f"{FIGURES[r]} : {figs[r][2]}" for r in (11, 12, 13, 14) if r in figs],
              "detail": [txt_c, txt_v] + [f"{FIGURES[r]} = {figs[r][0]}" for r in (11, 12, 13, 14) if r in figs]}
    return evaluer, textes


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    cartes = []
    for f in films[:60]:
        try:
            fi = fiche(api, f)
        except Exception:  # noqa: BLE001
            continue
        if _an(fi):
            cartes.append((f, fi))
        if len(cartes) == 36:
            break
    if len(cartes) < 24:
        raise RuntimeError("Le poker de Bernard : pas assez de films dans les listes choisies.")
    evaluer, textes = regles(cartes)
    images, paquet = [], []
    for i, (f, fi) in enumerate(cartes):
        images.append(en_jpeg(ImageOps.fit(affiche(api, f, "w185"), (160, 240)), 240))
        r, c = evaluer(fi)
        paquet.append({"img": i, "txt": f["title"], "r": r, "c": c})
    for f, _ in cartes[:16]:
        deja.add(cle_film(f))
    T = float(cfg.get("bernard_tour", 30))
    return dict(jeu="bernard", vue="poker", duree=round(4 * T + 8, 1), reponse="poker",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[],
                bonne="", solution="Abattage", detail="", films=[cle_film(f) for f, _ in cartes[:12]], paquet=paquet,
                regles=textes, dur_tour=T, signature=tuple(p["txt"] for p in paquet[:10]))


# ---------------- évaluation des mains (5 cartes parmi 7) ----------------
def _cinq(cs):
    rangs = sorted((r for r, _ in cs), reverse=True)
    cnt = Counter(rangs)
    groupes = sorted(cnt.items(), key=lambda x: (-x[1], -x[0]))
    flush = len({c for _, c in cs}) == 1
    uniq = sorted(set(rangs), reverse=True)
    suite = None
    if len(uniq) == 5 and uniq[0] - uniq[4] == 4:
        suite = uniq[0]
    elif uniq == [14, 5, 4, 3, 2]:
        suite = 5
    if suite and flush:
        return (8, suite)
    if groupes[0][1] == 4:
        return (7, groupes[0][0], groupes[1][0])
    if groupes[0][1] == 3 and groupes[1][1] == 2:
        return (6, groupes[0][0], groupes[1][0])
    if flush:
        return (5, *rangs)
    if suite:
        return (4, suite)
    if groupes[0][1] == 3:
        return (3, groupes[0][0], *[g for g, n in groupes[1:]])
    if groupes[0][1] == 2 and groupes[1][1] == 2:
        return (2, groupes[0][0], groupes[1][0], groupes[2][0])
    if groupes[0][1] == 2:
        return (1, groupes[0][0], *[g for g, n in groupes[1:]])
    return (0, *rangs)


def meilleure(cs):
    """(valeur comparable, les 5 cartes) de la meilleure main de 5 parmi les cartes données."""
    if len(cs) < 5:
        return ((-1,), list(cs))
    return max(((_cinq(c), c) for c in combinations(cs, 5)), key=lambda x: x[0])


class Moteur:
    suggestions = False
    BERNARD = "__bernard__"

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.sabot = list(range(len(m["paquet"])))
        random.shuffle(self.sabot)
        self.joueurs = list(partie.joueurs)
        self.mains = {pid: [self.sabot.pop(), self.sabot.pop()] for pid in self.joueurs + [self.BERNARD]}
        self.milieu = [self.sabot.pop() for _ in range(5)]
        self.tour, self.debut = 0, 1.0                    # 0 : avant le flop, 1 : flop, 2 : turn, 3 : river
        self.mises = {pid: 0 for pid in self.joueurs}
        self.joue = {}                                    # pid -> choix fait ce tour
        self.couches = set()
        self.defausses = {pid: 0 for pid in self.joueurs}
        self.defausse_tour = set()
        self.fin = False
        self.gains, self.mains_finales = {}, {}

    def ok(self):
        return ""

    def _actifs(self):
        return [p for p in self.joueurs if p in self.p.joueurs and p not in self.couches]

    def _maj(self):
        if self.fin:
            return
        t = self.p.ecoule - self.debut
        actifs = self._actifs()
        if t >= self.m["dur_tour"] or (actifs and all(p in self.joue for p in actifs)) or not actifs:
            self.tour += 1
            self.joue, self.defausse_tour = {}, set()
            self.debut = self.p.ecoule
            if self.tour > 3 or not actifs:
                self.fin = True

    def _visibles(self):
        return {0: 0, 1: 3, 2: 4, 3: 5}.get(self.tour, 5)

    def action(self, pid, d, frac, info=None):
        self._maj()
        if self.fin:
            return {"ok": False, "msg": "Abattage !"}
        if pid not in self.mises:
            return {"ok": False, "msg": "Vous n'êtes pas à la table"}
        if pid in self.couches:
            return {"ok": False, "msg": "Vous êtes couché"}
        if "defausser" in d:
            k = d.get("defausser")
            if self.tour >= 3:
                return {"ok": False, "msg": "Plus de défausse au dernier tour"}
            if pid in self.defausse_tour or pid in self.joue:
                return {"ok": False, "msg": "Une défausse par tour, avant de miser"}
            if k not in (0, 1) or not self.sabot:
                return {"ok": False, "msg": ""}
            self.mains[pid][k] = self.sabot.pop()
            self.defausses[pid] += 1
            self.defausse_tour.add(pid)
            return {"ok": True, "msg": f"Carte remplacée (−{int(self.cfg.get('bernard_defausse', 15))} % du gain final)"}
        if pid in self.joue:
            return {"ok": False, "msg": "Déjà joué ce tour"}
        if d.get("coucher"):
            self.couches.add(pid)
            self.joue[pid] = "couché"
            return {"ok": True, "msg": "Vous vous couchez"}
        x = d.get("relance")
        if x not in RELANCES:
            return {"ok": False, "msg": ""}
        self.mises[pid] += x
        self.joue[pid] = f"+{x}" if x else "reste"
        return {"ok": True, "msg": f"Mise : {self.mises[pid]}" if x else "Vous restez"}

    def fini(self):
        self._maj()
        return self.fin

    def _calculer(self):
        mid = [(self.m["paquet"][i]["r"], self.m["paquet"][i]["c"]) for i in self.milieu]
        val = {}
        for pid, main in self.mains.items():
            cs = [(self.m["paquet"][i]["r"], self.m["paquet"][i]["c"]) for i in main] + mid
            v, cinq = meilleure(cs)
            val[pid] = v
            self.mains_finales[pid] = MAINS[v[0]] if v[0] >= 0 else ""
        contrib = dict(self.mises)
        contrib[self.BERNARD] = max(contrib.values(), default=0)    # Bernard suit toujours
        eligibles = {p for p in contrib if p not in self.couches and (p in self.p.joueurs or p == self.BERNARD)}
        gagne = {p: 0 for p in contrib}
        niveaux = sorted(set(contrib.values()))
        prec = 0
        for lv in niveaux:
            if lv <= prec:
                continue
            couche_pot = sum(min(c, lv) - min(c, prec) for c in contrib.values())
            el = [p for p in eligibles if contrib[p] >= lv]
            if el and couche_pot:
                best = max(val[p] for p in el)
                w = [p for p in el if val[p] == best]
                for p in w:
                    gagne[p] += couche_pot / len(w)
            prec = lv
        self.vainqueurs = [p for p in eligibles if val[p] == max(val[q] for q in eligibles)] if eligibles else []
        net = {}
        pct = float(self.cfg.get("bernard_defausse", 15)) / 100
        bonus = int(self.cfg.get("bernard_pts", 200))
        for p in self.joueurs:
            n = gagne.get(p, 0) - contrib.get(p, 0)
            if p in self.vainqueurs:
                n += bonus                                 # même sans miser, gagner la main rapporte un peu
            if n > 0:
                n *= max(0.0, 1 - pct * self.defausses.get(p, 0))
            net[p] = int(round(n))
        return net

    def clore(self):
        self.fin = True
        net = self._calculer()
        for pid, j in self.p.joueurs.items():
            gain = max(net.get(pid, 0), -j.score)
            self.gains[pid] = gain
            j.gain += gain
            j.score += gain
            j.trouve = pid in self.vainqueurs
            j.serie = j.serie + 1 if j.trouve else 0

    def duree_revelation(self, base):
        return base + 6

    def statut(self, pid):
        if pid in self.couches:
            return {"t": "couché", "c": "ko"}
        return {"t": f"mise {self.mises.get(pid, 0)}" + (" ✓" if pid in self.joue else ""), "c": "ok" if pid in self.joue else ""}

    def avancement(self):
        noms = ["Avant le flop", "Le flop", "Le turn", "La river"]
        return f"{noms[min(self.tour, 3)]} · {len(self.joue)} / {len(self._actifs())} ont joué" if not self.fin else "Abattage"

    def _carte(self, i, montrer):
        c = self.m["paquet"][i]
        x = {"img": c["img"], "txt": c["txt"]}
        if montrer:
            x.update(r=NOM_RANG[c["r"]], c=COULEURS[c["c"]], rouge=c["c"] in (1, 2))
        return x

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        nv = 5 if revele else self._visibles()
        R = self.m["regles"]
        connues = []
        if revele:
            connues = list(R.get("detail") or [])
        elif True:
            if self.tour >= 1:
                connues.append(R["couleur"])
            if self.tour >= 2:
                connues.append(R["chiffres"])
                connues += [x for x in R["figures"] if x.startswith(("Valet", "Dame"))]
            if self.tour >= 3:
                connues += [x for x in R["figures"] if x.startswith(("Roi", "As"))]
        v = {"tour": self.tour, "fin": self.fin, "reste": round(max(0.0, self.m["dur_tour"] - (self.p.ecoule - self.debut)), 1),
             "milieu": [self._carte(i, True) for i in self.milieu[:nv]] + [None] * (5 - nv),
             "regles": connues, "n_regles": 2 + len(R["figures"]), "relances": list(RELANCES),
             "pot": sum(self.mises.values()) + max(self.mises.values(), default=0),
             "joueurs": [dict(J[p].public(), mise=self.mises.get(p, 0), couche=p in self.couches, a_joue=self.joue.get(p),
                              defausses=self.defausses.get(p, 0),
                              cartes=[self._carte(i, True) for i in self.mains[p]] if revele else [],
                              main=self.mains_finales.get(p, "") if revele else "") for p in self.joueurs if p in J],
             "bernard": {"cartes": [self._carte(i, True) for i in self.mains[self.BERNARD]] if revele else [],
                         "main": self.mains_finales.get(self.BERNARD, "") if revele else "",
                         "gagne": revele and self.BERNARD in getattr(self, "vainqueurs", [])}}
        if pid and pid in self.mains:
            v.update(mes_cartes=[self._carte(i, revele) for i in self.mains[pid]], ma_mise=self.mises.get(pid, 0),
                     couche=pid in self.couches, deja_joue=self.joue.get(pid), peut_defausser=self.tour < 3 and
                     pid not in self.defausse_tour and pid not in self.joue and not self.fin,
                     defausses=self.defausses.get(pid, 0), pct=int(self.cfg.get("bernard_defausse", 15)),
                     actif=not revele and not self.p.pause and not self.fin and pid not in self.couches and pid not in self.joue)
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0), main=self.mains_finales.get(p, ""),
                                          gagne=p in getattr(self, "vainqueurs", [])) for p in J], key=lambda x: -x["gain"])
        return v
