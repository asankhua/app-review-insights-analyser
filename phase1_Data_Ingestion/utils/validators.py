"""
Utility functions for review processing and PII filtering
"""
import re
import emoji
from typing import List, Optional
from datetime import datetime
from src.models.review import ScrapedReview, ReviewRecord

class ReviewValidator:
    """Review validation and filtering utilities"""
    
    @staticmethod
    def has_min_words(text: str, min_words: int = 5) -> bool:
        """Check if text has minimum number of words"""
        if not text:
            return False
        # Split by whitespace and filter out empty strings
        words = [word for word in text.split() if word.strip()]
        return len(words) >= min_words
    
    @staticmethod
    def contains_emoji(text: str) -> bool:
        """Check if text contains emojis or star rating icons"""
        # Check using regex patterns
        if PIIFilter.STAR_RATING_PATTERN.search(text):
            return True
        if PIIFilter.EMOJI_PATTERN.search(text):
            return True
        
        # Check using emoji library as backup
        return bool(emoji.emoji_count(text))
    
    @staticmethod
    def is_english_text(text: str) -> bool:
        """Basic check if text is primarily English"""
        # Simple heuristic: check if text contains primarily ASCII characters
        try:
            text.encode('ascii')
            return True
        except UnicodeEncodeError:
            # If it contains non-ASCII characters, check if they're just common punctuation
            non_ascii_chars = sum(1 for char in text if ord(char) > 127)
            total_chars = len(text.replace(' ', '').replace('\n', ''))
            return non_ascii_chars / max(total_chars, 1) < 0.1  # Less than 10% non-ASCII
    
    @staticmethod
    def is_valid_review(text: str, min_words: int = 5) -> bool:
        """Comprehensive review validation"""
        if not text or not text.strip():
            return False
        
        # Check minimum word count
        if not ReviewValidator.has_min_words(text, min_words):
            return False
        
        # Check for emojis and star rating icons
        if ReviewValidator.contains_emoji(text):
            return False
        
        # Check if primarily English
        if not ReviewValidator.is_english_text(text):
            return False
        
        return True

class PIIFilter:
    """PII detection and removal utilities"""
    
    # PII patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b')
    USERNAME_PATTERN = re.compile(r'@[A-Za-z0-9_]+')
    ID_PATTERN = re.compile(r'\b[A-Z]{2,}-\d{4,}\b|\b\d{6,}\b')  # Generic ID patterns
    URL_PATTERN = re.compile(r'https?://[^\s<>"]{1,}|www\.[^\s<>"]{1,}')
    
    # Star rating and emoji patterns
    STAR_RATING_PATTERN = re.compile(r'[⭐★☆]+')
    EMOJI_PATTERN = re.compile(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]'
    )
    
    @staticmethod
    def remove_pii(text: str) -> str:
        """Remove PII from text"""
        if not text:
            return text
        
        # Remove emails
        text = PIIFilter.EMAIL_PATTERN.sub('[EMAIL_REMOVED]', text)
        
        # Remove phone numbers
        text = PIIFilter.PHONE_PATTERN.sub('[PHONE_REMOVED]', text)
        
        # Remove usernames
        text = PIIFilter.USERNAME_PATTERN.sub('[USERNAME_REMOVED]', text)
        
        # Remove IDs
        text = PIIFilter.ID_PATTERN.sub('[ID_REMOVED]', text)
        
        # Remove URLs
        text = PIIFilter.URL_PATTERN.sub('[URL_REMOVED]', text)
        
        return text.strip()
    
    @staticmethod
    def remove_emojis_and_stars(text: str) -> str:
        """Remove emojis and star rating icons from text"""
        if not text:
            return text
        
        # Remove star rating icons (⭐★☆)
        text = PIIFilter.STAR_RATING_PATTERN.sub('', text)
        
        # Remove emojis using regex
        text = PIIFilter.EMOJI_PATTERN.sub('', text)
        
        # Additional emoji removal using emoji library as backup
        import emoji
        text = emoji.replace_emoji(text, replace='')
        
        return text.strip()
    
    @staticmethod
    def sanitize_review_text(text: str) -> str:
        """Sanitize review text by removing PII, emojis, and normalizing"""
        if not text:
            return ""
        
        # Remove PII
        text = PIIFilter.remove_pii(text)
        
        # Remove emojis and star rating icons
        text = PIIFilter.remove_emojis_and_stars(text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text

class DateFilter:
    """Date filtering utilities"""
    
    @staticmethod
    def is_within_weeks(review_date: datetime, weeks: int) -> bool:
        """Check if review date is within specified weeks from today"""
        now = datetime.now()
        delta = now - review_date
        return delta.days <= weeks * 7
    
    @staticmethod
    def filter_by_date(reviews: List[ScrapedReview], weeks: int) -> List[ScrapedReview]:
        """Filter reviews by date range"""
        return [
            review for review in reviews
            if DateFilter.is_within_weeks(review.at, weeks)
        ]

class ReviewTransformer:
    """Transform scraped reviews to internal format"""
    
    @staticmethod
    def to_review_record(scraped_review: ScrapedReview) -> ReviewRecord:
        """Transform scraped review to internal record format"""
        # Sanitize the text content
        sanitized_text = PIIFilter.sanitize_review_text(scraped_review.content)
        
        return ReviewRecord(
            reviewId=scraped_review.reviewId,
            rating=scraped_review.score,
            text=sanitized_text,
            date=scraped_review.at
        )
    
    @staticmethod
    def transform_valid_reviews(scraped_reviews: List[ScrapedReview], weeks: int, min_words: int = 5) -> List[ReviewRecord]:
        """Transform and filter scraped reviews"""
        valid_reviews = []
        
        # Filter by date first
        date_filtered = DateFilter.filter_by_date(scraped_reviews, weeks)
        
        for scraped_review in date_filtered:
            # Validate review content
            if ReviewValidator.is_valid_review(scraped_review.content, min_words):
                # Transform to internal format
                review_record = ReviewTransformer.to_review_record(scraped_review)
                valid_reviews.append(review_record)
        
        return valid_reviews

