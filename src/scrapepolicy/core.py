from __future__ import annotations

from urllib.parse import urlparse

import httpx

from . import __version__
from .discovery import find_links
from .models import SiteInfo
from .robots import can_fetch, parse_robots

USER_AGENT = f"scrapepolicy/{__version__} (+https://github.com/billycemerson/scrapepolicy)"


def _origin(url: str) -> str:
    """'kompas.com/x' -> 'https://kompas.com'"""
    if "://" not in url:
        url = f"https://{url}"
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}"


def _get(client: httpx.Client, url: str, info: SiteInfo) -> httpx.Response | None:
    """GET that never throws an error: failures are recorded in info.warnings."""
    try:
        response = client.get(url)
    except httpx.HTTPError as exc:
        info.warnings.append(f"{url}: {type(exc).__name__}")
        return None
    if response.status_code != 200:
        info.warnings.append(f"{url}: HTTP {response.status_code}")
        return None
    return response

def inspect(url: str, *, client: httpx.Client | None = None, timeout: float = 10.0) -> SiteInfo:
    origin = _origin(url)
    owns_client = client is None
    if client is None:
        client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True
        )
    try:
        return _inspect(origin, client)
    finally:
        if owns_client:
            client.close()

def _inspect(origin: str, client: httpx.Client) -> SiteInfo:
    info = SiteInfo(url=origin)
    robots_text = ""

    # Fetch and parse robots.txt.
    robots_url = f"{origin}/robots.txt"
    response = _get(client, robots_url, info)
    if response is not None:
        # Some sites answer 200 with a normal HTML page instead of a 404.
        if "<html" in response.text[:500].lower():
            info.warnings.append(f"{robots_url}: returned HTML, ignored")
        else:
            robots_text = response.text
            info.robots = parse_robots(robots_text, robots_url)

    # Respect robots.txt ourselves: do not fetch the homepage if it is disallowed.
    if robots_text and not can_fetch(robots_text, USER_AGENT, f"{origin}/"):
        info.warnings.append("robots.txt disallows the homepage; page links not fetched")
        return info

    # Fetch the homepage and look for terms / about / contact links.
    home = _get(client, f"{origin}/", info)
    if home is not None:
        # Use the final URL (after redirects, e.g. to www.) as the base for relative links.
        links = find_links(home.text, str(home.url))
        info.terms_of_use = links["terms_of_use"]
        info.about = links["about"]
        info.contact = links["contact"]

    return info