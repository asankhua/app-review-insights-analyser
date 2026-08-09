#!/usr/bin/env python3
"""
MCP Logging System - Dedicated logging for MCP operations
Tracks MCP success/failure status with detailed logs and status files
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure dedicated MCP logger
mcp_logger = logging.getLogger('mcp_operations')

class MCPLogger:
    """Dedicated logger for MCP operations"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            # Create mcp_status folder in project root
            project_root = Path(__file__).resolve().parent.parent
            log_dir = project_root / "mcp_status"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup file logging
        self.setup_logging()
        
        # Status files
        self.latest_status_file = self.log_dir / "latest_status.json"
        self.status_history_file = self.log_dir / "status_history.json"
        self.mcp_log_file = self.log_dir / "mcp_operations.log"
        self.error_log_file = self.log_dir / "mcp_errors.log"
        
    def setup_logging(self):
        """Setup dedicated logging configuration"""
        # Create file handler for MCP operations
        file_handler = logging.FileHandler(
            self.log_dir / "mcp_operations.log",
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Create error file handler
        error_handler = logging.FileHandler(
            self.log_dir / "mcp_errors.log",
            mode='a',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Create console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configure logger
        mcp_logger.addHandler(file_handler)
        mcp_logger.addHandler(error_handler)
        mcp_logger.addHandler(console_handler)
        mcp_logger.setLevel(logging.INFO)
    
    def log_mcp_start(self, operation: str, doc_id: str, details: Optional[Dict] = None):
        """Log MCP operation start"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "doc_id": doc_id,
            "status": "started",
            "details": details or {}
        }
        
        # Log to file
        mcp_logger.info(f"MCP START: {operation} for doc {doc_id}")
        
        # Update latest status
        self.update_latest_status(log_entry)
        
        return log_entry
    
    def log_mcp_success(self, operation: str, doc_id: str, message: str, details: Optional[Dict] = None):
        """Log MCP operation success"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "doc_id": doc_id,
            "status": "success",
            "message": message,
            "details": details or {}
        }
        
        # Log to file
        mcp_logger.info(f"MCP SUCCESS: {operation} for doc {doc_id} - {message}")
        
        # Update status files
        self.update_latest_status(log_entry)
        self.add_to_history(log_entry)
        
        return log_entry
    
    def log_mcp_failure(self, operation: str, doc_id: str, error: str, details: Optional[Dict] = None):
        """Log MCP operation failure"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "doc_id": doc_id,
            "status": "failure",
            "error": error,
            "details": details or {}
        }
        
        # Log to file
        mcp_logger.error(f"MCP FAILURE: {operation} for doc {doc_id} - {error}")
        
        # Update status files
        self.update_latest_status(log_entry)
        self.add_to_history(log_entry)
        
        return log_entry
    
    def log_mcp_fallback(self, operation: str, doc_id: str, fallback_reason: str, details: Optional[Dict] = None):
        """Log MCP fallback to direct API"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "doc_id": doc_id,
            "status": "fallback",
            "fallback_reason": fallback_reason,
            "details": details or {}
        }
        
        # Log to file
        mcp_logger.warning(f"MCP FALLBACK: {operation} for doc {doc_id} - {fallback_reason}")
        
        # Update status files
        self.update_latest_status(log_entry)
        self.add_to_history(log_entry)
        
        return log_entry
    
    def update_latest_status(self, status_entry: Dict):
        """Update the latest status file"""
        try:
            with open(self.latest_status_file, 'w', encoding='utf-8') as f:
                json.dump(status_entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            mcp_logger.error(f"Failed to update latest status: {e}")
    
    def add_to_history(self, status_entry: Dict):
        """Add entry to status history"""
        try:
            # Read existing history
            history = []
            if self.status_history_file.exists():
                try:
                    with open(self.status_history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    history = []
            
            # Add new entry
            history.append(status_entry)
            
            # Keep only last 100 entries
            history = history[-100:]
            
            # Write back
            with open(self.status_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            mcp_logger.error(f"Failed to update status history: {e}")
    
    def get_latest_status(self) -> Optional[Dict]:
        """Get the latest MCP status"""
        try:
            if self.latest_status_file.exists():
                with open(self.latest_status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            mcp_logger.error(f"Failed to read latest status: {e}")
        return None
    
    def get_status_summary(self, hours: int = 24) -> Dict:
        """Get MCP status summary for the last N hours"""
        try:
            if not self.status_history_file.exists():
                return {"total": 0, "success": 0, "failure": 0, "fallback": 0}
            
            with open(self.status_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # Filter by time
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_entries = []
            for entry in history:
                try:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time >= cutoff_time:
                        recent_entries.append(entry)
                except (KeyError, ValueError):
                    continue
            
            # Count statuses
            summary = {
                "total": len(recent_entries),
                "success": 0,
                "failure": 0,
                "fallback": 0,
                "period_hours": hours,
                "entries": recent_entries[-10:]  # Last 10 entries
            }
            
            for entry in recent_entries:
                status = entry.get("status", "unknown")
                if status == "success":
                    summary["success"] += 1
                elif status == "failure":
                    summary["failure"] += 1
                elif status == "fallback":
                    summary["fallback"] += 1
            
            return summary
            
        except Exception as e:
            mcp_logger.error(f"Failed to get status summary: {e}")
            return {"error": str(e)}
    
    def create_status_report(self) -> str:
        """Create a human-readable status report"""
        latest = self.get_latest_status()
        summary_24h = self.get_status_summary(24)
        summary_7d = self.get_status_summary(168)  # 7 days
        
        report = []
        report.append("=" * 60)
        report.append("MCP STATUS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Latest status
        if latest:
            report.append("LATEST STATUS:")
            report.append(f"  Operation: {latest.get('operation', 'Unknown')}")
            report.append(f"  Status: {latest.get('status', 'Unknown').upper()}")
            report.append(f"  Document ID: {latest.get('doc_id', 'Unknown')}")
            report.append(f"  Timestamp: {latest.get('timestamp', 'Unknown')}")
            if latest.get('status') == 'success':
                report.append(f"  Message: {latest.get('message', 'Unknown')}")
            elif latest.get('status') in ['failure', 'fallback']:
                report.append(f"  Reason: {latest.get('error') or latest.get('fallback_reason', 'Unknown')}")
            report.append("")
        
        # 24-hour summary
        report.append("24-HOUR SUMMARY:")
        report.append(f"  Total Operations: {summary_24h.get('total', 0)}")
        report.append(f"  Successful: {summary_24h.get('success', 0)}")
        report.append(f"  Failed: {summary_24h.get('failure', 0)}")
        report.append(f"  Fallback: {summary_24h.get('fallback', 0)}")
        
        success_rate = 0
        if summary_24h.get('total', 0) > 0:
            success_rate = (summary_24h.get('success', 0) / summary_24h.get('total', 1)) * 100
        report.append(f"  Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # 7-day summary
        report.append("7-DAY SUMMARY:")
        report.append(f"  Total Operations: {summary_7d.get('total', 0)}")
        report.append(f"  Successful: {summary_7d.get('success', 0)}")
        report.append(f"  Failed: {summary_7d.get('failure', 0)}")
        report.append(f"  Fallback: {summary_7d.get('fallback', 0)}")
        
        success_rate_7d = 0
        if summary_7d.get('total', 0) > 0:
            success_rate_7d = (summary_7d.get('success', 0) / summary_7d.get('total', 1)) * 100
        report.append(f"  Success Rate: {success_rate_7d:.1f}%")
        report.append("")
        
        # Recent entries
        recent_entries = summary_24h.get('entries', [])
        if recent_entries:
            report.append("RECENT OPERATIONS (Last 10):")
            for i, entry in enumerate(recent_entries[-5:], 1):  # Last 5 entries
                timestamp = entry.get('timestamp', 'Unknown')
                operation = entry.get('operation', 'Unknown')
                status = entry.get('status', 'Unknown').upper()
                doc_id = entry.get('doc_id', 'Unknown')[:20] + "..."
                report.append(f"  {i}. {timestamp} - {operation} - {status} - {doc_id}")
        
        report.append("=" * 60)
        
        return "\n".join(report)

# Global MCP logger instance
mcp_status_logger = MCPLogger()

# Convenience functions for easy importing
def log_mcp_start(operation: str, doc_id: str, details: Optional[Dict] = None):
    """Log MCP operation start"""
    return mcp_status_logger.log_mcp_start(operation, doc_id, details)

def log_mcp_success(operation: str, doc_id: str, message: str, details: Optional[Dict] = None):
    """Log MCP operation success"""
    return mcp_status_logger.log_mcp_success(operation, doc_id, message, details)

def log_mcp_failure(operation: str, doc_id: str, error: str, details: Optional[Dict] = None):
    """Log MCP operation failure"""
    return mcp_status_logger.log_mcp_failure(operation, doc_id, error, details)

def log_mcp_fallback(operation: str, doc_id: str, fallback_reason: str, details: Optional[Dict] = None):
    """Log MCP fallback to direct API"""
    return mcp_status_logger.log_mcp_fallback(operation, doc_id, fallback_reason, details)

def get_mcp_status():
    """Get latest MCP status"""
    return mcp_status_logger.get_latest_status()

def get_mcp_summary(hours: int = 24):
    """Get MCP status summary"""
    return mcp_status_logger.get_status_summary(hours)

def create_mcp_status_report():
    """Create MCP status report"""
    return mcp_status_logger.create_status_report()

