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

:: 4. Start Backend
echo.
echo [4/5] Starting Backend Server...
set PYTHONPATH=%cd%
set BACKEND_URL=http://127.0.0.1:8000

:: Create a temporary backend starter script to avoid quoting issues
echo @echo off > start_backend.bat
echo title ResearchPal Backend >> start_backend.bat
echo call .venv_win\Scripts\activate.bat >> start_backend.bat
echo set PYTHONPATH=%cd% >> start_backend.bat
echo python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload >> start_backend.bat
echo if %%errorlevel%% neq 0 pause >> start_backend.bat

start "ResearchPal Backend" start_backend.bat

:: 5. Start Frontend
echo.
echo [5/5] Waiting for backend and starting Frontend...
echo Waiting 10 seconds...
timeout /t 10 /nobreak >nul

echo Starting Frontend...
python frontend/gradio_app.py

if %errorlevel% neq 0 (
    echo Error: Frontend crashed.
    pause
)

pause
