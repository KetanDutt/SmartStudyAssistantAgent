"""
PDF processing utilities.
Extracts clean plain text from uploaded PDF documents with caching.
"""

import hashlib
import io
import streamlit as st
from pypdf import PdfReader
from app.text_processing import clean_text


@st.cache_data(show_spinner=False)
def _extract_text_cached(file_hash: str, file_bytes: bytes) -> str:
    """Read all pages of a PDF and clean the extracted text."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for idx, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())
        except Exception as e:
            print(f"Warning: could not extract text from page {idx}: {e}")

    extracted = "\n\n".join(pages)
    return clean_text(extracted)


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract clean text from an uploaded Streamlit file object."""
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    return _extract_text_cached(file_hash, file_bytes)
