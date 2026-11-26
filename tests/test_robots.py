from scrapepolicy import parse_robots

ROBOTS = """\
# comment
User-agent: *
Disallow: /search
Disallow: /admin  # inline comment
Allow: /search/about
Crawl-delay: 10

User-agent: GPTBot
User-agent: CCBot
Disallow: /

User-agent: Googlebot
Disallow:

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/news-sitemap.xml
"""


def test_groups_and_rules():
    star = parse_robots(ROBOTS).groups[0]
    assert star.user_agents == ["*"]
    assert star.disallow == ["/search", "/admin"]
    assert star.allow == ["/search/about"]
    assert star.crawl_delay == 10.0


def test_multiple_agents_share_a_group():
    info = parse_robots(ROBOTS)
    assert info.groups[1].user_agents == ["GPTBot", "CCBot"]
    assert info.groups[1].disallow == ["/"]


def test_blocked_agents_and_sitemaps():
    info = parse_robots(ROBOTS)
    assert info.blocked_agents == ["GPTBot", "CCBot"]
    assert info.sitemaps == [
        "https://example.com/sitemap.xml",
        "https://example.com/news-sitemap.xml",
    ]


def test_empty_disallow_is_not_recorded():
    info = parse_robots(ROBOTS)
    assert info.groups[2].user_agents == ["Googlebot"]
    assert info.groups[2].disallow == []


def test_blocked_restricted_and_dedupe():
    info = parse_robots(
        "User-agent: GPTBot\nAllow: /read/\nDisallow: /\n\n"
        "User-agent: CCBot\nDisallow: /\n\n"
        "User-agent: ccbot\nDisallow: /\n"
    )
    assert info.blocked_agents == ["CCBot"]
    assert info.restricted_agents == ["GPTBot"]
    

def test_empty_text():
    info = parse_robots("")
    assert info.groups == [] and info.sitemaps == []