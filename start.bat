@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
if not exist "frontend\node_modules\vite" goto missing
start "DiasAvto API" /D "%~dp0backend" cmd /k ..\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
start "DiasAvto Frontend" /D "%~dp0frontend" cmd /k npm run dev
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5173/"
exit /b 0
:missing
echo ERROR: First run setup.bat to install dependencies.
pause
exit /b 1
