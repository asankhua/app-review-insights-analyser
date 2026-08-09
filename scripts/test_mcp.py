#!/usr/bin/env python3
"""
Test Phase 8 MCP: append combined report to Google Doc.
Requires .env: GOOGLE_DOC_ID and (for MCP) MCP_GOOGLE_DOCS_USE_MCP=1, MCP_GOOGLE_DOCS_MCP_COMMAND, etc.
Run: python scripts/test_mcp.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Load .env from project root so GOOGLE_DOC_ID and MCP vars are always picked up (override=True so vars are applied)
try:
    from dotenv import load_dotenv
    for env_path in [ROOT / ".env", Path.cwd() / ".env"]:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            break
    load_dotenv(override=True)
except Exception:
    pass
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def main():
    from datetime import date
    from phase8_Combined_JSON_Google_Doc_MCP.models.combined_report import CombinedReportPayload, WeeklyPulseSection
    from phase8_Combined_JSON_Google_Doc_MCP.mcp_docs_client import append_to_google_doc, _is_mcp_configured, _extract_doc_id

    doc_id = _extract_doc_id(os.environ.get("GOOGLE_DOC_ID", ""))
    mcp_ok = _is_mcp_configured()

    print("=== Phase 8 MCP test ===\n")
    print("GOOGLE_DOC_ID:", doc_id or "(not set)")
    print("MCP configured:", mcp_ok)
    if mcp_ok:
        print("  MCP_GOOGLE_DOCS_MCP_COMMAND:", os.environ.get("MCP_GOOGLE_DOCS_MCP_COMMAND", ""))
        print("  MCP_GOOGLE_DOCS_MCP_ARGS:", os.environ.get("MCP_GOOGLE_DOCS_MCP_ARGS", "(default)"))

    if not doc_id:
        print("\nTo run a real append test, set in .env:")
        print("  GOOGLE_DOC_ID=<your-google-doc-id-or-url>")
        if not mcp_ok:
            print("  MCP_GOOGLE_DOCS_USE_MCP=1")
            print("  MCP_GOOGLE_DOCS_MCP_COMMAND=uvx")
            print("  MCP_GOOGLE_DOCS_MCP_ARGS=google-docs-mcp-server")
            print("  MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH=/path/to/service-account.json")
            print("  MCP_GOOGLE_DOCS_SUBJECT_EMAIL=you@yourdomain.com")
        print("\nThen run again: python scripts/test_mcp.py")
        return 0 if mcp_ok else 1

    # Minimal payload for test
    payload = CombinedReportPayload(
        date=date.today().isoformat(),
        weekly_pulse=WeeklyPulseSection(
            themes=["[Test] Theme 1", "[Test] Theme 2"],
            quotes=["[Test] Quote 1"],
            action_ideas=["[Test] Action 1"],
        ),
        fee_scenario="Mutual Fund Exit Load",
        explanation_bullets=["[Test] Exit load 1%", "[Test] Bullet 2", "[Test] Bullet 3"],
        source_links=["https://example.com/fund"],
        last_checked=date.today().isoformat(),
    )

    print("\nAppending test block to Google Doc...")
    ok, msg = append_to_google_doc(payload, doc_id=doc_id)
    if msg:
        print("  ", msg)
    if ok:
        print("OK: Append succeeded. Check your Google Doc for the test block.")
        return 0
    print("FAIL: Append failed or skipped. Check MCP env vars and service account.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

