#!/usr/bin/env python3
"""Upload report and status to Render backend after scheduler run. Requires RENDER_URL and REPORT_UPLOAD_SECRET."""
import json
import os
import sys
from pathlib import Path

def main():
    url = os.environ.get("RENDER_URL", "").rstrip("/")
    secret = os.environ.get("REPORT_UPLOAD_SECRET", "")
    if not url or not secret:
        return
    reports = sorted(Path("data/reports").glob("pulse-*.md"))
    if not reports:
        return
    p = reports[-1]
    date = p.stem.replace("pulse-", "")
    content = p.read_text(encoding="utf-8")
    run = ""
    try:
        run = (Path("data/logs") / "last_run.txt").read_text(encoding="utf-8").strip()
    except Exception:
        pass
    try:
        import urllib.request
        req = urllib.request.Request(
            url + "/api/upload/sync",
            data=json.dumps({"report_content": content, "report_date": date, "last_run": run or None}).encode(),
            headers={"Content-Type": "application/json", "X-Upload-Secret": secret},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=30)
        print("Report uploaded to", url)
    except Exception as e:
        print("Upload failed:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
