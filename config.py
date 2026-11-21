"""Constantes, description des jeux et des réglages, lecture / écriture de settings.json."""
import copy
import json
import os

import shutil

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DOSSIER_WEB = os.path.join(DOSSIER, "web")
DOSSIER_AVATARS = os.path.join(DOSSIER_WEB, "persos", "avatars")
# Tout ce que le jeu écrit (réglages, profils, caches, images téléchargées…) va dans un dossier de données, à part du
# code : une mise à jour (git pull, nouvelle version téléchargée par l'application) ne l'écrase jamais.
# Par défaut : donnees/ à côté du code (ignoré par git) ; l'application Android donne le sien (TP_DONNEES).
DOSSIER_DONNEES = os.environ.get("TP_DONNEES") or os.path.join(DOSSIER, "donnees")
os.makedirs(DOSSIER_DONNEES, exist_ok=True)


def donnee(nom, dossier=False):
    """Chemin d'un fichier (ou dossier) de données. Au premier usage, la version fournie avec le jeu (à côté du code)
    sert de point de départ : réglages par défaut, caches déjà remplis."""
    chemin = os.path.join(DOSSIER_DONNEES, nom)
    fourni = os.path.join(DOSSIER, nom)
    if not os.path.exists(chemin) and os.path.exists(fourni):
        try:
            (shutil.copytree if os.path.isdir(fourni) else shutil.copyfile)(fourni, chemin)
        except OSError:
            pass
    if dossier:
        os.makedirs(chemin, exist_ok=True)
    return chemin


DOSSIER_PLANS = os.path.join(DOSSIER, "plans")                 # plans locaux (facultatif : voir plans_distants.py)
DOSSIER_PLANS_CACHE = os.path.join(DOSSIER_DONNEES, "plans_cache")
DOSSIER_IMAGES_MENU = os.path.join(DOSSIER_DONNEES, "images_menu")   # images du menu ajoutées depuis l'écran hôte
FICHIER_REGLAGES = donnee("settings.json")
FICHIER_PROFILS = donnee("profils.json")
FICHIER_ACTEURS = os.path.join(DOSSIER, "acteurs.txt")
FICHIER_CACHE_ACTEURS = donnee("acteurs_cache.json")
FICHIER_CACHE_REALISATEURS = donnee("realisateurs_cache.json")

CLE_API_DEFAUT = "86ed8f1a7ba89d86b9736b6f0b765375"
LISTE_DEFAUT = 8707294
PORT = 8765

COULEURS = ["#8a6ae6", "#c6b6ff", "#3a86ff", "#7bdff2", "#1abc9c", "#2ecc71", "#b5e48c", "#f5c518",
            "#ff7a00", "#e5484d", "#ff4fa3", "#ff8fab", "#c9a27e", "#8d99ae", "#ffffff", "#a55eea"]

# reponse : "titre" (Écrit / QCM / Buzzer), "double" (Ben), "duree" (Big Ed), "duels" (Leo), "complice" (choix d'affiches), "choix" (une image parmi plusieurs),
#           "note" (une note de 1 à 10), "chrono" (le plus de films possible), "bingo" (grille de contraintes),
#           "nombre" (une année), "ordre" (remettre des films dans l'ordre)
# titre : nom du jeu dans le MENU (et en grand pendant la partie) : le nom Twin Peaks (« Pete's Percolator »).
#         ⚠ FIGÉ : ces noms ne doivent pas être changés (voir CONSIGNES.md).
# nom   : nom technique du jeu (« Affiche vidée ») : réglages, listes, messages d'erreur, petit texte du menu.
# qui   : le personnage de Twin Peaks      regle : la règle en une phrase (menu, réglages)
# perso : image web/persos/<perso>.jpg et emblème
# profils : nombre minimal de joueurs présents qui ont un profil (jeux fondés sur les notes des profils)
def _jeu(titre, nom, qui, regle, perso, reponse, listes=True, **kw):
    return dict(titre=titre, nom=nom, qui=qui, regle=regle, perso=perso, reponse=reponse, listes=listes, **kw)


JEUX = {
    "affiche": _jeu("Cooper's Investigation", "Affiche déformée", "Cooper", "L'affiche se précise peu à peu.",
                    "cooper", "titre"),
    "plans": _jeu("Truman's Files", "Trois plans", "Truman",
                  "Trois images du film, de la plus difficile à la plus facile.", "truman", "titre"),
    "casting": _jeu("Audrey's Dance", "Casting", "Audrey", "Les acteurs arrivent un par un.", "audrey", "titre"),
    "anagramme": _jeu("Cole's Hearing Aid", "Anagramme", "Cole", "Les lettres du titre sont mélangées.", "cole",
                      "titre"),
    "blindtest": _jeu("Diane's Tape", "Blind test", "Diane", "Un extrait de la bande originale.", "diane", "titre"),
    "complice": _jeu("BOB's Fire Walk With Me", "Complicité", "BOB", "Retrouvez le film préféré d'un autre joueur.",
                     "bob", "complice"),
    "synopsis": _jeu("Dr. Jacoby's Couch", "Synopsis", "Dr Jacoby", "Le résumé se dévoile peu à peu.", "jacoby",
                     "titre"),
    "filmo": _jeu("Laura's Secret Diary", "Filmographie", "Laura", "Ses films arrivent un par un : trouvez l'acteur.",
                  "laura", "titre", listes=False),
    "persos": _jeu("Janey-E's Owls", "Personnages", "Janey-E", "Les personnages du film, un par un.", "janey",
                   "titre"),
    "norma": _jeu("Norma's Double R", "Devine la note", "Norma", "Quelle note un autre joueur a-t-il donnée ?",
                  "norma", "note", listes=False, profils=2),
    "shelly": _jeu("Shelly's Cherry Pie", "La moyenne", "Shelly", "La moyenne de vos notes, puis des indices.",
                   "shelly", "titre", listes=False, profils=1),
    "leland": _jeu("Leland's Smile", "L'intrus", "Leland", "Un seul n'a rien à faire là.", "leland", "choix"),
    "lucy": _jeu("Lucy's Hotline", "Chrono", "Lucy", "Le plus de films possible pour une condition.", "lucy",
                 "chrono"),
    "donna": _jeu("One-Eyed Donna's", "Bingo", "Donna", "Un film par case, à la croisée de deux conditions.",
                  "donna", "bingo"),
    "bobby": _jeu("Bobby in the Ghostwood", "Le mieux noté", "Bobby", "Lequel a la meilleure note TMDB ?", "bobby",
                  "choix"),
    "couleurs": _jeu("The Man From Another Place's egdoL kcalB", "Couleurs", "L'Homme d'ailleurs",
                     "L'affiche réduite à ses couleurs, de plus en plus fine.", "manfrom", "titre"),
    "pete": _jeu("Pete's Percolator", "Affiche vidée", "Pete",
                 "Plus de titre ni de personnages : il ne reste que le décor.", "pete", "titre"),
    "briggs": _jeu("Major Briggs' Deep Space Monitor Printouts", "Mots-clés", "Major Briggs",
                   "Le relevé s'imprime : les éléments clés de l'histoire, un par un.", "briggs", "titre"),
    "albert": _jeu("Albert's Blue Rose Conversation", "Le lien", "Albert", "Qu'ont ces deux films en commun ?",
                   "albert", "choix"),
    "nadine": _jeu("Nadine's Silent Drape Runners", "La frise", "Nadine",
                   "Accrochez les films sur la tringle, du plus ancien au plus récent.", "nadine", "ordre"),
    "hawk": _jeu("Hawk's Missing Pages", "L'accroche", "Hawk",
                 "Le slogan de l'affiche, puis des indices petit à petit.", "hawk", "titre"),
    "andy": _jeu("Andy's Police Sketch", "Le croquis", "Andy",
                 "Le portrait-robot de l'affiche, au crayon, trait après trait.", "andy", "titre"),
    "ben": _jeu("Ben's Ghostwood Deal", "Le box-office", "Ben",
                "Son budget et ce qu'il a rapporté : il faut les deux.", "ben", "double"),
    "josie": _jeu("Josie's Double Ledger", "Le mensonge", "Josie",
                  "Six affirmations sur le film : une seule est fausse.", "josie", "choix"),
    "maddy": _jeu("Maddy's Impersonation", "Qui l'a dit ?", "Maddy",
                  "Une réplique du film : quel personnage l'a dite ?", "maddy", "choix"),
    "james": _jeu("James' Just You", "La bande originale", "James",
                  "Les morceaux de la BO, un par un, sur la jaquette de la cassette.", "james", "titre"),
    "ed": _jeu("Big Ed's Gas Farm", "La durée", "Big Ed", "Combien de minutes dure le film ?", "ed", "duree"),
    "loglady": _jeu("The Log Lady's Knothole", "Ce que la bûche a vu", "La Dame à la bûche",
                    "Une image du film, vue par le trou d'un nœud de la bûche.", "loglady", "titre"),
    "leo": _jeu("Leo's New Shoes", "Plus ou moins", "Leo",
                "Quatre duels : le plus récent, le plus long, le mieux noté, le plus rentable ?", "leo", "duels"),
    "geant": _jeu("The Giant's Three Clues", "Les trois répliques", "Le Géant",
                  "Trois répliques du film, l'une après l'autre.", "geant", "titre"),
    "catherine": _jeu("Catherine's Disguise", "Le titre déguisé", "Catherine",
                      "Le titre traduit en chaîne dans plusieurs langues, puis retraduit en français.", "catherine", "titre"),
    "denise": _jeu("Denise's Undercover", "Qui suis-je ?", "Denise",
                   "La carte d'identité d'un acteur se remplit, sans son nom.", "denise", "titre", listes=False),
    "phillip": _jeu("Phillip's Associates", "Les complices", "Phillip Jeffries",
                    "Une personne mystère, devinée d'après ceux avec qui elle a le plus tourné.", "phillip", "titre",
                    listes=False),
    "jerry": _jeu("Jerry's Trip", "Le rébus", "Jerry", "Le titre du film écrit en images.", "jerry", "titre"),
    "hank": _jeu("Hank's Dominoes", "Les dominos", "Hank",
                 "Chacun a un film secret dans la grille ; à son tour on retire un film proche du sien. Devinez ceux des autres.",
                 "hank", "focus"),
    "carl": _jeu("Carl's Fat Trout Trailers", "Les deux films", "Carl",
                 "Derrière le store, une lame sur deux montre un film différent : trouvez les deux.", "carl", "plusieurs"),
    "annie": _jeu("Annie's Miss Twin Peaks", "L'absente", "Annie",
                  "Sept écharpes de candidates évoquent sept films : lequel des huit n'a pas la sienne ?", "annie",
                  "choix"),
    "dougie": _jeu("Dougie's Jackpots", "Le jackpot", "Dougie",
                   "La machine à sous tourne : retrouvez les cinq films de ses rouleaux avant qu'elle s'arrête.",
                   "dougie", "plusieurs"),
    "mike": _jeu("Mike's Shoe Samples", "Les paires", "Mike",
                 "Quatre personnages, quatre films : rendez à chacun son film (les chaussures vont par paires).", "mike",
                 "paires"),
    "windom": _jeu("Windom Earle's Chess Clock", "La pendule", "Windom Earle",
                   "Chacun son tour, un film lié au précédent (acteur, réalisateur, compositeur, année…), pendule d'échecs en marche.",
                   "windom", "pendule"),
    "harold": _jeu("Harold's Orchids", "Les pétales", "Harold Smith",
                   "Chaque pétale montre un détail de l'affiche, vu à la loupe, puis de plus en plus large.", "harold",
                   "titre"),
    "jacques": _jeu("Jacques Renault's Card Table", "Le brelan", "Jacques Renault",
                    "Cinq cartes, cinq affiches : trouvez les trois qui ont quelqu'un en commun.", "jacques", "brelan"),
    "sarah": _jeu("Sarah Palmer's Visions", "La vision", "Sarah Palmer",
                  "Des affiches passent très vite, comme une vision. Laquelle n'en faisait pas partie ?", "sarah", "choix"),
    "jean": _jeu("Jean Renault's Blackjack", "Le blackjack", "Jean Renault",
                 "Les cartes sont des films, leur valeur est leur note TMDB : approchez-vous de 21 sans dépasser.",
                 "jean", "blackjack"),
    "woodsman": _jeu("The Woodsman's Light", "Got a light?", "Le Woodsman",
                     "Dans le noir, chacun éclaire l'écran avec son téléphone : trouvez les indices, puis le film.",
                     "woodsman", "lumiere"),
    "mitchum": _jeu("The Mitchum Brothers' Contract", "Le contrat", "Les frères Mitchum",
                    "Des contrats passent de main en main : répondez juste pour refiler le vôtre avant que ça éclate.",
                    "mitchum", "contrat"),
    "mrc": _jeu("Mr. C's Doppelganger", "Le double", "Mr. C",
                "L'affiche et son double, retouché en douce : trouvez les différences.", "mrc", "differences"),
    "desmond": _jeu("Desmond's Code", "Le code", "Chet Desmond",
                    "Comme Codenames : un indice et un nombre ; on touche les films jusqu'à la première erreur, sans toucher le film noir.",
                    "desmond", "code"),
    "dick": _jeu("Dick Tremayne's Gala", "La cérémonie", "Dick Tremayne",
                 "Oscars, Césars, Palme d'or… : les vrais nommés s'affichent, trouvez le lauréat.", "dick", "enveloppes"),
    "milford": _jeu("Mayor Milford's Golden Owl", "Le Hibou d'or", "Dwayne Milford",
                    "Vous êtes l'académie : à quel film vos notes ont-elles donné le Hibou d'or ?", "milford", "enveloppes",
                    listes=False, profils=2),
}
# Garde-fou : les noms du menu sont figés (CONSIGNES.md). Un nom changé par erreur arrête le jeu au lancement.
TITRES_FIGES = {
    "affiche": "Cooper's Investigation", "plans": "Truman's Files", "casting": "Audrey's Dance",
    "anagramme": "Cole's Hearing Aid", "blindtest": "Diane's Tape", "complice": "BOB's Fire Walk With Me",
    "synopsis": "Dr. Jacoby's Couch", "filmo": "Laura's Secret Diary", "persos": "Janey-E's Owls",
    "norma": "Norma's Double R", "shelly": "Shelly's Cherry Pie", "leland": "Leland's Smile",
    "lucy": "Lucy's Hotline", "donna": "One-Eyed Donna's", "bobby": "Bobby in the Ghostwood",
    "couleurs": "The Man From Another Place's egdoL kcalB", "pete": "Pete's Percolator",
    "briggs": "Major Briggs' Deep Space Monitor Printouts", "albert": "Albert's Blue Rose Conversation",
    "nadine": "Nadine's Silent Drape Runners", "hawk": "Hawk's Missing Pages", "andy": "Andy's Police Sketch",
    "ben": "Ben's Ghostwood Deal", "josie": "Josie's Double Ledger", "maddy": "Maddy's Impersonation",
    "james": "James' Just You", "ed": "Big Ed's Gas Farm", "loglady": "The Log Lady's Knothole",
    "leo": "Leo's New Shoes", "geant": "The Giant's Three Clues", "catherine": "Catherine's Disguise",
    "denise": "Denise's Undercover", "carl": "Carl's Fat Trout Trailers", "phillip": "Phillip's Associates", "annie": "Annie's Miss Twin Peaks",
    "dougie": "Dougie's Jackpots", "mike": "Mike's Shoe Samples", "windom": "Windom Earle's Chess Clock",
    "harold": "Harold's Orchids", "jacques": "Jacques Renault's Card Table", "sarah": "Sarah Palmer's Visions",
    "jean": "Jean Renault's Blackjack", "woodsman": "The Woodsman's Light", "mitchum": "The Mitchum Brothers' Contract",
    "mrc": "Mr. C's Doppelganger", "desmond": "Desmond's Code",
    "dick": "Dick Tremayne's Gala", "milford": "Mayor Milford's Golden Owl",
    "jerry": "Jerry's Trip", "hank": "Hank's Dominoes",
}
assert all(JEUX[g]["titre"] == t for g, t in TITRES_FIGES.items() if g in JEUX), \
    "Noms des jeux du menu modifiés : voir CONSIGNES.md"
MENU_COLONNES = 3                        # ⚠ FIGÉ : 3 cartes par ligne dans le menu, ni plus ni moins (CONSIGNES.md)
JEUX_LISTES = [g for g, d in JEUX.items() if d["listes"]]
MODES_REPONSE = {"texte": "Écrit", "qcm": "QCM", "buzzer": "Buzzer"}
MODES_COMPLICE = {"tous": "Devinettes croisées", "tour": "Meneur à tour de rôle", "fixe": "Meneur fixe"}

# Sources du compte TMDB (identifiants négatifs pour ne pas les confondre avec les listes)
SOURCES_COMPTE = {
    -1: ("favorite", "movies", "Mes favoris (films)"),
    -2: ("favorite", "tv", "Mes favoris (séries)"),
    -3: ("watchlist", "movies", "À voir (films)"),
    -4: ("watchlist", "tv", "À voir (séries)"),
    -5: ("rated", "movies", "Films notés"),
    -6: ("rated", "tv", "Séries notées"),
}
VERSION_REGLAGES = 17

PLAYLIST_MENU = "https://music.youtube.com/playlist?list=PLA7jHGp_FUM4"
PLAYLIST_JEU = "https://music.youtube.com/playlist?list=OLAK5uy_mlZa8Lsr_mNkYfrYynkfQE1ZyamvGWY3A"
# Musique d'ambiance (Deezer, extraits de 30 s enchaînés en fondu) : menu = Twin Peaks ; partie = BO des films
# des listes (ou instrumental en attendant qu'une BO soit trouvée).
MENU_ARTISTE, MENU_ALBUM = "Angelo Badalamenti", "Twin Peaks"
AMBIANCE_ARTISTES = ["Bohren & der Club of Gore", "The Kilimanjaro Darkjazz Ensemble",
                     "The Dale Cooper Quartet & The Dictaphones", "BADBADNOTGOOD", "Khruangbin", "Tycho",
                     "Nujabes", "Emancipator"]
SOURCES_PLANS = {"auto": "Automatique", "local": "Mes fichiers seulement", "tmdb": "TMDB seulement"}
SENS_BOBBY = {"mieux": "Le mieux noté", "moins": "Le moins bien noté", "hasard": "Au hasard"}
ORDRE_CASTING = {"stars": "Têtes d'affiche d'abord", "hasard": "Au hasard", "inverse": "Seconds rôles d'abord"}

# Catégories d'intrus (L'intrus), de conditions (Chrono, Bingo) et de liens (Le lien) : désactivables.
INTRUS = {"realisateur": "Même réalisateur", "compositeur": "Même compositeur", "acteur": "Même acteur",
          "duo": "Même duo d'acteurs", "casting": "Acteurs d'un même film", "genre": "Même genre",
          "decennie": "Même décennie", "annee": "Même année de sortie", "langue": "Même langue originale",
          "pays": "Même pays de production", "scenariste": "Même scénariste",
          "photo": "Même directeur de la photo", "theme": "Même thème (mot-clé)", "duree": "Durée (très longs ou très courts)",
          "note": "Note TMDB", "joueurs": "Notes des joueurs (profils)"}
INTRUS_DIFFICILES = ("scenariste", "photo", "theme", "duree")     # peu parlants : décochés par défaut
CONTRAINTES = {"genre": "Genre", "decennie": "Décennie", "periode": "Année ou période de sortie",
               "realisateur": "Réalisateur (realisateurs.txt)", "acteur": "Acteur (acteurs.txt)",
               "compositeur": "Compositeur", "note": "Note TMDB", "langue": "Langue originale",
               "pays": "Pays de production", "duree": "Durée", "boxoffice": "Box-office", "saga": "Film d'une saga",
               "theme": "Thème (zombies, voyage dans le temps…)",
               "titre": "Titre (lettre, mots, nombre…)", "joueurs": "Notes d'un autre joueur (profils)"}
CONTRAINTES_LUCY = {k: v for k, v in CONTRAINTES.items() if k != "saga"}      # Chrono : pas de « film d'une saga »
LIENS_ALBERT = {"acteur": "Même acteur", "realisateur": "Même réalisateur", "compositeur": "Même compositeur",
                "scenariste": "Même scénariste", "photo": "Même directeur de la photo", "theme": "Même thème (mot-clé)",
                "genre": "Même genre", "decennie": "Même décennie", "annee": "Même année de sortie",
                "langue": "Même langue originale (hors anglais)", "budget": "Même ordre de budget"}
REPLIQUES_LANGUES = {"fr": "Français (l'anglais en petit)", "fr_seul": "Français seulement",
                     "en": "Anglais (le français en petit)", "en_seul": "Anglais seulement"}
ORDRES_PETE = {"connus": "Les plus connus", "hasard": "Au hasard"}
SOURCES_MUSIQUE = {"auto": "Automatique", "local": "Dossier musique/", "youtube": "Playlist YouTube",
                   "deezer": "Deezer (extraits)"}
TAILLES_DONNA = {"2": "2 × 2", "3": "3 × 3"}
MODES_DONNA = {"lignes": "Lignes × colonnes", "cases": "Une par case"}
GRILLES_DONNA = {"joueur": "Une grille par joueur", "commune": "La même pour tous"}


def avatars():
    """Photos de profil disponibles : web/persos/avatars/<nom>.jpg (les personnages des jeux d'abord)."""
    try:
        noms = sorted(os.path.splitext(f)[0] for f in os.listdir(DOSSIER_AVATARS) if f.lower().endswith(".jpg"))
    except OSError:
        return []
    ordre = [d["perso"] for d in JEUX.values()]
    return [n for n in ordre if n in noms] + [n for n in noms if n not in ordre]


def _p(cle, groupe, label, defaut, mini=None, maxi=None, pas=1, **kw):
    t = kw.pop("type", None) or ("bool" if isinstance(defaut, bool)
                                 else "float" if isinstance(defaut, float) else "int")
    return dict(cle=cle, groupe=groupe, label=label, defaut=defaut, min=mini, max=maxi, pas=pas, type=t, **kw)


# Tous les réglages : l'écran hôte construit ses formulaires à partir de cette liste.
PARAMS = [
    _p("reveal_secs", "general", "Affichage de la réponse (s)", 6, 2, 30),
    _p("hasard", "general", "Jeux au hasard parmi ceux choisis (juste un nombre de manches)", False, menu=True),
    _p("hasard_n", "general", "Nombre de manches (jeux au hasard)", 15, 1, 200, menu=True),
    _p("indices_recompenses", "general", "Indice « récompenses » (Oscars, Césars, Palme d'or…) dans les jeux", True),
    _p("anti_repetition", "general", "Écarter les films joués lors des dernières parties", True),
    _p("anti_repetition_n", "general", "… pendant combien de parties", 3, 1, 20),
    _p("max_essais", "general", "Essais par manche (Écrit)", 3, 1, 10),
    _p("qcm_choix", "general", "Propositions en mode QCM", 6, 2, 12),
    _p("blocage", "general", "Blocage après une erreur (Buzzer, s)", 3, 0, 15),
    _p("bonus_vitesse", "general", "Bonus de rapidité maximal", 300, 0, 1000, 50),
    _p("serie_bonus", "general", "Bonus par manche de série", 50, 0, 500, 10),
    _p("rattrapage", "general", "Rattrapage : bonus pour les joueurs en retard qui marquent", True,
       aide="Dans tous les jeux : quand un joueur marque des points, il gagne en plus une part de son retard sur le "
            "premier."),
    _p("rattrapage_pct", "general", "Rattrapage : part du retard sur le premier (%)", 15, 0, 50, 1),
    _p("rattrapage_max", "general", "Rattrapage : bonus maximal par manche", 500, 0, 3000, 50),
    _p("musique", "general", "Musique d'ambiance (Twin Peaks au menu)", True),
    _p("musique_volume", "general", "Volume de la musique d'ambiance (%)", 40, 0, 100, 5),
    _p("musique_films", "general", "Pendant la partie : musiques des films des listes", True,
       aide="Bandes originales des films joués (jamais celle de la manche en cours) : dossier musique/films/ "
            "(morceaux complets), sinon extraits Deezer."),
    _p("musique_menu_source", "general", "Musique du menu : source", "youtube", type="choix", choix=SOURCES_MUSIQUE,
       aide="Automatique : dossier musique/menu/ s'il contient des fichiers, sinon la playlist, sinon Deezer (30 s)."),
    _p("musique_menu_youtube", "general", "Musique du menu : playlist YouTube (lien)", PLAYLIST_MENU, type="texte",
       placeholder="https://www.youtube.com/playlist?list=…"),
    _p("musique_jeu_source", "general", "Musique de la partie : source", "youtube", type="choix", choix=SOURCES_MUSIQUE,
       aide="Dossiers musique/films/ et musique/partie/, playlist YouTube ci-dessous, ou extraits Deezer."),
    _p("musique_jeu_youtube", "general", "Musique de la partie : playlist YouTube (lien)", PLAYLIST_JEU, type="texte",
       placeholder="https://www.youtube.com/playlist?list=…"),
    _p("salle_internet", "general", "Code de la partie : joignable aussi par Internet", True,
       aide="Le tunnel cloudflared s'ouvre tout seul (téléchargé la première fois) : avec le code, on rejoint la partie "
            "même sans être sur le même Wi-Fi."),
    _p("profils_auto", "general", "Profils : listes choisies selon les joueurs présents", True,
       aide="Si des joueurs ont un profil, les jeux utilisent les films vus par tous (intersection de leurs listes), "
            "plus les listes ajoutées pour chaque jeu (bouton Listes)."),
    _p("profils_fichier", "general", "Profils : compter aussi les films du fichier importé", False,
       aide="Sinon le fichier importé ne sert que pour les notes (et pour les profils sans liste)."),
    _p("sagas", "general", "Films d'une saga : le nom de la saga suffit", True,
       aide="Jeux où l'on devine un film : « Harry Potter » est accepté et affiché pour tous les Harry Potter."),
    _p("films_uniques", "general", "Chrono et Bingo : un film déjà donné lors d'une manche précédente ne compte plus",
       True, aide="Pour ne pas répondre « Intouchables » à chaque « film français »."),
    _p("realisateurs_fichier", "general", "Chrono et Bingo : fichier de réalisateurs (.txt)", "realisateurs.txt",
       type="texte", placeholder="realisateurs.txt",
       aide="Un nom par ligne. Les réalisateurs des conditions viennent toujours de ce fichier (comme les acteurs de "
            "acteurs.txt) ; chaque profil peut cocher ceux qu'il connaît (bouton Profils)."),

    _p("dur_affiche", "affiche", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("aff_puissance", "affiche", "Puissance des effets au départ", 8, 1, 10),
    _p("aff_effets", "affiche", "Nombre d'effets combinés", 4, 2, 10),
    _p("aff_etapes", "affiche", "Étapes de simplification", 12, 4, 24,
       aide="Les effets diminuent régulièrement (en ligne droite) pendant toute la manche."),
    _p("aff_final", "affiche", "Effets restants à la toute fin (% du départ)", 10, 0, 100, 5,
       aide="10 % : l'affiche n'est presque nette qu'à la fin de la manche."),

    _p("dur_plans", "plans", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("plans_intervalle", "plans", "Secondes entre deux plans", 6.0, 1, 30, 0.5),
    _p("plans_source", "plans", "Origine des images", "auto", type="choix", choix=SOURCES_PLANS,
       aide="Automatique : dossier plans/, puis vos vidéos, sinon TMDB."),
    _p("plans_dossier", "plans", "Dossier de vos films (sous-dossiers compris)", "", type="texte",
       aide="Les plans sont extraits de vos fichiers vidéo avec ffmpeg. Le dossier plans/ du jeu passe avant."),

    _p("dur_casting", "casting", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("casting_max", "casting", "Acteurs principaux au maximum", 6, 2, 10),
    _p("casting_intervalle", "casting", "Secondes entre deux acteurs", 2.5, 0.5, 15, 0.5),
    _p("casting_ordre", "casting", "Ordre d'apparition (toujours parmi les acteurs principaux)", "hasard", type="choix",
       choix=ORDRE_CASTING),

    _p("dur_filmo", "filmo", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("filmo_max", "filmo", "Films (tirés au hasard parmi ses 16 plus connus)", 8, 2, 12),
    _p("filmo_intervalle", "filmo", "Secondes entre deux films", 2.5, 0.5, 15, 0.5),

    _p("dur_anagramme", "anagramme", "Durée d'une manche (s)", 35, 15, 180, 5),
    _p("ana_lettres", "anagramme", "Lettres placées au final (% du titre)", 40, 0, 90, 5),
    _p("ana_debut", "anagramme", "Début du placement des lettres (% du temps)", 40, 0, 90, 5),

    _p("dur_synopsis", "synopsis", "Durée d'une manche (s)", 35, 15, 180, 5),
    _p("syn_debut", "synopsis", "Texte visible au début (%)", 35, 5, 100, 5),

    _p("dur_blind", "blindtest", "Durée d'une manche (s)", 25, 10, 90, 5),
    _p("blind_indices", "blindtest", "Indices (genre, année, acteurs, compositeur)", True),
    _p("blind_affiche", "blindtest", "Indice : l'affiche très floue, qui se précise un peu", True),
    _p("blind_titre", "blindtest", "Indice : les premières lettres du titre (à la fin)", True),
    _p("blind_top", "blindtest", "Morceau tiré parmi les N plus écoutés de la BO", 5, 1, 15),

    _p("dur_persos", "persos", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("persos_max", "persos", "Personnages au maximum", 5, 3, 8),
    _p("persos_intervalle", "persos", "Secondes entre deux personnages", 3.5, 0.5, 15, 0.5),
    _p("persos_indices", "persos", "Indices (année et genre, réalisateur, acteurs, titre à trous)", True),

    _p("comp_mode", "complice", "Qui choisit son film préféré ?", "tous", type="choix", choix=MODES_COMPLICE),
    _p("comp_meneur", "complice", "Meneur (mode « Meneur fixe »)", "", type="joueur"),
    _p("comp_confirmer", "complice", "Bouton « Valider » après avoir touché un film", True),
    _p("comp_films", "complice", "Films proposés", 6, 3, 12),
    _p("comp_dur_choix", "complice", "Temps pour choisir son film (s)", 25, 10, 120, 5),
    _p("comp_dur_devine", "complice", "Temps pour deviner (s)", 20, 10, 120, 5),
    _p("comp_pts_devin", "complice", "Points pour une bonne réponse", 500, 0, 2000, 50),
    _p("comp_bonus_rang", "complice", "Bonus du 1er à trouver (dégressif)", 300, 0, 1000, 50),
    _p("comp_bonus_vitesse", "complice", "Bonus de rapidité maximal", 200, 0, 1000, 50),
    _p("comp_pts_meneur", "complice", "Points du meneur par joueur qui le devine", 250, 0, 1000, 25),
    _p("comp_pts_tous", "complice", "Bonus du meneur si tout le monde le devine", 250, 0, 2000, 50),
    _p("comp_remontada", "complice", "Remontada : % de l'écart avec le leader (max 300)", 20, 0, 100, 5),
    _p("comp_rev_pas", "complice", "Révélation : secondes par joueur", 3.5, 1.5, 10, 0.5),

    _p("dur_norma", "norma", "Durée d'une manche (s)", 20, 10, 90, 5),
    _p("norma_pts", "norma", "Points pour la note exacte", 1000, 100, 3000, 50,
       aide="Rien si la note n'est pas exacte."),
    _p("norma_vitesse", "norma", "Bonus de rapidité maximal (note exacte)", 200, 0, 1000, 50),
    _p("norma_cible", "norma", "Points de la cible quand sa note est trouvée", 150, 0, 1000, 25),

    _p("dur_shelly", "shelly", "Durée d'une manche (s)", 35, 15, 120, 5),
    _p("shelly_titre", "shelly", "Dernier indice : le titre à trous", True),

    _p("dur_leland", "leland", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("leland_nb", "leland", "Éléments affichés (dont l'intrus)", 6, 3, 8,
       aide="Jamais deux films de la même saga ou du même univers."),
    *[_p("leland_" + k, "leland", v, k not in INTRUS_DIFFICILES, bloc="Intrus possibles") for k, v in INTRUS.items()],

    _p("dur_lucy", "lucy", "Durée d'une manche (s)", 60, 20, 240, 5),
    _p("lucy_pts", "lucy", "Points par film trouvé (fixe)", 150, 10, 1000, 10),
    _p("lucy_premier", "lucy", "Bonus du 1er (le plus de films)", 400, 0, 3000, 50,
       aide="Le 2e reçoit la moitié, le 3e le quart."),
    _p("lucy_personnes", "lucy", "Personnes proposées (acteur, réalisateur, compositeur)", 3, 1, 5,
       aide="« Avec A, B ou C » : un film avec l'un des trois compte."),
    _p("lucy_changer", "lucy", "Bouton « Changer » sur les téléphones", True,
       aide="Quand tous les joueurs l'ont touché : nouvelle condition, le chrono repart et les films déjà donnés "
            "sont retirés (avec leurs points)."),
    *[_p("lucy_" + k, "lucy", v, True, bloc="Conditions possibles") for k, v in CONTRAINTES_LUCY.items()],

    _p("dur_donna", "donna", "Durée d'une manche (s)", 90, 30, 300, 10, aide="Doublée automatiquement en 3 × 3."),
    _p("donna_taille", "donna", "Grille", "2", type="choix", choix=TAILLES_DONNA),
    _p("donna_mode", "donna", "Conditions", "lignes", type="choix", choix=MODES_DONNA,
       aide="Lignes × colonnes : chaque case respecte la condition de sa ligne et celle de sa colonne."),
    _p("donna_grilles", "donna", "Grilles", "joueur", type="choix", choix=GRILLES_DONNA,
       aide="Une grille par joueur : les conditions « réalisateur » ne portent que sur des réalisateurs que le joueur "
            "connaît (profil)."),
    _p("donna_pts", "donna", "Points par case remplie", 250, 10, 1000, 10),
    _p("donna_bingo", "donna", "Bonus grille complète", 500, 0, 3000, 50),
    _p("donna_premier", "donna", "Bonus du 1er à finir sa grille", 400, 0, 3000, 50,
       aide="Le 2e reçoit la moitié, le 3e le quart."),
    _p("donna_malus", "donna", "Perte par condition changée (%)", 40, 0, 90, 5,
       aide="Touchez une condition, confirmez : elle change, et ses cases rapportent moins."),
    *[_p("donna_" + k, "donna", v, True, bloc="Conditions possibles") for k, v in CONTRAINTES.items()],

    _p("dur_bobby", "bobby", "Durée d'une manche (s)", 20, 10, 90, 5),
    _p("bobby_nb", "bobby", "Films proposés", 6, 3, 8),
    _p("bobby_sens", "bobby", "Il faut trouver…", "mieux", type="choix", choix=SENS_BOBBY),
    _p("bobby_indice", "bobby", "Indice : une note révélée à mi-temps", True),

    _p("dur_couleurs", "couleurs", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("couleurs_bandes", "couleurs", "Bandes horizontales au final (plus = plus net)", 12, 2, 40,
       aide="Au départ, chaque colonne de l'affiche prend sa couleur moyenne ; puis elle se coupe en bandes."),
    _p("couleurs_indices", "couleurs", "Indices (genre et année, réalisateur, titre à trous)", True),

    _p("dur_pete", "pete", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("pete_auto", "pete", "Préparer les affiches automatiquement", True,
       aide="Dès qu'une liste est incluse ou qu'un joueur se connecte avec un profil : toutes les affiches des films "
            "de Pete sont préparées en arrière-plan. Celles qui existent déjà sont réutilisées."),
    _p("pete_ordre", "pete", "Films à traiter en premier", "connus", type="choix", choix=ORDRES_PETE),
    _p("pete_textes", "pete", "Effacer le titre, les textes et les logos", True),
    _p("pete_personnages", "pete", "Effacer les personnages (humains ou animés)", True),
    _p("pete_objets", "pete", "Effacer aussi le sujet principal (objet, véhicule, créature…)", True,
       aide="Il ne reste que le décor. L'affiche peut être largement reconstruite."),
    _p("pete_indices", "pete", "Indices (genre et année, réalisateur, titre à trous)", True),

    _p("dur_briggs", "briggs", "Durée d'une manche (s)", 35, 10, 120, 5),
    _p("briggs_max", "briggs", "Mots-clés au maximum", 8, 4, 12),
    _p("briggs_indices", "briggs", "Indices (année et genre, titre à trous)", True),

    _p("dur_albert", "albert", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("albert_choix", "albert", "Propositions (dont la bonne)", 6, 3, 8),
    _p("albert_tiers", "albert", "Indice : un troisième film qui partage le même lien", True),
    _p("albert_elimine", "albert", "Indice : la moitié des fausses pistes s'efface", True),
    *[_p("albert_" + k, "albert", v, True, bloc="Liens possibles") for k, v in LIENS_ALBERT.items()],

    _p("dur_nadine", "nadine", "Durée d'une manche (s)", 35, 10, 120, 5),
    _p("nadine_nb", "nadine", "Films à accrocher", 5, 3, 8),
    _p("nadine_ecart", "nadine", "Écart minimal entre deux films (années)", 2, 0, 10,
       aide="Jamais deux films de la même année."),
    _p("nadine_pts", "nadine", "Points par film bien placé", 150, 10, 1000, 10),
    _p("nadine_parfait", "nadine", "Bonus frise parfaite", 400, 0, 2000, 50),
    _p("nadine_indice", "nadine", "Indice à mi-temps : l'année d'un des films", True),

    _p("dur_andy", "andy", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("andy_etapes", "andy", "Étapes du dessin", 10, 4, 20),
    _p("andy_acteurs", "andy", "Part des manches où il faut trouver un acteur (%)", 30, 0, 100, 10,
       aide="Le reste : l'affiche (sans texte) d'un film à trouver."),
    _p("andy_realisateurs", "andy", "Part des manches où il faut trouver un réalisateur (%)", 10, 0, 100, 5),
    _p("andy_indices", "andy", "Indices (genre et année, titre à trous)", True),

    _p("dur_ben", "ben", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("ben_choix", "ben", "Montants proposés par page (dont le bon)", 4, 3, 6),
    _p("ben_pts", "ben", "Points (les deux justes ; la moitié pour un seul)", 1000, 100, 3000, 50),
    _p("ben_indices", "ben", "Indice : deux montants faux s'effacent sur chaque page", True),

    _p("dur_josie", "josie", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("josie_nb", "josie", "Affirmations (dont le mensonge)", 6, 3, 8),
    _p("josie_indice", "josie", "Indice à mi-temps : des affirmations vraies sont barrées", True),

    _p("dur_maddy", "maddy", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("maddy_choix", "maddy", "Personnages proposés (dont le bon)", 4, 3, 6),
    _p("maddy_indice", "maddy", "Indice à mi-temps : un mauvais personnage s'efface", True),

    _p("dur_james", "james", "Durée d'une manche (s)", 35, 10, 120, 5),
    _p("james_pistes", "james", "Morceaux au maximum", 10, 4, 16),
    _p("james_indices", "james", "Indices (genre et année, pochette floue, titre à trous)", True),

    _p("dur_ed", "ed", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("ed_tolerance", "ed", "Les points baissent jusqu'à … minutes d'écart", 60, 10, 180, 5,
       aide="La réponse la plus proche gagne toujours son bonus ; au-delà de cet écart, plus de points d'écart."),
    _p("ed_pts", "ed", "Points (réponse exacte)", 800, 100, 3000, 50),
    _p("ed_proche", "ed", "Bonus du plus proche (il gagne toujours)", 400, 0, 1000, 50),
    _p("ed_cinq", "ed", "Bonus à 5 minutes près", 200, 0, 1000, 50),
    _p("ed_indice", "ed", "Indice à mi-temps : une fourchette de 40 minutes", True),

    _p("dur_loglady", "loglady", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("loglady_indices", "loglady", "Indices (genre et année, titre à trous)", True),

    _p("dur_leo", "leo", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("leo_duels", "leo", "Duels par manche", 4, 2, 6),
    _p("leo_pts", "leo", "Points par duel gagné", 250, 10, 1000, 10),
    _p("leo_parfait", "leo", "Bonus si tous les duels sont gagnés", 300, 0, 2000, 50),
    *[_p("leo_" + k, "leo", v, True, bloc="Duels possibles") for k, v in
      {"annee": "Le plus récent", "duree": "Le plus long", "note": "Le mieux noté", "recettes": "Le plus rentable"}.items()],

    _p("dur_geant", "geant", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("geant_trous", "geant", "Titre à trous à la fin", True),

    _p("dur_catherine", "catherine", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("catherine_trous", "catherine", "Titre à trous à la fin", True),

    _p("dur_denise", "denise", "Durée d'une manche (s)", 40, 10, 120, 5),
    _p("denise_realisateurs", "denise", "Part des manches avec un réalisateur (%)", 25, 0, 100, 5),

    _p("dur_phillip", "phillip", "Durée d'une manche (s)", 40, 10, 120, 5),
    _p("phillip_realisateurs", "phillip", "Part des manches avec un réalisateur (%)", 25, 0, 100, 5),
    _p("phillip_lien", "phillip", "Part des manches où un ou deux complices disent un film fait ensemble (%)", 60, 0, 100, 5),
    _p("dur_jerry", "jerry", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("dur_hank", "hank", "Durée maximale d'une manche (s)", 180, 60, 600, 10),
    _p("hank_tour", "hank", "Temps pour retirer un domino à son tour (s)", 20, 5, 90, 5),
    _p("hank_pts", "hank", "Points pour un film deviné sans aucun indice", 1000, 100, 3000, 50),
    _p("hank_pas", "hank", "Points en moins par domino retiré par le joueur visé", 150, 0, 1000, 10),
    _p("hank_mini", "hank", "Points minimum pour un film deviné", 200, 0, 1000, 10),
    _p("hank_cible", "hank", "Points pour celui dont le film est trouvé (par devin)", 150, 0, 1000, 10),
    _p("hank_erreur", "hank", "Points perdus pour une mauvaise devinette", 100, 0, 1000, 10),
    _p("hank_retire", "hank", "Points perdus si l'on retire le film d'un autre joueur (la manche s'arrête)", 600, 0, 3000, 10),

    _p("dur_carl", "carl", "Durée d'une manche (s)", 45, 10, 120, 5),
    _p("carl_indices", "carl", "Indices (genres, années, titres à trous)", True),
    _p("carl_pts", "carl", "Points par film trouvé", 600, 0, 3000, 50),
    _p("carl_deux", "carl", "Bonus si les deux films sont trouvés", 300, 0, 3000, 50),
    _p("jerry_indices", "jerry", "Indices (genre et année, mots sous les images)", True),

    _p("dur_annie", "annie", "Durée d'une manche (s)", 40, 10, 120, 5),
    _p("annie_indice", "annie", "Indice : deux affiches qui ont leur écharpe barrées à mi-temps", True),
    _p("dur_dougie", "dougie", "Durée d'une manche (s)", 45, 15, 120, 5),
    _p("dougie_indices", "dougie", "Indices : les années sous les rouleaux, puis les initiales", True),
    _p("dougie_pts", "dougie", "Points par film trouvé", 300, 0, 3000, 50),
    _p("dougie_tous", "dougie", "Bonus si les cinq films sont trouvés", 500, 0, 3000, 50),
    _p("dur_mike", "mike", "Durée d'une manche (s)", 25, 10, 120, 5),
    _p("mike_indice", "mike", "Indice : l'acteur de chaque personnage à mi-temps", True),
    _p("mike_pts", "mike", "Points par paire juste", 250, 0, 2000, 50),
    _p("mike_tous", "mike", "Bonus si les quatre paires sont justes", 400, 0, 3000, 50),
    _p("dur_windom", "windom", "Durée maximale d'une partie de pendule (s)", 420, 60, 1200, 30),
    _p("windom_temps", "windom", "Pendule de chaque joueur (s)", 40, 10, 180, 5),
    _p("windom_rapide", "windom", "Répondre en moins de … s rend du temps", 10, 0, 60, 1),
    _p("windom_bonus", "windom", "Temps rendu (s)", 5, 0, 30, 1),
    _p("windom_max_lien", "windom", "Un même lien sert au plus … fois", 3, 1, 10),
    _p("windom_pts", "windom", "Points du vainqueur (le 2e en a la moitié, etc.)", 1000, 0, 5000, 50),
    _p("windom_film", "windom", "Points par film cité", 50, 0, 500, 10),
    _p("dur_harold", "harold", "Durée d'une manche (s)", 40, 15, 120, 5),
    _p("harold_indices", "harold", "Indices (genre, titre à trous)", True),
    _p("dur_jacques", "jacques", "Durée d'une manche (s)", 40, 10, 120, 5),
    _p("jacques_indice", "jacques", "Indice : le métier de la personne commune", True),
    _p("jacques_pts", "jacques", "Points pour le brelan exact", 1000, 0, 3000, 50),
    _p("sarah_flash", "sarah", "Durée de chaque affiche de la vision (s)", 0.2, 0.1, 3, 0.05),
    _p("sarah_nb", "sarah", "Nombre de films dans la vision", 12, 3, 16),
    _p("sarah_modifs", "sarah", "Affiches retouchées (inversées, à l'envers…) (%)", 35, 0, 100, 5),
    _p("dur_sarah", "sarah", "Temps pour répondre après la vision (s)", 15, 5, 60, 5),
    _p("jean_dur_mise", "jean", "Temps pour miser (s)", 12, 5, 60, 1),
    _p("dur_jean", "jean", "Temps pour jouer sa main (s)", 45, 15, 180, 5),
    _p("jean_pts", "jean", "Points quand on bat Jean (en plus de la mise doublée)", 200, 0, 2000, 50),
    _p("jean_votes", "jean", "Cartes : films notés par au moins … votants TMDB", 200, 0, 5000, 50),
    _p("dur_woodsman", "woodsman", "Durée d'une manche (s)", 75, 20, 240, 5),
    _p("woodsman_pts", "woodsman", "Points pour qui trouve le film", 800, 0, 3000, 50),
    _p("woodsman_premier", "woodsman", "Bonus pour le premier", 300, 0, 2000, 50),
    _p("mitchum_min", "mitchum", "Minuterie : au plus tôt (s)", 30, 15, 120, 5),
    _p("mitchum_max", "mitchum", "Minuterie : au plus tard (s)", 45, 15, 120, 5),
    _p("mitchum_pct", "mitchum", "Points perdus par contrat tenu quand ça éclate (%)", 20, 0, 100, 5),
    _p("mitchum_mini", "mitchum", "Perte minimum par contrat tenu", 200, 0, 2000, 50),
    _p("mitchum_passe", "mitchum", "Points chaque fois qu'on refile un contrat", 50, 0, 1000, 10),
    _p("mitchum_penalite", "mitchum", "Pénalité après une mauvaise réponse (s)", 2.0, 0, 10, 0.5),
    _p("mitchum_affiches", "mitchum", "Questions « Quel film ? » sur un gros plan d'affiche", True),
    _p("dur_mrc", "mrc", "Durée d'une manche (s)", 50, 15, 180, 5),
    _p("mrc_pts", "mrc", "Points par différence (plus tôt = plus)", 400, 0, 2000, 50),
    _p("mrc_malus", "mrc", "Points perdus par touche à côté", 50, 0, 500, 10),
    _p("mrc_erreurs", "mrc", "Touches à côté permises", 4, 1, 20),
    _p("mrc_n", "mrc", "Nombre de différences", 3, 2, 6),
    _p("dick_n", "dick", "Enveloppes par manche", 6, 2, 12),
    _p("dick_dur", "dick", "Temps pour répondre à chaque enveloppe (s)", 15, 5, 60, 1),
    _p("dick_pts", "dick", "Points pour le bon lauréat (plus vite = plus)", 500, 0, 3000, 50),
    _p("dick_bonus", "dick", "Experts : bonus pour la bonne année", 300, 0, 2000, 50),
    _p("dick_experts", "dick", "Profils experts (Oscars plus durs), séparés par des virgules", "Louison", type="texte"),
    _p("milford_n", "milford", "Enveloppes par manche", 5, 2, 10),
    _p("milford_dur", "milford", "Temps pour répondre à chaque enveloppe (s)", 15, 5, 60, 1),
    _p("milford_pts", "milford", "Points pour le bon lauréat (plus vite = plus)", 500, 0, 3000, 50),
    _p("dur_desmond", "desmond", "Durée d'une manche (s)", 180, 60, 480, 10),
    _p("desmond_or", "desmond", "Films en or à faire deviner", 6, 2, 9),
    _p("desmond_rouges", "desmond", "Films rouges", 4, 0, 8),
    _p("desmond_attente", "desmond", "Le donneur peut relancer après (s), même si tous n'ont pas fini", 25, 5, 120, 5),
    _p("desmond_pts", "desmond", "Points par bon film (devineur)", 300, 0, 2000, 50),
    _p("desmond_donneur", "desmond", "Points par bon film (donneur)", 150, 0, 2000, 50),
    _p("desmond_rouge", "desmond", "Malus du donneur par film rouge touché", 150, 0, 2000, 50),
    _p("desmond_noir", "desmond", "Malus du film noir (donneur et devineur)", 500, 0, 3000, 50),
    _p("jacques_deux", "jacques", "Points pour deux cartes justes sur trois", 300, 0, 3000, 50),

    _p("dur_hawk", "hawk", "Durée d'une manche (s)", 30, 10, 120, 5),
    _p("hawk_indices", "hawk", "Indices petit à petit (genre et année, réalisateur, acteur, personnage, titre à trous)",
       True),
]
PARAMS_PAR_CLE = {p["cle"]: p for p in PARAMS}
GROUPES = {"general": "Général", **{g: d["nom"] for g, d in JEUX.items()}}

# Anciennes valeurs par défaut : remplacées par les nouvelles si l'utilisateur ne les avait pas changées.
ANCIENS_DEFAUTS = {
    2: {"dur_affiche": 30, "aff_simplif": 24, "dur_plans": 30, "plans_intervalle": 7.0, "dur_casting": 30,
        "casting_debut": 1, "casting_intervalle": 3.0, "dur_filmo": 30, "filmo_intervalle": 3.0,
        "dur_anagramme": 45, "dur_synopsis": 45, "dur_blind": 30, "dur_persos": 30, "persos_intervalle": 4.0,
        "comp_dur_choix": 30, "comp_dur_devine": 25},
    3: {"leland_nb": 4, "bobby_nb": 4},
    5: {"donna_mode": "cases", "briggs_max": 7},
    6: {"aff_final": 0, "aff_etapes": 6, "realisateurs_fichier": "", "donna_bingo": 300},
}


def defauts():
    s = {p["cle"]: p["defaut"] for p in PARAMS}
    s.update(version=VERSION_REGLAGES, api_key="", session_id="", account_id=0, account_name="", reponse="texte",
             jeux={g: {"on": g == "affiche", "n": 5} for g in JEUX},
             listes={g: {"inc": [LISTE_DEFAUT], "exc": [], "plus": []} for g in JEUX_LISTES},
             listes_connues=[{"id": LISTE_DEFAUT, "nom": "list-pour-jeu", "nb": 0}])
    return s


def _valeur(p, v):
    t = p["type"]
    try:
        if t == "bool":
            return bool(v)
        if t == "choix":
            return v if v in p["choix"] else p["defaut"]
        if t == "joueur":
            return str(v or "").strip()[:16]
        if t == "texte":
            return str(v or "").strip().strip('"')[:500]
        x = max(p["min"], min(p["max"], float(v)))
        if t == "int":
            return int(round(x))
        pas = p.get("pas") if p.get("pas") and p["pas"] < 1 else 0.5      # réglages à virgule : au pas du réglage
        return round(round(x / pas) * pas, 3)
    except (TypeError, ValueError):
        return p["defaut"]


def _ids(x):
    if not isinstance(x, list):
        return []
    return [int(i) for i in x if not isinstance(i, bool) and str(i).lstrip("-").isdigit()]


def valider(brut, base=None):
    """Fusionne des réglages (complets ou partiels) dans base, en vérifiant chaque valeur."""
    s = copy.deepcopy(base) if base else defauts()
    if not isinstance(brut, dict):
        return s
    for cle, p in PARAMS_PAR_CLE.items():
        if cle in brut:
            s[cle] = _valeur(p, brut[cle])
    for cle in ("api_key", "session_id", "account_name"):
        if isinstance(brut.get(cle), str):
            s[cle] = brut[cle].strip()
    if isinstance(brut.get("account_id"), int):
        s["account_id"] = brut["account_id"]
    if brut.get("reponse") in MODES_REPONSE:
        s["reponse"] = brut["reponse"]
    if isinstance(brut.get("jeux"), dict):
        for g, v in brut["jeux"].items():
            if g in JEUX and isinstance(v, dict):
                if "on" in v:
                    s["jeux"][g]["on"] = bool(v["on"])
                if "n" in v:
                    s["jeux"][g]["n"] = _valeur(dict(type="int", min=1, max=50, defaut=5), v["n"])
    if isinstance(brut.get("listes"), dict):
        for g, v in brut["listes"].items():
            if g in s["listes"] and isinstance(v, dict):
                cur = s["listes"][g]
                s["listes"][g] = {k: _ids(v[k]) if k in v else list(cur.get(k, [])) for k in ("inc", "exc", "plus")}
    if isinstance(brut.get("listes_connues"), list):
        connues = {}
        for l in brut["listes_connues"]:
            if isinstance(l, dict) and _ids([l.get("id")]):
                i = _ids([l["id"]])[0]
                try:
                    nb = int(l.get("nb") or l.get("count") or 0)
                except (TypeError, ValueError):
                    nb = 0
                connues[i] = {"id": i, "nom": str(l.get("nom") or l.get("name") or f"Liste {i}")[:120], "nb": nb}
        s["listes_connues"] = list(connues.values())
    s["listes_connues"] = [dict(l, nom=SOURCES_COMPTE[l["id"]][2]) if l["id"] in SOURCES_COMPTE else l
                           for l in s["listes_connues"] if l["id"] > 0 or l["id"] in SOURCES_COMPTE]
    ids = {l["id"] for l in s["listes_connues"]}
    for i, (_, _, nom) in SOURCES_COMPTE.items():
        if i not in ids:
            s["listes_connues"].append({"id": i, "nom": nom, "nb": 0})
    if not any(v["on"] for v in s["jeux"].values()):
        s["jeux"]["affiche"]["on"] = True
    return s


def migrer(brut):
    """Réglages d'une version précédente : les anciennes valeurs par défaut laissent place aux nouvelles."""
    if not isinstance(brut, dict):
        return brut
    version = brut.get("version") if isinstance(brut.get("version"), int) else 1
    if version < 2:
        brut.pop("comp_mode", None)          # anciens réglages : Complicité repasse en devinettes croisées
    for v, anciens in ANCIENS_DEFAUTS.items():
        if version <= v:
            for cle, ancien in anciens.items():
                if cle in brut and brut[cle] == ancien:
                    brut.pop(cle)
    if version < 5:                          # Pete devient le jeu des affiches vidées ; Briggs et Albert arrivent
        listes, jeux = brut.get("listes"), brut.get("jeux")
        if isinstance(listes, dict):
            if "annee" in listes and "pete" not in listes:
                listes["pete"] = listes["annee"]
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("pete", "briggs", "albert"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        if isinstance(jeux, dict) and "annee" in jeux and "pete" not in jeux:
            jeux["pete"] = jeux["annee"]
    if version < 8:                          # nouveaux jeux : mêmes listes que l'Affiche déformée
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("nadine", "hawk", "andy", "ben", "josie"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
    if version < 9:                          # James et Big Ed : mêmes listes que l'Affiche déformée ; Ben change de règle
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("james", "ed"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        for cle in ("ben_choix", "dur_ben"):
            brut.pop(cle, None)
        for cle in ("musique_menu_source", "musique_jeu_source", "musique_menu_youtube", "musique_jeu_youtube"):
            brut.pop(cle, None)              # les playlists YouTube choisies pour le menu et la partie
    if version < 10:                         # Maddy change de jeu ; La Dame à la bûche, Leo, le Géant arrivent
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("maddy", "loglady", "leo", "geant"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        for cle in ("casting_ordre", "filmo_max", "maddy_etapes", "maddy_indices", "dur_maddy", "ed_tolerance", "ed_pts",
                    "ed_proche"):
            brut.pop(cle, None)
    if version < 11:                         # playlists remises dans le bon sens ; Josie : 6 affirmations
        for cle in ("musique_menu_source", "musique_jeu_source", "musique_menu_youtube", "musique_jeu_youtube", "josie_nb",
                    "dur_maddy", "dur_loglady"):
            brut.pop(cle, None)
    if version < 12:                         # Catherine, Carl (listes de films) ; Denise (acteurs)
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("catherine", "carl"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
    if version < 13:                         # Jerry, Hank (listes de films) ; Carl change de jeu
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("jerry", "hank"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        for cle in ("dur_carl", "dur_denise"):
            brut.pop(cle, None)
        for k in INTRUS_DIFFICILES:                # l'intrus : les catégories peu parlantes, décochées
            brut["leland_" + k] = False
    if version < 14:                         # Lil, Dougie, Mr. C, Mike (listes de films) ; Carl, Hank, Catherine changent
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("lil", "dougie", "mrc", "mike"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        for cle in ("dur_carl", "dur_hank"):
            brut.pop(cle, None)
    if version < 15:                         # Annie remplace Lil, Mr. C s'en va ; Windom, Harold, Jacques arrivent
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("annie", "dougie", "mike", "windom", "harold", "jacques", "hank"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(listes.get("lil") if g == "annie" and listes.get("lil") else modele)
            for g in ("lil", "mrc"):
                listes.pop(g, None)
        for cle in ("dur_lil", "lil_indice", "dur_mrc", "dur_mike", "mike_indice", "dur_dougie", "dur_hank"):
            brut.pop(cle, None)
        jeux = brut.get("jeux")
        if isinstance(jeux, dict):
            if "lil" in jeux and "annie" not in jeux:
                jeux["annie"] = jeux.pop("lil")
            for g in ("lil", "mrc"):
                jeux.pop(g, None)
    if version < 16:                         # v10 : nouveaux jeux, Hank et Windom changent
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("sarah", "jean", "woodsman", "mitchum", "mrc", "desmond"):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        for cle in ("dur_hank", "hank_indice", "hank_pts", "hank_parfait", "dur_mike", "dur_windom"):
            brut.pop(cle, None)
    if version < 17:                         # v11 : Jean (blackjack), Windom (pendule), Mitchum, Desmond, Sarah… changent
        listes = brut.get("listes")
        if isinstance(listes, dict):
            modele = listes.get("affiche") or listes.get("pete")
            for g in ("dick",):
                if modele and g not in listes:
                    listes[g] = copy.deepcopy(modele)
        for cle in ("sarah_flash", "sarah_nb", "mrc_film", "dur_jean", "jean_dur_mise", "jean_pts", "dur_windom",
                    "windom_indices", "mitchum_min", "mitchum_max", "mitchum_pct", "mitchum_mini", "mitchum_passe",
                    "dur_desmond", "desmond_min", "desmond_max", "hank_retire"):
            brut.pop(cle, None)
        for k in ("genre", "decennie", "periode", "acteur", "realisateur", "compositeur", "langue", "pays", "duree",
                  "note", "theme", "titre"):
            brut.pop("mitchum_" + k, None)
    brut["version"] = VERSION_REGLAGES
    return brut


def charger():
    try:
        with open(FICHIER_REGLAGES, encoding="utf-8") as f:
            brut = json.load(f)
    except (OSError, ValueError):
        brut = {}
    s = valider(migrer(brut))
    if not s["api_key"]:
        s["api_key"] = os.environ.get("TMDB_API_KEY", "") or CLE_API_DEFAUT
    return s


def sauver(s):
    try:
        with open(FICHIER_REGLAGES, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
    except OSError:
        pass
