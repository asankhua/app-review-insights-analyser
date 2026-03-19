"""
Phase 8: Build combined JSON from Phase 3 (weekly pulse) and Phase 7 (fee explanation).
"""
import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.combined_report import CombinedReportPayload, WeeklyPulseSection

logger = logging.getLogger(__name__)


def _extract_themes_quotes_actions_from_report(report: Dict[str, Any]) -> WeeklyPulseSection:
    """Extract string lists from Phase 3 WeeklyReport.report dict."""
    themes: List[str] = []
    quotes: List[str] = []
    action_ideas: List[str] = []

    for t in report.get("themes") or []:
        if isinstance(t, dict):
            themes.append(
                t.get("name") or t.get("description") or t.get("label") or str(t)
            )
        else:
            themes.append(str(t))

    for q in report.get("quotes") or []:
        if isinstance(q, dict):
            quotes.append(q.get("text") or q.get("quote") or str(q))
        else:
            quotes.append(str(q))

    for a in report.get("actions") or []:
        if isinstance(a, dict):
            action_ideas.append(
                a.get("description") or a.get("action") or str(a)
            )
        else:
            action_ideas.append(str(a))

    return WeeklyPulseSection(
        themes=themes,
        quotes=quotes,
        action_ideas=action_ideas,
    )


def _parse_pulse_markdown(content: str) -> WeeklyPulseSection:
    """Fallback: parse pulse-*.md to extract themes, quotes, action ideas as string lists."""
    themes: List[str] = []
    quotes: List[str] = []
    action_ideas: List[str] = []

    section = None
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "Top Themes" in line or "### Top Themes" in line:
            section = "themes"
            continue
        if "Real User Quotes" in line or "### Real User Quotes" in line:
            section = "quotes"
            continue
        if "Action Ideas" in line or "### Action Ideas" in line:
            section = "actions"
            continue
        if section == "themes" and (line.startswith("-") or line.startswith("*")):
            themes.append(line.lstrip("-*").strip())
        elif section == "quotes":
            if '"' in line:
                m = re.search(r'"([^"]+)"', line)
                if m:
                    quotes.append(m.group(1))
            elif line.startswith("-") or line.startswith("*"):
                quotes.append(line.lstrip("-*").strip())
        elif section == "actions" and (line.startswith("-") or line.startswith("*") or line.startswith("Action")):
            action_ideas.append(line.lstrip("-*").strip() if line[0] in "-*" else line)

    return WeeklyPulseSection(
        themes=themes[:5],
        quotes=quotes[:3],
        action_ideas=action_ideas[:3],
    )


def load_weekly_pulse_for_date(report_date: date, reports_dir: Optional[Path] = None) -> Optional[WeeklyPulseSection]:
    """
    Load Phase 3 output for the given date.
    Prefer weekly_pulse-YYYY-MM-DD.json; fallback to pulse-YYYY-MM-DD.md.
    """
    reports_dir = reports_dir or Path("data/reports")
    date_str = report_date.isoformat()

    # Prefer JSON
    json_path = reports_dir / f"weekly_pulse-{date_str}.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            report = data.get("report") or data
            return _extract_themes_quotes_actions_from_report(report)
        except Exception as e:
            logger.warning("Could not load weekly_pulse JSON %s: %s", json_path, e)

    # Fallback: latest weekly_pulse-*.json if date match not found
    for f in sorted(reports_dir.glob("weekly_pulse-*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            report = data.get("report") or data
            return _extract_themes_quotes_actions_from_report(report)
        except Exception as e:
            logger.debug("Skip %s: %s", f, e)
        break

    # Fallback: pulse markdown
    md_path = reports_dir / f"pulse-{date_str}.md"
    if md_path.exists():
        try:
            return _parse_pulse_markdown(md_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Could not parse pulse markdown %s: %s", md_path, e)
    for f in sorted(reports_dir.glob("pulse-*.md"), reverse=True):
        try:
            return _parse_pulse_markdown(f.read_text(encoding="utf-8"))
        except Exception as e:
            logger.debug("Skip %s: %s", f, e)
        break

    return None


def build_combined_payload(
    report_date: date,
    weekly_pulse: Optional[WeeklyPulseSection] = None,
    fee_scenario: Optional[str] = None,
    explanation_bullets: Optional[List[str]] = None,
    source_links: Optional[List[str]] = None,
    last_checked: Optional[str] = None,
) -> CombinedReportPayload:
    """
    Assemble CombinedReportPayload from Phase 3 and Phase 7 data.
    If weekly_pulse is None, tries to load from data/reports.
    Fee fields default to empty when Phase 7 was skipped.
    """
    if weekly_pulse is None:
        weekly_pulse = load_weekly_pulse_for_date(report_date) or WeeklyPulseSection()

    return CombinedReportPayload(
        date=report_date.isoformat(),
        weekly_pulse=weekly_pulse,
        fee_scenario=fee_scenario or "",
        explanation_bullets=explanation_bullets or [],
        source_links=source_links or [],
        last_checked=last_checked or "",
    )
