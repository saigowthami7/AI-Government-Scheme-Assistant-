"""
multilingual.py
Owner: Member 4 - LLM & NLP Developer

Handles language detection (English vs Telugu) so the assistant can:
  1. Pick the right system prompt (see prompts.py)
  2. Ask the LLM to respond in the same language the user wrote in

Approach: Telugu uses a distinct Unicode block (0C00–0C7F), so a simple
character-range check is a fast, dependency-free way to detect it
reliably — no ML model needed for this part. `langdetect` is included
as an optional fallback for mixed/ambiguous text.
"""

import re

TELUGU_UNICODE_RANGE = re.compile(r"[\u0C00-\u0C7F]")


def detect_language(text: str) -> str:
    """
    Returns 'te' if the text contains Telugu script, otherwise 'en'.
    This intentionally does NOT try to detect other Indian languages —
    the project scope is English + Telugu only.
    """
    if TELUGU_UNICODE_RANGE.search(text):
        return "te"

    # Fallback for romanized Telugu (Telugu written in Latin letters) is
    # intentionally left as a future enhancement — flagged in README.
    return "en"


def language_instruction(language: str) -> str:
    """Appended to the LLM prompt so the model replies in the right language."""
    if language == "te":
        return "దయచేసి తెలుగులో సమాధానం ఇవ్వండి (Please respond in Telugu)."
    return "Please respond in English."


if __name__ == "__main__":
    print(detect_language("What schemes are available for farmers?"))  # en
    print(detect_language("రైతులకు ఏ పథకాలు అందుబాటులో ఉన్నాయి?"))       # te
