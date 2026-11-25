"""Mr. C's Doppelganger (Le double) : Mr. C est le double maléfique de Cooper. Deux versions de la même affiche,
côte à côte : l'originale et son double, trafiqué à trois endroits (un objet effacé, une zone retournée, une couleur
changée…). Les retouches sont petites et discrètes. Chacun touche sur son téléphone les endroits des différences : points
selon la vitesse (une erreur coûte un peu). On ne cherche pas le film. À la réponse, les différences sont entourées.
"""
import random

from PIL import Image, ImageFilter, ImageOps

from texte import correspond
from tmdb import affiches_film, details_film
from visuels import en_jpeg
from .commun import affiche, manche_titre, tirer
from .harold import centres

L, H = 480, 720


def _affiche(api, film):
    try:
        for p in affiches_film(api, film)[:6]:
            if p["langue"] is None:
                return api.image(p["chemin"], "w780").convert("RGB"), True
    except Exception:  # noqa: BLE001
        pass
    return affiche(api, film, "w780").convert("RGB"), False


TYPES = ("efface", "retourne", "couleur", "decale", "agrandi", "teinte")


def trafiquer(im, sans_texte, n=3):
    """Le double et ses différences [{x, y, r, type}] (coordonnées en part de l'image). Retouches petites et discrètes."""
    im = ImageOps.fit(im, (L, H))
    double = im.copy()
    pts = centres(im, sans_texte, 8)
    random.shuffle(pts)
    diffs, pris = [], []
    for t in random.sample(TYPES, min(n, len(TYPES))):
        for x, y in pts:
            if all((x - a) ** 2 + ((y - b) * H / L) ** 2 > 0.28 ** 2 for a, b in pris):
                break
        else:
            x, y = random.uniform(.2, .8), random.uniform(.25, .75)
        pris.append((x, y))
        c = int(L * random.uniform(0.09, 0.13))
        x0 = int(min(max(0, x * L - c / 2), L - c))
        y0 = int(min(max(0, y * H - c / 2), H - c))
        boite = (x0, y0, x0 + c, y0 + c)
        zone = im.crop(boite)
        if t == "efface":                                  # un détail disparaît : le fond « bavé » par-dessus
            grand = im.crop((max(0, x0 - c // 2), max(0, y0 - c // 2), min(L, x0 + c + c // 2), min(H, y0 + c + c // 2)))
            flou = grand.filter(ImageFilter.GaussianBlur(c / 3)).resize(zone.size)
            masque = Image.new("L", zone.size, 0)
            masque.paste(255, (c // 5, c // 5, c - c // 5, c - c // 5))
            masque = masque.filter(ImageFilter.GaussianBlur(c / 8))
            zone = Image.composite(flou, zone, masque)
        elif t == "retourne":
            zone = ImageOps.mirror(zone)
            if zone.tobytes() == im.crop(boite).tobytes():
                zone = ImageOps.flip(zone)
        elif t == "decale":                                # le détail glisse de quelques pixels
            dx = max(4, c // 6) * random.choice((-1, 1))
            src = im.crop((max(0, x0 + dx), y0, max(0, x0 + dx) + c, y0 + c))
            zone = src.resize(zone.size)
        elif t == "agrandi":                               # le détail grossit un peu
            m = c // 8
            zone = zone.crop((m, m, c - m, c - m)).resize(zone.size, Image.LANCZOS)
        elif t == "teinte":                                # plus clair ou plus sombre
            f = random.choice((0.7, 1.35))
            zone = zone.point(lambda p: max(0, min(255, int(p * f))))
        else:                                              # la couleur tourne un peu
            hsv = zone.convert("HSV")
            h, s_, v = hsv.split()
            dec = random.choice((40, -40, 60))
            h = h.point(lambda p: (p + dec) % 256)
            s_ = s_.point(lambda p: min(255, p + 25))
            zone = Image.merge("HSV", (h, s_, v)).convert("RGB")
        # bords adoucis : la retouche se fond dans l'affiche
        fondu = Image.new("L", zone.size, 0)
        fondu.paste(255, (c // 10, c // 10, c - c // 10, c - c // 10))
        fondu = fondu.filter(ImageFilter.GaussianBlur(c / 14))
        double.paste(Image.composite(zone, im.crop(boite), fondu), boite)
        diffs.append({"x": round((x0 + c / 2) / L, 4), "y": round((y0 + c / 2) / H, 4),
                      "r": round(max(c / L * 0.8, 0.075), 4), "type": t})
    return im, double, diffs


def construire(api, cfg, pool, deja):
    film = tirer([f for f in pool if f.get("poster_path")] or pool, deja)
    d = details_film(api, film)
    im, sans_texte = _affiche(api, film)
    orig, double, diffs = trafiquer(im, sans_texte, int(cfg.get("mrc_n", 3)))
    images = [en_jpeg(orig, H), en_jpeg(double, H)]
    m = manche_titre("mrc", "double", float(cfg["dur_mrc"]), film, d, [(0.0, {"cachees": [0, 1]})], images, None, cfg)
    m.update(reponse="differences", diffs=diffs)
    return m


class Moteur:

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.trouves, self.erreurs, self.gains = {}, {}, {}
        self.n = len(m["diffs"])

    def ok(self):
        return ""

    def _fini_pour(self, pid):
        return len(self.trouves.get(pid, {})) == self.n or self.erreurs.get(pid, 0) >= int(self.cfg["mrc_erreurs"])

    def action(self, pid, d, frac, info=None):
        try:
            x, y = float(d["pos"][0]), float(d["pos"][1])
        except (KeyError, TypeError, ValueError, IndexError):
            return {"ok": False, "msg": ""}
        mes = self.trouves.setdefault(pid, {})
        if self.erreurs.get(pid, 0) >= int(self.cfg["mrc_erreurs"]):
            return {"ok": False, "msg": "Plus de touches : trop d'erreurs"}
        for k, df in enumerate(self.m["diffs"]):
            dedans = ((x - df["x"]) ** 2 + ((y - df["y"]) * H / L) ** 2) ** 0.5 <= df["r"] * 1.35
            if k in mes:
                if dedans:
                    return {"ok": False, "msg": "Celle-là est déjà trouvée"}
                continue
            if dedans:
                mes[k] = frac
                reste = len(self.m["diffs"]) - len(mes)
                return {"ok": True, "correct": not reste, "msg": f"Trouvé ! Encore {reste}" if reste else "Toutes les différences !"}
        self.erreurs[pid] = self.erreurs.get(pid, 0) + 1
        reste = int(self.cfg["mrc_erreurs"]) - self.erreurs[pid]
        return {"ok": True, "correct": False, "msg": f"Rien ici ({reste} erreur{'s' if reste > 1 else ''} permise{'s' if reste > 1 else ''})"}

    def fini(self):
        J = self.p.joueurs
        return bool(J) and all(self._fini_pour(p) for p in J)

    def clore(self):
        for pid, j in self.p.joueurs.items():
            fr = self.trouves.get(pid, {})
            gain = sum(int(self.cfg["mrc_pts"] * (0.5 + 0.5 * f)) for f in fr.values())
            gain -= int(self.cfg["mrc_malus"]) * self.erreurs.get(pid, 0)
            gain = max(gain, -j.score)
            j.gain += gain
            j.score += gain
            j.trouve = len(fr) == len(self.m["diffs"])
            j.serie = j.serie + 1 if j.trouve else 0
            self.gains[pid] = gain

    def statut(self, pid):
        n = len(self.trouves.get(pid, {}))
        return {"t": f"{n}/{self.n}", "c": "ok" if n == self.n else ""} if n else {"t": "", "c": ""}

    def avancement(self):
        J = self.p.joueurs
        return f"{sum(1 for p in J if len(self.trouves.get(p, {})) == self.n)} / {len(J)} ont tout trouvé"

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"compte": [dict(J[p].public(), n=len(self.trouves.get(p, {}))) for p in J]}
        if pid:
            v.update(mes=[self.m["diffs"][k] for k in self.trouves.get(pid, {})], erreurs=self.erreurs.get(pid, 0),
                     max_erreurs=int(self.cfg["mrc_erreurs"]),
                     actif=not revele and not self.p.pause and self.erreurs.get(pid, 0) < int(self.cfg["mrc_erreurs"])
                     and len(self.trouves.get(pid, {})) < len(self.m["diffs"]))
        v["n"] = self.n
        if revele:
            v["diffs"] = self.m["diffs"]
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0), n=len(self.trouves.get(p, {})))
                                     for p in J], key=lambda x: -x["gain"])
        return v
