"""Les enveloppes : une suite de « Et le prix est attribué à… », pour La cérémonie (Dick Tremayne) et Le Hibou d'or
(le maire Dwayne Milford). Chaque enveloppe a un temps de réponse (roulement de tambour) puis une révélation.

Une enveloppe : {"titre", "sous" (ex. l'année), "items": [{"img", "txt"}], "bonne": indice dans items,
                 "infos": [texte affiché sous chaque item à la révélation],
                 "cacher_sous": True si l'écran ne doit pas afficher « sous » (les experts doivent le trouver),
                 "cacher_items": True si l'écran ne montre pas les nommés pendant la question,
                 "experts": {"items", "bonne", "question", "annees": [6 années], "bonne_annee"} (facultatif)}
Les joueurs « experts » (réglage) reçoivent la variante experts sur leur téléphone quand elle existe ; les autres
ont au plus quatre choix (le lauréat et des nommés).
"""
import random

from texte import cle

SIMPLE_MAX = 4


def simplifier(env):
    """Les choix des joueurs non experts : le lauréat et trois nommés au plus."""
    items, b = env["items"], env["bonne"]
    autres = [i for i in range(len(items)) if i != b]
    random.shuffle(autres)
    garde = sorted([b] + autres[:SIMPLE_MAX - 1])
    env["simple"] = {"items": [items[i] for i in garde], "bonne": garde.index(b), "idx": garde}
    return env


def experts_de(cfg):
    return {cle(x) for x in str(cfg.get("dick_experts") or "").replace(";", ",").split(",") if cle(x)}


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.D, self.R = float(m["dur_question"]), float(m["dur_revelation"])
        self.rep = {}                                       # (pid, k) -> {"i", "t", "ok", "annee"}
        exp = experts_de(cfg) if m.get("avec_experts") else set()
        self.experts = {pid for pid, j in partie.joueurs.items() if cle(j.profil or "") in exp or cle(j.nom) in exp}
        self.gains = {}

    def ok(self):
        return ""

    def _k(self):
        """(enveloppe en cours, temps écoulé dans l'enveloppe)."""
        t = self.p.ecoule - float(self.m.get("t0", 0))
        if t < 0:
            return -1, 0.0
        k = int(t // (self.D + self.R))
        return min(k, len(self.m["enveloppes"]) - 1), t - k * (self.D + self.R)

    def _variante(self, pid, env):
        if pid in self.experts and env.get("experts"):
            return "experts", env["experts"]
        return "simple", env.get("simple") or {"items": env["items"], "bonne": env["bonne"]}

    def action(self, pid, d, frac, info=None):
        k, t = self._k()
        if k < 0:
            return {"ok": False, "msg": "La cérémonie commence…"}
        if d.get("env") != k or t >= self.D:
            return {"ok": False, "msg": "Trop tard pour cette enveloppe"}
        env = self.m["enveloppes"][k]
        nom, v = self._variante(pid, env)
        r = self.rep.get((pid, k))
        if "annee" in d:                                   # experts : la question bonus de l'année
            if not r or r.get("annee") is not None or not v.get("annees"):
                return {"ok": False, "msg": ""}
            a = d.get("annee")
            if type(a) is not int or not 0 <= a < len(v["annees"]):
                return {"ok": False, "msg": ""}
            r["annee"] = a
            ok = a == v["bonne_annee"]
            return {"ok": True, "correct": ok, "msg": "Bonne année !" if ok else "Ce n'était pas cette année-là"}
        if r:
            return {"ok": False, "msg": "Déjà répondu"}
        i = d.get("i")
        if type(i) is not int or not 0 <= i < len(v["items"]):
            return {"ok": False, "msg": "Touchez un film"}
        self.rep[(pid, k)] = {"i": i, "t": t, "ok": i == v["bonne"], "annee": None}
        return {"ok": True, "msg": "Enveloppe scellée…"}

    def fini(self):
        return False

    def _points(self, pid, k):
        r = self.rep.get((pid, k))
        if not r:
            return 0
        env = self.m["enveloppes"][k]
        _, v = self._variante(pid, env)
        pts = 0
        if r["ok"]:
            pts += int(int(self.m["pts"]) * (0.5 + 0.5 * max(0.0, 1 - r["t"] / self.D)))
        if r.get("annee") is not None and v.get("annees") and r["annee"] == v["bonne_annee"]:
            pts += int(self.m.get("bonus", 0))
        return pts

    def clore(self):
        for pid, j in self.p.joueurs.items():
            gain = sum(self._points(pid, k) for k in range(len(self.m["enveloppes"])))
            self.gains[pid] = gain
            j.gain += gain
            j.score += gain
            j.trouve = gain > 0
            j.serie = j.serie + 1 if j.trouve else 0

    def statut(self, pid):
        n = sum(1 for k in range(len(self.m["enveloppes"])) if (self.rep.get((pid, k)) or {}).get("ok")
                and k < self._k()[0] + (self._k()[1] >= self.D))
        return {"t": f"{n} ✓", "c": "ok"} if n else {"t": "", "c": ""}

    def avancement(self):
        k, t = self._k()
        if k < 0:
            return ""
        J = self.p.joueurs
        n = sum(1 for p in J if (p, k) in self.rep)
        return f"Enveloppe {k + 1}/{len(self.m['enveloppes'])} · {n}/{len(J)} ont répondu"

    def vue(self, pid, revele):
        J = self.p.joueurs
        k, t = self._k()
        envs = self.m["enveloppes"]
        devoile = revele or (k >= 0 and t >= self.D)
        v = {"n": len(envs), "k": k, "question": k >= 0 and t < self.D and not revele,
             "reste": round(max(0.0, self.D - t), 1) if k >= 0 else 0, "dur": self.D, "hote_nom": self.m.get("hote_nom", "")}
        if k >= 0:
            env = envs[k]
            v["env"] = {"titre": env["titre"], "sous": "" if env.get("cacher_sous") and not devoile else env.get("sous", ""),
                        "items": [] if env.get("cacher_items") and not devoile else env["items"],
                        "bonne": env["bonne"] if devoile else None, "infos": env.get("infos") if devoile else None,
                        "repondu": [J[p].public() for p in J if (p, k) in self.rep]}
            if devoile:
                v["env"]["justes"] = [J[p].public() for p in J if (self.rep.get((p, k)) or {}).get("ok")]
        if pid and k >= 0:
            env = envs[k]
            nom, var = self._variante(pid, env)
            r = self.rep.get((pid, k))
            q = {"mode": nom, "items": var["items"], "question": var.get("question") or env.get("question", ""),
                 "sous": "" if nom == "experts" and env.get("cacher_sous") else env.get("sous", "")}
            if r and var.get("annees") and r.get("annee") is None and not devoile:
                q["annees"] = var["annees"]
            v.update(ma_q=q, mon_choix=r["i"] if r else None, mon_annee=r.get("annee") if r else None,
                     ma_bonne=var["bonne"] if devoile else None, expert=pid in self.experts,
                     actif=not devoile and not self.p.pause)
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0)) for p in J], key=lambda x: -x["gain"])
        return v
