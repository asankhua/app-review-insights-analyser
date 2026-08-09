"""
Groq LLM service for Phase 2b Review Classification
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from groq import Groq
from .models.classification import ReviewClassificationRequest, ReviewClassificationResponse
from .config.classification_prompts import (
    REVIEW_CLASSIFICATION_PROMPT, 
    REVIEW_CLASSIFICATION_RETRY_PROMPT, 
    REVIEW_CLASSIFICATION_SYSTEM_MESSAGE
)
from src.config.settings import Config
from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class GroqClassificationService:
    """Service for review classification using Groq LLM"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.cache = CacheService()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Groq client (lazy - only when API is called)"""
        if self.client is not None:
            return
        api_key = self.config.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        logger.info("Groq classification client initialized successfully")
    
    def classify_review(
        self, 
        review: Dict[str, Any], 
        themes: List[Dict[str, Any]], 
        max_retries: int = 2,
        use_cache: bool = True
    ) -> ReviewClassificationResponse:
        """
        Classify a single review into themes
        
        Args:
            review: Review dictionary
            themes: List of available themes
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use cached results
            
        Returns:
            ReviewClassificationResponse with classification result
        """
        try:
            # Generate cache key based on review text and themes
            cache_key = self.cache._get_cache_key({
                'review_text': review.get('text', ''),
                'themes': [t.get('id', '') for t in themes]
            })
            
            # Try to get from cache
            if use_cache:
                cached_result = self.cache.get(cache_key, 'classification')
                if cached_result:
                    logger.debug(f"Using cached classification for review {review.get('reviewId', 'unknown')}")
                    return ReviewClassificationResponse(**cached_result)
            
            themes_list = self._format_themes_for_prompt(themes)
            
            # Generate classification with retry logic
            classification = self._classify_with_retry(
                review_text=review.get('text', ''),
                rating=review.get('rating', 1),
                themes_list=themes_list,
                app_name="INDMoney",
                max_retries=max_retries
            )
            
            # Cache the result
            if use_cache:
                self.cache.set(cache_key, 'classification', classification.dict())
            
            return classification
            
        except Exception as e:
            logger.error(f"Review classification failed: {str(e)}")
            raise
    
    def classify_reviews_batch(
        self, 
        reviews: List[Dict[str, Any]], 
        themes: List[Dict[str, Any]], 
        batch_size: int = 20,  
        delay_between_batches: float = 1.0,  
        max_retries: int = 2,
        use_cache: bool = True,
        app_name: str = "INDMoney"
    ) -> List[ReviewClassificationResponse]:
        """
        Classify multiple reviews in batches with caching
        
        Args:
            reviews: List of review dictionaries
            themes: List of available themes
            batch_size: Number of reviews per batch
            delay_between_batches: Delay between batches in seconds
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use cached results
            
        Returns:
            List of ReviewClassificationResponse objects
        """
        try:
            self._initialize_client()
            logger.info(f"Starting batch classification for {len(reviews)} reviews")
            
            classifications = []
            total_batches = (len(reviews) + batch_size - 1) // batch_size
            
            for i in range(0, len(reviews), batch_size):
                batch_reviews = reviews[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_reviews)} reviews)")
                
                # Process each review in the batch
                for review in batch_reviews:
                    try:
                        classification = self.classify_review(
                            review, themes, max_retries, use_cache
                        )
                        classifications.append(classification)
                        
                    except Exception as e:
                        logger.error(f"Failed to classify review {review.get('reviewId', 'unknown')}: {str(e)}")
                        # Add unclassified review
                        classifications.append(ReviewClassificationResponse(
                            themeId="unclassified",
                            confidence=0.0,
                            reasoning="Classification failed"
                        ))
                
                # Add delay between batches to avoid rate limits
                if i + batch_size < len(reviews):  # Don't delay after last batch
                    logger.info(f"Waiting {delay_between_batches}s before next batch...")
                    time.sleep(delay_between_batches)
            
            logger.info(f"Successfully classified {len(classifications)} reviews")
            return classifications
            
        except Exception as e:
            logger.error(f"Batch classification failed: {str(e)}")
            raise
    
    def _format_themes_for_prompt(self, themes: List[Dict[str, Any]]) -> str:
        """Format themes for the classification prompt"""
        themes_list = []
        
        for theme in themes:
            theme_id = theme.get('id', '')
            label = theme.get('label', '')
            description = theme.get('description', '')
            
            theme_text = f"- {theme_id}: {label} - {description}"
            themes_list.append(theme_text)
        
        return "\n".join(themes_list)
    
    def _classify_with_retry(
        self, 
        review_text: str, 
        rating: int, 
        themes_list: str, 
        app_name: str, 
        max_retries: int
    ) -> ReviewClassificationResponse:
        """Classify review with retry logic. Uses fallback model on 429 rate limit."""
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        last_error = None
        
        for model in models:
            for attempt in range(max_retries + 1):
                try:
                    prompt = REVIEW_CLASSIFICATION_PROMPT.format(
                        app_name=app_name,
                        themes_list=themes_list,
                        rating=rating,
                        review_text=review_text
                    ) if attempt == 0 else REVIEW_CLASSIFICATION_RETRY_PROMPT.format(
                        app_name=app_name,
                        themes_list=themes_list,
                        rating=rating,
                        review_text=review_text
                    )
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": REVIEW_CLASSIFICATION_SYSTEM_MESSAGE},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=200
                    )
                    content = response.choices[0].message.content.strip()
                    return self._parse_classification_response(content, themes_list)
                except json.JSONDecodeError as e:
                    last_error = e
                    if attempt < max_retries:
                        time.sleep(0.5)
                    elif model == models[-1]:
                        raise
                    else:
                        break
                except Exception as e:
                    last_error = e
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        if model != models[-1]:
                            logger.warning(f"Rate limit on {model}, trying llama-3.1-8b-instant")
                            break
                        raise Exception(
                            "Groq rate limit reached. Wait ~12 min or use 'Use sample data'."
                        ) from e
                    if attempt < max_retries:
                        time.sleep(1)
                    elif model == models[-1]:
                        raise
                    else:
                        break
        raise Exception("Classification failed") from last_error
    
    def _parse_classification_response(self, content: str, themes_list: str) -> ReviewClassificationResponse:
        """Parse classification response from LLM"""
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
            classification_data = json.loads(content)
            
            # Validate and create classification response
            classification = ReviewClassificationResponse(**classification_data)
            
            # Validate confidence range
            if not (0.0 <= classification.confidence <= 1.0):
                logger.warning(f"Confidence {classification.confidence} out of range, clamping to [0,1]")
                classification.confidence = max(0.0, min(1.0, classification.confidence))
            
            return classification
            
        except Exception as e:
            logger.error(f"Failed to parse classification response: {str(e)}")
            logger.error(f"Raw content: {content}")
            raise

