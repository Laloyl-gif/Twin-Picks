"""Ben's Ghostwood Deal (Le budget et le box-office) : Ben Horne ne parle que d'argent. Son registre est ouvert sur
deux pages : à gauche, ce que le film a coûté (budget) ; à droite, ce qu'il a rapporté dans le monde (box-office).
Sur chaque page, plusieurs montants dont un seul est juste ; chaque joueur coche une ligne par page (une seule fois).

Points : les deux justes = tous les points (plus un bonus de rapidité) ; un seul juste = la moitié.
Indices (réglables) : genre et année dès le début ; à 55 % deux montants faux s'effacent sur chaque page.
Seuls les films dont TMDB connaît le budget ET les recettes sont tirés.
"""
import random

from PIL import ImageOps

from tmdb import cle_film, details_film, fiche
from visuels import en_jpeg
from .commun import affiche, chronologie, tirer

PAGES = ("budget", "recettes")


def montant(x):
    """312 M$, 1,24 Md$, 8,5 M$."""
    if x >= 1e9:
        return f"{x / 1e9:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " Md$"
    if x >= 1e7:
        return f"{round(x / 1e6):.0f} M$"
    return f"{x / 1e6:.1f}".replace(".", ",") + " M$"


def propositions(vrai, n):
    """n montants : le vrai à une place au hasard, les autres en progression géométrique (×1,8 à ×2,3 par pas)."""
    for _ in range(50):
        place = random.randrange(n)
        pas = random.uniform(1.8, 2.3)
        vals = [vrai * pas ** (i - place) * (1 if i == place else random.uniform(0.9, 1.1)) for i in range(n)]
        if vals[0] < 1e5:
            continue
        txts = [montant(v) for v in vals]
        if len(set(txts)) == n:
            return txts, place
    return [montant(vrai * 2 ** (i - 2)) for i in range(n)], 2


def construire(api, cfg, pool, deja):
    duree, n = float(cfg["dur_ben"]), max(3, min(6, int(cfg.get("ben_choix", 4))))
    fi = None
    for _ in range(30):
        film = tirer(pool, deja, lambda f: not f.get("tv") and f.get("poster_path"))
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        if (fi.get("recettes") or 0) >= 1e6 and (fi.get("budget") or 0) >= 1e5:
            break
    else:
        raise RuntimeError("Le budget et le box-office : aucun film des listes n'a un budget et des recettes connus sur TMDB.")
    d = details_film(api, film)
    vrais = {"budget": fi["budget"], "recettes": fi["recettes"]}
    txts, bonnes = {}, {}
    for p in PAGES:
        txts[p], bonnes[p] = propositions(vrais[p], n)
    image = en_jpeg(ImageOps.contain(affiche(api, film, "w500"), (400, 600)), 600)
    etat = {"film": {"img": 0, "txt": film["title"],
                     "sous": " · ".join(x for x in (", ".join(d["genres"][:2]), d["annee"]) if x)},
            "budget": [{"txt": t} for t in txts["budget"]], "recettes": [{"txt": t} for t in txts["recettes"]],
            "indices": []}
    evts = []
    if cfg.get("ben_indices", True):
        def barrer():
            for p in PAGES:
                fausses = [i for i in range(n) if i != bonnes[p]]
                barrees = set(random.sample(fausses, min(2, len(fausses) - 1)))
                etat[p] = [dict(it, barre=True) if i in barrees else it for i, it in enumerate(etat[p])]
        evts.append((duree * 0.55, barrer))
    etapes = chronologie(evts, lambda: {**etat, "budget": [dict(i) for i in etat["budget"]],
                                        "recettes": [dict(i) for i in etat["recettes"]], "indices": list(etat["indices"])})
    rapport = fi["recettes"] / fi["budget"]
    detail = (f"{rapport:.1f} fois sa mise".replace(".", ",") if rapport >= 1
              else f"il n'a rapporté que {round(100 * rapport)} % de sa mise")
    infos = {p: ["juste" if i == bonnes[p] else ("trop haut" if i > bonnes[p] else "trop bas") for i in range(n)]
             for p in PAGES}
    return dict(jeu="ben", vue="ben", duree=duree, reponse="double", etapes=etapes, revelation=None, images=[image],
                cles=[], bonne="", bonnes=bonnes, infos=infos,
                solution=f"Budget {txts['budget'][bonnes['budget']]} · box-office {txts['recettes'][bonnes['recettes']]}",
                detail=f"{film['title']} : {detail}", films=[cle_film(film)])


class Moteur:
    """Une ligne cochée par page et par joueur ; on ne revient pas sur une ligne cochée."""
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.n = len(m["infos"]["budget"])
        self.reponses, self.fracs, self.gains = {}, {}, {}

    def ok(self):
        return ""

    def action(self, pid, d, frac, info=None):
        page, i = d.get("page"), d.get("i")
        if page not in PAGES or type(i) is not int or not 0 <= i < self.n:
            return {"ok": False, "msg": "Cochez une ligne du registre"}
        r = self.reponses.setdefault(pid, {})
        if page in r:
            return {"ok": False, "msg": "Cette page est déjà cochée"}
        etat = self.p.manche["etapes"][max(0, self.p.etape)][1]
        if etat[page][i].get("barre"):
            return {"ok": False, "msg": "Ce montant a été rayé"}
        r[page] = i
        self.fracs[pid] = frac
        if len(r) == 2:
            self.p.joueurs[pid].essais = 1
            return {"ok": True, "msg": "Registre signé !"}
        autre = "le box-office" if page == "budget" else "le budget"
        return {"ok": True, "msg": f"Noté. Et {autre} ?"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(len(self.reponses.get(p, {})) == 2 for p in J)

    def justes(self, pid):
        r = self.reponses.get(pid, {})
        return {p: r.get(p) == self.m["bonnes"][p] for p in PAGES if p in r}

    def clore(self):
        pts = self.cfg.get("ben_pts", 1000)
        for pid, j in self.p.joueurs.items():
            nb = sum(self.justes(pid).values())
            gain = pts if nb == 2 else pts // 2 if nb == 1 else 0
            if nb == 2:
                gain += int(self.cfg["bonus_vitesse"] * self.fracs.get(pid, 0))
            j.gain += gain
            j.score += gain
            j.trouve = nb == 2
            j.serie = j.serie + 1 if nb == 2 else 0
            self.gains[pid] = gain

    def duree_revelation(self, base):
        return base + 3

    def statut(self, pid):
        k = len(self.reponses.get(pid, {}))
        return {"t": "a signé", "c": "ok"} if k == 2 else {"t": "1 page sur 2", "c": "go"} if k else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if len(self.reponses.get(p, {})) == 2)} / {len(J)} ont signé le registre"

    def vue(self, pid, revele):
        v = {"n": self.n}
        if pid:
            v.update(ma_reponse=self.reponses.get(pid, {}), actif=len(self.reponses.get(pid, {})) < 2 and not revele
                     and not self.p.pause)
        if revele:
            votes = {p: {} for p in PAGES}
            for q, r in self.reponses.items():
                j = self.p.joueurs.get(q)
                if not j:
                    continue
                for page, i in r.items():
                    votes[page].setdefault(str(i), []).append(dict(j.public(), ok=i == self.m["bonnes"][page]))
            v.update(bonnes=self.m["bonnes"], infos=self.m["infos"], votes=votes,
                     resultats=sorted([dict(self.p.joueurs[q].public(), justes=sum(self.justes(q).values()),
                                            gain=self.gains.get(q, 0)) for q in self.p.joueurs], key=lambda x: -x["gain"]))
            if pid:
                v["mes_justes"] = self.justes(pid)
        return v
