import pytest
from app.features import generate_quiz

def test_generate_quiz_insufficient_output(monkeypatch):
    import app.features

    def fake_generate(*args, **kwargs):
        return '{"items": [{"id": 1, "topic": "test", "question": "Q?", "options": ["a", "b", "c", "d"], "answer_index": 0}]}'

    monkeypatch.setattr(app.features, "_generate", fake_generate)

    with pytest.raises(RuntimeError, match="Quiz generation did not return enough valid questions."):
        generate_quiz("some context", num_questions=5)

def test_generate_quiz_success(monkeypatch):
    import app.features

    def fake_generate(*args, **kwargs):
        return '''{
          "items": [
            {"id": 1, "topic": "test1", "question": "Q1", "options": ["a", "b", "c", "d"], "answer_index": 0},
            {"id": 2, "topic": "test2", "question": "Q2", "options": ["a", "b", "c", "d"], "answer_index": 1}
          ]
        }'''

    monkeypatch.setattr(app.features, "_generate", fake_generate)

    quiz = generate_quiz("some context", num_questions=2)
    assert len(quiz) == 2
    assert quiz[0]["topic"] == "test1"
