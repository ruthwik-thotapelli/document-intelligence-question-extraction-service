"""
Extraction Service
==================
Uses Google Gemini 1.5 Flash (vision model) to extract structured questions
from uploaded PDF and image files.

Design decisions:
- Gemini 1.5 Flash handles both native PDFs and images natively via the File API.
- A structured JSON prompt is used so the model outputs machine-readable data.
- Confidence is derived from the model's own uncertainty signals and the
  completeness of extracted fields.
- If GEMINI_API_KEY is not set, a mock extraction is returned for development/testing.
"""

import json
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Extraction result schema ────────────────────────────────────────────────


def _empty_result() -> list[dict[str, Any]]:
    return []


EXTRACTION_PROMPT = """
You are an expert at extracting questions from examination documents.

Analyse the provided document and extract ALL questions you can find.
For EACH question, return a JSON object with EXACTLY these fields:
- "question_number": string or null (e.g. "1", "Q2", "i", null if not visible)
- "text": string — the full question text
- "question_type": one of "mcq", "short_answer", "long_answer", "true_false", "fill_blank", "unknown"
- "options": list of strings (e.g. ["A. Paris", "B. London"]) or null if not applicable
- "answer": string or null — only if an answer key is present in this document
- "source_pages": list of integers — page numbers (1-indexed) where this question appears
- "has_image": boolean — true if the question references a diagram or figure
- "confidence": float between 0.0 and 1.0 — your confidence in the extraction quality
  Use 0.9–1.0 for clean, clearly formatted questions.
  Use 0.6–0.89 for questions that needed inference (e.g. OCR artefacts, split across pages).
  Use 0.0–0.59 for very uncertain or partial extractions.
- "review_notes": string or null — any issues you encountered (OCR noise, truncation, etc.)

Return ONLY a valid JSON array containing these objects. No other text, no markdown fences.
If no questions are found, return an empty array: []
"""


def extract_questions(file_path: str) -> list[dict[str, Any]]:
    """
    Main extraction entry point.
    Falls back to mock extraction if GEMINI_API_KEY is not configured.
    """
    from app.core.config import settings

    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — using mock extraction for development.")
        return _mock_extraction(file_path)

    try:
        return _gemini_extraction(file_path, settings.GEMINI_API_KEY)
    except Exception as exc:
        logger.error(f"Gemini extraction failed: {exc}", exc_info=True)
        raise RuntimeError(f"AI extraction error: {exc}") from exc


def _gemini_extraction(file_path: str, api_key: str) -> list[dict[str, Any]]:
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        suffix = path.suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        mime_type = mime_map.get(suffix, "application/octet-stream")

    logger.info(f"Uploading {path.name} ({mime_type}) to Gemini File API…")
    uploaded_file = genai.upload_file(path=str(path), mime_type=mime_type)
    logger.info(f"File uploaded: {uploaded_file.name}")

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        [uploaded_file, EXTRACTION_PROMPT],
        generation_config=genai.GenerationConfig(
            temperature=0.1,  # low temperature → deterministic, structured output
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()
    logger.debug(f"Raw Gemini response (first 500 chars): {raw_text[:500]}")

    questions = _parse_json_response(raw_text)
    logger.info(f"Extracted {len(questions)} questions from {path.name}")
    return questions


def _parse_json_response(raw: str) -> list[dict[str, Any]]:
    """Robustly parse JSON even if the model adds minor formatting."""
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}\nRaw: {raw[:300]}")
        return []


def _mock_extraction(file_path: str) -> list[dict[str, Any]]:
    """
    Returns realistic mock data when no API key is available.
    Used for local development and CI testing.
    """
    logger.info(f"Mock extraction for: {file_path}")
    return [
        {
            "question_number": "1",
            "text": "What is the capital of France?",
            "question_type": "mcq",
            "options": ["A. Berlin", "B. Madrid", "C. Paris", "D. Rome"],
            "answer": "C",
            "source_pages": [1],
            "has_image": False,
            "confidence": 0.95,
            "review_notes": None,
        },
        {
            "question_number": "2",
            "text": "Explain the significance of the Turing Test in the context of artificial intelligence.",
            "question_type": "long_answer",
            "options": None,
            "answer": None,
            "source_pages": [1, 2],
            "has_image": False,
            "confidence": 0.80,
            "review_notes": "Question spans two pages; continuation inferred from context.",
        },
        {
            "question_number": "3",
            "text": "The speed of light in vacuum is approximately _____ m/s.",
            "question_type": "fill_blank",
            "options": None,
            "answer": "3 × 10^8",
            "source_pages": [2],
            "has_image": False,
            "confidence": 0.88,
            "review_notes": None,
        },
        {
            "question_number": None,
            "text": "[Partial text — OCR noise detected] The process of ph__synthesis converts CO2 and H2O into…",
            "question_type": "unknown",
            "options": None,
            "answer": None,
            "source_pages": [3],
            "has_image": True,
            "confidence": 0.42,
            "review_notes": "OCR artefacts detected. Question number missing. Manual review recommended.",
        },
    ]
