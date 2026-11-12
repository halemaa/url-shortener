# Decision 002: Where mappings are stored

**Status:** accepted

## The question

The mapping `code -> long URL` has to survive a restart. Where does it live?

## Options

| Option | Good | Bad |
|---|---|---|
| Python dict in memory | Fastest, zero setup | Everything is lost when the program stops |
| JSON file | Simple, readable | The whole file is rewritten on every change; unsafe if two writers overlap |
| SQLite | One file, real transactions, indexes, built into Python | One machine only; one writer at a time |
| Postgres / MySQL server | Many servers can share it; replication | Needs installing, running, and securing |
| Key-value store (Redis, DynamoDB) | A natural fit for `code -> url`; very fast | Another service to run; extra care needed for durability |

## Choice

SQLite, one table:

```sql
CREATE TABLE links (
    code       TEXT PRIMARY KEY,
    url        TEXT NOT NULL UNIQUE,
    clicks     INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
```

## Why

- The data is one simple table. There is nothing here that needs a
  database server.
- The primary key on `code` gives fast lookups and enforces uniqueness,
  which is what the collision check in decision 001 relies on.
- The unique index on `url` prevents the same URL being stored twice.
- It is in Python's standard library, so the project has no dependencies.

## Cost of this choice

- Only one process can write at a time. Fine for a single-machine
  tool; not fine for a service running on several servers.
- Counting a click is a write, so every lookup currently writes to the
  database. At real traffic levels, click counts would be batched or
  moved to a separate store.

## When to revisit

When the service needs more than one server. The table design carries
over to Postgres unchanged; only the connection code changes.
