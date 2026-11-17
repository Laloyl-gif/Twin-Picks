"""Préparer les affiches vidées sans lancer le jeu (pratique pour une longue série, la nuit par exemple).

    python -m affiches outils                  outils installés
    python -m affiches etat                    contenu du catalogue
    python -m affiches preparer [N]            prépare toutes les affiches des listes de Pete (ou les N premières)
    python -m affiches refaire "Alien (1979)"  refait une affiche (l'ancienne est gardée dans _anciennes/)
    python -m affiches vider                   vide le cache : toutes les affiches seront refaites
"""
import sys
import time

import config
from tmdb import TMDB, charger_pools
from . import detection
from .preparation import PREPARATEUR


def main(args):
    cmd = args[0] if args else "--aide"
    if cmd == "outils":
        for k, v in detection.outils_disponibles().items():
            print(f"{k:15} {v}")
        return
    cat = PREPARATEUR.catalogue()
    if cmd == "etat":
        print(f"Dossier : {cat.dossier}")
        print(cat.resume())
        for e in sorted(cat.films.values(), key=lambda e: e.get("fichier", "")):
            part = f"{e['part'] * 100:.0f} % effacé" if e.get("part") is not None else ""
            print(f"  {e.get('statut', '?'):9} {e.get('fichier', '?'):50} {part:14} {e.get('erreur', '')}")
        return
    if cmd == "vider":
        n = cat.vider()
        print(f"Cache vidé ({n} fichiers supprimés) : les affiches seront refaites à la prochaine préparation.")
        return
    if cmd == "refaire" and len(args) > 1:
        cibles = [k for k, e in cat.films.items() if e.get("fichier") == args[1]]
        if not cibles:
            print("Aucune affiche de ce nom dans le catalogue (voir : python -m affiches etat).")
            return
        typ, ident = cibles[0].split(":")
        cat.refaire({"id": int(ident), "tv": typ == "tv"})
        print("Affiche remise à faire ; elle sera refaite à la prochaine préparation.")
        return
    if cmd == "preparer":
        r = config.charger()
        api = TMDB(r["api_key"], r["session_id"], r["account_id"])
        pools, _ = charger_pools(api, r, {"pete"})
        films = pools["films_pete"]
        n = int(args[1]) if len(args) > 1 else None
        PREPARATEUR.lancer(api, films, {"textes": r["pete_textes"], "personnages": r["pete_personnages"],
                                        "objets": r["pete_objets"]}, r["pete_ordre"], n)
        dernier = ""
        try:
            while PREPARATEUR.actif():
                m = PREPARATEUR.etat()["message"]
                if m != dernier:
                    print(m)
                    dernier = m
                time.sleep(0.5)
        except KeyboardInterrupt:
            PREPARATEUR.arreter()
            print("Arrêt demandé…")
            while PREPARATEUR.actif():
                time.sleep(0.5)
        print(PREPARATEUR.etat()["message"])
        return
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
