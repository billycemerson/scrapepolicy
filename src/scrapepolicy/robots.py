from __future__ import annotations

from urllib.robotparser import RobotFileParser

from .models import RobotsGroup, RobotsInfo


def parse_robots(text: str, url: str = "") -> RobotsInfo:
    """Parse robots.txt text into rule groups plus sitemap links.

    Empty ``Disallow:`` lines (meaning "allow everything") are not recorded.
    """
    info = RobotsInfo(url=url, raw=text)
    group: RobotsGroup | None = None  # the group currently being filled
    has_rules = False  # True once the current group has an allow/disallow/crawl-delay line

    # Strip a leading BOM, which some servers include.
    for line in text.lstrip("\ufeff").splitlines():
        # Drop inline comments and surrounding whitespace.
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue

        # Split on the FIRST colon only: sitemap URLs contain colons too.
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()

        if key == "sitemap":
            # Sitemap lines are global: they never affect the current group.
            if value and value not in info.sitemaps:
                info.sitemaps.append(value)

        elif key == "user-agent":
            # Start a new group if there is none yet, or if the current one
            # already has rules. Otherwise consecutive User-agent lines share
            # the same set of rules.
            if group is None or has_rules:
                group = RobotsGroup(user_agents=[])
                info.groups.append(group)
                has_rules = False
            group.user_agents.append(value)

        elif group is not None and key in {"allow", "disallow", "crawl-delay"}:
            # Rule lines before the first User-agent are ignored (group is None).
            has_rules = True
            if key == "allow" and value:
                group.allow.append(value)
            elif key == "disallow" and value:
                group.disallow.append(value)
            elif key == "crawl-delay":
                try:
                    group.crawl_delay = float(value)
                except ValueError:
                    pass  # ignore malformed values such as "fast"

    return info


def can_fetch(robots_text: str, user_agent: str, url: str) -> bool:
    """
    Check if a user agent can fetch a URL based on robots.txt rules.
    """
    parser = RobotFileParser()
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(user_agent, url)