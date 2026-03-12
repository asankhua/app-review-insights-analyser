"""
Configuration management for App Review Insights Analyzer
"""
import os
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class AppConfig:
    """App configuration for a specific application"""
    package_id: str
    app_name: str
    lang: str = "en"
    country: str = "in"

class Config:
    """Main configuration class"""
    
    # App configuration - INDMoney only
    APP = AppConfig(
        package_id="in.indwealth",
        app_name="INDMoney"
    )
    
    # Scraper configuration
    SCRAPER_CONFIG = {
        "sort": "NEWEST",
        "count": 100,  # Limited to 100 as per requirement
        "rating_filter": None
    }
    
    # Review filtering
    MIN_WORDS = 10
    MAX_WEEKS = 12
    MIN_WEEKS = 8
    
    # File paths
    DATA_DIR = "data"
    REVIEWS_DIR = os.path.join(DATA_DIR, "reviews")
    REPORTS_DIR = os.path.join(DATA_DIR, "reports")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    
    # API Keys (from environment)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Email configuration
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # Scheduler configuration
    SCHEDULER_RECIPIENT = os.getenv("INDMONEY_SCHEDULER_RECIPIENT", "codeflex16@gmail.com")
    SCHEDULER_TZ = os.getenv("INDMONEY_SCHEDULER_TZ", "Asia/Kolkata")
    SCHEDULER_INTERVAL_MINUTES = int(os.getenv("INDMONEY_SCHEDULER_INTERVAL_MINUTES", "5"))
    SCHEDULER_WEEKS = int(os.getenv("INDMONEY_SCHEDULER_WEEKS", "8"))
    SCHEDULER_MAX_REVIEWS = int(os.getenv("INDMONEY_SCHEDULER_MAX_REVIEWS", "1000"))
    
    @classmethod
    def get_app_config(cls) -> AppConfig:
        """Get app configuration for INDMoney"""
        return cls.APP
    
    @classmethod
    def validate_weeks(cls, weeks: int) -> bool:
        """Validate weeks parameter"""
        return cls.MIN_WEEKS <= weeks <= cls.MAX_WEEKS
    
    @classmethod
    def get_reviews_dir(cls) -> str:
        """Get reviews directory"""
        return cls.REVIEWS_DIR
    
    @classmethod
    def get_reports_dir(cls) -> str:
        """Get reports directory"""
        return cls.REPORTS_DIR
