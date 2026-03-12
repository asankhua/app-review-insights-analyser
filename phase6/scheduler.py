"""
Phase 6: Scheduler - runs full pipeline (Phases 1-3 only) at 9:00 AM IST every Sunday.
Fetch data only; email is sent from the Web UI.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

_SUBPROCESS_ENV = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}

from .config import SCHEDULED_WEEKS, SCHEDULED_COUNT

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent


def run_scheduled_pulse(mock: bool = False) -> int:
    """
    Run full pipeline (Phases 1-3). Phase 4 skipped (--skip-email). Email from UI.
    Uses: python main.py --phase run --skip-email --weeks 8 --count 100
    If mock=True: uses sample data, skips Play Store scrape and Groq/Gemini APIs.
    Returns exit code (0 = success).
    """
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "main.py"),
        "--phase",
        "run",
        "--skip-email",
        "--weeks",
        str(SCHEDULED_WEEKS),
        "--count",
        str(SCHEDULED_COUNT),
    ]
    if mock:
        cmd.insert(cmd.index("--phase") + 2, "--mock")
    logger.info(f"Running scheduled pulse: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=600,  # 10 min
        env=_SUBPROCESS_ENV,
    )
    if result.returncode != 0:
        logger.error(f"Scheduled run failed: {result.stderr or result.stdout}")
    return result.returncode


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    sys.exit(run_scheduled_pulse())
