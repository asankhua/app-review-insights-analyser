#!/usr/bin/env python3
"""
MCP Client with Logging - Enhanced MCP client with dedicated logging
"""
import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict

# Add project root to path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_status.mcp_logger import log_mcp_start, log_mcp_success, log_mcp_failure, log_mcp_fallback

logger = logging.getLogger(__name__)

async def append_via_simplified_mcp_logged(doc_id: str, text: str) -> tuple[bool, str]:
    """
    Append text to Google Doc using simplified MCP server with logging
    """
    operation = "append_text"
    
    # Log operation start
    log_mcp_start(operation, doc_id, {"text_length": len(text)})
    
    try:
        command = os.environ.get("MCP_GOOGLE_DOCS_MCP_COMMAND", "").strip()
        args_str = os.environ.get("MCP_GOOGLE_DOCS_MCP_ARGS", "").strip()
        
        if not command:
            error = "MCP_GOOGLE_DOCS_MCP_COMMAND not set"
            log_mcp_failure(operation, doc_id, error, {"reason": "missing_command"})
            return False, error
        
        # Parse arguments
        args_list = []
        if args_str:
            try:
                args_list = json.loads(args_str) if args_str.startswith("[") else args_str.split()
            except (json.JSONDecodeError, ValueError):
                args_list = [a.strip() for a in args_str.split() if a.strip()]
        
        # Prepare environment
        service_account_path = os.environ.get("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH") or os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH")
        subject_email = os.environ.get("MCP_GOOGLE_DOCS_SUBJECT_EMAIL", "").strip()
        
        env = {**os.environ}
        if service_account_path:
            import os.path as path_module
            resolved = path_module.expanduser(service_account_path)
            if not path_module.isabs(resolved):
                resolved = path_module.abspath(resolved)
            env["SERVICE_ACCOUNT_PATH"] = resolved
        if subject_email:
            env["SUBJECT_EMAIL"] = subject_email
        
        # Create MCP protocol message for append_text
        mcp_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "append_text",
                "arguments": {
                    "document_id": doc_id,
                    "text": text
                }
            }
        }
        
        # Log MCP server start
        log_mcp_start("mcp_server", doc_id, {"command": command, "args": args_list})
        
        # Run the simplified MCP server
        process = await asyncio.create_subprocess_exec(
            command, *args_list,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        # Send the MCP message
        message_json = json.dumps(mcp_message) + "\n"
        stdout, stderr = await process.communicate(message_json.encode())
        
        if process.returncode == 0:
            try:
                response = json.loads(stdout.decode())
                result = response.get("result", {})
                content = result.get("content", [])
                if content and not result.get("isError", False):
                    message = content[0].get("text", "Unknown success")
                    log_mcp_success(operation, doc_id, message, {
                        "mcp_response": result,
                        "process_returncode": process.returncode
                    })
                    return True, message
                else:
                    error_msg = content[0].get("text", "Unknown error") if content else "Unknown error"
                    log_mcp_failure(operation, doc_id, error_msg, {
                        "mcp_response": result,
                        "process_returncode": process.returncode
                    })
                    return False, error_msg
            except json.JSONDecodeError:
                error_msg = "Failed to parse MCP response"
                log_mcp_failure(operation, doc_id, error_msg, {
                    "stdout": stdout.decode()[:200],
                    "process_returncode": process.returncode
                })
                return False, error_msg
        else:
            error_msg = stderr.decode().strip() or "MCP server failed"
            log_mcp_failure(operation, doc_id, error_msg, {
                "stderr": stderr.decode()[:200],
                "process_returncode": process.returncode
            })
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Simplified MCP append failed: {e}"
        log_mcp_failure(operation, doc_id, error_msg, {"exception": str(e)})
        return False, error_msg

# Monkey patch the _append_via_mcp function to use our logged version
def patch_mcp_client_with_logging():
    """Patch the MCP client to use simplified version with logging"""
    try:
        import phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client as mcp_client
        
        # Save original function
        original_append = mcp_client._append_via_mcp
        
        # Create new async wrapper
        async def new_append_via_mcp(doc_id: str, text: str):
            return await append_via_simplified_mcp_logged(doc_id, text)
        
        # Replace the function
        mcp_client._append_via_mcp = new_append_via_mcp
        
        logger.info("Patched MCP client to use simplified version with logging")
        return True
        
    except Exception as e:
        logger.error(f"Failed to patch MCP client with logging: {e}")
        return False

if __name__ == "__main__":
    # Test the simplified MCP client with logging
    import asyncio
    
    async def test():
        doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
        text = "\n--- MCP Client with Logging Test ---\nTesting MCP client with dedicated logging."
        
        success, message = await append_via_simplified_mcp_logged(doc_id, text)
        print(f"Success: {success}, Message: {message}")
    
    asyncio.run(test())

