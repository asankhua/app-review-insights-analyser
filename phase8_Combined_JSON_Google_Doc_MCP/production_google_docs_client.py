#!/usr/bin/env python3
"""
Production-ready Google Docs MCP client that handles both local and production environments.
Supports both file-based and base64-encoded service account credentials.
"""
import os
import json
import base64
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def get_google_credentials() -> Optional[str]:
    """
    Get Google service account credentials for production deployment.
    Supports JSON string, base64-encoded, and file-based credentials.
    
    Returns:
        JSON string of service account credentials or None if not configured
    """
    # Try JSON string (for Render env - GOOGLE_DRIVE_CREDENTIALS_JSON)
    json_creds = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON", "").strip()
    if json_creds:
        try:
            json.loads(json_creds)
            logger.info("Using GOOGLE_DRIVE_CREDENTIALS_JSON")
            return json_creds
        except Exception as e:
            logger.debug("Invalid GOOGLE_DRIVE_CREDENTIALS_JSON: %s", e)

    # Try base64 encoded credentials (for production)
    base64_creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_BASE64", "").strip()
    if base64_creds:
        try:
            decoded_creds = base64.b64decode(base64_creds).decode('utf-8')
            # Validate it's valid JSON
            json.loads(decoded_creds)
            logger.info("Using base64-encoded service account credentials")
            return decoded_creds
        except Exception as e:
            logger.error(f"Failed to decode base64 credentials: {e}")
    
    # Try file-based credentials (for local development)
    for path_env in ("MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH", "GOOGLE_DRIVE_CREDENTIALS_PATH"):
        service_account_path = os.environ.get(path_env, "").strip()
        if service_account_path:
            resolved = os.path.expanduser(service_account_path)
            if os.path.exists(resolved):
                try:
                    with open(resolved, 'r', encoding='utf-8') as f:
                        file_creds = f.read()
                    logger.info(f"Using file-based service account credentials: {resolved}")
                    return file_creds
                except Exception as e:
                    logger.error(f"Failed to read service account file: {e}")
    
    # Try alternative file path
    alt_path = "secrets/optimum-plexus-490703-p5-768ba7e7734c.json"
    if os.path.exists(alt_path):
        try:
            with open(alt_path, 'r', encoding='utf-8') as f:
                file_creds = f.read()
            logger.info(f"Using alternative service account file: {alt_path}")
            return file_creds
        except Exception as e:
            logger.error(f"Failed to read alternative service account file: {e}")
    
    logger.warning("No Google service account credentials configured")
    return None

def append_to_google_doc_production(doc_id: str, text: str) -> Tuple[bool, str]:
    """
    Append text to Google Doc in production environment.
    Uses base64 or file-based service account credentials.
    
    Args:
        doc_id: Google Document ID
        text: Text to append
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Get credentials
        credentials_json = get_google_credentials()
        if not credentials_json:
            return False, "No Google service account credentials configured"
        
        # Import Google libraries
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as e:
            return False, f"Google libraries not available: {e}"
        
        # Create credentials from JSON
        try:
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/documents']
            )
        except Exception as e:
            return False, f"Failed to create credentials: {e}"
        
        # Build Docs API client
        try:
            service = build('docs', 'v1', credentials=credentials)
        except Exception as e:
            return False, f"Failed to build Docs API client: {e}"
        
        # Get document and find end index
        try:
            doc = service.documents().get(documentId=doc_id).execute()
            content = doc.get('body', {}).get('content', [])
            end_index = 1
            for element in content:
                end_index = element.get('endIndex', end_index)
        except Exception as e:
            return False, f"Failed to get document: {e}"
        
        # Append text
        try:
            requests = [
                {
                    'insertText': {
                        'location': {'index': end_index - 1},
                        'text': '\n' + text
                    }
                }
            ]
            service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            logger.info(f"Successfully appended to Google Doc: {doc_id}")
            return True, f"Appended to Google Doc: {doc_id}"
        except Exception as e:
            return False, f"Failed to append text: {e}"
            
    except Exception as e:
        logger.error(f"Unexpected error in append_to_google_doc_production: {e}")
        return False, f"Unexpected error: {e}"

if __name__ == "__main__":
    # Test the production append functionality
    import sys
    from datetime import datetime
    
    doc_id = os.environ.get("GOOGLE_DOC_ID", "18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0")
    test_text = f"Production Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    print(f"Testing production Google Doc append to: {doc_id}")
    print(f"Test text: {test_text}")
    
    success, message = append_to_google_doc_production(doc_id, test_text)
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    if success:
        print("✅ Production Google Doc append working!")
    else:
        print("❌ Production Google Doc append failed!")
        sys.exit(1)

