"""Vraies images de film pour « Truman's Files », triées de la plus difficile à la plus facile.

Sources, de la meilleure à la moins bonne :
  1. Vos fichiers vidéo (dossier réglable) : ffmpeg extrait des images à des instants tirés au hasard
     dans le film (hors génériques). Ce sont de vraies images du film, jamais des photos promotionnelles.
  2. Séries : les images d'épisodes de TMDB (captures d'écran des épisodes).
  3. Films sans vidéo : les fonds TMDB sans texte, sans les plus votés (souvent des visuels promotionnels).

Chaque image candidate reçoit une note de facilité (visages en gros plan, couleurs, lumière, détails,
ressemblance avec l'affiche, popularité sur TMDB) ; on garde une image difficile, une moyenne, une facile.
"""
import io
import os
import random
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps

from texte import cle

try:
    import numpy as np
except ImportError:                       # numpy absent : difficulté au hasard
    np = None
try:
    import cv2                            # facultatif (opencv-python-headless) : détection des visages
    _fichier = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    _VISAGES = cv2.CascadeClassifier(_fichier) if os.path.isfile(_fichier) else None
    if _VISAGES is not None and _VISAGES.empty():
        _VISAGES = None
except Exception:  # noqa: BLE001
    cv2 = _VISAGES = None

EXTENSIONS = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".webm", ".wmv", ".mpg", ".mpeg", ".ts", ".m2ts", ".vob"}
ETIQUETTES = re.compile(
    r"\b(2160p|1080p|1080i|720p|576p|480p|4k|uhd|hdr|hdr10|dv|dovi|bluray|blu ray|bdrip|brrip|bdremux|remux|webrip|"
    r"web dl|webdl|web|hdtv|dvdrip|dvd|hdrip|x264|x265|h264|h265|hevc|avc|av1|aac|ac3|eac3|dts|truehd|atmos|"
    r"multi|vff|vfq|vfi|vf|vo|vostfr|truefrench|french|subfrench|english|proper|repack|extended|unrated|"
    r"directors cut|director s cut|theatrical|imax|remastered|10bit|8bit)\b", re.I)
IGNORER = re.compile(r"\b(sample|trailer|bande annonce|featurette|extras?|bonus|making of|behind the scenes)\b", re.I)
EPISODE = re.compile(r"\bs\d{1,2} ?e\d{1,3}\b|\b\d{1,2}x\d{2}\b", re.I)
NB_CANDIDATES = 14
TAILLE_MIN = 50 * 1024 * 1024                  # en dessous : extrait, bande-annonce…


# ====================================================================================
# Vidéothèque locale
# ====================================================================================
def analyser_nom(nom):
    """« Le.Fabuleux.Destin.d'Amélie.Poulain.2001.1080p.BluRay.mkv » -> ("fabuleux destin d amelie poulain", 2001)."""
    base, ext = os.path.splitext(nom)
    t = re.sub(r"[._]+", " ", base if ext.lower() in EXTENSIONS else nom)
    annees = [m for m in re.finditer(r"(?<!\d)(19[0-9]{2}|20[0-9]{2})(?!\d)", t) if m.start() > 0]
    annee = int(annees[-1].group(1)) if annees else None
    if annees:
        t = t[:annees[-1].start()]
    m = ETIQUETTES.search(t)
    if m and m.start() > 0:
        t = t[:m.start()]
    t = re.sub(r"[\(\[\{][^\)\]\}]*$", "", t)              # parenthèse ouverte avant l'année
    return cle(t), annee


class Videotheque:
    def __init__(self, dossier):
        self.dossier, self.films = dossier, {}
        for racine, dossiers, fichiers in os.walk(dossier):
            dossiers[:] = [d for d in dossiers if not d.startswith(".") and not IGNORER.search(d)]
            for f in fichiers:
                if os.path.splitext(f)[1].lower() not in EXTENSIONS or IGNORER.search(f) or EPISODE.search(f):
                    continue
                chemin = os.path.join(racine, f)
                try:
                    taille = os.path.getsize(chemin)
                except OSError:
                    continue
                if taille < TAILLE_MIN:
                    continue
                vus = set()
                for nom in (f, os.path.basename(racine)):     # nom du fichier, puis nom du dossier
                    k, annee = analyser_nom(nom)
                    if k and k not in vus:
                        vus.add(k)
                        self.films.setdefault(k, []).append((annee, taille, chemin))

    def __len__(self):
        return len({c for v in self.films.values() for _, _, c in v})

    def chercher(self, noms, annee):
        """Le plus gros fichier dont le titre correspond (et l'année, à un an près, si elle est connue)."""
        try:
            annee = int(annee) if annee else None
        except ValueError:
            annee = None
        trouves = []
        for n in noms:
            for a, taille, chemin in self.films.get(cle(n or ""), []):
                if not (a and annee) or abs(a - annee) <= 1:
                    trouves.append((taille, chemin))
        return max(trouves)[1] if trouves else None


_VIDEOTHEQUES, _verrou_vt = {}, threading.Lock()


def videotheque(dossier):
    """Vidéothèque du dossier (relue toutes les 10 minutes au plus)."""
    dossier = os.path.expanduser((dossier or "").strip())
    if not dossier:
        return None
    if not os.path.isdir(dossier):
        raise RuntimeError(f"Dossier de films introuvable : {dossier}")
    with _verrou_vt:
        date, vt = _VIDEOTHEQUES.get(dossier, (0, None))
        if vt is None or time.time() - date > 600:
            vt = Videotheque(dossier)
            _VIDEOTHEQUES[dossier] = (time.time(), vt)
        return vt


# ====================================================================================
# ffmpeg
# ====================================================================================
def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return None


def _creationflags():
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)           # pas de fenêtre console sous Windows


def sonder(chemin):
    """(durée en secondes, vidéo HDR ?) d'après la sortie de « ffmpeg -i »."""
    exe = ffmpeg()
    r = subprocess.run([exe, "-hide_banner", "-nostdin", "-i", chemin], capture_output=True, timeout=60,
                       creationflags=_creationflags())
    sortie = r.stderr.decode("utf-8", "replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", sortie)
    duree = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    return duree, bool(re.search(r"smpte2084|arib-std-b67|bt2020", sortie))


FILTRE_HDR = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
              "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


def image_a(chemin, t, hdr=False, largeur=960):
    """Image du film à l'instant t (secondes), ou None."""
    filtres = (FILTRE_HDR if hdr else "") + f"scale='trunc(iw*sar/2)*2':ih,setsar=1,scale={largeur}:-2"
    for f in ([filtres, filtres[len(FILTRE_HDR):]] if hdr else [filtres]):   # sans tonemap si zscale manque
        cmd = [ffmpeg(), "-hide_banner", "-nostdin", "-loglevel", "error", "-noaccurate_seek", "-ss", f"{t:.2f}",
               "-i", chemin, "-map", "0:v:0", "-frames:v", "1", "-vf", f, "-f", "image2pipe", "-vcodec", "mjpeg",
               "-q:v", "3", "-"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=45, creationflags=_creationflags())
            if r.returncode == 0 and r.stdout:
                return Image.open(io.BytesIO(r.stdout)).convert("RGB")
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
    return None


def extraire(chemin, n=NB_CANDIDATES):
    """n images réparties au hasard entre 6 % et 90 % du film (pas de générique) : [(instant, image)]."""
    duree, hdr = sonder(chemin)
    if duree < 60:
        return []
    debut, fin = duree * 0.06, duree * 0.90
    pas = (fin - debut) / n
    instants = [debut + pas * (i + random.uniform(0.1, 0.9)) for i in range(n)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        images = list(ex.map(lambda t: image_a(chemin, t, hdr), instants))
    return [(t, im) for t, im in zip(instants, images) if im is not None]


def horodatage(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


# ====================================================================================
# Qualité et difficulté
# ====================================================================================
def rogner_bandes(img):
    """Retire les bandes noires (cinémascope, 4/3 dans du 16/9)."""
    if np is None:
        return img
    g = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = g.shape
    lignes, colonnes = g.mean(axis=1) > 14, g.mean(axis=0) > 14
    if not lignes.any() or not colonnes.any():
        return img
    haut, bas = int(np.argmax(lignes)), h - int(np.argmax(lignes[::-1]))
    gauche, droite = int(np.argmax(colonnes)), w - int(np.argmax(colonnes[::-1]))
    if haut > h * 0.3 or h - bas > h * 0.3:
        haut, bas = 0, h
    if gauche > w * 0.3 or w - droite > w * 0.3:
        gauche, droite = 0, w
    return img.crop((gauche, haut, droite, bas))


def empreinte(img):
    """dHash 64 bits (pour écarter les images presque identiques)."""
    g = img.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
    px = list(g.getdata())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])


def _histo(img):
    im = img.convert("RGB").resize((64, 64))
    h = [0] * 64
    for r, g, b in im.getdata():
        h[(r >> 6) * 16 + (g >> 6) * 4 + (b >> 6)] += 1
    return [x / 4096 for x in h]


def _visage(img):
    """Part de l'image occupée par le plus grand visage (0 sans opencv ou sans visage)."""
    if _VISAGES is None or np is None:
        return None
    im = img.convert("L")
    im.thumbnail((480, 480))
    g = np.asarray(im)
    faces = _VISAGES.detectMultiScale(g, scaleFactor=1.15, minNeighbors=6, minSize=(24, 24))
    if len(faces) == 0:
        return 0.0
    return max(w * h for (_, _, w, h) in faces) / float(g.shape[0] * g.shape[1])


def mesures(img):
    """Mesures 0..1 d'une image : lumiere, contraste, couleur, detail, peau (centre), visage."""
    im = img.convert("RGB")
    im.thumbnail((256, 256))
    a = np.asarray(im, dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    rg, yb = r - g, 0.5 * (r + g) - b
    couleur = (np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean())) / 100
    detail = (np.abs(np.diff(lum, axis=1)).mean() + np.abs(np.diff(lum, axis=0)).mean()) / 30
    cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
    cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
    h, w = lum.shape
    centre = (slice(h // 5, h - h // 5), slice(w // 5, w - w // 5))
    peau = ((cb >= 77) & (cb <= 127) & (cr >= 137) & (cr <= 173) & (lum > 45))[centre].mean()
    return dict(lumiere=float(lum.mean() / 255), contraste=float(min(1, lum.std() / 70)),
                couleur=float(min(1, couleur)), detail=float(min(1, detail)), peau=float(peau), visage=_visage(img))


def exploitable(m):
    """Écarte les images noires, délavées ou presque unies (fondus, génériques)."""
    return m["lumiere"] > 0.07 and m["contraste"] > 0.16 and m["detail"] > 0.08


def facilite(m, histo_affiche=None, histo=None, popularite=None):
    """Note de facilité 0..1 : plus c'est haut, plus le film est facile à reconnaître."""
    if m.get("visage") is not None:
        personnage = min(1.0, (m["visage"] ** 0.5) * 3.2)
    else:
        personnage = min(1.0, m["peau"] * 3.5)
    ressemblance = 0.0
    if histo_affiche and histo:
        inter = sum(min(x, y) for x, y in zip(histo_affiche, histo))
        ressemblance = max(0.0, min(1.0, (inter - 0.25) / 0.5))
    note = (0.34 * personnage + 0.14 * m["couleur"] + 0.14 * min(1.0, m["lumiere"] / 0.45)
            + 0.10 * m["detail"] + 0.10 * m["contraste"] + 0.18 * ressemblance)
    if popularite is not None:
        note = 0.75 * note + 0.25 * popularite
    return note


def choisir(cands, n=3):
    """cands : [(facilité, image, info)]. Garde n images étalées en difficulté, la plus difficile d'abord."""
    s = sorted(cands, key=lambda c: c[0])
    if len(s) <= n:
        return s
    reperes = [0.12 + (0.92 - 0.12) * k / (n - 1) for k in range(n)] if n > 1 else [0.5]
    idx = []
    for q in reperes:
        i = round(q * (len(s) - 1))
        while i in idx and i < len(s) - 1:
            i += 1
        idx.append(i)
    return [s[i] for i in sorted(set(idx))][:n]


def noter(images, affiche=None, popularites=None):
    """[(image, info)] -> [(facilité, image, info)] sans doublons ni images inexploitables."""
    histo_affiche = _histo(affiche) if affiche is not None else None
    out, empreintes = [], []
    for k, (im, info) in enumerate(images):
        im = rogner_bandes(im)
        e = empreinte(im)
        if any(bin(e ^ x).count("1") <= 10 for x in empreintes):
            continue
        if np is None:
            out.append((random.random(), im, info))
            empreintes.append(e)
            continue
        m = mesures(im)
        if not exploitable(m):
            continue
        empreintes.append(e)
        pop = popularites[k] if popularites else None
        out.append((facilite(m, histo_affiche, _histo(im), pop), im, info))
    return out


# ====================================================================================
# Dossier plans/ : des plans choisis à la main, un sous-dossier par film
# ====================================================================================
IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
ID_TMDB = re.compile(r"\[tmdb-(tv-)?(\d+)\]", re.I)


class Planotheque:
    """plans/<Titre (année) [tmdb-123]>/01.jpg, 02.jpg… (01 = le plus difficile).
    Le dossier est reconnu par l'identifiant TMDB entre crochets, sinon par le titre et l'année."""

    def __init__(self, dossier):
        self.dossier, self.par_id, self.par_titre = dossier, {}, {}
        try:
            noms = sorted(os.listdir(dossier))
        except OSError:
            noms = []
        for nom in noms:
            chemin = os.path.join(dossier, nom)
            if not os.path.isdir(chemin) or nom.startswith("."):
                continue
            images = sorted(f for f in os.listdir(chemin) if os.path.splitext(f)[1].lower() in IMAGES)
            if len(images) < 3:
                continue
            m = ID_TMDB.search(nom)
            if m:
                self.par_id[("tv" if m.group(1) else "m", int(m.group(2)))] = chemin
            k, annee = analyser_nom(ID_TMDB.sub("", nom).strip() + ".dossier")
            if k:
                self.par_titre.setdefault(k, []).append((annee, chemin))

    def __len__(self):
        return len(set(self.par_id.values()) | {c for v in self.par_titre.values() for _, c in v})

    def chercher(self, film, noms, annee):
        chemin = self.par_id.get(("tv" if film["tv"] else "m", film["id"]))
        if chemin:
            return chemin
        try:
            annee = int(annee) if annee else None
        except ValueError:
            annee = None
        for n in noms:
            for a, c in self.par_titre.get(cle(n or ""), []):
                if not (a and annee) or abs(a - annee) <= 1:
                    return c
        return None


_PLANOTHEQUE = [0.0, None]


def planotheque(dossier):
    """Dossier plans/ (relu toutes les 30 s au plus : on peut y ajouter des films pendant que le jeu tourne)."""
    if _PLANOTHEQUE[1] is None or _PLANOTHEQUE[1].dossier != dossier or time.time() - _PLANOTHEQUE[0] > 30:
        _PLANOTHEQUE[:] = [time.time(), Planotheque(dossier)]
    return _PLANOTHEQUE[1]


def plans_dossier(chemin, affiche, n=3):
    """n plans du dossier d'un film, la plus difficile d'abord : un tiré dans chaque tranche de difficulté.
    Noms numérotés (01, 02…) : l'ordre des noms est l'ordre de difficulté ; sinon, difficulté estimée."""
    fichiers = sorted(f for f in os.listdir(chemin) if os.path.splitext(f)[1].lower() in IMAGES)
    if len(fichiers) < n:
        return None
    if not all(f[:1].isdigit() for f in fichiers):
        images = []
        for f in fichiers:
            try:
                images.append((Image.open(os.path.join(chemin, f)).convert("RGB"), f))
            except OSError:
                continue
        notes = sorted(noter(images, affiche), key=lambda c: c[0])      # du plus difficile au plus facile
        fichiers = [info for _, _, info in notes]
        if len(fichiers) < n:
            return None
    tranches = [fichiers[round(k * len(fichiers) / n):round((k + 1) * len(fichiers) / n)] for k in range(n)]
    out = []
    for t in tranches:
        f = random.choice(t)
        try:
            out.append((Image.open(os.path.join(chemin, f)).convert("RGB"), ""))
        except OSError:
            return None
    return out


# ====================================================================================
# Les trois sources
# ====================================================================================
def plans_video(chemin, affiche, n=3):
    """n vraies images extraites de la vidéo, la plus difficile d'abord : [(image, horodatage)]."""
    if not ffmpeg():
        raise RuntimeError("ffmpeg introuvable : installez ffmpeg ou « pip install imageio-ffmpeg ».")
    notes = noter([(im, horodatage(t)) for t, im in extraire(chemin)], affiche)
    choix = choisir(notes, n)
    return [(im, info) for _, im, info in choix] if len(choix) >= n else None


def plans_serie(api, film, affiche, n=3):
    """Images d'épisodes (vraies captures) d'une série TMDB."""
    try:
        saisons = [s["season_number"] for s in api.get(f"/tv/{film['id']}").get("seasons", [])
                   if s.get("season_number", 0) > 0 and s.get("episode_count")]
    except Exception:  # noqa: BLE001
        return None
    stills = []
    for s in random.sample(saisons, min(2, len(saisons))):
        try:
            for ep in api.get(f"/tv/{film['id']}/season/{s}").get("episodes", []):
                if ep.get("still_path"):
                    stills.append((ep["still_path"], f"S{s:02d}E{ep.get('episode_number', 0):02d}"))
        except Exception:  # noqa: BLE001
            continue
    if len(stills) < n:
        return None
    stills = random.sample(stills, min(NB_CANDIDATES, len(stills)))
    petites = api.images([p for p, _ in stills], "w300")
    choix = choisir(noter([(im, (p, ep)) for im, (p, ep) in zip(petites, stills)], affiche), n)
    if len(choix) < n:
        return None
    grandes = api.images([info[0] for _, _, info in choix], "w780")
    return [(rogner_bandes(g), info[1]) for g, (_, _, info) in zip(grandes, choix)]


def plans_tmdb(api, details, affiche, n=3):
    """Fonds TMDB sans texte, sans les plus votés (souvent des visuels promotionnels)."""
    fonds = sorted(details.get("fonds_votes") or [], key=lambda f: (f["note"], f["votes"]), reverse=True)
    if len(fonds) >= 8:
        fonds = fonds[2:]
    elif len(fonds) >= 5:
        fonds = fonds[1:]
    if len(fonds) < n:
        return None
    total = len(fonds)
    pop = {f["p"]: 1 - i / max(1, total - 1) for i, f in enumerate(fonds)}   # 1 = le plus voté restant
    fonds = random.sample(fonds, min(NB_CANDIDATES, total))
    petites = api.images([f["p"] for f in fonds], "w300")
    notes = noter([(im, f["p"]) for im, f in zip(petites, fonds)], affiche, [pop[f["p"]] for f in fonds])
    choix = choisir(notes, n)
    if len(choix) < n:
        return None
    grandes = api.images([p for _, _, p in choix], "w780")
    return [(g, "") for g in grandes]
