"""
Phase 3: Weekly Note Generation
"""
from .gemini_service import GeminiService
from .note_generation import WeeklyNoteService
from .models.note import WeeklyReport, Theme, Quote, ActionIdea
from .config.prompts import WEEKLY_NOTE_PROMPT, THEME_SUMMARY_PROMPT, QUOTE_SELECTION_PROMPT, ACTION_IDEAS_PROMPT

__all__ = [
    'GeminiService',
    'WeeklyNoteService',
    'WeeklyReport',
    'Theme',
    'Quote',
    'ActionIdea',
    'WEEKLY_NOTE_PROMPT',
    'THEME_SUMMARY_PROMPT',
    'QUOTE_SELECTION_PROMPT',
    'ACTION_IDEAS_PROMPT'
]

