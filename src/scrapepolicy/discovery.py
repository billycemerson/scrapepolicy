from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

KEYWORDS: dict[str, list[str]] = {
    "terms_of_use": [
        "terms of use", "terms of service", "terms and conditions",
        "terms & conditions", "terms", "syarat dan ketentuan",
        "syarat & ketentuan", "syarat ketentuan", "ketentuan layanan",
        "ketentuan penggunaan",
    ],
    "about": ["about us", "about", "tentang kami", "tentang"],
    "contact": ["contact us", "contact", "hubungi kami", "kontak kami", "kontak", "hubungi"],
}

URL_HINTS: dict[str, set[str]] = {
    "terms_of_use": {"terms", "term", "tos", "syarat", "ketentuan"},
    "about": {"about", "aboutus", "tentang", "tentangkami"},
    "contact": {"contact", "contactus", "kontak", "hubungi", "hubungikami"},
}

MIN_SCORE = 2
MAX_TEXT_LEN = 40

def _score(kind: str, text: str, tokens: set[str], in_footer: bool) -> int:
    """Score how well one link matches one page type (higher is better).

    Scoring:
      - link text equals a keyword exactly ........ 3
      - link text contains a keyword as a word ..... 2
      - URL path has a hint token .................. +1
      - link is inside a footer (only if score > 0)  +1
    """
    score = 0

    # Only short link texts count, so long article headlines that happen to
    # contain "terms" or "about" are not mistaken for policy pages.
    if text and len(text) <= MAX_TEXT_LEN:
        for keyword in KEYWORDS[kind]:
            if text == keyword:
                score = max(score, 3)
            elif re.search(rf"\b{re.escape(keyword)}\b", text):
                score = max(score, 2)

    # URL hints work on whole path tokens, so "/photos" does not match "tos".
    if tokens & URL_HINTS[kind]:
        score += 1

    # Being in a footer reinforces a match but is never enough on its own.
    if score and in_footer:
        score += 1

    return score


def _in_footer(tag) -> bool:
    """Return True if the tag sits inside a <footer> or a footer-like container."""
    for parent in tag.parents:
        if parent.name == "footer":
            return True
        # "class" is a list in BeautifulSoup, "id" is a string (or None).
        marks = " ".join(parent.get("class", [])) + " " + (parent.get("id") or "")
        if "footer" in marks.lower():
            return True
    return False


def find_links(html: str, base_url: str) -> dict[str, str | None]:
    """Return the best link for each page type, or None if nothing fits."""
    soup = BeautifulSoup(html, "html.parser")

    # kind -> (best score so far, URL that earned it)
    best: dict[str, tuple[int, str | None]] = {kind: (0, None) for kind in KEYWORDS}

    for anchor in soup.find_all("a", href=True):
        # Resolve relative links ("/terms", "legal/tos") against the page URL.
        url = urljoin(base_url, str(anchor["href"]).strip())
        if urlparse(url).scheme not in {"http", "https"}:
            continue  # skip mailto:, javascript:, tel:, ...

        # Normalise link text: collapse whitespace, lowercase.
        text = " ".join(anchor.get_text(" ").split()).lower()
        # Split the URL path into tokens: "/syarat-dan-ketentuan" -> {"syarat", "dan", "ketentuan"}.
        tokens = set(re.split(r"[/\-_.]+", urlparse(url).path.lower()))
        footer = _in_footer(anchor)

        for kind in KEYWORDS:
            score = _score(kind, text, tokens, footer)
            # Strictly greater: on ties, the link that appears first wins.
            if score > best[kind][0]:
                best[kind] = (score, url)

    # Below MIN_SCORE we prefer "not found" over a weak guess.
    return {kind: url if score >= MIN_SCORE else None for kind, (score, url) in best.items()}