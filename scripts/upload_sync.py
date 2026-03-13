#!/usr/bin/env python3
"""Upload report to Render and/or GitHub Gist after scheduler run.
- Render: requires RENDER_URL, REPORT_UPLOAD_SECRET (ephemeral on free tier)
- Gist: requires GH_GIST_TOKEN (PAT with gist scope). REPORT_GIST_ID optional (auto-created if not set).
  GITHUB_TOKEN cannot create Gists—use a PAT: Settings → Developer settings → Tokens → Generate (classic), enable 'gist'.
"""
import json
import os
import sys
from pathlib import Path


def upload_to_gist(content: str, report_date: str, last_run: str | None) -> bool:
    """Create or update a GitHub Gist with report and metadata. Auto-creates on first run if no REPORT_GIST_ID.
    Requires GH_GIST_TOKEN (PAT with gist scope)—GITHUB_TOKEN cannot create Gists."""
    token = os.environ.get("GH_GIST_TOKEN", os.environ.get("GITHUB_TOKEN", "")).strip()
    if not token:
        return False
    gist_id = os.environ.get("REPORT_GIST_ID", "").strip()
    meta = {"report_date": report_date, "last_run": last_run or ""}
    files_payload = {
        "pulse.md": {"content": content},
        "meta.json": {"content": json.dumps(meta, indent=2)},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        import urllib.request
        if gist_id:
            # Update existing Gist
            req = urllib.request.Request(
                f"https://api.github.com/gists/{gist_id}",
                data=json.dumps({"files": files_payload}).encode(),
                headers={**headers},
                method="PATCH",
            )
        else:
            # Create new Gist (first run)
            payload = {
                "description": "Weekly Pulse report (App Review Insights)",
                "public": True,
                "files": files_payload,
            }
            req = urllib.request.Request(
                "https://api.github.com/gists",
                data=json.dumps(payload).encode(),
                headers={**headers},
                method="POST",
            )
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            status = getattr(r, "status", 200)
            data = json.loads(body) if body else {}
        if 200 <= status <= 299:
            created_id = data.get("id")
            if created_id and not gist_id:
                print("")
                print("=" * 60)
                print("Gist created! Add this to your secrets:")
                print("")
                print(f"  REPORT_GIST_ID = {created_id}")
                print("")
                print("Add to: GitHub Secrets + Render environment variables")
                print("Then View Report will show the synced report.")
                print("=" * 60)
            else:
                print("Report uploaded to Gist")
            return True
        return False
    except Exception as e:
        print("Gist upload failed:", e, file=sys.stderr)
        return False


def upload_to_render(url: str, secret: str, content: str, report_date: str, last_run: str | None) -> bool:
    """Upload to Render backend. Returns True on success."""
    if not url or not secret:
        return False
    try:
        import urllib.request
        req = urllib.request.Request(
            url.rstrip("/") + "/api/upload/sync",
            data=json.dumps({
                "report_content": content,
                "report_date": report_date,
                "last_run": last_run,
            }).encode(),
            headers={"Content-Type": "application/json", "X-Upload-Secret": secret},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=30)
        print("Report uploaded to Render")
        return True
    except Exception as e:
        print("Render upload failed:", e, file=sys.stderr)
        return False


def main():
    reports = sorted(Path("data/reports").glob("pulse-*.md"))
    if not reports:
        sys.exit(0)
    p = reports[-1]
    date = p.stem.replace("pulse-", "")
    content = p.read_text(encoding="utf-8")
    run = ""
    try:
        run = (Path("data/logs") / "last_run.txt").read_text(encoding="utf-8").strip()
    except Exception:
        pass

    gist_ok = upload_to_gist(content, date, run or None)
    render_ok = upload_to_render(
        os.environ.get("RENDER_URL", ""),
        os.environ.get("REPORT_UPLOAD_SECRET", ""),
        content, date, run or None,
    )

    if not gist_ok and not render_ok:
        print("Upload failed. For Gist: add GH_GIST_TOKEN (PAT with gist scope) to GitHub Secrets.", file=sys.stderr)
        print("Create at: GitHub Settings → Developer settings → Personal access tokens → gist", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
