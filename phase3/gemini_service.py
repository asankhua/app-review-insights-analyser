"""
Gemini LLM service for Phase 3 Weekly Note Generation
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from src.config.settings import Config
from phase3.config.prompts import (
    WEEKLY_NOTE_PROMPT, 
    THEME_SUMMARY_PROMPT, 
    QUOTE_SELECTION_PROMPT, 
    ACTION_IDEAS_PROMPT,
    WEEKLY_NOTE_SYSTEM_MESSAGE
)

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Gemini LLM API"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client"""
        try:
            api_key = self.config.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise
    
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
        Generate a complete weekly note using Gemini
        
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
            logger.info(f"Starting weekly note generation for {app_name}")
            
            # Prepare data for prompts
            themes_data = self._format_themes_for_prompt(themes)
            grouped_reviews_text = self._format_reviews_for_prompt(grouped_reviews)
            week_date = f"{week_start} - {week_end}" if (week_start and week_end) else (week_start or self._get_current_week_range())
            
            logger.debug(f"Themes data: {themes_data[:200]}...")
            logger.debug(f"Grouped reviews: {grouped_reviews_text[:200]}...")
            
            # Generate complete weekly note
            note_content = self._generate_with_retry(
                WEEKLY_NOTE_PROMPT.format(
                    app_name=app_name,
                    themes_data=themes_data,
                    grouped_reviews=grouped_reviews_text,
                    week_date=week_date
                ),
                max_retries
            )
            
            logger.debug(f"Generated content: {note_content[:500]}...")
            
            # Parse and structure the response
            structured_note = self._parse_weekly_note(note_content, themes, grouped_reviews)
            
            logger.info("Successfully generated weekly note")
            return structured_note
            
        except Exception as e:
            logger.error(f"Weekly note generation failed: {str(e)}")
            raise
    
    def generate_theme_summary(self, themes: List[Dict[str, Any]], max_retries: int = 2) -> str:
        """Generate a summary of top themes"""
        try:
            themes_data = self._format_themes_for_prompt(themes)
            
            summary = self._generate_with_retry(
                THEME_SUMMARY_PROMPT.format(themes_data=themes_data),
                max_retries
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Theme summary generation failed: {str(e)}")
            raise
    
    def select_quotes(self, grouped_reviews: Dict[str, List[Dict[str, Any]]], max_retries: int = 2) -> str:
        """Select representative user quotes"""
        try:
            grouped_reviews_text = self._format_reviews_for_prompt(grouped_reviews)
            
            quotes = self._generate_with_retry(
                QUOTE_SELECTION_PROMPT.format(grouped_reviews=grouped_reviews_text),
                max_retries
            )
            
            return quotes.strip()
            
        except Exception as e:
            logger.error(f"Quote selection failed: {str(e)}")
            raise
    
    def generate_action_ideas(self, themes_summary: str, max_retries: int = 2) -> str:
        """Generate actionable improvement ideas"""
        try:
            actions = self._generate_with_retry(
                ACTION_IDEAS_PROMPT.format(themes_summary=themes_summary),
                max_retries
            )
            
            return actions.strip()
            
        except Exception as e:
            logger.error(f"Action ideas generation failed: {str(e)}")
            raise
    
    def _generate_with_retry(self, prompt: str, max_retries: int) -> str:
        """Generate content with retry logic"""
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}: Calling Gemini API")
                
                # Call Gemini API
                response = self.client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,  # Balanced creativity
                        max_output_tokens=2000,  # Sufficient for weekly note
                        top_p=0.8,
                        top_k=40
                    )
                )
                
                content = response.text.strip()
                
                if not content:
                    raise ValueError("Empty response from Gemini")
                
                logger.debug(f"Successfully generated content on attempt {attempt + 1}")
                return content
                
            except Exception as e:
                logger.warning(f"Generation failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise
                time.sleep(1)  # Wait before retry
        
        raise Exception("Failed to generate content after all retries")
    
    def _format_themes_for_prompt(self, themes: List[Dict[str, Any]]) -> str:
        """Format themes for the prompt"""
        themes_list = []
        
        for theme in themes:
            # Handle both dict and ThemeModel objects
            if hasattr(theme, 'id'):
                theme_id = theme.id
                label = theme.label
                description = theme.description
                review_count = getattr(theme, 'reviewCount', 0)
            else:
                theme_id = theme.get('id', '')
                label = theme.get('label', '')
                description = theme.get('description', '')
                review_count = theme.get('reviewCount', 0)
            
            theme_text = f"- {label} ({theme_id}): {description} ({review_count} reviews)"
            themes_list.append(theme_text)
        
        return "\n".join(themes_list)
    
    def _format_reviews_for_prompt(self, grouped_reviews: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format grouped reviews for the prompt"""
        reviews_text = []
        
        for theme_id, reviews in grouped_reviews.items():
            if theme_id == 'unclassified':
                continue
                
            reviews_text.append(f"\nTheme: {theme_id}")
            
            # Select a few representative reviews (max 3 per theme)
            for review in reviews[:3]:
                rating = review.get('rating', 1)
                text = review.get('text', '').strip()
                if text:
                    reviews_text.append(f"- ({rating}/5) {text}")
        
        return "\n".join(reviews_text)
    
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
            
            # Extract structured data with fallbacks
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
        """Extract structured quotes. No star ratings in output (per ARCHITECTURE)."""
        import re
        quotes = []
        lines = quotes_section.split('\n')
        star_pattern = re.compile(r'\s*\([^)]*rating\)\s*$', re.IGNORECASE)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            quote_text = None
            if line.startswith('Quote') and ':' in line:
                quote_part = line.split(':', 1)[1].strip()
                quote_text = star_pattern.sub('', quote_part).strip().strip('"\'')
            elif (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
                quote_text = star_pattern.sub('', line.strip('"\'')).strip()
            if quote_text:
                quotes.append({'text': quote_text, 'rating': 0, 'theme_id': 'unknown'})
        
        while len(quotes) < 3:
            quotes.append({'text': 'User feedback shows areas for improvement', 'rating': 0, 'theme_id': 'unknown'})
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
        
        return actions
    
    def _get_current_week_range(self) -> str:
        """Get current week date range"""
        from datetime import datetime, timedelta
        
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        return f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')}"
