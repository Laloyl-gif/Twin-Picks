"""Lana Budding's Lies (Les mensonges de Lana), façon Fibbage : Lana Budding embobine tout Twin Peaks. Une vraie
information avec un trou s'affiche (« Dans Pulp Fiction, Samuel L. Jackson joue ___ », un slogan à compléter, le
titre original d'un film…). Chacun invente en secret une fausse réponse crédible. Puis toutes les réponses, fausses
et vraie, s'affichent mélangées : chacun vote pour celle qu'il croit vraie. Points pour qui trouve la vraie, et pour
chaque joueur piégé par son mensonge. Plusieurs questions par manche.
"""
import random
import re

from texte import cle, est_latin
from tmdb import cle_film, details_film, fiche

MOTS_VIDES = {"dans", "avec", "pour", "sans", "plus", "tout", "tous", "elle", "nous", "vous", "leur", "cette", "comme",
              "mais", "quand", "the", "and", "with", "your", "from", "that", "this", "will", "have", "never", "every"}


def _q_role(api, f, fi):
    acteurs = [a for a in fi.get("acteurs", [])[:4] if a.get("role") and a.get("nom")
               and not re.search(r"himself|herself|lui-même|elle-même|voice|voix|narrat", a["role"], re.I)]
    if not acteurs:
        return None
    a = random.choice(acteurs)
    role = a["role"].split("/")[0].strip()
    if len(role) < 3 or len(role) > 40:
        return None
    leurres = [b["role"].split("/")[0].strip() for b in fi.get("acteurs", [])[4:12] if b.get("role")]
    return {"q": f"Dans « {fi['titre']} », {a['nom']} joue le rôle de ___", "vraie": role, "leurres": leurres}


def _q_slogan(api, f, d):
    s = (d.get("slogan") or "").strip()
    if not s or len(s) > 110:
        return None
    mots = [m for m in re.findall(r"[^\W\d_]{4,}", s) if m.lower() not in MOTS_VIDES]
    if not mots:
        return None
    m = max(mots, key=len)
    trou = re.sub(r"\b" + re.escape(m) + r"\b", "___", s, count=1)
    return {"q": f"Le slogan de « {f['title']} » : « {trou} »", "vraie": m.lower() if s.find(m) > 0 else m, "leurres": []}


def _q_original(api, f, fi):
    o = (fi.get("original") or "").strip()
    t = fi.get("titre") or f["title"]
    if not o or cle(o) == cle(t) or not est_latin(o) or len(o) > 45:
        return None
    return {"q": f"Le titre original de « {t} » ({fi.get('annee') or '?'}) est ___", "vraie": o, "leurres": []}


def _q_mot_cle(api, f, fi):
    """Ce que TMDB dit du film : un de ses mots-clés (traduit si possible)."""
    return None


GENERATEURS = (_q_role, _q_role, _q_slogan, _q_original)


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)
    n = max(1, int(cfg.get("lana_n", 3)))
    qs, utilises = [], []
    for f in films[:40]:
        if len(qs) >= n:
            break
        try:
            fi = fiche(api, f)
            d = details_film(api, f)
        except Exception:  # noqa: BLE001
            continue
        gens = list(GENERATEURS)
        random.shuffle(gens)
        for g in gens:
            q = g(api, f, d if g is _q_slogan else fi)
            if q and q["vraie"]:
                qs.append(q)
                utilises.append(cle_film(f))
                break
    if not qs:
        raise RuntimeError("Les mensonges de Lana : pas assez d'informations sur les films des listes.")
    for k in utilises:
        deja.add(k)
    E, V, R = float(cfg.get("lana_ecrire", 40)), float(cfg.get("lana_voter", 25)), 8.0
    return dict(jeu="lana", vue="mensonges", duree=round(len(qs) * (E + V + R) + 3, 1), reponse="mensonges",
                etapes=[(0.0, {})], images=[], revelation=None, cles=[], bonne="", solution="Les mensonges de Lana",
                detail="", films=utilises, questions=qs, dur_ecrire=E, dur_voter=V, dur_rev=R,
                signature=tuple(q["q"] for q in qs))


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.k, self.etape, self.debut = 0, "ecrire", 1.0
        self.mensonges = {}                      # pid -> texte (question en cours)
        self.votes = {}                          # pid -> indice de l'option
        self.options = []                        # [{"txt", "auteurs": [pid] | None (vraie) | "leurre"}]
        self.gains = {}
        self.historique = []

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Les mensonges de Lana se jouent à 2 joueurs minimum."
        return ""

    def _q(self):
        return self.m["questions"][min(self.k, len(self.m["questions"]) - 1)]

    def _dur(self):
        return {"ecrire": self.m["dur_ecrire"], "voter": self.m["dur_voter"], "rev": self.m["dur_rev"]}[self.etape]

    def _gagner(self, pid, n):
        self.gains[pid] = self.gains.get(pid, 0) + n

    def _ouvrir_vote(self):
        q = self._q()
        opts = {cle(q["vraie"]): {"txt": q["vraie"], "auteurs": None}}
        for pid, t in self.mensonges.items():
            k = cle(t)
            if k in opts:
                if opts[k]["auteurs"] is not None:
                    opts[k]["auteurs"].append(pid)
                continue
            opts[k] = {"txt": t, "auteurs": [pid]}
        leurres = [x for x in q.get("leurres", []) if cle(x) not in opts]
        random.shuffle(leurres)
        while len(opts) < 4 and leurres:                  # au moins quatre réponses : des leurres de Lana
            x = leurres.pop()
            opts[cle(x)] = {"txt": x, "auteurs": "leurre"}
        self.options = list(opts.values())
        random.shuffle(self.options)
        self.votes = {}
        self.etape, self.debut = "voter", self.p.ecoule

    def _reveler(self):
        u_vrai, u_piege = int(self.cfg.get("lana_vrai", 500)), int(self.cfg.get("lana_piege", 300))
        for pid, i in self.votes.items():
            o = self.options[i]
            if o["auteurs"] is None:
                self._gagner(pid, u_vrai)
            elif isinstance(o["auteurs"], list):
                for a in o["auteurs"]:
                    if a != pid:
                        self._gagner(a, u_piege)
        self.historique.append(self._q()["q"])
        self.etape, self.debut = "rev", self.p.ecoule

    def _maj(self):
        t = self.p.ecoule - self.debut
        J = self.p.joueurs
        if self.etape == "ecrire" and (t >= self._dur() or (J and all(p in self.mensonges for p in J))):
            self._ouvrir_vote()
        elif self.etape == "voter":
            votants = [p for p in J if self._peut_voter(p)]
            if t >= self._dur() or (votants and all(p in self.votes for p in votants)):
                self._reveler()
        elif self.etape == "rev" and t >= self._dur() and self.k < len(self.m["questions"]) - 1:
            self.k += 1
            self.mensonges, self.votes, self.options = {}, {}, []
            self.etape, self.debut = "ecrire", self.p.ecoule

    def _peut_voter(self, pid):
        return any(o["auteurs"] is None or o["auteurs"] == "leurre" or pid not in o["auteurs"] for o in self.options)

    def action(self, pid, d, frac, info=None):
        self._maj()
        if self.etape == "ecrire":
            t = " ".join(str(d.get("texte") or "").split())[:60]
            if not t:
                return {"ok": False, "msg": "Inventez une réponse"}
            if pid in self.mensonges:
                return {"ok": False, "msg": "Mensonge déjà envoyé"}
            if cle(t) == cle(self._q()["vraie"]):
                return {"ok": False, "msg": "C'est la vraie réponse ! Inventez autre chose"}
            self.mensonges[pid] = t
            return {"ok": True, "msg": "Mensonge enregistré"}
        if self.etape == "voter":
            i = d.get("vote")
            if pid in self.votes:
                return {"ok": False, "msg": "Vote déjà envoyé"}
            if type(i) is not int or not 0 <= i < len(self.options):
                return {"ok": False, "msg": "Choisissez une réponse"}
            o = self.options[i]
            if isinstance(o["auteurs"], list) and pid in o["auteurs"]:
                return {"ok": False, "msg": "C'est votre mensonge !"}
            self.votes[pid] = i
            return {"ok": True, "msg": "Vote enregistré"}
        return {"ok": False, "msg": ""}

    def fini(self):
        self._maj()
        return self.etape == "rev" and self.k >= len(self.m["questions"]) - 1 and self.p.ecoule - self.debut >= self._dur()

    def clore(self):
        if self.etape == "voter":
            self._reveler()
        for pid, j in self.p.joueurs.items():
            gain = self.gains.get(pid, 0)
            j.gain += gain
            j.score += gain
            j.trouve = gain > 0
            j.serie = j.serie + 1 if j.trouve else 0

    def duree_revelation(self, base):
        return base

    def statut(self, pid):
        if self.etape == "ecrire":
            return {"t": "a menti" if pid in self.mensonges else "", "c": "ok" if pid in self.mensonges else ""}
        if self.etape == "voter":
            return {"t": "a voté" if pid in self.votes else "", "c": "ok" if pid in self.votes else ""}
        g = self.gains.get(pid, 0)
        return {"t": f"+{g}" if g else "", "c": "ok" if g else ""}

    def avancement(self):
        J = self.p.joueurs
        if self.etape == "ecrire":
            return f"{len(self.mensonges)} / {len(J)} ont inventé leur mensonge"
        if self.etape == "voter":
            return f"{len(self.votes)} / {len(J)} ont voté"
        return ""

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        q = self._q()
        rev = self.etape == "rev" or revele
        v = {"q": q["q"], "k": self.k, "n": len(self.m["questions"]), "etape": "rev" if revele else self.etape,
             "reste": round(max(0.0, self._dur() - (self.p.ecoule - self.debut)), 1)}
        if self.etape in ("voter", "rev") or revele:
            opts = []
            for i, o in enumerate(self.options):
                x = {"txt": o["txt"], "i": i}
                if rev:
                    x.update(vraie=o["auteurs"] is None, leurre=o["auteurs"] == "leurre",
                             auteurs=[J[a].public() for a in o["auteurs"] if a in J] if isinstance(o["auteurs"], list) else [],
                             votants=[J[p].public() for p, k in self.votes.items() if k == i and p in J])
                opts.append(x)
            v["options"] = opts
        if pid:
            mien = self.mensonges.get(pid)
            v.update(mon_mensonge=mien, mon_vote=self.votes.get(pid),
                     interdit=[i for i, o in enumerate(self.options) if isinstance(o["auteurs"], list) and pid in o["auteurs"]],
                     actif=not revele and not self.p.pause and ((self.etape == "ecrire" and mien is None) or
                                                                 (self.etape == "voter" and pid not in self.votes)))
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0)) for p in J], key=lambda x: -x["gain"])
        return v
