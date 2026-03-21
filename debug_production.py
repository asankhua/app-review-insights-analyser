#!/usr/bin/env python3
"""
Debug script to check production environment for Google Docs integration.
Run this locally to simulate production environment and debug issues.
"""
import os
import json
import base64
from datetime import datetime

def test_production_credentials():
    """Test if production credentials are properly configured."""
    print("=== Testing Production Credentials ===")
    
    # Check if base64 environment variable is set
    base64_creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "").strip()
    print(f"GOOGLE_SERVICE_ACCOUNT_BASE64 set: {bool(base64_creds)}")
    print(f"Base64 length: {len(base64_creds)}")
    
    if base64_creds:
        try:
            decoded_creds = base64.b64decode(base64_creds).decode('utf-8')
            print("✅ Base64 decoding successful")
            
            # Validate JSON
            try:
                credentials_info = json.loads(decoded_creds)
                print("✅ JSON parsing successful")
                print(f"Project ID: {credentials_info.get('project_id', 'Not found')}")
                print(f"Client Email: {credentials_info.get('client_email', 'Not found')}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Base64 decoding failed: {e}")
            return False
    else:
        print("❌ GOOGLE_SERVICE_ACCOUNT_BASE64 not set")
        return False

def test_google_doc_access():
    """Test Google Doc access with production credentials."""
    print("\n=== Testing Google Doc Access ===")
    
    try:
        from production_google_docs_client import append_to_google_doc_production
        
        doc_id = os.environ.get("GOOGLE_DOC_ID", "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0")
        test_text = f"Production Debug Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"Doc ID: {doc_id}")
        print(f"Test text: {test_text}")
        
        success, message = append_to_google_doc_production(doc_id, test_text)
        print(f"Success: {success}")
        print(f"Message: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Google Doc access test failed: {e}")
        return False

def test_phase8_production():
    """Test Phase 8 with production client."""
    print("\n=== Testing Phase 8 Production ===")
    
    try:
        from phase8_Combined_JSON_Google_Doc_MCP import run_phase8
        from datetime import date
        
        report_date = date.today()
        print(f"Report date: {report_date}")
        
        success, payload, mcp_msg = run_phase8(
            report_date=report_date,
            fee_explanation=None,
            save_to_reports=True
        )
        
        print(f"Success: {success}")
        print(f"MCP message: {mcp_msg}")
        
        if payload:
            print(f"Payload date: {payload.date}")
            print(f"Themes count: {len(payload.weekly_pulse.themes)}")
            print(f"Quotes count: {len(payload.weekly_pulse.quotes)}")
        
        return success
        
    except Exception as e:
        print(f"❌ Phase 8 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_production_env():
    """Simulate production environment by setting base64 variable."""
    print("\n=== Simulating Production Environment ===")
    
    # Read the actual service account file and encode it
    try:
        with open("secrets/optimum-plexus-490703-p5-768ba7e7734c.json", "r") as f:
            service_account_json = f.read()
        
        # Encode to base64
        base64_encoded = base64.b64encode(service_account_json.encode()).decode()
        
        # Set environment variable
        os.environ["GOOGLE_SERVICE_ACCOUNT_BASE64"] = base64_encoded
        
        print("✅ Production environment simulated")
        print(f"Base64 length: {len(base64_encoded)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to simulate production environment: {e}")
        return False

def main():
    """Run all debug tests."""
    print("🔍 Production Environment Debug Script")
    print("=" * 50)
    
    # Test 1: Check if we can simulate production environment
    if simulate_production_env():
        
        # Test 2: Test production credentials
        creds_ok = test_production_credentials()
        
        if creds_ok:
            # Test 3: Test Google Doc access
            doc_access_ok = test_google_doc_access()
            
            if doc_access_ok:
                # Test 4: Test Phase 8
                phase8_ok = test_phase8_production()
                
                if phase8_ok:
                    print("\n🎉 All tests passed! Production setup is working.")
                else:
                    print("\n❌ Phase 8 failed. Check Phase 8 implementation.")
            else:
                print("\n❌ Google Doc access failed. Check permissions or credentials.")
        else:
            print("\n❌ Credentials failed. Check base64 encoding.")
    else:
        print("\n❌ Could not simulate production environment.")
    
    print("\n🔍 Debug complete.")

if __name__ == "__main__":
    main()
