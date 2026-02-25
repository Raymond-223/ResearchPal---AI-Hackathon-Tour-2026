@echo off
setlocal
title ResearchPal Launcher

echo ===================================================
echo        ResearchPal - AI Academic Assistant
echo ===================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH.
    echo Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
echo [2/5] Checking Virtual Environment...
if not exist ".venv_win" (
    echo Creating virtual environment in .venv_win...
    python -m venv .venv_win
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        echo Please check permissions or try running as Administrator.
        pause
        exit /b 1
    )
)

:: 3. Activate Environment and Install Dependencies
echo [3/5] Installing Dependencies (this may take a while)...
call .venv_win\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Start Backend (in same terminal, background)
echo.
echo [4/5] Starting Backend Server...
set PYTHONPATH=%cd%
set BACKEND_URL=http://127.0.0.1:8000

:: Run backend in background within same terminal
start "" /b python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

:: 5. Start Frontend
echo.
echo [5/5] Waiting for backend and starting Frontend...
echo Checking backend health...

:: Polling wait - check backend health instead of fixed wait
:wait_for_backend
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo   Backend not ready, retrying in 2 seconds...
    timeout /t 2 /nobreak >nul
    goto wait_for_backend
)
echo   Backend is ready!

echo Starting Frontend...
python frontend/gradio_app.py

if %errorlevel% neq 0 (
    echo Error: Frontend crashed.
    pause
)

pause
