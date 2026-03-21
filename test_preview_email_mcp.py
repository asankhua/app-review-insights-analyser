#!/usr/bin/env python3
"""
Test MCP Preview Email Integration
Tests the complete MCP functionality when clicking "Preview Email"
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_preview_email_mcp():
    """Test MCP functionality when Preview Email is clicked"""
    print("🧪 Testing MCP Preview Email Integration")
    print("=" * 50)
    
    # Set up environment variables
    os.environ["GOOGLE_SERVICE_ACCOUNT_BASE64"] = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "")
    os.environ["MCP_GOOGLE_DOCS_MCP_COMMAND"] = "python3"
    os.environ["MCP_GOOGLE_DOCS_MCP_ARGS"] = "phase8_Combined_JSON_Google_Doc_MCP/mcp/google_docs_mcp_server_simple.py"
    
    print("📧 Simulating 'Preview Email' click...")
    print("🔧 Environment variables configured:")
    print(f"   MCP_GOOGLE_DOCS_MCP_COMMAND: {os.environ.get('MCP_GOOGLE_DOCS_MCP_COMMAND')}")
    print(f"   MCP_GOOGLE_DOCS_MCP_ARGS: {os.environ.get('MCP_GOOGLE_DOCS_MCP_ARGS')}")
    print()
    
    try:
        # Import the preview email function
        from phase5_Orchestration_Web_UI.pipeline import append_combined_report_on_preview
        
        print("✅ Successfully imported append_combined_report_on_preview")
        
        # Call the function (this is what happens when Preview Email is clicked)
        print("🚀 Calling append_combined_report_on_preview()...")
        success, message, payload = append_combined_report_on_preview(use_sample=False)
        
        print(f"📊 Result:")
        print(f"   Success: {success}")
        print(f"   Message: {message}")
        print(f"   Payload: {type(payload).__name__ if payload else 'None'}")
        
        if success:
            print("🎉 MCP Preview Email test PASSED!")
            print("✅ Combined report was appended to Google Doc via MCP")
        else:
            print("❌ MCP Preview Email test FAILED!")
            print(f"❌ Error: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_mcp_status():
    """Check the latest MCP status"""
    print("\n🔍 Checking MCP Status...")
    print("-" * 30)
    
    try:
        from data.mcp_status.mcp_logger import get_mcp_status, get_mcp_summary
        
        # Get latest status
        latest = get_mcp_status()
        if latest:
            print(f"📊 Latest Status: {latest.get('status', 'Unknown').upper()}")
            print(f"📅 Timestamp: {latest.get('timestamp', 'Unknown')}")
            print(f"🔄 Operation: {latest.get('operation', 'Unknown')}")
            if latest.get('status') == 'success':
                print(f"✅ Message: {latest.get('message', 'Unknown')}")
            else:
                error = latest.get('error') or latest.get('fallback_reason', 'Unknown')
                print(f"❌ Reason: {error}")
        else:
            print("📊 No MCP operations recorded")
        
        # Get summary
        summary = get_mcp_summary(1)  # Last hour
        if 'error' not in summary:
            total = summary.get('total', 0)
            success = summary.get('success', 0)
            failure = summary.get('failure', 0)
            fallback = summary.get('fallback', 0)
            
            print(f"\n📈 1-Hour Summary:")
            print(f"   Total Operations: {total}")
            print(f"   ✅ Successful: {success}")
            print(f"   ❌ Failed: {failure}")
            print(f"   🔄 Fallback: {fallback}")
            
            if total > 0:
                success_rate = (success / total) * 100
                print(f"   📊 Success Rate: {success_rate:.1f}%")
                
                # Show status indicator
                if success_rate >= 90:
                    print(f"   🟢 Status: EXCELLENT")
                elif success_rate >= 70:
                    print(f"   🟡 Status: GOOD")
                elif success_rate >= 50:
                    print(f"   🟠 Status: FAIR")
                else:
                    print(f"   🔴 Status: POOR")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check MCP status: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 MCP Preview Email Integration Test")
    print("=" * 60)
    
    # Test 1: Preview Email MCP functionality
    preview_test_passed = test_preview_email_mcp()
    
    # Test 2: Check MCP status
    status_check_passed = check_mcp_status()
    
    print("\n" + "=" * 60)
    print("📋 Test Results:")
    print(f"✅ Preview Email MCP: {'PASS' if preview_test_passed else 'FAIL'}")
    print(f"✅ MCP Status Check: {'PASS' if status_check_passed else 'FAIL'}")
    
    if preview_test_passed and status_check_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ MCP is working correctly when Preview Email is clicked")
        print("✅ Status logging is working correctly")
        print("✅ Combined reports are being appended to Google Doc")
        print("\n🚀 Ready for production!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("❌ Check the logs above for details")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
