# MCP Status - Dedicated Logging and Monitoring

## 🎯 Overview

This folder provides comprehensive logging and monitoring for MCP (Model Context Protocol) operations. It tracks MCP success/failure status with detailed logs and real-time monitoring capabilities.

## 📁 Files

### Core Logging System
- `mcp_logger.py` - Dedicated MCP logging system with status tracking
- `mcp_status_monitor.py` - Real-time status monitoring and reporting

### Testing
- `test_mcp_logging.py` - Test script for logging functionality

### Generated Files (Auto-created)
- `latest_status.json` - Latest MCP operation status
- `status_history.json` - Historical MCP operation logs (last 100 entries)
- `mcp_operations.log` - All MCP operation logs
- `mcp_errors.log` - MCP error logs only

## 🚀 Quick Start

### 1. Check Current Status
```bash
python3 mcp_status/mcp_status_monitor.py
```

### 2. View Full Report
```bash
python3 mcp_status/mcp_status_monitor.py report
```

### 3. Monitor Real-time
```bash
python3 mcp_status/mcp_status_monitor.py monitor 5
```

### 4. Test Logging System
```bash
python3 mcp_status/test_mcp_logging.py
```

## 📊 Status Information

### Status Types
- **SUCCESS** ✅ - MCP operation completed successfully
- **FAILURE** ❌ - MCP operation failed
- **FALLBACK** 🔄 - MCP failed, fell back to Google Docs API
- **STARTED** ⏳ - MCP operation started

### Status Indicators
- 🟢 **EXCELLENT** - Success rate ≥ 90%
- 🟡 **GOOD** - Success rate ≥ 70%
- 🟠 **FAIR** - Success rate ≥ 50%
- 🔴 **POOR** - Success rate < 50%

## 🔧 Monitoring Commands

### Basic Status
```bash
# Show current status and 24h summary
python3 mcp_status/mcp_status_monitor.py status

# Show summary for specific hours
python3 mcp_status/mcp_status_monitor.py summary 12

# Show recent operations
python3 mcp_status/mcp_status_monitor.py recent 10
```

### Advanced Monitoring
```bash
# Full detailed report
python3 mcp_status/mcp_status_monitor.py report

# Continuous monitoring (updates every 5 seconds)
python3 mcp_status/mcp_status_monitor.py monitor 5

# Continuous monitoring (updates every 30 seconds)
python3 mcp_status/mcp_status_monitor.py monitor 30
```

## 📋 Log Files

### latest_status.json
```json
{
  "timestamp": "2026-03-21T09:25:10.942845",
  "operation": "append_text",
  "doc_id": "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0",
  "status": "success",
  "message": "Appended via MCP",
  "details": {...}
}
```

### status_history.json
Array of the last 100 MCP operations with full details.

### mcp_operations.log
```
2026-03-21 09:25:10 - mcp_operations - INFO - MCP START: append_text for doc 18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0
2026-03-21 09:25:10 - mcp_operations - INFO - MCP SUCCESS: append_text for doc 18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0 - Appended via MCP
```

### mcp_errors.log
```
2026-03-21 09:25:10 - mcp_operations - ERROR - MCP FAILURE: append_text for doc 18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0 - MCP server failed
```

## 🔍 Integration

### Automatic Logging
The logging system is automatically integrated with:
- Phase 8 MCP client operations
- Simplified MCP server operations
- Fallback to Google Docs API

### Manual Logging
```python
from mcp_status.mcp_logger import log_mcp_success, log_mcp_failure

# Log success
log_mcp_success("append_text", doc_id, "Operation completed", {"details": "..."})

# Log failure
log_mcp_failure("append_text", doc_id, "Operation failed", {"error": "..."})
```

## 📈 Usage Examples

### Example 1: Check MCP Health
```bash
# Quick health check
python3 mcp_status/mcp_status_monitor.py

# Look for:
# ✅ High success rate (≥ 90%)
# 🟢 Status indicator
# Recent successful operations
```

### Example 2: Troubleshoot MCP Issues
```bash
# Check recent failures
python3 mcp_status/mcp_status_monitor.py recent 20

# Look for:
# ❌ Recent failures
# 🔄 Fallback operations
# Error messages and patterns
```

### Example 3: Monitor Production
```bash
# Real-time monitoring
python3 mcp_status/mcp_status_monitor.py monitor 10

# Watch for:
# Status changes
# Success/failure patterns
# Error frequency
```

## 🔧 Configuration

### Log Rotation
- History limited to last 100 entries
- Logs are automatically pruned
- Error logs kept separate for easy filtering

### Environment Variables
No additional configuration required. The logging system automatically detects MCP operations.

### Custom Logging Level
```python
import logging
logging.getLogger('mcp_operations').setLevel(logging.DEBUG)
```

## 🚨 Troubleshooting

### Common Issues

#### "No MCP operations recorded yet"
- MCP hasn't been used yet
- Check MCP configuration
- Trigger an MCP operation

#### "Permission denied" errors
- Check write permissions to mcp_status folder
- Ensure folder exists and is writable

#### "Failed to read latest status"
- Check if latest_status.json exists
- Verify file permissions
- Test logging system

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Report Interpretation

### Success Rate
- **≥ 90%**: MCP working excellently
- **70-89%**: MCP working well with occasional issues
- **50-69%**: MCP has issues, check configuration
- **< 50%**: MCP has serious problems, investigate immediately

### Fallback Rate
- **Low fallback rate**: MCP working well
- **High fallback rate**: MCP configuration issues
- **Consistent fallback**: Check MCP server and credentials

### Error Patterns
- **Authentication errors**: Check service account permissions
- **Network errors**: Check connectivity and timeouts
- **Server errors**: Check MCP server logs

## 🎯 Best Practices

### 1. Regular Monitoring
- Check status daily
- Monitor success rates weekly
- Investigate sudden changes

### 2. Alert Thresholds
- Alert if success rate < 80%
- Alert if fallback rate > 20%
- Alert on consecutive failures

### 3. Log Management
- Archive old logs periodically
- Monitor log file sizes
- Backup important status data

---

## 🎉 Summary

The MCP Status system provides comprehensive visibility into your MCP operations:

- ✅ **Real-time monitoring** of MCP operations
- ✅ **Detailed logging** of success/failure events
- ✅ **Status tracking** with success rates and trends
- ✅ **Easy troubleshooting** with detailed error information
- ✅ **Production ready** with automatic log management

**Use this system to keep your MCP implementation running smoothly!**
