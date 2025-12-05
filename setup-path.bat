@echo off

echo ========================================
echo        Lazzy Commit - Setup Script
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)
python --version
echo.

echo [2/4] Setting up environment configuration...
if not exist "%SCRIPT_DIR%\.env" (
    if exist "%SCRIPT_DIR%\.env.example" (
        copy "%SCRIPT_DIR%\.env.example" "%SCRIPT_DIR%\.env" >nul
        echo .env file created from .env.example
        echo Please edit .env and add your GEMINI_API_KEY
    ) else (
        echo WARNING: .env.example not found!
    )
) else (
    echo .env file already exists.
)
echo.

echo [3/4] Setting up virtual environment...
if not exist "%SCRIPT_DIR%\venv" (
    python -m venv "%SCRIPT_DIR%\venv"
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

echo [4/4] Installing dependencies...
call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "%SCRIPT_DIR%\requirements.txt" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

:finish
echo.
echo ========================================
echo            SETUP COMPLETE!
echo ========================================
echo.
echo IMPORTANT: Edit .env and add your GEMINI_API_KEY
echo Then run: lazzycommit
echo.
pause