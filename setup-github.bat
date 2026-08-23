@echo off
REM Derniere etape de la veille 24/7 : deposer les secrets sur le repo GitHub.
REM Le code et le workflow sont deja en ligne, il ne manque que ca.
cd /d "%~dp0"

echo.
echo == Ta cle Resend, a copier dans l'invite juste apres ==
findstr /b "RESEND_API_KEY" "..\..\site\.env.vercel.local"
echo.

gh secret set RESEND_API_KEY --repo Speerla/codeur-watch
if errorlevel 1 goto :fin
gh secret set AUDIT_FROM --repo Speerla/codeur-watch --body "Robin Bouvet - Speerla <audit@speerlastudio.com>"
gh secret set WATCH_TO --repo Speerla/codeur-watch --body "audit@speerlastudio.com"

echo.
echo == Verification ==
gh secret list --repo Speerla/codeur-watch
echo.
echo == Passe de controle (tu dois recevoir un mail s'il y a du frais) ==
gh workflow run "Veille Codeur" --repo Speerla/codeur-watch -f min_score=8 -f max_age=48
echo.
echo Termine. Suivi des passes : gh run list --repo Speerla/codeur-watch

:fin
pause
