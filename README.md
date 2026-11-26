# scrapepolicy

Check what a website publishes about bots and policies: its `robots.txt`
rules, sitemap links, and the links to its terms of use, about and contact
pages (`None` if not found).

> Status: early release (v0.1). The API may change.

## Install

```bash
pip install scrapepolicy
# or
uv add scrapepolicy
```

Requires Python 3.10+.

## Usage

```python
import scrapepolicy

info = scrapepolicy.inspect("https://example.com")

info.robots                   # None if robots.txt is missing or unusable
info.robots.groups            # user agents with allow / disallow / crawl_delay
info.robots.blocked_agents    # agents blocked from the whole site
info.robots.restricted_agents # blocked from "/" but with Allow exceptions
info.sitemaps                 # sitemap URLs declared in robots.txt
info.terms_of_use             # URL or None
info.about                    # URL or None
info.contact                  # URL or None
info.warnings                 # anything that went wrong while fetching
```

CLI:

```bash
scrapepolicy https://example.com          # JSON output
scrapepolicy https://example.com --raw    # include raw robots.txt
```

Example output (shortened):

```json
{
  "url": "https://example.com",
  "robots": {
    "url": "https://example.com/robots.txt",
    "groups": [
      {"user_agents": ["*"], "allow": [], "disallow": ["/search"], "crawl_delay": null},
      {"user_agents": ["GPTBot"], "allow": ["/read/"], "disallow": ["/"], "crawl_delay": null}
    ],
    "sitemaps": ["https://example.com/sitemap.xml"],
    "blocked_agents": [],
    "restricted_agents": ["GPTBot"]
  },
  "terms_of_use": "https://example.com/terms",
  "about": "https://example.com/about",
  "contact": null,
  "warnings": []
}
```

## Behaviour

- Makes at most two requests per site: `robots.txt` and the homepage.
- Identifies itself honestly (`scrapepolicy/<version>`).
- Reads `robots.txt` first. If it disallows the homepage for scrapepolicy,
  the homepage is not fetched, page links are `None`, and a warning says why.
- Finds links in the homepage (header, nav, footer) using English and
  Indonesian keywords.
- Network failures are reported in `warnings` instead of raising.

## Limitations

- Pages rendered only with JavaScript are not supported yet.
- Only the homepage is searched for links.
- Wildcard rules (`*`, `$`) are listed as published but not evaluated when
  checking the homepage.

## Disclaimer

Link discovery is heuristic. `robots.txt` is a convention, not legal
permission, and nothing here is legal advice. Read a site's terms before
scraping it.

## Development

```bash
uv sync
uv run pytest
```

## License

MIT