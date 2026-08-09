"""
Groq LLM service for Phase 2b Review Classification
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from groq import Groq
from src.models.classification import ReviewClassificationRequest, ReviewClassificationResponse
from src.config.settings import Config
from src.config.classification_prompts import (
    REVIEW_CLASSIFICATION_PROMPT, 
    REVIEW_CLASSIFICATION_RETRY_PROMPT, 
    REVIEW_CLASSIFICATION_SYSTEM_MESSAGE
)

logger = logging.getLogger(__name__)

class GroqClassificationService:
    """Service for review classification using Groq LLM"""
    
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
            logger.info("Groq classification client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq classification client: {str(e)}")
            raise
    
    def classify_review(
        self, 
        review: Dict[str, Any], 
        themes: List[Dict[str, Any]], 
        app_name: str = "INDMoney",
        max_retries: int = 2
    ) -> ReviewClassificationResponse:
        """
        Classify a single review into a theme
        
        Args:
            review: Review dictionary with text, rating, etc.
            themes: List of available themes
            app_name: Name of the app for context
            max_retries: Maximum number of retry attempts
            
        Returns:
            ReviewClassificationResponse with theme assignment
        """
        try:
            # Format themes for prompt
            themes_list = self._format_themes_for_prompt(themes)
            
            # Extract review details
            rating = review.get('rating', 1)
            review_text = review.get('text', '').strip()
            
            # Classify with retry logic
            classification = self._classify_with_retry(
                review_text, rating, themes_list, app_name, max_retries
            )
            
            return classification
            
        except Exception as e:
            logger.error(f"Review classification failed: {str(e)}")
            raise
    
    def classify_reviews_batch(
        self, 
        reviews: List[Dict[str, Any]], 
        themes: List[Dict[str, Any]], 
        app_name: str = "INDMoney",
        batch_size: int = 10
    ) -> List[ReviewClassificationResponse]:
        """
        Classify multiple reviews in batches
        
        Args:
            reviews: List of review dictionaries
            themes: List of available themes
            app_name: Name of the app for context
            batch_size: Number of reviews to process in each batch
            
        Returns:
            List of ReviewClassificationResponse objects
        """
        try:
            logger.info(f"Starting batch classification of {len(reviews)} reviews")
            
            classifications = []
            
            # Process in batches to avoid rate limits
            for i in range(0, len(reviews), batch_size):
                batch_reviews = reviews[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(reviews) + batch_size - 1)//batch_size}")
                
                batch_classifications = []
                for review in batch_reviews:
                    try:
                        classification = self.classify_review(review, themes, app_name)
                        batch_classifications.append(classification)
                    except Exception as e:
                        logger.warning(f"Failed to classify review {review.get('reviewId', 'unknown')}: {str(e)}")
                        # Create fallback classification
                        fallback = ReviewClassificationResponse(
                            themeId="unclassified",
                            confidence=0.0,
                            reasoning="Classification failed"
                        )
                        batch_classifications.append(fallback)
                
                classifications.extend(batch_classifications)
                
                # Add delay between batches to avoid rate limits
                if i + batch_size < len(reviews):
                    time.sleep(1)
            
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
        """Classify review with retry logic"""
        
        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    prompt = REVIEW_CLASSIFICATION_PROMPT.format(
                        app_name=app_name,
                        themes_list=themes_list,
                        rating=rating,
                        review_text=review_text
                    )
                else:
                    prompt = REVIEW_CLASSIFICATION_RETRY_PROMPT.format(
                        app_name=app_name,
                        themes_list=themes_list,
                        rating=rating,
                        review_text=review_text
                    )
                
                logger.debug(f"Attempt {attempt + 1}: Calling Groq API for classification")
                
                # Call Groq API
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": REVIEW_CLASSIFICATION_SYSTEM_MESSAGE},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Lower temperature for consistent classification
                    max_tokens=200
                )
                
                # Parse response
                content = response.choices[0].message.content.strip()
                classification = self._parse_classification_response(content, themes_list)
                
                logger.debug(f"Successfully classified review on attempt {attempt + 1}")
                return classification
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise
                time.sleep(0.5)  # Wait before retry
                
            except Exception as e:
                logger.warning(f"Classification failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise
                time.sleep(1)  # Wait before retry
        
        raise Exception("Failed to classify review after all retries")
    
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
