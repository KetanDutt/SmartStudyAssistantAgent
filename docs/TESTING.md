# Testing and Quality Assurance Guide

This document describes the testing strategy, test suites, and linting procedures for the Smart Study Assistant Agent.

---

## 1. Test Suite Structure

All unit and integration tests reside in the `tests/` directory:

| Test File | Description |
|---|---|
| `test_config.py` | Validates API key resolution, fallback mechanisms, and Gemini model filtering. |
| `test_features.py` | Tests AI feature generation (quiz validation, flashcards, insufficient output handling). |
| `test_gemini_utils.py` | Tests resilient JSON extraction, markdown fence handling, and transient error detection. |
| `test_handlers.py` | Tests quiz option shuffling, weak topic recording, and score logging. |
| `test_text_processing.py` | Tests text normalization, overlapping chunking, tokenization, and ranking. |

---

## 2. Running Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

Run tests with coverage (if `pytest-cov` is installed):
```bash
pytest --cov=app tests/
```

---

## 3. Code Quality & Formatting

The codebase enforces PEP 8 compliance and code formatting standards:

### Code Formatting with Black
```bash
black --line-length 88 app tests app.py
```

### Static Analysis with Flake8
```bash
flake8 --max-line-length=88 --extend-ignore=E203,W503 app tests
```

---

## 4. Continuous Integration Checklist

Before pushing code or creating pull requests, ensure:
1. `pytest` passes with 100% green tests.
2. `flake8` returns 0 linting warnings or errors.
3. No sensitive files or API keys are committed in `.env`.
