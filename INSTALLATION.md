# Twin Picks : installation (toujours à jour)

Le jeu vit dans un **dépôt GitHub**. Les ordinateurs (raccourci du bureau) et les téléphones (application Android) vont
toujours y chercher la dernière version : on ne déplace plus jamais de fichiers à la main.

```
                 GitHub : compte/twin-picks
        ┌───────────────┬───────────────────────────┐
  branche main          branche plans               Releases
  (le code du jeu)      (les plans de Truman)       (l'application Android)
        │                       │                           │
  raccourci du bureau   téléchargés à la demande    twin-picks.apk
  (git pull à chaque    (seulement les images       (télécharge le code
   lancement)            utilisées, gardées)          à chaque lancement)
```

Ce qui est propre à chaque appareil (réglages, profils, caches, images du menu ajoutées…) est dans `donnees/`, que
git ignore : une mise à jour ne l'efface jamais.

---

## 1. Une seule fois : mettre le jeu sur GitHub

1. Créez un compte sur <https://github.com> si besoin, puis un **dépôt public** vide nommé par exemple `twin-picks`
   (public : l'application Android et les plans le lisent sans mot de passe).
2. Installez **Git** (<https://git-scm.com/download/win>) et **Python 3.11 ou plus** (<https://www.python.org/downloads/>,
   cochez « Add python.exe to PATH »).
3. Dézippez `twin_picks.zip` là où vous voulez garder le jeu (par exemple `Documents\twin_picks`).
4. Double-cliquez `outils\premiere_publication.bat` et collez l'adresse du dépôt
   (`https://github.com/COMPTE/twin-picks`). Git demande de se connecter à GitHub la première fois.

## 2. Sur chaque ordinateur : le raccourci du bureau

- **L'ordinateur qui a publié le jeu** : double-cliquez `installer.bat` dans le dossier du jeu.
- **Un autre ordinateur** : installez Git et Python, puis dans un terminal :
  `git clone https://github.com/COMPTE/twin-picks` et double-cliquez `installer.bat` dans le dossier créé.
- macOS / Linux : `sh installer.sh`.

Le raccourci **Twin Picks** apparaît sur le bureau. Il lance `lancer.bat`, qui à chaque fois :

1. récupère la dernière version (`git pull`) ; hors ligne, on joue avec la version déjà là ;
2. installe les modules Python si la liste a changé ;
3. lance le jeu (l'écran hôte s'ouvre dans le navigateur).

Le raccourci ne change jamais : c'est toujours la dernière version qui démarre.

## 3. Publier une nouvelle version

Glissez le `.zip` reçu sur `outils\publier_version.bat`. Le code du dépôt est remplacé par celui du zip puis envoyé
sur GitHub. Ordinateurs et téléphones se mettent à jour d'eux-mêmes au prochain lancement.

## 4. L'application Android

Dès que le dossier `android/` est sur GitHub, **GitHub Actions** construit l'application (onglet *Actions* du dépôt,
3 à 6 minutes la première fois) et la publie à une adresse fixe :

    https://github.com/COMPTE/twin-picks/releases/download/application/twin-picks.apk

Sur le téléphone : ouvrez ce lien, téléchargez, ouvrez le fichier et autorisez l'installation (« sources inconnues »).
L'application elle-même change rarement. À chaque lancement, elle :

1. **se met à jour** : elle télécharge la dernière version du jeu (branche `main`) si elle a changé ;
2. **cherche une partie sur le Wi-Fi** :
   - un ordinateur a lancé le jeu → elle rejoint sa partie (l'ordinateur est l'administrateur, il n'est pas joueur) ;
   - un autre téléphone a déjà ouvert une partie → elle la rejoint ;
   - sinon, **ce téléphone ouvre la partie et en devient l'administrateur** ;
3. ouvre le choix du pseudo, de la couleur, de la photo et du profil, puis, pour l'administrateur, le **menu** en
   version téléphone (deux cartes par ligne, on fait défiler), les réglages, les listes, Lancer, Pause, Passer…

Tout le monde sur le même Wi-Fi arrive dans la même partie. Seul l'administrateur (l'ordinateur, ou le téléphone qui a
ouvert la partie) peut changer les jeux et les réglages : il a un bouton rouge « Partie » en haut à droite.

À savoir :
- Lancez le jeu sur l'ordinateur **avant** d'ouvrir l'application, pour que les téléphones rejoignent l'ordinateur.
- Le téléphone qui héberge doit rester dans l'application (écran allumé : l'application l'empêche de s'éteindre).
- Sur téléphone, « Affiche vidée » (Pete) marche en mode simplifié (sans les outils de détection lourds).
- La toute première ouverture a besoin d'Internet (pour télécharger le jeu).

## 5. Les plans de Truman's Files (plus tard)

Les plans sont sur la branche `plans` du même dépôt. Le jeu tire toujours un film au hasard parmi tous les films des
listes choisies : si ce film a des plans, ils sont pris là (le plus dur, puis le moyen, puis le plus facile) ; sinon,
les images de TMDB. Seules les images utilisées sont téléchargées, puis gardées dans `donnees/plans_cache/`.

Pour mettre des plans en ligne :

1. `python outils/preparer_plans.py plans.zip` : range chaque film en trois niveaux
   (`1_difficile/`, `2_moyen/`, `3_facile/`) et écrit `index.json` dans `donnees/plans_tries/`.
   - images déjà rangées dans ces trois dossiers : gardées telles quelles ;
   - images numérotées (01 = la plus difficile) : coupées en trois tranches ;
   - sinon, la difficulté est estimée (gros plans, visages, couleurs…).
   Nommez les dossiers `Titre (année) [tmdb-123]` (l'identifiant TMDB évite toute confusion), ou au moins
   `Titre (année)`.
2. `python outils/publier_plans.py` : les envoie sur la branche `plans`.

Un dossier `plans/` posé à côté du jeu marche aussi (il passe en premier) : pratique pour essayer.
La Dame à la bûche utilise aussi ces plans (les moyens et les faciles).

## Rejoindre avec le code de la partie

Le code (5 caractères) est affiché sur l'écran hôte. Sur le téléphone : « Rejoindre une autre partie avec un code ».
Sur le même Wi-Fi, ça marche toujours. Depuis un autre réseau, l'ordinateur ouvre tout seul un tunnel cloudflared
(téléchargé la première fois dans `donnees/outils`) et publie son adresse : le code suffit. Le code est gardé dans
`donnees/salle.json` (le même d'une soirée à l'autre).

## En cas de souci

- *Le raccourci ne se met pas à jour* : le dossier doit être un clone git (`installer.bat` le vérifie).
- *L'application dit « construite sans adresse de dépôt »* : relancez la construction dans l'onglet *Actions*.
- *Les téléphones ne trouvent pas l'ordinateur* : même Wi-Fi ? Le pare-feu Windows doit autoriser Python
  (réseau privé) ; on peut aussi scanner le QR code de l'écran hôte avec le navigateur du téléphone.
