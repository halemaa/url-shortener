# Decision 001: How short codes are generated

**Status:** accepted

## The question

Every stored URL needs a short code. How is that code produced?

## Options

| Option | How it works | Good | Bad |
|---|---|---|---|
| Counter | 1, 2, 3… encoded in base62 | Never collides; shortest possible codes | Codes are guessable: anyone can walk through every link ever created |
| Hash of the URL | Hash the URL, keep the first 6 characters | Same URL always gives the same code | Two different URLs can share a prefix, so collisions still need handling |
| Random | 6 random base62 characters | Not guessable; simple | Collisions are possible and must be checked |

## Choice

Random base62, 6 characters, generated with Python's `secrets` module.
If the code is already taken, generate another (up to 10 attempts).

## Why

- A short link often points at something semi-private (a shared
  document, an unlisted page). Guessable codes would let a stranger
  enumerate every link. That rules out the plain counter.
- 6 base62 characters give 62^6, about 56.8 billion, possible codes.
  With a few thousand or even a few million links stored, a random
  clash is rare, and the retry makes it harmless.
- The "same URL gives the same code" benefit of hashing is kept a
  different way: the database has a unique index on the URL, and
  `shorten` returns the existing code if the URL is already stored.

## Cost of this choice

- Every insert needs a uniqueness check. Here the database's primary
  key does it, so it costs one failed insert on a collision.
- As the table fills, collisions become more frequent. Long before
  that matters, the code length would be raised to 7.
- Random codes cannot be generated independently by several servers
  without that same database check.

## How it is tested

`test_collision_is_retried` forces the generator to return the same
code twice and checks that the second URL ends up with a fresh one.
