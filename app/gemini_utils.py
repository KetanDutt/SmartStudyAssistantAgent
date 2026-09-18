"""
Google Gemini API integration utilities.
Provides cached client generation, retry logic with exponential backoff,
robust JSON extraction, and content generation helpers.
"""

import json
import re
from typing import Any, Optional
from google import genai
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import (
    DEFAULT_TEMPERATURE,
    get_api_key,
    require_api_key,
)


def get_client(api_key: Optional[str] = None) -> genai.Client:
    """Instantiate a Gemini API client using the active API key."""
    key = api_key or require_api_key()
    return genai.Client(api_key=key)


def _extract_json(text: str) -> Any:
    """Extract and parse a JSON object or array from LLM responses."""
    text = text.strip()
    fenced = re.search(
        r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE
    )
    if fenced:
        text = fenced.group(1).strip()

    # Direct parsing attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract bracketed object or array
    first_obj = text.find("{")
    last_obj = text.rfind("}")
    first_arr = text.find("[")
    last_arr = text.rfind("]")

    candidates = []
    if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
        candidates.append(text[first_obj : last_obj + 1])
    if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
        candidates.append(text[first_arr : last_arr + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Model did not return valid JSON. Output snippet: {text[:200]}")


def _is_transient_error(exception: Exception) -> bool:
    """Check if exception is transient and worthy of a retry."""
    err_msg = str(exception).lower()
    permanent_patterns = [
        "api key not valid",
        "api_key_invalid",
        "invalid_argument",
        "permission_denied",
        "not found",
    ]
    if any(pat in err_msg for pat in permanent_patterns):
        return False
    return True


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(_is_transient_error),
    reraise=True,
)
def _generate(
    model_name: str,
    prompt: str,
    temperature: float = DEFAULT_TEMPERATURE,
    api_key: Optional[str] = None,
) -> str:
    """Call Gemini to generate text with error handling and retry mechanism."""
    client = get_client(api_key=api_key or get_api_key())
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Generation failed: {str(e)}")

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()
