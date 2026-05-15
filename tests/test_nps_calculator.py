"""Tests for NPS calculator — 100% coverage target."""

import pandas as pd

from src.analytics.nps_calculator import calculate_nps, categorize, category_breakdown


class TestCategorize:
    def test_promoter_score_10(self) -> None:
        assert categorize(10) == "promoter"

    def test_promoter_score_9(self) -> None:
        assert categorize(9) == "promoter"

    def test_passive_score_8(self) -> None:
        assert categorize(8) == "passive"

    def test_passive_score_7(self) -> None:
        assert categorize(7) == "passive"

    def test_detractor_score_6(self) -> None:
        assert categorize(6) == "detractor"

    def test_detractor_score_0(self) -> None:
        assert categorize(0) == "detractor"

    def test_detractor_score_3(self) -> None:
        assert categorize(3) == "detractor"


class TestCalculateNPS:
    def test_all_promoters(self) -> None:
        """All 10s → NPS = 100."""
        df = pd.DataFrame({"nps_score": [10, 10, 10, 10]})
        assert calculate_nps(df) == 100.0

    def test_all_detractors(self) -> None:
        """All 0s → NPS = -100."""
        df = pd.DataFrame({"nps_score": [0, 0, 0, 0]})
        assert calculate_nps(df) == -100.0

    def test_balanced(self) -> None:
        """Equal promoters and detractors → NPS = 0."""
        df = pd.DataFrame({"nps_score": [10, 10, 0, 0]})
        assert calculate_nps(df) == 0.0

    def test_all_passives(self) -> None:
        """All passives → NPS = 0 (0% promoters - 0% detractors)."""
        df = pd.DataFrame({"nps_score": [7, 7, 8, 8]})
        assert calculate_nps(df) == 0.0

    def test_empty_dataframe(self) -> None:
        """Empty DataFrame → NPS = 0."""
        df = pd.DataFrame(columns=["nps_score"])
        assert calculate_nps(df) == 0.0

    def test_single_promoter(self) -> None:
        df = pd.DataFrame({"nps_score": [10]})
        assert calculate_nps(df) == 100.0

    def test_single_detractor(self) -> None:
        df = pd.DataFrame({"nps_score": [3]})
        assert calculate_nps(df) == -100.0

    def test_mixed_realistic(self) -> None:
        """5 promoters, 3 passives, 2 detractors → NPS = 30."""
        scores = [10, 10, 9, 9, 10, 7, 8, 7, 3, 1]
        df = pd.DataFrame({"nps_score": scores})
        # 5 promoters (50%), 3 passives, 2 detractors (20%) → 50 - 20 = 30
        assert calculate_nps(df) == 30.0

    def test_boundary_score_9_is_promoter(self) -> None:
        """Score 9 counts as promoter."""
        df = pd.DataFrame({"nps_score": [9, 6]})
        # 1 promoter (50%), 1 detractor (50%) → 0
        assert calculate_nps(df) == 0.0

    def test_boundary_score_7_is_passive(self) -> None:
        """Score 7 is passive — doesn't affect NPS."""
        df = pd.DataFrame({"nps_score": [7]})
        assert calculate_nps(df) == 0.0


class TestCategoryBreakdown:
    def test_all_promoters(self) -> None:
        df = pd.DataFrame({"nps_score": [10, 9, 10]})
        result = category_breakdown(df)
        assert result == {"promoter": 1.0, "passive": 0.0, "detractor": 0.0}

    def test_all_detractors(self) -> None:
        df = pd.DataFrame({"nps_score": [0, 1, 5]})
        result = category_breakdown(df)
        assert result == {"promoter": 0.0, "passive": 0.0, "detractor": 1.0}

    def test_even_split(self) -> None:
        df = pd.DataFrame({"nps_score": [10, 7, 3]})
        result = category_breakdown(df)
        assert abs(result["promoter"] - 1 / 3) < 1e-9
        assert abs(result["passive"] - 1 / 3) < 1e-9
        assert abs(result["detractor"] - 1 / 3) < 1e-9

    def test_empty_dataframe(self) -> None:
        df = pd.DataFrame(columns=["nps_score"])
        result = category_breakdown(df)
        assert result == {"promoter": 0.0, "passive": 0.0, "detractor": 0.0}

    def test_proportions_sum_to_one(self) -> None:
        df = pd.DataFrame({"nps_score": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]})
        result = category_breakdown(df)
        assert abs(sum(result.values()) - 1.0) < 1e-9
