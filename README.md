# url-shortener

A small, working URL shortener, built as a **system design** exercise.
The code is short. The interesting part is the `design/` folder, which
records each decision, the options considered, and what the choice costs.

Pure Python, standard library only (SQLite is built in).

## See it work

```bash
$ python shorten.py add https://github.com/halemaa/notes-api/blob/main/README.md
http://short.ly/MAP5ii

$ python shorten.py expand MAP5ii
https://github.com/halemaa/notes-api/blob/main/README.md

$ python shorten.py stats MAP5ii
Code   : MAP5ii
URL    : https://github.com/halemaa/notes-api/blob/main/README.md
Clicks : 1

$ python shorten.py list
http://short.ly/MAP5ii  (1 clicks)  https://github.com/halemaa/notes-api/...
```

`short.ly` is a placeholder domain. This repo is the engine (generate,
store, look up, count, limit); it does not run a web server.

## The four design decisions

| Decision | Choice | Record |
|---|---|---|
| How to make short codes | Random base62, 6 characters, with a collision check | [design/001-code-generation.md](design/001-code-generation.md) |
| Where to store mappings | SQLite, one file | [design/002-storage.md](design/002-storage.md) |
| How to make lookups fast | In-memory LRU cache | [design/003-caching.md](design/003-caching.md) |
| How to stop abuse | Sliding-window rate limit per client | [design/004-rate-limiting.md](design/004-rate-limiting.md) |

What changes as traffic grows is in [design/scaling.md](design/scaling.md).

## What's in the box

```
shortener.py              core: codes, storage, cache, rate limiter
shorten.py                command line
tests/test_shortener.py   20 passing tests
design/                   four decision records + a scaling note
theory/                   four beginner-level notes on system design
```

## Run the tests

```bash
pytest tests
```

The tests cover the round trip, duplicate URLs, a forced collision,
persistence across a restart, cache eviction, and the rate limiter
(using a fake clock, so no test has to wait 60 seconds).

## Read the theory

1. [What system design is](theory/01-what-is-system-design.md)
2. [The four decisions, explained with a parcel shop](theory/02-the-four-decisions.md)
3. [Read-heavy systems and caching](theory/03-reads-writes-caching.md)
4. [How to talk about trade-offs](theory/04-talking-about-tradeoffs.md)

## Limits

- No web server: a real service needs an HTTP layer that answers a
  request for `/MAP5ii` with a redirect.
- The cache and the rate limiter live in one process's memory. With
  more than one server they would need a shared store (see
  [design/scaling.md](design/scaling.md)).
- Links never expire and cannot be deleted.
- No check that a target URL is safe. Real shorteners screen links
  against malware and phishing lists, because short links hide the
  destination.

## Related repos

- [`log-anomaly-detector`](https://github.com/halemaa/log-anomaly-detector):
  the sliding window used here for rate limiting
- [`duplicate-file-finder`](https://github.com/halemaa/duplicate-file-finder):
  hashing and collisions
