"""
Mock Groq service for testing Phase 2a without API calls
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from src.models.theme import ThemeModel, ThemeDiscoveryRequest, ThemeDiscoveryResponse
from src.config.settings import Config
from src.config.prompts import THEME_DISCOVERY_PROMPT, THEME_DISCOVERY_RETRY_PROMPT, THEME_DISCOVERY_SYSTEM_MESSAGE

logger = logging.getLogger(__name__)

class GroqService:
    """Mock service for Phase 2a: Theme Discovery (for testing without API)"""
    
    def __init__(self):
        self.config = Config()
        logger.info("Mock Groq service initialized (for testing)")
    
    def discover_themes(
        self, 
        reviews: List[Dict[str, Any]], 
        app_name: str = "INDMoney",
        sample_size: int = 150,
        max_retries: int = 2
    ) -> ThemeDiscoveryResponse:
        """
        Mock theme discovery from reviews
        
        Args:
            reviews: List of review dictionaries
            app_name: Name of the app for context
            sample_size: Number of reviews to sample for analysis
            max_retries: Maximum number of retry attempts
            
        Returns:
            ThemeDiscoveryResponse with discovered themes
        """
        try:
            logger.info(f"Starting mock theme discovery for {app_name} with {len(reviews)} reviews")
            
            # Sample reviews
            sampled_reviews = self._sample_reviews(reviews, sample_size)
            
            # Generate mock themes based on common app review patterns
            themes = self._generate_mock_themes(app_name, len(sampled_reviews))
            
            # Create response
            response = ThemeDiscoveryResponse(
                themes=themes,
                sample_size=len(sampled_reviews),
                app_name=app_name
            )
            
            logger.info(f"Successfully generated {len(themes)} mock themes")
            return response
            
        except Exception as e:
            logger.error(f"Mock theme discovery failed: {str(e)}")
            raise
    
    def _sample_reviews(self, reviews: List[Dict[str, Any]], sample_size: int) -> List[Dict[str, Any]]:
        """Sample reviews stratified by rating"""
        if len(reviews) <= sample_size:
            return reviews
        
        # Group reviews by rating
        reviews_by_rating = {}
        for review in reviews:
            rating = review.get('rating', 1)
            if rating not in reviews_by_rating:
                reviews_by_rating[rating] = []
            reviews_by_rating[rating].append(review)
        
        # Calculate sample size per rating (stratified sampling)
        sampled_reviews = []
        remaining_sample = sample_size
        
        for rating in sorted(reviews_by_rating.keys(), reverse=True):  # Start with higher ratings
            rating_reviews = reviews_by_rating[rating]
            rating_count = len(rating_reviews)
            rating_proportion = rating_count / len(reviews)
            
            # Calculate how many to sample from this rating
            if rating == 5:  # Ensure we get some 5-star reviews
                rating_sample_size = max(5, int(sample_size * rating_proportion))
            else:
                rating_sample_size = int(sample_size * rating_proportion)
            
            # Don't exceed available reviews or remaining sample
            rating_sample_size = min(rating_sample_size, rating_count, remaining_sample)
            
            # Sample reviews from this rating
            if rating_sample_size > 0:
                import random
                sampled = random.sample(rating_reviews, rating_sample_size)
                sampled_reviews.extend(sampled)
                remaining_sample -= rating_sample_size
        
        # If we still have room, add more reviews from the largest group
        if remaining_sample > 0:
            largest_rating = max(reviews_by_rating.keys(), key=lambda k: len(reviews_by_rating[k]))
            additional_reviews = reviews_by_rating[largest_rating][:remaining_sample]
            sampled_reviews.extend(additional_reviews)
        
        logger.info(f"Sampled {len(sampled_reviews)} reviews stratified by rating")
        return sampled_reviews[:sample_size]
    
    def _generate_mock_themes(self, app_name: str, review_count: int) -> List[ThemeModel]:
        """Generate mock themes based on common app review patterns"""
        
        # Common themes for financial/trading apps
        mock_themes = [
            {
                "id": "app_performance",
                "label": "App Performance Issues",
                "description": "Users experiencing slow loading, crashes, and bugs"
            },
            {
                "id": "ui_ux_problems",
                "label": "UI/UX Navigation Issues",
                "description": "Difficulty finding features, confusing interface design"
            },
            {
                "id": "customer_service",
                "label": "Customer Support Response",
                "description": "Issues with ticket resolution and support responsiveness"
            },
            {
                "id": "trading_features",
                "label": "Trading Functionality",
                "description": "Problems with order execution, charts, and trading tools"
            },
            {
                "id": "account_management",
                "label": "Account & Banking Issues",
                "description": "Problems with account setup, bank linking, and fund management"
            }
        ]
        
        # Select 3-5 themes randomly
        import random
        selected_themes = random.sample(mock_themes, random.randint(3, 5))
        
        # Convert to ThemeModel objects
        theme_models = []
        for theme_data in selected_themes:
            theme = ThemeModel(**theme_data)
            theme_models.append(theme)
        
        return theme_models

