@echo off
setlocal enabledelayedexpansion
title EchoScape - $0-Budget Spatial Radar

echo.
echo  ============================================================
echo    ECHOSCAPE - the $0-budget spatial radar
echo  ============================================================
echo.

rem ---- 1. check Python ----
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found on PATH. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

rem ---- 2. check Node ----
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js not found on PATH. Install Node 18+ from https://nodejs.org
    pause
    exit /b 1
)

rem ---- 3. backend virtualenv + deps ----
if not exist "backend\.venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv backend\.venv || goto :fail
)
echo [1/3] Installing backend dependencies (first run only)...
call backend\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt || goto :fail

rem ---- 4. frontend deps ----
if not exist "frontend\node_modules" (
    echo [2/3] Installing frontend dependencies (first run only)...
    pushd frontend
    call npm install --no-audit --no-fund || (popd & goto :fail)
    popd
) else (
    echo [2/3] Frontend dependencies found.
)

echo [3/3] Starting EchoScape...
echo    - backend  : http://127.0.0.1:5001
echo    - frontend : http://localhost:5173
echo    - press Ctrl+C in the backend window to stop
echo.

start "EchoScape Backend" cmd /k "cd backend && .venv\Scripts\python.exe app.py"
cd frontend
call npm run dev
goto :done

:fail
echo.
echo [ERROR] Setup failed. See messages above.
pause
exit /b 1

:done
endlocal
