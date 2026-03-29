import json
import re
from typing import Any
import streamlit as st
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, require_api_key

@st.cache_resource
def get_client():
    require_api_key()
    return genai.Client(api_key=API_KEY)

def _extract_json(text: str) -> Any:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    first_obj = text.find("{")
    last_obj = text.rfind("}")
    first_arr = text.find("[")
    last_arr = text.rfind("]")

    candidates = []
    if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
        candidates.append(text[first_obj:last_obj + 1])
    if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
        candidates.append(text[first_arr:last_arr + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Model did not return valid JSON.")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _generate(model_name: str, prompt: str, temperature: float = DEFAULT_TEMPERATURE) -> str:
    client = get_client()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=2048,
            )
        )
    except Exception as e:
        raise RuntimeError(f"Generation failed: {str(e)}")

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()
