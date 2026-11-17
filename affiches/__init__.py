"""Affiches vidées (jeu de Pete) : affiches de films sans titre, textes, personnages ni sujet principal, préparées en local.

    reglages.py        réglages techniques (affiches/config.json)
    catalogue.py       correspondance film -> originale / vidée / masque, reprise, jamais d'écrasement
    detection.py       masques des textes et des personnages
    reconstruction.py  reconstruction des zones effacées (LaMa)
    pipeline.py        traitement d'une affiche
    preparation.py     préparation en arrière-plan de N affiches pour les listes choisies
    __main__.py        en ligne de commande : python -m affiches --aide
"""
