#!/usr/bin/env python3
"""
Complete test of Preview Email functionality
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_complete_flow():
    """Test complete Preview Email flow"""
    print("🧪 TESTING COMPLETE PREVIEW EMAIL FLOW")
    print("=" * 50)
    
    try:
        # Test the exact same flow as web UI
        from phase5_Orchestration_Web_UI.pipeline import append_combined_report_on_preview
        
        print("📋 Calling append_combined_report_on_preview()...")
        success, message, payload = append_combined_report_on_preview(use_sample=False)
        
        print(f"📊 Result: success={success}")
        print(f"📊 Message: {message}")
        
        if payload:
            print(f"📊 Themes: {len(payload.weekly_pulse.themes)}")
            print(f"📊 Quotes: {len(payload.weekly_pulse.quotes)}")
        
        if success:
            print("✅ SUCCESS: Combined report appended to Google Doc")
            print("🔗 Doc Link: https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0/edit?tab=t.0")
        else:
            print("❌ FAILED: Combined report append failed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_flow()
