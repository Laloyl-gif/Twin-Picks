@echo off
rem Met le jeu sur GitHub la premiere fois (depot vide cree sur github.com, par exemple « twin-picks »).
rem Usage : glissez ce fichier... ou lancez-le, puis collez l'adresse du depot (https://github.com/COMPTE/twin-picks).
chcp 65001 >nul
cd /d "%~dp0.."
set /p URL=Adresse du depot GitHub : 
git init -b main
git add -A
git commit -m "Twin Picks"
git remote remove origin 2>nul
git remote add origin %URL%
git push -u origin main
echo.
echo Fait. Lancez maintenant installer.bat pour creer le raccourci du bureau.
pause
