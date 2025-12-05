@echo off

set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%main.py" %*
) else (
    echo "%SCRIPT_DIR%\main.py"
    python "%SCRIPT_DIR%\main.py" %*
)
