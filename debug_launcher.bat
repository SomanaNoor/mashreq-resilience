@echo off
TITLE Mashreq Debug Launcher

echo ===================================================
echo     MASHREQ RESPONSIBLE AI - DIAGNOSTIC MODE
echo ===================================================
echo.

:: Kill python to free ports
taskkill /F /IM python.exe >nul 2>&1

cd src

echo Starting API...
start "Mashreq API" cmd /k "python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Dashboard with logging...
echo.
echo Launching Streamlit on localhost:8501...
echo Errors will be written to error_log.txt
echo.

python -m streamlit run dashboard.py --server.port 8501 --server.address 127.0.0.1 > error_log.txt 2>&1

echo.
echo Dashboard crashed or stopped.
echo Displaying last 20 lines of error log:
echo ---------------------------------------------------
powershell -command "Get-Content error_log.txt -Tail 20"
echo ---------------------------------------------------
pause
