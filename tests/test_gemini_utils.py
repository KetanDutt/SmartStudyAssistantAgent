import pytest
from app.gemini_utils import _extract_json

def test_extract_json_valid_object():
    text = "Here is the JSON: ```json\n{\"key\": \"value\"}\n```"
    result = _extract_json(text)
    assert result == {"key": "value"}

def test_extract_json_valid_array():
    text = "[{\"item\": 1}, {\"item\": 2}]"
    result = _extract_json(text)
    assert result == [{"item": 1}, {"item": 2}]

def test_extract_json_invalid():
    text = "Not JSON at all"
    with pytest.raises(ValueError):
        _extract_json(text)

def test_extract_json_multiple_fences():
    text = "Ignore this { ```json\n{\"target\": \"hit\"}\n```"
    result = _extract_json(text)
    assert result == {"target": "hit"}
