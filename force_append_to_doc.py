#!/usr/bin/env python3
"""
Force append combined report to Google Doc
This bypasses MCP and uses Google Docs API directly
"""
import os
from dotenv import load_dotenv
from datetime import date

# Load environment
load_dotenv()

def main():
    """Force append combined report to Google Doc."""
    from phase8_Combined_JSON_Google_Doc_MCP import run_phase8
    from phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client import _append_via_docs_api
    
    doc_id = os.environ.get('GOOGLE_DOC_ID', '')
    if not doc_id:
        print("Error: GOOGLE_DOC_ID not set")
        return
    
    print(f"Force appending combined report to Google Doc: {doc_id}")
    
    # Generate combined report for today
    report_date = date.today()
    success, payload, mcp_msg = run_phase8(
        report_date=report_date,
        fee_explanation=None,
        save_to_reports=True
    )
    
    if not success or not payload:
        print("Error: Failed to generate combined report")
        return
    
    # Force append using Google Docs API directly
    text = payload.to_human_readable()
    api_success = _append_via_docs_api(doc_id, text)
    
    if api_success:
        print(f"✅ SUCCESS: Combined report appended to Google Doc")
        print(f"📄 Check your doc: https://docs.google.com/document/d/{doc_id}")
    else:
        print(f"❌ FAILED: Could not append to Google Doc")

if __name__ == "__main__":
    main()
