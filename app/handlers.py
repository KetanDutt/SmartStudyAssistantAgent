"""
User data handling and state management for Smart Study Assistant Agent.
Supports local JSON storage, weak topic tracking, and study progress logs.
"""

from copy import deepcopy
from datetime import datetime
import json
import os
import random
from typing import Any, Dict, List
import streamlit as st

DATA_FILE = "user_data.json"


def load_user_data() -> Dict[str, Any]:
    """Load user data from local file safely."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "weak_topics": data.get("weak_topics", []),
                    "score_history": data.get("score_history", []),
                }
        except Exception as err:
            print(f"Warning: Failed to load user data: {err}")
    return {"weak_topics": [], "score_history": []}


def save_user_data(data: Dict[str, Any]) -> None:
    """Save user data to local file safely."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as err:
        print(f"Warning: Failed to save user data: {err}")


def ensure_state() -> None:
    """Initialize session state variables with sensible defaults."""
    user_data = load_user_data()
    defaults = {
        "context_text": "",
        "source_name": "",
        "user_api_key": "",
        "quiz_items": [],
        "exam_items": [],
        "weak_topics": user_data.get("weak_topics", []),
        "score_history": user_data.get("score_history", []),
        "quiz_result": None,
        "exam_result": None,
        "summary_text": "",
        "revision_text": "",
        "revision_plan": "",
        "flashcards": [],
        "chat_history": [],
        "flashcard_idx": 0,
        "flashcard_flipped": False,
        "flashcard_mastered": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def update_user_data() -> None:
    """Persist current session weak topics and scores to storage."""
    data = {
        "weak_topics": st.session_state.get("weak_topics", []),
        "score_history": st.session_state.get("score_history", []),
    }
    save_user_data(data)


def shuffle_quiz_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Shuffle multiple-choice answer options while updating answer_index."""
    shuffled_items = []
    for item in items:
        new_item = deepcopy(item)
        options = new_item.get("options", [])
        answer_index = new_item.get("answer_index", 0)

        if not options or len(options) != 4:
            shuffled_items.append(new_item)
            continue

        indexed_options = list(enumerate(options))
        random.shuffle(indexed_options)

        shuffled_options = []
        new_answer_index = 0
        for new_idx, (original_idx, opt) in enumerate(indexed_options):
            shuffled_options.append(opt)
            if original_idx == answer_index:
                new_answer_index = new_idx

        new_item["options"] = shuffled_options
        new_item["answer_index"] = new_answer_index
        shuffled_items.append(new_item)
    return shuffled_items


def record_weak_topics(
    items: List[Dict[str, Any]], selected_answers: List[int]
) -> None:
    """Record missed topics from a quiz or exam into weak topics list."""
    updated = False
    for item, selected in zip(items, selected_answers):
        correct = item.get("answer_index")
        topic = item.get("topic", "General").strip()
        if correct is not None and selected != correct:
            if topic and topic not in st.session_state.weak_topics:
                st.session_state.weak_topics.append(topic)
                updated = True
    if updated:
        update_user_data()


def add_score(
    score_percent: int, type_str: str, correct: int = 0, total: int = 0
) -> None:
    """Append a quiz/exam score record with timestamp to history."""
    if "score_history" not in st.session_state:
        st.session_state.score_history = []
    st.session_state.score_history.append(
        {
            "date": datetime.now().isoformat(timespec="seconds"),
            "score_percent": score_percent,
            "type": type_str,
            "correct": correct,
            "total": total,
        }
    )
    update_user_data()
