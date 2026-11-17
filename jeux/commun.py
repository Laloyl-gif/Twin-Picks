"""Outils partagés par les jeux."""
import random

from PIL import Image

import sagas
from texte import cle, normaliser, variantes_titre
from tmdb import cle_film, details_film, libelle, nom_affiche


def tirer(pool, deja, ok=lambda x: True, ident=cle_film):
    """Un élément pas encore joué (on recommence quand tout a été joué). Les films d'une saga déjà jouée
    pendant la partie passent après les autres (pas deux Harry Potter de suite)."""
    cands = [x for x in pool if ok(x) and ident(x) not in deja]
    if not cands:
        for x in pool:
            deja.discard(ident(x))
        cands = [x for x in pool if ok(x)]
    if not cands:
        raise RuntimeError("Aucun élément exploitable dans les listes choisies.")
    if ident is cle_film:
        neufs = [x for x in cands if not (s := sagas.saga(x)) or ("saga", s[0]) not in deja]
        cands = neufs or cands
    x = random.choice(cands)
    deja.add(ident(x))
    return x


def cles_reponses(*noms):
    return sorted({cle(v) for v in variantes_titre(*noms)} - {""})


def affiche(api, film, taille="w342"):
    chemin = film.get("poster_path")
    if not chemin:                                    # film venu d'un profil importé : affiche via les détails
        try:
            chemin = details_film(api, film).get("affiche")
        except Exception:  # noqa: BLE001
            chemin = None
    return api.image(chemin, taille) if chemin else Image.new("RGB", (342, 513), "#333333")


def saga_de(cfg, details):
    """Nom de la saga à accepter / afficher (réglage « sagas »), sinon ""."""
    return details.get("saga", "") if cfg is None or cfg.get("sagas", True) else ""


def reponse_affichee(cfg, film, details):
    """Ce que les joueurs doivent trouver : le nom de la saga, sinon le titre du film."""
    return saga_de(cfg, details) or film["title"]


def manche_titre(jeu, vue, duree, film, details, etapes, images, revelation, cfg=None):
    """Manche « trouver le film ». Film d'une saga (si cfg l'autorise) : le nom de la saga suffit, et c'est lui
    qui s'affiche en solution (le titre exact passe en détail)."""
    saga = saga_de(cfg, details)
    m = dict(jeu=jeu, vue=vue, duree=float(duree), etapes=etapes, images=images, revelation=revelation,
             reponse="titre", cles=cles_reponses(*details["noms"], film["title"]), bonne=film["title"],
             solution=nom_affiche(film["title"], details["annee"], details["en"]), films=[cle_film(film)],
             saga_ok=cfg is not None)
    if saga:
        m.update(cles=sorted(set(m["cles"]) | set(cles_reponses(saga))), bonne=saga, solution=saga,
                 detail=libelle(dict(film, release_date=details["annee"] or film.get("release_date", ""))),
                 saga_id=details.get("saga_id"))
    return m


def horaires(n, debut, intervalle):
    return [0.0 if i < debut else intervalle * (i - debut + 1) for i in range(n)]


def grille(temps, legendes):
    """Étapes d'une grille de cartes qui apparaissent une à une."""
    etapes = []
    for k, t in enumerate(temps):
        etat = {"cartes": [{"img": i, "txt": legendes[i]} for i in range(k + 1)], "total": len(temps)}
        if etapes and etapes[-1][0] == t:
            etapes[-1] = (t, etat)
        else:
            etapes.append((t, etat))
    return etapes


def chronologie(evenements, etat):
    """evenements : [(instant, action)] ; chaque action modifie l'état, etat() le photographie.
    Retourne les étapes [(instant, état)] (une étape par instant distinct)."""
    etapes = [(0.0, etat())]
    for t, action in sorted(evenements, key=lambda e: e[0]):
        action()
        if etapes[-1][0] == t:
            etapes[-1] = (t, etat())
        else:
            etapes.append((t, etat()))
    return etapes


def trous(titre, part=0.0, graine=0):
    """Titre à trous : 1re lettre de chaque mot, puis une part des autres lettres (ordre fixé par la graine).
    « Le Parrain » -> « L_ P______ »."""
    lettres = [i for i, c in enumerate(titre) if c.isalnum()]
    premieres = {i for i in lettres if i == 0 or not titre[i - 1].isalnum()}
    autres = [i for i in lettres if i not in premieres]
    random.Random(graine or titre).shuffle(autres)
    montrees = premieres | set(autres[:round(len(autres) * part)])
    return "".join(c if (not c.isalnum() or i in montrees) else "_" for i, c in enumerate(titre))


def indice_titre(titre):
    """« Titre en 2 mots »."""
    n = len(normaliser(titre).split())
    return f"Titre en {n} mot{'s' if n > 1 else ''}"
