"""Réglages techniques de la préparation des affiches (jeu « Affiche vidée », Pete).

Les réglages de jeu (préparation automatique, textes / personnages / sujet principal oui ou non…) sont dans
l'écran hôte (Réglages › Affiche vidée). Ceux-ci sont techniques : outils, modèles, marges. Ils sont lus dans
affiches/config.json (créé au premier lancement avec les valeurs par défaut ; modifiez-le librement,
une clé absente reprend sa valeur par défaut).
"""
import copy
import json
import os

DOSSIER_PAQUET = os.path.dirname(os.path.abspath(__file__))
DOSSIER_JEU = os.path.dirname(DOSSIER_PAQUET)
try:                                    # le dossier de données du jeu (réglages, affiches vidées, modèles)
    import config as _config
    DOSSIER_DONNEES = _config.DOSSIER_DONNEES
except ImportError:                     # outil lancé seul (python -m affiches)
    DOSSIER_DONNEES = DOSSIER_JEU
FICHIER = os.path.join(DOSSIER_DONNEES, "affiches_config.json")

VERSION = 2          # version 2 : nouveau traitement (masques nettoyés, affinage, halos) ; l'ancien fichier est remplacé
DEFAUTS = {
    "_aide": "Réglages techniques des affiches de Pete. Supprimez une clé pour revenir à sa valeur par défaut.",
    "version": VERSION,
    # dossier des affiches (relatif au dossier du jeu, ou chemin absolu)
    "dossier": "affiches_pete",
    # taille téléchargée sur TMDB (w500, w780 ou original) : plus grand = plus net, plus lent
    "taille_tmdb": "w780",
    # préférer une affiche « sans langue » de TMDB (presque toujours sans texte) quand elle existe
    "preferer_sans_texte": True,
    # nombre d'échecs (réseau, fichier illisible…) avant de laisser un film de côté
    "essais_max": 3,
    # passes de vérification : on cherche encore du texte et des personnages sur l'affiche reconstruite ;
    # s'il en reste (ou si la reconstruction en a inventé), on efface aussi ces zones et on recommence
    "verifications": 3,
    # part de l'affiche en dessous de laquelle un reste est négligé (poussière)
    "reste_min": 0.0015,
    # affiches candidates essayées (sans texte d'abord) : on garde celle qu'il faut le moins effacer ; au-delà de
    # part_max_affiche effacée, on essaie la suivante ; au-delà de part_refus, l'affiche est refusée (plus rien à voir)
    "candidats": 3,
    "part_max_affiche": 0.6,
    "part_refus": 0.93,
    # nettoyage du masque : trous fermés (zones prisonnières d'un personnage ou d'un titre), fentes refermées,
    # poussières oubliées (parts de l'affiche)
    "masque": {"trous_max": 0.04, "fermeture": 0.012, "poussiere": 0.0005},
    # dernière passe : les contours restés autour des zones effacées (halo d'un personnage) sont effacés aussi
    "halos": True,
    "texte": {
        # premiers outils disponibles utilisés, dans cet ordre
        "moteurs": ["rapidocr", "easyocr", "opencv"],
        "score_min": 0.25,
        # échelles supplémentaires (petits textes du générique, mentions légales)
        "echelles": [1.6, 2.2],
        # passe de plus sur l'affiche contrastée (textes pâles, gris sur gris, lettres fines)
        "contraste": True,
        # bas de l'affiche (part de la hauteur) repassé au détecteur OpenCV : le générique en lettres serrées
        "generique_bas": 0.25,
        # marge autour des lettres (part de la largeur de l'affiche)
        "marge": 0.02,
    },
    "personnages": {
        "moteurs": ["rembg", "mediapipe", "visages"],
        # modèles rembg : humains (prises de vue réelles), animation occidentale, anime japonais
        "modele_humains": "u2net_human_seg",
        "modele_animation": "isnet-general-use",
        "modele_anime": "isnet-anime",
        "seuil": 0.35,
        # contour (cheveux, bords flous) : les pixels plus faibles que le seuil mais reliés au personnage sont pris
        "seuil_halo": 0.12,
        "marge": 0.025,
        # une tache plus petite que cette part de l'affiche est ignorée (poussières)
        "aire_min": 0.002,
        # ajouter les visages trouvés par OpenCV (de face) à ce que le détourage a trouvé
        "visages": True,
    },
    "objets": {
        # sujet principal au premier plan (voiture, requin, vaisseau…) : détourage « tout sujet »
        "modele_objets": "isnet-general-use",
        "seuil": 0.45,
        "seuil_halo": 0.15,
        "marge": 0.025,
        "aire_min": 0.01,
        # au-delà de cette part de l'affiche, le « sujet » est le décor lui-même : on le garde
        "aire_max": 0.8,
    },
    "reconstruction": {
        "moteurs": ["simple_lama", "lama_onnx", "opencv"],
        "lama_onnx_url": "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx",
        # fondu (pixels) entre la zone reconstruite et l'affiche
        "fondu": 6,
        # LaMa ONNX : après une passe sur toute l'affiche, chaque zone est refaite de près (plus net)
        "affinage": True,
        # grain ajouté aux grandes zones reconstruites, pour qu'elles ne paraissent pas lisses (0 : aucun)
        "grain": 0.5,
    },
    "modeles": {
        "dossier": "modeles",
        "telechargement_auto": True,
        "mediapipe_url": "https://storage.googleapis.com/mediapipe-models/image_segmenter/deeplab_v3/float32/1/"
                         "deeplab_v3.tflite",
    },
}


def _fusion(base, ajout):
    for k, v in ajout.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _fusion(base[k], v)
        elif k in base:
            base[k] = v
    return base


def charger():
    r = copy.deepcopy(DEFAUTS)
    try:
        with open(FICHIER, encoding="utf-8") as f:
            lu = json.load(f)
        if not isinstance(lu, dict) or lu.get("version", 1) < VERSION:
            # ancien réglage technique : remplacé par les nouvelles valeurs (seul le dossier est gardé)
            if isinstance(lu, dict) and isinstance(lu.get("dossier"), str):
                r["dossier"] = lu["dossier"]
            with open(FICHIER, "w", encoding="utf-8") as f:
                json.dump(r, f, indent=2, ensure_ascii=False)
        else:
            _fusion(r, lu)
    except FileNotFoundError:
        try:
            with open(FICHIER, "w", encoding="utf-8") as f:
                json.dump(DEFAUTS, f, indent=2, ensure_ascii=False)
        except OSError:
            pass
    except (OSError, ValueError) as err:
        print(f"[affiches] config.json illisible ({err}) : valeurs par défaut utilisées.")
    return r


def chemin(rel):
    return rel if os.path.isabs(rel) else os.path.join(DOSSIER_DONNEES, rel)
