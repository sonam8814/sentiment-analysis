"""Tests for the ABSA engine with mocked LLM responses."""

import json
import tempfile
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.ai.absa_engine import (
    _default_result,
    _parse_llm_response,
    _strip_markdown_fences,
    _validate_single_result,
    analyze_batch,
    analyze_dataframe,
)


# ---------------------------------------------------------------------------
# Helper: build a mock Settings object
# ---------------------------------------------------------------------------
def _mock_settings(tmp_dir: str) -> MagicMock:
    settings = MagicMock()
    settings.cache_dir = tmp_dir
    settings.cache_expiry_days = 30
    settings.llm_batch_size = 10
    settings.llm_provider_primary = "groq"
    settings.groq_api_key = "fake"
    settings.groq_model = "test-model"
    settings.gemini_api_key = "fake"
    settings.gemini_model = "test-model"
    settings.llm_max_retries = 1
    settings.llm_timeout_seconds = 5
    return settings


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------
class TestStripMarkdownFences:
    def test_no_fences(self) -> None:
        assert _strip_markdown_fences('{"results": []}') == '{"results": []}'

    def test_json_fences(self) -> None:
        text = '```json\n{"results": []}\n```'
        assert _strip_markdown_fences(text) == '{"results": []}'

    def test_plain_fences(self) -> None:
        text = '```\n{"results": []}\n```'
        assert _strip_markdown_fences(text) == '{"results": []}'


class TestParseLLMResponse:
    def test_valid_json(self) -> None:
        raw = json.dumps(
            {
                "results": [
                    {
                        "index": 0,
                        "overall_sentiment": "positive",
                        "aspects": [
                            {
                                "aspect": "features",
                                "sentiment": "positive",
                                "confidence": 0.95,
                            }
                        ],
                    }
                ]
            }
        )
        results = _parse_llm_response(raw)
        assert len(results) == 1
        assert results[0]["overall_sentiment"] == "positive"

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            _parse_llm_response("not json at all")

    def test_missing_results_key_raises(self) -> None:
        with pytest.raises(ValueError, match="missing 'results'"):
            _parse_llm_response('{"data": []}')

    def test_json_with_markdown_fences(self) -> None:
        raw = '```json\n{"results": [{"index": 0, "overall_sentiment": "neutral", "aspects": []}]}\n```'
        results = _parse_llm_response(raw)
        assert len(results) == 1


class TestValidateSingleResult:
    def test_valid_result(self) -> None:
        result = {
            "overall_sentiment": "negative",
            "aspects": [
                {"aspect": "pricing", "sentiment": "negative", "confidence": 0.88}
            ],
        }
        validated = _validate_single_result(result)
        assert validated["overall_sentiment"] == "negative"
        assert len(validated["aspects"]) == 1

    def test_invalid_overall_sentiment_defaults_neutral(self) -> None:
        result = {"overall_sentiment": "angry", "aspects": []}
        validated = _validate_single_result(result)
        assert validated["overall_sentiment"] == "neutral"

    def test_invalid_aspect_name_skipped(self) -> None:
        result = {
            "overall_sentiment": "positive",
            "aspects": [
                {"aspect": "banana", "sentiment": "positive", "confidence": 0.9},
                {"aspect": "features", "sentiment": "positive", "confidence": 0.8},
            ],
        }
        validated = _validate_single_result(result)
        assert len(validated["aspects"]) == 1
        assert validated["aspects"][0]["aspect"] == "features"

    def test_missing_aspect_fields_skipped(self) -> None:
        result = {
            "overall_sentiment": "positive",
            "aspects": [
                {"aspect": "pricing"},  # missing sentiment and confidence
            ],
        }
        validated = _validate_single_result(result)
        assert len(validated["aspects"]) == 0

    def test_empty_aspects_valid(self) -> None:
        result = {"overall_sentiment": "positive", "aspects": []}
        validated = _validate_single_result(result)
        assert validated["aspects"] == []

    def test_all_valid_aspects_accepted(self) -> None:
        aspects = [
            {"aspect": a, "sentiment": "neutral", "confidence": 0.5}
            for a in [
                "ui_ux",
                "pricing",
                "features",
                "support",
                "performance",
                "onboarding",
                "other",
            ]
        ]
        result = {"overall_sentiment": "neutral", "aspects": aspects}
        validated = _validate_single_result(result)
        assert len(validated["aspects"]) == 7


# ---------------------------------------------------------------------------
# Integration tests with mocked LLM
# ---------------------------------------------------------------------------
class TestAnalyzeBatch:
    def test_happy_path(self) -> None:
        """LLM returns valid JSON — results are correctly parsed and cached."""
        llm_response = json.dumps(
            {
                "results": [
                    {
                        "index": 0,
                        "overall_sentiment": "positive",
                        "aspects": [
                            {
                                "aspect": "features",
                                "sentiment": "positive",
                                "confidence": 0.95,
                            }
                        ],
                    },
                    {
                        "index": 1,
                        "overall_sentiment": "negative",
                        "aspects": [
                            {
                                "aspect": "support",
                                "sentiment": "negative",
                                "confidence": 0.87,
                            }
                        ],
                    },
                ]
            }
        )

        mock_client = MagicMock()
        mock_client.complete.return_value = llm_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            comments = ["Great features!", "Support is terrible."]
            results = analyze_batch(comments, llm_client=mock_client, settings=settings)

            assert len(results) == 2
            assert results[0]["overall_sentiment"] == "positive"
            assert results[1]["overall_sentiment"] == "negative"
            assert results[0]["aspects"][0]["aspect"] == "features"

    def test_malformed_json_degrades_gracefully(self) -> None:
        """Malformed LLM JSON doesn't crash — defaults to neutral."""
        mock_client = MagicMock()
        mock_client.complete.return_value = "this is not JSON {{{}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            results = analyze_batch(
                ["Some comment"], llm_client=mock_client, settings=settings
            )

            assert len(results) == 1
            assert results[0]["overall_sentiment"] == "neutral"
            assert results[0]["aspects"] == []

    def test_empty_comment_returns_default(self) -> None:
        """Empty comments get default result without calling LLM."""
        mock_client = MagicMock()

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            results = analyze_batch(
                ["", "   "], llm_client=mock_client, settings=settings
            )

            assert len(results) == 2
            assert all(r["overall_sentiment"] == "neutral" for r in results)
            mock_client.complete.assert_not_called()

    def test_cache_hit_skips_llm(self) -> None:
        """Second call for the same comment hits cache, not LLM."""
        llm_response = json.dumps(
            {
                "results": [
                    {
                        "index": 0,
                        "overall_sentiment": "positive",
                        "aspects": [],
                    }
                ]
            }
        )

        mock_client = MagicMock()
        mock_client.complete.return_value = llm_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            comments = ["Cached comment test"]

            # First call — hits LLM
            analyze_batch(comments, llm_client=mock_client, settings=settings)
            assert mock_client.complete.call_count == 1

            # Second call — should hit cache
            results = analyze_batch(comments, llm_client=mock_client, settings=settings)
            assert mock_client.complete.call_count == 1  # Not called again
            assert results[0]["overall_sentiment"] == "positive"

    def test_llm_exception_degrades_gracefully(self) -> None:
        """LLM raising an exception doesn't crash — defaults to neutral."""
        mock_client = MagicMock()
        mock_client.complete.side_effect = RuntimeError("API down")

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            results = analyze_batch(
                ["Test comment"], llm_client=mock_client, settings=settings
            )

            assert len(results) == 1
            assert results[0] == _default_result()


class TestAnalyzeDataFrame:
    def test_adds_columns(self) -> None:
        """analyze_dataframe adds aspects, overall_sentiment, analyzed_at."""
        llm_response = json.dumps(
            {
                "results": [
                    {
                        "index": 0,
                        "overall_sentiment": "positive",
                        "aspects": [
                            {
                                "aspect": "ui_ux",
                                "sentiment": "positive",
                                "confidence": 0.9,
                            }
                        ],
                    }
                ]
            }
        )

        mock_client = MagicMock()
        mock_client.complete.return_value = llm_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            df = pd.DataFrame({"comment_redacted": ["Love the new UI!"]})
            result_df = analyze_dataframe(df, llm_client=mock_client, settings=settings)

            assert "aspects" in result_df.columns
            assert "overall_sentiment" in result_df.columns
            assert "analyzed_at" in result_df.columns
            assert result_df.iloc[0]["overall_sentiment"] == "positive"

    def test_empty_dataframe(self) -> None:
        """Empty DataFrame returns with added columns, no LLM call."""
        mock_client = MagicMock()

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            df = pd.DataFrame(columns=["comment_redacted"])
            result_df = analyze_dataframe(df, llm_client=mock_client, settings=settings)

            assert "aspects" in result_df.columns
            assert "overall_sentiment" in result_df.columns
            assert "analyzed_at" in result_df.columns
            assert len(result_df) == 0
            mock_client.complete.assert_not_called()

    def test_respects_batch_size(self) -> None:
        """Comments are batched according to llm_batch_size setting."""
        llm_response_batch1 = json.dumps(
            {
                "results": [
                    {"index": i, "overall_sentiment": "neutral", "aspects": []}
                    for i in range(3)
                ]
            }
        )
        llm_response_batch2 = json.dumps(
            {
                "results": [
                    {"index": i, "overall_sentiment": "neutral", "aspects": []}
                    for i in range(2)
                ]
            }
        )

        mock_client = MagicMock()
        mock_client.complete.side_effect = [
            llm_response_batch1,
            llm_response_batch2,
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = _mock_settings(tmp_dir)
            settings.llm_batch_size = 3

            df = pd.DataFrame({"comment_redacted": [f"Comment {i}" for i in range(5)]})
            result_df = analyze_dataframe(df, llm_client=mock_client, settings=settings)

            assert len(result_df) == 5
            assert mock_client.complete.call_count == 2
