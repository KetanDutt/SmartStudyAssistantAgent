import json
import re
from typing import Any
import streamlit as st
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, require_api_key

if API_KEY:
    genai.configure(api_key=API_KEY)

@st.cache_resource
def get_model(model_name: str = DEFAULT_MODEL):
    require_api_key()
    return genai.GenerativeModel(model_name)

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
    model = get_model(model_name)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": 2048,
        },
    )

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        raise RuntimeError(f"Prompt blocked: {response.prompt_feedback.block_reason}")

    if not response.candidates:
        raise RuntimeError("No response candidates returned by Gemini.")

    candidate = response.candidates[0]
    if candidate.finish_reason != 1:  # 1 = STOP
        raise RuntimeError(f"Generation stopped due to: {candidate.finish_reason}")

    text = candidate.content.parts[0].text if candidate.content.parts else ""
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text.strip()
