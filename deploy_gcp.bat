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

:: Deploy to Cloud Run
echo [INFO] Deploying to Google Cloud Run...
call gcloud run deploy smart-study-agent ^
  --source . ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --set-env-vars GOOGLE_API_KEY=AIzio,GEMINI_MODEL_NAME=gemini-3.1-flash-lite

if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Deployment completed successfully.
) else (
    echo [ERROR] Deployment failed.
)

endlocal