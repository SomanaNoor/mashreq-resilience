@echo off
TITLE Mashreq Responsible AI System

echo ===================================================
echo     MASHREQ RESPONSIBLE AI - DEPLOYMENT LAUNCH
echo ===================================================
echo.

:: 1. Clean up old processes
taskkill /F /IM python.exe >nul 2>&1

cd src

echo [1/2] Starting API Backend (Port 8000)...
start "Mashreq API Backend" cmd /k "python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Dashboard Interface...
echo.
echo Dashboard Config: Port 8502 | Localhost | No Stats
echo.
echo Please wait while the dashboard loads...
echo IF BROWSER DOES NOT OPEN, GO TO: http://127.0.0.1:8502
echo.

:: Run streamlit (Config is in .streamlit/config.toml)
python -m streamlit run dashboard.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Dashboard failed to start.
    pause
)

pause
