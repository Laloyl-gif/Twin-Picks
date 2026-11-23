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
| hank        | Hank's Dominoes                              | Les dominos              |
| annie       | Annie's Miss Twin Peaks                      | L'absente                |
| dougie      | Dougie's Jackpots                            | Le jackpot               |
| mike        | Mike's Shoe Samples                          | Les paires               |
| windom      | Windom Earle's Chess Clock                   | La pendule               |
| harold      | Harold's Orchids                             | Les pétales              |
| jacques     | Jacques Renault's Card Table                 | Le brelan                |
| sarah       | Sarah Palmer's Visions                       | La vision                |
| jean        | Jean Renault's Blackjack                     | Le blackjack             |
| woodsman    | The Woodsman's Light                         | Got a light?             |
| mitchum     | The Mitchum Brothers' Contract               | Le contrat               |
| mrc         | Mr. C's Doppelganger                         | Le double                |
| desmond     | Desmond's Code                               | Le code                  |
| dick        | Dick Tremayne's Gala                         | La cérémonie             |
| milford     | Mayor Milford's Golden Owl                   | Le Hibou d'or            |
| lana        | Lana Budding's Lies                          | Les mensonges            |
| bernard     | Bernard Renault's Poker                      | Le poker                 |
| tremond     | Mrs. Tremond's Painting                      | Le tableau               |
| bushnell    | Bushnell Mullins' Rain                       | La pluie d'affiches      |
| hayward     | Doc Hayward's Secrets                        | Les secrets              |

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

## Version 10 (novembre 2026)

Jeux validés par Etienne (pitchs en oui / non) : Sarah (la vision), Jean Renault (la rançon et le marché noir),
le Woodsman (got a light?), les frères Mitchum (le contrat), Mr. C (le double), Hank (les dominos, façon Focus),
Desmond (le code, façon Codenames), Windom (le cavalier, plusieurs pièces). Les nouveaux jeux exploitent des
dimensions qui n'existaient pas : mémoire, mise de ses points et achat d'indices secrets, exploration à plusieurs
(le téléphone devient une lampe), patate chaude entre joueurs, jeu des différences, jeux de déduction et de code entre
joueurs.

## Version 11 (novembre 2026)

Validés par Etienne (QCM oui / non) : Jean Renault devient un vrai blackjack (« Jean Renault's Blackjack »), Windom
Earle devient la pendule d'échecs (« Windom Earle's Chess Clock »), le contrat des Mitchum passe à plusieurs contrats
et à des questions à six choix, deux jeux de récompenses arrivent : Dick Tremayne (la cérémonie, données Wikidata)
et le maire Dwayne Milford (le Hibou d'or, l'« Oscar » des profils). Les titres de Jean et de Windom changent avec
leur jeu (demande d'Etienne : changer ces jeux).
- Les récompenses (Oscars, Césars, Palme d'or, BAFTA, Golden Globes, Lion d'or, Ours d'or) s'ajoutent aux indices de
  la plupart des jeux (réglage général) ; elles viennent de Wikidata (recompenses.py, cache donnees/recompenses.json).
- La cérémonie : les profils « experts » (Louison par défaut) ont une version plus dure pour les Oscars ; tous les
  autres cas restent simples (quatre choix au plus).
- Le Hibou d'or : catégories toujours sur l'ensemble des joueurs, jamais sur un seul profil ; nommés proches, pas
  d'égalité en tête.
- Récap de fin de partie (podium, statistiques, image à partager) et anti-répétition des films entre parties.
- Refusés (ne pas reproposer) : le memory et le palmarès à cocher (Tammy), la danse de Lil en pictogrammes, le
  bonneteau, le buzzer de Freddie, le ring de Bushnell, le dossier chiffré de Tammy, joker, réactions emoji.

## Version 12 (novembre 2026)

Validés par Etienne (QCM) : Lana Budding (les mensonges, façon Fibbage), Bernard Renault (le poker à règles cachées,
défausse qui coûte un pourcentage du gain), Mrs. Tremond (le tableau, façon Dixit, avec une règle à deux joueurs),
Bushnell Mullins (la pluie d'affiches), le Dr Hayward (les anecdotes de tournage, Wikipédia FR) ; le palmarès à vie ;
le logo K (Cooper pouce levé en sérigraphie, d'après l'image fournie par Etienne, devant la Red Room).
Corrections : la pendule affiche les 40 s de chacun en texte ; un contrat par joueur ; le Hibou d'or : une enveloppe
par manche, des films toujours différents.
Refusés (ne pas reproposer) : Les scellés (Connections), Le cas rare (Pointless), Le road trip (GeoGuessr), Le duo
(coop à voix haute), Le gong (Snap), Le tape-taupe, Le Time's Up de Johnny ; mode équipes, règle animée, vote du jeu
suivant, bruitages, soirées toutes prêtes, niveaux par profil, rattrapage.
Envies d'Etienne pour la suite : jeux de bluff / entre joueurs et de rapidité, originaux, inspirés de jeux de société.
