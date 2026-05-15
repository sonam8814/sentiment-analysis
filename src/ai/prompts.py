"""Prompt templates for Aspect-Based Sentiment Analysis (ABSA).

Any change to prompts must bump PROMPT_VERSION to invalidate the cache.
"""

PROMPT_VERSION: str = "1.0"

VALID_ASPECTS: list[str] = [
    "ui_ux",
    "pricing",
    "features",
    "support",
    "performance",
    "onboarding",
    "other",
]

ABSA_SYSTEM_PROMPT: str = """You are an expert NPS (Net Promoter Score) comment analyst.
Your task is to perform Aspect-Based Sentiment Analysis (ABSA) on customer feedback comments.

## Rules
1. Classify each comment's overall sentiment as exactly one of: "positive", "neutral", or "negative".
2. Identify zero or more aspects from ONLY this fixed taxonomy:
   - "ui_ux" — design, navigation, layout, ease of use
   - "pricing" — cost, value, billing, plans
   - "features" — functionality, capabilities, missing features
   - "support" — customer service, documentation, response time
   - "performance" — speed, reliability, bugs, crashes
   - "onboarding" — signup, setup, first-time experience
   - "other" — anything that doesn't fit the above categories
3. For each aspect, assign a sentiment ("positive", "neutral", or "negative") and a confidence score (0.0 to 1.0).
4. If a comment has no identifiable aspect (e.g., "Great!"), return an empty aspects list.
5. Do NOT invent aspects outside the taxonomy.
6. Return ONLY valid JSON — no markdown fences, no explanation, no extra text.

## Output Schema
Return a JSON object with this exact structure:
{
  "results": [
    {
      "index": 0,
      "overall_sentiment": "positive|neutral|negative",
      "aspects": [
        {"aspect": "pricing", "sentiment": "negative", "confidence": 0.92}
      ]
    }
  ]
}

The "index" field must match the index of the comment in the input list (0-based).
"""


def build_absa_prompt(comments: list[str]) -> str:
    """Format a batch of comments into a prompt for ABSA analysis.

    Args:
        comments: List of PII-redacted comment strings.

    Returns:
        Formatted prompt string with numbered comments.
    """
    lines = ["Analyze the following customer feedback comments:\n"]
    for i, comment in enumerate(comments):
        lines.append(f"[{i}] {comment}")
    lines.append(
        "\nReturn the JSON results for all comments above. "
        "Remember: ONLY valid JSON, no markdown fences."
    )
    return "\n".join(lines)
