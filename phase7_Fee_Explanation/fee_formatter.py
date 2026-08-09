"""
Phase 7: Turn raw fee data into exactly 3 exit-load-specific bullets, source_links, and last_checked.
General and specific details are taken from the source link (e.g. INDMoney fund page).
"""
import re
from datetime import date
from typing import Any, Dict, List

from .models.fee import FeeExplanationResult

# General one-liner when we have no block from source
GENERAL_EXIT_LOAD_NOTE = (
    "Exit load is a charge applied when you redeem (sell) units of a mutual fund "
    "within a specified period; it is disclosed in the scheme document and on the fund page."
)

# Scraped UI/nav labels to exclude (e.g. "erview Get key fund statistics, minimum investment details...")
_FEE_UI_LABEL_PATTERNS = (
    "get key fund statistics",
    "minimum investment details",
    "erview",  # truncated "Overview"
)


def _is_ui_label_text(s: str) -> bool:
    """Return True if text looks like a scraped nav/menu label rather than actual fee content."""
    if not s or len(s) < 15:
        return False
    lower = s.lower()
    return any(p in lower for p in _FEE_UI_LABEL_PATTERNS)


def format_fee_result(raw: Dict[str, Any], report_date: date) -> FeeExplanationResult:
    """
    Build FeeExplanationResult from fetcher output.
    All 3 bullets are exit-load-specific; values are stamped from the source URL.
    """
    exit_load = (raw.get("exit_load") or "").strip()
    exit_load_value = (raw.get("exit_load_value") or "").strip()
    if not exit_load_value and exit_load:
        m = re.search(r"\d+(?:\.\d+)?\s*%", exit_load)
        if m:
            exit_load_value = m.group(0)
    exit_load_block = (raw.get("exit_load_block") or "").strip()
    exit_load_details = raw.get("exit_load_details") or []
    source_url = (raw.get("source_url") or "").strip()
    source_links = [source_url] if source_url else []

    # General description (from source block or fixed note)
    general_description = None
    if exit_load_block and len(exit_load_block) > 20:
        first_sentence = _first_sentence(exit_load_block)
        general_description = _clean_snippet(first_sentence[:200]) if first_sentence else exit_load_block[:200]
        if general_description and _is_ui_label_text(general_description):
            general_description = None
    if not general_description:
        general_description = GENERAL_EXIT_LOAD_NOTE

    # 3 bullets: all exit-load-specific, values from source
    bullets: List[str] = []

    # Bullet 1: exit load value / main detail from source
    _def_bullet1 = "Exit load and redemption charges apply as per the scheme document; see the fund page link below for current values."
    if exit_load_value:
        bullets.append(f"This fund's exit load (from fund page): {exit_load_value}.")
    elif exit_load and not _is_ui_label_text(exit_load):
        bullets.append(f"Exit load (from fund page): {_clean_snippet(exit_load)}")
    elif exit_load_details and not _is_ui_label_text(exit_load_details[0]):
        bullets.append(f"Exit load (from fund page): {_clean_snippet(exit_load_details[0])}.")
    else:
        bullets.append(_def_bullet1)

    # Bullet 2: specific condition/tier from source if available
    def _add_bullet(text: str) -> bool:
        t = _clean_snippet(text)
        if t and not _is_ui_label_text(t):
            bullets.append(t)
            return True
        return False
    if len(exit_load_details) > 1 and _add_bullet(exit_load_details[1]):
        pass
    elif len(exit_load_details) == 1 and exit_load_value and exit_load_details[0] != exit_load_value and _add_bullet(exit_load_details[0]):
        pass
    elif exit_load_block and len(exit_load_block) > len(exit_load_value or ""):
        second_part = _second_sentence(exit_load_block) or exit_load_block[100:300]
        if not _add_bullet(second_part[:200]):
            bullets.append("Redemption before the exit-load period may attract the stated percentage; check the fund page for exact conditions.")
    else:
        bullets.append(
            "Redemption before the exit-load period may attract the stated percentage; check the fund page for exact conditions."
        )

    # Bullet 3: source reference
    bullets.append(
        "For complete exit load structure and any updates, refer to the official fund page linked below (source of the values above)."
    )

    bullets = bullets[:3]
    while len(bullets) < 3:
        bullets.append("See source link for exit load details.")

    return FeeExplanationResult(
        fee_scenario="Mutual Fund Exit Load",
        explanation_bullets=bullets,
        source_links=source_links,
        last_checked=report_date.isoformat(),
        exit_load_value=exit_load_value or None,
        general_description=general_description,
    )


def _clean_snippet(s: str) -> str:
    """Normalize whitespace and truncate for a single bullet."""
    s = " ".join(s.split()).strip()
    return s[:250] if len(s) > 250 else s


def _first_sentence(block: str) -> str:
    """Return first sentence of a text block."""
    block = " ".join(block.split()).strip()
    for sep in (". ", ".\n", ";"):
        i = block.find(sep)
        if i != -1:
            return block[: i + 1].strip()
    return block[:200].strip()


def _second_sentence(block: str) -> str:
    """Return second sentence of a text block (or None)."""
    block = " ".join(block.split()).strip()
    for sep in (". ", ".\n"):
        i = block.find(sep)
        if i != -1:
            rest = block[i + len(sep) :].strip()
            j = rest.find(sep)
            if j != -1:
                return rest[: j + 1].strip()
            return rest[:200].strip() if rest else None
    return None

