@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo   Smart Study Assistant Agent - Setup ^& Run
echo ==============================================

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python and try again.
    goto :EOF
)

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        goto :EOF
    )
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo [INFO] Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    goto :EOF
)

:: Check for .env file
if not exist ".env" (
    echo [INFO] .env file not found. Creating one from .env.example...
    if exist ".env.example" (
        copy .env.example .env
        echo [WARNING] Please update the .env file with your actual GOOGLE_API_KEY before running.
    ) else (
        echo [ERROR] .env.example not found. Cannot create .env file.
    )
) else (
    echo [INFO] .env file found.
)

:: Run the Streamlit app locally
echo [INFO] Starting Streamlit app...
streamlit run app.py

endlocal