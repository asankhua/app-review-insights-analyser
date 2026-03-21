"""
Phase 5: FastAPI REST API for Web UI.
Run with: python run_web.py or uvicorn phase5_Orchestration_Web_UI.api:app --reload --port 8000
Backend: Render.com | Frontend: Vercel
"""
import os
from pathlib import Path

# Load .env early so REPORT_GIST_ID/GH_GIST_TOKEN work for View Report (Gist fetch)
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    for p in [_root / ".env", Path.cwd() / ".env"]:
        if p.exists():
            load_dotenv(p, override=True)
            break
    else:
        load_dotenv(override=True)
except ImportError:
    pass

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*OpenSSL.*LibreSSL.*")

import asyncio
import sys
import time
from typing import Optional

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import json
import logging
from datetime import date
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

# Lazy import pipeline so GET / and first paint never block on Gist/heavy code
# app = FastAPI(...) and routes import pipeline only when needed

app = FastAPI(title="App Review Insights API", version="1.0")

# Email send: run in background so POST returns immediately and UI doesn't hang
_email_send_pending = False
_email_send_result: Optional[dict] = None

# Status cache: filled in background so /api/status returns instantly on first load
_status_cache: Optional[dict] = None
_status_cache_ts: float = 0
_STATUS_CACHE_TTL = 30  # seconds
_minimal_status = {
    "reviews_count": 0,
    "themes_count": 0,
    "has_report": False,
    "report_path": None,
    "last_report_date": None,
    "last_scraped": None,
    "last_synced": None,
    "last_email_sent": None,
    "last_run": None,
    "scheduler_run": None,
    "pipeline_running": False,
    "pipeline_error": None,
    "gist_unavailable": False,
    "status_loading": True,
    "mcp_append_success": None,
    "mcp_append_message": None,
}

# CORS for Vercel frontend (and localhost for dev)
_DEFAULT_ORIGINS = "http://localhost:8000,http://localhost:3000,https://app-review-insights-analyser-dx6z.vercel.app"
ALLOWED_ORIGINS = [x.strip() for x in os.environ.get("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",") if x.strip()]
# Regex allows any Vercel deployment (main + preview URLs like xyz-abc123-def.vercel.app)
_VERCEL_ORIGIN_REGEX = r"https://[^/]*\.vercel\.app"
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=_VERCEL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Use absolute path so "/" works regardless of server cwd (e.g. uvicorn --reload)
STATIC_DIR = (ROOT / "phase5_Orchestration_Web_UI" / "static").resolve()

# Load index.html once at startup so "/" always serves the UI
_INDEX_HTML: Optional[str] = None


def _get_index_html() -> str:
    global _INDEX_HTML
    if _INDEX_HTML is None:
        html_path = STATIC_DIR / "index.html"
        if not html_path.exists():
            raise FileNotFoundError(f"Web UI not found at {html_path}")
        content = html_path.read_text(encoding="utf-8")
        if not content or not content.strip():
            raise FileNotFoundError(f"Web UI index.html is empty at {html_path}")
        _INDEX_HTML = content
    return _INDEX_HTML


class SendEmailRequest(BaseModel):
    recipient: Optional[str] = None


class SyncUploadRequest(BaseModel):
    """Payload from scheduler/workflow to sync report and status to backend."""
    report_content: str
    report_date: str  # YYYY-MM-DD
    last_run: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def index():
    """Serve the minimal Web UI."""
    try:
        return HTMLResponse(content=_get_index_html())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="UI not found")


def _refresh_status_cache_sync() -> None:
    """Run in thread: fetch status and update cache. Never blocks the caller."""
    global _status_cache, _status_cache_ts
    try:
        from phase5_Orchestration_Web_UI.pipeline import get_status
        s = get_status()
        status = dict(s)
        status["status_loading"] = False
        mcp_path = ROOT / "data" / "mcp_append.json"
        if mcp_path.exists():
            try:
                mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
                if mcp_data.get("success") is False or (mcp_data.get("message") and mcp_data.get("message").strip()):
                    status["mcp_append_success"] = mcp_data.get("success")
                    status["mcp_append_message"] = (mcp_data.get("message") or "").strip() or None
            except Exception:
                pass
        _status_cache = status
        _status_cache_ts = time.time()
    except Exception:
        pass


async def _refresh_status_background() -> None:
    """Run get_status in a thread so the event loop is not blocked."""
    await asyncio.to_thread(_refresh_status_cache_sync)


@app.get("/api/health")
async def api_health():
    """Lightweight health check (no pipeline deps). Use to verify backend is up and CORS works."""
    return {"ok": True, "status": "up"}


@app.get("/api/debug/fee")
async def api_debug_fee():
    """
    Debug fee explainer config. Use to verify FEE_EXPLANATION_URL/EXIT_LOAD_VALUE are set on Render.
    Returns only non-sensitive status; no secrets.
    """
    def _check():
        fee_url = (os.environ.get("FEE_EXPLANATION_URL") or "").strip().strip('"').strip("'")
        exit_load = (os.environ.get("EXIT_LOAD_VALUE") or "").strip().strip('"').strip("'")
        fee_url_configured = bool(fee_url)
        exit_load_configured = bool(exit_load)
        fee_explanation_result = None
        fee_fetch_ok = False
        if fee_url:
            try:
                from phase7_Fee_Explanation import get_fee_explanation
                from datetime import date
                result = get_fee_explanation(report_date=date.today(), fee_url=fee_url, save_to_reports=False)
                fee_explanation_result = "fetched" if result is not None else "none"
                fee_fetch_ok = result is not None
            except Exception as e:
                fee_explanation_result = f"error: {str(e)[:80]}"
        return {
            "fee_url_configured": fee_url_configured,
            "exit_load_configured": exit_load_configured,
            "fee_explanation_attempted": fee_url_configured,
            "fee_explanation_result": fee_explanation_result,
            "fee_fetch_ok": fee_fetch_ok,
            "hint": "If fee_url_configured is false, add FEE_EXPLANATION_URL to Render env and redeploy.",
        }
    try:
        return await asyncio.wait_for(asyncio.to_thread(_check), timeout=25.0)
    except asyncio.TimeoutError:
        return {"fee_url_configured": None, "error": "Fee check timed out (fund page may be slow or blocked)"}


@app.get("/api/status")
async def api_status(background_tasks: BackgroundTasks):
    """Return status from cache or fetch fresh (avoid minimal stub so Synced Pipeline date is correct)."""
    global _status_cache, _status_cache_ts
    now = time.time()
    if _status_cache is not None and (now - _status_cache_ts) < _STATUS_CACHE_TTL:
        out = dict(_status_cache)
        out["status_loading"] = False
        return out
    if _status_cache is not None:
        # Stale cache: return it and refresh in background
        out = dict(_status_cache)
        out["status_loading"] = False
        background_tasks.add_task(_refresh_status_background)
        return out
    # No cache (e.g. after pipeline): fetch fresh status so Synced Pipeline date is correct
    try:
        await asyncio.wait_for(asyncio.to_thread(_refresh_status_cache_sync), timeout=10.0)
        if _status_cache is not None:
            out = dict(_status_cache)
            out["status_loading"] = False
            return out
    except (asyncio.TimeoutError, Exception):
        pass
    # Fallback: refresh in background and return minimal
    background_tasks.add_task(_refresh_status_background)
    return dict(_minimal_status)


@app.get("/api/report")
async def api_report(sample: bool = False):
    """Get weekly pulse content (markdown). sample=1: sample_data; else: last synced (Gist/data/reports)."""
    def _fetch_report():
        from phase5_Orchestration_Web_UI.pipeline import get_status, get_report
        content = get_report(use_sample=sample)
        if content is None:
            status = get_status()
            detail = "No report found. Run pipeline first."
            if not os.environ.get("REPORT_GIST_ID"):
                detail = "Add REPORT_GIST_ID to Render env (Gist ID from workflow log). See docs/DEPLOYMENT.md §7."
            elif status.get("gist_unavailable"):
                gist_err = status.get("gist_error", "")
                detail = (
                    "Gist unreachable. Add REPORT_GIST_ID and GH_GIST_TOKEN to Render Environment. "
                    "Also add RENDER_URL and REPORT_UPLOAD_SECRET to GitHub Secrets so the sync uploads reports."
                )
                if gist_err:
                    detail += f" Error: {gist_err}"
            elif status.get("scheduler_run"):
                detail = "Report from last sync unavailable. Check Gist has pulse.md and meta.json."
            raise HTTPException(status_code=404, detail=detail)
        return {"content": content}
    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch_report), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Report load timed out. Try again.")


@app.get("/api/email/preview")
async def api_email_preview(sample: bool = False):
    """Get email preview (HTML) as it would appear in inbox. sample=1: use sample data (matches View Report checkbox)."""
    def _fetch_preview():
        from phase5_Orchestration_Web_UI.pipeline import get_email_preview
        return get_email_preview(use_sample=sample)
    try:
        preview = await asyncio.wait_for(asyncio.to_thread(_fetch_preview), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Email preview timed out. Try again.")
    if preview is None:
        raise HTTPException(status_code=404, detail="No report found. Run pipeline first.")
    if isinstance(preview, dict) and preview.get("_error"):
        err = preview["_error"]
        raise HTTPException(status_code=500, detail=f"Email preview failed: {err}")
    return preview


@app.post("/api/upload/sync")
async def api_upload_sync(req: SyncUploadRequest, x_upload_secret: Optional[str] = Header(None, alias="X-Upload-Secret")):
    """Receive report + status from scheduler (GitHub Actions). Secured with REPORT_UPLOAD_SECRET."""
    expected = os.environ.get("REPORT_UPLOAD_SECRET")
    if not expected or x_upload_secret != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    from phase5_Orchestration_Web_UI.pipeline import _save_sync_upload
    _save_sync_upload(
        report_content=req.report_content,
        report_date=req.report_date,
        last_run=req.last_run,
    )
    return {"success": True, "message": "Sync uploaded"}


def _run_email_send(recipient: Optional[str]) -> None:
    """Run in background thread: send email and store result so UI can poll."""
    global _email_send_pending, _email_send_result, _status_cache
    _email_send_pending = True
    _email_send_result = None
    try:
        from phase5_Orchestration_Web_UI.pipeline import _pipeline_state, send_email as pipeline_send_email
        result = pipeline_send_email(recipient=recipient)
        _email_send_result = dict(result) if result else {"success": False, "error": "No response"}
        if _email_send_result.get("success"):
            _pipeline_state["error"] = None
            _status_cache = None  # so next status fetch shows updated last_email_sent
    except Exception as e:
        _email_send_result = {"success": False, "error": str(e)}
    finally:
        _email_send_pending = False


@app.get("/api/email/send-status")
async def api_email_send_status():
    """Poll this after POST /api/email/send (202) to get result. Returns pending, success, error."""
    return {
        "pending": _email_send_pending,
        "success": _email_send_result.get("success") if _email_send_result else None,
        "error": _email_send_result.get("error") if _email_send_result else None,
        "message_id": _email_send_result.get("message_id") if _email_send_result else None,
    }


async def _send_email_background(recipient: Optional[str]) -> None:
    await asyncio.to_thread(_run_email_send, recipient)


@app.post("/api/email/send")
async def api_send_email(req: SendEmailRequest, background_tasks: BackgroundTasks):
    """Start email send in background; return 202 immediately so the page doesn't hang. Poll GET /api/email/send-status for result."""
    background_tasks.add_task(_send_email_background, req.recipient)
    return JSONResponse(
        status_code=202,
        content={"message": "Email send started. Poll /api/email/send-status for result.", "pending": True},
    )


@app.post("/api/force-combined-report")
async def api_force_combined_report(sample: bool = False):
    """Append combined report with timestamp to Google Doc. Called when Preview Email is clicked."""
    def _do_append():
        from phase5_Orchestration_Web_UI.pipeline import append_combined_report_on_preview
        return append_combined_report_on_preview(use_sample=sample)
    try:
        success, message, payload = await asyncio.wait_for(asyncio.to_thread(_do_append), timeout=25.0)
        themes_count = len(payload.weekly_pulse.themes) if payload else 0
        quotes_count = len(payload.weekly_pulse.quotes) if payload else 0
        
        # Get append status and doc link
        append_status = "success" if success else "failed"
        doc_link = "https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0/edit?tab=t.0"
        
        return JSONResponse(content={
            "success": success,
            "message": message,
            "themes_count": themes_count,
            "quotes_count": quotes_count,
            "append_status": append_status,
            "doc_link": doc_link,
        })
    except asyncio.TimeoutError:
        return JSONResponse(content={
            "success": False, 
            "message": "Append timed out",
            "append_status": "failed",
            "doc_link": "https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0/edit?tab=t.0"
        })
    except Exception as e:
        logger.error(f"Force combined report failed: {e}")
        return JSONResponse(content={
            "success": False, 
            "message": str(e),
            "append_status": "failed",
            "doc_link": "https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0/edit?tab=t.0"
        })


@app.get("/api/force-combined-report")
async def api_force_combined_report_get(sample: bool = False):
    """GET endpoint for easy testing."""
    return await api_force_combined_report(sample=sample)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
