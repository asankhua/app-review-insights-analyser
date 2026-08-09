"""
Upload DOCX to Google Drive and get shareable Google Docs link.
Requires GOOGLE_DRIVE_CREDENTIALS_JSON (service account JSON as string) or
GOOGLE_DRIVE_CREDENTIALS_PATH (path to JSON file).
Enable Drive API in Google Cloud Console.
"""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def upload_docx_to_google_docs(docx_bytes: bytes, filename: str) -> Optional[str]:
    """
    Upload DOCX to Google Drive, convert to Google Doc, share with anyone, return view link.
    Returns None if credentials not configured or upload fails.
    """
    creds_json = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON", "").strip()
    creds_path = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH", "").strip()
    if not creds_json and not creds_path:
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        import io

        if creds_json:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"],
            )
        else:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file"],
            )
        drive = build("drive", "v3", credentials=credentials)
        media = MediaIoBaseUpload(
            io.BytesIO(docx_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            resumable=False,
        )
        file_metadata = {
            "name": filename,
            "mimeType": "application/vnd.google-apps.document",
        }
        file = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()
        file_id = file.get("id")
        if not file_id:
            return None
        drive.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
        return f"https://docs.google.com/document/d/{file_id}/edit"
    except Exception as e:
        logger.warning("Google Drive upload failed: %s", e)
        return None

