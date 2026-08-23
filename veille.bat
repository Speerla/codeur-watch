@echo off
REM Veille Codeur en local : scanne toutes les 2 minutes et envoie un mail sur les projets chauds.
REM La cle Resend est lue automatiquement depuis site\.env.vercel.local si elle n'est pas dans l'environnement.
cd /d "%~dp0"
python watch.py --loop 120 --max-age 3 --min-score 8 --notify
pause
