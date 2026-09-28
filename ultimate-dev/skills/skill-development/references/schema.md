# Table Schemas

Reference for the `references/schema.md` file inside a skill: what goes in it, how
to write it, and when a schema belongs there rather than in `SKILL.md`.

> **Provenance.** Authored from this skill's `SKILL.md` and its sibling
> references; no original copy was recovered. The example schemas below are
> reconstructions built to demonstrate the documented shape — use them as a
> pattern, not as a catalogue of what this skill shipped.

## What a schema reference is for

A schema reference documents the shape of the data a skill's scripts read and
write: table definitions, field meanings, key relationships, and the constraints
that are not enforced anywhere else.

The case that motivates it: someone asks a BigQuery skill "how many users logged
in today". Without a schema reference, the skill re-derives the tables, the
columns, and the join keys on every such question, and gets a subtly different
answer each time. With one, the answer is a lookup.

That is the whole argument. A schema reference turns a repeated discovery
problem into a lookup.

## When to write one

Write `references/schema.md` when the skill:

- queries a database, warehouse, or API with a stable shape;
- reads or writes a file format it defines;
- consumes a config format that has more than a couple of fields;
- bridges two systems whose field names differ and the mapping matters.

Do not write one when the format is small enough to fit in `SKILL.md`, or when
it changes often enough that a reference copy will be stale within a release. A
stale schema reference is worse than none: it is confidently wrong, and the
agent that reads it has no way to notice.

## Structure

```markdown
# <System> schema

Last verified: YYYY-MM-DD against <source> (project, version, or URL).

## Tables

### `users`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | string | no | Primary key |
| `email` | string | no | Lowercased on write; do not assume case |
| `created_at` | timestamp | no | UTC |
| `deleted_at` | timestamp | yes | Soft delete; every filter must exclude these |

Indexes: `id` (primary), `created_at`.

## Relationships

- `sessions.user_id` -> `users.id`, many-to-one.
- `orders.customer_id` -> `users.id`. Note the name differs from `user_id` on
  `sessions`; this is not a typo.

## Conventions

- Timestamps are UTC. There is no local-time column anywhere in this schema.
- Money is stored in minor units as an integer. `19.99` is `1999`.
- Soft-deleted rows are present in every table except `audit_log`.

## Queries that have bitten us

- Counting "active users" needs `deleted_at IS NULL`; without it the count is
  roughly 3% high and nobody notices until finance reconciles.
- `sessions` has one row per session, not per user. `COUNT(*)` on it is not a
  user count.
```

## Rules that make a schema reference hold up

1. **Date the schema.** "Verified 2026-03-11 against project `analytics-prod`."
   A reference with no date cannot be stale-checked, and stale-checkability is
   the only thing that keeps it honest.
2. **Write the source, not the summary.** Where did this come from? A project, a
   file, a `DESCRIBE` output, a version tag.
3. **Record the surprising parts.** The notes column is for the things that cost
   someone an afternoon: the soft delete, the unit mismatch, the column that is
   named differently from its neighbours. A field called `email` needs no
   annotation; a field called `email_raw` next to a normalized `email` does.
4. **Record what is absent.** "There is no local-time column anywhere" saves the
   next person from looking.
5. **Do not duplicate `SKILL.md`.** If the skill's procedure already explains the
   field, the reference explains the field. Duplication is how the two drift.

## Keeping it accurate

Schema references rot. Three practices keep them useful:

- **Regenerate where you can.** If the schema is introspectable, the reference
  should be generated and committed, not hand-maintained. A generated file with a
  header saying so is trustworthy in a way a hand-maintained one is not.
- **Fail loudly on a mismatch.** If a documented column is missing at query
  time, say the schema reference is out of date and name the reference. Do not
  silently fall back to a different column — that is how a wrong answer gets
  reported as a right one.
- **Date-stamp the verification in the agent's own output** when it uses the
  reference, so a reader can see how old the assumption was.

## Anti-patterns

| Do not | Because |
| --- | --- |
| Copy the entire API documentation | Ten thousand words nobody reads, and it goes stale the day the vendor ships |
| Document only the tables the skill happens to use | The next question uses a different one, and there is nothing to look up |
| Write the schema in `SKILL.md` | `SKILL.md` is always loaded; a schema is only needed sometimes |
| Omit nullability and units | Both are the questions that get asked after the wrong answer ships |
| Document a column you have not read | A guessed column name in a reference is a claim, and it will be trusted |
