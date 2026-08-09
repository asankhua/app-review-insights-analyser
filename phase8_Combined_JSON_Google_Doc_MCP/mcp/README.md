# Google Docs MCP Server

Complete Model Context Protocol (MCP) server implementation for Google Documents integration.

## 📁 Files

- `google_docs_mcp_server.py` - Main MCP server implementation
- `requirements.txt` - Required Python dependencies
- `test_mcp_server.py` - Test script for the MCP server
- `setup.py` - Setup and installation script
- `README.md` - This documentation

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd mcp
python3 setup.py
```

### 2. Environment Variables
Set these environment variables in your `.env` file:

```bash
# Required
GOOGLE_SERVICE_ACCOUNT_BASE64=<base64-encoded-service-account-json>
GOOGLE_DOC_ID=18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0

# MCP Configuration
MCP_GOOGLE_DOCS_USE_MCP=1
MCP_GOOGLE_DOCS_MCP_COMMAND=python3
MCP_GOOGLE_DOCS_MCP_ARGS=mcp/google_docs_mcp_server.py
MCP_GOOGLE_DOCS_SUBJECT_EMAIL=your-email@gmail.com
```

### 3. Test the Server
```bash
python3 test_mcp_server.py
```

## 🔧 Features

### MCP Tools

#### `append_text`
Append text to a Google Document.

**Parameters:**
- `document_id` (string): Google Document ID
- `text` (string): Text to append

**Example:**
```python
result = await session.call_tool(
    name="append_text",
    arguments={
        "document_id": "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0",
        "text": "\n--- New Entry ---\nThis is my content."
    }
)
```

#### `get_document`
Get the content of a Google Document.

**Parameters:**
- `document_id` (string): Google Document ID

**Example:**
```python
result = await session.call_tool(
    name="get_document",
    arguments={
        "document_id": "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
    }
)
```

## 🔐 Authentication

The MCP server supports multiple authentication methods:

1. **Base64 Environment Variable** (Recommended for production)
   ```bash
   GOOGLE_SERVICE_ACCOUNT_BASE64=<base64-encoded-json>
   ```

2. **Service Account File**
   ```bash
   SERVICE_ACCOUNT_PATH=/path/to/service-account.json
   ```

3. **Default File**
   - `secrets/optimum-plexus-490703-p5-768ba7e7734c.json`

## 🧪 Testing

### Run Tests
```bash
python3 test_mcp_server.py
```

### Test Coverage
- ✅ MCP server initialization
- ✅ Google Docs API authentication
- ✅ `append_text` tool functionality
- ✅ `get_document` tool functionality
- ✅ Integration with existing Phase 8 client

## 🔍 Troubleshooting

### Common Issues

#### "Missing required dependencies"
```bash
pip install -r requirements.txt
```

#### "No Google credentials configured"
Make sure `GOOGLE_SERVICE_ACCOUNT_BASE64` is set in your environment.

#### "Permission denied" errors
Ensure your service account has Editor permissions on the Google Document.

#### "MCP server not found"
Check that `MCP_GOOGLE_DOCS_MCP_ARGS` points to the correct file path:
```bash
MCP_GOOGLE_DOCS_MCP_ARGS=mcp/google_docs_mcp_server.py
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Integration

The MCP server integrates seamlessly with the existing Phase 8 workflow:

1. **Phase 8** calls `_append_via_mcp()`
2. **MCP Client** starts the MCP server
3. **MCP Server** authenticates and calls Google Docs API
4. **Result** is returned back through the chain

### Fallback

If MCP fails, the system automatically falls back to the direct Google Docs API implementation.

## 📝 Development

### Adding New Tools

1. Add tool definition in `handle_list_tools()`
2. Implement handler in `handle_call_tool()`
3. Add corresponding method in the server class
4. Update tests

### Example New Tool:
```python
Tool(
    name="create_document",
    description="Create a new Google Document",
    inputSchema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Document title"}
        },
        "required": ["title"]
    }
)
```

## 🚀 Production Deployment

### Environment Setup
1. Set `GOOGLE_SERVICE_ACCOUNT_BASE64` in production environment
2. Ensure service account has proper permissions
3. Configure MCP environment variables

### Monitoring
- Check logs for MCP server activity
- Monitor Google Docs API quota usage
- Test fallback mechanism regularly

## 📄 License

This MCP server is part of the App Review Insights Analyzer project.
