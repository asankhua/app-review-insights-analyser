"""
Groq LLM service for Phase 2a Theme Discovery
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from groq import Groq
from src.models.theme import ThemeModel, ThemeDiscoveryRequest, ThemeDiscoveryResponse
from src.config.settings import Config
from src.config.prompts import THEME_DISCOVERY_PROMPT, THEME_DISCOVERY_RETRY_PROMPT, THEME_DISCOVERY_SYSTEM_MESSAGE

logger = logging.getLogger(__name__)

class GroqService:
    """Service for interacting with Groq LLM API"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Groq client"""
        try:
            api_key = self.config.GROQ_API_KEY
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required")
            
            self.client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            raise
    
    def discover_themes(
        self, 
        reviews: List[Dict[str, Any]], 
        app_name: str = "INDMoney",
        sample_size: int = 150,
        max_retries: int = 2
    ) -> ThemeDiscoveryResponse:
        """
        Discover themes from reviews using Groq LLM
        
        Args:
            reviews: List of review dictionaries
            app_name: Name of the app for context
            sample_size: Number of reviews to sample for analysis
            max_retries: Maximum number of retry attempts
            
        Returns:
            ThemeDiscoveryResponse with discovered themes
        """
        try:
            logger.info(f"Starting theme discovery for {app_name} with {len(reviews)} reviews")
            
            # Sample reviews
            sampled_reviews = self._sample_reviews(reviews, sample_size)
            reviews_text = self._format_reviews_for_prompt(sampled_reviews)
            
            # Generate themes with retry logic
            themes = self._generate_themes_with_retry(
                reviews_text, app_name, max_retries
            )
            
            # Create response
            response = ThemeDiscoveryResponse(
                themes=themes,
                sample_size=len(sampled_reviews),
                app_name=app_name
            )
            
            logger.info(f"Successfully discovered {len(themes)} themes")
            return response
            
        except Exception as e:
            logger.error(f"Theme discovery failed: {str(e)}")
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
    
    def _format_reviews_for_prompt(self, reviews: List[Dict[str, Any]]) -> str:
        """Format reviews for the LLM prompt"""
        formatted_reviews = []
        
        for i, review in enumerate(reviews[:150], 1):  # Limit to 150 for prompt length
            rating = review.get('rating', 1)
            text = review.get('text', '').strip()
            date = review.get('date', '')
            
            # Format each review
            review_text = f"{i}. Rating: {rating}/5 - \"{text}\""
            if date:
                review_text += f" (Date: {date})"
            
            formatted_reviews.append(review_text)
        
        return "\n".join(formatted_reviews)
    
    def _generate_themes_with_retry(
        self, 
        reviews_text: str, 
        app_name: str, 
        max_retries: int
    ) -> List[ThemeModel]:
        """Generate themes with retry logic"""
        
        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    prompt = THEME_DISCOVERY_PROMPT.format(
                        app_name=app_name,
                        reviews_text=reviews_text
                    )
                else:
                    prompt = THEME_DISCOVERY_RETRY_PROMPT.format(
                        app_name=app_name,
                        reviews_text=reviews_text
                    )
                
                logger.info(f"Attempt {attempt + 1}: Calling Groq API")
                
                # Call Groq API
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": THEME_DISCOVERY_SYSTEM_MESSAGE},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                # Parse response
                content = response.choices[0].message.content.strip()
                themes = self._parse_theme_response(content)
                
                # Validate themes
                if 3 <= len(themes) <= 5:
                    logger.info(f"Successfully generated {len(themes)} themes on attempt {attempt + 1}")
                    return themes
                else:
                    raise ValueError(f"Invalid number of themes: {len(themes)} (must be 3-5)")
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise
                time.sleep(1)  # Wait before retry
                
            except Exception as e:
                logger.warning(f"Theme generation failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Failed to generate themes after all retries")
    
    def _parse_theme_response(self, content: str) -> List[ThemeModel]:
        """Parse theme response from LLM"""
        try:
            # Clean up the response
            content = content.strip()
            
            # Remove any markdown code blocks
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            themes_data = json.loads(content)
            
            # Validate and create theme models
            themes = []
            for theme_data in themes_data:
                theme = ThemeModel(**theme_data)
                themes.append(theme)
            
            return themes
            
        except Exception as e:
            logger.error(f"Failed to parse theme response: {str(e)}")
            logger.error(f"Raw content: {content}")
            raise
