"""
High-level integration test: pipeline → view report → email preview → send email, plus Phase 7 (fee) and Phase 8 (combined JSON / MCP).
Uses mock data for Phases 1–2; Phase 3 (Gemini) requires GEMINI_API_KEY in env.
Run: pytest tests/test_pipeline_integration.py -v
Or: python -m pytest tests/test_pipeline_integration.py -v
"""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _seed_sample_data():
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "seed_sample_data.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        check=True,
        timeout=15,
    )


@pytest.fixture(scope="module")
def ensure_sample_data():
    """Ensure sample data exists once per module."""
    _seed_sample_data()
    yield


@pytest.mark.integration
class TestPipelineViewReportEmail:
    """Integration: run pipeline (mock) → view report → email preview → send path. Phase 7 & 8 exercised."""

    def test_1_run_pipeline_mock(self, ensure_sample_data):
        """Run full pipeline with mock data (Phase 1–2 from sample; Phase 3 uses Gemini if key set)."""
        if not os.environ.get("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set; pipeline Phase 3 requires it")
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "run", "--mock"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ},
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_2_view_report(self):
        """View report: get_latest_report() returns content."""
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from phase5_Orchestration_Web_UI.pipeline import get_latest_report

        content = get_latest_report()
        if content is None:
            pytest.skip("No report (run pipeline with GEMINI_API_KEY first)")
        assert "INDMoney" in content or "Weekly" in content or "Themes" in content

    def test_3_email_preview(self):
        """Email preview returns subject and HTML (includes fee section when Phase 7 configured)."""
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from phase5_Orchestration_Web_UI.pipeline import get_email_preview

        preview = get_email_preview()
        if preview is None:
            pytest.skip("No email preview (run pipeline with GEMINI_API_KEY first)")
        assert "subject" in preview
        assert "html" in preview
        assert "INDMoney" in preview["subject"] or "Weekly" in preview["subject"]
        if os.environ.get("FEE_EXPLANATION_URL"):
            assert "Fee Explanation" in preview["html"] or "fee" in preview["html"].lower()

    def test_4_send_email_returns_dict(self):
        """Send email path: pipeline send_email() returns a result dict (actual send requires credentials)."""
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from phase5_Orchestration_Web_UI.pipeline import send_email

        result = send_email(recipient=None)
        assert isinstance(result, dict)
        assert "success" in result
        # May be False if no credentials; we only check the API works
        assert "error" in result or "message_id" in result or "recipient" in result


@pytest.mark.integration
class TestPhase7FeeExplanation:
    """Phase 7: Fee explanation (optional)."""

    def test_fee_skip_when_url_unset(self):
        """When FEE_EXPLANATION_URL is unset, get_fee_explanation returns None."""
        env = {k: v for k, v in os.environ.items() if k != "FEE_EXPLANATION_URL"}
        # Ensure unset in this process
        env.pop("FEE_EXPLANATION_URL", None)
        result = subprocess.run(
            [sys.executable, "-c", "from phase7_Fee_Explanation import get_fee_explanation; from datetime import date; r = get_fee_explanation(report_date=date.today()); assert r is None"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0

    def test_fee_result_shape_when_set(self):
        """When fee URL is set and fetch succeeds, result has fee_scenario, explanation_bullets, source_links, last_checked."""
        if not os.environ.get("FEE_EXPLANATION_URL"):
            pytest.skip("FEE_EXPLANATION_URL not set")
        sys.path.insert(0, str(PROJECT_ROOT))
        from phase7_Fee_Explanation import get_fee_explanation

        r = get_fee_explanation(report_date=date.today(), save_to_reports=False)
        if r is None:
            pytest.skip("Fee fetch failed (network or parse)")
        assert hasattr(r, "fee_scenario")
        assert hasattr(r, "explanation_bullets")
        assert len(r.explanation_bullets) <= 3
        assert hasattr(r, "source_links")
        assert hasattr(r, "last_checked")


@pytest.mark.integration
class TestPhase8CombinedJsonAndDoc:
    """Phase 8: Combined JSON and optional Google Doc / MCP."""

    def test_phase8_builds_combined_json(self):
        """Phase 8 run_phase8 produces combined payload and optional file; append to Doc skipped when no config."""
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from phase8_Combined_JSON_Google_Doc_MCP import run_phase8

        report_date = date.today()
        ok, payload, _ = run_phase8(report_date=report_date, fee_explanation=None, save_to_reports=True)
        assert ok is True
        assert payload is not None
        assert payload.date == report_date.isoformat()
        assert hasattr(payload, "weekly_pulse")
        assert hasattr(payload, "fee_scenario")
        # Optional file may be written
        combined_file = PROJECT_ROOT / "data" / "reports" / f"combined-{report_date.isoformat()}.json"
        assert combined_file.exists(), "combined-*.json should be written when save_to_reports=True"

    def test_phase8_human_readable(self):
        """Combined payload has to_human_readable() for Doc append."""
        sys.path.insert(0, str(PROJECT_ROOT))
        from phase8_Combined_JSON_Google_Doc_MCP.models.combined_report import CombinedReportPayload, WeeklyPulseSection

        p = CombinedReportPayload(
            date="2026-03-15",
            weekly_pulse=WeeklyPulseSection(themes=["T1"], quotes=["Q1"], action_ideas=["A1"]),
            fee_scenario="Mutual Fund Exit Load",
            explanation_bullets=["B1", "B2", "B3"],
            source_links=[],
            last_checked="2026-03-15",
        )
        text = p.to_human_readable()
        assert "Combined Report" in text
        assert "T1" in text
        assert "Mutual Fund Exit Load" in text

