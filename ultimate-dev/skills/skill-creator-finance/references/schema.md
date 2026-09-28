# Warehouse schema reference

SKILL.md names this file as the worked example of a `references/` entry worth
storing: *"Querying BigQuery requires re-discovering the table schemas and
relationships each time"* — so the schema goes in a reference file and the
SKILL.md keeps only the workflow and a pointer here.

A schema reference is not a data dictionary dump. It exists so that a query can
be written without a discovery round trip, and so that a wrong join is
impossible to write by accident. That sets what belongs in it.

> Reconstruction note: the example warehouse below is a small, invented analytics
> schema written to demonstrate the format. It is not a real BigQuery dataset,
> and the field lists are illustrative rather than authoritative for anything.

## Contents

- [What a schema reference must answer](#what-a-schema-reference-must-answer)
- [Format](#format)
- [Worked example](#worked-example)
- [Grain and keys](#grain-and-keys)
- [Join graph](#join-graph)
- [Conventions worth stating](#conventions-worth-stating)
- [Cost and freshness notes](#cost-and-freshness-notes)
- [What does not belong here](#what-does-not-belong-here)

## What a schema reference must answer

Five questions, and a reader who has all five can write a query without
exploring:

1. What is the **grain** of each table — one row is what?
2. What is the **primary key**, and is it enforced?
3. Which **columns are safe to group by**, and which are half-open (`status`
   has a `closed_at` that is null while the row is open).
4. Which **columns must be filtered** for a result to be correct — soft deletes,
   test accounts, rows loaded after the reporting window.
5. Which **other table** answers a question this table cannot.

If a table fails to answer 1 and 2, it is not ready to be documented. Find out
what a row is before writing the file, or the file will confidently encode a
wrong grain.

## Format

One block per table. Field names in code formatting, types from the warehouse
itself rather than a guess, and a one-line purpose for anything whose name is not
self-evident.

```
### table_name
Grain      one row per <entity> per <period or version>
Key        <column>            (enforced / not enforced)
Source     <system of record or pipeline that loads it>
Refresh    <schedule and lag>

| column | type | notes |
|---|---|---|
| ... | ... | ... |

Filters:  <conditions every correct query applies>
```

Keep the table of columns to the columns a query actually uses. A full dump
gets read once and then never again; a curated one gets consulted.

## Worked example

Warehouse: `analytics_prod`. All timestamps are UTC. All money columns are
integer minor units (cents), never floats.

### users

```
Grain      one row per registered user
Key        user_id            (enforced)
Source     the application database, replicated hourly
Refresh    hourly, ~15 min behind the application
```

| column | type | notes |
|---|---|---|
| `user_id` | STRING | opaque; do not parse |
| `created_at` | TIMESTAMP | registration time |
| `country_code` | STRING | ISO 3166-1 alpha-2; `ZZ` when the signup form omitted it |
| `plan` | STRING | `free`, `pro`, `team`; null while the user has no active plan |
| `is_internal` | BOOL | true for employees and test accounts |
| `deleted_at` | TIMESTAMP | soft delete; null while the account exists |

Filters: `is_internal = false` and `deleted_at IS NULL`. Reporting examples
that show internal traffic are a bug report, not a finding.

### sessions

```
Grain      one row per session
Key        session_id         (enforced)
Source     the events pipeline
Refresh    daily, complete through 02:00 UTC the previous day
```

| column | type | notes |
|---|---|---|
| `session_id` | STRING | |
| `user_id` | STRING | FK to `users.user_id`; anonymous sessions have no user |
| `started_at` | TIMESTAMP | |
| `ended_at` | TIMESTAMP | null while the session is open or was never closed |
| `device` | STRING | `web`, `ios`, `android` |
| `country_code` | STRING | the country at session start; it can differ from the user's |

Filters: none beyond the join. Exclude `ended_at IS NULL` only when the question
is about completed sessions, and say so in the result.

### events

```
Grain      one row per tracked interaction
Key        event_id           (enforced)
Source     client SDK, landing in the raw layer then transformed
Refresh    hourly
```

| column | type | notes |
|---|---|---|
| `event_id` | STRING | |
| `session_id` | STRING | FK to `sessions.session_id` |
| `user_id` | STRING | FK to `users.user_id`, denormalised at write time |
| `name` | STRING | the event name, e.g. `checkout_completed` |
| `occurred_at` | TIMESTAMP | when the client fired it, not when it arrived |
| `properties` | JSON | event-specific; see the events reference |

Filters: `occurred_at >= TIMESTAMP(...)` for every query, or the result includes
the open tail of the current day and looks like a dip.

### orders

```
Grain      one row per order
Key        order_id           (enforced)
Source     the billing service
Refresh    hourly, ~5 min behind the application
```

| column | type | notes |
|---|---|---|
| `order_id` | STRING | |
| `user_id` | STRING | FK to `users.user_id` |
| `status` | STRING | `pending`, `paid`, `refunded`, `failed`; see below |
| `amount_cents` | INT64 | the order total before tax |
| `refunded_cents` | INT64 | 0 until refunded; partial refunds are a real case |
| `currency` | STRING | ISO 4217; do not sum across currencies |
| `placed_at` | TIMESTAMP | |
| `closed_at` | TIMESTAMP | null while the order is `pending` |

Revenue is `SUM(amount_cents - refunded_cents)` over `status IN ('paid')`. The
`paid` filter is not optional: a `pending` order has an amount and no money
behind it, and an order can move from `paid` to `refunded` later, which is why
`refunded_cents` exists as a column rather than being derived from a status
history.

## Grain and keys

State the grain on every table. It is the one thing that makes an accidental
fan-out visible: joining `events` to `orders` on `user_id` alone multiplies rows,
and the inflated number still looks like a plausible result.

Keys marked "enforced" have a unique constraint. Keys marked "not enforced" are
best-effort; check for duplicates before relying on them, and say in the result
if there were any.

## Join graph

```
users  1 ────< sessions  1 ────< events
  │
  └────1───< orders
```

- `events` and `orders` both carry `user_id`. Join to `users` through whichever
  one the question is about; joining both on `user_id` and filtering on a user
  attribute is correct, joining both to each other is a cartesian fan-out.
- `sessions.country_code` and `users.country_code` are different questions. Say
  which one a report is using.
- There is no path from `events` to `orders`. A question that needs both
  (`did this user hit checkout_completed before buying?`) is answered by
  `events` joined to `orders` on `user_id` with both sides de-duplicated to one
  row per user first.

## Conventions worth stating

- Money is integer minor units.
- Timestamps are UTC; nothing in this warehouse is stored in local time.
- `*_at` columns are TIMESTAMP, never a formatted string.
- Boolean columns are BOOL, not a `0`/`1` integer.
- JSON columns are read with the warehouse's JSON functions, never a regexp.

Each of these has cost someone a wrong number at least once. That is the whole
reason the file exists.

## Cost and freshness notes

- `events` is the largest table. Filter on `occurred_at` before anything else;
  a query without a partition filter scans the whole history and is billed for
  it.
- Daily aggregates exist in `agg_daily_*` tables for anything asked about
  weekly. They are rebuilt at 05:00 UTC and are the right answer for a trend and
  the wrong answer for "yesterday".
- The complete-through time differs per table. A cross-table number computed at
  09:00 has three different freshnesses inside it.

## What does not belong here

- Row counts and cardinalities. They change daily and will be wrong on the page
  before anyone notices.
- Column comments copied from the warehouse's own catalogue. If the warehouse can
  generate them, reference the catalogue instead of duplicating it.
- Business rules that are not about the data's shape. A pricing decision is not
  a schema fact and belongs in a domain reference.
- Anything the reader would have to un-learn. A file that contradicts the
  warehouse's own documentation is worse than no file.
