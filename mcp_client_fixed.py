"""
Modified MCP client that works without MCP SDK
Uses direct subprocess communication with our custom server
"""
import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _append_to_google_doc_via_custom_mcp(doc_id: str, text: str) -> Tuple[bool, str]:
    """
    Append text to Google Doc using our custom MCP server without MCP SDK.
    """
    try:
        command = os.environ.get("MCP_GOOGLE_DOCS_MCP_COMMAND", "").strip()
        args_str = os.environ.get("MCP_GOOGLE_DOCS_MCP_ARGS", "").strip()
        
        if not command:
            return False, "MCP_GOOGLE_DOCS_MCP_COMMAND not set"
        
        args_list = []
        if args_str:
            import shlex
            try:
                args_list = shlex.split(args_str)
            except (ValueError, Exception):
                args_list = [a.strip() for a in args_str.split() if a.strip()]
        
        # Run the custom MCP server process
        process = subprocess.Popen(
            [command] + args_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )
        
        # Initialize the MCP server
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        # Send initialization
        init_response = process.communicate(input=json.dumps(init_request) + "\n", timeout=30)
        
        if process.returncode != 0:
            logger.error("MCP server failed to start: %s", init_response[1])
            return False, f"MCP server failed: {init_response[1]}"
        
        # Start a new process for the actual call
        process = subprocess.Popen(
            [command] + args_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy()
        )
        
        # Call the append_text tool
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "append_text",
                "arguments": {
                    "document_id": doc_id,
                    "text": text
                }
            }
        }
        
        # Send tool call
        response = process.communicate(input=json.dumps(tool_request) + "\n", timeout=30)
        
        if process.returncode != 0:
            logger.error("MCP tool call failed: %s", response[1])
            return False, f"MCP tool call failed: {response[1]}"
        
        # Parse response
        try:
            result = json.loads(response[0].strip())
            if "result" in result:
                content = result["result"].get("content", [])
                if content and not result["result"].get("isError", False):
                    logger.info("Successfully appended text via custom MCP: %s", doc_id)
                    return True, ""
                else:
                    error_msg = content[0].get("text", "Unknown error") if content else "Unknown error"
                    logger.warning("Custom MCP returned error: %s", error_msg)
                    return False, error_msg
            else:
                logger.error("Invalid MCP response: %s", result)
                return False, "Invalid MCP response"
        except json.JSONDecodeError as e:
            logger.error("Failed to parse MCP response: %s", e)
            return False, f"Failed to parse MCP response: {e}"
        
    except subprocess.TimeoutExpired:
        logger.error("MCP operation timed out")
        return False, "MCP operation timed out"
    except Exception as e:
        logger.error("Custom MCP append failed: %s", e)
        return False, str(e)


# Replace the original MCP function in the client
def append_to_google_doc(doc_id: str, text: str) -> Tuple[bool, str]:
    """
    Append text to Google Doc using MCP if configured, otherwise fallback to Docs API.
    """
    use_mcp = os.environ.get("MCP_GOOGLE_DOCS_USE_MCP", "").strip().lower() in ("1", "true", "yes")
    
    if use_mcp:
        try:
            # Try our custom MCP implementation first
            success, message = _append_to_google_doc_via_custom_mcp(doc_id, text)
            if success:
                return True, message
            logger.info("Custom MCP failed, trying fallback: %s", message)
        except Exception as e:
            logger.info("Custom MCP failed, trying fallback: %s", e)
    
    # Fallback to Docs API
    from .mcp_docs_client import _append_via_docs_api
    success = _append_via_docs_api(doc_id, text)
    if success:
        return True, "Appended via Docs API (MCP failed)"
    else:
        return False, "Both MCP and Docs API failed"
