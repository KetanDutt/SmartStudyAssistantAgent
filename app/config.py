import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

MAX_CONTEXT_WORDS_QA = 2600
MAX_CONTEXT_WORDS_SUMMARY = 3000
MAX_CONTEXT_WORDS_QUIZ = 2000
DEFAULT_TEMPERATURE = 0.2
QUIZ_TEMPERATURE = 0.3

def require_api_key() -> None:
    if not API_KEY:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Add it to your .env file or set it as an environment variable."
        )

def validate_api_key() -> bool:
    try:
        require_api_key()
        return True
    except RuntimeError:
        return False
