import pytest
from app.text_processing import clean_text, chunk_text, rank_chunks, tokenize

def test_clean_text():
    raw_text = "This   is \r some \n\n\n\n text."
    expected = "This is \n some \n\n text."
    assert clean_text(raw_text) == expected

def test_chunk_text():
    text = "word " * 100
    chunks = chunk_text(text, max_words=30)
    assert len(chunks) == 4
    assert len(chunks[0].split()) == 30
    assert len(chunks[3].split()) == 10

def test_tokenize():
    text = "The quick brown fox."
    tokens = tokenize(text)
    assert "the" not in tokens
    assert "quick" in tokens
    assert "brown" in tokens
    assert "fox" in tokens

def test_rank_chunks():
    chunks = [
        "Photosynthesis is a process used by plants.",
        "Gravity is a force that attracts a body toward the center of the earth.",
        "Plants need sunlight for photosynthesis."
    ]
    query = "How do plants use photosynthesis?"
    ranked = rank_chunks(query, chunks, top_k=2)
    assert len(ranked) == 2
    assert "Photosynthesis is a process used by plants." in ranked
    assert "Plants need sunlight for photosynthesis." in ranked
