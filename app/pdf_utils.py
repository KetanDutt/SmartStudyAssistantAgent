import hashlib
import streamlit as st
from pypdf import PdfReader
from app.text_processing import clean_text

@st.cache_data(show_spinner=False)
def _extract_text_cached(file_hash: str, file_bytes: bytes) -> str:
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return clean_text("\n".join(pages))

def extract_text_from_pdf(uploaded_file) -> str:
    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    return _extract_text_cached(file_hash, file_bytes)
