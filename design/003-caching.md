# Decision 003: Caching lookups

**Status:** accepted

## The question

A link is created once and looked up many times. How are lookups kept fast?

## Options

| Option | Good | Bad |
|---|---|---|
| No cache | Simplest; always correct | Every lookup hits the database |
| Cache everything in memory | Fastest | Memory grows without limit |
| LRU cache of fixed size | Bounded memory; keeps what is being used | Rarely used links still hit the database |
| Shared cache server (Redis) | Works across many servers | Another service to run |

## Choice

An in-memory **LRU** (least recently used) cache holding 128 entries.
When it is full and a new entry arrives, the entry that has gone
longest without being used is removed.

## Why

- Traffic to short links is usually uneven: a small number of links
  get most of the clicks. A small cache therefore answers a large
  share of lookups.
- LRU needs no tuning. Popular links stay because they keep being used.
- A mapping never changes after it is created (links cannot be edited
  or deleted), so a cached entry can never be out of date. That
  removes the hardest part of caching: knowing when to throw an entry away.

## Cost of this choice

- The cache belongs to one process. A second server would have its own
  cache and its own misses.
- If editing or deleting links were added, cached entries could become
  wrong and would need to be removed at the same moment.
- 128 is a guess. The cache counts hits and misses so the size can be
  judged from real use instead.

## How it is tested

`test_cache_hit_after_first_lookup` checks the first lookup is a miss
and the second is a hit. `test_lru_evicts_least_recently_used` checks
which entry is removed when the cache is full.
