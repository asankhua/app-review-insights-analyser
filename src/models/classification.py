"""
Review classification data models for Phase 2b
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

@dataclass
class ClassifiedReview:
    """Review with theme classification"""
    reviewId: str
    rating: int
    text: str
    date: datetime
    themeId: str
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "reviewId": self.reviewId,
            "rating": self.rating,
            "text": self.text,
            "date": self.date.isoformat(),
            "themeId": self.themeId,
            "confidence": self.confidence
        }

class ReviewClassificationRequest(BaseModel):
    """Request model for review classification"""
    review: Dict[str, Any] = Field(..., description="Review to classify")
    themes: List[Dict[str, Any]] = Field(..., description="Available themes")
    app_name: str = Field(default="INDMoney", description="App name for context")

class ReviewClassificationResponse(BaseModel):
    """Response model for review classification"""
    themeId: str = Field(..., description="Assigned theme ID")
    confidence: float = Field(..., description="Classification confidence")
    reasoning: Optional[str] = Field(None, description="Classification reasoning")
    
    @validator('themeId')
    def validate_theme_id(cls, v, values):
        if 'themes' in values:
            theme_ids = [theme['id'] for theme in values['themes']]
            if v not in theme_ids:
                raise ValueError(f'Theme ID {v} not in available themes: {theme_ids}')
        return v

class GroupedReviewsFile(BaseModel):
    """Model for grouped reviews file (Phase 2b Output)"""
    generatedAt: datetime
    appId: str
    packageId: str
    themes: List[Dict[str, Any]]
    byTheme: Dict[str, List[Dict[str, Any]]]
    weeksRequested: int
    totalReviews: int
    
    @validator('byTheme')
    def validate_by_theme(cls, v, values):
        if 'themes' in values:
            theme_ids = {theme['id'] for theme in values['themes']}
            by_theme_ids = set(v.keys())
            # Allow 'unclassified' as it's used for reviews that don't match any theme
            valid_ids = theme_ids.union({'unclassified'})
            if not by_theme_ids.issubset(valid_ids):
                missing = by_theme_ids - valid_ids
                raise ValueError(f'Theme IDs in byTheme not found in themes: {missing}')
        return v

class ClassificationStats(BaseModel):
    """Statistics for classification results"""
    total_reviews: int
    classified_reviews: int
    unclassified_reviews: int
    theme_distribution: Dict[str, int]
    average_confidence: float
    processing_time: float
