#!/usr/bin/env python3
"""
Test script for Google Docs MCP Server
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing Google Docs MCP Server...")
    
    # Set up test environment
    os.environ["GOOGLE_SERVICE_ACCOUNT_BASE64"] = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "")
    
    if not os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64"):
        print("❌ GOOGLE_SERVICE_ACCOUNT_BASE64 not set")
        return False
    
    # Test document ID
    test_doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
    test_text = f"\n--- MCP Test - {asyncio.get_event_loop().time()} ---\nThis is a test from the MCP server."
    
    try:
        # Import and test the server
        from mcp.google_docs_mcp_server import GoogleDocsMCPServer
        
        # Create server instance
        server = GoogleDocsMCPServer()
        
        # Initialize docs service
        await server._initialize_docs_service()
        
        # Test append_text
        print(f"📝 Testing append_text to document {test_doc_id}")
        result = await server._handle_append_text({
            "document_id": test_doc_id,
            "text": test_text
        })
        
        if result.isError:
            print(f"❌ Append failed: {result.content[0].text}")
            return False
        else:
            print(f"✅ Append successful: {result.content[0].text}")
        
        # Test get_document
        print(f"📖 Testing get_document for {test_doc_id}")
        result = await server._handle_get_document({
            "document_id": test_doc_id
        })
        
        if result.isError:
            print(f"❌ Get document failed: {result.content[0].text}")
            return False
        else:
            content = result.content[0].text
            print(f"✅ Get document successful (length: {len(content)})")
            print(f"📄 Document preview: {content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_integration():
    """Test MCP integration with the existing client"""
    print("\n🔗 Testing MCP Integration...")
    
    try:
        from phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client import _append_via_mcp
        
        test_doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
        test_text = f"\n--- MCP Integration Test - {asyncio.get_event_loop().time()} ---\nTesting MCP client integration."
        
        print(f"📝 Testing MCP append to {test_doc_id}")
        success, message = await _append_via_mcp(test_doc_id, test_text)
        
        if success:
            print(f"✅ MCP integration successful: {message}")
            return True
        else:
            print(f"❌ MCP integration failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    print("🚀 Google Docs MCP Server Test Suite")
    print("=" * 50)
    
    # Test 1: Basic MCP server functionality
    mcp_test_passed = await test_mcp_server()
    
    # Test 2: Integration with existing client
    integration_test_passed = await test_mcp_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ MCP Server: {'PASS' if mcp_test_passed else 'FAIL'}")
    print(f"✅ Integration: {'PASS' if integration_test_passed else 'FAIL'}")
    
    if mcp_test_passed and integration_test_passed:
        print("\n🎉 All tests passed! MCP server is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
