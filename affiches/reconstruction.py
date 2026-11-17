"""Reconstruction des zones effacées (inpainting), en local.

Outils, du meilleur au plus simple :
  simple_lama  LaMa (PyTorch) via « pip install simple-lama-inpainting » : le plus fidèle, toute taille d'image
  lama_onnx    le même modèle LaMa en ONNX (onnxruntime, sans PyTorch) : téléchargé une fois (~200 Mo).
               Une passe sur toute l'affiche (le décor d'ensemble), puis chaque zone est refaite de près, à pleine
               résolution, avec autour d'elle le décor déjà reconstruit (jamais un morceau de personnage) : plus net.
  opencv_fsr   repli sans modèle (opencv-contrib : cv2.xphoto) : bien meilleur que le remplissage simple
  opencv       repli sans modèle : remplissage en pyramide + grain ; correct pour de petites zones seulement
Après coup : grain de l'affiche ajouté aux grandes zones (pas d'aplat lisse), puis fondu des bords.
"""
import threading

import numpy as np

from . import modeles
from .modeles import OutilManquant

try:
    import cv2
except ImportError:
    cv2 = None

_SESSIONS, _VERROU = {}, threading.Lock()


def _fondre(img, rempli, masque, rayon):
    """Colle la zone reconstruite avec un bord adouci."""
    m = (masque > 0).astype(np.float32)
    if rayon > 0:
        k = 2 * int(rayon) + 1
        m = np.maximum(m, cv2.GaussianBlur(m, (k, k), rayon / 2))
    m = m[..., None]
    return np.clip(img.astype(np.float32) * (1 - m) + rempli.astype(np.float32) * m, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- LaMa (PyTorch)
def _simple_lama(rgb, masque, cfg):
    from PIL import Image
    from simple_lama_inpainting import SimpleLama
    with _VERROU:
        if "simple_lama" not in _SESSIONS:
            _SESSIONS["simple_lama"] = SimpleLama()
    out = _SESSIONS["simple_lama"](Image.fromarray(rgb), Image.fromarray(masque).convert("L"))
    out = np.asarray(out.convert("RGB"))[:rgb.shape[0], :rgb.shape[1]]
    return out, "simple_lama"


# ---------------------------------------------------------------- LaMa (ONNX)
def _session_onnx(cfg):
    import onnxruntime as ort
    with _VERROU:
        if "lama_onnx" not in _SESSIONS:
            chemin = modeles.obtenir(cfg["lama_onnx_url"], "lama_fp32.onnx")
            fournisseurs = [p for p in ("CUDAExecutionProvider", "DmlExecutionProvider", "CoreMLExecutionProvider",
                                        "CPUExecutionProvider") if p in ort.get_available_providers()]
            _SESSIONS["lama_onnx"] = ort.InferenceSession(chemin, providers=fournisseurs)
    return _SESSIONS["lama_onnx"]


def _lama_onnx(rgb, masque, cfg):
    s = _session_onnx(cfg)
    entrees = s.get_inputs()
    e_img = next((e for e in entrees if len(e.shape) == 4 and e.shape[1] == 3), entrees[0])
    e_msk = next((e for e in entrees if e is not e_img), entrees[-1])
    h, w = rgb.shape[:2]
    fixe = all(isinstance(d, int) for d in e_img.shape[2:])
    if fixe:
        th, tw = e_img.shape[2], e_img.shape[3]
    else:                                                  # taille libre : côté long ≤ 1024, multiple de 8
        k = min(1.0, 1024 / max(h, w))
        th, tw = max(8, int(h * k) // 8 * 8), max(8, int(w * k) // 8 * 8)
    # on travaille sur le cadre qui entoure les zones à effacer (plus de détails quand elles sont petites)
    ys, xs = np.nonzero(masque)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
    ch = min(h, max((y1 - y0) * 1.4, th))
    cw = min(w, max((x1 - x0) * 1.4, tw, ch * tw / th))
    ch = min(h, max(ch, cw * th / tw))
    y0, x0 = int(np.clip(cy - ch / 2, 0, h - ch)), int(np.clip(cx - cw / 2, 0, w - cw))
    y1, x1 = y0 + int(ch), x0 + int(cw)
    zone, zm = rgb[y0:y1, x0:x1], masque[y0:y1, x0:x1]
    im = cv2.resize(zone, (tw, th), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    mk = (cv2.resize(zm, (tw, th), interpolation=cv2.INTER_NEAREST) > 0).astype(np.float32)
    sortie = s.run(None, {e_img.name: im.transpose(2, 0, 1)[None], e_msk.name: mk[None, None]})[0][0]
    sortie = sortie.transpose(1, 2, 0)
    if sortie.max() <= 1.5:
        sortie = sortie * 255.0
    sortie = cv2.resize(np.clip(sortie, 0, 255).astype(np.uint8), (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
    out = rgb.copy()
    out[y0:y1, x0:x1] = sortie
    return out, "lama_onnx"


# ---------------------------------------------------------------- repli OpenCV
def _opencv(rgb, masque, cfg):
    h, w = rgb.shape[:2]
    m = (masque > 0).astype(np.uint8) * 255
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    rempli = bgr.copy()
    for f in (8, 4, 2):                                    # du grossier au fin : la structure, puis les bords
        petit = cv2.resize(rempli, (max(8, w // f), max(8, h // f)), interpolation=cv2.INTER_AREA)
        pm = cv2.resize(m, (petit.shape[1], petit.shape[0]), interpolation=cv2.INTER_NEAREST)
        petit = cv2.inpaint(petit, pm, 5, cv2.INPAINT_TELEA)
        grand = cv2.resize(petit, (w, h), interpolation=cv2.INTER_CUBIC)
        rempli = np.where(m[..., None] > 0, grand, bgr)
    rempli = cv2.inpaint(rempli, cv2.dilate(m, np.ones((3, 3), np.uint8)) - m, 3, cv2.INPAINT_TELEA) \
        if m.any() else rempli
    # grain : on reprend la texture fine de l'affiche pour que la zone ne paraisse pas lisse
    fin = bgr.astype(np.float32) - cv2.GaussianBlur(bgr, (0, 0), 1.5).astype(np.float32)
    sigma = float(fin[m == 0].std()) if (m == 0).any() else 0.0
    bruit = np.random.default_rng(0).normal(0, sigma * 0.8, rempli.shape).astype(np.float32)
    rempli = np.where(m[..., None] > 0, np.clip(rempli.astype(np.float32) + bruit, 0, 255), rempli).astype(np.uint8)
    return cv2.cvtColor(rempli, cv2.COLOR_BGR2RGB), "opencv"


def _lama_onnx_affine(rgb, masque, cfg):
    """LaMa ONNX en deux temps : toute l'affiche, puis chaque zone de près (plus de détails pour les petites)."""
    out, outil = _lama_onnx(rgb, masque, cfg)
    if not cfg.get("affinage", True):
        return out, outil
    h, w = masque.shape
    k = max(3, int(w * 0.03))
    groupes = cv2.dilate((masque > 0).astype(np.uint8), np.ones((k, k), np.uint8))
    n, etiquettes, stats, _ = cv2.connectedComponentsWithStats(groupes, 8)
    zones = sorted(range(1, n), key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    for i in zones[:12]:
        x, y, bw, bh, _ = stats[i]
        if bw * bh > 0.55 * w * h:                       # zone trop grande : la première passe suffit
            continue
        sous = np.where((etiquettes == i) & (masque > 0), 255, 0).astype(np.uint8)
        if not sous.any():
            continue
        try:
            out, _ = _lama_onnx(out, sous, cfg)
        except Exception:  # noqa: BLE001
            break
    return out, outil + "+affinage"


def _opencv_fsr(rgb, masque, cfg):
    if not hasattr(cv2, "xphoto"):
        raise ImportError("opencv-contrib absent")
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    m = np.where(masque > 0, 0, 255).astype(np.uint8)          # xphoto : 0 = à reconstruire
    h, w = masque.shape
    k = min(1.0, 700 / max(h, w))                                # FSR est lent : on travaille sur une version réduite
    petit = cv2.resize(bgr, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA) if k < 1 else bgr
    pm = cv2.resize(m, (petit.shape[1], petit.shape[0]), interpolation=cv2.INTER_NEAREST) if k < 1 else m
    dst = np.zeros_like(petit)
    cv2.xphoto.inpaint(petit, pm, dst, cv2.xphoto.INPAINT_FSR_FAST)
    if k < 1:
        dst = cv2.resize(dst, (w, h), interpolation=cv2.INTER_CUBIC)
    out = np.where((masque > 0)[..., None], dst, bgr)
    return cv2.cvtColor(out, cv2.COLOR_BGR2RGB), "opencv_fsr"


def _grain(img, rempli, masque, force):
    """Ajoute à la zone reconstruite le grain fin de l'affiche (une zone lisse se voit tout de suite)."""
    m = masque > 0
    if force <= 0 or m.mean() < 0.02 or (~m).sum() < 100:
        return rempli
    gris = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    fin = gris - cv2.GaussianBlur(gris, (0, 0), 1.2)
    sigma = float(np.std(fin[~m]))
    deja = cv2.cvtColor(rempli, cv2.COLOR_RGB2GRAY).astype(np.float32)
    sigma_zone = float(np.std((deja - cv2.GaussianBlur(deja, (0, 0), 1.2))[m]))
    manque = max(0.0, sigma - sigma_zone) * force
    if manque < 0.5:
        return rempli
    bruit = np.random.default_rng(1).normal(0, manque, rempli.shape[:2]).astype(np.float32)[..., None]
    out = rempli.astype(np.float32) + np.where(m[..., None], bruit, 0)
    return np.clip(out, 0, 255).astype(np.uint8)


MOTEURS = {"simple_lama": _simple_lama, "lama_onnx": _lama_onnx_affine, "opencv_fsr": _opencv_fsr, "opencv": _opencv}


def reconstruire(rgb, masque, cfg):
    """(image reconstruite, outil). cfg : section « reconstruction » de config.json."""
    if cv2 is None:
        raise OutilManquant("OpenCV manquant : pip install opencv-python-headless")
    if not masque.any():
        return rgb.copy(), "aucun"
    erreurs = []
    moteurs = list(cfg["moteurs"])
    if "opencv" in moteurs and "opencv_fsr" not in moteurs:      # repli de meilleure qualité avant OpenCV simple
        moteurs.insert(moteurs.index("opencv"), "opencv_fsr")
    for nom in moteurs:
        fn = MOTEURS.get(nom)
        if not fn:
            continue
        try:
            rempli, outil = fn(rgb, masque, cfg)
        except (ImportError, OutilManquant):
            continue
        except Exception as err:  # noqa: BLE001
            erreurs.append(f"{nom} : {err}")
            continue
        if rempli.shape != rgb.shape:                              # sécurité : jamais une image d'une autre taille
            rempli = cv2.resize(rempli, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
        rempli = _grain(rgb, rempli, masque, float(cfg.get("grain", 0.5)) if nom != "opencv" else 0)
        rayon = max(cfg.get("fondu", 5), int(round(rgb.shape[1] * 0.006)))
        return _fondre(rgb, rempli, masque, rayon), outil
    if not erreurs:
        raise OutilManquant("aucun outil de reconstruction installé : pip install opencv-python-headless onnxruntime")
    raise RuntimeError("reconstruction impossible (" + "; ".join(erreurs) + ")")
