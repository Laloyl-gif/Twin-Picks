"""Catalogue des affiches de Pete : la correspondance film -> affiche originale / affiche vidée / masque.

Dossier (affiches_pete/ par défaut) :
    catalogue.json            une entrée par film, clé « m:348 » (film) ou « tv:1399 » (série)
    originales/<Titre (année)>.jpg   l'affiche téléchargée sur TMDB
    videes/<Titre (année)>.png       l'affiche sans titre, textes ni personnages (ce que voient les joueurs)
    masques/<Titre (année)>.png      les zones effacées (blanc), pour vérifier ou retoucher
    _anciennes/                      affiches remplacées à la demande (jamais supprimées)

Règles :
  - le nom de fichier d'un film est fixé une fois pour toutes dans le catalogue (deux films au même titre et à la
    même année reçoivent « [tmdb-123] » en plus) ; le catalogue fait foi, pas le nom ;
  - une affiche prête n'est jamais retraitée ni écrasée, sauf demande explicite (refaire()) : l'ancienne
    va alors dans _anciennes/ ;
  - toute écriture passe par un fichier temporaire renommé à la fin : un arrêt brutal ne laisse jamais de
    fichier à moitié écrit ; au démarrage, les temporaires sont effacés et les traitements « en cours » repris ;
  - un fichier « vidé » trouvé dans le dossier sans entrée (catalogue perdu) est réadopté au lieu d'être refait ;
  - une affiche prête dont le fichier a disparu est refaite quand on en a besoin ;
  - quand le traitement change de version (VERSION_TRAITEMENT), le cache est vidé une fois : les affiches vidées,
    masques et originales de l'ancien traitement sont supprimés et tout est refait avec le nouveau
    (aussi à la demande : python -m affiches vider).
"""
import json
import os
import re
import shutil
import threading
import time

VERSION_TRAITEMENT = 3          # 3 : masques nettoyés, affiches candidates, affinage, halos
STATUTS = ("a_faire", "en_cours", "pret", "echec")
_INTERDITS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def cle(film):
    return f"{'tv' if film.get('tv') else 'm'}:{film['id']}"


def nom_propre(titre, annee):
    base = _INTERDITS.sub(" ", titre or "Sans titre")
    base = " ".join(base.split()).strip(" .") or "Sans titre"
    base = base[:90]
    return f"{base} ({annee})" if annee else base


def ecrire_atomique(chemin, data):
    tmp = chemin + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, chemin)


class Catalogue:
    def __init__(self, dossier):
        self.dossier = dossier
        self.fichier = os.path.join(dossier, "catalogue.json")
        self.verrou = threading.RLock()
        for sous in ("originales", "videes", "masques"):
            os.makedirs(os.path.join(dossier, sous), exist_ok=True)
        self._nettoyer_temporaires()
        self.traitement = VERSION_TRAITEMENT
        self.films = self._lire()
        if self.traitement < VERSION_TRAITEMENT:
            print(f"[affiches] nouveau traitement (v{VERSION_TRAITEMENT}) : le cache des affiches vidées est vidé.")
            self.vider()
        repris = 0
        for e in self.films.values():
            if e.get("statut") == "en_cours":            # traitement interrompu (arrêt du jeu, coupure…)
                e["statut"], repris = "a_faire", repris + 1
        if repris:
            self.sauver()

    # ---------- fichiers ----------
    def _nettoyer_temporaires(self):
        for racine, _, fichiers in os.walk(self.dossier):
            for f in fichiers:
                if f.endswith(".tmp"):
                    try:
                        os.remove(os.path.join(racine, f))
                    except OSError:
                        pass

    def _lire(self):
        try:
            with open(self.fichier, encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                return {}
            self.traitement = int(d.get("traitement") or 2)
            return d.get("films", {})
        except FileNotFoundError:
            # pas de catalogue : s'il reste des affiches d'un ancien traitement dans le dossier, on les retire aussi
            if any(os.listdir(os.path.join(self.dossier, "videes"))):
                self.traitement = 0
            return {}
        except (OSError, ValueError):
            secours = f"{self.fichier}.illisible-{time.strftime('%Y%m%d-%H%M%S')}"
            try:
                shutil.copy2(self.fichier, secours)
            except OSError:
                pass
            print(f"[affiches] catalogue illisible, copie gardée : {secours} ; les affiches présentes seront réadoptées.")
            return {}

    def sauver(self):
        with self.verrou:
            data = json.dumps({"version": 1, "traitement": VERSION_TRAITEMENT, "films": self.films}, ensure_ascii=False,
                              indent=1).encode("utf-8")
            ecrire_atomique(self.fichier, data)

    def vider(self):
        """Vide le cache : supprime les affiches vidées, les masques et les originales, et repart d'un catalogue vide
        (les affiches seront refaites avec le traitement actuel). _anciennes/ n'est pas touché."""
        with self.verrou:
            n = 0
            for sous in ("videes", "masques", "originales"):
                d = os.path.join(self.dossier, sous)
                for f in os.listdir(d):
                    try:
                        os.remove(os.path.join(d, f))
                        n += 1
                    except OSError:
                        pass
            self.films = {}
            self.traitement = VERSION_TRAITEMENT
            self.sauver()
            return n

    def chemin(self, rel):
        return os.path.join(self.dossier, rel) if rel else ""

    # ---------- entrées ----------
    def entree(self, film):
        with self.verrou:
            return self.films.get(cle(film))

    def _nom_libre(self, film, annee):
        base = nom_propre(film.get("title"), annee)
        pris = {e.get("fichier") for k, e in self.films.items() if k != cle(film)}
        if base in pris:
            base = f"{base} [tmdb-{'tv-' if film.get('tv') else ''}{film['id']}]"
        return base

    def preparer_entree(self, film, annee=""):
        """Entrée du film (créée si besoin, nom de fichier attribué). Réadopte une affiche vidée déjà présente."""
        with self.verrou:
            e = self.films.get(cle(film))
            if e is None:
                nom = self._nom_libre(film, annee)
                e = {"tmdb": film["id"], "tv": bool(film.get("tv")), "titre": film.get("title"), "annee": annee,
                     "fichier": nom, "statut": "a_faire", "essais": 0,
                     "originale": f"originales/{nom}.jpg", "videe": f"videes/{nom}.png", "masque": f"masques/{nom}.png"}
                self.films[cle(film)] = e
                if os.path.isfile(self.chemin(e["videe"])):
                    e.update(statut="pret", adoptee=True, version=VERSION_TRAITEMENT, date=time.strftime("%Y-%m-%d %H:%M"))
                    e["part"] = self._part_masque(e)
                self.sauver()
            return e

    def _part_masque(self, e):
        try:
            from PIL import Image
            m = Image.open(self.chemin(e["masque"])).convert("L")
            h = m.histogram()
            return round(sum(h[128:]) / max(1, sum(h)), 4)
        except Exception:  # noqa: BLE001
            return None

    def utilisable(self, film, part_max=1.0):
        """Vrai si l'affiche vidée est prête, présente sur le disque, et assez peu effacée."""
        with self.verrou:
            e = self.films.get(cle(film))
            if not e:
                nom = nom_propre(film.get("title"), (film.get("release_date") or "")[:4])
                if os.path.isfile(os.path.join(self.dossier, "videes", nom + ".png")):
                    e = self.preparer_entree(film, (film.get("release_date") or "")[:4])
                else:
                    return False
            if e.get("statut") != "pret":
                return False
            if (e.get("version") or 0) < VERSION_TRAITEMENT:      # ancien traitement : à refaire
                e.update(statut="a_faire", essais=0)
                self.sauver()
                return False
            if not os.path.isfile(self.chemin(e["videe"])):
                e.update(statut="a_faire", note="fichier vidé manquant : à refaire")
                self.sauver()
                return False
            part = e.get("part")
            return part is None or part <= part_max

    def a_traiter(self, film, essais_max):
        """Vrai si le film peut (encore) être traité : jamais traité, interrompu, ou échoué moins de essais_max fois."""
        with self.verrou:
            e = self.films.get(cle(film))
            if not e:
                return True
            if e.get("statut") == "pret":
                return not os.path.isfile(self.chemin(e["videe"]))
            if e.get("statut") == "echec":
                return e.get("essais", 0) < essais_max
            return True

    def maj(self, film, **champs):
        with self.verrou:
            e = self.films[cle(film)]
            e.update(champs)
            self.sauver()
            return e

    def refaire(self, film):
        """Demande explicite : l'affiche vidée actuelle part dans _anciennes/ et le film repasse « à faire »."""
        with self.verrou:
            e = self.films.get(cle(film))
            if not e:
                return False
            archive = os.path.join(self.dossier, "_anciennes")
            os.makedirs(archive, exist_ok=True)
            for champ in ("videe", "masque"):
                src = self.chemin(e.get(champ))
                if src and os.path.isfile(src):
                    base, ext = os.path.splitext(os.path.basename(src))
                    shutil.move(src, os.path.join(archive, f"{base}.{champ}.{time.strftime('%Y%m%d-%H%M%S')}{ext}"))
            e.update(statut="a_faire", essais=0)
            self.sauver()
            return True

    def resume(self):
        with self.verrou:
            n = {s: 0 for s in STATUTS}
            for e in self.films.values():
                n[e.get("statut", "a_faire")] = n.get(e.get("statut", "a_faire"), 0) + 1
            return n


_CATALOGUES = {}
_VERROU = threading.Lock()


def ouvrir(dossier):
    """Un seul objet Catalogue par dossier (partagé par la préparation et les manches)."""
    dossier = os.path.abspath(dossier)
    with _VERROU:
        if dossier not in _CATALOGUES:
            _CATALOGUES[dossier] = Catalogue(dossier)
        return _CATALOGUES[dossier]
