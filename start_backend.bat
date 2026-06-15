@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
echo === 3DGS 后端 (FastAPI :8000) ===
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --app-dir .
pause
