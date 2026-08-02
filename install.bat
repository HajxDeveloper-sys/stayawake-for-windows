@echo off
title StayAwake PC - Install Script
echo ===================================================
echo   StayAwake PC - Dependency Installer
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.12 or later.
    pause
    exit /b 1
)

echo Python detected. Installing required libraries...
if exist "venv\Scripts\python.exe" (
    echo The existing virtual environment is being used...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo Creating a new virtual environment venv...
    python -m venv venv
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo [SUCCESS] All dependencies installed successfully!
    echo Launching run.bat automatically...
    echo ===================================================
    start "" run.bat
    exit /b 0
) else (
    echo.
    echo [ERROR] An error occurred during library installation.
    pause
    exit /b 1
)
