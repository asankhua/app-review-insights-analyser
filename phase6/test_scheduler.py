"""
One-time scheduler test: run at 11:12 PM IST today.
Uses --mock to skip Play Store & Groq; tests if scheduler triggers and email is sent.
Usage: python -m phase6.test_scheduler [--run-soon]
  --run-soon: run in 1 min (for quick test without waiting for 11:12 PM)
"""
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    TZ_IST = ZoneInfo("Asia/Kolkata")
except ImportError:
    TZ_IST = None  # Fallback: use local time

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger

from phase6.scheduler import run_scheduled_pulse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def job():
    logger.info("Test job: running scheduled pulse (mock mode)")
    code = run_scheduled_pulse(mock=True)
    logger.info(f"Job finished with exit code {code}")


def main():
    run_soon = "--run-soon" in sys.argv
    now = datetime.now(TZ_IST) if TZ_IST else datetime.now()
    run_at = now.replace(hour=23, minute=12, second=0, microsecond=0)
    if run_soon or run_at <= now:
        run_at = now + timedelta(minutes=1)
        logger.info(f"Running in 1 min ({run_at})")
    else:
        logger.info(f"Scheduled for 11:12 PM IST ({run_at})")

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(job, DateTrigger(run_date=run_at), id="test_pulse")
    logger.info("Scheduler started. Waiting for scheduled time...")
    scheduler.start()


if __name__ == "__main__":
    main()
