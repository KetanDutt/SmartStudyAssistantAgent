"""
Configuration module for the Smart Study Assistant Agent.
Handles environment variables, API key resolution, and model retrieval.
"""

import os
from typing import List, Optional
import streamlit as st
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")

MAX_CONTEXT_WORDS_QA = 2600
MAX_CONTEXT_WORDS_SUMMARY = 3000
MAX_CONTEXT_WORDS_QUIZ = 2000
DEFAULT_TEMPERATURE = 0.2
QUIZ_TEMPERATURE = 0.3


def get_api_key() -> Optional[str]:
    """Retrieve API key from session state, environment, or Streamlit secrets."""
    # Check session state first (user-entered key via UI)
    if "user_api_key" in st.session_state and st.session_state.user_api_key:
        return st.session_state.user_api_key.strip()

    # Check environment variables
    env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key.strip()

    # Check Streamlit secrets if present
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return None


def require_api_key() -> str:
    """Ensure an API key is present or raise RuntimeError."""
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Add it to your .env file, "
            "set it in the sidebar, or configure an environment variable."
        )
    return key


def validate_api_key(api_key: Optional[str] = None) -> bool:
    """Validate whether an API key is provided and functional."""
    key = api_key or get_api_key()
    if not key:
        return False
    try:
        from google import genai

        client = genai.Client(api_key=key)
        # Test by fetching the first model item
        next(client.models.list())
        return True
    except Exception as e:
        print(f"API key validation failed: {e}")
        return False


@st.cache_data(ttl=3600, show_spinner=False)
def get_available_models(api_key: Optional[str] = None) -> List[str]:
    """Return a list of available Gemini text models supporting generateContent."""
    key = api_key or get_api_key()
    if not key:
        return []
    try:
        from google import genai

        client = genai.Client(api_key=key)
        models = []
        for m in client.models.list():
            actions = getattr(m, "supported_generation_methods", []) or getattr(
                m, "supported_actions", []
            )
            if "generateContent" in actions:
                name = m.name
                if name.startswith("models/"):
                    name = name[len("models/") :]

                name_lower = name.lower()
                exclusions = [
                    "embedding",
                    "aqa",
                    "vision",
                    "tts",
                    "image",
                    "clip",
                    "robotics",
                    "computer-use",
                    "lyria",
                    "nano-banana",
                ]
                if any(ex in name_lower for ex in exclusions):
                    continue

                models.append(name)
        return sorted(models)
    except Exception as e:
        print(f"Failed to fetch models: {e}")
        return []
