import json
import os
import random
import streamlit as st
from datetime import datetime
from copy import deepcopy

DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return {
                    "weak_topics": data.get("weak_topics", []),
                    "score_history": data.get("score_history", [])
                }
        except Exception:
            pass
    return {"weak_topics": [], "score_history": []}

def save_user_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def ensure_state():
    user_data = load_user_data()
    defaults = {
        "context_text": "",
        "source_name": "",
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def update_user_data():
    data = {
        "weak_topics": st.session_state.get("weak_topics", []),
        "score_history": st.session_state.get("score_history", [])
    }
    save_user_data(data)

def shuffle_quiz_items(items):
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

def record_weak_topics(items, selected_answers):
    updated = False
    for item, selected in zip(items, selected_answers):
        correct = item.get("answer_index")
        topic = item.get("topic", "General")
        if correct is not None and selected != correct:
            if topic and topic not in st.session_state.weak_topics:
                st.session_state.weak_topics.append(topic)
                updated = True
    if updated:
        update_user_data()

def add_score(score_percent, type_str):
    if "score_history" not in st.session_state:
        st.session_state.score_history = []
    st.session_state.score_history.append({
        "date": datetime.now().isoformat(),
        "score_percent": score_percent,
        "type": type_str
    })
    update_user_data()
