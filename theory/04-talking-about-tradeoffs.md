# 4. How to talk about trade-offs

In a system design interview you are assessed on your reasoning more
than on the final diagram. This note is about how to say it.

## The four-part sentence

For any decision:

1. **The options** you considered
2. **The choice** you made
3. **Why**, tied to something about this system
4. **The cost** you accepted

Example, for short codes:

> "I could use a counter, a hash of the URL, or random codes. I chose
> random codes, because a counter makes every link guessable. The cost
> is that two links can get the same code, so I check the database and
> try again when that happens."

That is a complete answer in three sentences.

## Questions you should expect, with answers from this project

**"What if two URLs get the same code?"**
The code column is the primary key, so the second insert fails. The
program generates a new code and tries again. There is a test that
forces this to happen.

**"What if the same URL is submitted twice?"**
The URL column is unique. The program finds the existing row and
returns the same code.

**"What happens when the program restarts?"**
Links are in a SQLite file, so they survive. The cache and the
rate-limit counts are in memory, so they start empty.

**"What breaks first if traffic grows 100 times?"**
A single process serving reads, then SQLite's single writer. I would
run several app servers, move the table to a database server, and move
the cache and rate limits to a shared store.

**"How do you stop abuse?"**
Creation is limited to 10 links per client per minute with a sliding
window. A public service would also screen target URLs, because short
links hide where they lead.

## Three habits that help

- **Ask about size first.** "How many links per day? How many clicks?"
  The right design for 100 links is wrong for 100 million.
- **Start simple, then grow it.** Describe the one-machine version,
  then say what you would change and when. That is how
  `../design/scaling.md` is laid out.
- **Name the limit before you are asked.** "This cache only works on
  one server" is a stronger thing to say than to be caught on.

## Words worth knowing

| Word | Plain meaning |
|---|---|
| Collision | Two different inputs ending up with the same code |
| Read-heavy | Looked up far more often than changed |
| Cache hit / miss | The answer was / was not already in the cache |
| Eviction | Removing an entry to make room |
| Rate limit | A cap on requests per client per period |
| Load balancer | Spreads requests across several servers |
| Replica | A copy of the database used for reads |
| Bottleneck | The part that fails first as load grows |
