"""Mrs. Tremond's Painting (Le tableau), façon Dixit : Mrs. Tremond offre à Laura un tableau dans lequel elle entre en
rêve. Chacun a six affiches en main sur son téléphone. Le conteur (chacun son tour) en choisit une et tape un
indice (un mot ou une phrase, jamais un mot du titre ni le nom d'un acteur). Puis :
- à 3 joueurs et plus (règle de Dixit) : chaque autre joueur pose l'affiche de sa main qui colle le mieux à l'indice,
  pour leurrer ; des affiches du « tableau » complètent jusqu'à six. Toutes s'affichent mélangées et chacun vote
  pour celle du conteur. Si tout le monde ou personne ne trouve : le conteur ne marque rien, les autres 2 unités.
  Sinon le conteur et ceux qui ont trouvé marquent 3 unités. Chaque vote sur votre affiche : 1 unité.
- à 2 joueurs (règle à deux) : on joue ensemble contre le tableau. Les leurres sont les cinq autres affiches de la
  main du conteur (il les a sous les yeux en choisissant son indice). Le devineur a deux essais : trouvé du premier
  coup, 3 unités chacun ; au second, 1 unité chacun.
"""
import random

from PIL import ImageOps

from texte import cle
from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche

MAIN, TABLE = 6, 6


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    random.shuffle(films)
    films = sorted(films, key=lambda f: cle_film(f) in deja)[:60]
    if len(films) < 24:
        raise RuntimeError("Le tableau : pas assez de films dans les listes choisies.")
    images = [en_jpeg(ImageOps.fit(affiche(api, f, "w342"), (200, 300)), 300) for f in films]
    cartes = [{"img": i, "txt": f["title"], "id": f["id"], "tv": False} for i, f in enumerate(films)]
    for f in films[:30]:
        deja.add(cle_film(f))
    return dict(jeu="tremond", vue="tableau", duree=float(cfg.get("dur_tremond", 180)), reponse="tableau",
                etapes=[(0.0, {"cachees": list(range(len(images)))})], images=images, revelation=None, cles=[],
                bonne="", solution="Le tableau de Mrs. Tremond", detail="", films=[cle_film(f) for f in films[:12]],
                cartes=cartes, api=api, signature=tuple(c["id"] for c in cartes[:12]))


class Moteur:
    suggestions = False

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        ids = list(partie.joueurs)
        self.conteur = ids[partie.index % len(ids)] if ids else None
        paquet = list(range(len(m["cartes"])))
        random.shuffle(paquet)
        self.mains = {pid: [paquet.pop() for _ in range(MAIN)] for pid in ids}
        self.paquet = paquet
        self.etape, self.debut = "conteur", 0.0
        self.cible, self.indice = None, ""
        self.poses = {}                          # pid -> carte posée (leurre)
        self.table = []                          # [{"c": carte, "de": pid | None}]
        self.votes = {}                          # pid -> [indices de la table votés, dans l'ordre]
        self.gains = {}

    def ok(self):
        if len(self.p.joueurs) < 2:
            return "Le tableau se joue à 2 joueurs minimum."
        return ""

    def _deux(self):
        return len([p for p in self.mains if p in self.p.joueurs]) == 2

    def _autres(self):
        return [p for p in self.mains if p != self.conteur and p in self.p.joueurs]

    def _dur(self):
        c = self.cfg
        return {"conteur": float(c.get("tremond_conteur", 60)), "poser": float(c.get("tremond_poser", 25)),
                "voter": float(c.get("tremond_voter", 25)), "rev": 9.0}[self.etape]

    def _interdits(self, carte):
        """Les mots qu'un indice ne doit pas contenir : le titre, les acteurs principaux, le réalisateur."""
        c = self.m["cartes"][carte]
        mots = set(cle(c["txt"]).split())
        try:
            fi = fiche(self.m["api"], {"id": c["id"], "tv": False, "title": c["txt"]})
            for x in fi.get("acteurs", [])[:5] + fi.get("realisateurs", [])[:2]:
                mots |= set(cle(x["nom"]).split())
        except Exception:  # noqa: BLE001
            pass
        return {m for m in mots if len(m) > 2}

    def _monter_table(self):
        if self._deux():
            leurres = [x for x in self.mains[self.conteur] if x != self.cible]
            table = [{"c": self.cible, "de": self.conteur}] + [{"c": x, "de": None} for x in leurres]
        else:
            table = [{"c": self.cible, "de": self.conteur}] + [{"c": x, "de": p} for p, x in self.poses.items()]
            while len(table) < TABLE and self.paquet:
                table.append({"c": self.paquet.pop(), "de": None})
        random.shuffle(table)
        self.table = table
        self.etape, self.debut = "voter", self.p.ecoule

    def _maj(self):
        t = self.p.ecoule - self.debut
        if self.etape == "conteur" and t >= self._dur():
            if self.cible is None:                       # le conteur n'a rien choisi : une carte au hasard, sans indice
                self.cible, self.indice = self.mains[self.conteur][0], "(pas d'indice)"
            self._apres_conteur()
        elif self.etape == "poser" and (t >= self._dur() or all(p in self.poses for p in self._autres())):
            for p in self._autres():
                self.poses.setdefault(p, random.choice(self.mains[p]))
            self._monter_table()
        elif self.etape == "voter" and (t >= self._dur() or all(self._vote_fini(p) for p in self._autres())):
            self._compter()

    def _apres_conteur(self):
        if self._deux():
            self._monter_table()
        else:
            self.etape, self.debut = "poser", self.p.ecoule

    def _vote_fini(self, pid):
        v = self.votes.get(pid, [])
        if not self._deux():
            return len(v) >= 1
        return len(v) >= 2 or any(self.table[i]["c"] == self.cible for i in v)

    def _compter(self):
        u = int(self.cfg.get("tremond_unite", 150))
        g = {p: 0 for p in self.mains}
        if self._deux():
            dv = self._autres()[0] if self._autres() else None
            v = self.votes.get(dv, [])
            k = next((n for n, i in enumerate(v) if self.table[i]["c"] == self.cible), None)
            pts = 3 if k == 0 else 1 if k == 1 else 0
            for p in (self.conteur, dv):
                if p:
                    g[p] += pts * u
        else:
            trouve = [p for p in self._autres() if self.votes.get(p) and self.table[self.votes[p][0]]["c"] == self.cible]
            if not trouve or len(trouve) == len(self._autres()):
                for p in self._autres():
                    g[p] += 2 * u
            else:
                g[self.conteur] += 3 * u
                for p in trouve:
                    g[p] += 3 * u
            for p, v in self.votes.items():
                de = self.table[v[0]]["de"]
                if de and de != self.conteur and de != p:
                    g[de] += u
        self.gains = g
        self.etape, self.debut = "rev", self.p.ecoule

    def action(self, pid, d, frac, info=None):
        self._maj()
        if self.etape == "conteur":
            if pid != self.conteur:
                return {"ok": False, "msg": "Le conteur choisit son affiche…"}
            if "carte" in d:
                c = d.get("carte")
                if c not in self.mains[pid]:
                    return {"ok": False, "msg": ""}
                self.cible = c
                return {"ok": True, "msg": "Affiche choisie : tapez votre indice"}
            texte = " ".join(str(d.get("texte") or "").split())[:80]
            if self.cible is None:
                return {"ok": False, "msg": "Touchez d'abord votre affiche"}
            if not texte:
                return {"ok": False, "msg": "Tapez un indice"}
            mauvais = set(cle(texte).split()) & self._interdits(self.cible)
            if mauvais:
                return {"ok": False, "msg": f"Interdit : « {sorted(mauvais)[0]} » (titre ou générique)"}
            self.indice = texte
            self._apres_conteur()
            return {"ok": True, "msg": "Indice envoyé"}
        if self.etape == "poser":
            if pid == self.conteur:
                return {"ok": False, "msg": "Les autres choisissent…"}
            c = d.get("carte")
            if pid in self.poses or c not in self.mains.get(pid, []):
                return {"ok": False, "msg": ""}
            self.poses[pid] = c
            return {"ok": True, "msg": "Affiche posée face cachée"}
        if self.etape == "voter":
            if pid == self.conteur:
                return {"ok": False, "msg": "Les autres votent…"}
            i = d.get("vote")
            v = self.votes.setdefault(pid, [])
            if self._vote_fini(pid) or type(i) is not int or not 0 <= i < len(self.table) or i in v:
                return {"ok": False, "msg": ""}
            if self.table[i]["de"] == pid:
                return {"ok": False, "msg": "C'est votre affiche !"}
            v.append(i)
            if self._deux():
                bon = self.table[i]["c"] == self.cible
                if bon:
                    return {"ok": True, "correct": True, "msg": "Trouvé !"}
                return {"ok": True, "correct": False, "msg": "Raté…" + (" encore un essai" if len(v) < 2 else "")}
            return {"ok": True, "msg": "Vote enregistré"}
        return {"ok": False, "msg": ""}

    def fini(self):
        self._maj()
        return self.etape == "rev" and self.p.ecoule - self.debut >= self._dur()

    def clore(self):
        if self.etape != "rev":
            if self.etape == "conteur" and self.cible is None:
                self.gains = {p: 0 for p in self.mains}
            else:
                if not self.table:
                    self._monter_table()
                self._compter()
        for pid, j in self.p.joueurs.items():
            gain = self.gains.get(pid, 0)
            j.gain += gain
            j.score += gain
            j.trouve = gain > 0
            j.serie = j.serie + 1 if j.trouve else 0

    def duree_revelation(self, base):
        return base

    def statut(self, pid):
        if pid == self.conteur:
            return {"t": "conteur", "c": "ok" if self.indice else ""}
        if self.etape == "poser":
            return {"t": "a posé" if pid in self.poses else "", "c": "ok" if pid in self.poses else ""}
        if self.etape == "voter":
            return {"t": "a voté" if self._vote_fini(pid) else "", "c": "ok" if self._vote_fini(pid) else ""}
        return {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        c = J.get(self.conteur)
        if self.etape == "conteur":
            return f"{c.nom if c else '?'} choisit une affiche et un indice…"
        if self.etape == "poser":
            return f"{len(self.poses)} / {len(self._autres())} ont posé une affiche"
        if self.etape == "voter":
            return f"{sum(1 for p in self._autres() if self._vote_fini(p))} / {len(self._autres())} ont voté"
        return ""

    def _carte(self, i):
        c = self.m["cartes"][i]
        return {"img": c["img"], "txt": c["txt"]}

    def vue(self, pid, revele):
        self._maj()
        J = self.p.joueurs
        c = J.get(self.conteur)
        rev = self.etape == "rev" or revele
        v = {"etape": "rev" if revele else self.etape, "conteur": c.public() if c else None, "indice": self.indice,
             "deux": self._deux(), "reste": round(max(0.0, self._dur() - (self.p.ecoule - self.debut)), 1)}
        if self.table and self.etape in ("voter", "rev"):
            tab = []
            for i, x in enumerate(self.table):
                t = {"i": i, "img": self.m["cartes"][x["c"]]["img"]}
                if rev:
                    t.update(txt=self.m["cartes"][x["c"]]["txt"], cible=x["c"] == self.cible,
                             de=J[x["de"]].public() if x["de"] in J and not (self._deux() and x["de"] == self.conteur and x["c"] != self.cible) else None,
                             votants=[J[p].public() for p, v in self.votes.items() if v and (v[0] == i or (self._deux() and i in v)) and p in J])
                tab.append(t)
            v["table"] = tab
        if pid:
            moi_c = pid == self.conteur
            v.update(conteur_moi=moi_c, main=[dict(self._carte(x), c=x) for x in self.mains.get(pid, [])],
                     ma_cible=self.cible if moi_c else None, ma_pose=self.poses.get(pid),
                     mes_votes=self.votes.get(pid, []),
                     actif=not revele and not self.p.pause and (
                         (self.etape == "conteur" and moi_c) or (self.etape == "poser" and not moi_c and pid not in self.poses)
                         or (self.etape == "voter" and not moi_c and not self._vote_fini(pid))))
            if self.etape == "voter" and self.table and not moi_c:
                v["ma_carte_table"] = next((i for i, x in enumerate(self.table) if x["de"] == pid), None)
        if revele or self.etape == "rev":
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0)) for p in J], key=lambda x: -x["gain"])
        return v
