"""
Data ingestion service for Phase 1
"""
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from src.models.review import ReviewsFile
from src.services.scraper_service import ScraperService
from src.config.settings import Config

logger = logging.getLogger(__name__)

class DataIngestionService:
    """Service for data ingestion and persistence"""
    
    def __init__(self):
        self.config = Config()
        self.scraper_service = ScraperService()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.config.REVIEWS_DIR, exist_ok=True)
        os.makedirs(self.config.REPORTS_DIR, exist_ok=True)
        os.makedirs(self.config.LOGS_DIR, exist_ok=True)
    
    def ingest_reviews(
        self, 
        weeks: int = 8,
        max_count: int = 100
    ) -> str:
        """
        Ingest reviews for INDMoney
        
        Args:
            weeks: Number of weeks to look back
            max_count: Maximum number of reviews to fetch
            
        Returns:
            Path to the created JSON file
        """
        try:
            logger.info(f"Starting ingestion for INDMoney with {weeks} weeks")
            
            # Validate parameters
            if not self.config.validate_weeks(weeks):
                raise ValueError(f"Weeks must be between {self.config.MIN_WEEKS} and {self.config.MAX_WEEKS}")
            
            # Get app configuration
            app_config = self.config.get_app_config()
            if not app_config:
                raise ValueError("App configuration not found")
            
            # Process reviews
            processed_reviews = self.scraper_service.process_reviews(weeks, max_count)
            
            # Create reviews file structure
            reviews_file = ReviewsFile(
                scrapedAt=datetime.now(),
                packageId=app_config.package_id,
                appId="indmoney",
                weeksRequested=weeks,
                reviews=processed_reviews
            )
            
            # Generate file path
            filename = self._generate_filename()
            filepath = os.path.join(self.config.REVIEWS_DIR, filename)
            
            # Save to file
            self._save_reviews_file(reviews_file, filepath)
            
            logger.info(f"Successfully saved {len(processed_reviews)} reviews to {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
            raise
    
    def _generate_filename(self) -> str:
        """Generate filename for reviews file"""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"{today}.json"
    
    def _save_reviews_file(self, reviews_file: ReviewsFile, filepath: str):
        """Save reviews file to disk"""
        try:
            # Convert to dictionary
            data = reviews_file.dict()
            
            # Save as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving reviews file to {filepath}: {str(e)}")
            raise
    
    def load_reviews_file(self, date_str: str) -> Optional[ReviewsFile]:
        """
        Load reviews file for a specific date
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            ReviewsFile object or None if file not found
        """
        try:
            filepath = os.path.join(self.config.REVIEWS_DIR, f"{date_str}.json")
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ReviewsFile(**data)
            
        except Exception as e:
            logger.error(f"Error loading reviews file for {date_str}: {str(e)}")
            return None
    
    def get_latest_reviews_file(self) -> Optional[ReviewsFile]:
        """Get the latest reviews file"""
        try:
            if not os.path.exists(self.config.REVIEWS_DIR):
                return None
            
            # Find the most recent JSON file
            json_files = [f for f in os.listdir(self.config.REVIEWS_DIR) if f.endswith('.json')]
            
            if not json_files:
                return None
            
            # Sort by filename (date) to get the latest
            latest_file = sorted(json_files)[-1]
            date_str = latest_file.replace('.json', '')
            
            return self.load_reviews_file(date_str)
            
        except Exception as e:
            logger.error(f"Error getting latest reviews file: {str(e)}")
            return None
    
    def list_reviews_files(self) -> List[str]:
        """List all reviews files"""
        try:
            if not os.path.exists(self.config.REVIEWS_DIR):
                return []
            
            json_files = [f for f in os.listdir(self.config.REVIEWS_DIR) if f.endswith('.json')]
            
            # Return sorted list (newest first)
            return sorted(json_files, reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing reviews files: {str(e)}")
            return []
    
    def get_ingestion_stats(self) -> Dict:
        """Get ingestion statistics for INDMoney"""
        try:
            latest_file = self.get_latest_reviews_file()
            
            if not latest_file:
                return {
                    "app_id": "indmoney",
                    "latest_file": None,
                    "total_reviews": 0,
                    "weeks_requested": 0,
                    "last_scraped": None
                }
            
            return {
                "app_id": "indmoney",
                "latest_file": os.path.basename(self._generate_filename()),
                "total_reviews": len(latest_file.reviews),
                "weeks_requested": latest_file.weeksRequested,
                "last_scraped": latest_file.scrapedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting ingestion stats: {str(e)}")
            return {"error": str(e)}
