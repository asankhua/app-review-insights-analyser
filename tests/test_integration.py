"""
High-level integration tests for App Review Insights Analyzer.
Uses mock/sample data - no external API calls required.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestSampleDataSeeding:
    """Tests for sample data creation"""

    def test_seed_script_runs(self):
        """Seed script should run without errors"""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "seed_sample_data.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_reviews_file_created(self):
        """Reviews JSON file should exist and be valid"""
        reviews_dir = PROJECT_ROOT / "data" / "reviews"
        assert reviews_dir.exists()
        files = list(reviews_dir.glob("*.json"))
        assert len(files) >= 1
        with open(files[-1]) as f:
            data = json.load(f)
        assert "reviews" in data
        assert len(data["reviews"]) >= 5
        assert "packageId" in data
        assert data["packageId"] == "in.indwealth"

    def test_themes_file_created(self):
        """Themes JSON file should exist and be valid"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        assert reports_dir.exists()
        theme_files = list(reports_dir.glob("themes-*.json"))
        assert len(theme_files) >= 1
        with open(theme_files[-1]) as f:
            data = json.load(f)
        assert "themes" in data
        assert 3 <= len(data["themes"]) <= 5

    def test_grouped_reviews_file_created(self):
        """Grouped reviews JSON file should exist"""
        reports_dir = PROJECT_ROOT / "data" / "reports"
        grouped_files = list(reports_dir.glob("grouped_reviews-*.json"))
        assert len(grouped_files) >= 1
        with open(grouped_files[-1]) as f:
            data = json.load(f)
        assert "byTheme" in data
        assert "themes" in data


class TestPipelineMockRun:
    """Tests for full pipeline in mock mode"""

    @pytest.fixture(autouse=True)
    def setup_sample_data(self):
        """Ensure sample data exists before pipeline run"""
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "seed_sample_data.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            check=True,
        )

    def test_full_pipeline_mock_completes(self):
        """Full pipeline with --mock should complete successfully"""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "run", "--mock"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_weekly_note_generated(self):
        """Pipeline should produce weekly note files"""
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "run", "--mock"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            check=True,
        )
        reports_dir = PROJECT_ROOT / "data" / "reports"
        pulse_md = list(reports_dir.glob("pulse-*.md"))
        pulse_json = list(reports_dir.glob("weekly_pulse-*.json"))
        assert len(pulse_md) >= 1 or len(pulse_json) >= 1

    def test_email_draft_created(self):
        """Pipeline should produce email draft"""
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "run", "--mock"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            check=True,
        )
        drafts_dir = PROJECT_ROOT / "data" / "drafts"
        if drafts_dir.exists():
            drafts = list(drafts_dir.glob("*.eml")) + list(drafts_dir.glob("*.html"))
            assert len(drafts) >= 1
        # Alternatively check deliveries for draft status
        deliveries_dir = PROJECT_ROOT / "data" / "deliveries"
        if deliveries_dir.exists():
            deliveries = list(deliveries_dir.glob("delivery_*.json"))
            assert len(deliveries) >= 1


class TestCLICommands:
    """Tests for CLI commands"""

    def test_status_command(self):
        """Status command should run"""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "status"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    def test_list_command(self):
        """List command should run"""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py"), "--phase", "list"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
