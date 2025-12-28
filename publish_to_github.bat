@echo off
set /p remote_url="Enter your GitHub Repository URL (e.g., https://github.com/Username/exoplanethunter.git): "
git remote add origin %remote_url%
git branch -M main
git push -u origin main
pause
