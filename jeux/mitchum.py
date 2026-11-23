"""The Mitchum Brothers' Contract (Le contrat) : les frères Mitchum ont des contrats sur la tête de quelqu'un… et ils
passent de main en main, comme des patates chaudes, toujours dans le même sens. Au départ, chaque joueur tient un
contrat. Celui qui tient un contrat reçoit sur son téléphone une question éclair à six
choix (réalisateur, acteur, année, gros plan d'affiche…) : bonne réponse, il refile le contrat au suivant (qui peut
alors en tenir deux) ; mauvaise réponse, une autre question après une courte pénalité. La minuterie (30 à 45 s) est
visible par tous ; quand elle éclate, chaque contrat qu'on tient coûte des points.
"""
import random

from .questions import preparer, questions


def construire(api, cfg, pool, deja):
    fs = preparer(api, pool, 24)
    if len(fs) < 8:
        raise RuntimeError("Le contrat : pas assez de films dans les listes choisies.")
    images = []
    qs = questions(api, fs, 60, images, avec_affiches=bool(cfg.get("mitchum_affiches", True)))
    if len(qs) < 12:
        raise RuntimeError("Le contrat : pas assez de questions possibles avec les films des listes.")
    duree = random.uniform(float(cfg["mitchum_min"]), float(cfg["mitchum_max"]))
    return dict(jeu="mitchum", vue="contrat", duree=round(duree, 1), reponse="contrat",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[],
                bonne="", solution="Les contrats ont éclaté", detail="", films=[], questions=qs)


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.ordre = list(partie.joueurs)
        random.shuffle(self.ordre)
        n = len(self.ordre)                                 # un contrat par joueur au départ
        self.contrats = {p: 0 for p in self.ordre}           # pid -> contrats tenus
        for p in self.ordre[:n]:
            self.contrats[p] = 1
        self.q = {}                                         # pid -> question en cours (indice dans m["questions"])
        self.bloque = {}                                    # pid -> fin de la pénalité (temps de la manche)
        self.suivante = 0
        self.passes = {}                                    # pid -> contrats refilés
        self.journal = []                                   # [(de, à)]
        self.pertes = {}
        for p in self.ordre:
            if self.contrats[p]:
                self._nouvelle(p)

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le contrat se joue à 2 joueurs minimum."
        return ""

    def _nouvelle(self, pid):
        qs = self.m["questions"]
        self.q[pid] = self.suivante % len(qs)
        self.suivante += 1

    def _vivants(self):
        return [p for p in self.ordre if p in self.p.joueurs]

    def _suivant(self, pid):
        v = self._vivants()
        return v[(v.index(pid) + 1) % len(v)] if pid in v else None

    def action(self, pid, d, frac, info=None):
        if not self.contrats.get(pid):
            return {"ok": False, "msg": "Vous n'avez pas de contrat"}
        if self.p.ecoule < self.bloque.get(pid, 0):
            return {"ok": False, "msg": "Pénalité : attendez…"}
        i = d.get("choix")
        if type(i) is not int or pid not in self.q:
            return {"ok": False, "msg": "Touchez une réponse"}
        q = self.m["questions"][self.q[pid]]
        if i != q["bonne"]:
            self.bloque[pid] = self.p.ecoule + float(self.cfg.get("mitchum_penalite", 2))
            self._nouvelle(pid)
            return {"ok": True, "correct": False, "msg": f"Raté ! C'était : {q['choix'][q['bonne']]}"}
        s = self._suivant(pid)
        self.contrats[pid] -= 1
        self.contrats[s] = self.contrats.get(s, 0) + 1
        self.passes[pid] = self.passes.get(pid, 0) + 1
        self.journal = (self.journal + [(pid, s)])[-6:]
        if self.contrats[pid]:
            self._nouvelle(pid)
        else:
            self.q.pop(pid, None)
        if s not in self.q:
            self._nouvelle(s)
        nom = self.p.joueurs[s].nom if s in self.p.joueurs else "?"
        return {"ok": True, "correct": True, "msg": f"Contrat refilé à {nom} !"}

    def fini(self):
        return False

    def clore(self):
        J = self.p.joueurs
        for pid, j in J.items():
            gain = int(self.cfg["mitchum_passe"]) * self.passes.get(pid, 0)
            n = self.contrats.get(pid, 0)
            if n:
                une = max(int(self.cfg["mitchum_mini"]), int(j.score * float(self.cfg["mitchum_pct"]) / 100))
                perte = min(une * n, j.score + gain)
                self.pertes[pid] = perte
                gain -= perte
            j.gain += gain
            j.score += gain
            j.trouve = not n
            j.serie = j.serie + 1 if j.trouve else 0

    def duree_revelation(self, base):
        return base + 2

    def statut(self, pid):
        n = self.contrats.get(pid, 0)
        return {"t": f"{n} contrat{'s' if n > 1 else ''}", "c": "bad"} if n else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        tient = [f"{J[p].nom}{' ×' + str(self.contrats[p]) if self.contrats[p] > 1 else ''}" for p in self._vivants()
                 if self.contrats.get(p)]
        return "Contrats : " + ", ".join(tient)

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"joueurs": [dict(J[p].public(), contrats=self.contrats.get(p, 0), passes=self.passes.get(p, 0),
                              perte=self.pertes.get(p, 0)) for p in self.ordre if p in J],
             "duree": self.m["duree"], "ecoule": round(self.p.ecoule, 1),
             "journal": [{"de": J[a].nom if a in J else "?", "a": J[b].nom if b in J else "?"} for a, b in self.journal]}
        if pid:
            n = self.contrats.get(pid, 0)
            v.update(mes_contrats=n if not revele else 0, actif=not revele and not self.p.pause)
            if n and not revele and pid in self.q:
                q = self.m["questions"][self.q[pid]]
                v.update(question={"k": self.q[pid], "q": q["q"], "choix": q["choix"], "img": q["img"]},
                         penalite=max(0, round(self.bloque.get(pid, 0) - self.p.ecoule, 1)))
        return v
