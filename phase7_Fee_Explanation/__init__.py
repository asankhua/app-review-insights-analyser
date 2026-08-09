"""
Phase 7: Fee Explanation.
Fetches exit load and fee details from FEE_EXPLANATION_URL and produces
fee_scenario, 3 explanation_bullets, source_links, last_checked for email and Phase 8.
"""
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from .models.fee import FeeExplanationResult
from .fee_fetcher import fetch_fee_page, extract_fee_snippets
from .fee_formatter import format_fee_result

logger = logging.getLogger(__name__)


def _fallback_fee_result(url: str, report_date: date, exit_load_override: Optional[str] = None) -> FeeExplanationResult:
    """
    Return a structured fee section when fetch/parse fails.
    If exit_load_override is set (e.g. from EXIT_LOAD_VALUE env), use it so email/doc still show a value and the link.
    """
    import os
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv()
        for _dir in [Path.cwd(), Path(__file__).resolve().parent.parent]:
            if (_dir / ".env").exists():
                load_dotenv(_dir / ".env")
                break
    except Exception:
        pass
    value = (exit_load_override or os.environ.get("EXIT_LOAD_VALUE", "") or "").strip().strip('"').strip("'") or None
    if value:
        logger.info("Using EXIT_LOAD_VALUE from env for fee section (fetch failed or blocked).")
    if value:
        return FeeExplanationResult(
            fee_scenario="Mutual Fund Exit Load",
            general_description=(
                "Exit load is a charge applied when you redeem (sell) units of a mutual fund "
                "within a specified period; it is disclosed in the scheme document and on the fund page."
            ),
            explanation_bullets=[
                f"Exit load (from fund page): {value}.",
                "Redemption before the exit-load period may attract the stated percentage; check the fund page for exact tiers.",
                "For complete exit load structure, refer to the official fund page linked below.",
            ],
            source_links=[url],
            last_checked=report_date.isoformat(),
            exit_load_value=value,
        )
    return FeeExplanationResult(
        fee_scenario="Mutual Fund Exit Load",
        general_description=(
            "Exit load is a charge applied when you redeem (sell) units of a mutual fund "
            "within a specified period; it is disclosed in the scheme document and on the fund page."
        ),
        explanation_bullets=[
            "Exit load could not be fetched from the fund page this time. See the link below for the exact percentage and conditions.",
            "Redemption before the exit-load period may attract a charge; check the fund page for current tiers.",
            "For complete exit load structure, refer to the official fund page linked below.",
        ],
        source_links=[url],
        last_checked=report_date.isoformat(),
        exit_load_value=None,
    )


def get_fee_explanation(
    report_date: Optional[date] = None,
    fee_url: Optional[str] = None,
    save_to_reports: bool = True,
) -> Optional[FeeExplanationResult]:
    """
    Run Phase 7: fetch fee page, parse, and format into FeeExplanationResult.
    If FEE_EXPLANATION_URL is unset or fetch/parse fails, returns None and logs a warning.
    """
    import os
    url = (fee_url or os.environ.get("FEE_EXPLANATION_URL", "") or "").strip().strip('"').strip("'")
    if not url:
        logger.info("FEE_EXPLANATION_URL not set; skipping fee explanation.")
        return None

    report_date = report_date or date.today()

    html = fetch_fee_page(url)
    if not html:
        logger.warning("Fee explanation fetch failed; returning fallback (set EXIT_LOAD_VALUE in env to show a value).")
        return _fallback_fee_result(url, report_date)

    try:
        raw = extract_fee_snippets(html, url)
        result = format_fee_result(raw, report_date)
    except Exception as e:
        logger.warning("Fee explanation parse/format failed: %s; returning fallback.", e)
        return _fallback_fee_result(url, report_date)

    if save_to_reports:
        try:
            reports_dir = Path("data/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            path = reports_dir / f"fee_explanation-{report_date.isoformat()}.json"
            path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug("Could not write fee_explanation JSON: %s", e)

    return result
