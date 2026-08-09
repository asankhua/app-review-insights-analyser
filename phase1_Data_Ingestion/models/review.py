"""
Review data models for App Review Insights Analyzer
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

@dataclass
class ReviewRecord:
    """Internal review record after scraping and PII filtering"""
    reviewId: str
    rating: int
    text: str
    date: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "reviewId": self.reviewId,
            "rating": self.rating,
            "text": self.text,
            "date": self.date.isoformat()
        }

class ReviewsFile(BaseModel):
    """Phase 1 Output: Reviews file structure"""
    scrapedAt: datetime
    packageId: str
    appId: str
    weeksRequested: int
    reviews: List[dict]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScrapedReview(BaseModel):
    """Raw scraped review before filtering"""
    reviewId: str
    userName: Optional[str] = None
    userImage: Optional[str] = None
    content: str
    score: int
    thumbsUpCount: int = 0
    reviewCreatedVersion: Optional[str] = None
    at: datetime
    replyContent: Optional[str] = None
    repliedAt: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AppInfo(BaseModel):
    """App information for scraping"""
    package_id: str
    app_name: str
    lang: str = "en"
    country: str = "in"

