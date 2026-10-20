@echo off
setlocal
cd /d "%~dp0"
echo === DiasAvto: installing dependencies ===
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m venv .venv
) else (
  where python >nul 2>nul
  if errorlevel 1 goto missing_python
  python -m venv .venv
)
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -e "./backend[dev]"
if errorlevel 1 goto failed
where npm >nul 2>nul
if errorlevel 1 goto missing_node
cd /d "%~dp0frontend"
call npm install --no-audit --no-fund
if errorlevel 1 goto failed
call npm run build
if errorlevel 1 goto failed
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pytest backend/tests -q
if errorlevel 1 goto failed
echo.
echo SUCCESS. Now run start.bat
pause
exit /b 0
:missing_python
echo ERROR: Install Python 3.11+ from python.org and run setup.bat again.
pause
exit /b 1
:missing_node
echo ERROR: Install Node.js 22+ from nodejs.org and run setup.bat again.
pause
exit /b 1
:failed
echo ERROR: Setup or tests failed. See the error above.
pause
exit /b 1
