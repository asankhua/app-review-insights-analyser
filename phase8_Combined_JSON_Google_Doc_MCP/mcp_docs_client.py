"""
Phase 8: Append combined report to a Google Doc.
- Primary: MCP (Model Context Protocol) when configured — e.g. google-docs-mcp-server append_text tool.
- Fallback: Google Docs REST API with service account credentials.
"""
import asyncio
import json
import logging
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

IST = ZoneInfo("Asia/Kolkata")

logger = logging.getLogger(__name__)

# Import CombinedReportPayload
try:
    from .models.combined_report import CombinedReportPayload
except ImportError:
    # Fallback for direct execution
    try:
        from phase8_Combined_JSON_Google_Doc_MCP.models.combined_report import CombinedReportPayload
    except ImportError:
        # If still not found, define a placeholder
        CombinedReportPayload = None

# Import logging functions
try:
    from data.mcp_status.mcp_logger import log_mcp_start, log_mcp_success, log_mcp_failure, log_mcp_fallback
except ImportError:
    # If logging module not available, continue without logging
    log_mcp_start = log_mcp_success = log_mcp_failure = log_mcp_fallback = lambda *args, **kwargs: None

def _append_via_simplified_mcp(doc_id: str, text: str, operation: str, log_mcp_start, log_mcp_success, log_mcp_failure) -> tuple[bool, str]:
    """
    Append text to Google Doc using simplified MCP server
    """
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
        process = subprocess.run(
            [command] + args_list,
            input=json.dumps(mcp_message) + "\n",
            text=True,
            capture_output=True,
            env=env,
            timeout=30
        )
        
        if process.returncode == 0:
            try:
                response = json.loads(process.stdout.strip())
                result = response.get("result", {})
                content = result.get("content", [])
                if content and not result.get("isError", False):
                    message = "mcp success"
                    log_mcp_success(operation, doc_id, message, {
                        "mcp_response": result,
                        "process_returncode": process.returncode,
                        "status": "mcp_success"
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
                    "stdout": process.stdout[:200],
                    "process_returncode": process.returncode
                })
                return False, error_msg
        else:
            error_msg = process.stderr.strip() or "MCP server failed"
            log_mcp_failure(operation, doc_id, error_msg, {
                "stderr": process.stderr[:200],
                "process_returncode": process.returncode
            })
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "MCP server timeout"
        log_mcp_failure(operation, doc_id, error_msg, {"timeout": True})
        return False, error_msg
    except Exception as e:
        error_msg = f"Simplified MCP append failed: {e}"
        log_mcp_failure(operation, doc_id, error_msg, {"exception": str(e)})
        return False, error_msg


def _extract_doc_id(doc_id_or_url: str) -> str:
    """Extract document ID from URL or return as-is if already an ID."""
    s = (doc_id_or_url or "").strip()
    if not s:
        return ""
    m = re.match(r".*/docs\.google\.com/document/d/([a-zA-Z0-9_-]+)", s)
    if m:
        return m.group(1)
    if re.match(r"^[a-zA-Z0-9_-]+$", s):
        return s
    return s


def _is_mcp_configured() -> bool:
    """True if MCP path for Google Docs is enabled and command is set."""
    use_mcp = os.environ.get("MCP_GOOGLE_DOCS_USE_MCP", "").strip().lower() in ("1", "true", "yes")
    cmd = os.environ.get("MCP_GOOGLE_DOCS_MCP_COMMAND", "").strip()
    return bool(use_mcp and cmd)


def _append_via_mcp(doc_id: str, text: str) -> tuple[bool, str]:
    """
    Append text to a Google Doc by calling an MCP server tool (e.g. append_text).
    Expects MCP_GOOGLE_DOCS_USE_MCP=1, MCP_GOOGLE_DOCS_MCP_COMMAND (and optional MCP_GOOGLE_DOCS_MCP_ARGS).
    Server env: SERVICE_ACCOUNT_PATH, SUBJECT_EMAIL (or GOOGLE_DRIVE_CREDENTIALS_PATH, MCP_GOOGLE_DOCS_SUBJECT_EMAIL).
    Returns (True, "") on success, (False, error_message) otherwise.
    """
    # Import logging functions
    try:
        from mcp_status.mcp_logger import log_mcp_start, log_mcp_success, log_mcp_failure, log_mcp_fallback
    except ImportError:
        # If logging module not available, continue without logging
        log_mcp_start = log_mcp_success = log_mcp_failure = log_mcp_fallback = lambda *args, **kwargs: None
    
    operation = "append_text"
    
    # Log operation start
    log_mcp_start(operation, doc_id, {"text_length": len(text)})
    
    try:
        from mcp import ClientSession, StdioServerParameters, stdio_client
    except ImportError as e:
        error_msg = f"MCP SDK not available; cannot use MCP path: {e}"
        log_mcp_fallback(operation, doc_id, error_msg, {"reason": "mcp_sdk_missing"})
        logger.debug(error_msg)
        # Try to use simplified MCP server instead
        return _append_via_simplified_mcp(doc_id, text, operation, log_mcp_start, log_mcp_success, log_mcp_failure)

    command = os.environ.get("MCP_GOOGLE_DOCS_MCP_COMMAND", "").strip()
    args_str = os.environ.get("MCP_GOOGLE_DOCS_MCP_ARGS", "").strip()
    if not command:
        return False, "MCP_GOOGLE_DOCS_MCP_COMMAND not set"

    args_list = []
    if args_str:
        try:
            args_list = json.loads(args_str) if args_str.startswith("[") else shlex.split(args_str)
        except (json.JSONDecodeError, ValueError):
            args_list = [a.strip() for a in args_str.split() if a.strip()]

    command, args_list = _resolve_mcp_command(command, args_list)

    service_account_path = os.environ.get("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH") or os.environ.get(
        "GOOGLE_DRIVE_CREDENTIALS_PATH"
    )
    subject_email = os.environ.get("MCP_GOOGLE_DOCS_SUBJECT_EMAIL", "").strip()
    env = {**os.environ}
    if service_account_path:
        resolved = os.path.expanduser(service_account_path)
        if not os.path.isabs(resolved):
            resolved = os.path.abspath(resolved)
        env["SERVICE_ACCOUNT_PATH"] = resolved
    if subject_email:
        env["SUBJECT_EMAIL"] = subject_email
    # Ensure PATH includes common install locations (e.g. uvx from brew) when run from minimal envs (e.g. IDE)
    path_prefixes = [d for d in ("/opt/homebrew/bin", "/usr/local/bin", os.path.expanduser("~/.local/bin")) if os.path.isdir(d)]
    if path_prefixes:
        old_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(path_prefixes) + (os.pathsep + old_path if old_path else "")

    async def _run_mcp_append() -> tuple[bool, str]:
        server_params = StdioServerParameters(
            command=command,
            args=args_list,
            env=env,
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    name="append_text",
                    arguments={"document_id": doc_id, "text": "\n" + text},
                )
                if getattr(result, "isError", False) or (hasattr(result, "content") and not result.content):
                    err_msg = str(result)
                    if hasattr(result, "content") and result.content and isinstance(result.content, list):
                        parts = [getattr(c, "text", str(c)) for c in result.content]
                        if parts:
                            err_msg = " ".join(str(p) for p in parts)
                    logger.warning("MCP append_text returned error or empty: %s", result)
                    log_mcp_failure(operation, doc_id, err_msg, {"mcp_result": str(result)})
                    return False, err_msg
                logger.info("Appended combined report to Google Doc via MCP: %s", doc_id)
                log_mcp_success(operation, doc_id, "Appended via MCP", {"mcp_result": str(result)})
                return True, ""

    try:
        return asyncio.run(_run_mcp_append())
    except Exception as e:
        error_msg = f"MCP append to Google Doc failed: {e}"
        logger.warning(error_msg)
        log_mcp_failure(operation, doc_id, error_msg, {"exception": str(e)})
        return False, error_msg


def _get_credentials():
    """Build Google API credentials from env (service account JSON or path)."""
    try:
        from google.oauth2 import service_account
    except ImportError:
        logger.debug("google.oauth2 not available")
        return None

    credentials_json = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON")
    credentials_path = (
        os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH")
        or os.environ.get("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH")
    )

    if credentials_json:
        try:
            info = json.loads(credentials_json)
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            logger.warning("Invalid GOOGLE_DRIVE_CREDENTIALS_JSON: %s", e)
            return None
    if credentials_path:
        expanded = os.path.expanduser(credentials_path)
        if os.path.isfile(expanded):
            try:
                return service_account.Credentials.from_service_account_file(expanded)
            except Exception as e:
                logger.warning("Invalid credentials file %s: %s", expanded, e)
                return None
    return None


def _append_via_docs_api(doc_id: str, text: str) -> bool:
    """
    Append text to a Google Doc using the Google Docs REST API (fallback when MCP is not used).
    Updated to use production-ready credentials handling.
    """
    try:
        # Import production client
        from production_google_docs_client import get_google_credentials
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Get credentials using production client
        credentials_json = get_google_credentials()
        if not credentials_json:
            logger.warning("Google credentials not configured; cannot use Docs API fallback.")
            return False
        
        # Create credentials from JSON
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
    except Exception as e:
        logger.warning("Google credentials not configured; cannot use Docs API fallback.")
        return False

    try:
        service = build("docs", "v1", credentials=credentials)
        doc = service.documents().get(documentId=doc_id).execute()
        content = doc.get("body", {}).get("content", [])
        end_index = 1
        for el in content:
            end_index = el.get("endIndex", end_index)
        requests = [
            {
                "insertText": {
                    "location": {"index": end_index - 1},
                    "text": "\n" + text,
                }
            }
        ]
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests},
        ).execute()
        logger.info("Appended combined report to Google Doc via Docs API: %s", doc_id)
        return True
    except Exception as e:
        logger.warning("Docs API append failed: %s", e)
        return False


def append_to_google_doc(
    payload: CombinedReportPayload,
    doc_id: Optional[str] = None,
    include_timestamp: bool = False,
) -> tuple[bool, str]:
    """
    Append the combined report (human-readable text) to the given Google Doc.
    - If MCP is configured (MCP_GOOGLE_DOCS_USE_MCP=1 and MCP_GOOGLE_DOCS_MCP_COMMAND set), tries MCP first.
    - Fallback: Google Docs API with GOOGLE_DRIVE_CREDENTIALS_* and GOOGLE_DOC_ID.
    - include_timestamp: when True, prepends "--- Appended at YYYY-MM-DD HH:MM:SS IST ---" to the text.
    Returns (success, message) for UI. success True if append succeeded; message is user-facing (e.g. "Appended to Google Doc" or error reason).
    """
    doc_id = _extract_doc_id(doc_id or os.environ.get("GOOGLE_DOC_ID", ""))
    if not doc_id:
        logger.info("GOOGLE_DOC_ID not set; skipping append to Google Doc.")
        return False, ""

    text = payload.to_human_readable()
    if include_timestamp:
        ts = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        text = f"--- Appended at {ts} IST ---\n\n{text}"
    
    if not text:
        return True, ""

    if _is_mcp_configured():
        # Prepare status text first
        mcp_status_text = "\n\n📊 **Append Method**: MCP (Model Context Protocol)\n✅ **Status**: MCP SUCCESS - Report appended via Model Context Protocol"
        fallback_status_text = "\n\n📊 **Append Method**: Google Docs API (Fallback)\n🔄 **Status**: MCP FAILED, FALLBACK SUCCESS - Report appended via Google Docs API"
        fallback_fail_text = "\n\n📊 **Append Method**: Google Docs API (Fallback)\n❌ **Status**: MCP FAILED, FALLBACK FAILED - Both MCP and Google Docs API failed"
        
        # Add status text to the content BEFORE calling MCP
        text += mcp_status_text
        
        # Now call MCP with the complete content (including status text)
        mcp_ok, mcp_err = _append_via_mcp(doc_id, text)
        if mcp_ok:
            # Log MCP success with specific status
            try:
                from data.mcp_status.mcp_logger import log_mcp_success
                log_mcp_success("append_text", doc_id, "mcp success", {"status": "mcp_success"})
            except ImportError:
                pass
            return True, "Google Doc: appended successfully via MCP."
        try:
            if _append_via_docs_api(doc_id, text):
                # Log MCP fail with fallback success
                try:
                    from data.mcp_status.mcp_logger import log_mcp_fallback
                    log_mcp_fallback("append_text", doc_id, "mcp fail, fallback success", {
                        "status": "mcp_fail_fallback_success",
                        "mcp_error": mcp_err,
                        "fallback_method": "docs_api"
                    })
                except ImportError:
                    pass
                return True, "Google Doc: appended via Docs API (MCP failed)."
        except Exception as e2:
            # Log fallback failure
            try:
                from data.mcp_status.mcp_logger import log_mcp_failure
                log_mcp_failure("append_text", doc_id, "mcp fail, fallback fail", {
                    "status": "mcp_fail_fallback_fail",
                    "mcp_error": mcp_err,
                    "fallback_error": str(e2)
                })
            except ImportError:
                pass
            return False, f"MCP failed ({mcp_err}); Docs API fallback failed: {e2}"
        return False, f"MCP append failed: {mcp_err}; Docs API fallback also failed."

    # When not using MCP, append directly with API
    try:
        # Prepare status text for direct API
        api_status_text = "\n\n📊 **Append Method**: Google Docs API (Direct)\n✅ **Status**: SUCCESS - Report appended via Google Docs API"
        api_fail_text = "\n\n📊 **Append Method**: Google Docs API (Direct)\n❌ **Status**: FAILED - Could not append via Google Docs API"
        
        # Add status text to the content BEFORE calling API
        text += api_status_text
        
        ok = _append_via_docs_api(doc_id, text)
        return ok, "Google Doc: appended successfully." if ok else "Google Doc: append failed."
    except Exception as e:
        return False, f"Google Doc: {str(e)}"
