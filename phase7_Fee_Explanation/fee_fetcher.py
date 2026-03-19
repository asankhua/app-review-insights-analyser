"""
Phase 7: Fetch fee/exit load content from FEE_EXPLANATION_URL.
Uses stdlib urllib; parses HTML for exit load and expense ratio text.
"""
import logging
import re
from typing import Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# Common patterns for mutual fund fee info on INDMoney-style pages
EXIT_LOAD_PATTERNS = [
    re.compile(r"exit\s*load[:\s]+([^.<\n]+?)\.?(?:\s*<|\n|$)", re.IGNORECASE | re.DOTALL),
    re.compile(r"(?:no\s+)?exit\s*load[:\s]*([^.<\n]{5,150})", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?\s*%)\s*(?:if redeemed within|exit load|for redemption)", re.IGNORECASE),
    re.compile(r"exit\s*load[:\s]*(\d+(?:\.\d+)?\s*%)", re.IGNORECASE),
]
EXPENSE_RATIO_PATTERNS = [
    re.compile(r"expense\s*ratio[:\s]+([^.<\n]+?)\.?(?:\s*<|\n|$)", re.IGNORECASE | re.DOTALL),
    re.compile(r"total\s*expense\s*ratio[:\s]+([^.<\n]+)", re.IGNORECASE | re.DOTALL),
    re.compile(r"(\d+(?:\.\d+)?\s*%\s*(?:p\.a\.|per annum|expense|TER))", re.IGNORECASE),
    re.compile(r"TER[:\s]+([^.<\n]{5,80})", re.IGNORECASE),
]
# Fallback: any span that looks like a percentage or fee
FEE_SNIPPET_PATTERN = re.compile(
    r"(?:exit|load|expense|ratio|charge|fee|TER)[\s:]+[^.<>\n]{5,120}",
    re.IGNORECASE,
)
# Any percentage mention (e.g. "1.00%", "0.50%")
PERCENTAGE_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*%[^.<>\n]{0,80}", re.IGNORECASE)
# Exit load numeric value: "1%", "1.00%", or "1.00% if redeemed within 1 year"
EXIT_LOAD_NUMBER_PATTERNS = [
    re.compile(r"exit\s*load[:\s]*(\d+(?:\.\d+)?\s*%)(?:[^.<>\n]{0,60})?", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?\s*%)\s*(?:if redeemed|exit load|for redemption)", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?\s*%)", re.IGNORECASE),  # first % in snippet
]
# Block of text around "exit load" for general + specific (INDMoney/fund pages)
EXIT_LOAD_BLOCK_PATTERN = re.compile(
    r".{0,80}(?:exit\s*load|redemption\s*charge)[^.]{10,400}",
    re.IGNORECASE | re.DOTALL,
)
# Specific lines: "X% if redeemed within Y", "Nil after Y", etc.
EXIT_LOAD_LINE_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?\s*%\s*(?:if redeemed|for redemption|within)[^.<>\n]{0,80})", re.IGNORECASE),
    re.compile(r"((?:nil|0\s*%|zero)\s*(?:after|if)[^.<>\n]{0,60})", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?\s*%\s*[^.<>\n]{0,50})", re.IGNORECASE),
]
# JSON/script embedded data (INDMoney and similar often put fund data in script tags)
EXIT_LOAD_JSON_PATTERNS = [
    re.compile(r'["\']exitLoad["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'["\']exit_load["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'["\']exitLoad["\']\s*:\s*(\d+(?:\.\d+)?)\s*[,}]', re.IGNORECASE),
    re.compile(r'["\']Exit\s*Load["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r"exitLoad[\"']?\s*:\s*[\"']?([^\"',}\s]+%?)[\"']?\s*[,}]", re.IGNORECASE),
]
# Table cell: <td>Exit Load</td>...<td>value</td>
EXIT_LOAD_TABLE_PATTERN = re.compile(
    r"<td[^>]*>\s*exit\s*load\s*</td[^>]*>\s*<td[^>]*>([^<]+)</td",
    re.IGNORECASE | re.DOTALL,
)


def _fetch_urllib(url: str, timeout: int, headers: dict) -> Optional[str]:
    """Fetch with urllib. Returns response text or None."""
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, OSError):
        return None


def _fetch_requests(url: str, timeout: int, headers: dict) -> Optional[str]:
    """Fetch with requests if available (sometimes avoids 403). Returns response text or None."""
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.ok:
            return r.text
    except Exception:
        pass
    return None


def fetch_fee_page(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetch HTML from URL. Returns raw response text or None on failure.
    Tries urllib first, then requests (if available) with browser-like headers; retries with longer timeout.
    """
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "identity",
        },
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept-Encoding": "identity",
        },
    ]
    for attempt, t in enumerate([timeout, 20]):
        for headers in headers_list:
            html = _fetch_urllib(url, t, headers)
            if html:
                return html
            html = _fetch_requests(url, t, headers)
            if html:
                return html
        if attempt == 0:
            logger.warning("Fee explanation fetch attempt 1 failed for %s; retrying with longer timeout.", url)
    logger.warning("Fee explanation fetch failed for %s (all attempts).", url)
    return None


def _extract_from_script_and_tables(html: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract exit load text and value from JSON in script tags and from table cells.
    Returns (exit_load_text, exit_load_value) for use when main HTML has no visible text.
    """
    exit_load_text = None
    exit_load_value = None
    # Table: <td>Exit Load</td><td>1%</td> or similar
    m = EXIT_LOAD_TABLE_PATTERN.search(html)
    if m:
        exit_load_value = " ".join(m.group(1).split()).strip()[:100]
        exit_load_text = exit_load_value
    # Script blocks: look for JSON-like "exitLoad":"1%" or "exit_load": "1%"
    for script in re.finditer(r"<script[^>]*>([^<]*(?:exitLoad|exit_load|Exit\s*Load)[^<]*)</script>", html, re.IGNORECASE | re.DOTALL):
        blob = script.group(1)
        for pat in EXIT_LOAD_JSON_PATTERNS:
            m = pat.search(blob)
            if m:
                val = m.group(1).strip()
                if val and len(val) < 80:
                    if not exit_load_value:
                        exit_load_value = val if "%" in val else f"{val}%"
                    if not exit_load_text:
                        exit_load_text = exit_load_value
                break
        if exit_load_value:
            break
    return (exit_load_text, exit_load_value)


def extract_fee_snippets(html: str, source_url: str) -> dict:
    """
    Parse HTML for exit load and fee-related snippets.
    Returns dict with keys: exit_load, expense_ratio, snippets, source_url.
    """
    # Try JSON/table extraction first (data often in script tags or tables)
    from_script_exit, from_script_value = _extract_from_script_and_tables(html)

    # Strip script/style to reduce noise for text search
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    exit_load = None
    for pat in EXIT_LOAD_PATTERNS:
        m = pat.search(html) or pat.search(text)
        if m:
            exit_load = m.group(1).strip()[:200]
            break

    expense_ratio = None
    for pat in EXPENSE_RATIO_PATTERNS:
        m = pat.search(html) or pat.search(text)
        if m:
            expense_ratio = m.group(1).strip()[:200]
            break

    # Prefer a clean exit load number for display (e.g. "1%" or "1.00% if redeemed within 1 year")
    exit_load_value = None
    for i, pat in enumerate(EXIT_LOAD_NUMBER_PATTERNS):
        m = pat.search(html) or pat.search(text)
        if m:
            # Pattern 2 captures a phrase like "1.00% if redeemed..."; use it. Others use percentage only.
            if i == 1 and len(m.group(0)) <= 80:
                exit_load_value = m.group(0).strip()
            else:
                exit_load_value = m.group(1).strip()
            break
    if not exit_load_value and exit_load:
        pm = re.search(r"\d+(?:\.\d+)?\s*%", exit_load)
        if pm:
            exit_load_value = pm.group(0)
    # Use values from JSON/table when visible HTML had nothing (e.g. JS-rendered page)
    if not exit_load and from_script_exit:
        exit_load = from_script_exit
    if not exit_load_value and from_script_value:
        exit_load_value = from_script_value

    # General + specific block around "exit load" (for bullets)
    exit_load_block = None
    for m in EXIT_LOAD_BLOCK_PATTERN.finditer(text):
        block = " ".join(m.group(0).split()).strip()[:400]
        if block and len(block) > 30:
            exit_load_block = block
            break
    if not exit_load_block and exit_load:
        exit_load_block = exit_load[:400]

    # Specific lines from source (values to stamp in bullets)
    exit_load_details: list = []
    search_text = text or html
    if search_text:
        for pat in EXIT_LOAD_LINE_PATTERNS:
            for m in pat.finditer(search_text):
                line = " ".join(m.group(1).split()).strip()
                if len(line) > 4 and line not in exit_load_details:
                    exit_load_details.append(line[:120])
            if exit_load_details:
                break
    if not exit_load_details and exit_load_value:
        exit_load_details = [exit_load_value]
    if not exit_load_block and (exit_load or exit_load_value):
        exit_load_block = (exit_load or "") + " " + (exit_load_value or "")
        exit_load_block = " ".join(exit_load_block.split()).strip()[:400]

    snippets = []
    for m in FEE_SNIPPET_PATTERN.finditer(text):
        s = m.group(0).strip()
        if len(s) > 10 and s not in snippets:
            snippets.append(s[:150])
    # Fallback: any percentage phrase (e.g. "1.00% if redeemed within 1 year")
    if not snippets and text:
        for m in PERCENTAGE_PATTERN.finditer(text[:3000]):
            s = m.group(0).strip()
            if len(s) > 6 and s not in snippets:
                snippets.append(s[:120])
                if len(snippets) >= 3:
                    break

    return {
        "exit_load": exit_load,
        "expense_ratio": expense_ratio,
        "exit_load_value": exit_load_value,
        "exit_load_block": exit_load_block,
        "exit_load_details": exit_load_details[:5],
        "snippets": snippets[:5],
        "source_url": source_url,
        "raw_preview": text[:1500] if text else "",
    }
