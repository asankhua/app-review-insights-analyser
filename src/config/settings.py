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
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")  # For Render free tier (SMTP blocked); optional
    GOOGLE_DRIVE_CREDENTIALS_JSON = os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON")  # Service account JSON for Google Doc link
    GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")  # Or path to JSON file
    FEE_EXPLANATION_URL = os.getenv("FEE_EXPLANATION_URL")  # Optional; Phase 7 fee/exit load source URL (e.g. INDMoney fund page)
    GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")  # Optional; Phase 8 target Google Doc ID (or URL) for appending combined report
    # Phase 8 MCP (primary): when set, append to Google Doc via MCP server (e.g. google-docs-mcp-server); else fallback to Docs API
    MCP_GOOGLE_DOCS_USE_MCP = os.getenv("MCP_GOOGLE_DOCS_USE_MCP", "").strip().lower() in ("1", "true", "yes")
    MCP_GOOGLE_DOCS_MCP_COMMAND = os.getenv("MCP_GOOGLE_DOCS_MCP_COMMAND")  # e.g. uvx or python
    MCP_GOOGLE_DOCS_MCP_ARGS = os.getenv("MCP_GOOGLE_DOCS_MCP_ARGS")  # e.g. ["google-docs-mcp-server"] or space-separated
    MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH = os.getenv("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH")  # or use GOOGLE_DRIVE_CREDENTIALS_PATH
    MCP_GOOGLE_DOCS_SUBJECT_EMAIL = os.getenv("MCP_GOOGLE_DOCS_SUBJECT_EMAIL")  # Workspace user for domain-wide delegation
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
