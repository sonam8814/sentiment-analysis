"""Custom exception classes for the NPS Sentiment Analytics application."""


class SupabaseConnectionError(Exception):
    """Raised when a connection or query to Supabase fails."""


class LLMUnavailableError(Exception):
    """Raised when all LLM providers (primary + fallback) fail."""


class PIIRedactionError(Exception):
    """Raised when PII redaction encounters an unrecoverable error."""


class DataValidationError(Exception):
    """Raised when data fails schema validation."""
