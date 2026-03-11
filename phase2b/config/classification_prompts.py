"""
Prompts for Phase 2b Review Classification using Groq LLM
"""

REVIEW_CLASSIFICATION_PROMPT = """You are a product analyst. Given this user review for the {app_name} app and the available themes, classify which theme best matches this review.

Available Themes:
{themes_list}

Review to classify:
Rating: {rating}/5
Text: "{review_text}"

Return ONLY a JSON object with the theme ID and confidence score:
{{"themeId": "theme_slug", "confidence": 0.85}}

Requirements:
- Choose the single best matching theme
- Confidence should be between 0.0 and 1.0
- If no theme matches well, use "unclassified" as themeId with low confidence
- Return ONLY valid JSON, no additional text or explanation"""

REVIEW_CLASSIFICATION_RETRY_PROMPT = """You are a product analyst. I need you to return ONLY valid JSON. Your previous response was not valid JSON.

Given this user review for the {app_name} app and the available themes, classify which theme best matches this review.

Available Themes:
{themes_list}

Review to classify:
Rating: {rating}/5
Text: "{review_text}"

Return ONLY this JSON format:
{{"themeId": "theme_slug", "confidence": 0.85}}

Choose the single best matching theme. Return ONLY the JSON object, nothing else."""

# System message for Groq
REVIEW_CLASSIFICATION_SYSTEM_MESSAGE = """You are a product analyst specializing in mobile app review classification. Your task is to classify reviews into predefined themes and return them in a specific JSON format. Always ensure your output is valid JSON that can be parsed."""
