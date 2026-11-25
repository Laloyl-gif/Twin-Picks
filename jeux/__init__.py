"""Un fichier par jeu ; chacun expose construire(api, cfg, pool, deja) -> manche (dict).

Format d'une manche :
    jeu, vue ("image" | "plans" | "grille" | "noms" | "anagramme" | "texte" | "cassette" | "complice" | "choix" |
              "note" | "fiche" | "chrono" | "bingo" | "couleurs" | "videe" | "briggs" | "frise" | "pages" | "croquis" | "ben" | "miroir"
              | "tracklist" | "ed" | "buche" | "duels" | "geant"), duree (s),
    etapes  : [(instant, état envoyé aux écrans), ...]   (images référencées par leur numéro)
    images  : [jpeg, ...]      revelation : jpeg ou None      audio : mp3 (blind test, écran hôte seulement)
    reponse : "titre" | "complice" | "choix" (bonne_i, infos) | "note" | "chrono" | "bingo" | "nombre" (une année)
              | "ordre" (remettre des films dans l'ordre : La frise) | "double" (budget + box-office : Ben)
              | "duree" (la durée du film en minutes : Big Ed)
    cles    : réponses acceptées (normalisées)   bonne : libellé (QCM)   solution / detail : textes affichés
    films   : clés des films de la manche (la musique d'ambiance évite leurs BO)

Les jeux « note », « chrono », « bingo », « ordre », « double » et « duree » ont un moteur (classe Moteur) : action(), fini(), clore(), vue()…
"""
from . import (affiche, albert, anagramme, andy, ben, blindtest, bobby, briggs, carl, casting, catherine, complicite,
               annie, couleurs, denise, donna, dougie, hank, harold, jacques, jerry, mike, phillip, plusieurs, windom,
               ed, filmo, geant, hawk, james, josie, leland, leo, loglady, lucy, maddy, nadine, norma, persos, pete, plans,
               shelly, synopsis, sarah, jean, woodsman, mitchum, mrc, desmond, dick, milford, enveloppes, lana, bernard,
               tremond, bushnell, hayward, gersten, naido, tammy)

CONSTRUCTEURS = {
    "affiche": affiche.construire, "plans": plans.construire, "casting": casting.construire,
    "anagramme": anagramme.construire, "blindtest": blindtest.construire, "complice": complicite.construire,
    "synopsis": synopsis.construire, "filmo": filmo.construire, "persos": persos.construire,
    "norma": norma.construire, "shelly": shelly.construire, "leland": leland.construire, "lucy": lucy.construire,
    "donna": donna.construire, "bobby": bobby.construire, "couleurs": couleurs.construire, "pete": pete.construire,
    "briggs": briggs.construire, "albert": albert.construire, "nadine": nadine.construire, "hawk": hawk.construire,
    "andy": andy.construire, "ben": ben.construire, "josie": josie.construire, "maddy": maddy.construire,
    "james": james.construire, "ed": ed.construire, "loglady": loglady.construire, "leo": leo.construire,
    "geant": geant.construire, "catherine": catherine.construire, "denise": denise.construire, "carl": carl.construire,
    "phillip": phillip.construire, "jerry": jerry.construire, "hank": hank.construire,
    "annie": annie.construire, "dougie": dougie.construire, "mike": mike.construire, "windom": windom.construire,
    "harold": harold.construire, "jacques": jacques.construire, "sarah": sarah.construire, "jean": jean.construire,
    "woodsman": woodsman.construire, "mitchum": mitchum.construire, "mrc": mrc.construire, "desmond": desmond.construire,
    "dick": dick.construire, "milford": milford.construire, "lana": lana.construire, "bernard": bernard.construire,
    "tremond": tremond.construire, "bushnell": bushnell.construire, "hayward": hayward.construire,
    "gersten": gersten.construire, "naido": naido.construire, "tammy": tammy.construire,
}
MOTEURS = {"note": norma.Moteur, "chrono": lucy.Moteur, "bingo": donna.Moteur, "ordre": nadine.Moteur,
           "double": ben.Moteur, "duree": ed.Moteur, "duels": leo.Moteur,
           "plusieurs": plusieurs.Moteur, "paire": plusieurs.Moteur, "brelan": jacques.Moteur, "paires": mike.Moteur,
           "focus": hank.Moteur, "dessin": woodsman.Moteur, "contrat": mitchum.Moteur, "blackjack": jean.Moteur,
           "differences": mrc.Moteur, "code": desmond.Moteur, "pendule": windom.Moteur, "enveloppes": enveloppes.Moteur,
           "mensonges": lana.Moteur, "poker": bernard.Moteur, "tableau": tremond.Moteur, "pluie": bushnell.Moteur,
           "diapason": gersten.Moteur, "entremots": naido.Moteur, "enquete": tammy.Moteur}
