"""
Tests for Gemini utility functions including JSON parsing and transient error logic.
"""

import pytest
from app.gemini_utils import _extract_json, _is_transient_error


def test_extract_json_valid_object():
    text = 'Here is the JSON: ```json\n{"key": "value"}\n```'
    result = _extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_valid_array():
    text = '[{"item": 1}, {"item": 2}]'
    result = _extract_json(text)
    assert result == [{"item": 1}, {"item": 2}]


def test_extract_json_invalid():
    text = "Not JSON at all"
    with pytest.raises(ValueError):
        _extract_json(text)


def test_extract_json_multiple_fences():
    text = 'Ignore this { ```json\n{"target": "hit"}\n```'
    result = _extract_json(text)
    assert result == {"target": "hit"}


def test_is_transient_error():
    assert _is_transient_error(Exception("Connection timeout")) is True
    assert _is_transient_error(Exception("API_KEY_INVALID")) is False
    assert _is_transient_error(Exception("permission_denied")) is False
