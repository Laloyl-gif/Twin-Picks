"""Traitement d'une affiche : téléchargement, détection, reconstruction, puis vérification.

    affiches candidates (TMDB, « sans langue » d'abord, donc sans texte ; puis l'officielle)
      -> pour chacune : masque des textes (plusieurs échelles + passe contrastée), des personnages (contours flous
         compris), du sujet principal ; on garde l'affiche qu'il faut le moins effacer
      -> masque nettoyé : trous refermés (le décor prisonnier entre les bras d'un personnage ou dans les lettres
         d'un titre part avec eux), fentes refermées, poussières retirées
      -> reconstruction (LaMa, affinée zone par zone) + grain de l'affiche
      -> vérification : textes, personnages et visages cherchés à nouveau sur le résultat ; s'il en reste (ou si la
         reconstruction en a inventé), ces zones s'ajoutent au masque et l'on reconstruit depuis l'originale
      -> halos : les contours nets restés au bord des zones effacées (silhouette fantôme) sont effacés à leur tour
      -> videes/<Titre (année)>.png  +  masques/<Titre (année)>.png  +  entrée du catalogue
Il n'y a pas de limite à ce qui est effacé : il ne doit rester que le décor (une affiche presque entièrement
effacée est refusée : il n'y aurait plus rien à voir).
"""
import io
import os
import time

import numpy as np
import requests
from PIL import Image

from tmdb import URL_IMG, affiches_film
from . import detection, reconstruction, reglages
from .catalogue import VERSION_TRAITEMENT, ecrire_atomique

try:
    import cv2
except ImportError:
    cv2 = None

RATIO_AFFICHE = (0.6, 0.75)          # largeur / hauteur d'une affiche de cinéma (2:3 ≈ 0,67)


def _telecharger(api, chemin_tmdb, taille):
    erreur = None
    for essai in range(3):                             # coupure réseau passagère : on réessaie
        try:
            r = api.http.get(URL_IMG + taille + chemin_tmdb, timeout=30)
            r.raise_for_status()
            data = r.content
            Image.open(io.BytesIO(data)).verify()      # fichier complet et lisible
            return data
        except (requests.RequestException, OSError, SyntaxError) as err:
            erreur = err
            time.sleep(1.5 * (essai + 1))
    raise RuntimeError(f"téléchargement impossible : {erreur}")


def choisir_affiches(api, film, preferer_sans_texte, nombre=3):
    """[(chemin TMDB, sans_texte)] : les affiches « sans langue » les mieux notées (si on les préfère), puis
    l'officielle. On essaiera chacune et l'on gardera celle qu'il faut le moins effacer."""
    out = []
    if preferer_sans_texte:
        try:
            for p in affiches_film(api, film):
                if p["langue"] is None and p["hauteur"] and RATIO_AFFICHE[0] <= p["largeur"] / p["hauteur"] <= RATIO_AFFICHE[1]:
                    out.append((p["chemin"], True))
                if len(out) >= max(1, nombre - 1):
                    break
        except Exception:  # noqa: BLE001
            pass
    chemin = film.get("poster_path")
    if not chemin:
        try:
            from tmdb import details_film
            chemin = details_film(api, film).get("affiche")
        except Exception:  # noqa: BLE001
            chemin = None
    if chemin and chemin not in [c for c, _ in out]:
        out.append((chemin, False))
    if not out:
        raise RuntimeError("aucune affiche sur TMDB")
    return out[:max(1, nombre)]


def choisir_affiche(api, film, preferer_sans_texte):
    """Compatibilité : la première affiche candidate."""
    return choisir_affiches(api, film, preferer_sans_texte, 1)[0]


# ---------------------------------------------------------------- masques
def nettoyer_masque(masque, cfg):
    """Fentes refermées, trous fermés (décor prisonnier d'un personnage ou d'un titre), poussières retirées."""
    if cv2 is None or not masque.any():
        return masque
    h, w = masque.shape
    c = cfg.get("masque", {})
    m = (masque > 0).astype(np.uint8) * 255
    k = max(3, int(w * c.get("fermeture", 0.012)) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    # trous : zones non effacées entièrement entourées d'effacé, et petites
    fond = (m == 0).astype(np.uint8)
    n, etiquettes, stats, _ = cv2.connectedComponentsWithStats(fond, 4)
    maxi = c.get("trous_max", 0.04) * h * w
    for i in range(1, n):
        x, y, bw, bh, aire = stats[i]
        if aire <= maxi and x > 0 and y > 0 and x + bw < w and y + bh < h:
            m[etiquettes == i] = 255
    # poussières : petites taches effacées isolées (souvent un faux positif, parfois un reste de lettre)
    mini = c.get("poussiere", 0.0005) * h * w
    n, etiquettes, stats, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), 8)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < mini:
            zone = etiquettes == i
            # une poussière collée au bord de l'affiche est souvent un reste de générique : on la garde
            if not (zone[:, :2].any() or zone[:, -2:].any() or zone[-2:].any()):
                m[zone] = 0
    return m


def masques(img, film, opts, cfg, journal=print):
    """Masque de tout ce qu'il faut effacer (nettoyé) + outils utilisés."""
    h, w = img.shape[:2]
    masque, outils = np.zeros((h, w), np.uint8), {}
    if opts.get("textes", True):
        journal("Recherche des textes…")
        mt, outils["texte"] = detection.masque_texte(img, cfg["texte"])
        masque |= mt
    if opts.get("personnages", True):
        journal("Recherche des personnages…")
        mp_, outils["personnages"] = detection.masque_personnages(img, cfg["personnages"], film, cfg["modeles"])
        masque |= mp_
    if opts.get("objets", True):
        try:
            mo, outils["objets"] = detection.masque_objets(img, cfg["objets"], film, cfg["modeles"])
            masque |= mo
        except detection.OutilManquant:
            raise
        except Exception as err:  # noqa: BLE001  (le sujet principal est un bonus : on continue sans)
            outils["objets"] = f"échec : {err}"[:120]
    return nettoyer_masque(masque, cfg), outils


def halos(out, masque, cfg):
    """Contours nets restés juste autour des zones effacées (silhouette d'un personnage, bord d'un titre) : le masque
    à ajouter, ou None. Une seule bande étroite autour des zones, et jamais plus de 4 % de l'affiche."""
    if cv2 is None or not cfg.get("halos", True) or not masque.any():
        return None
    h, w = masque.shape
    m = masque > 0
    r = max(3, int(w * 0.015))
    anneau = cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
    anneau &= ~m
    gris = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY)
    grad = cv2.morphologyEx(gris, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    hors = grad[~m & ~anneau]
    if hors.size < 100:
        return None
    seuil = max(45.0, float(np.percentile(hors, 94)))
    cand = ((grad > seuil) & anneau).astype(np.uint8)
    # on ne garde que les morceaux qui touchent une zone effacée (un contour du décor plus loin reste)
    bord = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    n, etiquettes = cv2.connectedComponents(cand, connectivity=8)
    if n <= 1:
        return None
    touchent = np.unique(etiquettes[bord & (cand > 0)])
    touchent = touchent[touchent > 0]
    ajout = np.isin(etiquettes, touchent)
    if ajout.sum() < 12 or ajout.mean() > 0.04:
        return None
    ajout = cv2.dilate(ajout.astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    return ajout


def verifier(out, masque, film, opts, cfg, journal=print):
    """Cherche ce qui reste à effacer sur l'affiche reconstruite : le masque à ajouter, ou None si tout est propre."""
    h, w = out.shape[:2]
    nouveau = np.zeros((h, w), np.uint8)
    if opts.get("textes", True):
        try:
            nouveau |= detection.masque_texte(out, cfg["texte"])[0]
        except detection.OutilManquant:
            pass
    if opts.get("personnages", True):
        try:
            nouveau |= detection.masque_personnages(out, cfg["personnages"], film, cfg["modeles"])[0]
        except detection.OutilManquant:
            pass
    neuf = (nouveau > 0) & ~(masque > 0)               # seulement ce qui n'était pas déjà effacé
    part = float(neuf.mean())
    if part < cfg.get("reste_min", 0.0015):
        return None
    journal(f"Vérification : il reste {part * 100:.1f} % à effacer, nouvelle passe…")
    return nouveau


def _ouvrir(data):
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))


def traiter(api, film, cat, opts, journal=print):
    """Traite un film (l'entrée du catalogue doit exister). opts : {textes, personnages}. Retourne l'entrée."""
    cfg = reglages.charger()
    e = cat.entree(film)
    cat.maj(film, statut="en_cours", debut=time.strftime("%Y-%m-%d %H:%M"))
    try:
        # 1. l'affiche : celle déjà téléchargée, sinon les candidates (on garde celle qu'il faut le moins effacer)
        chemin_orig = cat.chemin(e["originale"])
        if os.path.isfile(chemin_orig):
            with open(chemin_orig, "rb") as fh:
                data = fh.read()
            img = _ouvrir(data)
            masque, outils = masques(img, film, opts, cfg, journal)
        else:
            meilleur = None
            cands = choisir_affiches(api, film, cfg["preferer_sans_texte"], int(cfg.get("candidats", 3)))
            for k, (source, sans_texte) in enumerate(cands, 1):
                if len(cands) > 1:
                    journal(f"Affiche {k}/{len(cands)}…")
                try:
                    data = _telecharger(api, source, cfg["taille_tmdb"])
                    img = _ouvrir(data)
                    m, outils = masques(img, film, opts, cfg, journal)
                except detection.OutilManquant:
                    raise
                except Exception as err:  # noqa: BLE001
                    journal(f"Affiche {k} écartée : {err}")
                    continue
                part = float((m > 0).mean())
                if meilleur is None or part < meilleur[0]:
                    meilleur = (part, data, img, m, outils, source, sans_texte)
                if part <= cfg.get("part_max_affiche", 0.6):
                    break
            if meilleur is None:
                raise RuntimeError("aucune affiche exploitable")
            _, data, img, masque, outils, source, sans_texte = meilleur
            ecrire_atomique(chemin_orig, data)
            cat.maj(film, source=source, sans_texte=sans_texte)
        if float((masque > 0).mean()) > cfg.get("part_refus", 0.93):
            raise RuntimeError("affiche presque entièrement effacée : il ne resterait rien à voir")

        # 2. reconstruction, puis vérification du résultat
        journal("Reconstruction du décor…")
        out, outils["reconstruction"] = reconstruction.reconstruire(img, masque, cfg["reconstruction"])
        passes = 0
        for passes in range(1, int(cfg.get("verifications", 3)) + 1):
            reste = verifier(out, masque, film, opts, cfg, journal)
            if reste is None:
                break
            masque = nettoyer_masque(masque | reste, cfg)
            out, _ = reconstruction.reconstruire(img, masque, cfg["reconstruction"])
        outils["verifications"] = passes

        # 3. halos : les contours restés au bord des zones effacées partent aussi (une passe)
        reste = halos(out, masque, cfg)
        if reste is not None:
            journal("Nettoyage des contours restants…")
            masque = masque | reste
            out, _ = reconstruction.reconstruire(img, masque, cfg["reconstruction"])
            outils["halos"] = True
        part = round(float((masque > 0).mean()), 4)

        # 4. écriture (jamais par-dessus une affiche prête : le catalogue l'a vérifié avant d'appeler traiter)
        buf = io.BytesIO()
        Image.fromarray(out).save(buf, "PNG", optimize=True)
        ecrire_atomique(cat.chemin(e["videe"]), buf.getvalue())
        buf = io.BytesIO()
        Image.fromarray(masque).save(buf, "PNG", optimize=True)
        ecrire_atomique(cat.chemin(e["masque"]), buf.getvalue())
        return cat.maj(film, statut="pret", part=part, outils=outils, version=VERSION_TRAITEMENT, erreur="",
                       options={k: bool(v) for k, v in opts.items()}, date=time.strftime("%Y-%m-%d %H:%M"))
    except detection.OutilManquant:
        cat.maj(film, statut="a_faire")                    # pas la faute du film : il sera traité plus tard
        raise
    except Exception as err:  # noqa: BLE001
        e = cat.entree(film)
        cat.maj(film, statut="echec", essais=e.get("essais", 0) + 1, erreur=str(err)[:300])
        raise
