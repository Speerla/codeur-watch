@echo off
REM Met en place la veille 24/7 sur GitHub Actions.
REM A lancer une seule fois. Un navigateur va s'ouvrir pour l'etape 1.
cd /d "%~dp0"

echo.
echo == 1. Autoriser gh a pousser des workflows ==
echo    Un code va s'afficher, tu l'entres dans le navigateur qui s'ouvre.
echo.
gh auth refresh -h github.com -s workflow
if errorlevel 1 goto :fin

echo.
echo == 2. Pousser le workflow ==
git add .github
git commit -m "Ajoute la veille planifiee toutes les 5 minutes"
git push origin main
if errorlevel 1 goto :fin

echo.
echo == 3. Deposer les secrets sur le repo ==
echo    Ta cle Resend, a copier dans l'invite juste apres :
findstr /b "RESEND_API_KEY" "..\..\site\.env.vercel.local"
echo.
gh secret set RESEND_API_KEY --repo Speerla/codeur-watch
gh secret set AUDIT_FROM --repo Speerla/codeur-watch --body "Robin Bouvet - Speerla <audit@speerlastudio.com>"
gh secret set WATCH_TO --repo Speerla/codeur-watch --body "audit@speerlastudio.com"

echo.
echo == 4. Verification ==
gh secret list --repo Speerla/codeur-watch
gh workflow list --repo Speerla/codeur-watch
echo.
echo Termine. La veille tourne toutes les 5 minutes sur GitHub.

:fin
pause
