"""The Mitchum Brothers' Contract (Le contrat) : les frères Mitchum ont un contrat sur la tête de quelqu'un… et il
passe de main en main, comme une patate chaude, toujours dans le même sens. La minuterie tourne, visible par tous.
Celui qui tient le contrat doit citer un film qui respecte la condition affichée (genre, décennie, « avec A, B ou C »,
réalisateur, pays…) pour s'en débarrasser : le contrat passe alors au joueur suivant, avec une nouvelle condition.
On peut changer de condition, mais il faut alors citer un film de plus (trois au plus). Quand la minuterie éclate,
celui qui tient le contrat perd une grosse part de ses points. Un film ne sert qu'une fois par manche.
"""
import random

from tmdb import cle_film, libelle
from .contraintes import Ctx, connus_communs, entrees_films, generer, index, resoudre, suggerer_films

TYPES = ("genre", "decennie", "periode", "acteur", "realisateur", "compositeur", "langue", "pays", "duree", "note",
         "theme", "titre")
NB_CONDITIONS = 14


def construire(api, cfg, pool, deja):
    x = Ctx(api, cfg, pool, 3, realisateurs_ok=connus_communs(cfg.get("_profils", [])))
    types = [k for k in TYPES if cfg.get("mitchum_" + k, True)] or ["genre", "decennie"]
    conds = []
    for _ in range(NB_CONDITIONS * 2):
        c = generer(x, "mitchum_", exclues={c["txt"] for c in conds}, types=types)
        if c:
            conds.append(c)
        if len(conds) == NB_CONDITIONS:
            break
    if len(conds) < 4:
        raise RuntimeError("Le contrat : pas assez de conditions possibles avec les films des listes.")
    duree = random.uniform(float(cfg["mitchum_min"]), float(cfg["mitchum_max"]))
    return dict(jeu="mitchum", vue="contrat", duree=round(duree, 1), reponse="contrat", etapes=[(0.0, {})],
                images=[], revelation=None, cles=[], bonne="", solution="Le contrat a éclaté", detail="", films=[],
                suggestions=True, conditions=conds, api=api, films_pool=pool)


class Moteur:
    suggestions = True
    films_tmdb = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.ordre = list(partie.joueurs)
        random.shuffle(self.ordre)
        self.h = 0                                  # le joueur qui tient le contrat (indice dans ordre)
        self.ci = 0                                 # la condition en cours
        self.besoin, self.donnes = 1, []            # films à citer, films déjà cités pour cette condition
        self.utilises = set()                       # films déjà cités pendant la manche
        self.journal = []                           # [(nom, film)] les derniers films cités
        self.passes = {}                            # pid -> nombre de fois où il s'en est débarrassé
        self.victime, self.perte = None, 0
        toutes = list(m["conditions"])
        self.idx = index(list(m.get("films_pool", [])) + [f for c in toutes for f in c["valides"]()])
        self.entrees = entrees_films([f for f, _ in self.idx])

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le contrat se joue à 2 joueurs minimum."
        return ""

    def _porteur(self):
        vivants = [p for p in self.ordre if p in self.p.joueurs]
        if not vivants:
            return None
        return vivants[self.h % len(vivants)]

    def _condition(self):
        cs = self.m["conditions"]
        return cs[self.ci % len(cs)]

    def resoudre(self, d):
        return resoudre(self.m["api"], d.get("texte"), self.idx, bool(self._condition().get("fiche")))

    def suggerer(self, q):
        return suggerer_films(self.m["api"], q, self.entrees)

    def action(self, pid, d, frac, info=None):
        if pid != self._porteur():
            return {"ok": False, "msg": "Vous n'avez pas le contrat"}
        if d.get("type") == "changer":
            if self.besoin >= 3:
                return {"ok": False, "msg": "Plus de changement possible : trois films à citer"}
            self.ci += 1
            self.besoin += 1
            self.donnes = []
            return {"ok": True, "msg": f"Nouvelle condition : {self.besoin} films à citer"}
        texte = str(d.get("texte") or "").strip()
        if not texte:
            return {"ok": False, "msg": "Tapez un film"}
        f = (info or {}).get("film")
        if not f:
            return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
        c = self._condition()
        if c.get("fiche") and not (info or {}).get("fiche"):
            info = resoudre(self.m["api"], libelle(f), self.idx, True) or {}
        if not c["test"](f, (info or {}).get("fiche")):
            return {"ok": False, "msg": f"Raté : {libelle(f)} ne colle pas"}
        k = cle_film(f)
        if k in self.utilises:
            return {"ok": False, "msg": f"{libelle(f)} a déjà servi"}
        self.utilises.add(k)
        self.donnes.append(libelle(f))
        nom = self.p.joueurs[pid].nom
        self.journal = (self.journal + [(nom, libelle(f))])[-6:]
        if len(self.donnes) < self.besoin:
            return {"ok": True, "correct": True, "msg": f"✓ {libelle(f)} — encore {self.besoin - len(self.donnes)}"}
        self.passes[pid] = self.passes.get(pid, 0) + 1
        self.h += 1
        self.ci += 1
        self.besoin, self.donnes = 1, []
        suivant = self.p.joueurs.get(self._porteur())
        return {"ok": True, "correct": True, "msg": f"✓ {libelle(f)} — le contrat passe à {suivant.nom if suivant else '?'}"}

    def fini(self):
        return False

    def clore(self):
        J = self.p.joueurs
        self.victime = self._porteur()
        for pid, j in J.items():
            gain = int(self.cfg["mitchum_passe"]) * self.passes.get(pid, 0)
            if pid == self.victime:
                perte = max(int(self.cfg["mitchum_mini"]), int(j.score * float(self.cfg["mitchum_pct"]) / 100))
                self.perte = min(perte, j.score + gain)
                gain -= self.perte
            j.gain += gain
            j.score += gain
            j.trouve = pid != self.victime
            j.serie = j.serie + 1 if j.trouve else 0

    def duree_revelation(self, base):
        return base + 2

    def statut(self, pid):
        if pid == self._porteur():
            return {"t": "a le contrat", "c": "bad"}
        return {"t": "", "c": ""}

    def avancement(self):
        j = self.p.joueurs.get(self._porteur())
        return f"{j.nom} tient le contrat" if j else ""

    def vue(self, pid, revele):
        J = self.p.joueurs
        porteur = self._porteur()
        v = {"joueurs": [dict(J[p].public(), porteur=p == porteur, passes=self.passes.get(p, 0)) for p in self.ordre if p in J],
             "condition": self._condition()["txt"], "besoin": self.besoin, "donnes": list(self.donnes),
             "journal": [{"nom": n, "film": f} for n, f in self.journal], "peut_changer": self.besoin < 3}
        if pid:
            v.update(a_moi=pid == porteur and not revele, actif=not revele and not self.p.pause)
        if revele:
            v.update(victime=J[self.victime].public() if self.victime in J else None, perte=self.perte)
        return v
