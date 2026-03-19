"""
Weekly note generation data models for Phase 3
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

@dataclass
class Theme:
    """Theme model for weekly report"""
    id: str
    name: str
    description: str
    review_count: int
    confidence_score: float
    created_at: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "review_count": self.review_count,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class Quote:
    """User quote model for weekly report"""
    text: str
    rating: int
    theme_id: str
    review_id: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "text": self.text,
            "rating": self.rating,
            "theme_id": self.theme_id,
            "review_id": self.review_id
        }

@dataclass
class ActionIdea:
    """Action idea model for weekly report"""
    description: str
    theme_id: str
    priority: str = "medium"  # high, medium, low
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "description": self.description,
            "theme_id": self.theme_id,
            "priority": self.priority
        }

class WeeklyReport(BaseModel):
    """Weekly report model for Phase 3 output"""
    id: str = Field(..., description="Report identifier")
    week_start: date = Field(..., description="Week start date")
    week_end: date = Field(..., description="Week end date")
    app_id: str = Field(..., description="App identifier")
    app_name: str = Field(..., description="App name")
    themes: List[Dict[str, Any]] = Field(..., description="Top 3 themes")
    quotes: List[Dict[str, Any]] = Field(..., description="User quotes")
    actions: List[Dict[str, Any]] = Field(..., description="Action ideas")
    word_count: int = Field(..., description="Total words in report")
    generated_at: datetime = Field(..., description="Generation timestamp")
    
    @validator('themes')
    def validate_themes(cls, v):
        if len(v) > 3:
            raise ValueError("Maximum 3 themes allowed")
        if len(v) < 1:
            raise ValueError("At least 1 theme required")
        return v
    
    @validator('quotes')
    def validate_quotes(cls, v):
        if len(v) != 3:
            raise ValueError("Exactly 3 quotes required")
        return v
    
    @validator('actions')
    def validate_actions(cls, v):
        if len(v) != 3:
            raise ValueError("Exactly 3 action ideas required")
        return v
    
    @validator('word_count')
    def validate_word_count(cls, v):
        if v > 400:
            raise ValueError("Report must be under 400 words")
        return v

class WeeklyReportFile(BaseModel):
    """Model for weekly report file (Phase 3 Output)"""
    generatedAt: datetime
    appId: str
    appName: str
    weekStart: date
    weekEnd: date
    report: WeeklyReport
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NoteGenerationRequest(BaseModel):
    """Request model for note generation"""
    themes: List[Dict[str, Any]] = Field(..., description="Discovered themes")
    grouped_reviews: Dict[str, List[Dict[str, Any]]] = Field(..., description="Reviews grouped by theme")
    app_name: str = Field(default="INDMoney", description="App name for context")
    week_start: date = Field(..., description="Week start date")
    week_end: date = Field(..., description="Week end date")

class NoteGenerationResponse(BaseModel):
    """Response model for note generation"""
    report: WeeklyReport
    markdown_content: str
    text_content: str
    processing_time: float
