@echo off
SETLOCAL

REM Check if .venv exists
IF NOT EXIST ".venv" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv .venv
    
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate
    
    echo [INFO] Installing dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo [INFO] Setup complete.
) ELSE (
    echo [INFO] Virtual environment found. Activating...
    call .venv\Scripts\activate
)

REM Check if .env exists
IF NOT EXIST ".env" (
    echo [INFO] .env not found. Creating from .env.example...
    copy .env.example .env
    echo [WARNING] Please check .env and update your database credentials if necessary.
)

REM Add current directory to PYTHONPATH so 'app' module can be found
set PYTHONPATH=%~dp0

echo [INFO] Starting ExoHunter Pro...
streamlit run streamlit_app.py

ENDLOCAL
pause