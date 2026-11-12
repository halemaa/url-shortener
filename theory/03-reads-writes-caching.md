# 3. Reads, writes, and caching

## Two kinds of request

- A **write** changes stored data: creating a short link.
- A **read** only looks something up: following a short link.

Most systems are lopsided. A URL shortener is **read-heavy**: a link
is created once and may be followed thousands of times. A logging
system is the opposite: it writes constantly and is read rarely.

Knowing which way your system leans tells you where to spend effort.
In a read-heavy system, you make reads cheap.

## What a cache is

A cache is a small, fast copy of data you expect to need again.

Without a cache, every lookup goes to the database. With one:

1. Look in the cache. If the answer is there, return it. This is a **hit**.
2. If not, it is a **miss**: ask the database, return the answer, and
   put a copy in the cache for next time.

In `shortener.py`, `expand()` does exactly this.

## The cache is small on purpose

If the cache held everything, it would just be a second database in
memory. It is kept small, so it needs a rule for what to remove when
it is full.

**LRU (least recently used):** remove the entry that has gone longest
without being used.

Example with room for two entries:

```
put A        cache: A
put B        cache: A, B
get A        cache: B, A      (A was just used, so it moves to the back)
put C        cache: A, C      (full: B has gone longest unused, so B is removed)
```

Python's `OrderedDict` makes this short: `move_to_end(key)` marks an
entry as just used, and `popitem(last=False)` removes the oldest.

## Why a small cache helps a lot

Clicks are not spread evenly. A few links get most of the traffic and
most links get very little. A small cache holding the busy links
answers a large share of all lookups.

The cache in this project counts its hits and misses, so the benefit
can be measured instead of assumed.

## The hard part of caching, and why it is absent here

The classic caching problem is **stale data**: the database changes
and the cache still holds the old value.

Here, a link never changes after it is created. Nothing can be edited
or deleted. So a cached entry can never be wrong. If editing links
were added later, the cache entry would have to be removed at the same
moment as the database row is changed.

## One process only

This cache lives in the memory of one running program. Two servers
would each have their own. Larger systems move the cache to a shared
service so every server sees the same entries. See `../design/scaling.md`.
