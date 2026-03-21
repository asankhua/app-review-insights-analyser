#!/usr/bin/env python3
"""
Setup script for Google Docs MCP Server
Installs dependencies and sets up the environment
"""
import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing MCP server dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
    # Check for required environment variables
    required_vars = [
        "GOOGLE_SERVICE_ACCOUNT_BASE64",
        "GOOGLE_DOC_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before running the MCP server.")
        return False
    
    print("✅ Environment variables are set")
    return True

def test_mcp_server():
    """Test the MCP server"""
    print("🧪 Testing MCP server...")
    
    test_script = Path(__file__).parent / "test_mcp_server.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(test_script)
        ], check=True, capture_output=True, text=True)
        
        print("✅ MCP server test passed")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ MCP server test failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Google Docs MCP Server Setup")
    print("=" * 40)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return 1
    
    # Step 2: Setup environment
    if not setup_environment():
        print("❌ Setup failed at environment setup")
        return 1
    
    # Step 3: Test MCP server
    if not test_mcp_server():
        print("❌ Setup failed at MCP server test")
        return 1
    
    print("\n🎉 MCP server setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update your .env file to use the new MCP server:")
    print("   MCP_GOOGLE_DOCS_MCP_COMMAND=python3")
    print("   MCP_GOOGLE_DOCS_MCP_ARGS=mcp/google_docs_mcp_server.py")
    print("2. Make sure MCP_GOOGLE_DOCS_USE_MCP=1")
    print("3. Test the combined report functionality")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
