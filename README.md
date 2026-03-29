# Smart Study Assistant Agent

A beginner-friendly Streamlit app for the GenAI Academy project submission.

## Features
- Upload a PDF or paste notes
- Ask questions about the study material
- Generate MCQ quizzes
- Run exam mode
- Track weak topics from incorrect answers
- Generate revision notes and summaries

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
GEMINI_MODEL_NAME=gemini-1.5-flash
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

gcloud run deploy study-agent   --source .   --region us-central1   --allow-unauthenticated   --set-env-vars GOOGLE_API_KEY=YOUR_GEMINI_API_KEY,GEMINI_MODEL_NAME=gemini-1.5-flash
```

## Notes
- Do not commit your `.env` file.
- For production, consider storing the API key in Secret Manager.
