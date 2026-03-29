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


def answer_question(context: str, question: str, model_name: str = DEFAULT_MODEL, beginner_mode: bool = False) -> str:
    selected_context = select_context_for_question(context, question, max_words=MAX_CONTEXT_WORDS_QA)

    beginner_instruction = (
        "- Explain it extremely simply, as if you are explaining it to a 10-year-old, using easy-to-understand examples.\n"
        if beginner_mode else ""
    )

    prompt = f"""
You are a friendly study assistant helping a student learn from their notes.

Rules:
- Use only the provided notes as your source.
- If the notes do not contain enough information, say so clearly.
- Explain in simple language.
{beginner_instruction}- Keep the answer structured and easy to revise.

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


def generate_revision_plan(context: str, weak_topics: List[str], model_name: str = DEFAULT_MODEL) -> str:
    topic_list = ", ".join(sorted(set([t for t in weak_topics if t.strip()]))) or "general topics"
    selected_context = select_context_for_generation(context, max_words=MAX_CONTEXT_WORDS_SUMMARY)
    prompt = f"""
You are an expert study coach. The student needs to improve on these weak topics: {topic_list}.
Based on the provided notes, create a structured 3 to 5-day revision plan.

Requirements:
- Organize by Day (e.g., Day 1: [Topic]).
- For each day, include 2-3 specific, actionable daily tasks.
- Provide a short goal for the day.
- Format the plan clearly using Markdown headers and bullet points.
- Keep the language encouraging and simple.

Notes:
{selected_context}

Revision Plan:
"""
    return _generate(model_name, prompt, temperature=DEFAULT_TEMPERATURE)

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
