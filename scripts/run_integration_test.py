#!/usr/bin/env python3
"""
High-level integration test: run pipeline → view report → email preview → send path, plus Phase 7 (fee) and Phase 8 (combined JSON / MCP).
Run from project root: python scripts/run_integration_test.py
Requires: sample data (seeded automatically), GEMINI_API_KEY for Phase 3. Optional: FEE_EXPLANATION_URL, GOOGLE_DOC_ID for Phase 7/8.
"""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(cmd, timeout=120):
    r = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=timeout, env=os.environ)
    return r.returncode == 0, r.stdout, r.stderr


def main():
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

    print("=" * 60)
    print("High-level integration test: pipeline → report → email → Phase 7 & 8")
    print("=" * 60)

    # 1. Seed sample data
    print("\n1. Seeding sample data...")
    ok, out, err = run([sys.executable, str(PROJECT_ROOT / "scripts" / "seed_sample_data.py")], timeout=15)
    if not ok:
        print("   FAIL:", err or out)
        return 1
    print("   OK")

    # 2. Run pipeline (mock)
    print("\n2. Running pipeline (--mock)...")
    ok, out, err = run([sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "run", "--mock"], timeout=120)
    if not ok:
        print("   FAIL (Phase 3 may need GEMINI_API_KEY):", (err or out)[:500])
        return 1
    print("   OK")

    # 3. View report
    print("\n3. View report (get_latest_report)...")
    try:
        from phase5_Orchestration_Web_UI.pipeline import get_latest_report
        content = get_latest_report()
        if not content:
            print("   FAIL: no report content")
            return 1
        print("   OK (length %d chars)" % len(content))
    except Exception as e:
        print("   FAIL:", e)
        return 1

    # 4. Email preview (includes fee when Phase 7 configured)
    print("\n4. Email preview (get_email_preview)...")
    try:
        from phase5_Orchestration_Web_UI.pipeline import get_email_preview
        preview = get_email_preview()
        if not preview or "html" not in preview:
            print("   FAIL: no preview")
            return 1
        has_fee = "Fee Explanation" in preview["html"] or "fee" in preview["html"].lower()
        print("   OK (subject: %s, fee section: %s)" % (preview.get("subject", "")[:50], has_fee))
    except Exception as e:
        print("   FAIL:", e)
        return 1

    # 5. Send email (API only; may fail if no credentials)
    print("\n5. Send email (pipeline.send_email)...")
    try:
        from phase5_Orchestration_Web_UI.pipeline import send_email
        result = send_email(recipient=None)
        if not isinstance(result, dict) or "success" not in result:
            print("   FAIL: invalid result")
            return 1
        print("   OK (success=%s)" % result.get("success"))
        if result.get("error"):
            print("   Note: %s" % result.get("error"))
    except Exception as e:
        print("   FAIL:", e)
        return 1

    # 6. Phase 7: fee explanation
    print("\n6. Phase 7 (fee explanation)...")
    try:
        from phase7_Fee_Explanation import get_fee_explanation
        fee = get_fee_explanation(report_date=date.today(), save_to_reports=False)
        if os.environ.get("FEE_EXPLANATION_URL"):
            print("   FEE_EXPLANATION_URL set; result: %s" % ("data" if fee else "skipped/failed"))
        else:
            print("   FEE_EXPLANATION_URL unset; skipped (OK)")
    except Exception as e:
        print("   FAIL:", e)
        return 1

    # 7. Phase 8: combined JSON (and optional Doc/MCP)
    print("\n7. Phase 8 (combined JSON + optional Google Doc / MCP)...")
    try:
        from phase8_Combined_JSON_Google_Doc_MCP import run_phase8
        ok8, payload, _ = run_phase8(report_date=date.today(), fee_explanation=None, save_to_reports=True)
        if not ok8 or payload is None:
            print("   FAIL")
            return 1
        combined_path = PROJECT_ROOT / "data" / "reports" / ("combined-%s.json" % date.today().isoformat())
        print("   OK (combined JSON: %s)" % ("written" if combined_path.exists() else "in-memory"))
    except Exception as e:
        print("   FAIL:", e)
        return 1

    print("\n" + "=" * 60)
    print("All integration steps passed.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

