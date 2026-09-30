@echo off
title AI-Based Fake Identity & Document Screening System
cd /d "%~dp0"

echo ====================================================================
echo AI-Based Fake Identity & Document Screening System
echo B.Tech Computer Science (Cybersecurity) Project Prototype
echo ====================================================================
echo.
echo [1/2] Checking environment...
python --version
echo.
echo [2/2] Launching Forensic Web Server on http://127.0.0.1:5000 ...
echo.
echo Opening browser in 2 seconds...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000

python app.py

pause
