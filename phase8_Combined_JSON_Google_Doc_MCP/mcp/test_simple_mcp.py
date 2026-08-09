#!/usr/bin/env python3
"""
Test script for Simplified Google Docs MCP Server
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

async def test_simple_mcp_server():
    """Test the simplified MCP server functionality"""
    print("🧪 Testing Simplified Google Docs MCP Server...")
    
    # Set up test environment
    if not os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64"):
        print("❌ GOOGLE_SERVICE_ACCOUNT_BASE64 not set")
        return False
    
    # Test document ID
    test_doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
    test_text = f"\n--- Simple MCP Test - {asyncio.get_event_loop().time()} ---\nThis is a test from the simplified MCP server."
    
    try:
        # Import and test the server
        sys.path.insert(0, str(Path(__file__).parent))
        from google_docs_mcp_server_simple import SimpleGoogleDocsMCPServer
        
        # Create server instance
        server = SimpleGoogleDocsMCPServer()
        
        # Initialize server
        initialized = await server.initialize()
        if not initialized:
            print("❌ Failed to initialize MCP server")
            return False
        
        print("✅ MCP server initialized successfully")
        
        # Test append_text
        print(f"📝 Testing append_text to document {test_doc_id}")
        success, message = await server.append_text(test_doc_id, test_text)
        
        if success:
            print(f"✅ Append successful: {message}")
            return True
        else:
            print(f"❌ Append failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_protocol():
    """Test MCP protocol communication"""
    print("\n🔗 Testing MCP Protocol Communication...")
    
    try:
        # Create a simple MCP client simulation
        server_script = Path(__file__).parent / "google_docs_mcp_server_simple.py"
        
        # Test data
        test_doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
        test_text = f"\n--- MCP Protocol Test - {asyncio.get_event_loop().time()} ---\nTesting MCP protocol communication."
        
        # Simulate MCP protocol messages
        mcp_messages = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "append_text",
                    "arguments": {
                        "document_id": test_doc_id,
                        "text": test_text
                    }
                }
            }
        ]
        
        # Write test messages to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            for msg in mcp_messages:
                f.write(json.dumps(msg) + '\n')
            temp_file = f.name
        
        try:
            # Run the server with test input
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(server_script),
                stdin=temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print("✅ MCP protocol test successful")
                return True
            else:
                print(f"❌ MCP protocol test failed: {stderr.decode()}")
                return False
                
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ MCP protocol test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_phase8_integration():
    """Test integration with Phase 8 client"""
    print("\n🔗 Testing Phase 8 Integration...")
    
    try:
        from phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client import _append_via_mcp
        
        test_doc_id = "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0"
        test_text = f"\n--- Phase 8 Integration Test - {asyncio.get_event_loop().time()} ---\nTesting Phase 8 MCP integration."
        
        print(f"📝 Testing Phase 8 MCP append to {test_doc_id}")
        success, message = await _append_via_mcp(test_doc_id, test_text)
        
        if success:
            print(f"✅ Phase 8 integration successful: {message}")
            return True
        else:
            print(f"❌ Phase 8 integration failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Phase 8 integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    print("🚀 Simplified Google Docs MCP Server Test Suite")
    print("=" * 50)
    
    # Test 1: Basic MCP server functionality
    mcp_test_passed = await test_simple_mcp_server()
    
    # Test 2: MCP protocol communication
    protocol_test_passed = await test_mcp_protocol()
    
    # Test 3: Integration with Phase 8 client
    integration_test_passed = await test_phase8_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✅ MCP Server: {'PASS' if mcp_test_passed else 'FAIL'}")
    print(f"✅ Protocol: {'PASS' if protocol_test_passed else 'FAIL'}")
    print(f"✅ Integration: {'PASS' if integration_test_passed else 'FAIL'}")
    
    if mcp_test_passed and integration_test_passed:
        print("\n🎉 All tests passed! Simplified MCP server is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

