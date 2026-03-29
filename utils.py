import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, List

from dotenv import load_dotenv
from pypdf import PdfReader
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

MAX_CONTEXT_WORDS_QA = 2600
MAX_CONTEXT_WORDS_SUMMARY = 3000
MAX_CONTEXT_WORDS_QUIZ = 2000
DEFAULT_TEMPERATURE = 0.2
QUIZ_TEMPERATURE = 0.3

if API_KEY:
    genai.configure(api_key=API_KEY)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "could", "did", "do", "does", "doing", "for", "from", "had", "has", "have",
    "he", "her", "hers", "him", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "just", "me", "more", "most", "my", "no", "not", "of", "on",
    "or", "our", "out", "over", "she", "so", "some", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "to", "too",
    "us", "was", "we", "were", "what", "when", "where", "which", "who",
    "why", "with", "would", "you", "your"
}


def require_api_key() -> None:
    if not API_KEY:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Add it to your .env file or set it as an environment variable."
        )


def validate_api_key() -> bool:
    try:
        require_api_key()
        return True
    except RuntimeError:
        return False


@lru_cache(maxsize=4)
def get_model(model_name: str = DEFAULT_MODEL):
    require_api_key()
    return genai.GenerativeModel(model_name)


def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return clean_text("\n".join(pages))


def clean_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


import hashlib


@lru_cache(maxsize=4)
def chunk_text_cached(text_hash: str, text: str, max_words: int = 900) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    for start in range(0, len(words), max_words):
        chunk = " ".join(words[start:start + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def chunk_text(text: str, max_words: int = 900) -> List[str]:
    """Helper for chunking to avoid changing existing calls."""
    return get_chunks(text, max_words)


def get_chunks(text: str, max_words: int = 900) -> List[str]:
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return chunk_text_cached(text_hash, text, max_words)


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", text) if w.lower() not in STOPWORDS]


def rank_chunks(query: str, chunks: List[str], top_k: int = 4) -> List[str]:
    """Return the top_k chunks most relevant to the query using keyword overlap."""
    if not chunks:
        return []

    query_tokens = set(tokenize(query))
    if not query_tokens:
        return chunks[:top_k]

    scored = []
    for chunk in chunks:
        tokens = tokenize(chunk)
        if not tokens:
            score = 0
        else:
            overlap = len(query_tokens.intersection(tokens))
            score = overlap / max(1, len(query_tokens))
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [chunk for score, chunk in scored[:top_k] if score > 0]
    if not selected:
        selected = chunks[:top_k]
    return selected


def select_context_for_question(text: str, question: str, max_words: int = 2600) -> str:
    chunks = get_chunks(text)
    selected = rank_chunks(question, chunks, top_k=5)
    if not selected:
        selected = chunks[:4] if chunks else [text]

    combined = "\n\n".join(selected).strip()
    if len(combined.split()) > max_words:
        combined = " ".join(combined.split()[:max_words])
    return combined


def select_context_for_generation(text: str, max_words: int = 3200) -> str:
    chunks = get_chunks(text)
    if not chunks:
        return text

    if len(text.split()) <= max_words:
        return text

    # Use a mix of the first chunks and a few spread across the content to keep coverage.
    chosen = chunks[:2]
    if len(chunks) > 4:
        chosen.append(chunks[len(chunks) // 2])
    if len(chunks) > 6:
        chosen.append(chunks[-2])
    context = "\n\n".join(chosen)
    return " ".join(context.split()[:max_words])


def split_notes_for_display(text: str, max_chars: int = 3500) -> str:
    text = clean_text(text)
    return text[:max_chars] + ("\n\n..." if len(text) > max_chars else "")


def _extract_json(text: str) -> Any:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    first_obj = text.find("{")
    last_obj = text.rfind("}")
    first_arr = text.find("[")
    last_arr = text.rfind("]")

    candidates = []
    if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
        candidates.append(text[first_obj:last_obj + 1])
    if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
        candidates.append(text[first_arr:last_arr + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Model did not return valid JSON.")


def _generate(model_name: str, prompt: str, temperature: float = DEFAULT_TEMPERATURE) -> str:
    model = get_model(model_name)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": 2048,
        },
    )

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        raise RuntimeError(f"Prompt blocked: {response.prompt_feedback.block_reason}")

    if not response.candidates:
        raise RuntimeError("No response candidates returned by Gemini.")

    candidate = response.candidates[0]
    if candidate.finish_reason != 1:  # 1 = STOP
        raise RuntimeError(f"Generation stopped due to: {candidate.finish_reason}")

    text = candidate.content.parts[0].text if candidate.content.parts else ""
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text.strip()


def answer_question(context: str, question: str, model_name: str = DEFAULT_MODEL) -> str:
    selected_context = select_context_for_question(context, question, max_words=MAX_CONTEXT_WORDS_QA)
    prompt = f"""
You are a friendly study assistant helping a student learn from their notes.

Rules:
- Use only the provided notes as your source.
- If the notes do not contain enough information, say so clearly.
- Explain in simple language.
- Keep the answer structured and easy to revise.

Notes:
{selected_context}

Student question:
{question}

Answer:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)


def summarize_notes(context: str, model_name: str = DEFAULT_MODEL) -> str:
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_SUMMARY)
    prompt = f"""
Summarize these study notes for a student.

Requirements:
- Give a short title.
- Include the 5 most important ideas.
- Use simple wording.
- Keep it concise but useful for revision.

Notes:
{selected_context}

Summary:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)


def generate_quiz(
    context: str,
    num_questions: int = 5,
    model_name: str = DEFAULT_MODEL,
    exam_mode: bool = False,
) -> List[Dict[str, Any]]:
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_QUIZ)
    mode_line = (
        "Do not include explanations in the questions section."
        if exam_mode
        else "Include a short explanation for the correct answer."
    )

    prompt = f"""
Create a JSON object for a study quiz based only on the notes below.

Return ONLY valid JSON with this exact shape:
{{
  "title": "Quiz title",
  "items": [
    {{
      "id": 1,
      "topic": "short topic name",
      "question": "question text",
      "options": ["option A", "option B", "option C", "option D"],
      "answer_index": 0,
      "explanation": "short explanation"
    }}
  ]
}}

Rules:
- Make exactly {num_questions} items.
- Every question must have exactly 4 options.
- answer_index must be 0, 1, 2, or 3.
- Keep the language simple and beginner-friendly.
- Choose practical questions that help revision.
- {mode_line}
- Do not wrap the JSON in markdown fences.
- Do not add extra text.

Notes:
{selected_context}
"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            raw = _generate(model_name, prompt, temperature=QUIZ_TEMPERATURE)
            data = _extract_json(raw)
            break
        except ValueError:
            if attempt == max_retries - 1:
                raise
            prompt += "\n\nReturn ONLY valid JSON, no extra text."

    items = data.get("items", []) if isinstance(data, dict) else []
    normalized = []
    for idx, item in enumerate(items[:num_questions], start=1):
        options = item.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            continue
        answer_raw = item.get("answer_index", 0)
        try:
            answer_index = int(answer_raw)
        except Exception:
            answer_index = 0
        if answer_index not in (0, 1, 2, 3):
            answer_index = 0
        normalized.append(
            {
                "id": item.get("id", idx),
                "topic": str(item.get("topic", "General")).strip() or "General",
                "question": str(item.get("question", "")).strip(),
                "options": [str(opt).strip() for opt in options[:4]],
                "answer_index": answer_index,
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )

    if len(normalized) < max(1, num_questions // 2):
        raise RuntimeError(
            "Quiz generation did not return enough valid questions. Try again with a shorter PDF or notes."
        )
    return normalized[:num_questions]


def generate_flashcards(context: str, weak_topics: List[str], model_name: str) -> List[Dict[str, str]]:
    """Generates simple flashcards for weak topics."""
    topic_list = ", ".join(weak_topics)
    if not topic_list:
        return []

    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_QUIZ)
    prompt = f"""
Create 5 simple flashcards based on the notes. Focus on these topics: {topic_list}.
If the topics are not well covered, make flashcards for important general concepts in the notes.

Return ONLY valid JSON with this exact shape:
{{
  "flashcards": [
    {{
      "front": "Question or term",
      "back": "Short answer or definition"
    }}
  ]
}}

Notes:
{selected_context}
"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            raw = _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)
            data = _extract_json(raw)
            return data.get("flashcards", [])
        except ValueError:
            if attempt == max_retries - 1:
                return []
            prompt += "\n\nReturn ONLY valid JSON, no extra text."
    return []


def generate_revision_notes(
    context: str,
    weak_topics: List[str],
    model_name: str = DEFAULT_MODEL,
) -> str:
    topic_list = ", ".join(sorted(set([t for t in weak_topics if t.strip()]))) or "general weak areas"
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_SUMMARY)
    prompt = f"""
You are a patient tutor. Create revision notes for the student's weak topics.

Weak topics:
{topic_list}

Use the study notes below to produce:
- a simple explanation for each weak topic
- one memory trick or example
- one short revision checklist

Keep it beginner-friendly and concise.

Notes:
{selected_context}

Revision notes:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)
