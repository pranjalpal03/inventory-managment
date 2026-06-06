@echo off
REM Push project to GitHub (run from this file's folder)
cd /d "%~dp0"

ngit --version >nul 2>&1 || goto NoGit
if not exist .git (
  git init
)
git add -A
git commit -m "docs: add README and .gitignore, prepare repo for deployment" || echo No changes to commit
git branch -M main
git remote remove origin 2>nul || echo No remote to remove
git remote add origin https://github.com/pranjalpal03/inventory-managment.git
echo Pushing to GitHub...
git push -u origin main
pause
exit /b 0

:NoGit
echo Git not found in PATH. Please install Git and re-run.
pause
exit /b 1
