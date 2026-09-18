# Deployment Guide

This guide describes how to run and deploy the **Smart Study Assistant Agent** locally, in Docker, and on Google Cloud Run.

---

## 1. Prerequisites

- Python 3.9+ (Python 3.11 recommended)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- (Optional) Docker or Google Cloud SDK (`gcloud`)

---

## 2. Local Setup & Execution

### Automated Scripts

**Linux / macOS:**
```bash
chmod +x run_local.sh
./run_local.sh
```

**Windows:**
```cmd
run_local.bat
```

### Manual Setup
```bash
# Clone the repository
git clone https://github.com/KetanDutt/SmartStudyAssistantAgent.git
cd SmartStudyAssistantAgent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env to add your GOOGLE_API_KEY

# Run the app
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 3. Docker Container Deployment

### Build the Docker Image
```bash
docker build -t smart-study-agent:latest .
```

### Run the Container
```bash
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY="your_api_key_here" \
  -e GEMINI_MODEL_NAME="gemini-2.5-flash-lite" \
  smart-study-agent:latest
```

The app will be available on `http://localhost:8080`.

---

## 4. Google Cloud Run Deployment

### Option A: Using the Provided Deploy Script
```bash
# Ensure gcloud is configured
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy via script
./deploy_gcp.sh  # or deploy_gcp.bat on Windows
```

### Option B: Direct gcloud Command
```bash
gcloud run deploy smart-study-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars GOOGLE_API_KEY=YOUR_KEY,GEMINI_MODEL_NAME=gemini-2.5-flash-lite
```

---

## 5. Security & Best Practices

1. **API Key Security**: Never commit `.env` or API keys into git. Use Google Secret Manager or Cloud Run environment variables for production deployments.
2. **Health Checks**: The Dockerfile includes an automatic health check endpoint targeting Streamlit's `/_stcore/health`.
3. **CORS & Origin Handling**: Configured in `.streamlit/config.toml` for seamless container proxying.
