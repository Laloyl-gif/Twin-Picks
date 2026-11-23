"""Un film tapé par un joueur (n'importe quel film de TMDB) : sa fiche et sa petite affiche, prêtes à afficher.
Sert aux jeux où les joueurs proposent eux-mêmes des films (le diapason, entre les mots, l'enquête de Tammy)."""
from PIL import ImageOps

from tmdb import fiche, libelle
from visuels import en_jpeg
from .commun import affiche
from .contraintes import entrees_films, index, resoudre, suggerer_films


class Saisie:
    def __init__(self, api, pool):
        self.api = api
        self.idx = index([f for f in pool if not f.get("tv")])
        self.entrees = entrees_films([f for f, _ in self.idx])

    def suggerer(self, q):
        return suggerer_films(self.api, q, self.entrees)

    def resoudre(self, texte, avec_fiche=True, avec_image=True):
        """{"film", "fiche", "img" (jpeg), "libelle"} ou {"film": None}. À appeler HORS du verrou de la partie."""
        r = resoudre(self.api, texte, self.idx, avec_fiche) or {"film": None}
        f = r.get("film")
        if not f or f.get("tv"):
            return {"film": None}
        if avec_fiche and not r.get("fiche"):
            try:
                r["fiche"] = fiche(self.api, f)
            except Exception:  # noqa: BLE001
                r["fiche"] = None
        if avec_image:
            try:
                r["img"] = en_jpeg(ImageOps.fit(affiche(self.api, f, "w185"), (160, 240)), 240)
            except Exception:  # noqa: BLE001
                r["img"] = None
        r["libelle"] = libelle(f)
        return r


def publier(partie, m, jpeg):
    """Ajoute une image à la manche en cours et la rend visible (numéro de l'image, ou None)."""
    if not jpeg:
        return None
    m["images"].append(jpeg)
    n = len(m["images"]) - 1
    partie.publies.add(n)
    return n
