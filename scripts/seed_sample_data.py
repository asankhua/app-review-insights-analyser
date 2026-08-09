#!/usr/bin/env python3
"""
Seed sample data for offline/mock pipeline testing.
Creates reviews, themes, and grouped_reviews without API calls.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

PROJECT_ROOT = Path(__file__).parent.parent
REVIEWS_DIR = PROJECT_ROOT / "data" / "reviews"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

# Sample reviews (INDmoney-style feedback)
SAMPLE_REVIEWS = [
    {"reviewId": "r1", "rating": 4, "text": "App is good but needs average NAV feature for mutual funds to track performance better. Would help with SIP tracking.", "date": None},
    {"reviewId": "r2", "rating": 2, "text": "Can't modify orders after placement, this is very frustrating for active traders. Please add order modification within 5 minutes.", "date": None},
    {"reviewId": "r3", "rating": 5, "text": "UI is confusing, hard to find mutual fund section and track investments. Great app otherwise.", "date": None},
    {"reviewId": "r4", "rating": 3, "text": "Technical chart was better before. The new chart is not as user friendly as TradingView.", "date": None},
    {"reviewId": "r5", "rating": 2, "text": "Fractional shares limit order does not work. It resets every time I try to set limit price for dollar amount.", "date": None},
    {"reviewId": "r6", "rating": 4, "text": "Love the flash trading feature. App is faster now. Good job team.", "date": None},
    {"reviewId": "r7", "rating": 1, "text": "Lost money due to multiple failed transactions. Order execution is unreliable during market hours.", "date": None},
    {"reviewId": "r8", "rating": 4, "text": "Need trailing stop loss for US stocks. Feature request from long time user.", "date": None},
    {"reviewId": "r9", "rating": 3, "text": "Fund tracking is broken. Shows wrong NAV and P&L. Please fix data sync issues.", "date": None},
    {"reviewId": "r10", "rating": 5, "text": "Best investment app for NRIs. Simple and straightforward. Minor UI tweaks needed.", "date": None},
]

# Sample themes
SAMPLE_THEMES = [
    {"id": "feature_requests", "label": "Feature Requests", "description": "Users asking for average NAV, trailing stoploss, order modification"},
    {"id": "bug_fixes", "label": "Bug Fixes", "description": "Issues with order execution, fund tracking, fractional shares limit orders"},
    {"id": "ui_ux", "label": "UI/UX Issues", "description": "Navigation difficulties, chart usability, interface problems"},
]

# Theme to review mapping for grouped_reviews
THEME_TO_REVIEWS = {
    "feature_requests": [0, 1, 7],
    "bug_fixes": [2, 4, 6, 8],
    "ui_ux": [3, 5, 9],
}


def seed_reviews():
    """Create sample reviews file"""
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    
    base_date = datetime.now() - timedelta(days=14)
    reviews = []
    for i, r in enumerate(SAMPLE_REVIEWS):
        review = r.copy()
        review["date"] = (base_date + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S")
        reviews.append(review)
    
    data = {
        "scrapedAt": datetime.now(IST).isoformat(),
        "packageId": "in.indwealth",
        "appId": "indmoney",
        "weeksRequested": 8,
        "reviews": reviews,
    }
    
    filepath = REVIEWS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  Created: {filepath}")
    return filepath


def seed_themes():
    """Create sample themes file"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "generatedAt": datetime.now(IST).isoformat(),
        "appId": "indmoney",
        "packageId": "in.indwealth",
        "themes": SAMPLE_THEMES,
        "sampleSize": 10,
        "weeksRequested": 8,
    }
    
    filepath = REPORTS_DIR / f"themes-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  Created: {filepath}")
    return filepath


def seed_grouped_reviews():
    """Create sample grouped reviews file"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    base_date = datetime.now() - timedelta(days=14)
    reviews = []
    for i, r in enumerate(SAMPLE_REVIEWS):
        review = r.copy()
        review["date"] = (base_date + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S")
        reviews.append(review)
    
    by_theme = {}
    for theme_id, indices in THEME_TO_REVIEWS.items():
        by_theme[theme_id] = []
        for idx in indices:
            r = reviews[idx].copy()
            r["themeId"] = theme_id
            r["confidence"] = 0.9
            by_theme[theme_id].append(r)
    
    # Add unclassified for any remaining
    classified_ids = set()
    for indices in THEME_TO_REVIEWS.values():
        classified_ids.update(indices)
    unclassified = [reviews[i] for i in range(len(reviews)) if i not in classified_ids]
    for r in unclassified:
        r["themeId"] = "unclassified"
        r["confidence"] = 0.5
    by_theme["unclassified"] = unclassified if unclassified else []
    
    data = {
        "generatedAt": datetime.now(IST).isoformat(),
        "appId": "indmoney",
        "packageId": "in.indwealth",
        "themes": SAMPLE_THEMES,
        "byTheme": by_theme,
        "weeksRequested": 8,
        "totalReviews": len(reviews),
    }
    
    filepath = REPORTS_DIR / f"grouped_reviews-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  Created: {filepath}")
    return filepath


def main():
    print("Seeding sample data for App Review Insights Analyzer...")
    print("\nPhase 1: Reviews")
    seed_reviews()
    print("\nPhase 2a: Themes")
    seed_themes()
    print("\nPhase 2b: Grouped reviews")
    seed_grouped_reviews()
    print("\nDone. Run: python main.py --phase run --mock")


if __name__ == "__main__":
    main()

