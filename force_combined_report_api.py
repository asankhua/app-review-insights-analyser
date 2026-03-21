#!/usr/bin/env python3
"""
Force Combined Report API - Direct fix for production combined report issue.
This API endpoint will force append combined report to Google Doc when called.
"""
import os
import json
import logging
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ForceAppendRequest(BaseModel):
    doc_id: str = None
    report_date: str = None

@app.post("/api/force-combined-report")
async def force_combined_report(request: ForceAppendRequest = None):
    """
    Force append combined report to Google Doc.
    This endpoint bypasses all MCP logic and directly uses production client.
    """
    try:
        # Get parameters
        doc_id = request.doc_id if request else None
        report_date_str = request.report_date if request else None
        
        # Use defaults if not provided
        if not doc_id:
            doc_id = os.environ.get("GOOGLE_DOC_ID", "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0")
        
        if not report_date_str:
            today = date.today()
            report_date_str = today.strftime("%Y-%m-%d")
        
        # Parse date
        try:
            from datetime import datetime
            report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except ValueError:
            report_date = date.today()
        
        logger.info(f"Force appending combined report for {report_date} to {doc_id}")
        
        # Import and run Phase 8
        from phase8_Combined_JSON_Google_Doc_MCP import run_phase8
        
        success, payload, mcp_message = run_phase8(
            report_date=report_date,
            fee_explanation=None,
            save_to_reports=True,
            doc_id=doc_id
        )
        
        if success and payload:
            # Force append using production client
            from production_google_docs_client import append_to_google_doc_production
            
            # Generate human-readable report
            report_text = payload.to_human_readable()
            
            # Add timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_text = f"\n--- FORCE APPEND - {timestamp} ---\n{report_text}"
            
            # Append to Google Doc
            append_success, append_message = append_to_google_doc_production(doc_id, report_text)
            
            return {
                "success": True,
                "message": "Combined report force-appended successfully",
                "report_date": report_date_str,
                "doc_id": doc_id,
                "themes_count": len(payload.weekly_pulse.themes),
                "quotes_count": len(payload.weekly_pulse.quotes),
                "append_success": append_success,
                "append_message": append_message,
                "google_doc_url": f"https://docs.google.com/document/d/{doc_id}"
            }
        else:
            return {
                "success": False,
                "message": "Failed to generate combined report",
                "error": mcp_message or "Unknown error"
            }
            
    except Exception as e:
        logger.error(f"Force combined report failed: {e}")
        return {
            "success": False,
            "message": "Force append failed",
            "error": str(e)
        }

@app.get("/api/force-combined-report")
async def force_combined_report_get():
    """GET endpoint for easy testing."""
    return await force_combined_report()

@app.post("/api/debug/force-test")
async def debug_force_test():
    """Debug endpoint to test the force append functionality."""
    try:
        # Test production client directly
        from production_google_docs_client import append_to_google_doc_production
        from datetime import datetime
        
        doc_id = os.environ.get("GOOGLE_DOC_ID", "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0")
        test_text = f"FORCE TEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nThis is a direct test of the production client."
        
        success, message = append_to_google_doc_production(doc_id, test_text)
        
        return {
            "success": success,
            "message": message,
            "doc_id": doc_id,
            "test_text": test_text,
            "timestamp": datetime.now().isoformat(),
            "google_doc_url": f"https://docs.google.com/document/d/{doc_id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
    print("Force Combined Report API running on http://localhost:8002")
    print("Available endpoints:")
    print("  GET  /api/force-combined-report - Force append combined report")
    print("  POST /api/force-combined-report - Force append with parameters")
    print("  POST /api/debug/force-test - Test production client")
