@echo off
chcp 65001 >nul
cd /d "%~dp0frontend"
echo === 3DGS 前端 (Vite :5173) ===
call npm run dev
pause
