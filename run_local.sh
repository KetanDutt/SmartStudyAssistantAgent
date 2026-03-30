#!/bin/bash

echo "=============================================="
echo "  Smart Study Assistant Agent - Setup & Run"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3 and try again."
    return 1 2>/dev/null || exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        return 1 2>/dev/null || exit 1
    fi
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    return 1 2>/dev/null || exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "[INFO] .env file not found. Creating one from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "[WARNING] Please update the .env file with your actual GOOGLE_API_KEY before running."
    else
        echo "[ERROR] .env.example not found. Cannot create .env file."
    fi
else
    echo "[INFO] .env file found."
fi

# Run the Streamlit app locally
echo "[INFO] Starting Streamlit app..."
streamlit run app.py