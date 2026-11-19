"""Le vocabulaire en images des rébus (Jerry's Trip) : seulement des mots que l'image montre directement (un chat 🐈,
pas un oiseau pour « pie »). Quand une seule image ne suffit pas, plusieurs images dans un cadre la composent
(« zoo » = [🦒🦁🐯], « ferme » = [🐄🐖🐔]). Leur son est calculé par phonetique.py ; un même son peut avoir
plusieurs images (« dé » ou « deux » ? on tire au sort parmi les mots qui sonnent pareil)."""
from .phonetique import mot as son_de

MOTS = """
roi=🤴 reine=👸 rat=🐀 riz=🍚 roue=🛞 rose=🌹 robe=👗 rire=😂 robot=🤖 renard=🦊 requin=🦈 radio=📻 raisin=🍇
lait=🥛 lit=🛏️ loup=🐺 lune=🌙 lion=🦁 lapin=🐇 loupe=🔍 lettre=✉️ livre=📖 langue=👅 laine=🧶 lézard=🦎 loutre=🦦
lama=🦙 lèvres=👄 lunettes=👓 lacet=👟
mur=🧱 mer=🌊 main=✋ miel=🍯 mouche=🪰 mouton=🐑 moto=🏍️ masque=🎭 marteau=🔨 maïs=🌽 melon=🍈 micro=🎤 montre=⌚
mont=⛰️ manteau=🧥 mangue=🥭 mains=🙌
pain=🍞 pied=🦶 pomme=🍎 pont=🌉 porc=🐖 poule=🐔 paon=🦚 sapin=🎄 pinceau=🖌️ piano=🎹 pile=🔋 papillon=🦋 poire=🍐
poisson=🐟 pizza=🍕 pouce=👍 poing=👊 panda=🐼 pingouin=🐧 pieuvre=🐙 pois=🫛 poêle=🍳 pêche=🍑 pastèque=🍉
pirate=🏴‍☠️ parapluie=☂️ pomme=🍏 pain=🥖 patin=⛸️ panier=🧺 piment=🌶️ poulet=🍗 prune=🫐 pelle=🪏
bol=🥣 bain=🛁 ballon=🎈 balle=⚽ bague=💍 bébé=👶 bougie=🕯️ bus=🚌 bulle=🫧 beurre=🧈 bière=🍺 banane=🍌 bateau=⛵
bombe=💣 bonbon=🍬 botte=👢 bouche=👄 bras=💪 brosse=🪥 bois=🪵 blé=🌾 bouteille=🍾 bonhomme=⛄ boussole=🧭 boîte=📦
thé=🍵 tour=🗼 tente=⛺ tasse=☕ tigre=🐯 tomate=🍅 train=🚆 taxi=🚕 tortue=🐢 trois=3️⃣ tram=🚋 terre=🌍 tambour=🥁
téléphone=☎️ tulipe=🌷 trompette=🎺 tracteur=🚜 tournevis=🪛 tronc=🪵 trèfle=♣️ tête=🙂
dé=🎲 deux=2️⃣ dent=🦷 doigt=☝️ dinde=🦃 dix=🔟 drapeau=🚩 dragon=🐉 disque=💿 dauphin=🐬 diamant=💎 dame=♛
coq=🐓 clé=🔑 cor=📯 corde=🪢 cœur=❤️ kiwi=🥝 koala=🐨 cadeau=🎁 café=☕ camion=🚚 canot=🛶 carte=🃏 cible=🎯
cinq=5️⃣ cochon=🐷 crabe=🦀 crâne=💀 croissant=🥐 couteau=🔪 couronne=👑 cloche=🔔 clown=🤡 carotte=🥕 chameau=🐫
castor=🦫 coco=🥥 cactus=🌵 cerveau=🧠 caméra=🎥 casque=🪖 canard=🦆 carreau=♦️ quatre=4️⃣ cuillère=🥄
gant=🧤 gâteau=🍰 guitare=🎸 glace=🍦 globe=🌐 gorille=🦍 grenouille=🐸 glaçon=🧊 goutte=💧 gaufre=🧇
fée=🧚 feu=🔥 fil=🧵 fleur=🌸 flûte=🪈 fraise=🍓 frite=🍟 fusée=🚀 fromage=🧀 fantôme=👻 fourchette=🍴 fenêtre=🪟
flèche=➡️ feuille=🍃 fourmi=🐜 ferme=[🐄🐖🐔] fruit=[🍎🍐🍊]
vin=🍷 vent=🌬️ ver=🪱 verre=🥃 vélo=🚲 vache=🐄 vase=🏺 vague=🌊 voiture=🚗 violon=🎻 vampire=🧛 volcan=🌋
scie=🪚 seau=🪣 sac=👜 sel=🧂 six=6️⃣ sang=🩸 cent=💯 singe=🐒 sirène=🧜‍♀️ soleil=☀️ savon=🧼 souris=🐭
serpent=🐍 cerise=🍒 cerf=🦌 citron=🍋 cygne=🦢 sept=7️⃣ soupe=🍲 stylo=🖊️ ski=🎿 skate=🛹 sorcière=🧙‍♀️ sablier=⏳
zéro=0️⃣ zoo=[🦒🦁🐯] zèbre=🦓
chat=🐈 chien=🐕 chaise=🪑 chapeau=🎩 château=🏰 chef=🧑‍🍳 cheval=🐎 chèvre=🐐 chouette=🦉 hibou=🦉 chocolat=🍫
chaîne=⛓️ chaussure=👞 chemise=👔 champignon=🍄 chaussette=🧦 chameau=🐪
jambe=🦵 girafe=🦒 jus=🧃 journal=📰 jean=👖 jongleur=🤹
nez=👃 nid=🪺 nœud=🎀 nuit=🌃 neuf=9️⃣ neige=❄️ note=🎵 nouilles=🍜 nuage=☁️ navire=🚢
œuf=🥚 œil=👁️ oie=🪿 os=🦴 ours=🐻 eau=💧 olive=🫒 oignon=🧅 orange=🍊 oreille=👂 orage=⛈️
âne=🫏 arbre=🌳 arc=🏹 ail=🧄 aile=🪽 aigle=🦅 avion=✈️ ananas=🍍 ancre=⚓ abeille=🐝 ange=👼 épée=🗡️ araignée=🕷️
escargot=🐌 étoile=⭐ éléphant=🐘 enfant=🧒 hérisson=🦔 avocat=🥑 aubergine=🍆 ampoule=💡 aimant=🧲
île=🏝️ hache=🪓 herbe=🌿 heure=🕐 huit=8️⃣ un=1️⃣ huître=🦪
yoyo=🪀 wagon=🚃 kangourou=🦘 rhinocéros=🦏 citrouille=🎃 pluie=🌧️ arc-en-ciel=🌈 noël=🎄 famille=👪 musique=🎶
fête=🎉 danse=💃 couple=💑 jeux=[🎲🃏🎮] hiver=[⛄❄️] pique=♠️ roche=🪨 caillou=🪨
lampe=🪔 tige=🌱 feux=🚦 bougies=🕯️ rideau=🎭 sous=🪙 clou=📌 punaise=📌 scène=🎭 roc=🪨
baleine=🐋 crocodile=🐊 dinosaure=🦕 flamant=🦩 hamster=🐹 hippopotame=🦛 léopard=🐆 licorne=🦄 mammouth=🦣
perroquet=🦜 phoque=🦭 poulpe=🐙 scorpion=🦂 taureau=🐂 chauve-souris=🦇 crevette=🦐 homard=🦞 coccinelle=🐞
moustique=🦟 grillon=🦗 dodo=🦤 zombie=🧟 ninja=🥷 police=👮 pompier=🧑‍🚒 prince=🤴 père-noël=🎅 sapin=🎄
burger=🍔 brocoli=🥦 châtaigne=🌰 concombre=🥒 crêpe=🥞 hot-dog=🌭 popcorn=🍿 salade=🥗 sandwich=🥪 sushi=🍣
taco=🌮 bretzel=🥨 beignet=🍩 biscuit=🍪 sucette=🍭 tarte=🥧 cocktail=🍸 lard=🥓 champagne=🍾 pain=🍞
crayon=✏️ ciseaux=✂️ cadenas=🔒 boomerang=🪃 échelle=🪜 horloge=🕰️ lanterne=🏮 miroir=🪞 parachute=🪂 plume=🪶
poubelle=🗑️ valise=🧳 cravate=👔 bikini=👙 casquette=🧢 kimono=👘 coupe=🏆 médaille=🏅 trophée=🏆 tournesol=🌻
montagne=🏔️ plage=🏖️ désert=🏜️ éclair=⚡ tornade=🌪️ maison=🏠 église=⛪ usine=🏭 hôpital=🏥 école=🏫 banque=🏦
cirque=🎪 stade=🏟️ hélicoptère=🚁 ambulance=🚑 métro=🚇 traîneau=🛷 roller=🛼 saxophone=🎷 golf=⛳ tennis=🎾
boxe=🥊 pion=♟️ bougie=🕯️ bouée=🛟 aimant=🧲 ampoule=💡 savon=🧼 fusée=🚀 éponge=🧽 brosse=🪥
seringue=💉 pilule=💊 loupe=🔍 lune=🌙 comète=☄️ planète=🪐 satellite=🛰️ soucoupe=🛸 extraterrestre=👽 robot=🤖
diable=😈  bisou=😘 larme=😢 sommeil=😴 cri=😱 colère=😡 rire=😂 sourire=🙂
baiser=💋 squelette=💀 fantôme=👻 citrouille=🎃 sorcière=🧙‍♀️ magicien=🧙 génie=🧞 elfe=🧝 sirène=🧜‍♀️ vampire=🧛
chevalier=🛡️ bouclier=🛡️ arbalète=🏹 hache=🪓 pioche=⛏️ marteau=🔨 clé=🔑 pelle=🪏 chaîne=⛓️
dollar=💵 pièce=🪙 cible=🎯 dés=🎲 cartes=🃏 domino=🁫 billard=🎱 bowling=🎳 kayak=🛶 voile=⛵
a=🅰️ b=🅱️ o=🅾️ i=ℹ️ m=Ⓜ️ p=🅿️
""".split()

VOCAB = {}                                     # son -> [(mot, émoji ou [émojis encadrés])]
for entree in MOTS:
    mot_ecrit, emo = entree.split("=")
    mot_ecrit = mot_ecrit.rstrip("_")
    s = son_de(mot_ecrit)
    if s and (mot_ecrit, emo) not in VOCAB.setdefault(s, []):
        VOCAB[s].append((mot_ecrit, emo))
LONGUEUR_MAX = max(len(s) for s in VOCAB) + 1
