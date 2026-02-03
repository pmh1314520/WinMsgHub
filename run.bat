@echo off
chcp 65001 >nul
REM WinMsgHub Startup Script
REM Author: Qingyun Production - Peng Minghang

echo ========================================
echo WinMsgHub
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found, please install Python 3.9+
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting WinMsgHub...
echo.

REM Run the application
python main.py

pause
