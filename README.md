# Smart Study Assistant Agent

A beginner-friendly Streamlit app for the GenAI Academy project submission.

## Features

- **File Upload:** Upload a PDF or paste notes to get started
- **Dynamic Model Selection:** Choose from a dynamically generated list of available Gemini text-to-text models
- **Q&A System:** Ask questions about the study material, featuring a simple explanation "Explain Like I'm 10" mode and confidence scores
- **Quizzes:** Generate MCQ quizzes with instant feedback
- **Exam Mode:** Practice exam mode where answers stay hidden until submission
- **Performance Analytics:** Track weak topics, view color-coded scores, and percentage breakdowns
- **Smart Revision:** Generate structured 3-5 day revision plans from weak topics
- **Interactive Flashcards:** Create interactive click-to-reveal flashcards focusing on your weak areas
- **Quick Summaries:** Generate 5-point summaries of your uploaded materials
- **Persistent Storage:** Results and weak areas are saved and reload upon page refresh

## Demo Steps

1. Add your Google Gemini API key to `.env`
2. Run `streamlit run app.py`
3. Upload a PDF or paste your notes on the sidebar
4. Ask a question and toggle "Explain Like I'm 10 Mode"
5. Switch to the Quiz tab and generate a quiz, intentionally getting some wrong
6. View the new Performance Dashboard and how your weak topics are tracked
7. Go to the Weak Areas tab to generate a Smart Revision Plan and Flashcards
8. Test the interactive click-to-reveal on the Flashcards

## Tech stack

- Python
- Streamlit
- Gemini API via `google-generativeai`
- `python-dotenv`
- `pypdf`

## Local setup

Create a `.env` file in the project root based on `.env.example`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash
```

We provide convenient scripts to automatically setup your environment, install dependencies, and run the app.

**Windows:**
```cmd
run_local.bat
```

**macOS / Linux:**
```bash
./run_local.sh
```

Alternatively, you can manually set it up:

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Cloud Run deployment

We provide deployment scripts that automatically read your `GOOGLE_API_KEY` and `GEMINI_MODEL_NAME` from your `.env` file and deploy the app to Google Cloud Run.

Make sure you are authenticated with `gcloud` and have selected your project:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

Then simply run the deployment script for your platform.

**Windows:**
```cmd
deploy_gcp.bat
```

**macOS / Linux:**
```bash
./deploy_gcp.sh
```

Alternatively, you can deploy manually:
```bash
gcloud run deploy smart-study-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=YOUR_GEMINI_API_KEY,GEMINI_MODEL_NAME=gemini-2.5-flash
```

## Notes

- Do not commit your `.env` file.
- For production, consider storing the API key in Secret Manager.
