# Architecture & Technical Design

The **Smart Study Assistant Agent** is an end-to-end AI-powered study companion built using Streamlit, Google Gemini (`google-genai` SDK), and local state persistence.

---

## 1. System Architecture Overview

```
 ┌────────────────────────────────────────────────────────┐
 │                   Streamlit Web UI                     │
 │  (Tabs: Chat Tutor, Quiz, Exam, Cards, Plan, Map, Log) │
 └──────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
 ┌──────────────────────┐        ┌──────────────────────┐
 │   PDF / Text Loader  │        │ Session State & Data │
 │   (pypdf, cached)    │        │  (handlers.py / JSON)│
 └──────────┬───────────┘        └──────────────────────┘
            │
            ▼
 ┌───────────────────────────────────┐
 │ Text Processing & RAG Engine      │
 │ - Normalization & Whitespace Clean│
 │ - Overlapping Window Chunking     │
 │ - Frequency-Weighted Token Ranker │
 └──────────────────┬────────────────┘
                    │
                    ▼
 ┌───────────────────────────────────┐
 │       Gemini Integration Layer    │
 │ - `google.genai` SDK Client       │
 │ - Exponential Backoff Retries     │
 │ - Resilient JSON & Fenced Parser  │
 └──────────────────┬────────────────┘
                    │
                    ▼
 ┌───────────────────────────────────┐
 │        Google Gemini Models       │
 │   (gemini-2.5-flash-lite, etc.)   │
 └───────────────────────────────────┘
```

---

## 2. Core Modules

### `app/config.py`
- Manages application configuration, model parameters, context limits, and temperature settings.
- Resolves API credentials flexibly across user input (session state), environment variables (`.env`), and Streamlit secrets.
- Fetches and filters available Gemini models dynamically via `google.genai.Client.models.list()`.

### `app/gemini_utils.py`
- Instantiates Google Gemini SDK client with retry handlers.
- Implements `tenacity` retry with exponential backoff for transient network and 5xx errors while aborting early on invalid API keys.
- Robust JSON extraction parser handling markdown fences, trailing text, and nested objects.

### `app/text_processing.py`
- Text normalization (`clean_text`).
- Cached chunking with configurable overlap (`chunk_text_cached`, `get_chunks`) to prevent losing context across chunk boundaries.
- Weighted term-frequency keyword ranking (`rank_chunks`) prioritizing chunks with matching concepts.
- Document display formatting with word boundary-aware truncation.

### `app/pdf_utils.py`
- In-memory PDF text extraction using `pypdf.PdfReader`.
- MD5 file hash caching via `@st.cache_data` to avoid re-extracting large files upon rerun.

### `app/handlers.py`
- Session state initialization and synchronization with local `user_data.json`.
- Quiz option shuffling algorithm maintaining correct answer indexing.
- Weak topic tracking and quiz/exam score logging.

### `app/features.py`
- **Q&A Tutor (`answer_question`)**: Targeted chunk retrieval with confidence score output and beginner mode toggle.
- **Adaptive Quiz (`generate_quiz`)**: Generates 4-option MCQs with difficulty selection, feedback, and topic categorization.
- **Flashcard Deck (`generate_flashcards`)**: Targeted active recall cards prioritizing identified weak topics.
- **Revision Planner (`generate_revision_plan`)**: Structured 3-5 day study schedule.
- **Revision Notes (`generate_revision_notes`)**: Cheat-sheet summaries with mnemonics and common pitfalls.
- **Concept Mindmap (`generate_mindmap_markdown`)**: Mermaid.js mindmap diagram generation.
- **Executive Summary (`summarize_notes`)**: Multi-section document summary.

---

## 3. Data Persistence Schema

User progress and weak areas persist in `user_data.json`:

```json
{
  "weak_topics": [
    "Photosystem II",
    "Electron Transport Chain"
  ],
  "score_history": [
    {
      "date": "2026-09-18T07:15:00",
      "score_percent": 85,
      "type": "Quiz",
      "correct": 4,
      "total": 5
    }
  ]
}
```
