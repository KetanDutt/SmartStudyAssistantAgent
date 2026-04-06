import pytest
from app.text_processing import clean_text, chunk_text, rank_chunks, tokenize, split_notes_for_display

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

def test_split_notes_for_display():
    # Scenario 1: Text shorter than max_chars
    text = "Hello world"
    assert split_notes_for_display(text, max_chars=20) == "Hello world"

    # Scenario 2: Text exactly max_chars long
    text = "A" * 10
    assert split_notes_for_display(text, max_chars=10) == "A" * 10

    # Scenario 3: Text longer than max_chars, with word boundary
    # "AAAAA BBBBBBBBBB" (Total 16 chars)
    # max_chars = 10, ellipsis length = 5, limit = 5
    # text[:5] is "AAAAA". No space.
    text = "AAAAA BBBBBBBBBB"
    result = split_notes_for_display(text, max_chars=10)
    assert result == "AAAAA\n\n..."
    assert len(result) <= 10

    # Scenario 3b: Text longer than max_chars, with space within limit
    # "ABC DEFGHI" (Total 10 chars)
    # max_chars = 9, ellipsis length = 5, limit = 4
    # text[:4] is "ABC ". space at index 3.
    # result "ABC" + "\n\n..." -> length 8
    text = "ABC DEFGHI"
    result = split_notes_for_display(text, max_chars=9)
    assert result == "ABC\n\n..."
    assert len(result) <= 9

    # Scenario 4: Text longer than max_chars, no word boundary
    text = "ABCDEFGHIJKL" # 12 chars
    # limit = 10 - 5 = 5
    # No space in "ABCDE", returns "ABCDE\n\n..." (total 10 chars)
    result = split_notes_for_display(text, max_chars=10)
    assert result == "ABCDE\n\n..."
    assert len(result) <= 10

    # Scenario 5: Empty string
    assert split_notes_for_display("", max_chars=10) == ""

    # Scenario 6: Cleaning integration
    text = "  A    B    C  "
    # clean_text -> "A B C" (5 chars)
    assert split_notes_for_display(text, max_chars=10) == "A B C"
    # Cleaned length is 5, if max_chars is 4, ellipsis is 5, limit is -1.
    # Returns text[:4] -> "A B "
    result = split_notes_for_display(text, max_chars=4)
    assert result == "A B "
    assert len(result) <= 4

    # Scenario 7: max_chars very small (less than ellipsis)
    text = "Something long"
    # limit = 2 - 5 = -3. Should return text[:2] -> "So"
    assert split_notes_for_display(text, max_chars=2) == "So"
