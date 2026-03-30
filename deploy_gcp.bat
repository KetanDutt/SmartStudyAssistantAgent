@echo off
setlocal

echo ==============================================
echo   Smart Study Assistant Agent - GCP Deploy
echo ==============================================

echo Checking gcloud installation...
call gcloud --version

if errorlevel 1 (
    echo [ERROR] Google Cloud SDK ^(gcloud^) is not installed or not in PATH.
    pause
    exit /b 1
)

echo [OK] gcloud is installed

if not exist ".env" (
    echo [ERROR] .env file not found.
    pause
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if "%%A"=="GOOGLE_API_KEY" set "GOOGLE_API_KEY=%%B"
    if "%%A"=="GEMINI_MODEL_NAME" set "GEMINI_MODEL_NAME=%%B"
)

if "%GOOGLE_API_KEY%"=="" (
    echo [ERROR] GOOGLE_API_KEY not set
    pause
    exit /b 1
)

if "%GEMINI_MODEL_NAME%"=="" set "GEMINI_MODEL_NAME=gemini-2.5-flash"

echo [INFO] Deploying to Google Cloud Run with model %GEMINI_MODEL_NAME%...
call gcloud run deploy smart-study-agent ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --set-env-vars GOOGLE_API_KEY="%GOOGLE_API_KEY%",GEMINI_MODEL_NAME="%GEMINI_MODEL_NAME%"

pause
endlocal