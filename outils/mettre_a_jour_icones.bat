@echo off
rem Remet tout de suite la derniere icone de Twin Picks sur le raccourci du bureau (sinon : fait tout seul au prochain lancement).
chcp 65001 >nul
cd /d "%~dp0.."
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% outils\lanceur.py --icones
echo Icone mise a jour.
pause
