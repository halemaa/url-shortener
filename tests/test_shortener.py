"""Tests for the URL shortener."""

import pytest

from shortener import (
    ALPHABET,
    CODE_LENGTH,
    InvalidURL,
    LRUCache,
    RateLimited,
    RateLimiter,
    URLShortener,
    random_code,
    validate_url,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def shortener(tmp_path):
    s = URLShortener(db_path=str(tmp_path / "test.db"), rate_limit=1000)
    yield s
    s.close()


# ---------- codes and validation ----------

def test_random_code_shape():
    code = random_code()
    assert len(code) == CODE_LENGTH
    assert all(c in ALPHABET for c in code)


def test_validate_accepts_http_and_https():
    assert validate_url("https://example.com/a") == "https://example.com/a"
    assert validate_url(" http://example.com ") == "http://example.com"


@pytest.mark.parametrize("bad", ["", "example.com", "ftp://x.com", "javascript:alert(1)", "https://"])
def test_validate_rejects_bad_urls(bad):
    with pytest.raises(InvalidURL):
        validate_url(bad)


# ---------- shorten and expand ----------

def test_round_trip(shortener):
    code = shortener.shorten("https://example.com/long/path")
    assert shortener.expand(code) == "https://example.com/long/path"


def test_same_url_gets_same_code(shortener):
    a = shortener.shorten("https://example.com/x")
    b = shortener.shorten("https://example.com/x")
    assert a == b


def test_different_urls_get_different_codes(shortener):
    a = shortener.shorten("https://example.com/1")
    b = shortener.shorten("https://example.com/2")
    assert a != b


def test_unknown_code_returns_none(shortener):
    assert shortener.expand("nope00") is None


def test_clicks_are_counted(shortener):
    code = shortener.shorten("https://example.com/c")
    for _ in range(3):
        shortener.expand(code)
    assert shortener.stats(code).clicks == 3


def test_links_survive_a_restart(tmp_path):
    path = str(tmp_path / "persist.db")
    first = URLShortener(db_path=path)
    code = first.shorten("https://example.com/keep")
    first.close()

    second = URLShortener(db_path=path)
    assert second.expand(code) == "https://example.com/keep"
    second.close()


def test_collision_is_retried(tmp_path):
    """If the generated code is already taken, a new one is tried."""
    codes = iter(["same01", "same01", "fresh2"])
    s = URLShortener(db_path=str(tmp_path / "c.db"),
                     code_factory=lambda: next(codes))
    first = s.shorten("https://example.com/a")
    second = s.shorten("https://example.com/b")
    assert first == "same01"
    assert second == "fresh2"
    s.close()


# ---------- cache ----------

def test_cache_hit_after_first_lookup(shortener):
    code = shortener.shorten("https://example.com/cached")
    shortener.expand(code)      # miss, fills the cache
    shortener.expand(code)      # hit
    assert shortener.cache.hits == 1
    assert shortener.cache.misses == 1


def test_lru_evicts_least_recently_used():
    cache = LRUCache(capacity=2)
    cache.put("a", "1")
    cache.put("b", "2")
    cache.get("a")              # "a" is now the most recently used
    cache.put("c", "3")         # evicts "b"
    assert cache.get("b") is None
    assert cache.get("a") == "1"
    assert cache.get("c") == "3"


# ---------- rate limiting ----------

def test_rate_limiter_blocks_after_limit():
    clock = FakeClock()
    limiter = RateLimiter(limit=3, window_seconds=60, clock=clock)
    assert [limiter.allow("x") for _ in range(4)] == [True, True, True, False]


def test_rate_limiter_recovers_after_window():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
    assert limiter.allow("x")
    assert not limiter.allow("x")
    clock.now = 61
    assert limiter.allow("x")


def test_rate_limit_is_per_client():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window_seconds=60, clock=clock)
    assert limiter.allow("alice")
    assert limiter.allow("bob")


def test_shorten_raises_when_rate_limited(tmp_path):
    clock = FakeClock()
    s = URLShortener(db_path=str(tmp_path / "r.db"), rate_limit=2, clock=clock)
    s.shorten("https://example.com/1")
    s.shorten("https://example.com/2")
    with pytest.raises(RateLimited):
        s.shorten("https://example.com/3")
    s.close()
