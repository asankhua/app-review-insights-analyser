#!/usr/bin/env python3
"""
MCP Status Monitor - Real-time monitoring and reporting of MCP operations
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.mcp_status.mcp_logger import get_mcp_status, get_mcp_summary, create_mcp_status_report

def print_status():
    """Print current MCP status"""
    print("🔍 MCP Status Monitor")
    print("=" * 50)
    
    latest = get_mcp_status()
    if latest:
        print(f"📊 Latest Status: {latest.get('status', 'Unknown').upper()}")
        print(f"📅 Timestamp: {latest.get('timestamp', 'Unknown')}")
        print(f"🔄 Operation: {latest.get('operation', 'Unknown')}")
        print(f"📄 Document ID: {latest.get('doc_id', 'Unknown')}")
        
        if latest.get('status') == 'success':
            print(f"✅ Message: {latest.get('message', 'Unknown')}")
        elif latest.get('status') in ['failure', 'fallback']:
            error = latest.get('error') or latest.get('fallback_reason', 'Unknown')
            print(f"❌ Reason: {error}")
    else:
        print("📊 No MCP operations recorded yet")

def print_summary(hours: int = 24):
    """Print MCP summary for specified hours"""
    print(f"\n📈 {hours}-Hour Summary:")
    print("-" * 30)
    
    summary = get_mcp_summary(hours)
    if 'error' in summary:
        print(f"❌ Error: {summary['error']}")
        return
    
    total = summary.get('total', 0)
    success = summary.get('success', 0)
    failure = summary.get('failure', 0)
    fallback = summary.get('fallback', 0)
    
    print(f"Total Operations: {total}")
    print(f"✅ Successful: {success}")
    print(f"❌ Failed: {failure}")
    print(f"🔄 Fallback: {fallback}")
    
    if total > 0:
        success_rate = (success / total) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Show success indicator
        if success_rate >= 90:
            print("🟢 Status: EXCELLENT")
        elif success_rate >= 70:
            print("🟡 Status: GOOD")
        elif success_rate >= 50:
            print("🟠 Status: FAIR")
        else:
            print("🔴 Status: POOR")
    else:
        print("📊 No operations in this period")

def print_recent_entries(count: int = 5):
    """Print recent MCP entries"""
    print(f"\n📝 Recent Operations (Last {count}):")
    print("-" * 40)
    
    summary = get_mcp_summary(24)
    if 'error' in summary:
        print(f"❌ Error: {summary['error']}")
        return
    
    entries = summary.get('entries', [])
    if not entries:
        print("No recent operations")
        return
    
    for i, entry in enumerate(entries[-count:], 1):
        timestamp = entry.get('timestamp', 'Unknown')
        operation = entry.get('operation', 'Unknown')
        status = entry.get('status', 'Unknown').upper()
        doc_id = entry.get('doc_id', 'Unknown')[:20] + "..."
        
        # Status emoji
        status_emoji = {
            'SUCCESS': '✅',
            'FAILURE': '❌',
            'FALLBACK': '🔄',
            'STARTED': '⏳'
        }.get(status, '❓')
        
        print(f"{i}. {timestamp} - {operation} - {status_emoji} {status} - {doc_id}")

def print_full_report():
    """Print full MCP status report"""
    report = create_mcp_status_report()
    print(report)

def monitor_mode(interval: int = 10):
    """Continuous monitoring mode"""
    print(f"🔄 Starting MCP Monitor (updates every {interval} seconds)")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            # Clear screen
            print("\033[2J\033[H", end="")
            
            # Print status
            print_status()
            print_summary(1)  # Last hour
            print_recent_entries(3)  # Last 3 entries
            
            print(f"\n⏰ Next update in {interval} seconds...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 MCP Monitor stopped")

def main():
    """Main function"""
    args = sys.argv[1:]
    
    if not args or args[0] == 'status':
        print_status()
        print_summary(24)
        print_recent_entries()
        
    elif args[0] == 'summary':
        hours = int(args[1]) if len(args) > 1 else 24
        print_summary(hours)
        
    elif args[0] == 'recent':
        count = int(args[1]) if len(args) > 1 else 5
        print_recent_entries(count)
        
    elif args[0] == 'report':
        print_full_report()
        
    elif args[0] == 'monitor':
        interval = int(args[1]) if len(args) > 1 else 10
        monitor_mode(interval)
        
    else:
        print("MCP Status Monitor")
        print("=" * 20)
        print("Usage:")
        print("  python3 mcp_status_monitor.py [command] [options]")
        print("")
        print("Commands:")
        print("  status     - Show current status and 24h summary")
        print("  summary N  - Show summary for last N hours")
        print("  recent N   - Show last N operations")
        print("  report     - Show full detailed report")
        print("  monitor N  - Continuous monitoring (N seconds interval)")
        print("")
        print("Examples:")
        print("  python3 mcp_status_monitor.py")
        print("  python3 mcp_status_monitor.py summary 12")
        print("  python3 mcp_status_monitor.py recent 10")
        print("  python3 mcp_status_monitor.py report")
        print("  python3 mcp_status_monitor.py monitor 5")

if __name__ == "__main__":
    main()

