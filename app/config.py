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

_api_key_valid = None

def validate_api_key() -> bool:
    global _api_key_valid
    if _api_key_valid is not None:
        return _api_key_valid

    if not API_KEY:
        _api_key_valid = False
        return False
    try:
        from google import genai
        client = genai.Client(api_key=API_KEY)
        client.models.generate_content(
            model=DEFAULT_MODEL,
            contents="test"
        )
        _api_key_valid = True
        return True
    except Exception as e:
        _api_key_valid = False
        return False
