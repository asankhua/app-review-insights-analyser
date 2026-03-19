"""
Phase 8: Combined JSON (Phase 3 + Phase 7) and append to Google Doc.
When GOOGLE_DOC_ID and credentials are set, appends human-readable report to the Doc;
otherwise skips append and optionally still writes combined-YYYY-MM-DD.json.
"""
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

from .models.combined_report import CombinedReportPayload
from .combined_builder import build_combined_payload, load_weekly_pulse_for_date
from .mcp_docs_client import append_to_google_doc

logger = logging.getLogger(__name__)

_MCP_RESULT_PATH = Path("data/logs/mcp_last.json")


def _write_mcp_result(success: bool, message: str) -> None:
    """Write last MCP append result for status API / UI."""
    try:
        _MCP_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _MCP_RESULT_PATH.write_text(
            json.dumps({"success": success, "message": (message or "").strip()}, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.debug("Could not write MCP result: %s", e)


def run_phase8(
    report_date: date,
    fee_explanation=None,
    save_to_reports: bool = True,
    doc_id: Optional[str] = None,
) -> Tuple[bool, Optional[CombinedReportPayload], str]:
    """
    Build combined JSON from Phase 3 (weekly pulse) and Phase 7 (fee), optionally save to file,
    and append to Google Doc if GOOGLE_DOC_ID (or doc_id) and credentials are set.
    Returns (success, payload, mcp_message). mcp_message is for UI (success or failure text); empty if append skipped.
    """
    weekly_pulse = load_weekly_pulse_for_date(report_date)
    fee_scenario = ""
    explanation_bullets = []
    source_links = []
    last_checked = ""
    if fee_explanation is not None and hasattr(fee_explanation, "fee_scenario"):
        fee_scenario = getattr(fee_explanation, "fee_scenario", "") or ""
        explanation_bullets = list(getattr(fee_explanation, "explanation_bullets", []) or [])
        source_links = list(getattr(fee_explanation, "source_links", []) or [])
        last_checked = getattr(fee_explanation, "last_checked", "") or ""

    payload = build_combined_payload(
        report_date=report_date,
        weekly_pulse=weekly_pulse,
        fee_scenario=fee_scenario or None,
        explanation_bullets=explanation_bullets or None,
        source_links=source_links or None,
        last_checked=last_checked or None,
    )

    if save_to_reports:
        try:
            reports_dir = Path("data/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            path = reports_dir / f"combined-{report_date.isoformat()}.json"
            path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug("Could not write combined JSON: %s", e)

    appended, mcp_message = append_to_google_doc(payload, doc_id=doc_id)
    if mcp_message:
        _write_mcp_result(appended, mcp_message)
    return True, payload, mcp_message or ""
