#!/usr/bin/env python3
"""
Debug Web UI MCP flow to find the issue
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def debug_web_ui_mcp():
    """Debug the exact same flow as web UI"""
    print("🔍 DEBUGGING WEB UI MCP FLOW")
    print("=" * 50)
    
    try:
        # Import the exact same function as web UI
        from phase5_Orchestration_Web_UI.pipeline import append_combined_report_on_preview
        
        # Call the exact same function
        print("📋 Calling append_combined_report_on_preview()...")
        success, message, payload = append_combined_report_on_preview(use_sample=False)
        
        print(f"📊 Result: success={success}, message={message}")
        print(f"📊 Payload type: {type(payload)}")
        
        if payload:
            print(f"📊 Payload content preview:")
            print(payload.to_human_readable()[:200] + "...")
        
        if success:
            print("✅ SUCCESS: append_combined_report_on_preview worked")
        else:
            print("❌ FAILED: append_combined_report_on_preview failed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_web_ui_mcp()
