"""
Phase 5: Pipeline orchestration.
Runs Phases 1-4 in sequence. Used by CLI and Web API.
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent

_SUBPROCESS_ENV = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}

# Shared state for background pipeline (avoids Render 30s request timeout)
_pipeline_state = {"running": False, "error": None}


@dataclass
class PipelineResult:
    success: bool
    message: str
    report_path: Optional[str] = None
    stats: Optional[dict] = None
    error: Optional[str] = None


def run_pipeline(
    mock: bool = False,
    weeks: int = 8,
    count: int = 100,
    send_email: bool = False,
    in_process: bool = True,
) -> PipelineResult:
    """
    Run full pipeline (Phase 1 -> 2a -> 2b -> 3 -> 4).
    Uses in-process by default to avoid subprocess segfault on ARM Mac.
    """
    if in_process:
        return _run_in_process(mock, weeks, count, send_email)
    return _run_subprocess(mock, weeks, count, send_email)


def _run_in_process(mock: bool, weeks: int, count: int, send_email: bool) -> PipelineResult:
    """Run in API process (avoids subprocess segfault on ARM Mac)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    _pipeline_state["running"] = True
    _pipeline_state["error"] = None
    try:
        from main import run_pipeline_sync
        ok, err = run_pipeline_sync(mock=mock, weeks=weeks, count=count, send=send_email, recipient=None)
        if not ok:
            _pipeline_state["error"] = err or "Unknown error"
            return PipelineResult(success=False, message="Pipeline failed", error=err or "Unknown error")
        return PipelineResult(
            success=True,
            message="Pipeline completed successfully",
            report_path=_get_latest_report_path(),
            stats=_get_status(),
        )
    except Exception as e:
        logger.exception("Pipeline failed")
        _pipeline_state["error"] = str(e)
        return PipelineResult(success=False, message=str(e), error=str(e))
    finally:
        _pipeline_state["running"] = False


def _run_subprocess(mock: bool, weeks: int, count: int, send_email: bool) -> PipelineResult:
    """Run via subprocess (can segfault on ARM Mac)."""
    try:
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "--phase", "run",
        ]
        if mock:
            cmd.append("--mock")
        cmd.extend(["--weeks", str(weeks), "--count", str(count)])
        if send_email:
            cmd.append("--send")

        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300, env=_SUBPROCESS_ENV)

        if result.returncode != 0:
            err = result.stderr or result.stdout or f"Exit code {result.returncode}"
            if result.returncode == 139:
                err = "Process segfaulted. The pipeline now runs in-process to avoid this."
            return PipelineResult(success=False, message="Pipeline failed", error=err)
        return PipelineResult(
            success=True,
            message="Pipeline completed successfully",
            report_path=_get_latest_report_path(),
            stats=_get_status(),
        )
    except subprocess.TimeoutExpired:
        return PipelineResult(success=False, message="Pipeline timed out", error="Timeout")
    except Exception as e:
        logger.exception("Pipeline failed")
        return PipelineResult(success=False, message=str(e), error=str(e))


def get_status() -> dict:
    """Get current pipeline status (reviews, themes, report)."""
    return _get_status()


def _get_status() -> dict:
    """Internal status aggregation from data files."""
    reviews_dir = PROJECT_ROOT / "data" / "reviews"
    reports_dir = PROJECT_ROOT / "data" / "reports"
    status = {
        "reviews_count": 0,
        "themes_count": 0,
        "has_report": False,
        "report_path": None,
        "last_report_date": None,
        "pipeline_running": _pipeline_state["running"],
        "pipeline_error": _pipeline_state["error"],
    }
    try:
        if reviews_dir.exists():
            files = sorted(reviews_dir.glob("*.json"))
            if files:
                with open(files[-1]) as f:
                    data = json.load(f)
                status["reviews_count"] = len(data.get("reviews", []))
                status["last_scraped"] = data.get("scrapedAt", "")
        if reports_dir.exists():
            theme_files = list(reports_dir.glob("themes-*.json"))
            if theme_files:
                with open(theme_files[-1]) as f:
                    data = json.load(f)
                status["themes_count"] = len(data.get("themes", []))
            pulse_files = list(reports_dir.glob("pulse-*.md"))
            if pulse_files:
                latest = sorted(pulse_files)[-1]
                status["has_report"] = True
                status["report_path"] = str(latest)
                status["last_report_date"] = latest.stem.replace("pulse-", "")
    except Exception as e:
        status["error"] = str(e)
    return status


def get_latest_report() -> Optional[str]:
    """Get content of latest weekly pulse (markdown)."""
    path = _get_latest_report_path()
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8")
    return None


def _get_latest_report_path() -> Optional[str]:
    """Get path to latest pulse markdown."""
    reports_dir = PROJECT_ROOT / "data" / "reports"
    if not reports_dir.exists():
        return None
    pulse_files = list(reports_dir.glob("pulse-*.md"))
    if not pulse_files:
        return None
    return str(sorted(pulse_files)[-1])


def send_email(recipient: Optional[str] = None) -> dict:
    """
    Send latest weekly report via email.
    Returns dict with status, message_id, error.
    """
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    try:
        from phase4.email_delivery import EmailDeliveryService
        from phase4.models.email import EmailMode

        svc = EmailDeliveryService()
        response = svc.deliver_weekly_note(
            recipient_email=recipient,
            mode=EmailMode.SEND,
        )
        return {
            "success": response.status.value == "sent",
            "message_id": response.message_id,
            "recipient": response.recipient,
            "subject": response.subject,
            "error": response.error_message,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
