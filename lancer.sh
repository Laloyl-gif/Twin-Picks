#!/bin/sh
# Twin Picks (macOS / Linux) : outils/lanceur.py met le jeu à jour (git), installe ce qui manque, puis le lance.
cd "$(dirname "$0")" && exec python3 outils/lanceur.py
