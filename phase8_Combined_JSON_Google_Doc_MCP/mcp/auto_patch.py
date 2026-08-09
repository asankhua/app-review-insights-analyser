#!/usr/bin/env python3
"""
Auto-patch for Phase 8 MCP client
This module automatically patches the Phase 8 MCP client when imported
"""
import logging
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

def auto_patch_mcp():
    """Automatically patch Phase 8 MCP client"""
    try:
        # Check if MCP is enabled
        use_mcp = os.environ.get("MCP_GOOGLE_DOCS_USE_MCP", "").strip()
        if not use_mcp or use_mcp != "1":
            return  # MCP not enabled, no patch needed
        
        # Check if we're using the simplified MCP server
        mcp_args = os.environ.get("MCP_GOOGLE_DOCS_MCP_ARGS", "").strip()
        if "google_docs_mcp_server_simple.py" not in mcp_args:
            return  # Not using simplified server, no patch needed
        
        # Import the simplified MCP client
        from mcp.simplified_mcp_client import append_via_simplified_mcp
        
        # Import the Phase 8 client module
        import phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client as mcp_client
        
        # Save original function
        original_append = mcp_client._append_via_mcp
        
        # Create new wrapper that handles both sync/async
        def new_append_via_mcp(doc_id: str, text: str):
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use the async function
                return loop.run_until_complete(append_via_simplified_mcp(doc_id, text))
            except RuntimeError:
                # No running loop, create a new one
                return asyncio.run(append_via_simplified_mcp(doc_id, text))
        
        # Replace the function
        mcp_client._append_via_mcp = new_append_via_mcp
        
        logger.info("Auto-patched Phase 8 MCP client to use simplified version")
        
    except Exception as e:
        logger.warning(f"Failed to auto-patch Phase 8 MCP client: {e}")

# Apply the patch when this module is imported
auto_patch_mcp()
