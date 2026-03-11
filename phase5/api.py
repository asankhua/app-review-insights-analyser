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

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from phase5.pipeline import (
    run_pipeline,
    get_status,
    get_latest_report,
    send_email as pipeline_send_email,
)

app = FastAPI(title="INDMoney Review Insights", version="1.0")

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


@app.post("/api/run")
async def api_run(req: RunRequest):
    """Run full pipeline (Phase 1 -> 4)."""
    result = run_pipeline(mock=req.mock, weeks=req.weeks, count=req.count)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or result.message)
    return {
        "success": True,
        "message": result.message,
        "stats": result.stats,
        "report_path": result.report_path,
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
