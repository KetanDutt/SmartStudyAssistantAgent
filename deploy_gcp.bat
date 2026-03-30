@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo   Smart Study Assistant Agent - GCP Deploy
echo ==============================================

:: Check if gcloud CLI is installed
gcloud --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Google Cloud SDK ^(gcloud^) is not installed or not in PATH.
    echo Please install it from https://cloud.google.com/sdk/docs/install and try again.
    goto :EOF
)

:: Ensure user is authenticated
echo [INFO] Please make sure you are logged in to gcloud...
call gcloud auth login --update-adc

:: Read variables from .env
if not exist ".env" (
    echo [ERROR] .env file not found. Please create one with GOOGLE_API_KEY and GEMINI_MODEL_NAME.
    goto :EOF
)

for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    if "%%A"=="GOOGLE_API_KEY" set GOOGLE_API_KEY=%%B
    if "%%A"=="GEMINI_MODEL_NAME" set GEMINI_MODEL_NAME=%%B
)

if "%GOOGLE_API_KEY%"=="" (
    echo [ERROR] GOOGLE_API_KEY is not set in .env.
    goto :EOF
)

if "%GEMINI_MODEL_NAME%"=="" (
    set GEMINI_MODEL_NAME=gemini-2.5-flash
)

:: Deploy to Cloud Run
echo [INFO] Deploying to Google Cloud Run with model %GEMINI_MODEL_NAME%...
call gcloud run deploy smart-study-agent ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --set-env-vars GOOGLE_API_KEY="%GOOGLE_API_KEY%",GEMINI_MODEL_NAME="%GEMINI_MODEL_NAME%"

if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Deployment completed successfully.
) else (
    echo [ERROR] Deployment failed.
)

endlocal