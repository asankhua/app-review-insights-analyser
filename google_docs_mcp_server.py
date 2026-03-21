#!/usr/bin/env python3
"""
Simple MCP Server for Google Docs
This provides the append_text tool using the existing Google Docs API
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        Tool,
        TextContent,
    )
except ImportError:
    print("MCP SDK not available. Please install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("google-docs-simple")


def _get_credentials():
    """Build Google API credentials from environment."""
    try:
        from google.oauth2 import service_account
    except ImportError:
        logger.error("google.oauth2 not available")
        return None

    # Try JSON content first
    credentials_json = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON")
    if credentials_json:
        try:
            info = json.loads(credentials_json)
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            logger.warning("Invalid GOOGLE_DRIVE_CREDENTIALS_JSON: %s", e)
    
    # Try file path
    credentials_path = (
        os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH")
        or os.environ.get("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH")
    )
    if credentials_path:
        expanded = os.path.expanduser(credentials_path)
        if os.path.isfile(expanded):
            try:
                return service_account.Credentials.from_service_account_file(expanded)
            except Exception as e:
                logger.warning("Invalid credentials file %s: %s", expanded, e)
    
    return None


def _append_to_doc(doc_id: str, text: str) -> bool:
    """Append text to Google Doc using Google Docs API."""
    creds = _get_credentials()
    if not creds:
        logger.error("Google credentials not configured")
        return False

    try:
        from googleapiclient.discovery import build
    except ImportError:
        logger.error("google-api-python-client not available")
        return False

    try:
        service = build("docs", "v1", credentials=creds)
        
        # Get document to find end index
        doc = service.documents().get(documentId=doc_id).execute()
        content = doc.get("body", {}).get("content", [])
        end_index = 1
        for el in content:
            end_index = el.get("endIndex", end_index)
        
        # Insert text at end
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
        
        logger.info("Successfully appended text to Google Doc: %s", doc_id)
        return True
        
    except Exception as e:
        logger.error("Failed to append to Google Doc: %s", e)
        return False


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="append_text",
            description="Append text to a Google Doc",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Google Doc ID to append to",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to append",
                    },
                },
                "required": ["document_id", "text"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    if name == "append_text":
        doc_id = arguments.get("document_id")
        text = arguments.get("text")
        
        if not doc_id or not text:
            return [TextContent(type="text", text="Error: document_id and text are required")]
        
        success = _append_to_doc(doc_id, text)
        if success:
            return [TextContent(type="text", text=f"Successfully appended text to Google Doc: {doc_id}")]
        else:
            return [TextContent(type="text", text="Failed to append text to Google Doc")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    # Import os here for environment variables
    import os
    
    # Check if environment variables are set
    if not os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON") and not os.environ.get("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH"):
        logger.error("Neither GOOGLE_DRIVE_CREDENTIALS_JSON nor MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH is set")
        sys.exit(1)
    
    # Run server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-docs-simple",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
