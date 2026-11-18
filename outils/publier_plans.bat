@echo off
rem Met les plans de Truman's Files en ligne : glissez le .zip des plans rangés (plans_twin_picks.zip) sur ce fichier.
rem Ils vont sur la branche « plans » du dépôt GitHub : tous les ordinateurs et téléphones les trouvent tout seuls.
chcp 65001 >nul
cd /d "%~dp0.."
if "%~1"=="" (echo Glissez le fichier .zip des plans sur publier_plans.bat & pause & exit /b 1)
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% outils\publier_plans.py "%~1"
pause
