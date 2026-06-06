@echo off
REM Launcher for Lazzy Commit. Prefers the bundled venv so the tool runs with its
REM own pinned dependencies regardless of which git repo it's invoked from.
REM All arguments (commit flags, the `config` subcommand, etc.) pass straight through.

set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    "%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%main.py" %*
) else (
    python "%SCRIPT_DIR%main.py" %*
)
