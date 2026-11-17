"""Les plans de Truman's Files (et de la Dame à la bûche), rangés en trois niveaux de difficulté.

Où sont les plans :
  - en ligne, sur la branche « plans » du dépôt GitHub du jeu (rien à copier : le jeu va les chercher) ;
    seules les images utilisées sont téléchargées, puis gardées dans donnees/plans_cache/ (le jeu marche aussi
    hors ligne avec ce qui a déjà été téléchargé) ;
  - et/ou dans le dossier plans/ du jeu (facultatif, prioritaire : pratique pour essayer de nouveaux plans).

Rangement (outils/preparer_plans.py le fait tout seul à partir d'un dossier ou d'un .zip) :
    <Titre (année) [tmdb-123]>/1_difficile/*.jpg
                               2_moyen/*.jpg
                               3_facile/*.jpg
    index.json   (en ligne : la liste des films et de leurs images, pour ne rien télécharger d'inutile)
L'ancien rangement (01.jpg, 02.jpg… du plus difficile au plus facile) est encore compris.
Un film est reconnu par son identifiant TMDB entre crochets, sinon par son titre et son année.
"""
import io
import json
import os
import random
import re
import threading
import time

import requests
from PIL import Image

import depot
from config import DOSSIER_PLANS, DOSSIER_PLANS_CACHE
from texte import cle

NIVEAUX = ("1_difficile", "2_moyen", "3_facile")
IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
ID_TMDB = re.compile(r"\[tmdb-(tv-)?(\d+)\]", re.I)
ANNEE = re.compile(r"\((\d{4})\)")
FRAIS = 6 * 3600                      # l'index en ligne est relu toutes les 6 h au plus
_VERROU = threading.Lock()


def analyser_dossier(nom):
    """« Alien (1979) [tmdb-348] » -> (("m", 348) ou None, "alien", 1979)"""
    m = ID_TMDB.search(nom)
    ident = (("tv" if m.group(1) else "m"), int(m.group(2))) if m else None
    reste = ID_TMDB.sub("", nom)
    a = ANNEE.search(reste)
    annee = int(a.group(1)) if a else None
    titre = ANNEE.sub("", reste).strip()
    return ident, cle(titre), annee


def ranger(fichiers):
    """Fichiers d'un film -> {niveau: [fichiers]}. Sous-dossiers de niveau, sinon numéros (01 = le plus dur)."""
    par = {n: sorted(f for f in fichiers if f.split("/")[0] == n) for n in NIVEAUX}
    if all(par.values()):
        return par
    plats = sorted(f for f in fichiers if "/" not in f)
    if len(plats) < 3:
        return None
    k = len(plats)
    return {n: plats[round(i * k / 3):round((i + 1) * k / 3)] for i, n in enumerate(NIVEAUX)}


class Entree:
    def __init__(self, dossier, niveaux, local=None):
        self.dossier, self.niveaux, self.local = dossier, niveaux, local
        self.ident, self.cle, self.annee = analyser_dossier(dossier)

    def images(self, niveaux=NIVEAUX):
        """Une image tirée au hasard dans chaque niveau demandé (dans l'ordre : du plus dur au plus facile)."""
        out = []
        for n in niveaux:
            choix = list(self.niveaux.get(n) or [])
            random.shuffle(choix)
            for f in choix[:3]:
                im = self._ouvrir(f)
                if im is not None:
                    out.append(im)
                    break
            else:
                return None
        return out

    def _ouvrir(self, f):
        if self.local:
            try:
                return Image.open(os.path.join(self.local, *f.split("/"))).convert("RGB")
            except OSError:
                return None
        cache = os.path.join(DOSSIER_PLANS_CACHE, self.dossier, *f.split("/"))
        if not os.path.isfile(cache):
            url = depot.url_brute(f"{self.dossier}/{f}", depot.infos()["branche_plans"])
            if not url:
                return None
            try:
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                os.makedirs(os.path.dirname(cache), exist_ok=True)
                with open(cache + ".tmp", "wb") as fh:
                    fh.write(r.content)
                os.replace(cache + ".tmp", cache)
            except (requests.RequestException, OSError):
                return None
        try:
            return Image.open(cache).convert("RGB")
        except OSError:
            return None


def _locales():
    out = []
    try:
        noms = sorted(os.listdir(DOSSIER_PLANS))
    except OSError:
        return out
    for nom in noms:
        chemin = os.path.join(DOSSIER_PLANS, nom)
        if nom.startswith(".") or not os.path.isdir(chemin):
            continue
        fichiers = []
        for racine, _, fs in os.walk(chemin):
            rel = os.path.relpath(racine, chemin)
            for f in fs:
                if os.path.splitext(f)[1].lower() in IMAGES:
                    fichiers.append(f if rel == "." else f"{rel.replace(os.sep, '/')}/{f}")
        niveaux = ranger(fichiers)
        if niveaux:
            out.append(Entree(nom, niveaux, local=chemin))
    return out


def _index_en_ligne():
    """L'index des plans en ligne (gardé dans le cache ; relu toutes les 6 h ; hors ligne : la dernière copie)."""
    copie = os.path.join(DOSSIER_PLANS_CACHE, "index.json")
    donnees = None
    try:
        recent = time.time() - os.path.getmtime(copie) < FRAIS
        with open(copie, encoding="utf-8") as f:
            donnees = json.load(f)
    except (OSError, ValueError):
        recent = False
    if not recent:
        url = depot.url_brute("index.json", depot.infos()["branche_plans"])
        if url:
            try:
                r = requests.get(url, timeout=8)
                r.raise_for_status()
                donnees = r.json()
                os.makedirs(DOSSIER_PLANS_CACHE, exist_ok=True)
                with open(copie, "w", encoding="utf-8") as f:
                    json.dump(donnees, f, ensure_ascii=False)
            except (requests.RequestException, ValueError, OSError):
                if donnees is not None:                  # on garde la vieille copie, on réessaiera plus tard
                    try:
                        os.utime(copie, None)
                    except OSError:
                        pass
    out = []
    for f in (donnees or {}).get("films", []):
        niveaux = f.get("niveaux") or {}
        if all(niveaux.get(n) for n in NIVEAUX):
            out.append(Entree(f["dossier"], {n: niveaux[n] for n in NIVEAUX}))
    return out


class Catalogue:
    def __init__(self):
        self.entrees = _locales() + _index_en_ligne()          # le dossier local passe avant
        self.par_id, self.par_titre = {}, {}
        for e in self.entrees:
            if e.ident:
                self.par_id.setdefault(e.ident, e)
            if e.cle:
                self.par_titre.setdefault(e.cle, []).append(e)

    def __len__(self):
        return len(self.entrees)

    def chercher(self, film, noms=(), annee=None):
        e = self.par_id.get(("tv" if film.get("tv") else "m", film.get("id")))
        if e:
            return e
        try:
            annee = int(str(annee or film.get("release_date", ""))[:4] or 0) or None
        except ValueError:
            annee = None
        for n in list(noms) + [film.get("title"), film.get("original_title")]:
            for c in self.par_titre.get(cle(n or ""), []):
                if not (c.annee and annee) or abs(c.annee - annee) <= 1:
                    return c
        return None


_CATALOGUE = [0.0, None]


def catalogue():
    """Le catalogue des plans (relu toutes les 60 s au plus : on peut ajouter des plans pendant que le jeu tourne)."""
    with _VERROU:
        if _CATALOGUE[1] is None or time.time() - _CATALOGUE[0] > 60:
            _CATALOGUE[:] = [time.time(), Catalogue()]
        return _CATALOGUE[1]
