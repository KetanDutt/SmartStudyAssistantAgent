"""
Tests for state handlers and user score management.
"""

from app.handlers import add_score, record_weak_topics, shuffle_quiz_items
import streamlit as st


def test_shuffle_quiz_items():
    items = [
        {
            "id": 1,
            "topic": "Math",
            "question": "What is 2+2?",
            "options": ["1", "2", "3", "4"],
            "answer_index": 3,
        }
    ]
    shuffled = shuffle_quiz_items(items)
    assert len(shuffled) == 1
    # Check that the option at new answer_index still equals '4'
    new_idx = shuffled[0]["answer_index"]
    assert shuffled[0]["options"][new_idx] == "4"


def test_record_weak_topics():
    st.session_state.weak_topics = []
    items = [
        {"topic": "Physics", "answer_index": 0},
        {"topic": "Chemistry", "answer_index": 2},
    ]
    # User answered index 1 (wrong) for Q1, and index 2 (correct) for Q2
    selected = [1, 2]
    record_weak_topics(items, selected)
    assert "Physics" in st.session_state.weak_topics
    assert "Chemistry" not in st.session_state.weak_topics


def test_add_score():
    st.session_state.score_history = []
    add_score(80, "Quiz", correct=4, total=5)
    assert len(st.session_state.score_history) == 1
    record = st.session_state.score_history[0]
    assert record["score_percent"] == 80
    assert record["type"] == "Quiz"
    assert record["correct"] == 4
    assert record["total"] == 5
