"""
Phase 7: Fee Explanation data models.
"""
import html
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class FeeExplanationResult(BaseModel):
    """Result of fee explanation fetch and format. Used by Phase 4 (email) and Phase 8 (combined JSON)."""

    fee_scenario: str = Field(description="Short scenario title, e.g. 'Mutual Fund Exit Load'")
    explanation_bullets: List[str] = Field(
        description="Exactly 3 factual bullets about exit load / fees",
        min_length=3,
        max_length=3,
    )
    source_links: List[str] = Field(description="URLs used as sources", default_factory=list)
    last_checked: str = Field(description="Date of fetch (YYYY-MM-DD)")
    exit_load_value: Optional[str] = Field(
        default=None,
        description="Exit load percentage or short phrase when available, e.g. '1%' or '1.00% if redeemed within 1 year'",
    )
    general_description: Optional[str] = Field(
        default=None,
        description="Short general note on exit load (what it is); from source when available.",
    )

    def to_email_section_plain(self) -> str:
        """Plain text block for email body."""
        lines = [f"Fee Explanation: {self.fee_scenario}"]
        if self.general_description:
            lines.append(self.general_description)
        if self.exit_load_value:
            lines.append(f"Exit load (from fund page): {self.exit_load_value}")
        lines.append("")
        for b in self.explanation_bullets:
            lines.append(f"• {b}")
        if self.source_links:
            lines.append("")
            lines.append("Source links:")
            for url in self.source_links:
                lines.append(f"  {url}")
        return "\n".join(lines)

    def to_email_section_html(self) -> str:
        """HTML block for email body."""
        extra = []
        if self.general_description:
            extra.append(f"<p>{html.escape(self.general_description)}</p>")
        if self.exit_load_value:
            extra.append(f'<p><strong>Exit load (from fund page):</strong> {html.escape(self.exit_load_value)}</p>')
        exit_load_line = "\n".join(extra)
        bullets_html = "".join(
            f'<div class="theme-item">• {html.escape(b)}</div>' for b in self.explanation_bullets
        )
        links_html = ""
        if self.source_links:
            links_html = "<p><strong>Source links:</strong><br/>" + "".join(
                f'<a href="{url}">{url}</a><br/>' for url in self.source_links
            ) + "</p>"
        return f"""
        <div class="section">
            <h2>Fee Explanation: {self.fee_scenario}</h2>
            {exit_load_line}
            {bullets_html}
            {links_html}
            <p><small>Last checked: {self.last_checked}</small></p>
        </div>
        """
