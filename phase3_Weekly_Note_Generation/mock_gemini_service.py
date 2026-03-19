"""
Mock Gemini service for Phase 3 Weekly Note Generation (for testing without API)
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from src.config.settings import Config
from phase3_Weekly_Note_Generation.config.prompts import (
    WEEKLY_NOTE_PROMPT, 
    THEME_SUMMARY_PROMPT, 
    QUOTE_SELECTION_PROMPT, 
    ACTION_IDEAS_PROMPT,
    WEEKLY_NOTE_SYSTEM_MESSAGE
)

logger = logging.getLogger(__name__)

class GeminiService:
    """Mock service for Phase 3: Weekly Note Generation (for testing)"""
    
    def __init__(self):
        self.config = Config()
        logger.info("Mock Gemini service initialized (for testing)")
    
    def generate_weekly_note(
        self, 
        themes: List[Dict[str, Any]], 
        grouped_reviews: Dict[str, List[Dict[str, Any]]],
        app_name: str = "INDMoney",
        week_start: str = None,
        week_end: str = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Generate a complete weekly note using mock data
        
        Args:
            themes: List of discovered themes
            grouped_reviews: Reviews grouped by theme
            app_name: Name of the app for context
            week_start: Week start date string
            week_end: Week end date string
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with generated content and metadata
        """
        try:
            logger.info(f"Starting mock weekly note generation for {app_name}")
            
            # Generate mock content - use full range (e.g. "March 2 - March 8") so it's clear report includes today
            week_date = f"{week_start} - {week_end}" if (week_start and week_end) else (week_start or "March 2 - March 8")
            
            # Create mock weekly note content
            mock_content = f"""## {app_name} Weekly Review Pulse -- {week_date}

### Top Themes
Feature Requests: Users asking for average NAV and trailing stoploss features (31 mentions)
Bug Fixes: Issues with order modification and fund tracking (26 mentions)  
UI/UX Issues: Navigation difficulties and interface problems (23 mentions)

### Real User Quotes
"App is good but needs average NAV feature for mutual funds to track performance better"
"Can't modify orders after placement, this is very frustrating for active traders"
"UI is confusing, hard to find mutual fund section and track investments"

### Action Ideas
Action 1: Implement average NAV calculation for mutual funds (Priority: High)
Action 2: Add order modification functionality within 5 minutes of placement (Priority: Medium)  
Action 3: Redesign navigation to highlight mutual fund section prominently (Priority: Low)"""
            
            # Parse and structure the response
            structured_note = self._parse_weekly_note(mock_content, themes, grouped_reviews)
            
            logger.info("Successfully generated mock weekly note")
            return structured_note
            
        except Exception as e:
            logger.error(f"Mock weekly note generation failed: {str(e)}")
            raise
    
    def generate_theme_summary(self, themes: List[Dict[str, Any]], max_retries: int = 2) -> str:
        """Generate a summary of top themes"""
        try:
            themes_data = self._format_themes_for_prompt(themes)
            
            summary = """Feature Requests: Users asking for average NAV and trailing stoploss features (31 mentions)
Bug Fixes: Issues with order modification and fund tracking (26 mentions)
UI/UX Issues: Navigation difficulties and interface problems (23 mentions)"""
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Theme summary generation failed: {str(e)}")
            raise
    
    def select_quotes(self, grouped_reviews: Dict[str, List[Dict[str, Any]]], max_retries: int = 2) -> str:
        """Select representative user quotes"""
        try:
            quotes = """Quote 1: "App is good but needs average NAV feature for mutual funds to track performance better"
Quote 2: "Can't modify orders after placement, this is very frustrating for active traders"
Quote 3: "UI is confusing, hard to find mutual fund section and track investments" """
            
            return quotes.strip()
            
        except Exception as e:
            logger.error(f"Quote selection failed: {str(e)}")
            raise
    
    def generate_action_ideas(self, themes_summary: str, max_retries: int = 2) -> str:
        """Generate actionable improvement ideas"""
        try:
            actions = """Action 1: Implement average NAV calculation for mutual funds (Priority: High)
Action 2: Add order modification functionality within 5 minutes of placement (Priority: Medium)
Action 3: Redesign navigation to highlight mutual fund section prominently (Priority: Low)"""
            
            return actions.strip()
            
        except Exception as e:
            logger.error(f"Action ideas generation failed: {str(e)}")
            raise
    
    def _format_themes_for_prompt(self, themes: List[Dict[str, Any]]) -> str:
        """Format themes for the prompt"""
        themes_list = []
        
        for theme in themes:
            theme_id = theme.get('id', '')
            label = theme.get('label', '')
            description = theme.get('description', '')
            review_count = theme.get('reviewCount', 0)
            
            theme_text = f"- {label} ({theme_id}): {description} ({review_count} reviews)"
            themes_list.append(theme_text)
        
        return "\n".join(themes_list)
    
    def _parse_weekly_note(self, content: str, themes: List[Dict[str, Any]], grouped_reviews: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Parse the generated weekly note into structured format"""
        try:
            # Split content into sections
            sections = {}
            current_section = None
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('##'):
                    current_section = line.replace('##', '').strip()
                    sections[current_section] = []
                elif current_section and line:
                    sections[current_section].append(line)
            
            # Extract structured data
            themes_section = '\n'.join(sections.get('Top Themes', []))
            quotes_section = '\n'.join(sections.get('Real User Quotes', []))
            actions_section = '\n'.join(sections.get('Action Ideas', []))
            
            # Count words
            word_count = len(content.split())
            
            return {
                'content': content,
                'themes_summary': themes_section,
                'quotes': quotes_section,
                'actions': actions_section,
                'word_count': word_count,
                'structured_themes': themes[:3],  # Top 3 themes
                'structured_quotes': self._extract_quotes(quotes_section),
                'structured_actions': self._extract_actions(actions_section)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse weekly note: {str(e)}")
            # Return raw content if parsing fails
            return {
                'content': content,
                'word_count': len(content.split()),
                'themes_summary': '',
                'quotes': '',
                'actions': '',
                'structured_themes': themes[:3],
                'structured_quotes': [],
                'structured_actions': []
            }
    
    def _extract_quotes(self, quotes_section: str) -> List[Dict[str, Any]]:
        """Extract structured quotes from the quotes section. No star ratings in output (per architecture)."""
        import re
        quotes = []
        lines = quotes_section.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            quote_text = None
            if line.startswith('Quote') and ':' in line:
                quote_part = line.split(':', 1)[1].strip()
                # Strip (⭐... rating) if present
                quote_text = re.sub(r'\s*\([⭐★☆\d\s]*rating\)\s*$', '', quote_part).strip().strip('"\'')
            elif (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                quote_text = line.strip('"\'')
                quote_text = re.sub(r'\s*\([⭐★☆\d\s]*rating\)\s*$', '', quote_text).strip()
            if quote_text:
                quotes.append({'text': quote_text, 'rating': 0, 'theme_id': 'unknown'})
        
        while len(quotes) < 3:
            quotes.append({'text': "User feedback shows areas for improvement", 'rating': 0, 'theme_id': 'unknown'})
        
        return quotes[:3]
    
    def _extract_actions(self, actions_section: str) -> List[Dict[str, Any]]:
        """Extract structured actions from the actions section"""
        actions = []
        lines = actions_section.split('\n')
        
        for line in lines:
            if line.startswith('Action'):
                # Extract action description and priority
                if ':' in line:
                    action_part = line.split(':', 1)[1].strip()
                    if '(' in action_part:
                        description = action_part.rsplit('(', 1)[0].strip()
                        priority_part = action_part.rsplit('(', 1)[1].strip().rstrip(')')
                        
                        actions.append({
                            'description': description,
                            'priority': priority_part.lower(),
                            'theme_id': 'unknown'
                        })
                    else:
                        actions.append({
                            'description': action_part,
                            'priority': 'medium',
                            'theme_id': 'unknown'
                        })
        
        # Ensure exactly 3 actions
        while len(actions) < 3:
            actions.append({
                'description': 'Continue improving user experience based on feedback',
                'priority': 'medium',
                'theme_id': 'unknown'
            })
        
        return actions[:3]  # Return exactly 3 actions
