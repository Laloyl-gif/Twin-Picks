"""Préparation des affiches vidées (Pete), en arrière-plan.

Principe : toutes les affiches des films choisis (listes de Pete, ou films vus par les joueurs présents) sont
préparées, sauf celles qui existent déjà : elles sont simplement réutilisées.
  1. les affiches déjà prêtes (catalogue + fichier présent) comptent d'office ;
  2. les autres sont traitées dans un ordre stable (les plus connues d'abord, ou un « hasard » qui reste le même
     d'une fois à l'autre) ; changer de listes ne traite que les nouveaux films ;
  3. un film en échec est retenté au plus essais_max fois ; un outil manquant arrête tout (rien n'est compté
     en échec) ; arrêter la préparation ne perd rien (l'affiche en cours sera refaite au prochain lancement).
"""
import hashlib
import threading
import time
import traceback

from . import catalogue as catalogue_mod
from . import detection, pipeline, reglages

ORDRES = {"connus": "Les plus connus d'abord", "hasard": "Au hasard (toujours le même ordre)"}


def _cle(f):
    return catalogue_mod.cle(f)


def _ordre(films, ordre):
    if ordre == "hasard":
        return sorted(films, key=lambda f: hashlib.sha1(_cle(f).encode()).hexdigest())
    return sorted(films, key=lambda f: (-(f.get("votes") or 0), -(f.get("popularite") or 0)))


class Preparateur:
    def __init__(self):
        self.verrou = threading.Lock()
        self.thread, self.stop = None, threading.Event()
        self._etat = {"actif": False, "voulu": 0, "prets": None, "traites": 0, "echecs": 0, "a_traiter": 0,
                      "courant": "", "etape": "", "message": "", "erreur": "", "fin": ""}
        self.signature = None                      # ce que la préparation en cours (ou la dernière) a reçu

    # ---------- accès ----------
    def catalogue(self):
        return catalogue_mod.ouvrir(reglages.chemin(reglages.charger()["dossier"]))

    def pretes(self, films, part_max=1.0):
        cat = self.catalogue()
        vus, out = set(), []
        for f in films:
            k = _cle(f)
            if k not in vus and cat.utilisable(f, part_max):
                vus.add(k)
                out.append(f)
        return out

    def actif(self):
        return bool(self.thread and self.thread.is_alive())

    def etat(self):
        with self.verrou:
            e = dict(self._etat)
        e["actif"] = self.actif()
        e["dossier"] = reglages.chemin(reglages.charger()["dossier"])
        return e

    def _maj(self, **champs):
        with self.verrou:
            self._etat.update(champs)

    # ---------- commandes ----------
    def lancer(self, api, films, opts, ordre="connus", nombre=None, signature=None):
        """Démarre la préparation de toutes les affiches de `films` (ou des `nombre` premières), sans attendre.
        Retourne False si une préparation tourne déjà."""
        if self.actif():
            return False
        self.stop.clear()
        films = list(films)
        nombre = len({_cle(f) for f in films if f.get("id")}) if nombre is None else int(nombre)
        self.signature = signature
        self._maj(actif=True, voulu=nombre, traites=0, echecs=0, courant="", etape="", erreur="", fin="",
                  message="Recherche des affiches déjà prêtes…")
        self.thread = threading.Thread(target=self._tourner, args=(api, films, nombre, dict(opts), 1.0, ordre),
                                       daemon=True)
        self.thread.start()
        return True

    def arreter(self, attendre=0):
        self.stop.set()
        if attendre and self.thread:
            self.thread.join(attendre)

    def attendre(self, films, part_max, exclus=(), delai=900):
        """Pour une manche : attend qu'au moins une affiche hors `exclus` soit prête (ou que la préparation
        s'arrête). Retourne les films prêts hors exclus."""
        fin = time.time() + delai
        while True:
            prets = [f for f in self.pretes(films, part_max) if _cle(f) not in exclus]
            if prets or not self.actif() or time.time() > fin:
                return prets
            time.sleep(1.0)

    # ---------- travail ----------
    def _tourner(self, api, films, nombre, opts, part_max, ordre):
        try:
            self._preparer(api, films, nombre, opts, part_max, ordre)
        except Exception as err:  # noqa: BLE001
            traceback.print_exc()
            self._maj(erreur=str(err), message=f"Préparation interrompue : {err}")
        finally:
            self._maj(actif=False, courant="", etape="", fin=time.strftime("%H:%M"))

    def _preparer(self, api, films, nombre, opts, part_max, ordre):
        cfg = reglages.charger()
        cat = self.catalogue()
        uniques = {}
        for f in films:
            if f.get("id"):
                uniques.setdefault(_cle(f), f)
        films = list(uniques.values())
        prets = self.pretes(films, part_max)
        manque = nombre - len(prets)
        self._maj(prets=len(prets), a_traiter=max(0, manque))
        if manque <= 0:
            self._maj(message=f"{len(prets)} affiches prêtes : tout est déjà fait.")
            return
        deja = {_cle(f) for f in prets}
        file = [f for f in _ordre(films, ordre) if _cle(f) not in deja and cat.a_traiter(f, cfg["essais_max"])]
        if not file:
            self._maj(message=f"{len(prets)} affiches prêtes sur {nombre} (les autres films n'ont pas d'affiche "
                              f"exploitable).")
            return
        derniere_erreur, d_affilee = "", 0
        for f in file:
            if self.stop.is_set() or manque <= 0:
                break
            annee = (f.get("release_date") or "")[:4]
            nom = f"{f.get('title')} ({annee})" if annee else f.get("title")
            self._maj(courant=nom, etape="", message=f"Affiche {len(prets) + 1}/{nombre} : {nom}")
            e = cat.preparer_entree(f, annee)
            if e.get("statut") == "pret" and cat.utilisable(f, part_max):   # réadoptée depuis le dossier
                prets.append(f)
                manque -= 1
                self._maj(prets=len(prets))
                continue
            try:
                e = pipeline.traiter(api, f, cat, opts, journal=lambda m: self._maj(etape=m))
            except detection.OutilManquant as err:
                self._maj(erreur=str(err), message=f"Préparation arrêtée : {err}")
                return
            except Exception as err:  # noqa: BLE001
                traceback.print_exc()
                self._maj(echecs=self._etat["echecs"] + 1)
                d_affilee = d_affilee + 1 if str(err) == derniere_erreur else 1
                derniere_erreur = str(err)
                if d_affilee >= 4:
                    self._maj(erreur=derniere_erreur, message=f"Préparation arrêtée (même erreur 4 fois) : {err}")
                    return
                continue
            d_affilee = 0
            self._maj(traites=self._etat["traites"] + 1)
            if e.get("part") is None or e["part"] <= part_max:
                prets.append(f)
                manque -= 1
                self._maj(prets=len(prets))
        if self.stop.is_set():
            self._maj(message=f"Préparation arrêtée : {len(prets)} affiches prêtes sur {nombre}.")
        elif manque > 0:
            self._maj(message=f"{len(prets)} affiches prêtes sur {nombre} (les autres sont en échec).")
        else:
            self._maj(message=f"{len(prets)} affiches prêtes.")


PREPARATEUR = Preparateur()
