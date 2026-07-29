@echo off
TITLE KRATOS - Vector DB Generator & DeepGlobe Feature Indexer
COLOR 0B
SETLOCAL EnableDelayedExpansion

echo ===============================================================================
echo            KRATOS VECTOR DATABASE GENERATOR & FEATURE INDEXER
echo ===============================================================================
echo.

SET ROOT_DIR=%~dp0
CD /D "%ROOT_DIR%"

IF EXIST "vision-service\.venv\Scripts\python.exe" (
    SET PYTHON_EXE="%ROOT_DIR%vision-service\.venv\Scripts\python.exe"
) ELSE (
    SET PYTHON_EXE=python
)

echo [*] Using Python Executable: %PYTHON_EXE%
echo [*] Processing satellite imagery and road masks from dataset_unprocessed\train...
echo.

%PYTHON_EXE% scripts\build_vector_db.py

IF !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Vector DB indexing failed! Ensure dataset files exist in dataset_unprocessed\train.
    PAUSE
    EXIT /B 1
)

echo.
echo ===============================================================================
echo  SUCCESS! VECTOR DB INDEXING COMPLETED (vector.db)
echo ===============================================================================
echo.
PAUSE
