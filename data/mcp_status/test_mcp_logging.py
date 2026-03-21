#!/usr/bin/env python3
"""
Test MCP Logging - Test the MCP logging system
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_status.mcp_logger import log_mcp_start, log_mcp_success, log_mcp_failure, log_mcp_fallback, get_mcp_status, get_mcp_summary, create_mcp_status_report

def test_logging():
    """Test MCP logging functionality"""
    print("🧪 Testing MCP Logging System...")
    
    doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
    
    # Test 1: Log a success
    print("\n1. Testing success logging...")
    log_mcp_start("append_text", doc_id, {"test": "success_case"})
    time.sleep(0.1)
    log_mcp_success("append_text", doc_id, "Test success message", {"test": "success_case"})
    
    # Test 2: Log a failure
    print("2. Testing failure logging...")
    log_mcp_start("append_text", doc_id, {"test": "failure_case"})
    time.sleep(0.1)
    log_mcp_failure("append_text", doc_id, "Test failure message", {"test": "failure_case"})
    
    # Test 3: Log a fallback
    print("3. Testing fallback logging...")
    log_mcp_start("append_text", doc_id, {"test": "fallback_case"})
    time.sleep(0.1)
    log_mcp_fallback("append_text", doc_id, "Test fallback reason", {"test": "fallback_case"})
    
    # Test 4: Check status
    print("4. Testing status retrieval...")
    latest = get_mcp_status()
    if latest:
        print(f"✅ Latest status: {latest.get('status', 'Unknown')} - {latest.get('message', latest.get('error', latest.get('fallback_reason', 'Unknown')))}")
    else:
        print("❌ No latest status found")
    
    # Test 5: Check summary
    print("5. Testing summary...")
    summary = get_mcp_summary(1)  # Last 1 hour
    if 'error' not in summary:
        print(f"✅ Summary: {summary.get('total', 0)} total, {summary.get('success', 0)} success, {summary.get('failure', 0)} failure, {summary.get('fallback', 0)} fallback")
    else:
        print(f"❌ Summary error: {summary['error']}")
    
    # Test 6: Generate report
    print("6. Testing report generation...")
    report = create_mcp_status_report()
    print("✅ Report generated successfully")
    print("\n" + "="*50)
    print("SAMPLE REPORT:")
    print("="*50)
    print(report[:500] + "..." if len(report) > 500 else report)
    
    print("\n🎉 MCP Logging System Test Complete!")
    return True

def test_file_creation():
    """Test that log files are created"""
    print("\n📁 Testing file creation...")
    
    mcp_status_dir = Path(__file__).resolve().parent.parent / "mcp_status"
    
    expected_files = [
        "latest_status.json",
        "status_history.json", 
        "mcp_operations.log",
        "mcp_errors.log"
    ]
    
    for filename in expected_files:
        file_path = mcp_status_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {filename} exists ({size} bytes)")
        else:
            print(f"❌ {filename} missing")
    
    return True

def main():
    """Main test function"""
    print("🚀 MCP Logging System Test Suite")
    print("=" * 50)
    
    # Test logging functionality
    if not test_logging():
        print("❌ Logging test failed")
        return 1
    
    # Test file creation
    if not test_file_creation():
        print("❌ File creation test failed")
        return 1
    
    print("\n🎉 All tests passed!")
    print("\n📋 Next steps:")
    print("1. Check the mcp_status folder for log files")
    print("2. Use the status monitor: python3 mcp_status/mcp_status_monitor.py")
    print("3. Test with real MCP operations")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
