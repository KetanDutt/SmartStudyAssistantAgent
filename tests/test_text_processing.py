"""
Tests for text processing algorithms: clean, chunk, rank, tokenize.
"""

from app.text_processing import (
    clean_text,
    chunk_text,
    rank_chunks,
    tokenize,
    split_notes_for_display,
)


def test_clean_text():
    raw_text = "This   is \r some \n\n\n\n text."
    expected = "This is \n some \n\n text."
    assert clean_text(raw_text) == expected


def test_chunk_text():
    text = "word " * 100
    # Overlap defaults to 10. If max_words=30, step=20:
    # chunk 0: 0-30
    # chunk 1: 20-50
    # chunk 2: 40-70
    # chunk 3: 60-90
    # chunk 4: 80-100
    chunks = chunk_text(text, max_words=30, overlap=10)
    assert len(chunks) == 5
    assert len(chunks[0].split()) == 30
    assert len(chunks[-1].split()) == 20


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
        "Plants need sunlight for photosynthesis.",
    ]
    query = "How do plants use photosynthesis?"
    ranked = rank_chunks(query, chunks, top_k=2)
    assert len(ranked) == 2
    assert "Photosynthesis is a process used by plants." in ranked
    assert "Plants need sunlight for photosynthesis." in ranked


def test_split_notes_for_display():
    text = "Hello world"
    assert split_notes_for_display(text, max_chars=20) == "Hello world"

    text = "A" * 10
    assert split_notes_for_display(text, max_chars=10) == "A" * 10

    text = "AAAAA BBBBBBBBBB"
    result = split_notes_for_display(text, max_chars=10)
    assert result == "AAAAA\n\n..."
    assert len(result) <= 10

    text = "ABC DEFGHI"
    result = split_notes_for_display(text, max_chars=9)
    assert result == "ABC\n\n..."
    assert len(result) <= 9

    text = "ABCDEFGHIJKL"
    result = split_notes_for_display(text, max_chars=10)
    assert result == "ABCDE\n\n..."
    assert len(result) <= 10

    assert split_notes_for_display("", max_chars=10) == ""

    text = "  A    B    C  "
    result = split_notes_for_display(text, max_chars=4)
    assert result == "A B "
    assert len(result) <= 4

    text = "Something long"
    assert split_notes_for_display(text, max_chars=2) == "So"
