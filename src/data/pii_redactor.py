"""PII redaction using Presidio NER and deterministic regex patterns.

Strips emails, phone numbers, URLs, and person names from text,
replacing them with bracketed placeholders.
"""

import re

from loguru import logger
from presidio_analyzer import AnalyzerEngine, RecognizerResult

# Pre-compiled regex patterns for deterministic PII detection
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_PHONE_PATTERN = re.compile(
    r"(?<!\d)(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}(?!\d)"
)
_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+")

# Placeholder tokens (must match these exactly for idempotency)
_PLACEHOLDERS = {"[EMAIL]", "[PHONE]", "[URL]", "[NAME]"}

_analyzer: AnalyzerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    """Lazily initialize and return the Presidio analyzer engine."""
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
        logger.debug("Presidio AnalyzerEngine initialized")
    return _analyzer


def _redact_with_regex(text: str) -> tuple[str, dict[str, int]]:
    """Apply deterministic regex-based redaction for emails, phones, and URLs.

    Args:
        text: Input text to redact.

    Returns:
        Tuple of (redacted text, counts dict).
    """
    counts: dict[str, int] = {"email": 0, "phone": 0, "url": 0}

    # URLs first (they may contain email-like patterns)
    urls = _URL_PATTERN.findall(text)
    counts["url"] = len(urls)
    text = _URL_PATTERN.sub("[URL]", text)

    # Emails
    emails = _EMAIL_PATTERN.findall(text)
    counts["email"] = len(emails)
    text = _EMAIL_PATTERN.sub("[EMAIL]", text)

    # Phones
    phones = _PHONE_PATTERN.findall(text)
    counts["phone"] = len(phones)
    text = _PHONE_PATTERN.sub("[PHONE]", text)

    return text, counts


def _redact_names_with_presidio(text: str) -> tuple[str, int]:
    """Use Presidio NER to detect and redact person names.

    Args:
        text: Input text (already regex-redacted).

    Returns:
        Tuple of (redacted text, count of names found).
    """
    analyzer = _get_analyzer()
    results: list[RecognizerResult] = analyzer.analyze(
        text=text,
        entities=["PERSON"],
        language="en",
    )

    if not results:
        return text, 0

    # Sort by start position descending so replacements don't shift indices
    results.sort(key=lambda r: r.start, reverse=True)

    name_count = 0
    for result in results:
        detected = text[result.start : result.end].strip()
        # Skip if it's already a placeholder
        if detected in _PLACEHOLDERS:
            continue
        text = text[: result.start] + "[NAME]" + text[result.end :]
        name_count += 1

    return text, name_count


def redact(text: str) -> str:
    """Strip PII from text, replacing with bracketed placeholders.

    Handles: emails, phone numbers, URLs, and person names.
    Idempotent: redact(redact(x)) == redact(x).

    Args:
        text: Raw input text.

    Returns:
        Text with PII replaced by [EMAIL], [PHONE], [URL], [NAME].
    """
    if not text or not text.strip():
        return text

    # Skip if text is only placeholders already
    stripped = text.strip()
    if all(token in _PLACEHOLDERS for token in stripped.split()):
        return text

    # Regex-based redaction
    redacted, regex_counts = _redact_with_regex(text)

    # Presidio NER for names
    redacted, name_count = _redact_names_with_presidio(redacted)

    total = (
        regex_counts["email"] + regex_counts["phone"] + regex_counts["url"] + name_count
    )
    if total > 0:
        logger.debug(
            f"PII redacted — emails: {regex_counts['email']}, "
            f"phones: {regex_counts['phone']}, "
            f"urls: {regex_counts['url']}, "
            f"names: {name_count}"
        )

    return redacted
