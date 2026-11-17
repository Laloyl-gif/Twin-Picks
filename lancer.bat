@echo off
rem Twin Picks : le raccourci du bureau lance ce fichier. outils\lanceur.py met le jeu a jour (git), installe ce qui
rem manque, puis lance le jeu : le raccourci ne change jamais, c'est toujours la derniere version qui demarre.
chcp 65001 >nul & cd /d "%~dp0" & title Twin Picks
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% outils\lanceur.py & if errorlevel 1 (pause) & exit /b
