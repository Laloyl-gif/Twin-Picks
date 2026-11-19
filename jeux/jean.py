"""Jean Renault's Ransom (La rançon) : Jean Renault retient un film en otage au One Eyed Jack's.
1) La mise : on ne connaît du film que deux infos tirées au hasard (le genre, la décennie, le pays, la durée…).
   Chacun mise une rançon : de 0 à 2 500 points.
2) Le marché noir : Jean vend des preuves. Chacun achète en secret, sur son téléphone, les indices qu'il veut ; leur
   prix suit ce qu'ils révèlent (le genre ne coûte presque rien, le réalisateur cher) et grimpe avec la mise. On ne
   voit que ce qu'on a acheté, et on répond quand on veut (trois essais).
Trouvé : la mise × 2 (plus quelques points), moins les achats. Raté : la mise et les achats sont perdus.
"""
import random

from PIL import ImageOps

from texte import correspond, proche
from tmdb import details_film, fiche
from visuels import en_jpeg
from .commun import affiche, manche_titre, reponse_affichee, tirer, trous

MISES = (0, 250, 500, 1000, 1500, 2500)


def _hm(m):
    return f"{m // 60} h {m % 60:02d}" if m >= 60 else f"{m} min"


def preuves(api, film, d, fi, rep):
    """[(id, nom, prix de base, {"texte"} | {"img"})] du moins cher (le moins parlant) au plus cher, et les images."""
    an = d.get("annee") or ""
    out, images = [], []
    if d.get("genres"):
        out.append(("genre", "Le genre", 40, {"texte": ", ".join(g.lower() for g in d["genres"][:3])}))
    if an:
        out.append(("decennie", "La décennie", 60, {"texte": f"Les années {an[2]}0" if an[:2] == "19" else f"Les années {an[:3]}0"}))
    if fi.get("pays"):
        out.append(("pays", "Le pays", 70, {"texte": ", ".join(fi["pays"][:2])}))
    if fi.get("duree"):
        out.append(("duree", "La durée", 70, {"texte": _hm(fi["duree"])}))
    if fi.get("note"):
        out.append(("note", "La note TMDB", 80, {"texte": f"{fi['note']:.1f}/10".replace(".", ",")}))
    if an:
        out.append(("annee", "L'année exacte", 150, {"texte": an}))
    acteurs = fi.get("acteurs", [])
    if len(acteurs) > 3:
        out.append(("second", "Un second rôle", 180, {"texte": acteurs[random.randint(3, min(6, len(acteurs) - 1))]["nom"]}))
    fonds = d.get("fonds_neutres") or d.get("fonds") or []
    if fonds:
        try:
            images.append(en_jpeg(ImageOps.fit(api.image(random.choice(fonds[:8]), "w780").convert("RGB"), (480, 270)), 270))
            out.append(("image", "Une image du film", 220, {"img": len(images) - 1}))
        except Exception:  # noqa: BLE001
            pass
    if fi.get("compositeurs"):
        out.append(("compo", "Le compositeur", 240, {"texte": fi["compositeurs"][0]["nom"]}))
    if acteurs:
        out.append(("star", "La tête d'affiche", 350, {"texte": acteurs[0]["nom"]}))
    if fi.get("realisateurs"):
        out.append(("real", "Le réalisateur", 420, {"texte": " & ".join(r["nom"] for r in fi["realisateurs"][:2])}))
    out.append(("initiales", "Les initiales du titre", 500, {"texte": trous(rep, 0)}))
    out.append(("trous", "Le titre à moitié", 700, {"texte": trous(rep, 0.5)}))
    return out, images


def construire(api, cfg, pool, deja):
    for _ in range(15):
        film = tirer(pool, deja)
        d = details_film(api, film)
        try:
            fi = fiche(api, film)
        except Exception:  # noqa: BLE001
            continue
        rep = reponse_affichee(cfg, film, d)
        cat, images = preuves(api, film, d, fi, rep)
        bases = [c for c in cat if c[0] in ("genre", "decennie", "pays", "duree", "note")]
        if len(bases) >= 2 and len(cat) >= 7:
            break
    else:
        raise RuntimeError("La rançon : pas assez d'informations sur les films des listes choisies.")
    donnees = random.sample(bases, 2)
    marche = [{"id": c[0], "nom": c[1], "prix": c[2], **c[3]} for c in cat if c not in donnees]
    etat = {"etape": "mise", "infos": [{"nom": c[1], "texte": c[3]["texte"]} for c in donnees],
            "cachees": list(range(len(images)))}
    dm = float(cfg["jean_dur_mise"])
    etapes = [(0.0, etat), (dm, {**etat, "etape": "marche"})]
    m = manche_titre("jean", "rancon", float(cfg["dur_jean"]) + dm, film, d, etapes, images,
                     en_jpeg(affiche(api, film, "w500")), cfg)
    m.update(reponse="rancon", dur_mise=dm, marche=marche, suggestions=True)
    return m


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.mises, self.achats, self.trouve, self.essais, self.gains = {}, {}, {}, {}, {}

    def ok(self):
        return ""

    def _etape(self):
        return "mise" if self.p.ecoule < self.m["dur_mise"] else "marche"

    def prix(self, pid, base):
        """Plus on a misé, plus les preuves coûtent (×1 sans mise, ×2 pour 2 500)."""
        return int(round(base * (1 + self.mises.get(pid, 0) / 2500) / 10) * 10)

    def _depense(self, pid):
        return sum(self.prix(pid, c["prix"]) for c in self.m["marche"] if c["id"] in self.achats.get(pid, []))

    def action(self, pid, d, frac, info=None):
        if "mise" in d:
            if self._etape() != "mise":
                return {"ok": False, "msg": "Trop tard pour miser"}
            try:
                mise = int(d["mise"])
            except (TypeError, ValueError):
                return {"ok": False, "msg": "Mise refusée"}
            if mise not in MISES:
                return {"ok": False, "msg": "Mise refusée"}
            self.mises[pid] = mise
            if all(p in self.mises for p in self.p.joueurs):        # tout le monde a misé : le marché ouvre
                self.p.ecoule = max(self.p.ecoule, self.m["dur_mise"])
            return {"ok": True, "msg": f"Rançon : {mise}"}
        if self._etape() == "mise":
            return {"ok": False, "msg": "Misez d'abord"}
        if pid in self.trouve:
            return {"ok": False, "msg": "Otage déjà libéré !"}
        maxi = int(self.cfg.get("max_essais", 3))
        if "acheter" in d:
            c = next((c for c in self.m["marche"] if c["id"] == d["acheter"]), None)
            if not c:
                return {"ok": False, "msg": "Preuve inconnue"}
            if c["id"] in self.achats.setdefault(pid, []):
                return {"ok": False, "msg": "Déjà achetée"}
            self.achats[pid].append(c["id"])
            return {"ok": True, "msg": f"{c['nom']} : achetée {self.prix(pid, c['prix'])}"}
        texte = str(d.get("texte", "")).strip()
        if not texte:
            return {"ok": False, "msg": "Tapez un titre"}
        if self.essais.get(pid, 0) >= maxi:
            return {"ok": False, "msg": "Plus d'essais"}
        if any(correspond(texte, c) for c in self.m["cles"]):
            self.trouve[pid] = frac
            self.p.joueurs[pid].essais = 1
            return {"ok": True, "correct": True, "msg": "L'otage est libéré !"}
        self.essais[pid] = self.essais.get(pid, 0) + 1
        reste = maxi - self.essais[pid]
        if not reste:
            self.p.joueurs[pid].essais = 1
        presque = any(proche(texte, c) for c in self.m["cles"])
        return {"ok": False, "msg": ("Presque ! " if presque else "Raté. ") + (f"{reste} essai(s)" if reste else "Plus d'essais.")}

    def fini(self):
        J = self.p.joueurs
        maxi = int(self.cfg.get("max_essais", 3))
        return bool(J) and self._etape() == "marche" and all(p in self.trouve or self.essais.get(p, 0) >= maxi for p in J)

    def clore(self):
        for pid, j in self.p.joueurs.items():
            mise, dep = self.mises.get(pid, 0), self._depense(pid)
            if pid in self.trouve:
                gain = 2 * mise + int(self.cfg["jean_pts"]) + int(self.cfg["bonus_vitesse"] * self.trouve[pid] / 2) - dep
            else:
                gain = -(mise + dep)
            gain = max(gain, -j.score)                      # on ne descend pas sous zéro
            j.gain += gain
            j.score += gain
            j.trouve = pid in self.trouve
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        if pid in self.trouve:
            return {"t": "libéré", "c": "ok"}
        if self._etape() == "mise":
            return {"t": "a misé", "c": "ok"} if pid in self.mises else {"t": "", "c": ""}
        n = len(self.achats.get(pid, []))
        return {"t": f"{n} preuve{'s' if n > 1 else ''}", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        if self._etape() == "mise":
            return f"{sum(1 for p in J if p in self.mises)} / {len(J)} ont misé"
        return f"{sum(1 for p in J if p in self.trouve)} / {len(J)} ont libéré l'otage"

    def vue(self, pid, revele):
        J = self.p.joueurs
        et = self._etape()
        v = {"etape": et, "mises": MISES,
             "joueurs": [dict(J[p].public(), mise=self.mises.get(p) if et != "mise" or revele else None,
                              a_mise=p in self.mises, achats=len(self.achats.get(p, [])), libere=p in self.trouve) for p in J]}
        if pid:
            maxi = int(self.cfg.get("max_essais", 3))
            pris = self.achats.get(pid, [])
            v.update(ma_mise=self.mises.get(pid), trouve=pid in self.trouve, depense=self._depense(pid),
                     marche=[{"id": c["id"], "nom": c["nom"], "prix": self.prix(pid, c["prix"]), "achete": c["id"] in pris,
                              **({k: c[k] for k in ("texte", "img") if k in c} if c["id"] in pris or revele else {})}
                             for c in self.m["marche"]],
                     actif=not revele and not self.p.pause and (pid not in self.mises if et == "mise" else
                                                               pid not in self.trouve and self.essais.get(pid, 0) < maxi))
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0), mise=self.mises.get(p, 0),
                                          depense=self._depense(p), trouve=p in self.trouve) for p in J], key=lambda x: -x["gain"])
        return v
