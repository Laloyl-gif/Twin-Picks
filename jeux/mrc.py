"""Mr. C's Doppelganger (Le double) : Mr. C est le double maléfique de Cooper. Deux versions de la même affiche,
côte à côte : l'originale et son double, trafiqué à trois endroits (un objet effacé, une zone retournée, une couleur
changée…). Les retouches se voient quand on compare (zones assez grandes, écart minimal vérifié) sans sauter
aux yeux. Chacun touche sur son téléphone les endroits des différences : points
selon la vitesse (une erreur coûte un peu). On ne cherche pas le film. À la réponse, les différences sont entourées.
"""
import random

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

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


def _retouche(im, t, x0, y0, c):
    """La zone (x0, y0, c × c) retouchée selon le type t."""
    zone = im.crop((x0, y0, x0 + c, y0 + c))
    if t == "efface":                                  # un détail disparaît : le fond « bavé » par-dessus
        grand = im.crop((max(0, x0 - c // 2), max(0, y0 - c // 2), min(L, x0 + c + c // 2), min(H, y0 + c + c // 2)))
        flou = grand.filter(ImageFilter.GaussianBlur(c / 2.5)).resize(zone.size)
        masque = Image.new("L", zone.size, 0)
        masque.paste(255, (c // 7, c // 7, c - c // 7, c - c // 7))
        masque = masque.filter(ImageFilter.GaussianBlur(c / 10))
        return Image.composite(flou, zone, masque)
    if t == "retourne":
        z = ImageOps.mirror(zone)
        return ImageOps.flip(z) if z.tobytes() == zone.tobytes() else z
    if t == "decale":                                  # le détail glisse nettement
        dx = max(8, c // 4) * random.choice((-1, 1))
        sx = min(max(0, x0 + dx), L - c)
        return im.crop((sx, y0, sx + c, y0 + c))
    if t == "agrandi":                                 # le détail grossit
        m = c // 5
        return zone.crop((m, m, c - m, c - m)).resize(zone.size, Image.LANCZOS)
    if t == "teinte":                                  # plus clair ou plus sombre
        f = random.choice((0.6, 1.5))
        return zone.point(lambda p: max(0, min(255, int(p * f))))
    hsv = zone.convert("HSV")                          # la couleur tourne franchement
    h, s_, v = hsv.split()
    dec = random.choice((45, -45, 70))
    h = h.point(lambda p: (p + dec) % 256)
    s_ = s_.point(lambda p: min(255, int(p * 1.2) + 12))
    return Image.merge("HSV", (h, s_, v)).convert("RGB")


def _ecart(a, b):
    """Écart moyen entre deux zones (0 à 255) : sert à refuser une retouche invisible."""
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


SEUIL, PLAFOND = 13, 24     # écart moyen voulu : visible quand on compare, sans sauter aux yeux


def trafiquer(im, sans_texte, n=3):
    """Le double et ses différences [{x, y, r, type}] (coordonnées en part de l'image).
    Retouches assez grandes et assez fortes pour se voir en comparant les deux affiches (zones choisies là où l'image
    a du détail, écart minimal vérifié), mais fondues dans l'affiche : pas de tache qui saute aux yeux."""
    im = ImageOps.fit(im, (L, H))
    double = im.copy()
    pts = centres(im, sans_texte, 10)
    random.shuffle(pts)
    diffs, pris = [], []
    types = random.sample(TYPES, min(n, len(TYPES)))
    for t in types:
        libres = [(x, y) for x, y in pts
                  if all((x - a) ** 2 + ((y - b) * H / L) ** 2 > 0.26 ** 2 for a, b in pris)]
        libres = libres or [(random.uniform(.2, .8), random.uniform(.25, .75)) for _ in range(4)]
        c = int(L * random.uniform(0.12, 0.155))
        meilleur = None
        for essai, (x, y) in enumerate(libres):
            x0 = int(min(max(0, x * L - c / 2), L - c))
            y0 = int(min(max(0, y * H - c / 2), H - c))
            orig = im.crop((x0, y0, x0 + c, y0 + c))
            for tt in (t, "teinte"):                   # en dernier recours, plus clair ou plus sombre
                zone = _retouche(im, tt, x0, y0, c)
                e = _ecart(zone, orig)
                if e > PLAFOND:                        # trop flagrant : on adoucit vers l'original
                    zone, e = Image.blend(orig, zone, PLAFOND / e), PLAFOND
                if meilleur is None or e > meilleur[0]:
                    meilleur = (e, x, y, x0, y0, zone, tt)
                if e >= SEUIL or essai < len(libres) - 1:
                    break
            if meilleur[0] >= SEUIL:
                break
        _, x, y, x0, y0, zone, tt = meilleur
        pris.append((x, y))
        boite = (x0, y0, x0 + c, y0 + c)
        # bords adoucis : la retouche se fond dans l'affiche, sans arête carrée
        fondu = Image.new("L", zone.size, 0)
        fondu.paste(255, (c // 8, c // 8, c - c // 8, c - c // 8))
        fondu = fondu.filter(ImageFilter.GaussianBlur(c / 12))
        double.paste(Image.composite(zone, im.crop(boite), fondu), boite)
        diffs.append({"x": round((x0 + c / 2) / L, 4), "y": round((y0 + c / 2) / H, 4),
                      "r": round(max(c / L * 0.75, 0.08), 4), "type": tt})
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
