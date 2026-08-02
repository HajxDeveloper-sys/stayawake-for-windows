@echo off
title StayAwake PC Launcher
echo StayAwake PC Starting...

if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    start "" "venv\Scripts\python.exe" main.py
) else (
    start "" "pythonw.exe" main.py
)

if exist "install.bat" del /f /q "install.bat"
(goto) 2>nul & del "%~f0"
