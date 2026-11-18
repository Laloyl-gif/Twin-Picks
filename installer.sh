#!/bin/sh
# À lancer UNE fois (macOS / Linux), depuis le dossier du jeu (un clone git du dépôt) : crée le raccourci du bureau.
cd "$(dirname "$0")" || exit 1
ICI="$(pwd)"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)                      # Windows (Git Bash) : c'est installer.bat qu'il faut
    echo "Sous Windows, lancez installer.bat (double-clic dans l'Explorateur)."
    cmd.exe //c installer.bat
    exit $? ;;
esac
chmod +x lancer.sh
python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt
mkdir -p donnees && cp requirements.txt donnees/requirements.installe
BUREAU="$HOME/Desktop"; [ -d "$HOME/Bureau" ] && BUREAU="$HOME/Bureau"
if [ "$(uname)" = "Darwin" ]; then
  printf '#!/bin/sh\nexec "%s/lancer.sh"\n' "$ICI" > "$BUREAU/Twin Picks.command"
  chmod +x "$BUREAU/Twin Picks.command"
else
  cat > "$BUREAU/twin-picks.desktop" <<EOD
[Desktop Entry]
Type=Application
Name=Twin Picks
Exec="$ICI/lancer.sh"
Icon=$ICI/web/icone.png
Terminal=true
EOD
  chmod +x "$BUREAU/twin-picks.desktop"
fi
echo "Raccourci « Twin Picks » créé sur le bureau : il met le jeu à jour à chaque lancement."
