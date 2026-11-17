"""Le vocabulaire en images des rébus (Jerry's Trip) : des mots faciles à dessiner, avec leur émoji. Leur son est
calculé par phonetique.py ; un même son peut avoir plusieurs images (« de » : un dé 🎲 ou un 2 ? on tire au sort
parmi les mots qui sonnent pareil)."""
from .phonetique import mot as son_de

MOTS = """
roi=👑 rat=🐀 riz=🍚 rue=🛣️ roue=🛞 ré=🎵 raie=🐟 reine=👸 rose=🌹 robe=👗 rire=😂 rôti=🍖 radis=🌱 rame=🚣
lait=🥛 lit=🛏️ loup=🐺 lune=🌙 lion=🦁 lac=🏞️ lame=🔪 lampe=💡 laine=🧶 langue=👅 lapin=🐇 larme=💧 lèvre=👄 loi=⚖️
la=🎵 las=😩 lilas=💐 loupe=🔍 lampion=🏮 lettre=✉️ livre=📖 lèche=👅 lis=🌷 lot=🎁
mur=🧱 mer=🌊 mère=👩‍👦 main=✋ mai=🌼 mie=🍞 miel=🍯 mot=💬 mou=🍮 mouche=🪰 moule=🦪 mouton=🐑 moto=🏍️ malle=🧳
masque=🎭 mât=⛵ marteau=🔨 maïs=🌽 melon=🍈 menton=🧔 mètre=📏 micro=🎤 mine=⛏️ mouette=🕊️ montre=⌚ mont=⛰️
pain=🍞 pas=👣 pot=🍯 pou=🐛 pie=🐦 pied=🦶 paix=☮️ pois=🫛 poêle=🍳 pomme=🍎 pont=🌉 porc=🐖 port=⚓ poule=🐔
paon=🦚 pin=🌲 pinceau=🖌️ pipe=🚬 piano=🎹 pile=🔋 pull=🧥 puce=🐜 puits=🕳️ paille=🥤 panneau=🪧 papa=👨 papillon=🦋
bas=🧦 beau=😍 bol=🥣 bain=🛁 banc=🪑 bal=💃 balle=⚽ ballon=🎈 bague=💍 bébé=👶 bec=🐦 bec=🦆 bise=😘 bouche=👄 bouée=🛟
bout=🔚 boue=💩 bois=🪵 bombe=💣 bonbon=🍬 botte=👢 bougie=🕯️ bus=🚌 but=🥅 bulle=🫧 beurre=🧈 bière=🍺 blé=🌾
thé=🍵 tas=🪨 toit=🏠 tour=🗼 tôle=🔩 temps=⏳ tente=⛺ tasse=☕ tête=🗣️ tigre=🐯 tomate=🍅 toux=🤧 train=🚆 trou=🕳️
taupe=🐾 taxi=🚕 tir=🎯 tonneau=🛢️ table=🍽️ tortue=🐢 trois=3️⃣ trèfle=☘️ thon=🐟 tram=🚋 tank=🪖 terre=🌍
dé=🎲 deux=2️⃣ dent=🦷 dos=🧍 doigt=☝️ dinde=🦃 dix=🔟 dôme=🕌 drap=🛏️ drapeau=🚩 dragon=🐉 dune=🏜️ disque=💿
cas=📦 car=🚌 coq=🐓 cou=🦒 coup=👊 clou=🔩 clé=🔑 col=👔 cor=📯 corde=🪢 canne=🦯 cane=🦆 cœur=❤️ quai=🚉 cube=🧊
kiwi=🥝 koala=🐨 képi=👮 cadeau=🎁 cage=🐦 café=☕ camion=🚚 canot=🛶 carte=🃏 cave=🍷 cible=🎯 ciel=🌌 cinq=5️⃣
gant=🧤 gaz=⛽ gâteau=🍰 gare=🚉 gong=🔔 goût=👅 gui=🌿 guitare=🎸 glace=🧊 globe=🌍 gomme=✏️ gorille=🦍 gourde=🫗
fée=🧚 feu=🔥 fil=🧵 fou=🤪 four=♨️ fa=🎵 faux=🌾 faon=🦌 fer=🧲 ferme=🚜 fête=🎉 fiole=🧪 flèche=🏹 fleur=🌸 flûte=🪈
foin=🌾 fraise=🍓 frite=🍟 fusée=🚀 fusil=🔫 fumée=💨 four=🔥
vin=🍷 veau=🐄 vis=🔩 vent=🌬️ ver=🪱 verre=🥛 vélo=🚲 vache=🐄 vase=🏺 vague=🌊 voile=⛵ voiture=🚗 violon=🎻 vampire=🧛
scie=🪚 seau=🪣 sou=🪙 sac=👜 sel=🧂 six=6️⃣ sang=🩸 cent=💯 sein=🫀 singe=🐒 sirène=🧜‍♀️ soleil=☀️ sapin=🎄 savon=🧼
souris=🐭 sous=🪙 serpent=🐍 cerise=🍒 cerf=🦌 citron=🍋 cygne=🦢 sept=7️⃣ sœur=👭 soupe=🍲 sucre=🍬 stylo=🖊️ sable=🏖️
zéro=0️⃣ zoo=🦒 zèbre=🦓
chat=🐈 chou=🥬 chaud=🥵 chien=🐕 chaise=🪑 chapeau=🎩 chameau=🐫 château=🏰 chef=🧑‍🍳 cheval=🐎 cheveu=💇 chiffre=🔢
chant=🎶 chaussure=👟 chemise=👕 chèvre=🐐 chouette=🦉 chocolat=🍫 chaîne=⛓️ champ=🌾 chips=🥔 cheminée=🏭
jeu=🎮 joue=😊 jus=🧃 jupe=👗 jambe=🦵 jardin=🏡 genou=🦵 girafe=🦒 gilet=🦺 jet=✈️ jonc=🌾 jour=🌞 journal=📰
nez=👃 nid=🪺 nœud=🎀 noix=🌰 nuit=🌃 nain=🧔 neuf=9️⃣ neige=❄️ note=🎵 nouille=🍜 nuage=☁️ nageur=🏊 navire=🚢
œuf=🥚 œil=👁️ oie=🪿 os=🦴 ours=🐻 eau=💧 or=🥇 orge=🌾 olive=🫒 oignon=🧅 orange=🍊 ongle=💅 orteil=🦶 ombre=👤
an=🎂 ange=👼 âne=🫏 arbre=🌳 arc=🏹 ail=🧄 aile=🪽 aigle=🦅 avion=✈️ ananas=🍍 ancre=⚓ anneau=💍 abeille=🐝 épée=⚔️
île=🏝️ igloo=🛖 indien=🪶 if=🌲 hibou=🦉 hache=🪓 haie=🌳 herbe=🌿 heure=🕐 hotte=🎅 houx=🎄 hutte=🛖
oui=✅ ouest=⬅️ ouïe=👂 âme=👻 été=☀️ étoile=⭐ œil=👁️ usine=🏭 un=1️⃣ huit=8️⃣ hublot=🚢
wagon=🚃 week-end=🗓️ western=🤠 yoyo=🪀 yaourt=🥛
lion=🦁 lit=🛏️ loupe=🔍 pomme=🍏 pin=🌲 vin=🍇 pain=🥖 rat=🐭 chat=😺 roi=🤴 mer=🏖️ feu=🧯 eau=🚿 dé=🎲
noeud=🪢 sceau=🪣 saut=🦘 seau=🧺 cou=🦢 vers=🪱 verre=🍷 thé=🫖 temps=🕰️ main=🤚 bal=🪩 bas=🧦 pas=🐾
mort=💀 mords=🦷 maire=🎗️ lait=🍼 lard=🥓 pré=🌾 prix=🏆 pro=🏅 bras=💪 brin=🌿 brosse=🪥 grain=🌾 gros=🐘 gris=🐭
croix=✝️ cri=😱 crabe=🦀 crâne=💀 craie=🖍️ creux=🕳️ fromage=🧀 front=🧠 frein=🛑 froid=🥶 frère=👬 plat=🍽️ plume=🪶
pluie=🌧️ planète=🪐 plage=🏖️ pli=📄 blanc=⬜ bleu=🟦 brun=🟫 noir=⬛ vert=🟩 rouge=🟥 jaune=🟨 rose_=🩷
trèfle=🍀 tronc=🪵 trompette=🎺 drôle=🤣 dragée=🍬 glisse=🛷 glaçon=🧊 clown=🤡 club=🏌️ clope=🚬 clan=👪
a=🅰️ i=ℹ️ o=🅾️ b=🅱️ on=🔛 œufs=🥚 bœufs=🐂 eux=👥 hé=👋 ah=😮 oh=😲 euh=🤔 ouh=👻 hi=🫢 aïe=🤕
bague=💍 bol=🥣 boule=🎱 cape=🦸 chêne=🌳 chèque=💸 colle=🧴 code=🔢 côte=🌊 dame=👵 date=📅 dinde=🦃
dune=🏜️ fête=🎊 fiche=📇 file=🚶 flaque=💦 forge=⚒️ fosse=🕳️ fourche=🍴 golf=⛳ grappe=🍇 griffe=🐾 grotte=🕳️
guêpe=🐝 harpe=🪕 jarre=🏺 lac=🏞️ lime=🍋‍🟩 linge=🧺 louche=🥄 luge=🛷 mèche=🕯️ merle=🐦‍⬛ mime=🤡 mite=🦋
mode=👠 mousse=🫧 mule=🫏 nappe=🧺 niche=🐕 nuque=💆 page=📄 palme=🌴 patte=🐾 pelle=🪏 perle=🦪 piste=🛤️
poche=👖 poste=📮 quille=🎳 rame=🚣 rêve=💭 roche=🪨 rock=🎸 rond=⭕ ruche=🐝 sabre=🗡️ salle=🏛️ sole=🐟 stade=🏟️
tache=🫗 tarte=🥧 thym=🌿 tige=🌱 torche=🔦 trace=👣 tresse=👱‍♀️ truite=🐟 tube=🧪 valse=💃 veste=🧥 vigne=🍇
ville=🏙️ zone=🚧 nom=📛 plomb=🎣 don=🎁 son=🔊 long=📏 jambon=🍖 bonnet=🧢 bouton=🔘 carton=📦 mouton=🐑
dent=🦷 dans=🕺 tante=👩 tente=⛺ vent=💨 lent=🐌 banc=🪑 gant=🧤 camp=⛺ champ=🌾 chant=🎶 enfant=🧒 éléphant=🐘
bain=🛁 nain=🧔 sein=🫀 thym=🌿 daim=🦌 lin=🌾 vin=🍷 main=✋ coin=📐 foin=🌾 point=⚫ poing=👊 loin=🔭 groin=🐽
sac=👜 bac=🗑️ lac=🛶 pic=⛏️ tic=⏱️ coq=🐓 roc=🪨 truc=❓ duc=🦉 bec=🐤 sec=🌵 chic=💅 choc=💥 clic=🖱️ flic=👮
mère=👩‍👦 père=👨‍👧 terre=🌍 air=🌬️ hiver=⛄ fer=🧲 cerf=🦌 serre=🌱 verre=🥂 paire=👟 guerre=⚔️ bière=🍺 pierre=🪨
mort=💀 port=⚓ porc=🐖 or=🥇 cor=📯 corps=🧍 bord=⛵ fort=🏰 nord=🧭 sort=🔮 tort=❌ dort=😴 lord=🎩
tour=🗼 four=🔥 cour=🏡 sourd=🦻 lourd=🏋️ jour=🌞 amour=💘 ours=🐻 course=🏃 bourse=💰 douche=🚿 mouche=🪰
cire=🕯️ lyre=🎼 tir=🎯 rire=😆 sire=🤴 mur=🧱 dur=🪨 pur=💎 sur=🔝 lire=📚 dire=🗣️ pire=👎 rire=🤣
sel=🧂 ciel=☁️ miel=🍯 aile=🪽 elle=👩 pelle=🪏 selle=🐴 cel=🧂 belle=💃 bulle=🫧 balle=🎾 salle=🏛️
stop=🛑 sport=🏅 star=⭐ stop=🛑 spirale=🌀 squelette=💀 skate=🛹 ski=🎿 slip=🩲 snack=🍔
""".split()

VOCAB = {}                                     # son -> [(mot, émoji)]
PRESQUE = {}                                   # son avec une consonne en moins -> sons du vocabulaire
for entree in MOTS:
    mot_ecrit, emo = entree.split("=")
    mot_ecrit = mot_ecrit.rstrip("_")
    s = son_de(mot_ecrit)
    if s and (mot_ecrit, emo) not in VOCAB.setdefault(s, []):
        VOCAB[s].append((mot_ecrit, emo))
for s in VOCAB:                                # « tour » peut dessiner « tou… » (une consonne de trop sur l'image)
    for i, c in enumerate(s):
        if c not in "ae2ioyuAOI" and len(s) > 2:
            PRESQUE.setdefault(s[:i] + s[i + 1:], []).append(s)
LONGUEUR_MAX = max(len(s) for s in VOCAB) + 1
