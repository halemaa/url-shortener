"""
URL shortener command line.

Usage:
    python shorten.py add https://example.com/a/very/long/link
    python shorten.py expand aB3kF9
    python shorten.py stats aB3kF9
    python shorten.py list
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shortener import InvalidURL, RateLimited, URLShortener

BASE = "http://short.ly/"
DEFAULT_DB = str(Path(__file__).parent / "urls.db")


def main() -> int:
    parser = argparse.ArgumentParser(description="A small URL shortener.")
    parser.add_argument("--db", default=DEFAULT_DB, help="database file")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="shorten a URL")
    p_add.add_argument("url")

    p_exp = sub.add_parser("expand", help="look up a short code")
    p_exp.add_argument("code")

    p_stats = sub.add_parser("stats", help="show clicks for a short code")
    p_stats.add_argument("code")

    sub.add_parser("list", help="list every stored link")

    args = parser.parse_args()
    shortener = URLShortener(db_path=args.db)

    try:
        if args.cmd == "add":
            try:
                code = shortener.shorten(args.url)
            except InvalidURL as exc:
                print(exc, file=sys.stderr)
                return 2
            except RateLimited as exc:
                print(exc, file=sys.stderr)
                return 3
            print(f"{BASE}{code}")
            return 0

        if args.cmd == "expand":
            code = args.code.replace(BASE, "")
            url = shortener.expand(code)
            if url is None:
                print(f"No link found for code {code!r}.", file=sys.stderr)
                return 1
            print(url)
            return 0

        if args.cmd == "stats":
            code = args.code.replace(BASE, "")
            info = shortener.stats(code)
            if info is None:
                print(f"No link found for code {code!r}.", file=sys.stderr)
                return 1
            print(f"Code   : {info.code}")
            print(f"URL    : {info.url}")
            print(f"Clicks : {info.clicks}")
            return 0

        links = shortener.all_links()
        if not links:
            print("No links stored yet.")
            return 0
        for info in links:
            print(f"{BASE}{info.code}  ({info.clicks} clicks)  {info.url}")
        return 0
    finally:
        shortener.close()


if __name__ == "__main__":
    sys.exit(main())
