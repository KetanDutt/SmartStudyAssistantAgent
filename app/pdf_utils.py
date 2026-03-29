from pypdf import PdfReader
from app.text_processing import clean_text

def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return clean_text("\n".join(pages))
