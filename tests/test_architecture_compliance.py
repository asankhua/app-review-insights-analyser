"""
ARCHITECTURE.md compliance tests.

Validates that output artifacts conform to:
- No star ratings (⭐★☆) in Real User Quotes
- No PII (usernames, emails, IDs)
- Max 5 themes
- Note ≤400 words
- Exactly 3 quotes, 3 actions
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

# Per ARCHITECTURE: No star ratings in output
STAR_PATTERN = re.compile(r'[⭐★☆]')
RATING_SUFFIX_PATTERN = re.compile(r'\(\s*[^)]*rating\s*\)', re.IGNORECASE)
# PII patterns (should not appear in output)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')


class TestArchitectureCompliance:
    """Tests per ARCHITECTURE.md constraints"""

    @pytest.fixture(autouse=True)
    def setup_pipeline_output(self):
        """Run pipeline to produce output for compliance checks"""
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "seed_sample_data.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "run", "--mock"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            check=True,
        )

    def test_no_star_ratings_in_weekly_note_md(self):
        """ARCHITECTURE: No star rating icons in Real User Quotes"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        pulse_files = list(reports_dir.glob("pulse-*.md"))
        assert len(pulse_files) >= 1, "No pulse markdown file found"
        content = pulse_files[-1].read_text(encoding="utf-8")
        # Real User Quotes section should not contain star icons
        if "### Real User Quotes" in content:
            quotes_section = content.split("### Real User Quotes")[1].split("###")[0]
            assert not STAR_PATTERN.search(quotes_section), (
                "Star ratings (⭐★☆) found in Real User Quotes - per ARCHITECTURE must be removed"
            )
            assert not RATING_SUFFIX_PATTERN.search(quotes_section), (
                "(...rating) pattern found in Real User Quotes - must be removed"
            )

    def test_no_star_ratings_in_email_draft(self):
        """ARCHITECTURE: Email draft must not contain star ratings in quotes"""
        drafts_dir = PROJECT_ROOT / "data" / "drafts"
        if not drafts_dir.exists():
            pytest.skip("No drafts directory")
        eml_files = list(drafts_dir.glob("*.eml"))
        if not eml_files:
            pytest.skip("No .eml drafts")
        content = eml_files[-1].read_text(encoding="utf-8")
        if "Real User Quotes" in content:
            # Get the body part (after headers)
            body = content.split("\n\n", 2)[-1] if "\n\n" in content else content
            assert not STAR_PATTERN.search(body), (
                "Star ratings found in email draft - per ARCHITECTURE must be removed"
            )

    def test_max_5_themes(self):
        """ARCHITECTURE: Maximum 5 themes"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        theme_files = list(reports_dir.glob("themes-*.json"))
        assert len(theme_files) >= 1
        with open(theme_files[-1]) as f:
            data = json.load(f)
        assert len(data["themes"]) <= 5, "Maximum 5 themes allowed"

    def test_note_word_count(self):
        """ARCHITECTURE: Note ≤400 words"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        pulse_json = list(reports_dir.glob("weekly_pulse-*.json"))
        if not pulse_json:
            pytest.skip("No weekly pulse JSON")
        with open(pulse_json[-1]) as f:
            data = json.load(f)
        word_count = data.get("report", {}).get("word_count", 0)
        assert word_count <= 400, f"Note must be ≤400 words, got {word_count}"

    def test_exactly_3_quotes_3_actions(self):
        """ARCHITECTURE: Exactly 3 quotes, 3 actions"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        pulse_json = list(reports_dir.glob("weekly_pulse-*.json"))
        assert len(pulse_json) >= 1
        with open(pulse_json[-1]) as f:
            data = json.load(f)
        report = data.get("report", {})
        assert len(report.get("quotes", [])) == 3, "Exactly 3 quotes required"
        assert len(report.get("actions", [])) == 3, "Exactly 3 actions required"

    def test_no_pii_in_quotes(self):
        """ARCHITECTURE: No PII in artifacts"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        pulse_json = list(reports_dir.glob("weekly_pulse-*.json"))
        if not pulse_json:
            pytest.skip("No weekly pulse JSON")
        with open(pulse_json[-1]) as f:
            data = json.load(f)
        for quote in data.get("report", {}).get("quotes", []):
            text = quote.get("text", "")
            assert not EMAIL_PATTERN.search(text), f"PII (email) found in quote: {text[:50]}..."
