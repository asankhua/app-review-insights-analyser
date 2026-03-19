"""
Theme data models for Phase 2a and 2b
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

@dataclass
class Theme:
    """Theme data structure"""
    id: str                   # Theme identifier (slug)
    label: str                # Human-readable theme name
    description: str          # One-line description
    review_count: int = 0     # Number of reviews assigned to this theme
    confidence_score: float = 0.0  # AI confidence score
    created_at: datetime = None  # Generation timestamp

class ThemeModel(BaseModel):
    """Pydantic model for theme validation"""
    id: str = Field(..., description="Theme slug identifier")
    label: str = Field(..., description="Human-readable theme name")
    description: str = Field(..., description="One-line description")
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Theme ID cannot be empty')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Theme ID must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()
    
    @validator('label')
    def validate_label(cls, v):
        if not v or not v.strip():
            raise ValueError('Theme label cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Theme description cannot be empty')
        return v.strip()

class ThemeDiscoveryRequest(BaseModel):
    """Request model for theme discovery"""
    reviews: List[Dict[str, Any]] = Field(..., description="List of reviews to analyze")
    sample_size: int = Field(default=150, description="Number of reviews to sample")
    app_name: str = Field(default="INDMoney", description="App name for context")

class ThemeDiscoveryResponse(BaseModel):
    """Response model for theme discovery"""
    themes: List[ThemeModel] = Field(..., description="Discovered themes")
    sample_size: int = Field(..., description="Number of reviews analyzed")
    app_name: str = Field(..., description="App name")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('themes')
    def validate_themes(cls, v):
        if not v:
            raise ValueError('At least one theme must be generated')
        if len(v) < 3 or len(v) > 5:
            raise ValueError('Number of themes must be between 3 and 5')
        return v

class ThemeFile(BaseModel):
    """Model for saving themes to file"""
    generatedAt: datetime
    appId: str
    packageId: str
    themes: List[ThemeModel]
    sampleSize: int
    weeksRequested: int
