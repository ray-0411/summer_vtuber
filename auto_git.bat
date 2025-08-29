@echo off
cd /d C:\Users\Ray\Desktop\coding\summer_project\vtuber\test\003
git add .
set mydate=%date:~0,10%
set mytime=%time:~0,8%
git commit -m "Auto commit on %mydate% %mytime%" || echo Nothing to commit
git push
pause