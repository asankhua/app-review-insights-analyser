"""
Prompts for Phase 3 Weekly Note Generation using Gemini LLM
"""

WEEKLY_NOTE_PROMPT = """You are a product insights analyst. Generate a concise weekly review pulse for the {app_name} app based on the provided themes and user reviews.

Requirements:
- Maximum 400 words total
- Focus on actionable insights
- Use the exact structure provided below
- Be professional yet engaging

Themes Data:
{themes_data}

Grouped Reviews by Theme:
{grouped_reviews}

Generate the weekly pulse using this exact format:

## {app_name} Weekly Review Pulse -- {week_date}

### Top Themes
{themes_summary}

### Real User Quotes
{user_quotes}

### Action Ideas
{action_ideas}

Guidelines:
- Top Themes: List top 3 themes with one-sentence summary and mention count
- Real User Quotes: Exactly 3 verbatim quotes only (no star ratings, no PII per architecture)
- Action Ideas: Exactly 3 concrete, theme-linked actions, maximum 30 words each
- Total length must be under 400 words"""

THEME_SUMMARY_PROMPT = """Given these themes and their review counts, generate a concise summary of the top 3 themes.

Themes Data:
{themes_data}

Output format (maximum 100 words total):
Theme 1: [Theme Name] - [One-sentence summary] ([count] mentions)
Theme 2: [Theme Name] - [One-sentence summary] ([count] mentions)
Theme 3: [Theme Name] - [One-sentence summary] ([count] mentions)"""

QUOTE_SELECTION_PROMPT = """Select 3 representative user quotes from these reviews. Each quote must be impactful and represent different themes.

Requirements:
- No PII (usernames, emails, IDs)
- Maximum 50 words per quote
- Do NOT include star ratings or emoji in output (per architecture)
- Should represent different themes
- Must be exact verbatim quotes from provided reviews

Grouped Reviews:
{grouped_reviews}

Output format (quote text only, no ratings):
Quote 1: "[Quote text]"
Quote 2: "[Quote text]"
Quote 3: "[Quote text]" """

ACTION_IDEAS_PROMPT = """Generate 3 actionable improvement ideas based on these themes and user feedback.

Requirements:
- Specific and measurable actions
- Prioritized by impact
- Feasible for development team
- Maximum 30 words per action
- Link to specific themes mentioned

Themes and Issues:
{themes_summary}

Output format:
Action 1: [Action description] (Priority: High)
Action 2: [Action description] (Priority: Medium)
Action 3: [Action description] (Priority: Low)"""

# System message for Gemini
WEEKLY_NOTE_SYSTEM_MESSAGE = """You are a product insights analyst specializing in mobile app review analysis. Your task is to generate concise, actionable weekly review pulses that help product teams understand user feedback and prioritize improvements. Always ensure your output is professional, insightful, and follows the specified format exactly."""

