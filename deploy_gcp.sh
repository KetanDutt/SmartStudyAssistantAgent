#!/bin/bash

echo "=============================================="
echo "  Smart Study Assistant Agent - GCP Deploy"
echo "=============================================="

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] Google Cloud SDK (gcloud) is not installed or not in PATH."
    echo "Please install it from https://cloud.google.com/sdk/docs/install and try again."
    return 1 2>/dev/null || exit 1
fi

# Ensure user is authenticated
echo "[INFO] Please make sure you are logged in to gcloud..."
gcloud auth login --update-adc

# Deploy to Cloud Run
echo "[INFO] Deploying to Google Cloud Run..."
gcloud run deploy smart-study-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=AIzio,GEMINI_MODEL_NAME=gemini-3.1-flash-lite

if [ $? -eq 0 ]; then
    echo "[SUCCESS] Deployment completed successfully."
else
    echo "[ERROR] Deployment failed."
fi