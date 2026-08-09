"""
Phase 3 Weekly Note Generation Service
"""
import json
import logging
import re
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Per ARCHITECTURE: No star ratings in output artifacts
STAR_RATING_PATTERN = re.compile(r'\s*\([^)]*rating\)\s*', re.IGNORECASE)

from .models.note import WeeklyReport, WeeklyReportFile, NoteGenerationRequest, NoteGenerationResponse
from .mock_gemini_service import GeminiService
from phase2b_Review_Classification.review_classification import ReviewClassificationService
from phase2a_Theme_Discovery.theme_discovery import ThemeDiscoveryService
from src.config.settings import Config

logger = logging.getLogger(__name__)

class WeeklyNoteService:
    """Service for Phase 3: Weekly Note Generation"""
    
    def __init__(self):
        self.config = Config()
        self.gemini_service = GeminiService()
        self.classification_service = ReviewClassificationService()
        self.theme_service = ThemeDiscoveryService()
        
        # Ensure reports directory exists
        Path(self.config.REPORTS_DIR).mkdir(exist_ok=True)
    
    def generate_weekly_note_from_latest(
        self,
        week_start: Optional[date] = None,
        week_end: Optional[date] = None,
        app_name: str = "INDMoney"
    ) -> str:
        """
        Generate weekly note from latest themes and classified reviews
        
        Args:
            week_start: Start date for the week (default: current week start)
            week_end: End date for the week (default: current week end)
            app_name: Name of the app
            
        Returns:
            Path to the saved weekly note file
        """
        try:
            logger.info(f"Starting weekly note generation for {app_name}")
            
            # Get week range
            if not week_start or not week_end:
                week_start, week_end = self._get_current_week_range()
            
            # Load latest themes and classified reviews
            latest_themes_file = self.theme_service.get_latest_themes_file()
            if not latest_themes_file:
                raise ValueError("No themes file found. Run Phase 2a first.")
            
            latest_classified_file = self.classification_service.get_latest_grouped_reviews_file()
            if not latest_classified_file:
                raise ValueError("No classified reviews file found. Run Phase 2b first.")
            
            logger.info(f"Loaded {len(latest_themes_file.themes)} themes and {len(latest_classified_file.byTheme)} theme groups")
            
            # Generate weekly note
            note_file = self._generate_weekly_note(
                themes=latest_themes_file.themes,
                grouped_reviews=latest_classified_file.byTheme,
                week_start=week_start,
                week_end=week_end,
                app_name=app_name
            )
            
            logger.info(f"Successfully generated and saved weekly note")
            return note_file
            
        except Exception as e:
            logger.error(f"Weekly note generation failed: {str(e)}")
            raise
    
    def _generate_weekly_note(
        self,
        themes: List[Dict[str, Any]],
        grouped_reviews: Dict[str, List[Dict[str, Any]]],
        week_start: date,
        week_end: date,
        app_name: str
    ) -> str:
        """Generate weekly note and save to files"""
        try:
            # Generate content using Gemini
            start_time = time.time()
            
            generated_content = self.gemini_service.generate_weekly_note(
                themes=themes,
                grouped_reviews=grouped_reviews,
                app_name=app_name,
                week_start=week_start.strftime("%B %d"),
                week_end=week_end.strftime("%B %d")
            )
            
            processing_time = time.time() - start_time
            
            # Sanitize content: remove star ratings from quotes (per ARCHITECTURE.md)
            generated_content['content'] = self._strip_star_ratings_from_content(generated_content['content'])
            
            # Create structured report
            report = WeeklyReport(
                id=f"weekly-{app_name.lower()}-{week_start.strftime('%Y%m%d')}",
                week_start=week_start,
                week_end=week_end,
                app_id="indmoney",
                app_name=app_name,
                themes=[theme.dict() if hasattr(theme, 'dict') else theme for theme in generated_content['structured_themes']],
                quotes=generated_content['structured_quotes'],
                actions=generated_content['structured_actions'],
                word_count=generated_content['word_count'],
                generated_at=datetime.now()
            )
            
            # Create report file structure
            report_file = WeeklyReportFile(
                generatedAt=datetime.now(),
                appId="indmoney",
                appName=app_name,
                weekStart=week_start,
                weekEnd=week_end,
                report=report,
                metadata={
                    "processing_time": processing_time,
                    "themes_count": len(themes),
                    "total_reviews": sum(len(reviews) for reviews in grouped_reviews.values())
                }
            )
            
            # Save files
            json_filepath = self._save_weekly_note_json(report_file)
            markdown_filepath = self._save_weekly_note_markdown(generated_content['content'], week_start)
            text_filepath = self._save_weekly_note_text(generated_content['content'], week_start)
            
            logger.info(f"Weekly note saved to: {markdown_filepath}")
            return markdown_filepath
            
        except Exception as e:
            logger.error(f"Failed to generate weekly note: {str(e)}")
            raise
    
    def _strip_star_ratings_from_content(self, content: str) -> str:
        """Remove star rating annotations from content (per ARCHITECTURE: no ⭐★☆ in output)"""
        if not content:
            return content
        return STAR_RATING_PATTERN.sub('', content)
    
    def _save_weekly_note_json(self, report_file: WeeklyReportFile) -> str:
        """Save weekly note as JSON file"""
        try:
            # Generate filename
            filename = f"weekly_pulse-{report_file.weekStart.strftime('%Y-%m-%d')}.json"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            # Convert to dictionary and save
            data = report_file.dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Weekly note JSON saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save weekly note JSON: {str(e)}")
            raise
    
    def _save_weekly_note_markdown(self, content: str, week_start: date) -> str:
        """Save weekly note as Markdown file"""
        try:
            # Generate filename
            filename = f"pulse-{week_start.strftime('%Y-%m-%d')}.md"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            # Save content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Weekly note Markdown saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save weekly note Markdown: {str(e)}")
            raise
    
    def _save_weekly_note_text(self, content: str, week_start: date) -> str:
        """Save weekly note as plain text file"""
        try:
            # Generate filename
            filename = f"pulse-{week_start.strftime('%Y-%m-%d')}.txt"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            # Convert markdown to plain text (simple conversion)
            text_content = content.replace('##', '').replace('###', '').replace('**', '').replace('*', '')
            
            # Save content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"Weekly note text saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save weekly note text: {str(e)}")
            raise
    
    def load_weekly_note_file(self, date_str: str) -> Optional[WeeklyReportFile]:
        """
        Load weekly note file for a specific date
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            WeeklyReportFile object or None if file not found
        """
        try:
            filename = f"weekly_pulse-{date_str}.json"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return WeeklyReportFile(**data)
            
        except Exception as e:
            logger.error(f"Error loading weekly note file for {date_str}: {str(e)}")
            return None
    
    def get_latest_weekly_note_file(self) -> Optional[WeeklyReportFile]:
        """Get the latest weekly note file"""
        try:
            reports_dir = Path(self.config.REPORTS_DIR)
            
            if not reports_dir.exists():
                return None
            
            # Find weekly note files
            weekly_files = [f for f in reports_dir.glob("weekly_pulse-*.json")]
            
            if not weekly_files:
                return None
            
            # Sort by filename (date) to get the latest
            latest_file = sorted(weekly_files)[-1]
            date_str = latest_file.stem.replace("weekly_pulse-", "")
            
            return self.load_weekly_note_file(date_str)
            
        except Exception as e:
            logger.error(f"Error getting latest weekly note file: {str(e)}")
            return None
    
    def list_weekly_note_files(self) -> List[str]:
        """List all weekly note files"""
        try:
            reports_dir = Path(self.config.REPORTS_DIR)
            
            if not reports_dir.exists():
                return []
            
            weekly_files = [f.name for f in reports_dir.glob("weekly_pulse-*.json")]
            
            # Return sorted list (newest first)
            return sorted(weekly_files, reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing weekly note files: {str(e)}")
            return []
    
    def get_weekly_note_stats(self) -> Dict:
        """Get weekly note statistics"""
        try:
            latest_note = self.get_latest_weekly_note_file()
            
            if not latest_note:
                return {
                    "app_id": "indmoney",
                    "latest_file": None,
                    "total_notes": 0,
                    "word_count": 0,
                    "generated_at": None
                }
            
            return {
                "app_id": latest_note.appId,
                "latest_file": f"weekly_pulse-{latest_note.weekStart.strftime('%Y-%m-%d')}.json",
                "total_notes": len(self.list_weekly_note_files()),
                "word_count": latest_note.report.word_count,
                "generated_at": latest_note.generatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting weekly note stats: {str(e)}")
            return {"error": str(e)}
    
    def _get_current_week_range(self) -> tuple[date, date]:
        """Get current week date range"""
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday
        
        return start_of_week, end_of_week
