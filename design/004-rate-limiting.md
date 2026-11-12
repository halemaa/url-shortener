# Decision 004: Rate limiting link creation

**Status:** accepted

## The question

What stops one client from creating links without limit?

Unlimited creation fills the database, uses up short codes, and lets
the service be used to hide large numbers of spam or phishing links.

## Options

| Option | How it works | Good | Bad |
|---|---|---|---|
| No limit | | Nothing to build | Open to abuse |
| Fixed window | Count per calendar minute; reset at :00 | Very little memory | A client can send a full quota at 0:59 and another at 1:00 |
| Sliding window | Keep the time of each recent request; count those in the last 60 seconds | Accurate; no burst at the boundary | Memory grows with the limit |
| Token bucket | Tokens refill at a steady rate; each request spends one | Allows short bursts; constant memory | Slightly harder to explain and test |

## Choice

Sliding window: at most 10 new links per client per 60 seconds, with
one queue of timestamps per client.

## Why

- It is the same pattern as
  [`log-anomaly-detector`](https://github.com/halemaa/log-anomaly-detector):
  add the new event on the right, drop expired events from the left,
  then count.
- It has no boundary problem. "Last 60 seconds" always means the last
  60 seconds.
- With a limit of 10, each client's queue holds at most 10 timestamps,
  so the memory cost is small.

Only creating links is limited. Lookups are not, because blocking a
redirect punishes the person clicking, not the person who created the link.

## Cost of this choice

- The counts live in one process's memory. They reset on restart, and
  a second server would count separately.
- A client is identified by a name passed in by the caller. A real
  service would use an account or an IP address, and IP addresses can
  be shared or rotated.

## How it is tested

The limiter takes a clock as a parameter. The tests pass a fake clock
and move it forward, so "61 seconds later" takes no real time.
