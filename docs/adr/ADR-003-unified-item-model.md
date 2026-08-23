# ADR-003 — Unified Item Model

**Status**: Accepted (2026-08-21; previously proposed 2026-08-20)
**Date**: 2026-08-21
**Related**: PRD-000, REQ-001, DATA-001

> **Note (2026-08-22, REVIEW-001)**: this decision stands unchanged. Two *implementation*
> details specified in `DATA-001` were corrected without altering any decision here:
> the `content_hash` input no longer includes `url` (it made cross-source matching
> impossible by construction), and `category` is nullable so that non-newsletter items are
> not counted as classification failures. See DATA-001 §"Changes in this revision".

## Context
Implementing the three capabilities independently would produce three unrelated structures —
effectively a postings app, a calendar app and a search app — and resuming after a pause
would require re-learning each. But per PRD-000 the three are one problem seen from three
directions: ingest, time output, content output.

## Decision
Normalise everything into a single `items` table with **shared columns plus an `extra jsonb`
column** for type-specific fields. Newsletters, postings, and later schedules and files all
live here, distinguished by `type`.

Three sub-decisions:

1. **Structure**: shared columns + `extra jsonb`, not a flat table and not per-type side
   tables.
2. **Nesting**: in v1 one email is one Item. A newsletter containing five postings is not
   split. A nullable `parent_id` column is created now so splitting later costs almost
   nothing.
3. **Deduplication**: `UNIQUE (source, source_id)` is enforced. `content_hash` is computed
   and stored but not enforced, so cross-source duplicates can be measured before deciding
   how to handle them.

## Rationale
- Ease of resumption: one structure to understand instead of three.
- The calendar view becomes a query on `due_at IS NOT NULL`; search becomes an index over
  the same table.
- `extra jsonb` avoids the column-sprawl failure mode where a shared table accumulates
  fields that are NULL for most rows.
- Deferring both nesting and cross-source deduplication follows the project principle of
  deciding from data rather than from speculation.
- `raw` preservation allows reparsing when parsing logic improves.

## Trade-offs
| Gained | Given up |
|---|---|
| Structure reused across all three capabilities | More up-front schema thinking |
| Calendar and search come nearly free structurally | `jsonb` fields are not validated by the database |
| Cheap migration path for nesting | Some queries need `jsonb` operators and are less obvious |

## Alternatives rejected
- **Separate tables per capability** — triples the structure and forces search to be built
  separately.
- **Flat single table** — every new type adds columns that are NULL for all other types.
- **Splitting postings out of newsletters in v1** — the need is unproven and the parsing to
  do it reliably does not exist yet.

## Open questions
- **Korean full-text search is not free.** PostgreSQL's default full-text search lacks Korean
  morphological analysis, so the claim that unified search comes at no cost applies to the
  structure only, not to search quality. Evaluate `pg_trgm` / `pg_bigm` at the search
  milestone.
- Concrete vocabularies for `category` and `tags` are finalised at blocks B4 and B20.
