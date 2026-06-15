@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   3DGS 三维重建系统 - 一键启动
echo   后端 :8000  +  前端 :5173
echo ================================================
start "3DGS Backend" "%~dp0start_backend.bat"
start "3DGS Frontend" "%~dp0start_frontend.bat"
echo 正在等待服务启动，稍后自动打开浏览器...
timeout /t 6 >nul
start "" "http://localhost:5173"
echo 已打开 http://localhost:5173
echo (关闭本窗口不影响服务；要停止请关掉弹出的两个黑窗口)
timeout /t 3 >nul
