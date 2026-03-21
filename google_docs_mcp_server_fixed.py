#!/usr/bin/env python3
"""
Simple MCP Server for Google Docs - No SDK required
This provides a minimal MCP server that works without the MCP SDK
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_credentials():
    """Build Google API credentials from environment."""
    try:
        from google.oauth2 import service_account
    except ImportError:
        logger.error("google.oauth2 not available")
        return None

    # Try JSON content first (decode base64 if needed)
    credentials_json = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON")
    if credentials_json:
        try:
            # Check if it's base64 encoded
            import base64
            if credentials_json.startswith('ewog'):
                # It's base64 encoded
                decoded_json = base64.b64decode(credentials_json).decode('utf-8')
                info = json.loads(decoded_json)
            else:
                # It's already JSON
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


async def main():
    """Simple MCP server implementation."""
    import sys
    
    # Read command from stdin (MCP protocol)
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                logger.info("Received request: %s", request.get("method", "unknown"))
                
                if request.get("method") == "tools/call":
                    params = request.get("params", {})
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if name == "append_text":
                        doc_id = arguments.get("document_id")
                        text = arguments.get("text")
                        
                        if not doc_id or not text:
                            result = {
                                "result": {
                                    "content": [{"type": "text", "text": "Error: document_id and text are required"}],
                                    "isError": True
                                }
                            }
                        else:
                            success = _append_to_doc(doc_id, text)
                            if success:
                                result = {
                                    "result": {
                                        "content": [{"type": "text", "text": f"Successfully appended text to Google Doc: {doc_id}"}],
                                        "isError": False
                                    }
                                }
                            else:
                                result = {
                                    "result": {
                                        "content": [{"type": "text", "text": "Failed to append text to Google Doc"}],
                                        "isError": True
                                    }
                                }
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": result["result"]
                        }
                        print(json.dumps(response))
                        sys.stdout.flush()
                    
                    elif request.get("method") == "tools/list":
                        result = {
                            "result": {
                                "tools": [
                                    {
                                        "name": "append_text",
                                        "description": "Append text to a Google Doc",
                                        "inputSchema": {
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
                                    }
                                ]
                            }
                        }
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": result["result"]
                        }
                        print(json.dumps(response))
                        sys.stdout.flush()
                    
                    elif request.get("method") == "initialize":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {
                                    "tools": {}
                                },
                                "serverInfo": {
                                    "name": "google-docs-simple",
                                    "version": "0.1.0"
                                }
                            }
                        }
                        print(json.dumps(response))
                        sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON: %s", e)
            except Exception as e:
                logger.error("Error processing request: %s", e)
    
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error("Server error: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
