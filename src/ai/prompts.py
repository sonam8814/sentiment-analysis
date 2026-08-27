PROMPT_VERSION = "1.0.0"

VALID_ASPECTS = [
    "Product Quality",
    "Customer Support",
    "Pricing",
    "Usability",
    "Features",
]

ABSA_SYSTEM_PROMPT = """
You are an expert in Aspect-Based Sentiment Analysis (ABSA).
Analyze the text and evaluate sentiments for relevant aspects.
"""

def build_absa_prompt(text: str) -> str:
    return f"Analyze the following feedback for aspect sentiments:\n\n{text}"