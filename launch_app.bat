@echo off
echo Starting MEP Ranking Application...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Launch the application
python launch_app.py

REM Keep the window open if there was an error
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
) 