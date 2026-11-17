# Application Android Twin Picks

Construite par GitHub Actions (`.github/workflows/android.yml`) avec Chaquopy (Python dans Android) :
`twin-picks.apk` est publiée dans les Releases du dépôt, à une adresse fixe (voir INSTALLATION.md).

- `app/src/main/java/fr/twinpicks/app/MainActivity.java` : l'écran (une page web plein écran) ;
- `app/src/main/python/demarrage.py` : au lancement, télécharge la dernière version du jeu depuis le dépôt
  (`GITHUB_REPOSITORY`, donné à la construction), cherche une partie sur le Wi-Fi (`reseau_local.py`), sinon ouvre la
  partie sur le téléphone (`main.demarrer_serveur("telephone")`) avec la clé d'administrateur ;
- `app/twinpicks.keystore` : clé de signature fixe (une nouvelle version de l'application s'installe par-dessus).

Construire à la main (Android Studio ou SDK installé) : `gradle assembleRelease -Pdepot=COMPTE/twin-picks` dans ce
dossier.
