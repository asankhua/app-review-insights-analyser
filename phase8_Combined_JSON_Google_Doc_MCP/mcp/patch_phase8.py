#!/usr/bin/env python3
"""
MCP Patch for Phase 8 - Integrates simplified MCP client
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

def patch_phase8_mcp():
    """Patch Phase 8 MCP client to use simplified version"""
    try:
        # Import the simplified MCP client
        from mcp.simplified_mcp_client import append_via_simplified_mcp
        
        # Import the Phase 8 client module
        import phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client as mcp_client
        
        # Save original function
        original_append = mcp_client._append_via_mcp
        
        # Create new wrapper that handles both sync/async
        def new_append_via_mcp(doc_id: str, text: str):
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use the async function
                return loop.run_until_complete(append_via_simplified_mcp(doc_id, text))
            except RuntimeError:
                # No running loop, create a new one
                return asyncio.run(append_via_simplified_mcp(doc_id, text))
        
        # Replace the function
        mcp_client._append_via_mcp = new_append_via_mcp
        
        logger.info("Successfully patched Phase 8 MCP client to use simplified version")
        return True
        
    except Exception as e:
        logger.error(f"Failed to patch Phase 8 MCP client: {e}")
        return False

def test_patch():
    """Test the patched MCP client"""
    try:
        # Apply the patch
        if not patch_phase8_mcp():
            return False
        
        # Test the patched function
        from phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client import _append_via_mcp
        
        doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
        text = "\n--- Patch Test ---\nTesting patched MCP client."
        
        print("Testing patched MCP client...")
        success, message = _append_via_mcp(doc_id, text)
        print(f"Success: {success}, Message: {message}")
        
        return success
        
    except Exception as e:
        print(f"Patch test failed: {e}")
        return False

if __name__ == "__main__":
    if test_patch():
        print("✅ MCP patch test successful!")
    else:
        print("❌ MCP patch test failed!")

