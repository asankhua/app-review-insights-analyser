#!/usr/bin/env python3
"""
Google Docs MCP Server - Complete implementation for Model Context Protocol
Provides append_text tool for Google Documents using Google Docs API
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
        CallToolResult,
        ListToolsResult,
        TextContent,
        Tool,
    )
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing required dependencies: {e}", file=sys.stderr)
    print("Install with: pip install mcp google-api-python-client google-auth", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDocsMCPServer:
    """Google Docs MCP Server implementation"""
    
    def __init__(self):
        self.server = Server("google-docs-mcp-server")
        self.docs_service = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="append_text",
                        description="Append text to a Google Document",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {
                                    "type": "string",
                                    "description": "Google Document ID (from URL)"
                                },
                                "text": {
                                    "type": "string", 
                                    "description": "Text to append to the document"
                                }
                            },
                            "required": ["document_id", "text"]
                        }
                    ),
                    Tool(
                        name="get_document",
                        description="Get content of a Google Document",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "document_id": {
                                    "type": "string",
                                    "description": "Google Document ID (from URL)"
                                }
                            },
                            "required": ["document_id"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            if name == "append_text":
                return await self._handle_append_text(arguments)
            elif name == "get_document":
                return await self._handle_get_document(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _get_docs_service(self):
        """Get or create Google Docs API service"""
        if self.docs_service is None:
            await self._initialize_docs_service()
        return self.docs_service
    
    async def _initialize_docs_service(self):
        """Initialize Google Docs API service"""
        try:
            # Get credentials from environment
            credentials = self._get_credentials()
            if not credentials:
                raise ValueError("No Google credentials configured")
            
            # Build Docs API client
            self.docs_service = build('docs', 'v1', credentials=credentials)
            logger.info("Google Docs API service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Docs API: {e}")
            raise
    
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
    
    async def _handle_append_text(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle append_text tool call"""
        try:
            document_id = arguments["document_id"]
            text = arguments["text"]
            
            # Get Docs service
            docs_service = await self._get_docs_service()
            
            # Get document to find end index
            doc = docs_service.documents().get(documentId=document_id).execute()
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
            
            result = docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            logger.info(f"Successfully appended text to document {document_id}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=f"Successfully appended text to document {document_id}")]
            )
            
        except HttpError as e:
            error_msg = f"Google Docs API error: {e}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=error_msg)],
                isError=True
            )
        except Exception as e:
            error_msg = f"Error appending text: {e}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=error_msg)],
                isError=True
            )
    
    async def _handle_get_document(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_document tool call"""
        try:
            document_id = arguments["document_id"]
            
            # Get Docs service
            docs_service = await self._get_docs_service()
            
            # Get document
            doc = docs_service.documents().get(documentId=document_id).execute()
            
            # Extract text content
            content = doc.get('body', {}).get('content', [])
            text_parts = []
            
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    for elem in paragraph.get('elements', []):
                        if 'textRun' in elem:
                            text_parts.append(elem['textRun'].get('content', ''))
            
            full_text = ''.join(text_parts)
            
            logger.info(f"Successfully retrieved document {document_id}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=full_text)]
            )
            
        except HttpError as e:
            error_msg = f"Google Docs API error: {e}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=error_msg)],
                isError=True
            )
        except Exception as e:
            error_msg = f"Error getting document: {e}"
            logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=error_msg)],
                isError=True
            )
    
    async def run(self):
        """Run the MCP server"""
        # Setup stdio transport
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="google-docs-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )

async def main():
    """Main entry point"""
    server = GoogleDocsMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

