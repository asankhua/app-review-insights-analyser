#!/usr/bin/env python3
"""
Main CLI interface for App Review Insights Analyzer - Phase 1
"""
# Reduce OpenBLAS threads to avoid segfault on ARM macOS (gemm_thread_n)
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*OpenSSL.*LibreSSL.*")

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from phase1_Data_Ingestion.data_ingestion import DataIngestionService
from phase2a_Theme_Discovery.theme_discovery import ThemeDiscoveryService
from phase2b_Review_Classification.review_classification import ReviewClassificationService
from phase3_Weekly_Note_Generation.note_generation import WeeklyNoteService
from phase4_Email_Delivery.email_delivery import EmailDeliveryService
from src.config.settings import Config

# Configure logging
Path("data/logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/phase1_Data_Ingestion.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(level)

def validate_args(args):
    """Validate command line arguments"""
    if args.phase == 'run':
        return
    config = Config()
    
    # Validate weeks
    if not config.validate_weeks(args.weeks):
        print(f"Error: Weeks must be between {config.MIN_WEEKS} and {config.MAX_WEEKS}")
        sys.exit(1)
    
    # Validate count
    if args.count <= 0:
        print("Error: Count must be greater than 0")
        sys.exit(1)

def run_phase1_scrape(args):
    """Run Phase 1: Review scraping and ingestion"""
    try:
        logger.info("Starting Phase 1: Review Ingestion and Cleaning for INDMoney")
        
        ingestion_service = DataIngestionService()
        
        logger.info(f"Processing INDMoney with {args.weeks} weeks")
        
        filepath = ingestion_service.ingest_reviews(
            weeks=args.weeks,
            max_count=args.count
        )
        print(f"✅ Successfully scraped INDMoney: {filepath}")
        
        # Show stats
        stats = ingestion_service.get_ingestion_stats()
        print(f"   Reviews: {stats['total_reviews']}, Weeks: {stats['weeks_requested']}")
        
        logger.info("Phase 1 completed successfully")
        
    except Exception as e:
        logger.error(f"Phase 1 failed: {str(e)}")
        print(f"❌ Phase 1 failed: {str(e)}")
        sys.exit(1)

def run_phase1_status(args):
    """Show status of scraped reviews and themes"""
    try:
        ingestion_service = DataIngestionService()
        theme_service = ThemeDiscoveryService()
        
        # Reviews status
        stats = ingestion_service.get_ingestion_stats()
        print(f"\n📊 INDMoney Review Status")
        print("=" * 50)
        
        if 'error' in stats:
            print(f"❌ {stats['error']}")
        else:
            print(f"📱 App: INDMONEY")
            print(f"📁 Latest: {stats['latest_file']}")
            print(f"📝 Reviews: {stats['total_reviews']}")
            print(f"📅 Weeks: {stats['weeks_requested']}")
            print(f"⏰ Scraped: {stats['last_scraped']}")
        
        # Themes status
        theme_stats = theme_service.get_themes_stats()
        print(f"\n🎯 Themes Status")
        print("=" * 50)
        
        if 'error' in theme_stats:
            print(f"❌ {theme_stats['error']}")
        else:
            print(f"📁 Latest: {theme_stats['latest_file']}")
            print(f"🎯 Themes: {theme_stats['total_themes']}")
            print(f"📊 Sample: {theme_stats['sample_size']}")
            print(f"⏰ Generated: {theme_stats['generated_at']}")
        
        # Classification status
        classification_service = ReviewClassificationService()
        classification_stats = classification_service.get_classification_stats()
        print(f"\n📋 Classification Status")
        print("=" * 50)
        
        if 'error' in classification_stats:
            print(f"❌ {classification_stats['error']}")
        else:
            print(f"📁 Latest: {classification_stats['latest_file']}")
            print(f"📋 Classified: {classification_stats['classified_reviews']}/{classification_stats['total_reviews']}")
            print(f"🎯 Themes: {len(classification_stats['theme_distribution'])}")
            print(f"⏰ Generated: {classification_stats['generated_at']}")
        
        # Weekly note status
        note_service = WeeklyNoteService()
        note_stats = note_service.get_weekly_note_stats()
        print(f"\n📝 Weekly Note Status")
        print("=" * 50)
        
        if 'error' in note_stats:
            print(f"❌ {note_stats['error']}")
        else:
            print(f"📁 Latest: {note_stats['latest_file']}")
            print(f"📝 Notes: {note_stats['total_notes']}")
            print(f"📊 Words: {note_stats['word_count']}")
            print(f"⏰ Generated: {note_stats['generated_at']}")
        
        # Email delivery status
        email_service = EmailDeliveryService()
        email_stats = email_service.get_delivery_stats()
        print(f"\n📧 Email Delivery Status")
        print("=" * 50)
        
        if 'error' in email_stats:
            print(f"❌ {email_stats['error']}")
        else:
            print(f"📧 Sent: {email_stats['total_sent']}")
            print(f"📝 Drafts: {email_stats['total_drafts']}")
            print(f"📊 Success Rate: {email_stats['success_rate']:.1f}%")
            if email_stats['last_sent']:
                print(f"⏰ Last Sent: {email_stats['last_sent']}")
            if email_stats['most_recent_file']:
                print(f"📁 Latest: {email_stats['most_recent_file']}")
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        print(f"❌ Status check failed: {str(e)}")
        sys.exit(1)

def run_phase2_analyze(args):
    """Run Phase 2a: Theme Discovery"""
    try:
        logger.info("Starting Phase 2a: Theme Discovery for INDMoney")
        
        theme_service = ThemeDiscoveryService()
        
        logger.info(f"Analyzing themes with sample size: {args.sample_size}")
        
        filepath = theme_service.discover_themes_from_latest_reviews(
            sample_size=args.sample_size
        )
        print(f"✅ Successfully discovered themes: {filepath}")
        
        # Show stats
        stats = theme_service.get_themes_stats()
        if 'error' not in stats:
            print(f"   Themes: {stats['total_themes']}, Sample: {stats['sample_size']}")
            print(f"   Generated: {stats['generated_at']}")
        
        logger.info("Phase 2a completed successfully")
        
    except Exception as e:
        logger.error(f"Phase 2a failed: {str(e)}")
        print(f"❌ Phase 2a failed: {str(e)}")
        sys.exit(1)

def run_phase2_classify(args):
    """Run Phase 2b: Review Classification"""
    try:
        logger.info("Starting Phase 2b: Review Classification for INDMoney")
        
        classification_service = ReviewClassificationService()
        
        logger.info(f"Classifying reviews with batch size: {args.batch_size}")
        
        filepath = classification_service.classify_reviews_from_latest(
            batch_size=args.batch_size
        )
        print(f"✅ Successfully classified reviews: {filepath}")
        
        # Show stats
        stats = classification_service.get_classification_stats()
        if 'error' not in stats:
            print(f"   Classified: {stats['classified_reviews']}/{stats['total_reviews']}")
            print(f"   Themes: {len(stats['theme_distribution'])}")
            print(f"   Generated: {stats['generated_at']}")
        
        logger.info("Phase 2b completed successfully")
        
    except Exception as e:
        logger.error(f"Phase 2b failed: {str(e)}")
        print(f"❌ Phase 2b failed: {str(e)}")
        sys.exit(1)

def run_phase3_generate(args):
    """Run Phase 3: Weekly Note Generation"""
    try:
        logger.info("Starting Phase 3: Weekly Note Generation for INDMoney")
        
        note_service = WeeklyNoteService()
        
        filepath = note_service.generate_weekly_note_from_latest()
        print(f"✅ Successfully generated weekly note: {filepath}")
        
        # Show stats
        stats = note_service.get_weekly_note_stats()
        if 'error' not in stats:
            print(f"   Word count: {stats['word_count']}")
            print(f"   Total notes: {stats['total_notes']}")
            print(f"   Generated: {stats['generated_at']}")
        
        logger.info("Phase 3 completed successfully")
        
    except Exception as e:
        logger.error(f"Phase 3 failed: {str(e)}")
        print(f"❌ Phase 3 failed: {str(e)}")
        sys.exit(1)

def run_phase4_email(args, fee_explanation=None):
    """Run Phase 4: Email Delivery. Optionally include Phase 7 fee_explanation in body."""
    try:
        logger.info("Starting Phase 4: Email Delivery for INDMoney")
        
        email_service = EmailDeliveryService()
        
        # Determine email mode
        from phase4_Email_Delivery.models.email import EmailMode
        mode = EmailMode.SEND if args.send else EmailMode.DRY_RUN
        
        # Deliver email (fee section included when fee_explanation is provided)
        response = email_service.deliver_weekly_note(
            recipient_email=args.recipient,
            recipient_name=args.recipient_name,
            mode=mode,
            include_attachments=True,
            fee_explanation=fee_explanation,
        )
        
        # Display results
        if response.status.value == 'draft':
            print(f"✅ Email draft created: {response.draft_path}")
        elif response.status.value == 'sent':
            print(f"✅ Email sent successfully to {response.recipient}")
            print(f"   Message ID: {response.message_id}")
            print(f"   Processing time: {response.processing_time:.2f}s")
        elif response.status.value == 'failed':
            print(f"❌ Email delivery failed: {response.error_message}")
            sys.exit(1)
        
        print(f"   Subject: {response.subject}")
        
        logger.info("Phase 4 completed successfully")
        
    except Exception as e:
        logger.error(f"Phase 4 failed: {str(e)}")
        print(f"❌ Phase 4 failed: {str(e)}")
        sys.exit(1)

def _mock_data_exists():
    """Check if sample data exists (without loading services that need API keys)"""
    reviews_dir = Path("data/reviews")
    reports_dir = Path("data/reports")
    has_reviews = reviews_dir.exists() and list(reviews_dir.glob("*.json"))
    has_themes = reports_dir.exists() and list(reports_dir.glob("themes-*.json"))
    has_grouped = reports_dir.exists() and list(reports_dir.glob("grouped_reviews-*.json"))
    return has_reviews, has_themes, has_grouped

def _write_last_run():
    """Write last pipeline run timestamp (IST) to logs for UI status."""
    try:
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
        (logs_dir / "last_run.txt").write_text(ts, encoding="utf-8")
    except Exception:
        pass


def run_full_pipeline(args):
    """Run all phases in sequence (Phase 1 -> 2a -> 2b -> 3 -> 4)"""
    try:
        logger.info("Starting full pipeline: Phase 1 -> 2a -> 2b -> 3 -> 4")
        
        if args.mock:
            # Ensure sample data exists
            import subprocess
            seed_script = Path(__file__).parent / "scripts" / "seed_sample_data.py"
            if seed_script.exists():
                subprocess.run([sys.executable, str(seed_script)], check=True, capture_output=True)
            
            has_reviews, has_themes, has_grouped = _mock_data_exists()
            if not (has_reviews and has_themes and has_grouped):
                print("❌ Sample data missing. Run: python scripts/seed_sample_data.py")
                sys.exit(1)
        
        # Phase 1
        print("\n" + "="*50)
        print("PHASE 1: Review ingestion")
        print("="*50)
        if not args.mock:
            run_phase1_scrape(args)
        else:
            # Quick file count without API-dependent services
            reviews_files = list(Path("data/reviews").glob("*.json"))
            if reviews_files:
                import json
                with open(reviews_files[-1]) as f:
                    data = json.load(f)
                print(f"✅ Using existing reviews: {len(data.get('reviews', []))} reviews")
            else:
                print("❌ No reviews found. Run: python scripts/seed_sample_data.py")
                sys.exit(1)
        
        # Phase 2a
        print("\n" + "="*50)
        print("PHASE 2a: Theme discovery")
        print("="*50)
        if not args.mock:
            run_phase2_analyze(args)
        else:
            theme_files = list(Path("data/reports").glob("themes-*.json"))
            if theme_files:
                import json
                with open(theme_files[-1]) as f:
                    data = json.load(f)
                print(f"✅ Using existing themes: {len(data.get('themes', []))} themes")
            else:
                print("❌ No themes found. Run: python scripts/seed_sample_data.py")
                sys.exit(1)
        
        # Phase 2b
        print("\n" + "="*50)
        print("PHASE 2b: Review classification")
        print("="*50)
        if not args.mock:
            run_phase2_classify(args)
        else:
            grouped_files = list(Path("data/reports").glob("grouped_reviews-*.json"))
            if grouped_files:
                import json
                with open(grouped_files[-1]) as f:
                    data = json.load(f)
                by_theme = data.get("byTheme", {})
                classified = sum(len(v) for k, v in by_theme.items() if k != "unclassified")
                print(f"✅ Using existing grouped reviews: {classified} classified")
            else:
                print("❌ No grouped reviews. Run: python scripts/seed_sample_data.py")
                sys.exit(1)
        
        # Phase 3
        print("\n" + "="*50)
        print("PHASE 3: Weekly note generation")
        print("="*50)
        run_phase3_generate(args)
        
        # Phase 7: Fee explanation (optional; before Phase 4 so email can include fee section)
        fee_explanation = None
        report_date = None
        if not getattr(args, 'skip_email', False):
            from datetime import date
            report_date = date.today()
            try:
                from phase7_Fee_Explanation import get_fee_explanation
                fee_explanation = get_fee_explanation(report_date=report_date, save_to_reports=True)
                if fee_explanation:
                    print("\n" + "="*50)
                    print("PHASE 7: Fee explanation (included in email)")
                    print("="*50)
            except Exception as e:
                logger.warning("Phase 7 fee explanation skipped: %s", e)
        
        # Phase 4 (skipped when --skip-email, e.g. scheduler)
        if getattr(args, 'skip_email', False):
            print("\n" + "="*50)
            print("PHASE 4: Skipped (--skip-email). Email from UI.")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("PHASE 4: Email" + (" (send)" if args.send else " (draft)"))
            print("="*50)
            run_phase4_email(args, fee_explanation=fee_explanation)
        
        # Phase 8: Combined JSON → Google Doc (optional; after Phase 4)
        if report_date is not None:
            try:
                from phase8_Combined_JSON_Google_Doc_MCP import run_phase8
                ok, _, mcp_msg = run_phase8(report_date=report_date, fee_explanation=fee_explanation, save_to_reports=True)
                if ok:
                    print("\n" + "="*50)
                    print("PHASE 8: Combined report (JSON + Google Doc if configured)")
                    if mcp_msg:
                        print("  " + mcp_msg)
                    print("="*50)
            except Exception as e:
                logger.warning("Phase 8 combined JSON / Google Doc skipped: %s", e)
        
        # Record last run timestamp (IST) for UI status
        _write_last_run()
        
        print("\n" + "="*50)
        print("✅ Pipeline complete!")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        print(f"❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_phase1_list(args):
    """List available review files"""
    try:
        ingestion_service = DataIngestionService()
        
        files = ingestion_service.list_reviews_files()
        print(f"\n📁 Available Review Files for INDMoney")
        print("=" * 50)
        
        if files:
            for file in files:
                print(f"📄 {file}")
        else:
            print("📭 No files found")
        
    except Exception as e:
        logger.error(f"List files failed: {str(e)}")
        print(f"❌ List files failed: {str(e)}")
        sys.exit(1)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="App Review Insights Analyzer - Phase 1: Review Ingestion and Cleaning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --phase scrape --weeks 8
  python main.py --phase run --send --recipient ashishmyweb@gmail.com
  python main.py --phase email --send --recipient team@company.com
  python main.py --phase status
  python -m phase6_Scheduler.scheduler
  python -m phase6_Scheduler.daemon
        """
    )
    
    # Phase selection
    parser.add_argument(
        '--phase',
        choices=['scrape', 'analyze', 'classify', 'generate', 'email', 'run', 'status', 'list'],
        required=True,
        help='Phase to run (run = all phases in sequence)'
    )
    
    # App selection removed - INDMoney only
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for classification (default: 10)'
    )
    
    # Email-specific arguments
    parser.add_argument(
        '--recipient',
        type=str,
        help='Email recipient address (overrides default)'
    )
    
    parser.add_argument(
        '--recipient-name',
        type=str,
        help='Recipient name for personalized greeting'
    )
    
    parser.add_argument(
        '--send',
        action='store_true',
        help='Send email via SMTP (default: dry-run mode)'
    )
    parser.add_argument(
        '--skip-email',
        action='store_true',
        help='Skip Phase 4 (email) entirely. Use for scheduler: fetch data only, send from UI.'
    )
    
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use sample data and skip API calls (for testing without GROQ_API_KEY)'
    )
    
    parser.add_argument(
        '--sample-size',
        type=int,
        default=150,
        help='Number of reviews to sample for theme analysis (default: 150)'
    )
    parser.add_argument(
        '--weeks',
        type=int,
        default=8,
        help='Review window in weeks (default: 8, range: 8-12)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Maximum number of reviews to fetch (default: 100)'
    )
    
    # Other options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate arguments
    validate_args(args)
    
    # Run appropriate phase
    if args.phase == 'run':
        run_full_pipeline(args)
    elif args.phase == 'scrape':
        run_phase1_scrape(args)
    elif args.phase == 'analyze':
        run_phase2_analyze(args)
    elif args.phase == 'classify':
        run_phase2_classify(args)
    elif args.phase == 'generate':
        run_phase3_generate(args)
    elif args.phase == 'email':
        run_phase4_email(args)
    elif args.phase == 'status':
        run_phase1_status(args)
    elif args.phase == 'list':
        run_phase1_list(args)


def run_pipeline_sync(
    mock: bool = False,
    weeks: int = 8,
    count: int = 100,
    send: bool = False,
    recipient: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Run full pipeline in-process (for Web API). Returns (success, error_message)."""
    args = SimpleNamespace(
        mock=mock,
        weeks=weeks,
        count=count,
        sample_size=150,
        batch_size=10,
        send=send,
        recipient=recipient,
        recipient_name=None,
    )
    try:
        run_full_pipeline(args)
        return True, None
    except SystemExit as e:
        return False, str(e.code) if e.code else "Pipeline exited"
    except Exception as e:
        logger.exception("Pipeline failed")
        return False, str(e)


if __name__ == "__main__":
    main()
