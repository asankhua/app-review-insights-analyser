#!/usr/bin/env python3
"""
Simplified Google Docs MCP Server - Compatible with Python 3.9
Provides append_text functionality without requiring the MCP package
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing required dependencies: {e}", file=sys.stderr)
    print("Install with: pip install google-api-python-client google-auth", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleGoogleDocsMCPServer:
    """Simplified Google Docs MCP Server compatible with Python 3.9"""
    
    def __init__(self):
        self.docs_service = None
    
    async def initialize(self):
        """Initialize the Google Docs API service"""
        try:
            credentials = self._get_credentials()
            if not credentials:
                raise ValueError("No Google credentials configured")
            
            self.docs_service = build('docs', 'v1', credentials=credentials)
            logger.info("Google Docs API service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Docs API: {e}")
            return False
    
    def _get_credentials(self):
        """Get Google service account credentials"""
        # Try base64 encoded credentials first
        base64_creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "").strip()
        if base64_creds:
            try:
                import base64
                decoded_creds = base64.b64decode(base64_creds).decode('utf-8')
                credentials_info = json.loads(decoded_creds)
                return service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/documents']
                )
            except Exception as e:
                logger.error(f"Failed to use base64 credentials: {e}")
        
        # Try file-based credentials
        service_account_path = os.environ.get("SERVICE_ACCOUNT_PATH", "").strip()
        if not service_account_path:
            service_account_path = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH", "").strip()
        if not service_account_path:
            service_account_path = os.environ.get("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH", "").strip()
        
        if service_account_path and os.path.exists(service_account_path):
            try:
                return service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/documents']
                )
            except Exception as e:
                logger.error(f"Failed to use service account file: {e}")
        
        # Try default file
        default_path = "secrets/optimum-plexus-490703-p5-768ba7e7734c.json"
        if os.path.exists(default_path):
            try:
                return service_account.Credentials.from_service_account_file(
                    default_path,
                    scopes=['https://www.googleapis.com/auth/documents']
                )
            except Exception as e:
                logger.error(f"Failed to use default service account file: {e}")
        
        return None
    
    async def append_text(self, document_id: str, text: str) -> tuple[bool, str]:
        """Append text to a Google Document"""
        try:
            if not self.docs_service:
                await self.initialize()
            
            # Get document to find end index
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body', {}).get('content', [])
            end_index = 1
            for element in content:
                end_index = element.get('endIndex', end_index)
            
            # Append text
            requests = [
                {
                    'insertText': {
                        'location': {'index': end_index - 1},
                        'text': text
                    }
                }
            ]
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            logger.info(f"Successfully appended text to document {document_id}")
            return True, "Google Doc: appended successfully."
            
        except HttpError as e:
            error_msg = f"Google Docs API error: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error appending text: {e}"
            logger.error(error_msg)
            return False, error_msg

async def main():
    """Main entry point - MCP protocol simulation"""
    # Read stdin for MCP protocol messages
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                message = json.loads(line.strip())
                
                # Handle initialize
                if message.get("method") == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "google-docs-mcp-server",
                                "version": "1.0.0"
                            }
                        }
                    }
                    print(json.dumps(response), flush=True)
                
                # Handle tools/list
                elif message.get("method") == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": "append_text",
                                    "description": "Append text to a Google Document",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "document_id": {
                                                "type": "string",
                                                "description": "Google Document ID"
                                            },
                                            "text": {
                                                "type": "string",
                                                "description": "Text to append"
                                            }
                                        },
                                        "required": ["document_id", "text"]
                                    }
                                }
                            ]
                        }
                    }
                    print(json.dumps(response), flush=True)
                
                # Handle tools/call
                elif message.get("method") == "tools/call":
                    params = message.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if tool_name == "append_text":
                        server = SimpleGoogleDocsMCPServer()
                        success, result = await server.append_text(
                            arguments.get("document_id"),
                            arguments.get("text", "")
                        )
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": result
                                    }
                                ],
                                "isError": not success
                            }
                        }
                        print(json.dumps(response), flush=True)
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "error": {
                                "code": -32601,
                                "message": f"Unknown tool: {tool_name}"
                            }
                        }
                        print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                continue
                
    except KeyboardInterrupt:
        logger.info("MCP server stopped")
    except Exception as e:
        logger.error(f"MCP server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

