# 2. The four decisions, as a parcel pickup shop

Picture a shop where you drop off a parcel and the recipient collects
it later with a code sent by SMS.

- The parcel is the **long URL**.
- The pickup code is the **short code**.
- Handing over the parcel when someone shows the code is the **redirect**.

The whole service is two actions: drop off, and collect. The four
design decisions are how the shop is run.

## Decision 1: how the attendant invents codes

**Numbered tickets (1, 2, 3…).** Two parcels never share a code. But
anyone can guess that ticket 58 exists and try to collect it.

**Random codes.** Nobody can guess them. One day, though, the
attendant will write down a code that is already in use. That is a
**collision**. The fix is simple: check the book first, and if the
code is taken, make another.

**A code made from the parcel itself (a hash).** The same parcel
always gets the same code. Two different parcels can still clash, so
the check is needed anyway.

This project uses random codes with a check. In `shortener.py` the
"book" is the database: inserting a code that already exists fails,
and the loop tries again.

## Decision 2: where the record is kept

**In the attendant's head** (a Python dict): fast, and gone when the
attendant goes home.

**A notebook under the counter** (SQLite, one file): cheap, survives
the night, fine for one shop.

**A head-office system every branch shares** (a database server):
needed once there are several branches, and it costs more to run.

This project uses the notebook.

## Decision 3: drop-offs are rare, collections are constant

Each parcel is dropped off once, but asked about many times. So the
attendant keeps the most-requested parcels **on the counter** instead
of walking to the storeroom every time. That is a **cache**.

The counter is small. When a new popular parcel arrives and the
counter is full, the one that has gone longest without being asked for
goes back to the storeroom. That rule is called **LRU**, least
recently used.

## Decision 4: one customer arrives with 5,000 parcels

The shop would be stuck serving one person all day, and the storeroom
would fill up. So there is a rule: at most 10 drop-offs per customer
per minute. That is **rate limiting**.

To apply the rule, the attendant keeps a short list of each customer's
recent drop-off times, crosses off any older than a minute, and counts
what is left. That is a **sliding window**, the same pattern as
`log-anomaly-detector`.

Collections are not limited. Turning away the person collecting would
punish the wrong customer.

## Where each decision is in the code

| Shop | Code |
|---|---|
| Inventing a code | `random_code()` and the retry loop in `shorten()` |
| The notebook | the `links` table in SQLite |
| The counter | `LRUCache` |
| The drop-off rule | `RateLimiter` |
