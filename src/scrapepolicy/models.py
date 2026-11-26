from __future__ import annotations

from dataclasses import asdict, dataclass, field


def _unique(names):
    """Case-insensitive de-duplication that keeps the first spelling and the order."""
    seen: dict[str, str] = {}
    for name in names:
        seen.setdefault(name.lower(), name)
    return list(seen.values())


@dataclass
class RobotsGroup:
    """One block of rules that applies to one or more user agents."""

    user_agents: list[str]
    allow: list[str] = field(default_factory=list)
    disallow: list[str] = field(default_factory=list)
    crawl_delay: float | None = None


@dataclass
class RobotsInfo:
    url: str
    groups: list[RobotsGroup] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def blocked_agents(self) -> list[str]:
        """Agents blocked from the whole site: Disallow '/' and no Allow rules at all."""
        return _unique(
            agent
            for group in self.groups
            if "/" in group.disallow and not group.allow
            for agent in group.user_agents
        )

    @property
    def restricted_agents(self) -> list[str]:
        """Agents blocked from '/' but with Allow exceptions (e.g. GPTBot -> /read/cm/)."""
        return _unique(
            agent
            for group in self.groups
            if "/" in group.disallow and group.allow and "/" not in group.allow
            for agent in group.user_agents
        )


@dataclass
class SiteInfo:
    url: str
    robots: RobotsInfo | None = None
    terms_of_use: str | None = None
    about: str | None = None
    contact: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def sitemaps(self) -> list[str]:
        return self.robots.sitemaps if self.robots else []

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.robots:
            data["robots"]["blocked_agents"] = self.robots.blocked_agents
            data["robots"]["restricted_agents"] = self.robots.restricted_agents
        return data