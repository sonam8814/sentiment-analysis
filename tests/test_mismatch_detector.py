"""Tests for mismatch detector — toxic promoters and glowing detractors."""

import pandas as pd

from src.analytics.mismatch_detector import flag_toxic_promoters


class TestFlagToxicPromoters:
    def test_toxic_promoter_score_10_negative(self) -> None:
        """Score 10 + negative sentiment = toxic promoter."""
        df = pd.DataFrame({"nps_score": [10], "overall_sentiment": ["negative"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_toxic_promoter"]) is True

    def test_toxic_promoter_score_9_negative(self) -> None:
        """Score 9 + negative sentiment = toxic promoter."""
        df = pd.DataFrame({"nps_score": [9], "overall_sentiment": ["negative"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_toxic_promoter"]) is True

    def test_not_toxic_score_9_neutral(self) -> None:
        """Score 9 + neutral sentiment = NOT toxic promoter."""
        df = pd.DataFrame({"nps_score": [9], "overall_sentiment": ["neutral"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_toxic_promoter"]) is False

    def test_not_toxic_score_9_positive(self) -> None:
        """Score 9 + positive sentiment = NOT toxic promoter."""
        df = pd.DataFrame({"nps_score": [9], "overall_sentiment": ["positive"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_toxic_promoter"]) is False

    def test_not_toxic_score_8_negative(self) -> None:
        """Score 8 + negative sentiment = NOT toxic (8 is passive, not promoter)."""
        df = pd.DataFrame({"nps_score": [8], "overall_sentiment": ["negative"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_toxic_promoter"]) is False

    def test_not_toxic_score_6_negative(self) -> None:
        """Score 6 + negative = detractor, not toxic promoter."""
        df = pd.DataFrame({"nps_score": [6], "overall_sentiment": ["negative"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_toxic_promoter"]) is False

    def test_glowing_detractor_score_0_positive(self) -> None:
        """Score 0 + positive sentiment = glowing detractor."""
        df = pd.DataFrame({"nps_score": [0], "overall_sentiment": ["positive"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_glowing_detractor"]) is True

    def test_glowing_detractor_score_6_positive(self) -> None:
        """Score 6 + positive sentiment = glowing detractor."""
        df = pd.DataFrame({"nps_score": [6], "overall_sentiment": ["positive"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_glowing_detractor"]) is True

    def test_not_glowing_score_7_positive(self) -> None:
        """Score 7 + positive = passive, NOT glowing detractor."""
        df = pd.DataFrame({"nps_score": [7], "overall_sentiment": ["positive"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_glowing_detractor"]) is False

    def test_not_glowing_score_6_neutral(self) -> None:
        """Score 6 + neutral = NOT glowing detractor."""
        df = pd.DataFrame({"nps_score": [6], "overall_sentiment": ["neutral"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_glowing_detractor"]) is False

    def test_not_glowing_score_6_negative(self) -> None:
        """Score 6 + negative = regular detractor, not glowing."""
        df = pd.DataFrame({"nps_score": [6], "overall_sentiment": ["negative"]})
        result = flag_toxic_promoters(df)
        assert bool(result.iloc[0]["is_glowing_detractor"]) is False

    def test_empty_dataframe(self) -> None:
        """Empty DataFrame returns with added columns, no crash."""
        df = pd.DataFrame(columns=["nps_score", "overall_sentiment"])
        result = flag_toxic_promoters(df)
        assert "is_toxic_promoter" in result.columns
        assert "is_glowing_detractor" in result.columns
        assert len(result) == 0

    def test_mixed_rows(self) -> None:
        """Multiple rows — only correct ones flagged."""
        df = pd.DataFrame(
            {
                "nps_score": [10, 9, 8, 6, 3],
                "overall_sentiment": [
                    "negative",
                    "positive",
                    "negative",
                    "positive",
                    "negative",
                ],
            }
        )
        result = flag_toxic_promoters(df)
        assert result["is_toxic_promoter"].tolist() == [
            True,
            False,
            False,
            False,
            False,
        ]
        assert result["is_glowing_detractor"].tolist() == [
            False,
            False,
            False,
            True,
            False,
        ]

    def test_does_not_mutate_input(self) -> None:
        """Original DataFrame is not modified."""
        df = pd.DataFrame({"nps_score": [10], "overall_sentiment": ["negative"]})
        flag_toxic_promoters(df)
        assert "is_toxic_promoter" not in df.columns
