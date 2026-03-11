"""
Phase 2b Review Classification Service
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.models.classification import GroupedReviewsFile, ClassificationStats
from src.services.classification_service import GroqClassificationService
from src.services.data_ingestion import DataIngestionService
from src.services.theme_discovery import ThemeDiscoveryService
from src.config.settings import Config

logger = logging.getLogger(__name__)

class ReviewClassificationService:
    """Service for Phase 2b: Review Classification"""
    
    def __init__(self):
        self.config = Config()
        self.groq_service = GroqClassificationService()
        self.data_ingestion = DataIngestionService()
        self.theme_service = ThemeDiscoveryService()
        
        # Ensure reports directory exists
        Path(self.config.REPORTS_DIR).mkdir(exist_ok=True)
    
    def classify_reviews_from_latest(
        self,
        batch_size: int = 10,
        app_name: str = "INDMoney"
    ) -> str:
        """
        Classify latest reviews into themes
        
        Args:
            batch_size: Number of reviews to process in each batch
            app_name: Name of the app
            
        Returns:
            Path to the saved grouped reviews file
        """
        try:
            logger.info(f"Starting review classification for {app_name}")
            
            # Load latest reviews and themes
            latest_reviews_file = self.data_ingestion.get_latest_reviews_file()
            if not latest_reviews_file:
                raise ValueError("No reviews file found. Run Phase 1 first.")
            
            latest_themes_file = self.theme_service.get_latest_themes_file()
            if not latest_themes_file:
                raise ValueError("No themes file found. Run Phase 2a first.")
            
            logger.info(f"Loaded {len(latest_reviews_file.reviews)} reviews and {len(latest_themes_file.themes)} themes")
            
            # Classify reviews
            grouped_reviews = self._classify_reviews_batch(
                reviews=latest_reviews_file.reviews,
                themes=[theme.dict() for theme in latest_themes_file.themes],
                batch_size=batch_size,
                app_name=app_name
            )
            
            # Create grouped reviews file structure
            grouped_file = GroupedReviewsFile(
                generatedAt=datetime.now(),
                appId=latest_reviews_file.appId,
                packageId=latest_reviews_file.packageId,
                themes=[theme.dict() for theme in latest_themes_file.themes],
                byTheme=grouped_reviews,
                weeksRequested=latest_reviews_file.weeksRequested,
                totalReviews=len(latest_reviews_file.reviews)
            )
            
            # Save grouped reviews to file
            grouped_filepath = self._save_grouped_reviews_file(grouped_file)
            
            logger.info(f"Successfully classified and saved grouped reviews")
            return grouped_filepath
            
        except Exception as e:
            logger.error(f"Review classification failed: {str(e)}")
            raise
    
    def _classify_reviews_batch(
        self,
        reviews: List[Dict[str, Any]],
        themes: List[Dict[str, Any]],
        batch_size: int,
        app_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Classify reviews and group by theme"""
        try:
            logger.info(f"Classifying {len(reviews)} reviews with batch size {batch_size}")
            
            # Classify all reviews
            classifications = self.groq_service.classify_reviews_batch(
                reviews=reviews,
                themes=themes,
                app_name=app_name,
                batch_size=batch_size
            )
            
            # Group reviews by theme
            grouped_reviews = {}
            
            # Initialize groups for all themes
            for theme in themes:
                grouped_reviews[theme['id']] = []
            
            # Add "unclassified" group
            grouped_reviews['unclassified'] = []
            
            # Group reviews
            for i, review in enumerate(reviews):
                classification = classifications[i]
                
                # Add theme and confidence to review
                review_with_theme = review.copy()
                review_with_theme['themeId'] = classification.themeId
                review_with_theme['confidence'] = classification.confidence
                
                # Group by theme
                theme_id = classification.themeId
                if theme_id in grouped_reviews:
                    grouped_reviews[theme_id].append(review_with_theme)
                else:
                    grouped_reviews['unclassified'].append(review_with_theme)
            
            # Log classification statistics
            self._log_classification_stats(grouped_reviews, len(reviews))
            
            return grouped_reviews
            
        except Exception as e:
            logger.error(f"Batch classification failed: {str(e)}")
            raise
    
    def _log_classification_stats(self, grouped_reviews: Dict[str, List[Dict[str, Any]]], total_reviews: int):
        """Log classification statistics"""
        try:
            classified_count = sum(len(reviews) for theme_id, reviews in grouped_reviews.items() if theme_id != 'unclassified')
            unclassified_count = len(grouped_reviews.get('unclassified', []))
            
            logger.info(f"Classification Results:")
            logger.info(f"  Total reviews: {total_reviews}")
            logger.info(f"  Classified: {classified_count}")
            logger.info(f"  Unclassified: {unclassified_count}")
            
            logger.info("Theme distribution:")
            for theme_id, reviews in grouped_reviews.items():
                if theme_id != 'unclassified':
                    logger.info(f"  {theme_id}: {len(reviews)} reviews")
            
            if unclassified_count > 0:
                logger.info(f"  unclassified: {unclassified_count} reviews")
                
        except Exception as e:
            logger.warning(f"Failed to log classification stats: {str(e)}")
    
    def _save_grouped_reviews_file(self, grouped_file: GroupedReviewsFile) -> str:
        """Save grouped reviews to file"""
        try:
            # Generate filename
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"grouped_reviews-{today}.json"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            # Convert to dictionary and save
            data = grouped_file.dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Grouped reviews saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save grouped reviews file: {str(e)}")
            raise
    
    def load_grouped_reviews_file(self, date_str: str) -> Optional[GroupedReviewsFile]:
        """
        Load grouped reviews file for a specific date
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            GroupedReviewsFile object or None if file not found
        """
        try:
            filename = f"grouped_reviews-{date_str}.json"
            filepath = Path(self.config.REPORTS_DIR) / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return GroupedReviewsFile(**data)
            
        except Exception as e:
            logger.error(f"Error loading grouped reviews file for {date_str}: {str(e)}")
            return None
    
    def get_latest_grouped_reviews_file(self) -> Optional[GroupedReviewsFile]:
        """Get the latest grouped reviews file"""
        try:
            reports_dir = Path(self.config.REPORTS_DIR)
            
            if not reports_dir.exists():
                return None
            
            # Find grouped reviews files
            grouped_files = [f for f in reports_dir.glob("grouped_reviews-*.json")]
            
            if not grouped_files:
                return None
            
            # Sort by filename (date) to get the latest
            latest_file = sorted(grouped_files)[-1]
            date_str = latest_file.stem.replace("grouped_reviews-", "")
            
            return self.load_grouped_reviews_file(date_str)
            
        except Exception as e:
            logger.error(f"Error getting latest grouped reviews file: {str(e)}")
            return None
    
    def list_grouped_reviews_files(self) -> List[str]:
        """List all grouped reviews files"""
        try:
            reports_dir = Path(self.config.REPORTS_DIR)
            
            if not reports_dir.exists():
                return []
            
            grouped_files = [f.name for f in reports_dir.glob("grouped_reviews-*.json")]
            
            # Return sorted list (newest first)
            return sorted(grouped_files, reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing grouped reviews files: {str(e)}")
            return []
    
    def get_classification_stats(self) -> Dict:
        """Get classification statistics"""
        try:
            latest_grouped = self.get_latest_grouped_reviews_file()
            
            if not latest_grouped:
                return {
                    "app_id": "indmoney",
                    "latest_file": None,
                    "total_reviews": 0,
                    "classified_reviews": 0,
                    "theme_distribution": {},
                    "generated_at": None
                }
            
            # Calculate statistics
            theme_distribution = {}
            classified_count = 0
            
            for theme_id, reviews in latest_grouped.byTheme.items():
                if theme_id != 'unclassified':
                    theme_distribution[theme_id] = len(reviews)
                    classified_count += len(reviews)
            
            return {
                "app_id": latest_grouped.appId,
                "latest_file": f"grouped_reviews-{latest_grouped.generatedAt.strftime('%Y-%m-%d')}.json",
                "total_reviews": latest_grouped.totalReviews,
                "classified_reviews": classified_count,
                "theme_distribution": theme_distribution,
                "generated_at": latest_grouped.generatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting classification stats: {str(e)}")
            return {"error": str(e)}
