#!/usr/bin/env python3
"""
Simple API endpoint to test Google Docs integration in production.
Add this to your production deployment to debug the issue.
"""
import os
import json
import base64
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TestRequest(BaseModel):
    doc_id: str = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
    test_message: str = None

@app.get("/api/debug/google-docs")
async def debug_google_docs():
    """Debug endpoint to check Google Docs configuration in production."""
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "environment": "production",
        "checks": {}
    }
    
    # Check 1: Environment variables
    debug_info["checks"]["google_doc_id"] = {
        "set": bool(os.environ.get("GOOGLE_DOC_ID")),
        "value": os.environ.get("GOOGLE_DOC_ID", "Not set")
    }
    
    debug_info["checks"]["base64_creds"] = {
        "set": bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64")),
        "length": len(os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "")),
        "preview": os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "")[:50] + "..." if os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64") else "Not set"
    }
    
    # Check 2: Base64 decoding
    base64_creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "").strip()
    if base64_creds:
        try:
            decoded = base64.b64decode(base64_creds).decode('utf-8')
            credentials_info = json.loads(decoded)
            debug_info["checks"]["base64_decode"] = {
                "success": True,
                "project_id": credentials_info.get("project_id"),
                "client_email": credentials_info.get("client_email")
            }
        except Exception as e:
            debug_info["checks"]["base64_decode"] = {
                "success": False,
                "error": str(e)
            }
    else:
        debug_info["checks"]["base64_decode"] = {
            "success": False,
            "error": "Base64 credentials not set"
        }
    
    # Check 3: Import production client
    try:
        from production_google_docs_client import get_google_credentials
        debug_info["checks"]["import_client"] = {
            "success": True
        }
    except Exception as e:
        debug_info["checks"]["import_client"] = {
            "success": False,
            "error": str(e)
        }
    
    # Check 4: Test credentials
    try:
        from production_google_docs_client import get_google_credentials
        creds = get_google_credentials()
        debug_info["checks"]["credentials"] = {
            "success": bool(creds),
            "has_content": bool(creds and len(creds) > 0)
        }
    except Exception as e:
        debug_info["checks"]["credentials"] = {
            "success": False,
            "error": str(e)
        }
    
    return debug_info

@app.post("/api/debug/test-google-docs")
async def test_google_docs(request: TestRequest):
    """Test endpoint to actually append to Google Doc."""
    try:
        from production_google_docs_client import append_to_google_doc_production
        
        doc_id = request.doc_id
        test_message = request.test_message or f"Production Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success, message = append_to_google_doc_production(doc_id, test_message)
        
        return {
            "success": success,
            "message": message,
            "doc_id": doc_id,
            "test_message": test_message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/debug/phase8")
async def debug_phase8():
    """Debug endpoint to test Phase 8 in production."""
    try:
        from phase8_Combined_JSON_Google_Doc_MCP import run_phase8
        from datetime import date
        
        report_date = date.today()
        success, payload, mcp_msg = run_phase8(
            report_date=report_date,
            fee_explanation=None,
            save_to_reports=False  # Don't save in production debug
        )
        
        return {
            "success": success,
            "mcp_message": mcp_msg,
            "payload_date": payload.date if payload else None,
            "themes_count": len(payload.weekly_pulse.themes) if payload else 0,
            "quotes_count": len(payload.weekly_pulse.quotes) if payload else 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    print("Debug server running on http://localhost:8001")
    print("Available endpoints:")
    print("  GET  /api/debug/google-docs - Check configuration")
    print("  POST /api/debug/test-google-docs - Test append")
    print("  GET  /api/debug/phase8 - Test Phase 8")
