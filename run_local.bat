@echo off
title BhuSynch AI - Local Free Runner
echo ========================================================
echo    BhuSynch AI - 3D Web-GIS & Cadastral Intelligence
echo ========================================================
echo.
echo Starting BhuSynch AI local services...
echo.

:: Check python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

:: Start Backend in background
echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "BhuSynch API" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Start Frontend web server
echo [2/2] Starting Web Server on http://localhost:3000 ...
start "BhuSynch Web" cmd /k "cd /d %~dp0 && python -m http.server 3000"

:: Wait 2 seconds and open browser
timeout /t 2 /nobreak >nul
echo.
echo Launching your browser to http://localhost:3000/frontend/index.html ...
start http://localhost:3000/frontend/index.html

echo.
echo ========================================================
echo   BhuSynch AI is running!
echo   - 3D Web-GIS Console: http://localhost:3000/frontend/index.html
echo   - Adjudication Portal: http://localhost:3000/frontend/adjudication.html
echo   - Interactive API Docs: http://localhost:8000/docs
echo ========================================================
echo.
pause
