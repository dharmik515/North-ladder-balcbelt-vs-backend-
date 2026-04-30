@echo off
REM NorthLadder Blackbelt Mismatch Detection System - Startup Script
REM This script starts the FastAPI web application

echo.
echo ============================================================
echo NorthLadder Mismatch Detection System
echo Version 1.0 - Production Ready
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [*] Starting FastAPI server...
echo.
echo Visit the application at: http://localhost:8000
echo.

REM Start the server
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause
