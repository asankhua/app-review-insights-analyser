"""
Phase 2a Theme Discovery Service
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.models.theme import ThemeModel, ThemeFile
from src.services.groq_service import GroqService
from src.services.data_ingestion import DataIngestionService
from src.config.settings import Config

logger = logging.getLogger(__name__)

class ThemeDiscoveryService:
    """Service for Phase 2a: Theme Discovery"""
    
    def __init__(self):
        self.config = Config()
        self.groq_service = GroqService()
        self.data_ingestion = DataIngestionService()
        
        # Ensure reports directory exists
        Path(self.config.REPORTS_DIR).mkdir(exist_ok=True)
    
    def discover_themes_from_latest_reviews(
        self,
        sample_size: int = 150,
        app_name: str = "INDMoney"
    ) -> str:
        """
        Discover themes from the latest reviews file
        
        Args:
            sample_size: Number of reviews to sample for analysis
            app_name: Name of the app
            
        Returns:
            Path to the saved themes file
        """
        try:
            logger.info(f"Starting theme discovery for {app_name}")
            
            # Load latest reviews
            latest_reviews_file = self.data_ingestion.get_latest_reviews_file()
            if not latest_reviews_file:
                raise ValueError("No reviews file found. Run Phase 1 first.")
            
            logger.info(f"Loaded {len(latest_reviews_file.reviews)} reviews from {latest_reviews_file.scrapedAt}")
            
            # Discover themes using Groq
            theme_response = self.groq_service.discover_themes(
                reviews=latest_reviews_file.reviews,
                app_name=app_name,
                sample_size=sample_size
            )
            
            # Create theme file structure
            theme_file = ThemeFile(
                generatedAt=datetime.now(),
                appId=latest_reviews_file.appId,
                packageId=latest_reviews_file.packageId,
                themes=theme_response.themes,
                sampleSize=theme_response.sample_size,
                weeksRequested=latest_reviews_file.weeksRequested
            )
            
            # Save themes to file
            themes_filepath = self._save_themes_file(theme_file)
            
            logger.info(f"Successfully discovered and saved {len(theme_response.themes)} themes")
            return themes_filepath
            
        except Exception as e:
            logger.error(f"Theme discovery failed: {str(e)}")
            raise
    
    def discover_themes_from_file(
        self,
        reviews_file_path: str,
        sample_size: int = 150,
        app_name: str = "INDMoney"
    ) -> str:
        """
        Discover themes from a specific reviews file
        
        Args:
            reviews_file_path: Path to the reviews JSON file
            sample_size: Number of reviews to sample for analysis
            app_name: Name of the app
            
        Returns:
            Path to the saved themes file
        """
        try:
            logger.info(f"Starting theme discovery from file: {reviews_file_path}")
            
            # Load reviews from file
            with open(reviews_file_path, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
            
            reviews = reviews_data.get('reviews', [])
            if not reviews:
                raise ValueError(f"No reviews found in file: {reviews_file_path}")
            
            logger.info(f"Loaded {len(reviews)} reviews from file")
            
            # Discover themes using Groq
            theme_response = self.groq_service.discover_themes(
                reviews=reviews,
                app_name=app_name,
                sample_size=sample_size
            )
            
            # Create theme file structure
            theme_file = ThemeFile(
                generatedAt=datetime.now(),
                appId=reviews_data.get('appId', 'indmoney'),
                packageId=reviews_data.get('packageId', 'in.indwealth'),
                themes=theme_response.themes,
                sampleSize=theme_response.sample_size,
                weeksRequested=reviews_data.get('weeksRequested', 8)
            )
            
            # Save themes to file
            themes_filepath = self._save_themes_file(theme_file)
            
            logger.info(f"Successfully discovered and saved {len(theme_response.themes)} themes")
            return themes_filepath
            
        except Exception as e:
            logger.error(f"Theme discovery from file failed: {str(e)}")
            raise
    
    def _save_themes_file(self, theme_file: ThemeFile) -> str:
        """Save themes to file"""
        try:
            # Generate filename
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"themes-{today}.json"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            # Convert to dictionary and save
            data = theme_file.dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Themes saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save themes file: {str(e)}")
            raise
    
    def load_themes_file(self, date_str: str) -> Optional[ThemeFile]:
        """
        Load themes file for a specific date
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            ThemeFile object or None if file not found
        """
        try:
            filename = f"themes-{date_str}.json"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ThemeFile(**data)
            
        except Exception as e:
            logger.error(f"Error loading themes file for {date_str}: {str(e)}")
            return None
    
    def get_latest_themes_file(self) -> Optional[ThemeFile]:
        """Get the latest themes file"""
        try:
            reports_dir = Path(self.config.REPORTS_DIR)
            
            if not reports_dir.exists():
                return None
            
            # Find theme files
            theme_files = [f for f in reports_dir.glob("themes-*.json")]
            
            if not theme_files:
                return None
            
            # Sort by filename (date) to get the latest
            latest_file = sorted(theme_files)[-1]
            date_str = latest_file.stem.replace("themes-", "")
            
            return self.load_themes_file(date_str)
            
        except Exception as e:
            logger.error(f"Error getting latest themes file: {str(e)}")
            return None
    
    def list_themes_files(self) -> List[str]:
        """List all themes files"""
        try:
            reports_dir = Path(self.config.REPORTS_DIR)
            
            if not reports_dir.exists():
                return []
            
            theme_files = [f.name for f in reports_dir.glob("themes-*.json")]
            
            # Return sorted list (newest first)
            return sorted(theme_files, reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing themes files: {str(e)}")
            return []
    
    def get_themes_stats(self) -> Dict:
        """Get themes statistics"""
        try:
            latest_themes = self.get_latest_themes_file()
            
            if not latest_themes:
                return {
                    "app_id": "indmoney",
                    "latest_file": None,
                    "total_themes": 0,
                    "sample_size": 0,
                    "generated_at": None
                }
            
            return {
                "app_id": latest_themes.appId,
                "latest_file": f"themes-{latest_themes.generatedAt.strftime('%Y-%m-%d')}.json",
                "total_themes": len(latest_themes.themes),
                "sample_size": latest_themes.sampleSize,
                "generated_at": latest_themes.generatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting themes stats: {str(e)}")
            return {"error": str(e)}
