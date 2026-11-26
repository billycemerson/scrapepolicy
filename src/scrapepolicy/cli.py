from __future__ import annotations

import argparse
import json

from .core import inspect


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="scrapepolicy",
        description="Inspect a website's robots.txt, sitemaps, terms of use, about and contact pages.",
    )
    parser.add_argument("url", help="website URL, e.g. https://example.com")
    parser.add_argument("--raw", action="store_true", help="include raw robots.txt text")
    args = parser.parse_args(argv)

    data = inspect(args.url).to_dict()
    if not args.raw and data["robots"]:
        data["robots"].pop("raw")
    print(json.dumps(data, indent=2, ensure_ascii=False))