import re
import hashlib
from functools import lru_cache
from typing import List

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "could", "did", "do", "does", "doing", "for", "from", "had", "has", "have",
    "he", "her", "hers", "him", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "just", "me", "more", "most", "my", "no", "not", "of", "on",
    "or", "our", "out", "over", "she", "so", "some", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "to", "too",
    "us", "was", "we", "were", "what", "when", "where", "which", "who",
    "why", "with", "would", "you", "your"
}

def clean_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

@lru_cache(maxsize=4)
def chunk_text_cached(text_hash: str, text: str, max_words: int = 900) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    for start in range(0, len(words), max_words):
        chunk = " ".join(words[start:start + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def chunk_text(text: str, max_words: int = 900) -> List[str]:
    """Helper for chunking to avoid changing existing calls."""
    return get_chunks(text, max_words)

def get_chunks(text: str, max_words: int = 900) -> List[str]:
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return chunk_text_cached(text_hash, text, max_words)

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]+", text) if w.lower() not in STOPWORDS]

def rank_chunks(query: str, chunks: List[str], top_k: int = 4) -> List[str]:
    """Return the top_k chunks most relevant to the query using keyword overlap."""
    if not chunks:
        return []

    query_tokens = set(tokenize(query))
    if not query_tokens:
        return chunks[:top_k]

    scored = []
    for chunk in chunks:
        tokens = tokenize(chunk)
        if not tokens:
            score = 0
        else:
            overlap = len(query_tokens.intersection(tokens))
            score = overlap / max(1, len(query_tokens))
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [chunk for score, chunk in scored[:top_k] if score > 0]
    if not selected:
        selected = chunks[:top_k]
    return selected

def split_notes_for_display(text: str, max_chars: int = 3500) -> str:
    text = clean_text(text)
    return text[:max_chars] + ("\n\n..." if len(text) > max_chars else "")
