"""
Google Play Store scraper service for Phase 1
"""
import logging
from datetime import datetime
from typing import List, Optional
from google_play_scraper import Sort, reviews, app
from src.models.review import ScrapedReview, AppInfo
from src.config.settings import Config
from src.utils.validators import ReviewTransformer

logger = logging.getLogger(__name__)

class ScraperService:
    """Service for scraping Google Play Store reviews"""
    
    def __init__(self):
        self.config = Config()
    
    def scrape_reviews(
        self, 
        app_info: AppInfo, 
        weeks: int = 8,
        max_count: int = 100
    ) -> List[ScrapedReview]:
        """
        Scrape reviews from Google Play Store
        
        Args:
            app_info: App information (package_id, app_name, etc.)
            weeks: Number of weeks to look back
            max_count: Maximum number of reviews to fetch (limited to 100)
            
        Returns:
            List of scraped reviews
        """
        try:
            logger.info(f"Starting to scrape reviews for {app_info.app_name} ({app_info.package_id})")
            
            # Validate input parameters
            if not self.config.validate_weeks(weeks):
                raise ValueError(f"Weeks must be between {self.config.MIN_WEEKS} and {self.config.MAX_WEEKS}")
            
            # Scrape reviews using google-play-scraper
            result, continuation_token = reviews(
                app_info.package_id,
                lang=app_info.lang,
                country=app_info.country,
                sort=Sort.NEWEST,
                count=max_count,
                filter_score_with=self.config.SCRAPER_CONFIG["rating_filter"]
            )
            
            logger.info(f"Successfully scraped {len(result)} reviews from Google Play Store")
            
            # Convert to ScrapedReview objects
            scraped_reviews = []
            for review_data in result:
                scraped_review = ScrapedReview(
                    reviewId=review_data.get('reviewId', ''),
                    userName=review_data.get('userName'),
                    userImage=review_data.get('userImage'),
                    content=review_data.get('content', ''),
                    score=review_data.get('score', 1),
                    thumbsUpCount=review_data.get('thumbsUpCount', 0),
                    reviewCreatedVersion=review_data.get('reviewCreatedVersion'),
                    at=review_data.get('at', datetime.now()),
                    replyContent=review_data.get('replyContent'),
                    repliedAt=review_data.get('repliedAt')
                )
                scraped_reviews.append(scraped_review)
            
            return scraped_reviews
            
        except Exception as e:
            logger.error(f"Error scraping reviews for {app_info.package_id}: {str(e)}")
            raise
    
    def get_app_info(self) -> AppInfo:
        """Get INDMoney app information"""
        app_config = self.config.get_app_config()
        if not app_config:
            raise ValueError("App configuration not found")
        
        return AppInfo(
            package_id=app_config.package_id,
            app_name=app_config.app_name,
            lang=app_config.lang,
            country=app_config.country
        )
    
    def process_reviews(
        self, 
        weeks: int = 8,
        max_count: int = 100
    ) -> List[dict]:
        """
        Process reviews: scrape, filter, and transform for INDMoney
        
        Args:
            weeks: Number of weeks to look back
            max_count: Maximum number of reviews to fetch
            
        Returns:
            List of processed review dictionaries
        """
        try:
            # Get app information
            app_info = self.get_app_info()
            
            # Scrape reviews
            scraped_reviews = self.scrape_reviews(app_info, weeks, max_count)
            
            # Transform and filter reviews
            processed_reviews = ReviewTransformer.transform_valid_reviews(
                scraped_reviews, weeks, self.config.MIN_WORDS
            )
            
            logger.info(f"Processed {len(processed_reviews)} valid reviews out of {len(scraped_reviews)} scraped")
            
            # Convert to dictionaries
            return [review.to_dict() for review in processed_reviews]
            
        except Exception as e:
            logger.error(f"Error processing reviews for INDMoney: {str(e)}")
            raise
    
    def get_app_details(self, package_id: str) -> dict:
        """Get app details from Google Play Store"""
        try:
            app_details = app(
                package_id,
                lang='en',
                country='in'
            )
            return app_details
        except Exception as e:
            logger.error(f"Error getting app details for {package_id}: {str(e)}")
            return {}

