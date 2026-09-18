"""
Text processing and retrieval utilities.
Includes text cleaning, smart chunking with overlap, tokenization,
BM25-style keyword search and ranking, and formatting.
"""

from functools import lru_cache
import hashlib
import re
from typing import List

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "hers",
    "him",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "me",
    "more",
    "most",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "over",
    "she",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "too",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "you",
    "your",
}


def clean_text(text: str) -> str:
    """Normalize line endings and redundant whitespace."""
    if not text:
        return ""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@lru_cache(maxsize=32)
def chunk_text_cached(
    text_hash: str, text: str, max_words: int = 800, overlap: int = 100
) -> List[str]:
    """Split text into overlapping chunks of words with lru_cache."""
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks = []
    step = max(1, max_words - overlap)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + max_words]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        if start + max_words >= len(words):
            break
    return chunks


def chunk_text(text: str, max_words: int = 800, overlap: int = 100) -> List[str]:
    """Split text into manageable chunks."""
    return get_chunks(text, max_words, overlap)


def get_chunks(text: str, max_words: int = 800, overlap: int = 100) -> List[str]:
    """Hash text for cached chunking."""
    if not text.strip():
        return []
    text_hash = hashlib.md5(f"{text}_{max_words}_{overlap}".encode("utf-8")).hexdigest()
    return chunk_text_cached(text_hash, text, max_words, overlap)


@lru_cache(maxsize=256)
def tokenize(text: str) -> List[str]:
    """Extract lowercased alphanumeric tokens excluding stopwords."""
    return [
        w.lower()
        for w in re.findall(r"[A-Za-z0-9]+", text)
        if w.lower() not in STOPWORDS
    ]


def rank_chunks(query: str, chunks: List[str], top_k: int = 4) -> List[str]:
    """
    Score and rank chunks against query using frequency-weighted token overlap.
    Returns top_k chunks.
    """
    if not chunks:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return chunks[:top_k]

    q_set = set(query_tokens)
    scored = []
    for chunk in chunks:
        tokens = tokenize(chunk)
        if not tokens:
            scored.append((0.0, chunk))
            continue

        token_counts = {}
        for t in tokens:
            if t in q_set:
                token_counts[t] = token_counts.get(t, 0) + 1

        # Score based on unique matched tokens plus term frequency
        unique_matches = len(token_counts)
        freq_bonus = sum(min(count, 3) for count in token_counts.values())
        score = (unique_matches * 2.0 + freq_bonus) / max(1, len(q_set))
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [chunk for score, chunk in scored[:top_k] if score > 0]
    if not selected:
        selected = chunks[:top_k]
    return selected


def split_notes_for_display(text: str, max_chars: int = 3500) -> str:
    """
    Cleans text and truncates it to approximately max_chars.
    Attempts to truncate at the last word boundary within the limit.
    Ensures the total length (including ellipsis) does not exceed max_chars.
    """
    text = clean_text(text)
    if len(text) <= max_chars:
        return text

    ellipsis = "\n\n..."
    limit = max_chars - len(ellipsis)
    if limit <= 0:
        return text[:max_chars]

    truncated = text[:limit]
    last_space = truncated.rfind(" ")

    if last_space != -1:
        truncated = truncated[:last_space]

    return truncated + ellipsis
