@echo off
rem Met le jeu sur GitHub la premiere fois (depot cree sur github.com, par exemple « twin-picks »).
rem Lancez-le, puis collez l'adresse du depot (https://github.com/COMPTE/twin-picks).
chcp 65001 >nul
cd /d "%~dp0.."
set /p URL=Adresse du depot GitHub : 
if not exist ".git" git init -b main
git add -A
git commit -m "Twin Picks"
git remote remove origin 2>nul
git remote add origin %URL%
rem --force : si le depot a ete cree avec un README (ou une licence), on le remplace par le jeu
git push -u origin main --force || (echo. & echo ECHEC de l'envoi sur GitHub : verifiez l'adresse et la connexion. & pause & exit /b 1)
echo.
echo Fait. Lancez maintenant installer.bat (dans le dossier du jeu, a cote de main.py) pour creer le raccourci du bureau.
pause
