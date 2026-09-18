"""
Tests for AI feature generation (quiz, flashcards, tutor).
"""

import pytest
from app.features import generate_quiz, generate_flashcards


def test_generate_quiz_insufficient_output(monkeypatch):
    import app.features

    def fake_generate(*args, **kwargs):
        return (
            '{"items": [{"id": 1, "topic": "test", "question": "Q?", '
            '"options": ["a", "b", "c", "d"], "answer_index": 0}]}'
        )

    monkeypatch.setattr(app.features, "_generate", fake_generate)

    with pytest.raises(
        RuntimeError, match="Quiz generation did not produce enough valid questions"
    ):
        generate_quiz("some context", num_questions=5, api_key="fake")


def test_generate_quiz_success(monkeypatch):
    import app.features

    raw_json = (
        "{\n"
        '  "items": [\n'
        '    {"id": 1, "topic": "t1", "question": "Q1", '
        '"options": ["a", "b", "c", "d"], "answer_index": 0},\n'
        '    {"id": 2, "topic": "t2", "question": "Q2", '
        '"options": ["a", "b", "c", "d"], "answer_index": 1}\n'
        "  ]\n"
        "}"
    )

    def fake_generate(*args, **kwargs):
        return raw_json

    monkeypatch.setattr(app.features, "_generate", fake_generate)

    quiz = generate_quiz("some context", num_questions=2, api_key="fake")
    assert len(quiz) == 2
    assert quiz[0]["topic"] == "t1"


def test_generate_flashcards_success(monkeypatch):
    import app.features

    raw_cards = (
        '{"flashcards": [{"topic": "Bio", "front": "Q?", "back": "A."}]}'
    )

    def fake_generate(*args, **kwargs):
        return raw_cards

    monkeypatch.setattr(app.features, "_generate", fake_generate)

    cards = generate_flashcards("context", ["Bio"], count=1, api_key="fake")
    assert len(cards) == 1
    assert cards[0]["topic"] == "Bio"
    assert cards[0]["front"] == "Q?"
