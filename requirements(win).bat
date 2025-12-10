@echo off
title requirements(win)
color 6
python -m pip install --upgrade pip
pip install --upgrade Flask
pip install --upgrade waitress
pip install --upgrade gunicorn
pip install --upgrade daemon
pip install --upgrade yt-dlp
python --version
echo Proceso terminado. 
pause 
