@echo off
TITLE KRATOS - Vision AI Model Training Workflow
COLOR 0A
SETLOCAL EnableDelayedExpansion

echo ===============================================================================
echo            KRATOS VISION AI - MODEL TRAINING ^& DATASET PIPELINE
echo ===============================================================================
echo.

SET SERVICE_DIR=%~dp0
CD /D "%SERVICE_DIR%"

REM -------------------------------------------------------------------------------
REM STEP 1: Environment and Virtual Environment Setup
REM -------------------------------------------------------------------------------
echo [1/4] Checking Python Virtual Environment...

IF NOT EXIST ".venv" (
    echo [*] Virtual environment (.venv) not found. Creating new .venv...
    py -3.12 -m venv .venv
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create Python virtual environment. Ensure Python 3.11/3.12 is installed and on PATH.
        PAUSE
        EXIT /B 1
    )
)
echo [OK] Virtual environment ready.
echo.

REM -------------------------------------------------------------------------------
REM STEP 2: Verify and Install Dependencies
REM -------------------------------------------------------------------------------
echo [2/4] Verifying and installing required PyTorch ^& Vision packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

IF !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Package installation failed. Check internet connection or requirements.txt.
    PAUSE
    EXIT /B 1
)
echo [OK] All dependencies installed and verified.
echo.

REM -------------------------------------------------------------------------------
REM STEP 3: Dataset Download and Resolution
REM -------------------------------------------------------------------------------
echo [3/4] Fetching ^& resolving DeepGlobe Satellite Road Extraction dataset...
echo [*] Checking local cache / kagglehub dataset...
.venv\Scripts\python.exe -m app.download

IF !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Automatic dataset download via kagglehub returned a non-zero exit code.
    echo [*] Checking if dataset files exist under data\train...
    IF NOT EXIST "data\train" (
        echo [ERROR] Could not locate satellite imagery under data\train.
        echo [*] Please place dataset imagery (*_sat.jpg / *_mask.png pairs) inside:
        echo     "%SERVICE_DIR%data\train\"
        PAUSE
        EXIT /B 1
    )
)
echo [OK] Dataset resolved successfully.
echo.

REM -------------------------------------------------------------------------------
REM STEP 4: Train SegFormer / U-Net Occlusion-Robust Road Extraction Model
REM -------------------------------------------------------------------------------
echo [4/4] Starting Vision Model Training (app.model)...
echo [*] Target Checkpoint: %SERVICE_DIR%weights\roadnet.pt
echo.

.venv\Scripts\python.exe -m app.model

IF !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Model training loop encountered an exception.
    echo [*] Diagnostics: Verify PyTorch/CUDA availability, GPU memory, or image dimensions in data\train.
    PAUSE
    EXIT /B 1
)

echo.
echo ===============================================================================
echo  SUCCESS: VISION MODEL TRAINING COMPLETED AND WEIGHTS SAVED:
echo  Checkpoint: %SERVICE_DIR%weights\roadnet.pt
echo ===============================================================================
echo.
PAUSE
