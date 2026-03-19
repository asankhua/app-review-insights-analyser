"""
Phase 8: Combined report payload (weekly pulse + fee explanation) for Google Doc / JSON.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class WeeklyPulseSection(BaseModel):
    """Weekly pulse themes, quotes, and action ideas (from Phase 3)."""
    themes: List[str] = Field(description="Top theme names/summaries", default_factory=list)
    quotes: List[str] = Field(description="User quotes", default_factory=list)
    action_ideas: List[str] = Field(description="Action ideas", default_factory=list)


class CombinedReportPayload(BaseModel):
    """
    Combined JSON: date + weekly_pulse (Phase 3) + fee explanation (Phase 7).
    Written to combined-YYYY-MM-DD.json and/or appended to Google Doc.
    """
    date: str = Field(description="Report date (YYYY-MM-DD)")
    weekly_pulse: WeeklyPulseSection = Field(
        default_factory=WeeklyPulseSection,
        description="Themes, quotes, action ideas from Phase 3",
    )
    fee_scenario: str = Field(
        default="",
        description="Fee scenario title from Phase 7 (empty if skipped)",
    )
    explanation_bullets: List[str] = Field(
        default_factory=list,
        description="Fee explanation bullets from Phase 7 (empty if skipped)",
    )
    source_links: List[str] = Field(
        default_factory=list,
        description="Fee source links from Phase 7",
    )
    last_checked: str = Field(
        default="",
        description="Fee data last checked date (YYYY-MM-DD) from Phase 7",
    )

    def to_human_readable(self) -> str:
        """Human-readable text for appending to a Google Doc."""
        lines = [
            f"--- Combined Report {self.date} ---",
            "",
            "Weekly Pulse",
            "Themes:",
        ]
        for t in self.weekly_pulse.themes:
            lines.append(f"  • {t}")
        lines.append("Quotes:")
        for q in self.weekly_pulse.quotes:
            lines.append(f"  \"{q}\"")
        lines.append("Action ideas:")
        for a in self.weekly_pulse.action_ideas:
            lines.append(f"  • {a}")
        if self.fee_scenario or self.explanation_bullets:
            lines.extend(["", f"Fee Explanation: {self.fee_scenario or 'N/A'}"])
            for b in self.explanation_bullets:
                lines.append(f"  • {b}")
            if self.source_links:
                lines.append("Sources: " + ", ".join(self.source_links))
        lines.append("")
        return "\n".join(lines)
