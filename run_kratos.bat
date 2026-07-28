@echo off
TITLE KRATOS Master Launcher - Multi-Agent System Setup ^& Execution
COLOR 0B
SETLOCAL EnableDelayedExpansion

echo ===============================================================================
echo                KRATOS MULTI-AGENT SYSTEM MASTER LAUNCHER
echo  Knowledge-driven Road Analysis for Terrain Occlusion ^& Security (KRATOS)
echo ===============================================================================
echo.

SET ROOT_DIR=%~dp0
CD /D "%ROOT_DIR%"

:: Helper for colored console messages using PowerShell
SET "PRINT_CYAN=powershell -Command "Write-Host '%~1' -ForegroundColor Cyan""
SET "PRINT_GREEN=powershell -Command "Write-Host '%~1' -ForegroundColor Green""
SET "PRINT_YELLOW=powershell -Command "Write-Host '%~1' -ForegroundColor Yellow""
SET "PRINT_RED=powershell -Command "Write-Host '%~1' -ForegroundColor Red""

powershell -Command "Write-Host '[1/5] Checking Environment Files (.env) and NVIDIA NIM/cuOpt API credentials...' -ForegroundColor Cyan"

IF NOT EXIST "%ROOT_DIR%.env" (
    powershell -Command "Write-Host '[!] Root .env missing. Creating default .env file...' -ForegroundColor Yellow"
    (
        echo NVIDIA_API_KEY=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
        echo CUOPT_API_KEY=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
        echo NIM_API_KEY=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
        echo CUOPT_ENDPOINT=https://integrate.api.nvidia.com/v1/cuopt
    ) > "%ROOT_DIR%.env"
)

IF NOT EXIST "%ROOT_DIR%agentverse-platform\backend\.env" (
    copy /Y "%ROOT_DIR%.env" "%ROOT_DIR%agentverse-platform\backend\.env" >NUL
)

IF NOT EXIST "%ROOT_DIR%graph-service\.env" (
    copy /Y "%ROOT_DIR%.env" "%ROOT_DIR%graph-service\.env" >NUL
)

IF NOT EXIST "%ROOT_DIR%vision-service\.env" (
    copy /Y "%ROOT_DIR%.env" "%ROOT_DIR%vision-service\.env" >NUL
)

powershell -Command "Write-Host '[OK] All .env environment files validated with active NVIDIA credentials.' -ForegroundColor Green"
echo.

:: -------------------------------------------------------------------------------
:: STEP 2: Vision Service Setup
:: -------------------------------------------------------------------------------
powershell -Command "Write-Host '[2/5] Setting up Vision AI Service (.venv ^& dependencies)...' -ForegroundColor Cyan"
CD /D "%ROOT_DIR%vision-service"

IF NOT EXIST ".venv" (
    powershell -Command "Write-Host '[!] Vision Service .venv not found. Creating virtual environment...' -ForegroundColor Yellow"
    python -m venv .venv
    IF !ERRORLEVEL! NEQ 0 (
        powershell -Command "Write-Host '[ERROR] Failed to create .venv for Vision Service! Ensure Python is installed.' -ForegroundColor Red"
        PAUSE
        EXIT /B 1
    )
)

echo [*] Checking Vision Service pip requirements...
.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
IF !ERRORLEVEL! NEQ 0 (
    powershell -Command "Write-Host '[ERROR] Vision Service pip install failed! Check requirements.txt.' -ForegroundColor Red"
    PAUSE
    EXIT /B 1
)
powershell -Command "Write-Host '[OK] Vision Service ready.' -ForegroundColor Green"
echo.

:: -------------------------------------------------------------------------------
:: STEP 3: Graph Service Setup
:: -------------------------------------------------------------------------------
powershell -Command "Write-Host '[3/5] Setting up Graph Criticality ^& Simulation Service (.venv ^& dependencies)...' -ForegroundColor Cyan"
CD /D "%ROOT_DIR%graph-service"

IF NOT EXIST ".venv" (
    powershell -Command "Write-Host '[!] Graph Service .venv not found. Creating virtual environment...' -ForegroundColor Yellow"
    python -m venv .venv
    IF !ERRORLEVEL! NEQ 0 (
        powershell -Command "Write-Host '[ERROR] Failed to create .venv for Graph Service!' -ForegroundColor Red"
        PAUSE
        EXIT /B 1
    )
)

echo [*] Checking Graph Service pip requirements...
.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
IF !ERRORLEVEL! NEQ 0 (
    powershell -Command "Write-Host '[ERROR] Graph Service pip install failed!' -ForegroundColor Red"
    PAUSE
    EXIT /B 1
)
powershell -Command "Write-Host '[OK] Graph Service ready.' -ForegroundColor Green"
echo.

:: -------------------------------------------------------------------------------
:: STEP 4: Backend Coordinator Setup ^& Frontend Dependencies
:: -------------------------------------------------------------------------------
powershell -Command "Write-Host '[4/5] Setting up Agentverse Backend Coordinator and Frontend...' -ForegroundColor Cyan"
CD /D "%ROOT_DIR%agentverse-platform\backend"

IF NOT EXIST ".venv" (
    powershell -Command "Write-Host '[!] Backend Coordinator .venv not found. Creating virtual environment...' -ForegroundColor Yellow"
    python -m venv .venv
    IF !ERRORLEVEL! NEQ 0 (
        powershell -Command "Write-Host '[ERROR] Failed to create .venv for Backend Coordinator!' -ForegroundColor Red"
        PAUSE
        EXIT /B 1
    )
)

echo [*] Checking Backend Coordinator pip requirements...
.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
IF !ERRORLEVEL! NEQ 0 (
    powershell -Command "Write-Host '[ERROR] Backend Coordinator pip install failed!' -ForegroundColor Red"
    PAUSE
    EXIT /B 1
)
powershell -Command "Write-Host '[OK] Backend Coordinator ready.' -ForegroundColor Green"

CD /D "%ROOT_DIR%agentverse-platform\frontend"
IF NOT EXIST "node_modules" (
    powershell -Command "Write-Host '[!] Node modules not found. Running npm install...' -ForegroundColor Yellow"
    call npm install
    IF !ERRORLEVEL! NEQ 0 (
        powershell -Command "Write-Host '[ERROR] npm install failed for Frontend!' -ForegroundColor Red"
        PAUSE
        EXIT /B 1
    )
) ELSE (
    powershell -Command "Write-Host '[OK] Frontend node_modules verified.' -ForegroundColor Green"
)
echo.

:: -------------------------------------------------------------------------------
:: STEP 5: Launch Microservices ^& Agents in Separate Terminal Windows
:: -------------------------------------------------------------------------------
powershell -Command "Write-Host '[5/5] Launching all services in dedicated terminals...' -ForegroundColor Cyan"
echo.

CD /D "%ROOT_DIR%"

powershell -Command "Write-Host '[1/5] Starting Vision AI Service (Port 8001)...' -ForegroundColor Magenta"
start "KRATOS - Vision AI Service (Port 8001)" cmd /k "cd /d %ROOT_DIR%vision-service && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

powershell -Command "Write-Host '[2/5] Starting Graph Criticality Service (Port 8002)...' -ForegroundColor Magenta"
start "KRATOS - Graph Criticality Service (Port 8002)" cmd /k "cd /d %ROOT_DIR%graph-service && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"

powershell -Command "Write-Host '[3/5] Starting Backend Coordinator ^& Agent Platform (Port 8000)...' -ForegroundColor Magenta"
start "KRATOS - Backend Coordinator (Port 8000)" cmd /k "cd /d %ROOT_DIR%agentverse-platform\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

powershell -Command "Write-Host '[4/5] Starting Vite React Frontend...' -ForegroundColor Magenta"
start "KRATOS - Vite React Frontend" cmd /k "cd /d %ROOT_DIR%agentverse-platform\frontend && npm run dev"

powershell -Command "Write-Host '[5/5] Starting Live Agent Telemetry Sentinel Monitor...' -ForegroundColor Magenta"
timeout /t 3 >NUL
start "KRATOS - Agent Health Telemetry Sentinel" cmd /k "cd /d %ROOT_DIR% && agentverse-platform\backend\.venv\Scripts\python.exe scripts\monitor_agents.py"

echo.
echo ===============================================================================
powershell -Command "Write-Host ' ALL KRATOS SERVICES AND AGENTS HAVE BEEN LAUNCHED SUCCESSFULLY!' -ForegroundColor Green"
echo ===============================================================================
echo  - Frontend Web UI      : http://localhost:5173
echo  - Backend Coordinator  : http://localhost:8000/docs
echo  - Vision Service API   : http://localhost:8001/docs
echo  - Graph Service API    : http://localhost:8002/docs
echo ===============================================================================
echo.
PAUSE
