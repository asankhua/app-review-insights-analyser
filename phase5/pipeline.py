"""
Phase 5: Pipeline orchestration.
Runs Phases 1-4 in sequence. Used by CLI and Web API.
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).parent.parent

# Cache for Gist fetch (avoids repeated API calls). TTL 60s.
_gist_cache: dict[str, Any] = {}
_GIST_CACHE_TTL = 60

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
        _write_last_run()
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


def _write_last_run() -> None:
    """Write last pipeline/scheduler run timestamp (IST) to logs."""
    try:
        logs_dir = PROJECT_ROOT / "data" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(IST).isoformat()
        (logs_dir / "last_run.txt").write_text(ts, encoding="utf-8")
    except Exception:
        pass


def _save_sync_upload(report_content: str, report_date: str, last_run: Optional[str] = None) -> None:
    """Save uploaded report and status from scheduler (GitHub Actions)."""
    try:
        reports_dir = PROJECT_ROOT / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        path = reports_dir / f"pulse-{report_date}.md"
        path.write_text(report_content, encoding="utf-8")
        if last_run:
            logs_dir = PROJECT_ROOT / "data" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            (logs_dir / "last_run.txt").write_text(last_run.strip(), encoding="utf-8")
    except Exception as e:
        logger.exception("Sync upload failed: %s", e)
        raise


def _fetch_from_gist() -> Optional[dict]:
    """Fetch report and metadata from GitHub Gist. Cached 60s. Returns {content, last_run, report_date} or None."""
    raw = os.environ.get("REPORT_GIST_ID", "").strip()
    # Allow full URL or just the ID
    if "/" in raw:
        gist_id = raw.rstrip("/").split("/")[-1]
    else:
        gist_id = raw
    if not gist_id:
        return None
    now = time.time()
    if _gist_cache and (now - _gist_cache.get("_ts", 0)) < _GIST_CACHE_TTL:
        return _gist_cache
    try:
        import urllib.request
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "App-Review-Insights/1.0",
        }
        token = os.environ.get("GH_GIST_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            f"https://api.github.com/gists/{gist_id}",
            headers=headers,
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        files = data.get("files", {})
        pulse = files.get("pulse.md") or files.get("pulse")
        if not pulse:
            for k, v in files.items():
                if v and (k.endswith(".md") or k == "pulse"):
                    pulse = v
                    break
        meta_file = files.get("meta.json") or files.get("meta")
        content = (pulse.get("content") or "").strip() if pulse else ""
        meta = {}
        if meta_file:
            try:
                meta = json.loads(meta_file.get("content", "{}"))
            except json.JSONDecodeError:
                pass
        last_run = meta.get("last_run", "") or None
        report_date = meta.get("report_date", "")
        if content:
            _gist_cache.update({
                "_ts": now, "content": content, "last_run": last_run,
                "report_date": report_date, "has_report": True,
            })
            return _gist_cache
        logger.warning("Gist %s has no pulse.md content", gist_id)
    except Exception as e:
        logger.warning("Gist fetch failed (id=%s): %s", gist_id, e)
    return None


def _get_last_run() -> Optional[str]:
    """Get last pipeline/scheduler run timestamp from Gist (if configured) or logs."""
    gist = _fetch_from_gist()
    if gist and gist.get("last_run"):
        return gist["last_run"]
    try:
        path = PROJECT_ROOT / "data" / "logs" / "last_run.txt"
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return None


def _get_last_email_sent() -> Optional[str]:
    """Get most recent email sent timestamp from delivery records or last_email_sent.txt."""
    try:
        fallback = PROJECT_ROOT / "data" / "logs" / "last_email_sent.txt"
        if fallback.exists():
            return fallback.read_text(encoding="utf-8").strip() or None
        deliveries_dir = PROJECT_ROOT / "data" / "deliveries"
        if not deliveries_dir.exists():
            return None
        files = list(deliveries_dir.glob("delivery_email_*.json")) or list(deliveries_dir.glob("delivery_*.json"))
        if not files:
            return None
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        for f in files[:20]:
            with open(f) as fp:
                data = json.load(fp)
            status = data.get("response", {}).get("status")
            if status in ("sent", "SENT"):
                return data.get("response", {}).get("sent_at")
        return None
    except Exception:
        return None


def _get_status() -> dict:
    """Internal status aggregation. Prefers Gist (REPORT_GIST_ID) for report/sync; else uses data files."""
    reviews_dir = PROJECT_ROOT / "data" / "reviews"
    reports_dir = PROJECT_ROOT / "data" / "reports"
    gist = _fetch_from_gist()
    last_run = _get_last_run()
    status = {
        "reviews_count": 0,
        "themes_count": 0,
        "has_report": bool(gist and gist.get("content")),
        "report_path": None,
        "last_report_date": gist.get("report_date") if gist else None,
        "last_scraped": None,
        "last_synced": last_run,
        "last_email_sent": _get_last_email_sent(),
        "last_run": last_run,
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
                status["last_scraped"] = data.get("scrapedAt", "") or None
        if not status["last_synced"] and status.get("last_scraped"):
            status["last_synced"] = status["last_scraped"]
        if reports_dir.exists():
            theme_files = list(reports_dir.glob("themes-*.json"))
            if theme_files:
                with open(theme_files[-1]) as f:
                    data = json.load(f)
                status["themes_count"] = len(data.get("themes", []))
            if not status["has_report"]:
                pulse_files = list(reports_dir.glob("pulse-*.md"))
                if pulse_files:
                    latest = sorted(pulse_files)[-1]
                    status["has_report"] = True
                    status["report_path"] = str(latest)
                    status["last_report_date"] = status["last_report_date"] or latest.stem.replace("pulse-", "")
    except Exception as e:
        status["error"] = str(e)
    return status


def get_latest_report() -> Optional[str]:
    """Get content of latest weekly pulse (markdown). Prefers Gist when REPORT_GIST_ID is set."""
    gist = _fetch_from_gist()
    if gist and gist.get("content"):
        return gist["content"]
    path = _get_latest_report_path()
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8")
    return None


def get_email_preview() -> Optional[dict]:
    """Get the email HTML and subject that would be sent (for preview)."""
    content = get_latest_report()
    if not content:
        return None
    try:
        import re
        from phase4.config.email_templates import HTML_TEMPLATE, format_markdown_to_html

        week_date = "Unknown"
        for line in content.split("\n"):
            if " -- " in line:
                week_date = line.split(" -- ")[-1].strip()
                break
            if "Week of" in line:
                week_date = line.split("Week of")[-1].strip()
                break

        snippet = content.strip()[:250].replace("\n", " ").strip()
        if len(content.strip()) > 250:
            snippet += "..."
        safe = re.sub(r"[^\w\s-]", "", week_date).strip().replace(" ", "_")[:40]
        attach_filename = f"INDMoney_Weekly_Pulse_{safe}.docx"

        weekly_note_html = format_markdown_to_html(content)
        html_body = HTML_TEMPLATE.format(
            recipient_name="Team",
            week_date=week_date,
            weekly_note_html=weekly_note_html,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            appended_snippet=snippet,
            appended_filename=attach_filename,
        )
        subject = f"INDMoney Weekly Review Pulse -- {week_date}"
        return {"subject": subject, "html": html_body}
    except Exception:
        return None


# Known sample report date - never serve this when last_run suggests a real sync occurred
_SAMPLE_REPORT_DATE = "2025-01-01"


def _get_latest_report_path() -> Optional[str]:
    """Get path to latest pulse markdown. Prefer data/reports (scheduler/sync); fallback to sample_data.
    When last_run exists (scheduler uploaded) but only sample report is present, return None to avoid
    showing misleading January data instead of the lost synced report."""
    reports_dir = PROJECT_ROOT / "data" / "reports"
    last_run = _get_last_run()
    if reports_dir.exists():
        pulse_files = list(reports_dir.glob("pulse-*.md"))
        if pulse_files:
            latest_path = sorted(pulse_files)[-1]
            latest_date = latest_path.stem.replace("pulse-", "")
            # If we have last_run (scheduler sync) but only the sample report, don't serve it
            if last_run and latest_date == _SAMPLE_REPORT_DATE:
                return None
            return str(latest_path)
    sample_dir = PROJECT_ROOT / "sample_data"
    if sample_dir.exists() and not last_run:
        sample_files = list(sample_dir.glob("pulse-*.md"))
        if sample_files:
            return str(sorted(sample_files)[-1])
    return None


def send_email(recipient: Optional[str] = None) -> dict:
    """
    Send latest weekly report via email.
    Uses same source as View Report (Gist when REPORT_GIST_ID set, else files).
    Returns dict with status, message_id, error.
    """
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    try:
        from phase4.email_delivery import EmailDeliveryService
        from phase4.models.email import EmailMode

        content = get_latest_report()
        svc = EmailDeliveryService()
        response = svc.deliver_weekly_note(
            weekly_note_content=content,
            recipient_email=recipient,
            mode=EmailMode.SEND,
        )
        if response.status.value == "sent" and response.sent_at:
            try:
                logs_dir = PROJECT_ROOT / "data" / "logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                ts = response.sent_at.isoformat() if hasattr(response.sent_at, "isoformat") else str(response.sent_at)
                (logs_dir / "last_email_sent.txt").write_text(ts, encoding="utf-8")
            except Exception:
                pass
        return {
            "success": response.status.value == "sent",
            "message_id": response.message_id,
            "recipient": response.recipient,
            "subject": response.subject,
            "error": response.error_message,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
