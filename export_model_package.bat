@echo off
TITLE KRATOS - Export Model Weights ^& Vector.db Package
COLOR 0B
SETLOCAL EnableDelayedExpansion

CD /D "%~dp0"
IF EXIST "agentverse-platform\backend\.venv\Scripts\python.exe" (
    "agentverse-platform\backend\.venv\Scripts\python.exe" scripts\export_portable_package.py
) ELSE (
    python scripts\export_portable_package.py
)

PAUSE
