"""Mots -> émojis, pour le rébus de Jerry. Clés : mots sans accent, en minuscules (français et anglais)."""
DICO = """
roi king=👑 reine queen=👸 prince princesse princess=🤴 lion=🦁 tigre tiger=🐯 ours bear=🐻 loup wolf loups=🐺
chat cat chats=🐈 chien dog chiens dogs=🐕 cheval horse chevaux=🐎 oiseau bird oiseaux birds=🐦 aigle eagle=🦅
corbeau crow=🐦‍⬛ hibou owl chouette=🦉 serpent snake=🐍 dragon=🐉 requin shark=🦈 poisson fish=🐟 baleine whale=🐋
dauphin dolphin=🐬 singe monkey=🐒 gorille gorilla kong=🦍 elephant=🐘 souris mouse=🐭 rat=🐀 lapin rabbit=🐇
araignee spider=🕷️ abeille bee=🐝 papillon butterfly=🦋 dinosaure dinosaur jurassic=🦖 vache cow=🐄 cochon pig=🐖
mouton agneaux agneau lamb sheep=🐑 canard duck=🦆 poule chicken=🐔 renard fox=🦊 zebre=🦓 pingouin manchot penguin=🐧
homme man hommes men=👨 femme woman femmes women=👩 enfant child enfants children=🧒 fille girl filles=👧
garcon boy=👦 bebe baby=👶 pere father=👨‍👧 mere mother=👩‍👦 famille family=👪 frere brother freres=👬 soeur sister=👭
ami friend amis friends=🤝 amour love=❤️ coeur heart=❤️ baiser kiss=💋 mariage wedding mariee bride=💍
mort death mortel deadly=💀 fantome ghost=👻 diable devil=😈 ange angel anges=👼 dieu god=🙏 sorciere witch=🧙‍♀️
magicien wizard sorcier=🧙 vampire=🧛 zombie zombies=🧟 monstre monster=👹 robot=🤖 alien extraterrestre=👽
pirate pirates=🏴‍☠️ cowboy=🤠 policier police flic=👮 detective=🕵️ espion spy=🕵️ docteur doctor=🧑‍⚕️ soldat soldier=💂
feu fire=🔥 eau water=💧 glace ice=🧊 neige snow=❄️ pluie rain=🌧️ orage tempete storm=⛈️ vent wind=🌬️ soleil sun=☀️
lune moon=🌙 etoile star etoiles stars=⭐ ciel sky=🌌 nuit night nuits=🌃 jour day jours=🌞 matin morning=🌅
soir evening=🌆 terre earth=🌍 monde world=🌍 planete planet=🪐 espace space=🚀 mer sea ocean=🌊 ile island=🏝️
montagne mountain=⛰️ foret forest bois=🌲 arbre tree=🌳 fleur flower fleurs=🌸 rose roses=🌹 desert=🏜️ riviere river=🏞️
volcan volcano=🌋 ville city=🏙️ maison house home=🏠 chateau castle=🏰 eglise church=⛪ ecole school=🏫 hopital hospital=🏥
prison=🔒 porte door=🚪 fenetre window=🪟 cle key=🔑 pont bridge=🌉 route road=🛣️ rue street=🛣️ hotel=🏨 tour tower=🗼
voiture car cars=🚗 taxi=🚕 bus=🚌 train=🚆 avion plane=✈️ bateau boat navire ship=🚢 velo bike=🚲 moto=🏍️ fusee rocket=🚀
argent money=💰 or gold=🥇 diamant diamond diamants=💎 tresor treasure=💰 couronne crown=👑 epee sword=⚔️ guerre war=⚔️
arme gun pistolet=🔫 bombe bomb=💣 bouclier shield=🛡️ fleche arrow=🏹 hache axe=🪓 couteau knife=🔪
temps time=⏳ horloge clock=🕰️ heure hour=🕐 livre book=📖 lettre letter=✉️ film movie cinema=🎬 musique music=🎵
chanson song=🎶 danse dance=💃 fete party=🎉 jeu game jeux games=🎮 cartes=🃏 photo=📷 telephone phone=📞
television tv=📺 radio=📻 ordinateur computer=💻 lumiere light=💡 ombre shadow=👤 noir black=⬛ blanc white=⬜
rouge red=🟥 bleu blue=🟦 vert green=🟩 jaune yellow=🟨 orange=🟧 violet purple=🟪 rose_couleur pink=🩷
tete head=🗣️ yeux eyes oeil eye=👁️ main hand mains=✋ pied foot=🦶 dents teeth dent=🦷 sang blood=🩸 cerveau brain=🧠
nez nose=👃 oreille ear=👂 bouche mouth=👄 visage face=🙂 cri scream=😱 rire laugh=😂 larmes tears=😢 sourire smile=😊
reve dream reves dreams=💭 sommeil sleep=😴 vie life=🌱 nouveau new=🆕 grand big=🔝 petit little small=🤏
fin end=🔚 premier first=🥇 dernier last=🔚 retour return=🔙 un one=1️⃣ deux two=2️⃣ trois three=3️⃣ quatre four=4️⃣
cinq five=5️⃣ six=6️⃣ sept seven=7️⃣ huit eight=8️⃣ neuf nine=9️⃣ dix ten=🔟 cent hundred=💯 mille thousand=1️⃣0️⃣0️⃣0️⃣
pomme apple=🍎 cerise cherry=🍒 orange_fruit=🍊 banane banana=🍌 fraise strawberry=🍓 pain bread=🍞 gateau cake=🍰
tarte pie=🥧 cafe coffee=☕ the tea=🍵 vin wine=🍷 biere beer=🍺 lait milk=🥛 chocolat chocolate=🍫 pizza=🍕
fromage cheese=🧀 oeuf egg=🥚 bonbon candy=🍬 glace_dessert=🍨 sucre sugar=🍬 poivre pepper=🌶️
noel christmas=🎄 halloween=🎃 cadeau gift=🎁 ballon ball=⚽ football=🏈 boxe boxing=🥊 course race=🏁 victoire=🏆
roche rock pierre stone=🪨 papier paper=📄 ciseaux scissors=✂️ verre glass=🥃 miroir mirror=🪞 masque mask=🎭
chapeau hat=🎩 robe dress=👗 chaussures shoes=👞 parapluie umbrella=☂️ sac bag=👜 anneau ring bague=💍
rideau curtain=🎭 secret secrets=🤫 mystere mystery=❓ question=❓ histoire story=📖 legende legend=📜 roman=📕
club=♣️ coeurs=♥️ pique=♠️ carreau=♦️ jungle=🌴 plage beach=🏖️ ete summer=☀️ hiver winter=❄️ printemps spring=🌷
automne autumn fall=🍂 vacances=🏖️ voyage travel=🧳 nord north=⬆️ sud south=⬇️ est east=➡️ ouest west=⬅️
blanche=⬜ noire=⬛ verte=🟩 petite=🤏 grande=🔝 belle beau beauty beautiful=😍 futur future=🔮 parrain godfather=🤵
seigneur lord=🤴 evade evades escape evasion=🏃 nain nains dwarf dwarfs=🧔 bete beast=👹 geant giant=🗿 voleur thief=🦹
tueur killer=🔪 heros hero=🦸 dernier_mot=🔚 noel_=🎄 shining=✨ alien_=👽 matrix=💊 titanic=🚢 jaws=🦈 psycho=🔪
lumieres lights=💡 marteau hammer=🔨 cle_=🔑 fusil rifle=🔫 balle bullet=🔫 sabre saber=⚔️ hache_=🪓
froid cold=🥶 chaud hot=🥵 fou crazy mad=🤪 seul alone=🧍 tous all=👥 rien nothing=🚫 non no=🚫 oui yes=✅
"""
EMOJI = {}
for ligne in DICO.strip().splitlines():
    morceaux = ligne.replace("=", " = ").split()
    mots = []
    for m in morceaux:
        if m == "=":
            continue
        if any(ord(c) > 0x2000 for c in m):           # c'est l'émoji : il s'applique aux mots qui précèdent
            for x in mots:
                EMOJI.setdefault(x.split("_")[0] if "_" in x and x.split("_")[0] not in ("rose", "orange", "glace") else x, m)
            mots = []
        else:
            mots.append(m)
