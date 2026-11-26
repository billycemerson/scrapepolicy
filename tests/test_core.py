import httpx

import scrapepolicy
from scrapepolicy.core import USER_AGENT

HOME = '<footer><a href="/terms">Terms of Use</a><a href="/contact">Contact</a></footer>'


def make_client(routes: dict[str, httpx.Response]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return routes.get(request.url.path, httpx.Response(404))

    return httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )


def test_inspect_full():
    client = make_client({
        "/robots.txt": httpx.Response(
            200, text="User-agent: *\nDisallow: /x\nSitemap: https://example.com/s.xml"
        ),
        "/": httpx.Response(200, text=HOME),
    })
    info = scrapepolicy.inspect("example.com", client=client)
    assert info.sitemaps == ["https://example.com/s.xml"]
    assert info.terms_of_use == "https://example.com/terms"
    assert info.about is None
    assert info.contact == "https://example.com/contact"
    assert info.warnings == []


def test_homepage_disallowed_is_not_fetched():
    client = make_client({
        "/robots.txt": httpx.Response(200, text="User-agent: *\nDisallow: /"),
        "/": httpx.Response(200, text=HOME),
    })
    info = scrapepolicy.inspect("https://example.com", client=client)
    assert info.terms_of_use is None and info.contact is None
    assert any("disallows the homepage" in w for w in info.warnings)


def test_to_dict_robots_summary():
    client = make_client({
        "/robots.txt": httpx.Response(
            200,
            text=(
                "User-agent: GPTBot\nAllow: /read/\nDisallow: /\n\n"
                "User-agent: CCBot\nDisallow: /\n\n"
                "Sitemap: https://example.com/s.xml"
            ),
        ),
        "/": httpx.Response(200, text=HOME),
    })
    data = scrapepolicy.inspect("https://example.com", client=client).to_dict()
    assert data["robots"]["blocked_agents"] == ["CCBot"]
    assert data["robots"]["restricted_agents"] == ["GPTBot"]
    assert data["robots"]["sitemaps"] == ["https://example.com/s.xml"]
    assert "sitemaps" not in data  # only robots.sitemaps now, no duplicate