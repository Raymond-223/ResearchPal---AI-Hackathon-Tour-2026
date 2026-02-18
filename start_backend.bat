@echo off 
title ResearchPal Backend 
call .venv_win\Scripts\activate.bat 
set PYTHONPATH=C:\Users\24045\Documents\trae_projects\ResearchPal---AI-Hackathon-Tour-2026-main 
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload 
if %errorlevel% neq 0 pause 
