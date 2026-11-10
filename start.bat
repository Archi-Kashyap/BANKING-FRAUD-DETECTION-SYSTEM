@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py %*
    exit /b %ERRORLEVEL%
)

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" run.py %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run.py %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 run.py %*
    exit /b %ERRORLEVEL%
)

echo [Error] Python 3 was not found in your PATH or virtual environment.
echo Please install Python 3 or add it to your system PATH.
exit /b 1
