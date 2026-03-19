"""
Phase 5: Pipeline orchestration.
Runs Phases 1-4 in sequence. Used by CLI and Web API.
"""
import os
from datetime import date, datetime
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


def _clear_gist_cache() -> None:
    """Clear Gist cache so next fetch gets fresh data."""
    _gist_cache.clear()

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
        _upload_report_to_gist()
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


def _upload_report_to_gist() -> None:
    """Upload the latest report to Gist so View Report shows fresh data.
    Runs after pipeline succeeds (local or Render). Requires GH_GIST_TOKEN and REPORT_GIST_ID."""
    if not os.environ.get("GH_GIST_TOKEN", "").strip() or not os.environ.get("REPORT_GIST_ID", "").strip():
        return
    try:
        upload_script = PROJECT_ROOT / "scripts" / "upload_sync.py"
        if upload_script.exists():
            subprocess.run(
                [sys.executable, str(upload_script)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=30,
                env={**os.environ},
            )
            _clear_gist_cache()
    except Exception as e:
        logger.warning("Gist upload after pipeline failed: %s", e)


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
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        files = data.get("files", {})
        # Support exact filename or GitHub's optional 'filename' variant
        pulse = files.get("pulse.md") or files.get("pulse")
        if not pulse:
            for k, v in files.items():
                if v and (k.endswith(".md") or k == "pulse"):
                    pulse = v
                    break
        meta_file = files.get("meta.json") or files.get("meta")
        if not meta_file and isinstance(files, dict):
            for k, v in files.items():
                if v and isinstance(v, dict) and k and k.lower() in ("meta.json", "meta"):
                    meta_file = v
                    break
        content = (pulse.get("content") or "").strip() if pulse else ""
        meta = {}
        if meta_file and isinstance(meta_file, dict):
            try:
                raw = meta_file.get("content") or "{}"
                meta = json.loads(raw) if isinstance(raw, str) else {}
            except (json.JSONDecodeError, TypeError):
                pass
        last_run = (meta.get("last_run") or "").strip() or None
        report_date = (meta.get("report_date") or "").strip()
        # Fallback: use Gist's updated_at when meta.json has no last_run (e.g. older uploads)
        if not last_run and content and data.get("updated_at"):
            last_run = data.get("updated_at")
        if content:
            _gist_cache.update({
                "_ts": now, "content": content, "last_run": last_run,
                "report_date": report_date, "has_report": True,
            })
            return _gist_cache
        logger.warning("Gist %s has no pulse.md content", gist_id)
    except Exception as e:
        logger.warning("Gist fetch failed (id=%s): %s", gist_id, e)
        # Return stale cache so Scheduler Run date never disappears on transient failure
        if _gist_cache and (_gist_cache.get("content") or _gist_cache.get("last_run")):
            return _gist_cache
    return None


def _get_last_run() -> Optional[str]:
    """Get last pipeline/scheduler run timestamp. Prefer newer of local vs Gist so Run pipeline updates the UI."""
    local = _get_local_last_run()
    gist = _fetch_from_gist()
    gist_run = (gist.get("last_run") or "").strip() or None if gist else None
    if not local:
        return gist_run
    if not gist_run:
        return local
    try:
        local_dt = _parse_last_run(local)
        gist_dt = _parse_last_run(gist_run)
        if local_dt and gist_dt and local_dt >= gist_dt:
            return local
    except Exception:
        pass
    return gist_run


def _get_local_last_run() -> Optional[str]:
    """Get last pipeline run timestamp from local logs only."""
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
    """Internal status aggregation. Prefers Gist (REPORT_GIST_ID) for report/sync; else uses data files.
    Uses latest-by-mtime for reviews/themes/pulse so post-pipeline counts and report are correct."""
    reviews_dir = PROJECT_ROOT / "data" / "reviews"
    reports_dir = PROJECT_ROOT / "data" / "reports"
    gist = _fetch_from_gist()
    last_run = _get_last_run()
    # Scheduler run = from Gist only (GitHub Actions / sync). Never disappears when Gist has data.
    scheduler_run = (gist.get("last_run") or "").strip() or None if gist else None
    gist_configured = bool(os.environ.get("REPORT_GIST_ID", "").strip())
    # Consider local reports when Gist fails (sync uploads to Render)
    local_path = _get_latest_report_path()
    has_local = False
    if local_path:
        p = PROJECT_ROOT / local_path if not Path(local_path).is_absolute() else Path(local_path)
        has_local = p.exists()
    status = {
        "reviews_count": 0,
        "themes_count": 0,
        "has_report": bool(gist and gist.get("content")) or has_local,
        "report_path": str(local_path) if local_path else None,
        "last_report_date": (gist.get("report_date") if gist else None) or (
            Path(local_path).stem.replace("pulse-", "") if local_path and has_local else None
        ),
        "gist_unavailable": gist_configured and (gist is None),
        "last_scraped": None,
        "last_synced": last_run,
        "last_email_sent": _get_last_email_sent(),
        "last_run": last_run,
        "scheduler_run": scheduler_run,
        "pipeline_running": _pipeline_state["running"],
        "pipeline_error": _pipeline_state["error"],
        "mcp_append_success": None,
        "mcp_append_message": None,
    }
    try:
        mcp_path = PROJECT_ROOT / "data" / "logs" / "mcp_last.json"
        if mcp_path.exists():
            try:
                mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
                status["mcp_append_success"] = mcp_data.get("success")
                status["mcp_append_message"] = (mcp_data.get("message") or "").strip() or None
            except Exception:
                pass
    except Exception:
        pass
    try:
        if reviews_dir.exists():
            files = list(reviews_dir.glob("*.json"))
            if files:
                latest = max(files, key=lambda p: p.stat().st_mtime)
                with open(latest) as f:
                    data = json.load(f)
                status["reviews_count"] = len(data.get("reviews", []))
                status["last_scraped"] = data.get("scrapedAt", "") or None
        if not status["last_synced"] and status.get("last_scraped"):
            status["last_synced"] = status["last_scraped"]
        if reports_dir.exists():
            theme_files = list(reports_dir.glob("themes-*.json"))
            if theme_files:
                latest_theme = max(theme_files, key=lambda p: p.stat().st_mtime)
                with open(latest_theme) as f:
                    data = json.load(f)
                status["themes_count"] = len(data.get("themes", []))
            if not status["has_report"]:
                pulse_files = list(reports_dir.glob("pulse-*.md"))
                if pulse_files:
                    latest = max(pulse_files, key=lambda p: p.stat().st_mtime)
                    status["has_report"] = True
                    try:
                        status["report_path"] = str(latest.relative_to(PROJECT_ROOT))
                    except ValueError:
                        status["report_path"] = latest.name
                    status["last_report_date"] = status["last_report_date"] or latest.stem.replace("pulse-", "")
    except Exception as e:
        status["error"] = str(e)
    return status


def _parse_last_run(ts: Optional[str]) -> Optional[datetime]:
    """Parse last_run timestamp (ISO format) for comparison. Returns None if invalid."""
    if not ts or not isinstance(ts, str):
        return None
    ts = ts.strip()
    if not ts:
        return None
    try:
        # Handle ISO format with or without timezone
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # Normalize to timezone-aware for comparison (assume IST if naive)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)
        return parsed
    except (ValueError, TypeError):
        return None


def get_report(use_sample: bool = False) -> Optional[str]:
    """Get weekly pulse content. use_sample=True: from sample_data; else: last synced (Gist/data/reports)."""
    if use_sample:
        sample_dir = PROJECT_ROOT / "sample_data"
        if sample_dir.exists():
            sample_files = list(sample_dir.glob("pulse-*.md"))
            if sample_files:
                latest = max(sample_files, key=lambda p: p.stat().st_mtime)
                return latest.read_text(encoding="utf-8").strip()
        return None
    return get_latest_report()


def get_latest_report() -> Optional[str]:
    """Get content of latest weekly pulse (markdown).
    Prefers local when local last_run is newer so View Report shows the report we just generated."""
    gist = _fetch_from_gist()
    gist_content = (gist.get("content") or "").strip() if gist else ""
    gist_last_run = _parse_last_run(gist.get("last_run")) if gist else None

    path = _get_latest_report_path()
    local_content = None
    local_last_run = None
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = PROJECT_ROOT / path
        if p.exists():
            local_content = p.read_text(encoding="utf-8").strip()
            local_last_run = _parse_last_run(_get_local_last_run())

    if not gist_content and not local_content:
        return None
    if gist_content and not local_content:
        return gist_content
    if local_content and not gist_content:
        return local_content

    # Prefer the source that ran more recently so Run pipeline shows new report
    if gist_last_run and local_last_run:
        return local_content if local_last_run >= gist_last_run else gist_content
    if local_last_run:
        return local_content
    if gist_content:
        return gist_content
    return local_content


def get_email_preview(use_sample: bool = False) -> Optional[dict]:
    """Get the email HTML and subject that would be sent (for preview). Uses last report (weekly pulse + fee explanation).
    use_sample: when True, uses sample_data (same as View Report with checkbox)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    content = get_report(use_sample=use_sample)
    if not content or not content.strip():
        return None
    try:
        # Load templates directly to avoid phase4->phase3->google.generativeai chain (optional dep)
        import importlib.util
        _tmpl_path = PROJECT_ROOT / "phase4_Email_Delivery" / "config" / "email_templates.py"
        _spec = importlib.util.spec_from_file_location("_email_templates", _tmpl_path)
        _tmpl = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_tmpl)
        HTML_TEMPLATE = _tmpl.HTML_TEMPLATE
        format_markdown_to_html = _tmpl.format_markdown_to_html
        _escape_for_format = _tmpl._escape_for_format

        week_date = "Unknown"
        for line in content.split("\n"):
            if " -- " in line:
                week_date = line.split(" -- ")[-1].strip()
                break
            if "Week of" in line:
                week_date = line.split("Week of")[-1].strip()
                break

        weekly_note_html = format_markdown_to_html(content)
        # Add fee section (don't fail preview if fee loading fails)
        try:
            report_date_val = _get_latest_report_date() or date.today()
            fee_explanation = _load_saved_fee_explanation(report_date_val)
            if fee_explanation is None:
                try:
                    from phase7_Fee_Explanation import get_fee_explanation
                    from src.config.settings import Config

                    fee_url = getattr(Config, "FEE_EXPLANATION_URL", None) or os.environ.get("FEE_EXPLANATION_URL", "").strip()
                    fee_explanation = get_fee_explanation(report_date=report_date_val, fee_url=fee_url or None, save_to_reports=False)
                except Exception:
                    pass
            if fee_explanation is not None and hasattr(fee_explanation, "to_email_section_html"):
                weekly_note_html = weekly_note_html + "\n" + fee_explanation.to_email_section_html()
            else:
                # Fallback when FEE_EXPLANATION_URL is set but fetch failed (match email_delivery behavior)
                fee_url = os.environ.get("FEE_EXPLANATION_URL", "").strip()
                if fee_url:
                    fee_section_html = (
                        '<div class="section">'
                        '<h2>Fee Explanation</h2>'
                        '<p>This section could not be fetched automatically. '
                        'For exit load, expense ratio and other charges, please refer to the fund page below.</p>'
                        f'<p><a href="{fee_url}">View fund page (exit load &amp; expense ratio)</a></p>'
                        '</div>'
                    )
                    weekly_note_html = weekly_note_html + "\n" + fee_section_html
        except Exception as fee_err:
            logger.debug("Fee section skipped for email preview: %s", fee_err)

        html_body = HTML_TEMPLATE.format(
            recipient_name="Team",
            week_date=week_date,
            weekly_note_html=_escape_for_format(weekly_note_html),
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        subject = f"INDMoney Weekly Review Pulse -- {week_date}"
        return {"subject": subject, "html": html_body}
    except Exception as e:
        logger.warning("Email preview failed: %s", e)
        import traceback

        logger.debug("Email preview traceback: %s", traceback.format_exc())
        # Return error dict so API can surface the real cause (vs generic "No report")
        return {"_error": str(e)}


# Known sample report date - never serve this when last_run suggests a real sync occurred
_SAMPLE_REPORT_DATE = "2025-01-01"


def _get_latest_report_date() -> Optional[date]:
    """Get the report date (YYYY-MM-DD) of the latest report. From local path or Gist metadata."""
    path = _get_latest_report_path()
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = PROJECT_ROOT / path
        stem = p.stem  # e.g. pulse-2026-03-16
        if stem.startswith("pulse-"):
            try:
                return datetime.strptime(stem.replace("pulse-", ""), "%Y-%m-%d").date()
            except ValueError:
                pass
    gist = _fetch_from_gist()
    if gist:
        rd = (gist.get("report_date") or "").strip()
        if rd:
            try:
                return datetime.strptime(rd, "%Y-%m-%d").date()
            except ValueError:
                pass
    return None


def _load_saved_fee_explanation(report_date: date) -> Optional[Any]:
    """Load fee explanation from data/reports/fee_explanation-{date}.json if it exists."""
    try:
        path = PROJECT_ROOT / "data" / "reports" / f"fee_explanation-{report_date.isoformat()}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            from phase7_Fee_Explanation.models.fee import FeeExplanationResult

            return FeeExplanationResult.model_validate(data)
    except Exception:
        pass
    return None


def _get_latest_report_path() -> Optional[str]:
    """Get path to latest pulse markdown. Prefer data/reports (scheduler/sync); fallback to sample_data.
    When last_run exists (scheduler uploaded) but only sample report is present, return None to avoid
    showing misleading January data instead of the lost synced report."""
    reports_dir = PROJECT_ROOT / "data" / "reports"
    last_run = _get_last_run()
    if reports_dir.exists():
        pulse_files = list(reports_dir.glob("pulse-*.md"))
        if pulse_files:
            latest_path = max(pulse_files, key=lambda p: p.stat().st_mtime)
            latest_date = latest_path.stem.replace("pulse-", "")
            if last_run and latest_date == _SAMPLE_REPORT_DATE:
                return None
            return str(latest_path)
    sample_dir = PROJECT_ROOT / "sample_data"
    if sample_dir.exists() and not last_run:
        sample_files = list(sample_dir.glob("pulse-*.md"))
        if sample_files:
            return str(max(sample_files, key=lambda p: p.stat().st_mtime))
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
        from phase4_Email_Delivery.email_delivery import EmailDeliveryService
        from phase4_Email_Delivery.models.email import EmailMode
        from datetime import date
        content = get_latest_report()
        report_date_val = _get_latest_report_date() or date.today()
        fee_explanation = _load_saved_fee_explanation(report_date_val)
        if fee_explanation is None:
            try:
                from phase7_Fee_Explanation import get_fee_explanation
                from src.config.settings import Config
                fee_url = getattr(Config, "FEE_EXPLANATION_URL", None) or os.environ.get("FEE_EXPLANATION_URL", "").strip()
                fee_explanation = get_fee_explanation(report_date=report_date_val, fee_url=fee_url or None, save_to_reports=False)
            except Exception:
                pass
        svc = EmailDeliveryService()
        response = svc.deliver_weekly_note(
            weekly_note_content=content,
            recipient_email=recipient,
            mode=EmailMode.SEND,
            fee_explanation=fee_explanation,
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
