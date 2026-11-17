@echo off
rem A lancer UNE fois sur chaque ordinateur, depuis le dossier du jeu (un clone git du depot).
rem Cree le raccourci « Twin Picks » sur le bureau : il lance lancer.bat, qui met toujours le jeu a jour avant de jouer.
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul || (
  echo Git n'est pas installe. Installation...
  winget install --id Git.Git -e --source winget || (echo Installez Git : https://git-scm.com/download/win & pause & exit /b 1)
)
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% --version >nul 2>nul || (
  echo Python n'est pas installe. Installation...
  winget install --id Python.Python.3.12 -e --source winget || (echo Installez Python : https://www.python.org/downloads/ & pause & exit /b 1)
)
if not exist ".git" (
  echo Ce dossier n'est pas un clone git du depot : lisez INSTALLATION.md ^(outils\premiere_publication.bat^).
  pause
  exit /b 1
)
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt
if not exist donnees mkdir donnees
copy /y requirements.txt donnees\requirements.installe >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Twin Picks.lnk');" ^
  "$s.TargetPath='%~dp0lancer.bat';$s.WorkingDirectory='%~dp0';$s.IconLocation='%~dp0web\icone.ico';$s.WindowStyle=7;" ^
  "$s.Description='Twin Picks (toujours la derniere version)';$s.Save()"
echo.
echo Le raccourci « Twin Picks » est sur le bureau. Il met le jeu a jour a chaque lancement.
pause
