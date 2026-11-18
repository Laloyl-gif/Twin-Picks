# Twin Picks : consignes figées

Ce fichier liste des choix **voulus et définitifs**. Toute modification du projet (à la main ou par une IA à qui l'on
renvoie le dossier) doit les respecter. Ne les changer que si la demande le dit explicitement, en citant ce fichier.

## 1. Noms des jeux

Chaque jeu a deux noms (dans `config.py`, dictionnaire `JEUX`) :

- **`titre`** : le nom Twin Peaks, affiché **en grand dans le menu** et pendant la partie (écran hôte et téléphones).
- **`nom`** : le nom technique (« Affiche vidée », « Chrono »…), utilisé dans les **réglages**, les listes, les
  messages d'erreur, et en petit au-dessus du titre dans le menu.

Les titres ci-dessous sont figés. `config.py` les vérifie au lancement (`TITRES_FIGES`) : un titre changé par erreur
arrête le programme.

| Clé         | Titre (menu)                                 | Nom technique (réglages) |
|-------------|----------------------------------------------|--------------------------|
| affiche     | Cooper's Investigation                       | Affiche déformée         |
| plans       | Truman's Files                               | Trois plans              |
| casting     | Audrey's Dance                               | Casting                  |
| anagramme   | Cole's Hearing Aid                           | Anagramme                |
| blindtest   | Diane's Tape                                 | Blind test               |
| complice    | BOB's Fire Walk With Me                      | Complicité               |
| synopsis    | Dr. Jacoby's Couch                           | Synopsis                 |
| filmo       | Laura's Secret Diary                         | Filmographie             |
| persos      | Janey-E's Owls                               | Personnages              |
| norma       | Norma's Double R                             | Devine la note           |
| shelly      | Shelly's Cherry Pie                          | La moyenne               |
| leland      | Leland's Smile                               | L'intrus                 |
| lucy        | Lucy's Hotline                               | Chrono                   |
| donna       | One-Eyed Donna's                             | Bingo                    |
| bobby       | Bobby in the Ghostwood                       | Le mieux noté            |
| couleurs    | The Man From Another Place's egdoL kcalB     | Couleurs                 |
| pete        | Pete's Percolator                            | Affiche vidée            |
| briggs      | Major Briggs' Deep Space Monitor Printouts   | Mots-clés                |
| albert      | Albert's Blue Rose Conversation              | Le lien                  |
| nadine      | Nadine's Silent Drape Runners                | La frise                 |
| hawk        | Hawk's Missing Pages                         | L'accroche               |
| andy        | Andy's Police Sketch                         | Le croquis               |
| ben         | Ben's Ghostwood Deal                         | Le box-office            |
| josie       | Josie's Double Ledger                        | Le mensonge              |
| maddy       | Maddy's Impersonation                        | Qui l'a dit ?            |
| james       | James' Just You                              | La bande originale       |
| ed          | Big Ed's Gas Farm                            | La durée                 |
| loglady     | The Log Lady's Knothole                      | Ce que la bûche a vu     |
| leo         | Leo's New Shoes                              | Plus ou moins            |
| geant       | The Giant's Three Clues                      | Les trois répliques      |
| catherine   | Catherine's Disguise                         | Le titre déguisé         |
| denise      | Denise's Undercover                          | Qui suis-je ?            |
| carl        | Carl's Fat Trout Trailers                    | Les deux films           |
| phillip     | Phillip's Associates                         | Les complices            |
| jerry       | Jerry's Trip                                 | Le rébus                 |
| hank        | Hank's Dominoes                              | L'effet domino           |
| annie       | Annie's Miss Twin Peaks                      | L'absente                |
| dougie      | Dougie's Jackpots                            | Le jackpot               |
| mike        | Mike's Shoe Samples                          | Les paires               |
| windom      | Windom Earle's Chessboard                    | L'échiquier              |
| harold      | Harold's Orchids                             | Les pétales              |
| jacques     | Jacques Renault's Card Table                 | Le brelan                |

Version 9 (novembre 2026, à la demande d'Etienne) : Mr. C retiré ; Annie remplace Lil ; Mike, Dougie et Hank
changent de jeu (Mike's Missing Arm devient Mike's Shoe Samples) ; Windom Earle, Harold Smith, Jacques Renault arrivent.

Renommés à la demande d'Etienne (novembre 2026) : Norma's Double R (ex-Cherry Pie), Shelly's Cherry Pie
(ex-Black Coffee), Maddy's Impersonation (nouveau jeu, ex-Blonde Wig puis Look-Alike),
The Log Lady's Knothole (ex-Rings).

Un nouveau jeu reçoit un titre Twin Peaks (ajouté à ce tableau et à `TITRES_FIGES`) et un nom technique.

## 2. Menu : 3 cartes par ligne

- Le menu affiche **exactement 3 cartes par ligne**, ni plus ni moins, quelle que soit la taille de l'écran
  (`MENU_COLONNES = 3` dans `config.py` et `web/hote.js`, `grid-template-columns: repeat(3, …)` dans `web/style.css`).
- Toutes les cartes s'affichent entières, sans texte coupé ni chevauchement : quand elles ne tiennent pas, elles sont
  réparties en **pages** (flèches, points, molette, ←/→, glisser du doigt). Jamais de défilement qui coupe une carte.

### Exception : le panneau du téléphone administrateur

Dans l'application Android, quand un téléphone héberge la partie (pas d'ordinateur), l'écran hôte s'ouvre en version
téléphone (`/hote?tel=1`) : deux cartes par ligne, et l'on fait défiler vers le bas. C'est la seule exception aux
3 cartes par ligne.

## 3. Ce qui reste libre

Tout le reste (règles, réglages, apparence des manches, nouveaux jeux) peut évoluer normalement.

## Interfaces des jeux

- Jamais de fond (aplat, cadre, dégradé) qui dénote du fond général de l'écran : le décor d'un jeu, ce sont des
  **objets** posés autour de la manche (tasse, donut, téléphone, registre, feuille imprimée…), dans web/decor.js.
- Jamais un objet caché derrière l'interface : les objets sont posés **par-dessus**, à cheval sur les bords, comme
  des post-it (calque `#j-colles`, `COLLES` dans web/decor.js), sans masquer un texte.
- Pas d'étiquette qui explique la référence sous un objet ou une image.
- Répliques de la série sur les interfaces : **en VO** (anglais), tirées au hasard à chaque manche parmi plusieurs
  (`REPLIQUES` dans web/decor.js) ; Cooper garde toujours « Black as midnight on a moonless night. », la pelle de
  Jacoby garde son slogan. Elles ne sont pas toujours sur un post-it : intégrées à l'interface (sous-titre de la Red
  Room, enseigne, carton, griffonnage, bulle…). Les répliques **des films** dans les jeux (Le Géant, Qui l'a dit ?)
  restent en français.
- Indices et titre à trous : leur place est réservée dès le début de la manche ; rien ne bouge quand ils arrivent.
- Jamais de barre de défilement pendant une manche : tout tient dans la fenêtre (le visuel est réduit au besoin,
  fonction `ajuster` de web/commun.js).

## Rébus (Jerry) — règles de la version 9

- Les images ont exactement les sons du titre (pas de « lait » pour « le ») ; ce qui n'a pas d'image s'écrit.
- Une image montre directement le mot (jamais une girafe pour « zoo »). Quand il faut plusieurs images, elles sont
  dans un cadre (« zoo » = girafe, lion, tigre ; « ferme » = vache, cochon, poule).
