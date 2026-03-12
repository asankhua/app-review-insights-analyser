"""
Phase 5: FastAPI REST API for Web UI.
Run with: python run_web.py or uvicorn phase5.api:app --reload --port 8000
"""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*OpenSSL.*LibreSSL.*")

import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from phase5.pipeline import (
    run_pipeline,
    get_status,
    get_latest_report,
    send_email as pipeline_send_email,
)

app = FastAPI(title="App Review Insights API", version="1.0")

# CORS for Vercel frontend (and localhost for dev)
_DEFAULT_ORIGINS = "http://localhost:8000,http://localhost:3000,https://app-review-insights-analyser.vercel.app"
ALLOWED_ORIGINS = [x.strip() for x in os.environ.get("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


class RunRequest(BaseModel):
    mock: bool = False
    weeks: int = 8
    count: int = 100


class SendEmailRequest(BaseModel):
    recipient: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the minimal Web UI."""
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(html_path)


@app.get("/api/status")
async def api_status():
    """Get pipeline status (reviews, themes, report)."""
    return get_status()


def _run_pipeline_task(mock: bool, weeks: int, count: int):
    """Background task: runs pipeline (avoids Render 30s request timeout)."""
    run_pipeline(mock=mock, weeks=weeks, count=count, send_email=False)


@app.post("/api/run")
async def api_run(req: RunRequest, background_tasks: BackgroundTasks):
    """Run pipeline in background; returns immediately (Render has 30s timeout)."""
    from phase5.pipeline import _pipeline_state
    if _pipeline_state["running"]:
        raise HTTPException(status_code=409, detail="Pipeline already running")
    _pipeline_state["error"] = None
    background_tasks.add_task(_run_pipeline_task, req.mock, req.weeks, req.count)
    return {
        "success": True,
        "message": "Pipeline started. Poll /api/status for progress.",
        "started": True,
    }


@app.get("/api/report")
async def api_report():
    """Get latest weekly pulse content (markdown)."""
    content = get_latest_report()
    if content is None:
        raise HTTPException(status_code=404, detail="No report found. Run pipeline first.")
    return {"content": content}


@app.post("/api/email/send")
async def api_send_email(req: SendEmailRequest):
    """Send latest report via email."""
    result = pipeline_send_email(recipient=req.recipient)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Send failed"))
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
