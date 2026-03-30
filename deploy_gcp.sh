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

# Read variables from .env
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found. Please create one with GOOGLE_API_KEY and GEMINI_MODEL_NAME."
    return 1 2>/dev/null || exit 1
fi

while IFS='=' read -r key value; do
    if [[ ! $key =~ ^# && -n $key ]]; then
        export "$key=$value"
    fi
done < .env

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "[ERROR] GOOGLE_API_KEY is not set in .env."
    return 1 2>/dev/null || exit 1
fi

MODEL_NAME=${GEMINI_MODEL_NAME:-"gemini-2.5-flash"}

# Deploy to Cloud Run
echo "[INFO] Deploying to Google Cloud Run with model $MODEL_NAME..."
gcloud run deploy smart-study-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY="${GOOGLE_API_KEY}",GEMINI_MODEL_NAME="${MODEL_NAME}"

if [ $? -eq 0 ]; then
    echo "[SUCCESS] Deployment completed successfully."
else
    echo "[ERROR] Deployment failed."
fi