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
import sys
from typing import Optional

from .models.combined_report import CombinedReportPayload

logger = logging.getLogger(__name__)


def _resolve_mcp_command(command: str, args_list: list) -> tuple[str, list]:
    """Use installed google-docs-mcp-server when uvx is not found."""
    if command != "uvx":
        return command, args_list
    try:
        import shutil

        if shutil.which("uvx"):
            return "uvx", args_list if args_list else ["google-docs-mcp-server"]
    except Exception:
        pass
    # Fallback: use google-docs-mcp-server from same env as current Python (pip install google-docs-mcp-server)
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    gdocs_bin = os.path.join(bin_dir, "google-docs-mcp-server")
    if os.path.isfile(gdocs_bin) and os.access(gdocs_bin, os.X_OK):
        return gdocs_bin, []
    return sys.executable, ["-m", "google_docs_mcp_server"]


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
    try:
        from mcp import ClientSession, StdioServerParameters, stdio_client
    except ImportError as e:
        logger.debug("MCP SDK not available; cannot use MCP path: %s", e)
        return False, str(e)

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
                    return False, err_msg
                logger.info("Appended combined report to Google Doc via MCP: %s", doc_id)
                return True, ""

    try:
        return asyncio.run(_run_mcp_append())
    except Exception as e:
        logger.warning("MCP append to Google Doc failed: %s", e)
        return False, str(e)


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
    """
    creds = _get_credentials()
    if not creds:
        logger.warning("Google credentials not configured; cannot use Docs API fallback.")
        return False

    try:
        from googleapiclient.discovery import build
    except ImportError:
        logger.warning("google-api-python-client not available; cannot use Docs API fallback.")
        return False

    try:
        service = build("docs", "v1", credentials=creds)
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
) -> tuple[bool, str]:
    """
    Append the combined report (human-readable text) to the given Google Doc.
    - If MCP is configured (MCP_GOOGLE_DOCS_USE_MCP=1 and MCP_GOOGLE_DOCS_MCP_COMMAND set), tries MCP first.
    - Fallback: Google Docs API with GOOGLE_DRIVE_CREDENTIALS_* and GOOGLE_DOC_ID.
    Returns (success, message) for UI. success True if append succeeded; message is user-facing (e.g. "Appended to Google Doc" or error reason).
    """
    doc_id = _extract_doc_id(doc_id or os.environ.get("GOOGLE_DOC_ID", ""))
    if not doc_id:
        logger.info("GOOGLE_DOC_ID not set; skipping append to Google Doc.")
        return False, ""

    text = payload.to_human_readable()
    if not text:
        return True, ""

    if _is_mcp_configured():
        mcp_ok, mcp_err = _append_via_mcp(doc_id, text)
        if mcp_ok:
            return True, "Google Doc: appended successfully via MCP."
        try:
            if _append_via_docs_api(doc_id, text):
                return True, "Google Doc: appended via Docs API (MCP failed)."
        except Exception as e2:
            return False, f"MCP failed ({mcp_err}); Docs API fallback failed: {e2}"
        return False, f"MCP append failed: {mcp_err}; Docs API fallback also failed."

    try:
        ok = _append_via_docs_api(doc_id, text)
        return ok, "Google Doc: appended successfully." if ok else "Google Doc: append failed."
    except Exception as e:
        return False, f"Google Doc: {str(e)}"
