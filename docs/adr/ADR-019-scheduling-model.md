# ADR-019 — Scheduling Model: Interval Semantics, and Reminders as Rows

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-003, ADR-012, ADR-015, ADR-017, DATA-001, REQ-001

## Context

`ADR-017` brings the time view into v1. `ADR-003` reserved `type = 'SCHEDULE'` and a `due_at`
column for exactly this, and that foresight holds — but `due_at` alone cannot express what the
highest-priority sources actually contain:

| Real example | Can `due_at` alone express it? |
|---|---|
| "공모전 마감 8/31 18:00" | **Yes.** A single instant |
| "수강신청 8/25 ~ 8/27" | **No.** There is no start |
| "개강 9/1" (all day) | **No.** Is that midnight? 09:00? A timestamp implies a time nobody stated |
| "시험기간 12/15 ~ 12/19" | **No.** Interval, all-day |
| "매주 화 10:00 자료구조" | **No.** Recurrence |
| "마감 3일 전에 알려줘" | **No.** No place to store it |

Because migrations are forward-only (`ADR-015`), the cost of getting this wrong is asymmetric:
**adding a column later is easy; changing what an existing column means is not.** Deciding
before block B2 writes the first migration is the cheap moment. Deciding after there are rows
means a backfill whose correctness cannot be verified, because the missing information was
never captured.

There is also a boundary question. `ADR-003` chose "shared columns plus `extra jsonb`", with
the rule that `extra` holds type-specific fields. Which of these belong in shared columns?

## Decision

### 1. Interval semantics: `starts_at` is added; `due_at` keeps its meaning

```sql
starts_at  TIMESTAMPTZ,                          -- when it begins; NULL for a pure deadline
due_at     TIMESTAMPTZ,                          -- when it ends or is due (unchanged)
all_day    BOOLEAN NOT NULL DEFAULT false
```

The pair is interpreted as a **half-open interval where both ends are optional**:

| `starts_at` | `due_at` | Meaning | Example |
|---|---|---|---|
| NULL | set | A deadline | 공모전 마감 |
| set | set | An interval | 수강신청 기간 |
| set | NULL | A point event | 개강, 회의 |
| NULL | NULL | Not time-bound | a newsletter |

`due_at` is **not** redefined, so every existing rule, index and query in `DATA-001` and
`REQ-001` continues to mean what it meant. This is the whole reason for adding `starts_at`
rather than reinterpreting `due_at` as "end".

### 2. `all_day` is a flag, and all-day values are stored at KST midnight

An all-day event still stores a `timestamptz`, anchored to **00:00 Asia/Seoul** converted to
UTC, with `all_day = true` telling the presentation layer to render a date and never a time.

### 3. Reminders are rows in their own table, not a column

```sql
CREATE TABLE reminders (
    id         BIGSERIAL PRIMARY KEY,
    item_id    BIGINT      NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    fire_at    TIMESTAMPTZ NOT NULL,   -- absolute, computed at creation
    offset_min INT,                    -- what it was derived from, for regeneration
    channel    TEXT        NOT NULL,   -- WEBHOOK | DASHBOARD
    sent_at    TIMESTAMPTZ,            -- NULL = pending
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX reminders_pending_idx ON reminders (fire_at) WHERE sent_at IS NULL;
```

`fire_at` is absolute. If `due_at` changes, pending reminders for that item are regenerated
from `offset_min`.

### 4. Recurrence is deferred, and the schema says so

v1 does **not** support recurring events. A repeating class timetable is entered as individual
items, or pasted once per semester (ADR-018). When recurrence is needed, it arrives as a
nullable `rrule TEXT` column holding an RFC 5545 `RRULE` string plus an expansion job — an
additive migration.

**Rejected explicitly: expanding a semester's classes into sixteen rows at entry time.** It
appears simpler and is a trap — editing "move the Tuesday class an hour later" then means
finding and updating sixteen rows, and there is no record that they were ever one thing.

### 5. Where each field lives

| Field | Location | Why |
|---|---|---|
| `starts_at`, `due_at`, `all_day` | **shared columns** | The calendar view filters and sorts on them for every type. A `jsonb` extraction cannot use a btree index efficiently |
| reminders | **own table** | "Which reminders are due now?" is a query over a partial index. As `jsonb` inside `items` it would be a full scan |
| `rrule` (later) | shared column | Same reason as the dates |
| location, attendees, colour, source-specific junk | `extra` | Never filtered on; ADR-003's rule applies |

## Rationale

- **`due_at`'s meaning is preserved**, so this is purely additive and nothing already written
  needs re-reading. Under a forward-only migration policy that is the property that matters.
- **All-day events are a real correctness issue, not a nicety.** Storing "개강 9/1" as
  `2026-09-01T00:00:00+09:00` and rendering it in UTC shows *8월 31일* — an off-by-one that is
  invisible until someone misses a date. `ADR-010` names silently-wrong data as this project's
  worst failure class; a timezone-shifted deadline is exactly that.
- **Reminders as rows make the sender trivial and correct.** A job asks
  `WHERE sent_at IS NULL AND fire_at <= now()`, sends, and stamps `sent_at` — idempotent, safe
  to re-run, and cheap on a partial index. Storing offsets on the item instead would mean
  recomputing every item's reminder times on every tick.
- **The reminder sender reuses ADR-012's webhook path.** The alerting channel already exists
  by design, so the marginal cost of "까먹지 않게 알려주는 기능" — the stated core of the
  schedule capability — is close to zero.
- **Deferring recurrence is consistent with the rest of the project**: build against known
  need, leave the migration cheap. The chosen sources (학사일정, 학교 공지) contain almost no
  recurrence; a class timetable does, and it is not in v1.

## Trade-offs

| Gained | Given up |
|---|---|
| Intervals, deadlines, point events and all-day dates are all representable, correctly | Three more columns and one more table before a single row exists |
| `due_at` semantics unchanged — no existing query or index is invalidated | Two nullable date columns mean every consumer must handle four combinations |
| Reminder delivery is an idempotent indexed query | Reminders must be regenerated when `due_at` moves — a rule that must not be forgotten |
| Recurrence stays a cheap future migration | The class timetable is manual until then |
| All-day handled at the boundary, so the off-by-one bug cannot occur | Presentation must consult `all_day` everywhere it renders a date |

## Alternatives rejected

- **Keep only `due_at` and put the start in `extra`.** Minimal change. Rejected: the calendar
  view's primary query is "everything overlapping this week", which needs an indexable start.
  A `jsonb` field cannot serve that well, and this is the single most-used query of the
  capability.
- **Rename `due_at` to `ends_at` and add `starts_at`.** Cleaner naming. Rejected: it rewrites
  the meaning of a column referenced across `DATA-001`, `REQ-001` FR-6, the deadline
  highlighting rules and two indexes, for a cosmetic gain — precisely the kind of change
  ADR-015 exists to discourage.
- **A separate `events` table for schedule items.** Conventional, and it would keep `items`
  clean. Rejected: it is the "separate tables per capability" option `ADR-003` already
  rejected, and it would split the unified search (ADR-017 capability 3) across two tables.
- **Store all-day events as a `DATE` column alongside the timestamps.** Type-correct and
  unambiguous. Rejected: it doubles the number of date columns and every query would need to
  coalesce across both. The `all_day` flag carries the same information at a fraction of the
  query complexity.
- **Reminders as an array column on `items`.** Fewer tables. Rejected: no clean way to record
  "already sent" per reminder, and finding due reminders becomes a scan.
- **Full RFC 5545 support in v1** (RRULE, EXDATE, timezones per event). Correct and complete.
  Rejected as premature: the v1 sources barely recur, and recurrence expansion is a genuinely
  large piece of work best done when there is something to test it against.

## Consequences

- `DATA-001` gains `starts_at`, `all_day`, the `reminders` table, `source = 'PASTE'`,
  `type = 'NOTICE'`, and index changes.
- The deadline-proximity logic in `REQ-001` FR-6 is defined against `due_at` where present,
  falling back to `starts_at` for point events.
- Block B7 (time view and reminders) implements this; block B2 creates the columns in the
  first migration so no backfill is ever needed.
- Timezone handling gets a dedicated unit test per `ADR-010`: an all-day event created in KST
  must render as the same calendar date after a UTC round trip.
