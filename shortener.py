"""
A small URL shortener: the classic system design exercise, built for real.

Four design decisions live in this file (each has a record in design/):

  1. Short codes are RANDOM base62 strings, with a collision check.
  2. Mappings are stored in SQLite (one file, survives restarts).
  3. Lookups go through a small LRU cache (the system is read-heavy).
  4. Creating links is rate limited per client with a sliding window.
"""

from __future__ import annotations

import secrets
import sqlite3
import string
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

ALPHABET = string.digits + string.ascii_letters      # 62 characters
CODE_LENGTH = 6                                      # 62^6 = ~56 billion codes
MAX_ATTEMPTS = 10


class InvalidURL(ValueError):
    """The text given is not an http(s) URL."""


class RateLimited(RuntimeError):
    """The client has created too many links in the current window."""


@dataclass(frozen=True)
class LinkStats:
    code: str
    url: str
    clicks: int
    created_at: float


# -------------------------------------------------------------------
# Decision 4: rate limiting (sliding window, one deque per client)
# -------------------------------------------------------------------

class RateLimiter:
    """Allow at most `limit` actions per `window_seconds` per client."""

    def __init__(self, limit: int, window_seconds: float,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._events: dict[str, deque[float]] = {}

    def allow(self, client: str) -> bool:
        now = self.clock()
        events = self._events.setdefault(client, deque())
        # Shrink: forget anything older than the window.
        while events and events[0] <= now - self.window:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True


# -------------------------------------------------------------------
# Decision 3: caching (least-recently-used, fixed size)
# -------------------------------------------------------------------

class LRUCache:
    """Keep the `capacity` most recently used code -> url pairs in memory."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._items: OrderedDict[str, str] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> str | None:
        if key in self._items:
            self._items.move_to_end(key)       # mark as recently used
            self.hits += 1
            return self._items[key]
        self.misses += 1
        return None

    def put(self, key: str, value: str) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)    # evict the least recently used


# -------------------------------------------------------------------
# The shortener itself
# -------------------------------------------------------------------

def validate_url(url: str) -> str:
    """Accept only http and https URLs that have a host."""
    cleaned = url.strip()
    parts = urlparse(cleaned)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise InvalidURL(f"Not a valid http(s) URL: {url!r}")
    return cleaned


def random_code(length: int = CODE_LENGTH) -> str:
    """Decision 1: an unguessable random base62 code."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


class URLShortener:
    def __init__(
        self,
        db_path: str = "urls.db",
        cache_size: int = 128,
        rate_limit: int = 10,
        rate_window: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
        code_factory: Callable[[], str] = random_code,
    ) -> None:
        # Decision 2: SQLite, one file.
        self._db = sqlite3.connect(db_path)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                code       TEXT PRIMARY KEY,
                url        TEXT NOT NULL UNIQUE,
                clicks     INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            )
            """
        )
        self._db.commit()
        self.cache = LRUCache(cache_size)
        self.limiter = RateLimiter(rate_limit, rate_window, clock)
        self._code_factory = code_factory

    # ---- write path -------------------------------------------------

    def shorten(self, url: str, client: str = "local") -> str:
        """Store `url` and return its short code."""
        url = validate_url(url)

        if not self.limiter.allow(client):
            raise RateLimited(
                f"Too many links created by {client!r}. Try again shortly."
            )

        # The same URL always gets the same code (no duplicates).
        row = self._db.execute(
            "SELECT code FROM links WHERE url = ?", (url,)
        ).fetchone()
        if row:
            return row[0]

        # Random code + collision check: if the code is taken, try another.
        for _ in range(MAX_ATTEMPTS):
            code = self._code_factory()
            try:
                self._db.execute(
                    "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
                    (code, url, time.time()),
                )
                self._db.commit()
                return code
            except sqlite3.IntegrityError:
                continue                        # collision: generate again
        raise RuntimeError("Could not find a free short code.")

    # ---- read path --------------------------------------------------

    def expand(self, code: str) -> str | None:
        """Return the long URL for `code`, or None if it doesn't exist."""
        url = self.cache.get(code)
        if url is None:
            row = self._db.execute(
                "SELECT url FROM links WHERE code = ?", (code,)
            ).fetchone()
            if row is None:
                return None
            url = row[0]
            self.cache.put(code, url)

        self._db.execute(
            "UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,)
        )
        self._db.commit()
        return url

    def stats(self, code: str) -> LinkStats | None:
        row = self._db.execute(
            "SELECT code, url, clicks, created_at FROM links WHERE code = ?",
            (code,),
        ).fetchone()
        return LinkStats(*row) if row else None

    def all_links(self) -> list[LinkStats]:
        rows = self._db.execute(
            "SELECT code, url, clicks, created_at FROM links "
            "ORDER BY created_at"
        ).fetchall()
        return [LinkStats(*r) for r in rows]

    def close(self) -> None:
        self._db.close()
