from typing import Any, Dict, List
from app.config import (
    DEFAULT_MODEL,
    MAX_CONTEXT_WORDS_QA,
    MAX_CONTEXT_WORDS_SUMMARY,
    MAX_CONTEXT_WORDS_QUIZ,
    DEFAULT_TEMPERATURE,
    QUIZ_TEMPERATURE,
)
from app.text_processing import get_chunks, rank_chunks
from app.gemini_utils import _generate, _extract_json


def select_context_for_question(text: str, question: str, max_words: int = MAX_CONTEXT_WORDS_QA) -> str:
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


import streamlit as st

@st.cache_data(show_spinner=False)
def answer_question(context: str, question: str, model_name: str = DEFAULT_MODEL, beginner_mode: bool = False) -> str:
    selected_context = select_context_for_question(context, question, max_words=MAX_CONTEXT_WORDS_QA)

    beginner_instruction = (
        "* Explain as if teaching a 10-year-old\n* Use very simple analogies and examples\n"
        if beginner_mode else ""
    )

    prompt = f"""
You are an expert AI tutor helping a student learn effectively.

Instructions:
* Use ONLY the provided notes as your source.
* If information is missing, clearly say: "This is not covered in the notes."
* Explain concepts in a structured, easy-to-understand way.
* Use:
  * Bullet points
  * Simple language
  * Real-world examples
  * Highlight key terms using **bold**
* Keep answers concise but useful for revision.

If beginner_mode is enabled:
{beginner_instruction}

Include a "Confidence Score" at the very end of your answer on a new line, indicating how confident you are in your answer based on the notes. Example: "Confidence: High / Medium / Low"

Notes:
{selected_context}

Question:
{question}

Answer:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)


@st.cache_data(show_spinner=False)
def summarize_notes(context: str, model_name: str = DEFAULT_MODEL) -> str:
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_SUMMARY)
    prompt = f"""
You are an expert summarizer.

Create a high-quality study summary.

Requirements:
* Give a short title
* Include:
  * 5 key points
  * Important concepts
  * Key terms in **bold**
* Use bullet points
* Keep it concise and revision-friendly

Notes:
{selected_context}

Summary:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)


@st.cache_data(show_spinner=False)
def generate_quiz(
    context: str,
    num_questions: int = 5,
    model_name: str = DEFAULT_MODEL,
    exam_mode: bool = False,
) -> List[Dict[str, Any]]:
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_QUIZ)
    mode_line = (
        "* Do not include explanations in the questions section."
        if exam_mode
        else "* Include:\n  * Short explanation\n  * Real-world or conceptual clarity"
    )

    prompt = f"""
You are an expert teacher creating a high-quality quiz for revision.

Return ONLY valid JSON in this exact format:
{{
"title": "Quiz title",
"items": [
{{
"id": 1,
"topic": "topic name",
"question": "clear question",
"options": ["A", "B", "C", "D"],
"answer_index": 0,
"explanation": "short explanation"
}}
]
}}

Rules:
* Create exactly {num_questions} questions
* Each question must:
  * Be clear and unambiguous
  * Test understanding (not just memorization)
* Use 4 options always
* Only ONE correct answer
{mode_line}
* Cover different topics evenly
* Keep language simple and beginner-friendly
* Do NOT include extra text outside JSON

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
    import random
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

        clean_options = [str(opt).strip() for opt in options[:4]]
        # Randomize options
        indexed_options = list(enumerate(clean_options))
        random.shuffle(indexed_options)

        shuffled_options = []
        new_answer_index = 0
        for new_idx, (original_idx, opt) in enumerate(indexed_options):
            shuffled_options.append(opt)
            if original_idx == answer_index:
                new_answer_index = new_idx

        normalized.append(
            {
                "id": item.get("id", idx),
                "topic": str(item.get("topic", "General")).strip() or "General",
                "question": str(item.get("question", "")).strip(),
                "options": shuffled_options,
                "answer_index": new_answer_index,
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )

    if len(normalized) < max(1, num_questions // 2):
        raise RuntimeError(
            "Quiz generation did not return enough valid questions. Try again with a shorter PDF or notes."
        )
    return normalized[:num_questions]


@st.cache_data(show_spinner=False)
def generate_flashcards(context: str, weak_topics: List[str], model_name: str) -> List[Dict[str, str]]:
    """Generates simple flashcards for weak topics."""
    topic_list = ", ".join(weak_topics)
    if not topic_list:
        return []

    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_QUIZ)
    prompt = f"""
You are a learning assistant generating revision flashcards.

Create 5 high-quality flashcards.

Return ONLY valid JSON:
{{
"flashcards": [
{{
"front": "question or concept",
"back": "clear explanation"
}}
]
}}

Rules:
* Keep front short and clear
* Back should:
  * Explain simply
  * Include key idea
* Focus on important concepts
* Avoid long paragraphs

Notes:
{selected_context}
Weak topics:
{topic_list}
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


@st.cache_data(show_spinner=False)
def generate_revision_plan(context: str, weak_topics: List[str], model_name: str = DEFAULT_MODEL) -> str:
    topic_list = ", ".join(sorted(set([t for t in weak_topics if t.strip()]))) or "general topics"
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_SUMMARY)
    prompt = f"""
You are an expert study coach.

The student is weak in these topics:
{topic_list}

Create a structured 3–5 day revision plan.

Requirements:
* Organize clearly by Day (Day 1, Day 2…)
* For each day include:
  * 🎯 Goal of the day
  * 📚 Topics to study
  * ✅ 2–3 actionable tasks
  * ⏱ Estimated time (optional)
* Keep it realistic and achievable
* Use simple, motivating language
* Format using clean markdown

Notes:
{selected_context}

Revision Plan:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)

@st.cache_data(show_spinner=False)
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
