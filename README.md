# Smart Study Assistant Agent

A beginner-friendly Streamlit app for the GenAI Academy project submission.

## Features
- **File Upload:** Upload a PDF or paste notes to get started
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

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash
```

Run the app:

```bash
streamlit run app.py
```

## Cloud Run deployment

Build and deploy from the project folder:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud run deploy study-agent   --source .   --region us-central1   --allow-unauthenticated   --set-env-vars GOOGLE_API_KEY=YOUR_GEMINI_API_KEY,GEMINI_MODEL_NAME=gemini-2.0-flash
```

## Notes
- Do not commit your `.env` file.
- For production, consider storing the API key in Secret Manager.
