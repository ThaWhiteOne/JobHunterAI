@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 desktop_app.py
) else (
    python desktop_app.py
)

if errorlevel 1 (
    echo.
    echo JobHunterAI could not start. Check that Python is installed and available on PATH.
    pause
)

endlocal
