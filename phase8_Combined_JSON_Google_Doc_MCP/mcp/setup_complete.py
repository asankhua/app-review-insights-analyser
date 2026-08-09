#!/usr/bin/env python3
"""
Complete MCP Setup and Test Script
Sets up simplified MCP server and tests the complete integration
"""
import os
import subprocess
import sys
from pathlib import Path

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
    # Read environment variables from .env file
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Load required environment variables
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key in ["GOOGLE_SERVICE_ACCOUNT_BASE64", "GOOGLE_DOC_ID"]:
                    os.environ[key] = value
    
    # Set MCP configuration
    os.environ["MCP_GOOGLE_DOCS_MCP_COMMAND"] = "python3"
    os.environ["MCP_GOOGLE_DOCS_MCP_ARGS"] = "mcp/google_docs_mcp_server_simple.py"
    
    # Check required variables
    required_vars = ["GOOGLE_SERVICE_ACCOUNT_BASE64", "GOOGLE_DOC_ID"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables are set")
    return True

def test_mcp_server():
    """Test the simplified MCP server"""
    print("🧪 Testing simplified MCP server...")
    
    try:
        result = subprocess.run([
            sys.executable, "-c", """
import sys
sys.path.insert(0, '.')
from mcp.google_docs_mcp_server_simple import SimpleGoogleDocsMCPServer
import asyncio

async def test():
    server = SimpleGoogleDocsMCPServer()
    success = await server.initialize()
    if success:
        doc_id = '18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0'
        text = '\\n--- MCP Server Test ---\\nTesting simplified MCP server.'
        success, message = await server.append_text(doc_id, text)
        print(f'SUCCESS:{success}:{message}')
    else:
        print('FAILED:Initialization')

asyncio.run(test())
"""
        ], capture_output=True, text=True, env=os.environ.copy())
        
        if result.returncode == 0 and "SUCCESS:True:" in result.stdout:
            message = result.stdout.split("SUCCESS:True:")[1].strip()
            print(f"✅ MCP server test passed: {message}")
            return True
        else:
            print(f"❌ MCP server test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server test error: {e}")
        return False

def test_mcp_client():
    """Test the simplified MCP client"""
    print("🔗 Testing simplified MCP client...")
    
    try:
        result = subprocess.run([
            sys.executable, "mcp/simplified_mcp_client.py"
        ], capture_output=True, text=True, env=os.environ.copy())
        
        if result.returncode == 0 and "Success: True" in result.stdout:
            message = result.stdout.split("Success: True, Message:")[1].strip()
            print(f"✅ MCP client test passed: {message}")
            return True
        else:
            print(f"❌ MCP client test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP client test error: {e}")
        return False

def test_phase8_patch():
    """Test the Phase 8 MCP patch"""
    print("🔧 Testing Phase 8 MCP patch...")
    
    try:
        result = subprocess.run([
            sys.executable, "mcp/patch_phase8.py"
        ], capture_output=True, text=True, env=os.environ.copy())
        
        if result.returncode == 0 and "✅ MCP patch test successful!" in result.stdout:
            print("✅ Phase 8 patch test passed")
            return True
        else:
            print(f"❌ Phase 8 patch test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Phase 8 patch test error: {e}")
        return False

def test_complete_integration():
    """Test complete Phase 8 integration"""
    print("🎯 Testing complete Phase 8 integration...")
    
    try:
        result = subprocess.run([
            sys.executable, "-c", """
import sys
sys.path.insert(0, '.')

# Apply the patch first
from mcp.patch_phase8 import patch_phase8_mcp
patch_phase8_mcp()

# Test the patched function
from phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client import _append_via_mcp

doc_id = '18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0'
text = '\\n--- Complete Integration Test ---\\nTesting complete Phase 8 MCP integration.'

success, message = _append_via_mcp(doc_id, text)
print(f'SUCCESS:{success}:{message}')
"""
        ], capture_output=True, text=True, env=os.environ.copy())
        
        if result.returncode == 0 and "SUCCESS:True:" in result.stdout:
            message = result.stdout.split("SUCCESS:True:")[1].strip()
            print(f"✅ Complete integration test passed: {message}")
            return True
        else:
            print(f"❌ Complete integration test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Complete integration test error: {e}")
        return False

def main():
    """Main setup and test function"""
    print("🚀 Complete MCP Setup and Test Suite")
    print("=" * 50)
    
    # Step 1: Setup environment
    if not setup_environment():
        print("❌ Setup failed at environment setup")
        return 1
    
    # Step 2: Test MCP server
    if not test_mcp_server():
        print("❌ Setup failed at MCP server test")
        return 1
    
    # Step 3: Test MCP client
    if not test_mcp_client():
        print("❌ Setup failed at MCP client test")
        return 1
    
    # Step 4: Test Phase 8 patch
    if not test_phase8_patch():
        print("❌ Setup failed at Phase 8 patch test")
        return 1
    
    # Step 5: Test complete integration
    if not test_complete_integration():
        print("❌ Setup failed at complete integration test")
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 All MCP tests passed! Setup completed successfully!")
    print("\n📋 MCP Implementation Summary:")
    print("✅ Simplified MCP server (Python 3.9 compatible)")
    print("✅ MCP client without MCP package dependency")
    print("✅ Phase 8 integration patch")
    print("✅ Complete end-to-end functionality")
    print("\n🔧 MCP Configuration:")
    print("   MCP_GOOGLE_DOCS_USE_MCP=1")
    print("   MCP_GOOGLE_DOCS_MCP_COMMAND=python3")
    print("   MCP_GOOGLE_DOCS_MCP_ARGS=mcp/google_docs_mcp_server_simple.py")
    print("\n🚀 Your MCP implementation is now ready!")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
