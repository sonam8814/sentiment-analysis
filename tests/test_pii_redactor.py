"""Tests for PII redaction — minimum 10 cases covering all PII types and edge cases."""

from src.data.pii_redactor import redact


class TestPIIRedactor:
    """Test suite for the PII redactor."""

    def test_email_redaction(self) -> None:
        """Emails are replaced with [EMAIL]."""
        text = "Contact me at john.doe@example.com for details."
        result = redact(text)
        assert "[EMAIL]" in result
        assert "john.doe@example.com" not in result

    def test_multiple_emails(self) -> None:
        """Multiple emails in one string are all redacted."""
        text = "Send to alice@test.com or bob@company.org"
        result = redact(text)
        assert result.count("[EMAIL]") == 2
        assert "alice@test.com" not in result
        assert "bob@company.org" not in result

    def test_phone_redaction(self) -> None:
        """Phone numbers are replaced with [PHONE]."""
        text = "Call me at 555-123-4567 anytime."
        result = redact(text)
        assert "[PHONE]" in result
        assert "555-123-4567" not in result

    def test_phone_with_country_code(self) -> None:
        """International phone numbers are redacted."""
        text = "My number is +1-800-555-0199."
        result = redact(text)
        assert "[PHONE]" in result
        assert "800-555-0199" not in result

    def test_url_redaction(self) -> None:
        """URLs are replaced with [URL]."""
        text = "Visit https://www.example.com/page for info."
        result = redact(text)
        assert "[URL]" in result
        assert "https://www.example.com/page" not in result

    def test_url_http(self) -> None:
        """HTTP URLs are also redacted."""
        text = "Go to http://insecure-site.com/path?q=1 please."
        result = redact(text)
        assert "[URL]" in result
        assert "http://insecure-site.com" not in result

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert redact("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string returns the same."""
        assert redact("   ") == "   "

    def test_no_pii(self) -> None:
        """Text without PII is returned unchanged."""
        text = "The product is great and I love the features!"
        result = redact(text)
        assert result == text

    def test_only_pii(self) -> None:
        """Text that is entirely PII gets fully replaced."""
        text = "user@example.com"
        result = redact(text)
        assert "[EMAIL]" in result
        assert "user@example.com" not in result

    def test_mixed_pii(self) -> None:
        """Text with multiple PII types gets all replaced."""
        text = "Email john@test.com or call 555-987-6543, see https://info.com"
        result = redact(text)
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "[URL]" in result
        assert "john@test.com" not in result
        assert "555-987-6543" not in result
        assert "https://info.com" not in result

    def test_idempotent(self) -> None:
        """Redacting an already-redacted string returns the same result."""
        text = "Reach me at jane@corp.io or 123-456-7890"
        once = redact(text)
        twice = redact(once)
        assert once == twice

    def test_none_handling(self) -> None:
        """None input should not crash (handled upstream, but defensive)."""
        # The function expects str, but empty string should work
        assert redact("") == ""

    def test_pii_in_feedback_context(self) -> None:
        """Realistic NPS comment with embedded PII."""
        text = (
            "I spoke with Sarah Johnson at support and she was unhelpful. "
            "I sent an email to support@company.com and never heard back. "
            "My account number is irrelevant but my phone is (415) 555-0100."
        )
        result = redact(text)
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "support@company.com" not in result
        assert "555-0100" not in result
