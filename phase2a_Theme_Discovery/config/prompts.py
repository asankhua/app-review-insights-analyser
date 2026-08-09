"""
Prompts for Phase 2a Theme Discovery using Groq LLM
"""

THEME_DISCOVERY_PROMPT = """You are a product analyst. Given these user reviews for the {app_name} app, identify exactly 3 to 5 recurring themes. Return ONLY a JSON array of theme objects: [{{"id": "theme_slug", "label": "Human Label", "description": "one-line description"}}].

Requirements:
- Maximum 5 themes, minimum 3 themes
- Each theme should be actionable and relevant to product improvements
- Group similar feedback together
- Focus on user pain points, feature requests, and overall experience
- Use lowercase, underscore-separated IDs (e.g., "app_performance", "ui_ux_issues")
- Labels should be human-readable and clear
- Descriptions should be concise one-line summaries

Reviews:
{reviews_text}

Return ONLY valid JSON array, no additional text or explanation."""

THEME_DISCOVERY_RETRY_PROMPT = """You are a product analyst. I need you to return ONLY a valid JSON array. Your previous response was not valid JSON.

Given these user reviews for the {app_name} app, identify exactly 3 to 5 recurring themes. Return ONLY this JSON format:
[{{"id": "theme_slug", "label": "Human Label", "description": "one-line description"}}]

Reviews:
{reviews_text}

Return ONLY the JSON array, nothing else."""

# System message for Groq
THEME_DISCOVERY_SYSTEM_MESSAGE = """You are a product analyst specializing in mobile app review analysis. Your task is to identify recurring themes from user reviews and return them in a specific JSON format. Always ensure your output is valid JSON that can be parsed."""

