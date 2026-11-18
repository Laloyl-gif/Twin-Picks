"""Moteur « plusieurs films à trouver » (Carl : les deux films ; Dougie : le jackpot à cinq films).
La manche fournit films_cles (les réponses acceptées pour chaque film) et films_titres. Chacun tape des titres ;
chaque film trouvé rapporte des points (plus tôt = plus), tous trouvés : un bonus."""
from texte import correspond, proche


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.n = len(m["films_cles"])
        self.trouves, self.essais, self.gains = {}, {}, {}
        jeu = m.get("jeu", "carl")
        self.pts = int(cfg.get(f"{jeu}_pts", 600 if self.n <= 2 else 300))
        self.tous = int(cfg.get(f"{jeu}_deux" if jeu == "carl" else f"{jeu}_tous", 300))

    def ok(self):
        return ""

    def _max(self):
        return (self.n + 1) * int(self.cfg.get("max_essais", 3))

    def action(self, pid, d, frac, info=None):
        texte = str(d.get("texte", "")).strip()
        if not texte:
            return {"ok": False, "msg": "Tapez un titre"}
        tr = self.trouves.setdefault(pid, {})
        if len(tr) == self.n:
            return {"ok": False, "msg": "Tous les films sont trouvés !"}
        if self.essais.get(pid, 0) >= self._max():
            return {"ok": False, "msg": "Plus d'essais"}
        for k, cles in enumerate(self.m["films_cles"]):
            if any(correspond(texte, c) for c in cles):
                if k in tr:
                    return {"ok": False, "msg": "Celui-là est déjà trouvé : un autre !"}
                tr[k] = frac
                self.p.joueurs[pid].essais = 1
                reste = self.n - len(tr)
                fin = "Tous trouvés, bravo !" if not reste else f"Encore {reste}."
                return {"ok": True, "correct": not reste, "msg": f"{self.m['films_titres'][k]} : trouvé. {fin}"}
        self.essais[pid] = self.essais.get(pid, 0) + 1
        reste = self._max() - self.essais[pid]
        presque = any(proche(texte, c) for cles in self.m["films_cles"] for c in cles)
        return {"ok": False, "msg": ("Presque ! Vérifiez l'orthographe. " if presque else "Raté. ") +
                (f"{reste} essai(s) restant(s)" if reste else "Plus d'essais.")}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(len(self.trouves.get(p, {})) == self.n or self.essais.get(p, 0) >= self._max() for p in J)

    def clore(self):
        for pid, j in self.p.joueurs.items():
            tr = self.trouves.get(pid, {})
            gain = sum(self.pts + int(self.cfg["bonus_vitesse"] * f / max(1, self.n - 1)) for f in tr.values())
            if len(tr) == self.n:
                gain += self.tous
            j.gain += gain
            j.score += gain
            j.trouve = len(tr) == self.n
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        n = len(self.trouves.get(pid, {}))
        return {"t": f"{n}/{self.n}", "c": "ok" if n == self.n else ""} if n else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if len(self.trouves.get(p, {})) == self.n)} / {len(J)} ont trouvé les {self.n} films"

    def vue(self, pid, revele):
        v = {"titres": self.m["films_titres"] if revele else [], "n": self.n,
             "trouves_k": sorted({k for tr in self.trouves.values() for k in tr})}
        if pid:
            tr = self.trouves.get(pid, {})
            v.update(mes_films=[self.m["films_titres"][k] for k in sorted(tr)], mes_k=sorted(tr),
                     actif=len(tr) < self.n and self.essais.get(pid, 0) < self._max() and not revele and not self.p.pause)
        if revele:
            v["resultats"] = sorted([dict(j.public(), n=len(self.trouves.get(p, {})), gain=self.gains.get(p, 0))
                                     for p, j in self.p.joueurs.items()], key=lambda x: -x["gain"])
        return v
