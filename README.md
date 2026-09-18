# 📚 Smart Study Assistant Agent

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini SDK](https://img.shields.io/badge/Google%20GenAI-v1.69.0-4285F4.svg)](https://github.com/google-gemini/generative-ai-python)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, production-ready AI study companion and revision assistant powered by Google Gemini and Streamlit. Designed for students, educators, and lifelong learners to turn course documents, textbooks, and notes into interactive tutoring dialogues, adaptive MCQ quizzes, active recall flashcard decks, and structured revision plans.

---

## 🌟 Key Features

- **📄 Document Ingestion:** Upload PDF files or paste lecture notes with automatic cleaning, deduplication, and cached parsing.
- **💬 Conversational AI Tutor:** Ask questions about your study material with chat history, verified citations from the notes, confidence scores, and an optional **"Explain Like I'm 10"** mode.
- **📝 Adaptive Practice Quizzes:** Generate randomized MCQs across custom difficulty levels (`Beginner`, `Medium`, `Hard`) with immediate answer explanations and option shuffling.
- **🎓 Timed Exam Simulation:** Practice in test mode where solutions stay strictly hidden until submission.
- **🎴 Spaced Recall Flashcards:** Interactive flashcards with click-to-flip functionality prioritizing your detected weak topics, with mastery tracking and JSON export.
- **🧠 Weak Areas Tracker & Smart Revision:** Automatically captures topics missed in quizzes and exams. Generate custom 3–5 day step-by-step revision timetables and high-yield condensed revision notes.
- **🗺️ Visual Concept Mindmap:** Generates Mermaid.js hierarchical mindmaps illustrating connections between key ideas.
- **📄 Executive Summary:** Multi-section study summaries covering core thesis, 5 critical takeaways, and self-check questions.
- **📈 Analytics & Progress Dashboard:** Track test scores over time with interactive line charts, performance metrics, and CSV export.
- **🔐 Flexible Credentials:** Support for `.env`, environment variables, Streamlit secrets, or on-the-fly UI input with live API key validation.

---

## 🚀 Quick Start

### 1. Clone & Set Up

```bash
git clone https://github.com/KetanDutt/SmartStudyAssistantAgent.git
cd SmartStudyAssistantAgent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash-lite
```

*(You can also enter your API key directly in the sidebar during runtime!)*

### 3. Launch the Application

```bash
streamlit run app.py
```

Or run our pre-configured startup script:
- **macOS / Linux:** `./run_local.sh`
- **Windows:** `run_local.bat`

---

## 📖 Detailed Documentation

Explore comprehensive documentation inside the [`docs/`](docs/) directory:

- [**System Architecture & Technical Design**](docs/ARCHITECTURE.md): Deep dive into the RAG pipeline, chunking logic, and components.
- [**Feature Guide & User Manual**](docs/FEATURES.md): Step-by-step walkthrough of all study modes and tools.
- [**Deployment Guide**](docs/DEPLOYMENT.md): Instructions for local execution, Docker containerization, and Google Cloud Run.
- [**Testing & Quality Assurance**](docs/TESTING.md): Unit testing instructions and linting guidelines.

---

## 🛠️ Tech Stack

- **Frontend & App Framework:** [Streamlit](https://streamlit.io/)
- **LLM SDK:** Official Google GenAI SDK (`google-genai`)
- **PDF Extraction:** `pypdf`
- **Resilience & Caching:** `tenacity`, `streamlit.cache_data`, `lru_cache`
- **Data Analytics:** `pandas`
- **Testing & Quality:** `pytest`, `black`, `flake8`

---

## 🧪 Testing & Code Quality

Run tests and style checks:

```bash
# Run test suite
pytest

# Code formatting check
black --check app tests app.py

# Linting
flake8 --max-line-length=88 --extend-ignore=E203,W503 app tests
```

---

## 🐳 Docker & Cloud Deployment

### Run with Docker

```bash
docker build -t smart-study-agent .
docker run -p 8080:8080 -e GOOGLE_API_KEY="your_api_key" smart-study-agent
```

### Deploy to Google Cloud Run

```bash
./deploy_gcp.sh  # or deploy_gcp.bat on Windows
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
