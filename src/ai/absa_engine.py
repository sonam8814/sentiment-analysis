"""ABSA engine — orchestrates aspect-based sentiment analysis over batches of comments."""

import json
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from loguru import logger
from pydantic import ValidationError

from config.settings import Settings, get_settings
from src.ai.cache import get_cache, get_cached, set_cached
from src.ai.llm_client import LLMClient
from src.ai.prompts import ABSA_SYSTEM_PROMPT, VALID_ASPECTS, build_absa_prompt
from src.data.schemas import AspectSentiment


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from LLM output.

    Args:
        text: Raw LLM response text.

    Returns:
        Cleaned text with fences removed.
    """
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _parse_llm_response(raw: str) -> list[dict[str, Any]]:
    """Parse and validate the LLM JSON response.

    Args:
        raw: Raw response text from the LLM.

    Returns:
        List of result dicts from the parsed JSON.

    Raises:
        ValueError: If JSON is invalid or missing expected structure.
    """
    cleaned = _strip_markdown_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

    if isinstance(parsed, dict) and "results" in parsed:
        return parsed["results"]
    raise ValueError(f"LLM response missing 'results' key: {cleaned[:200]}")


def _validate_single_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate a single ABSA result against the schema.

    Filters out invalid aspects and ensures sentiment values are valid.

    Args:
        result: A single result dict from the LLM.

    Returns:
        Validated result dict with only valid aspects.
    """
    valid_sentiments = {"positive", "neutral", "negative"}

    overall = result.get("overall_sentiment", "neutral")
    if overall not in valid_sentiments:
        logger.warning(f"Invalid overall_sentiment '{overall}', defaulting to neutral")
        overall = "neutral"

    validated_aspects: list[dict[str, Any]] = []
    for aspect_data in result.get("aspects", []):
        try:
            asp = AspectSentiment(**aspect_data)
            if asp.aspect in VALID_ASPECTS:
                validated_aspects.append(asp.model_dump())
            else:
                logger.warning(f"Invalid aspect '{asp.aspect}' — skipped")
        except (ValidationError, TypeError) as exc:
            logger.warning(f"Aspect validation failed: {exc} — skipped")

    return {
        "overall_sentiment": overall,
        "aspects": validated_aspects,
    }


def _default_result() -> dict[str, Any]:
    """Return a safe default result for failed analysis.

    Returns:
        Dict with neutral sentiment and empty aspects.
    """
    return {"overall_sentiment": "neutral", "aspects": []}


def analyze_batch(
    comments: list[str],
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    """Analyze a batch of comments, using cache where possible.

    Args:
        comments: List of PII-redacted comment strings.
        llm_client: Optional LLMClient override.
        settings: Optional settings override.

    Returns:
        List of result dicts, one per comment, in the same order.
    """
    settings = settings or get_settings()
    cache = get_cache(settings.cache_dir, settings.cache_expiry_days)

    results: dict[int, dict[str, Any]] = {}
    uncached_indices: list[int] = []
    uncached_comments: list[str] = []

    # Check cache for each comment
    for i, comment in enumerate(comments):
        if not comment.strip():
            results[i] = _default_result()
            continue

        cached = get_cached(cache, comment)
        if cached is not None:
            results[i] = cached
        else:
            uncached_indices.append(i)
            uncached_comments.append(comment)

    # Call LLM for uncached comments
    if uncached_comments:
        client = llm_client or LLMClient(settings)
        prompt = build_absa_prompt(uncached_comments)

        try:
            raw_response = client.complete(prompt, system=ABSA_SYSTEM_PROMPT)
            parsed_results = _parse_llm_response(raw_response)

            for parsed in parsed_results:
                idx_in_batch = parsed.get("index", -1)
                if 0 <= idx_in_batch < len(uncached_comments):
                    validated = _validate_single_result(parsed)
                    original_idx = uncached_indices[idx_in_batch]
                    results[original_idx] = validated

                    # Write to cache
                    set_cached(
                        cache,
                        uncached_comments[idx_in_batch],
                        validated,
                        settings.cache_expiry_days,
                    )
                else:
                    logger.warning(f"LLM returned out-of-range index: {idx_in_batch}")

        except Exception as exc:
            logger.error(f"LLM batch analysis failed: {exc}")

    # Fill any gaps with defaults
    for i in range(len(comments)):
        if i not in results:
            logger.warning(f"No result for comment index {i} — using default")
            results[i] = _default_result()

    return [results[i] for i in range(len(comments))]


def analyze_dataframe(
    df: pd.DataFrame,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> pd.DataFrame:
    """Run ABSA over a DataFrame and add derived columns.

    Adds columns: aspects, overall_sentiment, analyzed_at.
    Processes in batches according to LLM_BATCH_SIZE.

    Args:
        df: DataFrame with a 'comment_redacted' column.
        llm_client: Optional LLMClient override.
        settings: Optional settings override.

    Returns:
        DataFrame with ABSA columns added.
    """
    settings = settings or get_settings()
    df = df.copy()

    if df.empty:
        df["aspects"] = pd.Series(dtype="object")
        df["overall_sentiment"] = pd.Series(dtype="str")
        df["analyzed_at"] = pd.Series(dtype="datetime64[ns, UTC]")
        return df

    all_comments = df["comment_redacted"].fillna("").tolist()
    batch_size = settings.llm_batch_size
    all_results: list[dict[str, Any]] = []

    for start in range(0, len(all_comments), batch_size):
        batch = all_comments[start : start + batch_size]
        logger.info(
            f"Analyzing batch {start // batch_size + 1} "
            f"({len(batch)} comments, offset {start})"
        )
        batch_results = analyze_batch(batch, llm_client=llm_client, settings=settings)
        all_results.extend(batch_results)

    df["aspects"] = [r["aspects"] for r in all_results]
    df["overall_sentiment"] = [r["overall_sentiment"] for r in all_results]
    df["analyzed_at"] = datetime.now(timezone.utc)

    logger.info(f"ABSA complete: {len(df)} comments analyzed")
    return df
