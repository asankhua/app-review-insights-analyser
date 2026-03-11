"""
Phase 6: Scheduler daemon - runs weekly pulse at 9:00 AM IST every Sunday.
Use: python -m phase6.daemon
"""
import logging
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from phase6.scheduler import run_scheduled_pulse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def job():
    logger.info("Scheduled job: running weekly pulse")
    code = run_scheduled_pulse()
    if code != 0:
        logger.warning(f"Scheduled run exited with code {code}")


def main():
    # 9:00 AM IST = 3:30 AM UTC (IST is UTC+5:30)
    # Run every Sunday
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        job,
        CronTrigger(day_of_week="sun", hour=9, minute=0),
        id="weekly_pulse",
    )
    logger.info("Scheduler started. Next run: 9:00 AM IST every Sunday.")
    scheduler.start()


if __name__ == "__main__":
    main()
