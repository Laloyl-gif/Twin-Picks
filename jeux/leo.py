"""Leo's New Shoes (Plus ou moins) : « Leo needs a new pair of shoes! » On parie, comme aux dés : quatre duels de
deux films ; pour chacun, lequel est le plus récent, le plus long, le mieux noté ou celui qui a le plus rapporté ?
Chaque joueur touche un film par duel (on ne revient pas sur un pari).
Points : par duel gagné, plus un bonus si les quatre sont justes (et un bonus de rapidité). À la réponse : les vraies
valeurs sous chaque film.
"""
import random
from concurrent.futures import ThreadPoolExecutor

from PIL import ImageOps

from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche
from .ben import montant

CRITERES = {
    "annee": ("Le plus récent ?", lambda fi: int(fi["annee"]) if fi["annee"][:4].isdigit() else None, 1,
              lambda v: str(v)),
    "duree": ("Le plus long ?", lambda fi: fi["duree"] or None, 3, lambda v: f"{v // 60} h {v % 60:02d}"),
    "note": ("Le mieux noté sur TMDB ?", lambda fi: round(fi["note"], 1) if fi["votes"] >= 200 else None, 0.1,
             lambda v: f"{v:.1f}".replace(".", ",") + "/10"),
    "recettes": ("Celui qui a le plus rapporté ?", lambda fi: fi.get("recettes") or None, None, montant),
}


def _ecart(cle, a, b):
    """Écart relatif entre deux valeurs (0 : égales) ; on cherche les duels serrés (petit écart, mais pas nul)."""
    if cle == "recettes":
        return max(a, b) / max(1, min(a, b)) - 1
    return abs(a - b)


SEUILS = {"annee": (1, 4), "duree": (3, 14), "note": (0.1, 0.6), "recettes": (0.08, 0.6)}   # (écart mini, maxi)


def construire(api, cfg, pool, deja):
    duree, nb = float(cfg["dur_leo"]), int(cfg.get("leo_duels", 4))
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    neufs = [f for f in films if cle_film(f) not in deja]
    if len(neufs) < nb * 4:
        neufs = films
    if len(neufs) < nb * 2:
        raise RuntimeError("Plus ou moins : pas assez de films dans les listes.")
    random.shuffle(neufs)
    def lire(f):
        try:
            return f, fiche(api, f)
        except Exception:  # noqa: BLE001
            return f, None

    with ThreadPoolExecutor(max_workers=8) as ex:
        fiches = [(f, fi) for f, fi in ex.map(lire, neufs[:nb * 10]) if fi]
    criteres = [k for k in CRITERES if cfg.get("leo_" + k, True)] or list(CRITERES)
    duels, pris = [], set()
    for k in range(nb):
        cle = criteres[k % len(criteres)] if len(criteres) >= nb else random.choice(criteres)
        lib, val, _, fmt = CRITERES[cle]
        libres = [(f, fi) for f, fi in fiches if cle_film(f) not in pris and val(fi) is not None]
        mini, maxi = SEUILS[cle]
        paires = [(_ecart(cle, val(fia), val(fib)), fa, fia, fb, fib) for i, (fa, fia) in enumerate(libres)
                  for fb, fib in libres[i + 1:]]
        serrees = sorted([p for p in paires if mini <= p[0] <= maxi], key=lambda p: p[0])
        if not serrees:                                 # rien d'assez serré : le moins écarté au-dessus du minimum
            serrees = sorted([p for p in paires if p[0] >= mini], key=lambda p: p[0])
        trouve = random.choice(serrees[:4])[1:] if serrees else None
        if not trouve:
            continue
        fa, fia, fb, fib = trouve
        pris |= {cle_film(fa), cle_film(fb)}
        va, vb = val(fia), val(fib)
        duels.append({"critere": cle, "question": lib, "films": [fa, fb], "valeurs": [fmt(va), fmt(vb)],
                      "bonne": 0 if va > vb else 1})
    if len(duels) < 2:
        raise RuntimeError("Plus ou moins : pas assez d'informations sur les films des listes.")
    random.shuffle(duels)
    images, items = [], []
    for k, du in enumerate(duels):
        for f in du["films"]:
            images.append(en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (300, 450)), 450))
        items.append({"question": du["question"], "a": {"img": 2 * k, "txt": du["films"][0]["title"]},
                      "b": {"img": 2 * k + 1, "txt": du["films"][1]["title"]}})
    etat = {"duels": items, "indices": []}
    return dict(jeu="leo", vue="duels", duree=duree, reponse="duels", etapes=[(0.0, etat)], images=images,
                revelation=None, cles=[], bonne="", duels=[{"bonne": d["bonne"], "valeurs": d["valeurs"]} for d in duels],
                solution="Les bons paris", detail=" · ".join(
                    f"{d['films'][d['bonne']]['title']} ({d['valeurs'][d['bonne']]})" for d in duels),
                films=[cle_film(f) for d in duels for f in d["films"]])


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.n = len(m["duels"])
        self.reponses, self.fracs, self.gains = {}, {}, {}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        k, i = d.get("duel"), d.get("i")
        if type(k) is not int or not 0 <= k < self.n or i not in (0, 1):
            return {"ok": False, "msg": "Touchez un des deux films"}
        r = self.reponses.setdefault(pid, {})
        if str(k) in r:
            return {"ok": False, "msg": "Pari déjà fait"}
        r[str(k)] = i
        self.fracs[pid] = frac
        if len(r) == self.n:
            self.p.joueurs[pid].essais = 1
            return {"ok": True, "msg": "Tous les paris sont faits !"}
        return {"ok": True, "msg": f"Pari noté ({len(r)}/{self.n})"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(len(self.reponses.get(p, {})) == self.n for p in J)

    def justes(self, pid):
        r = self.reponses.get(pid, {})
        return {k: r[k] == self.m["duels"][int(k)]["bonne"] for k in r}

    def clore(self):
        pts, bonus = self.cfg.get("leo_pts", 250), self.cfg.get("leo_parfait", 300)
        for pid, j in self.p.joueurs.items():
            nb = sum(self.justes(pid).values())
            gain = pts * nb
            if nb == self.n:
                gain += bonus + int(self.cfg["bonus_vitesse"] * self.fracs.get(pid, 0))
            j.gain += gain
            j.score += gain
            j.trouve = nb == self.n
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def duree_revelation(self, base):
        return base + 3

    def statut(self, pid):
        k = len(self.reponses.get(pid, {}))
        return {"t": "a tout parié", "c": "ok"} if k == self.n else {"t": f"{k}/{self.n}", "c": "go"} if k else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if len(self.reponses.get(p, {})) == self.n)} / {len(J)} ont fait tous leurs paris"

    def vue(self, pid, revele):
        v = {"n": self.n}
        if pid:
            v.update(ma_reponse=self.reponses.get(pid, {}),
                     actif=len(self.reponses.get(pid, {})) < self.n and not revele and not self.p.pause)
        if revele:
            votes = [[[], []] for _ in range(self.n)]
            for q, r in self.reponses.items():
                j = self.p.joueurs.get(q)
                if j:
                    for k, i in r.items():
                        votes[int(k)][i].append(dict(j.public(), ok=i == self.m["duels"][int(k)]["bonne"]))
            v.update(duels=self.m["duels"], votes=votes,
                     resultats=sorted([dict(self.p.joueurs[q].public(), justes=sum(self.justes(q).values()),
                                            gain=self.gains.get(q, 0)) for q in self.p.joueurs], key=lambda x: -x["gain"]))
            if pid:
                v["mes_justes"] = self.justes(pid)
        return v
