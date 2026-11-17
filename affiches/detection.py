"""Détection de ce qu'il faut effacer sur une affiche : textes (titre, slogan, générique, logos écrits)
et personnages (humains, personnages animés). Chaque fonction rend un masque numpy (uint8, 255 = à effacer)
et le nom de l'outil utilisé ; les outils sont essayés dans l'ordre de config.json, le premier disponible gagne.

Outils (tous gratuits et libres, exécutés en local) :
  textes      rapidocr (PaddleOCR en ONNX, modèles inclus)  ·  easyocr  ·  opencv (repli sans modèle, moins précis)
  personnages rembg (U²-Net / IS-Net, modèles téléchargés une fois)  ·  mediapipe (DeepLab v3)  ·
              visages (OpenCV, repli grossier : visage + silhouette estimée)
"""
import os
import threading

import numpy as np

from . import modeles

try:
    import cv2
except ImportError:                         # opencv est indispensable à la préparation des affiches
    cv2 = None

_SESSIONS, _VERROU = {}, threading.Lock()
GENRE_ANIMATION = 16


OutilManquant = modeles.OutilManquant     # aucun outil utilisable : la préparation s'arrête (pas d'échec compté)


def _exiger_cv2():
    if cv2 is None:
        raise OutilManquant("OpenCV manquant : pip install opencv-python-headless")


def _dilater(masque, rayon):
    rayon = max(1, int(rayon))
    noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rayon + 1, 2 * rayon + 1))
    return cv2.dilate(masque, noyau)


def hysteresis(doux, seuil, seuil_halo):
    """Masque à deux seuils : le cœur (≥ seuil) et tout ce qui lui est relié au-dessus de seuil_halo (cheveux, bords
    flous, ombres portées) : c'est ce qui laisse sinon un halo du personnage autour de la zone effacée."""
    coeur = doux >= seuil * 255
    if not seuil_halo or seuil_halo >= seuil:
        return coeur.astype(np.uint8) * 255
    large = (doux >= seuil_halo * 255).astype(np.uint8)
    n, etiquettes = cv2.connectedComponents(large, connectivity=8)
    gardes = np.unique(etiquettes[coeur])
    gardes = gardes[gardes > 0]
    return np.isin(etiquettes, gardes).astype(np.uint8) * 255


def _sans_poussieres(masque, aire_min):
    n, etiquettes, stats, _ = cv2.connectedComponentsWithStats((masque > 0).astype(np.uint8), 8)
    out = np.zeros_like(masque)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= aire_min:
            out[etiquettes == i] = 255
    return out


# ====================================================================== textes
def _boites_rapidocr(bgr, score_min):
    try:
        from rapidocr_onnxruntime import RapidOCR          # rapidocr 1.x
        nouveau = False
    except ImportError:
        from rapidocr import RapidOCR                      # rapidocr 2.x / 3.x
        nouveau = True
    with _VERROU:
        if "rapidocr" not in _SESSIONS:
            _SESSIONS["rapidocr"] = RapidOCR()
    moteur = _SESSIONS["rapidocr"]
    if nouveau:
        res = moteur(bgr)
        boites = getattr(res, "boxes", None)
        return [] if boites is None else [np.asarray(b, dtype=np.float32) for b in boites]
    boites = []
    try:                                                  # détection seule : attrape aussi les titres stylisés
        res, _ = moteur(bgr, use_det=True, use_cls=False, use_rec=False)
    except TypeError:
        res, _ = moteur(bgr)
    for it in res or []:
        b = it[0] if isinstance(it, (list, tuple)) and len(it) in (2, 3) and np.asarray(it[0]).shape == (4, 2) else it
        b = np.asarray(b, dtype=np.float32)
        if b.shape == (4, 2):
            if isinstance(it, (list, tuple)) and len(it) == 3 and isinstance(it[2], (int, float)) and it[2] < score_min:
                continue
            boites.append(b)
    return boites


def _boites_easyocr(bgr, score_min):
    import easyocr
    with _VERROU:
        if "easyocr" not in _SESSIONS:
            try:
                import torch
                gpu = torch.cuda.is_available()
            except ImportError:
                gpu = False
            _SESSIONS["easyocr"] = easyocr.Reader(["en", "fr"], gpu=gpu, verbose=False)
    horizontales, libres = _SESSIONS["easyocr"].detect(bgr, text_threshold=max(0.3, score_min))
    boites = [np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32) for x0, x1, y0, y1 in horizontales[0]]
    boites += [np.asarray(p, np.float32) for p in libres[0]]
    return boites


def _boites_opencv(bgr, _score):
    """Repli sans modèle : lignes de texte = bandes horizontales très denses en contours fins (gradient
    morphologique), regroupées lettre à lettre. Moins précis qu'un vrai détecteur : titres très stylisés manqués."""
    gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gris.shape
    grad = cv2.morphologyEx(gris, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    _, bin_ = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    bin_ = cv2.bitwise_and(bin_, (grad > 40).astype(np.uint8) * 255)          # contours vraiment nets
    lignes = cv2.morphologyEx(bin_, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, w // 40), 3)))
    lignes = cv2.morphologyEx(lignes, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    n, _, stats, _ = cv2.connectedComponentsWithStats(lignes, 8)
    boites = []
    for i in range(1, n):
        x, y, bw, bh, aire = stats[i]
        if not (h * 0.008 <= bh <= h * 0.14) or bw < 1.8 * bh or bw < w * 0.06:
            continue
        zone = bin_[y:y + bh, x:x + bw]
        densite = zone.mean() / 255
        # du texte : beaucoup de contours fins, réguliers, et des « trous » entre les lettres
        if 0.18 <= densite <= 0.75 and aire >= 0.45 * bw * bh:
            boites.append([x, y, x + bw, y + bh])
    # morceaux d'une même ligne (coupée par un motif de l'affiche) : on les réunit
    boites.sort()
    fusion = []
    for b in boites:
        for f in fusion:
            haut = min(f[3], b[3]) - max(f[1], b[1])
            hmin = min(f[3] - f[1], b[3] - b[1])
            if haut >= 0.5 * hmin and b[0] - f[2] <= 2.5 * hmin:
                f[:] = [min(f[0], b[0]), min(f[1], b[1]), max(f[2], b[2]), max(f[3], b[3])]
                break
        else:
            fusion.append(list(b))
    return [np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32) for x0, y0, x1, y1 in fusion]


MOTEURS_TEXTE = {"rapidocr": _boites_rapidocr, "easyocr": _boites_easyocr, "opencv": _boites_opencv}


def _contraste(bgr):
    """Affiche contrastée localement (CLAHE sur la luminance) : fait ressortir les textes pâles ou fins."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _boites_multi(fn, bgr, cfg):
    """Boîtes de texte à plusieurs échelles : l'image entière, puis agrandie (petits textes du générique), puis
    contrastée (textes pâles)."""
    h, w = bgr.shape[:2]
    boites = list(fn(bgr, cfg["score_min"]))
    if cfg.get("contraste", True):
        try:
            boites += list(fn(_contraste(bgr), cfg["score_min"]))
        except Exception:  # noqa: BLE001
            pass
    for k in cfg.get("echelles", [1.6]):
        if k <= 1 or max(h, w) * k > 2600:
            continue
        grand = cv2.resize(bgr, (int(w * k), int(h * k)), interpolation=cv2.INTER_CUBIC)
        boites += [np.asarray(b, np.float32) / k for b in fn(grand, cfg["score_min"])]
    return boites


def _elargir(b, fx=0.45, fy=0.18):
    """Agrandit une boîte de texte (4 points) : les détecteurs rognent souvent la première et la dernière lettre."""
    b = np.asarray(b, np.float32)
    c = b.mean(axis=0)
    haut = max(1.0, float(np.linalg.norm(b[3] - b[0])), float(np.linalg.norm(b[2] - b[1])))
    larg = max(1.0, float(np.linalg.norm(b[1] - b[0])))
    ux = (b[1] - b[0]) / larg
    uy = (b[3] - b[0]) / haut
    out = b.copy()
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        out[i] = b[i] + ux * sx * fx * haut + uy * sy * fy * haut
    return out if np.isfinite(out).all() else b


def _relier_lignes(m, w):
    """Réunit les lettres d'une même ligne (les espaces entre les mots sont effacés aussi)."""
    k = max(3, int(w * 0.02))
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (k, max(3, k // 3))))


def masque_texte(img_rgb, cfg):
    """Masque des textes et logos écrits. cfg : section « texte » de config.json.
    Le premier outil disponible fait le gros du travail (à deux échelles) ; le détecteur OpenCV repasse en plus sur
    le bas de l'affiche, où le générique en lettres serrées échappe parfois aux modèles."""
    _exiger_cv2()
    bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    erreurs, manquants = [], []
    for nom in cfg["moteurs"]:
        fn = MOTEURS_TEXTE.get(nom)
        if not fn:
            continue
        try:
            boites = _boites_multi(fn, bgr, cfg) if nom != "opencv" else fn(bgr, cfg["score_min"])
        except ImportError:
            continue
        except OutilManquant as err:
            manquants.append(f"{nom} : {err}")
            continue
        except Exception as err:  # noqa: BLE001
            erreurs.append(f"{nom} : {err}")
            continue
        m = np.zeros((h, w), np.uint8)
        for b in boites:
            cv2.fillPoly(m, [np.round(_elargir(b)).astype(np.int32)], 255)
        if nom != "opencv" and cfg.get("generique_bas", 0.25) > 0:
            y0 = int(h * (1 - cfg.get("generique_bas", 0.25)))
            for b in _boites_opencv(bgr[y0:], 0):
                b = np.asarray(b, np.float32) + np.array([0, y0], np.float32)
                cv2.fillPoly(m, [np.round(_elargir(b)).astype(np.int32)], 255)
        return _dilater(_relier_lignes(m, w), cfg["marge"] * w), nom
    if not erreurs:
        raise OutilManquant("aucun outil de détection de texte utilisable : pip install rapidocr_onnxruntime"
                            + (f" ({'; '.join(manquants)})" if manquants else ""))
    raise RuntimeError("détection du texte impossible (" + "; ".join(erreurs) + ")")


# ====================================================================== personnages
def _modele_rembg(cfg, film):
    if GENRE_ANIMATION in (film.get("genre_ids") or []):
        return cfg["modele_anime"] if film.get("langue") == "ja" else cfg["modele_animation"]
    return cfg["modele_humains"]


def _personnages_rembg(rgb, cfg, film):
    from PIL import Image
    from rembg import new_session, remove
    modele = _modele_rembg(cfg, film)
    with _VERROU:
        if ("rembg", modele) not in _SESSIONS:
            _SESSIONS[("rembg", modele)] = new_session(modele)
    m = remove(Image.fromarray(rgb), session=_SESSIONS[("rembg", modele)], only_mask=True, post_process_mask=False)
    m = np.asarray(m.convert("L").resize((rgb.shape[1], rgb.shape[0])))
    return hysteresis(m, cfg["seuil"], cfg.get("seuil_halo", 0)), f"rembg:{modele}"


def _objets_rembg(rgb, cfg, film):
    """Le sujet principal de l'affiche (objet, véhicule, créature…) : détourage « tout sujet »."""
    from PIL import Image
    from rembg import new_session, remove
    modele = cfg.get("modele_objets", "isnet-general-use")
    with _VERROU:
        if ("rembg", modele) not in _SESSIONS:
            _SESSIONS[("rembg", modele)] = new_session(modele)
    m = remove(Image.fromarray(rgb), session=_SESSIONS[("rembg", modele)], only_mask=True, post_process_mask=False)
    m = np.asarray(m.convert("L").resize((rgb.shape[1], rgb.shape[0])))
    return hysteresis(m, cfg["seuil"], cfg.get("seuil_halo", 0)), f"rembg:{modele}"


def _personnages_mediapipe(rgb, cfg, film):
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    url = cfg.get("_mediapipe_url")
    chemin = modeles.obtenir(url, "deeplab_v3.tflite")
    with _VERROU:
        if "mediapipe" not in _SESSIONS:
            opts = vision.ImageSegmenterOptions(base_options=mp_python.BaseOptions(model_asset_path=chemin),
                                                output_category_mask=True)
            _SESSIONS["mediapipe"] = vision.ImageSegmenter.create_from_options(opts)
    res = _SESSIONS["mediapipe"].segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
    cat = res.category_mask.numpy_view()
    classes = {15}                                        # personne (PASCAL VOC)
    if GENRE_ANIMATION in (film.get("genre_ids") or []) or cfg.get("_objets"):
        classes |= {3, 8, 10, 12, 13, 17}                 # oiseau, chat, vache, chien, cheval, mouton
    if cfg.get("_objets"):
        classes |= {1, 2, 4, 6, 7, 14, 19}                # avion, vélo, bateau, bus, voiture, moto, train
    m = np.isin(cat, list(classes)).astype(np.uint8) * 255
    return cv2.resize(m, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST), "mediapipe:deeplab_v3"


def _personnages_visages(rgb, cfg, film):
    """Repli grossier : chaque visage trouvé + une silhouette estimée sous le visage."""
    fichier = getattr(cv2, "data", None) and cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(fichier) if fichier and os.path.isfile(fichier) else None
    if cascade is None or cascade.empty():
        raise ImportError("détecteur de visages OpenCV absent")
    gris = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = gris.shape
    m = np.zeros((h, w), np.uint8)
    for (x, y, fw, fh) in cascade.detectMultiScale(gris, 1.1, 6, minSize=(max(20, w // 30),) * 2):
        cx = x + fw // 2
        cv2.ellipse(m, (cx, y + fh // 2), (int(fw * 0.75), int(fh * 0.95)), 0, 0, 360, 255, -1)
        cv2.rectangle(m, (max(0, cx - int(fw * 1.4)), y + int(fh * 0.8)), (min(w, cx + int(fw * 1.4)), min(h, y + fh * 6)), 255, -1)
    return m, "visages"


MOTEURS_PERSONNAGES = {"rembg": _personnages_rembg, "mediapipe": _personnages_mediapipe, "visages": _personnages_visages}


def masque_visages(img_rgb, cfg=None):
    """Visages oubliés (de face) : contrôle d'appoint, ajouté au masque des personnages."""
    _exiger_cv2()
    try:
        m, _ = _personnages_visages(img_rgb, cfg or {}, {})
    except ImportError:
        return np.zeros(img_rgb.shape[:2], np.uint8)
    return m


def masque_objets(img_rgb, cfg, film, cfg_modeles=None):
    """Masque du sujet principal (au premier plan). Ignoré s'il couvre presque toute l'affiche (c'est alors le
    décor lui-même). Retourne (masque, outil) ; masque vide si aucun outil n'est installé."""
    _exiger_cv2()
    h, w = img_rgb.shape[:2]
    vide = np.zeros((h, w), np.uint8)
    for fn in (_objets_rembg, _personnages_mediapipe):
        try:
            m, outil = fn(img_rgb, dict(cfg, _objets=True, _mediapipe_url=(cfg_modeles or {}).get("mediapipe_url")),
                          film)
        except (ImportError, OutilManquant):
            continue
        except Exception:  # noqa: BLE001
            continue
        m = _sans_poussieres(m, cfg["aire_min"] * w * h)
        if (m > 0).mean() > cfg.get("aire_max", 0.8):
            return vide, outil + " (ignoré : tout le décor)"
        return _dilater(m, cfg["marge"] * w), outil
    return vide, "aucun"


def masque_personnages(img_rgb, cfg, film, cfg_modeles=None):
    """Masque des personnages (humains ou animés). cfg : section « personnages » de config.json.
    Les visages trouvés par OpenCV s'y ajoutent (un visage oublié par le détourage est quand même effacé)."""
    _exiger_cv2()
    cfg = dict(cfg, _mediapipe_url=(cfg_modeles or {}).get("mediapipe_url"))
    h, w = img_rgb.shape[:2]
    erreurs, manquants = [], []
    for nom in cfg["moteurs"]:
        fn = MOTEURS_PERSONNAGES.get(nom)
        if not fn:
            continue
        try:
            m, outil = fn(img_rgb, cfg, film)
        except ImportError:
            continue
        except OutilManquant as err:
            manquants.append(f"{nom} : {err}")
            continue
        except Exception as err:  # noqa: BLE001
            erreurs.append(f"{nom} : {err}")
            continue
        m = _sans_poussieres(m, cfg["aire_min"] * w * h)
        if nom != "visages" and cfg.get("visages", True):
            m |= masque_visages(img_rgb)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        return _dilater(m, cfg["marge"] * w), outil
    if not erreurs:
        raise OutilManquant("aucun outil de détection des personnages utilisable : pip install rembg"
                            + (f" ({'; '.join(manquants)})" if manquants else ""))
    raise RuntimeError("détection des personnages impossible (" + "; ".join(erreurs) + ")")


def outils_disponibles():
    """Pour l'écran des réglages : quels outils sont installés (sans les charger)."""
    import importlib.util as u
    ok = lambda m: u.find_spec(m) is not None   # noqa: E731
    return {
        "opencv": cv2 is not None,
        "texte": list(dict.fromkeys(n for n, m in (("rapidocr", "rapidocr_onnxruntime"), ("rapidocr", "rapidocr"), ("easyocr", "easyocr"))
                                    if ok(m))) + (["opencv"] if cv2 is not None else []),
        "personnages": [n for n, m in (("rembg", "rembg"), ("mediapipe", "mediapipe")) if ok(m)] +
                       (["visages"] if cv2 is not None and getattr(cv2, "data", None) and os.path.isfile(
                           cv2.data.haarcascades + "haarcascade_frontalface_default.xml") else []),
        "reconstruction": [n for n, m in (("simple_lama", "simple_lama_inpainting"), ("lama_onnx", "onnxruntime"))
                           if ok(m)] + (["opencv"] if cv2 is not None else []),
    }
