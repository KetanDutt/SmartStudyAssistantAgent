"""
AI study features module.
Includes Q&A tutor, summary, MCQ quiz, flashcard generator,
revision planning, and mindmap generation using Google Gemini.
"""

from typing import Any, Dict, List, Optional
import streamlit as st

from app.config import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_CONTEXT_WORDS_QA,
    MAX_CONTEXT_WORDS_QUIZ,
    MAX_CONTEXT_WORDS_SUMMARY,
    QUIZ_TEMPERATURE,
)
from app.gemini_utils import _extract_json, _generate
from app.text_processing import get_chunks, rank_chunks


def select_context_for_question(
    text: str, question: str, max_words: int = MAX_CONTEXT_WORDS_QA
) -> str:
    """Retrieve relevant context chunks for a student question."""
    chunks = get_chunks(text)
    selected = rank_chunks(question, chunks, top_k=5)
    if not selected:
        selected = chunks[:4] if chunks else [text]

    combined = "\n\n".join(selected).strip()
    words = combined.split()
    if len(words) > max_words:
        combined = " ".join(words[:max_words])
    return combined


def select_context_for_generation(text: str, max_words: int = 3200) -> str:
    """Select representative context across documents for generation tasks."""
    chunks = get_chunks(text)
    if not chunks:
        return text

    words = text.split()
    if len(words) <= max_words:
        return text

    # Select representative chunks across the document
    if len(chunks) <= 4:
        return " ".join(words[:max_words])

    # Sample beginning, middle, and end chunks to provide holistic coverage
    sample_indices = [
        0,
        len(chunks) // 4,
        len(chunks) // 2,
        (3 * len(chunks)) // 4,
        len(chunks) - 1,
    ]
    seen = set()
    sampled_chunks = []
    for idx in sample_indices:
        if idx not in seen and idx < len(chunks):
            seen.add(idx)
            sampled_chunks.append(chunks[idx])

    combined = "\n\n".join(sampled_chunks)
    return " ".join(combined.split()[:max_words])


@st.cache_data(show_spinner=False)
def answer_question(
    context: str,
    question: str,
    model_name: str = DEFAULT_MODEL,
    beginner_mode: bool = False,
    api_key: Optional[str] = None,
) -> str:
    """Answer a user question strictly based on the provided notes."""
    selected_context = select_context_for_question(
        context, question, max_words=MAX_CONTEXT_WORDS_QA
    )

    beginner_instruction = (
        "* Explain as if teaching a 10-year-old using simple analogies.\n"
        if beginner_mode
        else ""
    )

    prompt = f"""
You are an expert AI study tutor helping a student master their course material.

Instructions:
* Rely primarily on the provided study notes.
* If a question cannot be answered from the notes, state:
  "This topic is not covered in your uploaded notes."
* Explain clearly with structured sections, bullet points, and **bold** keywords.
* Include a short real-world example or practical intuition.
{beginner_instruction}
* Always conclude your answer with an explicit confidence indicator on its own line:
**Confidence:** High | Medium | Low (based on coverage in the notes)

Study Notes:
{selected_context}

Student Question:
{question}

Tutor Answer:
"""
    return _generate(
        model_name, prompt, temperature=DEFAULT_TEMPERATURE, api_key=api_key
    )


@st.cache_data(show_spinner=False)
def summarize_notes(
    context: str,
    model_name: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
) -> str:
    """Generate a structured, executive study summary with key concepts."""
    selected_context = select_context_for_generation(
        context, max_words=MAX_CONTEXT_WORDS_SUMMARY
    )
    prompt = f"""
You are an expert academic summarizer.

Analyze the notes and generate an engaging, structured study summary:
1. Short Title & Core Thesis (1-2 sentences)
2. 5 Critical Key Takeaways (bullet points)
3. Essential Concepts & Definitions (with **bold** terms)
4. Key Formulas / Rules / Principles (if applicable)
5. Quick Self-Check Question

Keep formatting clean with clear markdown headers.

Study Notes:
{selected_context}

Summary:
"""
    return _generate(
        model_name, prompt, temperature=DEFAULT_TEMPERATURE, api_key=api_key
    )


@st.cache_data(show_spinner=False)
def generate_quiz(
    context: str,
    num_questions: int = 5,
    model_name: str = DEFAULT_MODEL,
    exam_mode: bool = False,
    difficulty: str = "Medium",
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Generate multiple-choice quiz questions formatted in JSON."""
    selected_context = select_context_for_generation(
        context, max_words=MAX_CONTEXT_WORDS_QUIZ
    )

    prompt = f"""
You are an expert educational examiner creating a {difficulty.lower()} MCQ quiz.

Create exactly {num_questions} multiple-choice questions testing concepts.

Return ONLY a valid JSON object matching this schema:
{{
  "title": "Quiz Title",
  "items": [
    {{
      "id": 1,
      "topic": "Specific Topic Name",
      "question": "Clear, unambiguous question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer_index": 0,
      "explanation": "Clear explanation of why the correct option is right"
    }}
  ]
}}

Rules:
* Exactly {num_questions} questions.
* Exactly 4 options per question.
* answer_index must be an integer from 0 to 3 pointing to the correct option.
* Difficulty level: {difficulty}.
* Do NOT include any markdown code blocks or text outside the JSON.

Notes:
{selected_context}
"""
    max_retries = 3
    data = {}
    for attempt in range(max_retries):
        try:
            raw = _generate(
                model_name,
                prompt,
                temperature=QUIZ_TEMPERATURE,
                api_key=api_key,
            )
            data = _extract_json(raw)
            if isinstance(data, dict) and "items" in data:
                break
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"Quiz generation failed after {max_retries} attempts: {e}"
                )
            prompt += (
                f"\n\nRetry notice: Previous attempt failed ({e}). "
                "Ensure output is strictly valid JSON."
            )

    items = data.get("items", []) if isinstance(data, dict) else []
    normalized = []
    for idx, item in enumerate(items[:num_questions], start=1):
        options = item.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            continue
        try:
            answer_index = int(item.get("answer_index", 0))
        except (ValueError, TypeError):
            answer_index = 0

        if answer_index not in (0, 1, 2, 3):
            answer_index = 0

        clean_options = [str(opt).strip() for opt in options]

        normalized.append(
            {
                "id": item.get("id", idx),
                "topic": str(item.get("topic", "General")).strip() or "General",
                "question": str(item.get("question", "")).strip(),
                "options": clean_options,
                "answer_index": answer_index,
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )

    if len(normalized) < max(1, num_questions // 2):
        raise RuntimeError(
            "Quiz generation did not produce enough valid questions. "
            "Please try again or use longer notes."
        )
    return normalized[:num_questions]


@st.cache_data(show_spinner=False)
def generate_flashcards(
    context: str,
    weak_topics: Optional[List[str]] = None,
    model_name: str = DEFAULT_MODEL,
    count: int = 6,
    api_key: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Generate revision flashcards in JSON format with front/back pairs."""
    selected_context = select_context_for_generation(
        context, max_words=MAX_CONTEXT_WORDS_QUIZ
    )

    topic_instruction = ""
    if weak_topics:
        topics_str = ", ".join(weak_topics[:8])
        topic_instruction = f"Prioritize testing these weak topics: {topics_str}"

    prompt = f"""
You are a flashcard creator for active recall learning.

Generate {count} high-impact flashcards.
{topic_instruction}

Return ONLY valid JSON with this schema:
{{
  "flashcards": [
    {{
      "topic": "Topic Name",
      "front": "Clear question, prompt, or term",
      "back": "Concise answer, definition, or key insight (1-3 sentences)"
    }}
  ]
}}

Requirements:
* Front should provoke recall (e.g. 'What is the function of X?', 'Compare A and B').
* Back must be concise, accurate, and easy to memorize.
* Return ONLY valid JSON without extra remarks.

Study Notes:
{selected_context}
"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            raw = _generate(
                model_name,
                prompt,
                temperature=DEFAULT_TEMPERATURE,
                api_key=api_key,
            )
            data = _extract_json(raw)
            cards = data.get("flashcards", [])
            valid_cards = []
            for c in cards:
                if isinstance(c, dict) and c.get("front") and c.get("back"):
                    valid_cards.append(
                        {
                            "topic": str(c.get("topic", "General")).strip(),
                            "front": str(c.get("front", "")).strip(),
                            "back": str(c.get("back", "")).strip(),
                        }
                    )
            if valid_cards:
                return valid_cards
        except Exception:
            if attempt == max_retries - 1:
                return []
    return []


@st.cache_data(show_spinner=False)
def generate_revision_plan(
    context: str,
    weak_topics: List[str],
    model_name: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
) -> str:
    """Generate a 3-5 day targeted revision schedule addressing weak topics."""
    topic_list = (
        ", ".join(sorted(set([t for t in weak_topics if t.strip()])))
        or "key course topics"
    )
    selected_context = select_context_for_generation(
        context, max_words=MAX_CONTEXT_WORDS_SUMMARY
    )
    prompt = f"""
You are a top academic coach and tutor.

The student needs a high-yield revision plan focusing on these weak areas:
{topic_list}

Create a structured 3–5 day step-by-step revision timetable:
- For each day:
  * 🎯 **Daily Focus & Objective**
  * 📖 **Key Topics & Concepts to Review**
  * ✏️ **Actionable Practice Tasks** (active recall, problem solving, self-test)
  * ⏱️ **Estimated Time Commitment**
- Include 1 "Exam Day Strategy" tip at the end.

Study Notes:
{selected_context}

Revision Plan:
"""
    return _generate(
        model_name, prompt, temperature=DEFAULT_TEMPERATURE, api_key=api_key
    )


@st.cache_data(show_spinner=False)
def generate_revision_notes(
    context: str,
    weak_topics: List[str],
    model_name: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
) -> str:
    """Generate condensed review notes and mnemonics for difficult topics."""
    topic_list = (
        ", ".join(sorted(set([t for t in weak_topics if t.strip()])))
        or "fundamental concepts"
    )
    selected_context = select_context_for_generation(
        context, max_words=MAX_CONTEXT_WORDS_SUMMARY
    )
    prompt = f"""
You are an expert tutor writing condensed 'cheat-sheet' revision notes.

Focus especially on: {topic_list}

Produce high-yield revision notes:
1. **Concept Breakdown**: Simple explanation of each core topic.
2. **Mnemonics & Memory Tricks**: Catchy acronyms or analogies.
3. **Common Pitfalls**: What mistakes students often make on these topics.
4. **Quick Checklist**: 3-5 questions the student should test themselves on.

Study Notes:
{selected_context}

Revision Notes:
"""
    return _generate(
        model_name, prompt, temperature=DEFAULT_TEMPERATURE, api_key=api_key
    )


@st.cache_data(show_spinner=False)
def generate_mindmap_markdown(
    context: str,
    model_name: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
) -> str:
    """Generate a Mermaid-compatible mindmap diagram for visualizing concepts."""
    selected_context = select_context_for_generation(context, max_words=2000)
    prompt = f"""
You are an expert in visual knowledge synthesis.

Create a hierarchical concept mindmap using Mermaid markdown syntax (mindmap).

Requirements:
* Output ONLY valid Mermaid mindmap code starting with `mindmap`
* Structure logically: root node -> major topics -> subtopics -> details
* Keep node labels concise (1-4 words)
* Do not include markdown code fences or quotes outside the mermaid block

Example structure:
mindmap
  root((Subject))
    Topic A
      Concept 1
      Concept 2
    Topic B
      Concept 3
      Concept 4

Study Notes:
{selected_context}
"""
    raw = _generate(
        model_name, prompt, temperature=DEFAULT_TEMPERATURE, api_key=api_key
    )
    # Strip any enclosing code fences if model included them
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    return clean
