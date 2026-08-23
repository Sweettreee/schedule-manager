# DATA-001 — Data Model and Schema

**Status**: Approved
**Last updated**: 2026-08-22 (revised after REVIEW-001, then after ADR-017)
**Related**: ADR-003, ADR-015, ADR-017, ADR-018, ADR-019, ADR-020

## Changes in revision 3 (ADR-017 scope expansion)

| Change | Source |
|---|---|
| `starts_at`, `all_day` added to `items`; `due_at` meaning unchanged | ADR-019 |
| `reminders` table | ADR-019 |
| `source` gains `PASTE`, `ICS`, `API`; `type` gains `NOTICE` | ADR-018, ADR-017, ADR-021 |
| `blobs`, `files`, `file_versions`, `devices` tables | ADR-020 |
| Trigram indexes for basic search | ADR-017 capability 3 |

**All of these are created in block B2's first migration**, before any row exists — even
though several are not used until B7, B8 and B14. Under forward-only migrations (ADR-015),
adding a column later is cheap but retrofitting *meaning* into rows that never captured it is
not. See ADR-020 §"Why device identity and versions exist in v1".

## Changes in revision 2 (REVIEW-001)

| Change | Why |
|---|---|
| `content_hash` no longer includes `url` | The hash exists to detect the *same posting from two different sources*, and those always have different URLs. Including `url` guaranteed the hash could never do its job |
| `category` is now nullable | `NULL` = "not a classification target". Previously every JOB/CONTEST/RSS row defaulted to `UNCLASSIFIED`, which would have corrupted the evidence block B21 uses to decide whether AI classification is needed |
| New `collector_state` table | FR-13 (incremental collection) needs somewhere to persist the last collection point. There was no such place |
| `usage_events` index added | M-1…M-3 aggregation would otherwise full-scan |
| `CHECK` constraints on enum columns | Enum values existed only as SQL comments. One typo and an item silently disappears from every tab |
| `usage_events.kind` gains `COVERAGE_AUDIT` | PRD-000 §4.1 |

## Design decisions embedded here

| Decision | Choice | Source |
|---|---|---|
| Table strategy | Shared columns + `extra jsonb` for type-specific fields | ADR-003 |
| Nested postings | One email = one Item in v1; `parent_id` reserved | ADR-003 |
| Deduplication | `UNIQUE (source, source_id)` enforced; `content_hash` stored but not enforced | ADR-003 |
| Time | `timestamptz`, stored UTC, rendered KST | ADR-003 |
| Tags | PostgreSQL `text[]` + GIN index | ADR-003 |
| Raw bodies | Stored, deleted after 90 days — in backups too | SEC-001 |
| Migrations | Alembic, **forward-only** | ADR-015 |

## Schema

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- basic search (ADR-017 capability 3)

CREATE TABLE items (
    id           BIGSERIAL PRIMARY KEY,
    source       TEXT        NOT NULL,   -- GMAIL | RSS | ICS | API | PASTE
                                         -- | MANUAL | FILE_SYNC
    source_id    TEXT        NOT NULL,   -- Gmail message id, RSS guid, uuid for pastes
    parent_id    BIGINT      REFERENCES items(id) ON DELETE SET NULL,
    type         TEXT        NOT NULL,   -- NEWSLETTER | JOB | CONTEST | NOTICE
                                         -- | SCHEDULE | FILE | NOTE
    category     TEXT,                   -- NULL = not a classification target (see below)
                                         -- JOB_INFO | CAREER_COLUMN | TECH_COLUMN | UNCLASSIFIED
    title        TEXT        NOT NULL,
    org          TEXT,
    body_text    TEXT,                   -- HTML stripped
    url          TEXT,
    occurred_at  TIMESTAMPTZ NOT NULL,   -- when the message was received / the paste was made
    starts_at    TIMESTAMPTZ,            -- when it begins; NULL for a pure deadline (ADR-019)
    due_at       TIMESTAMPTZ,            -- when it ends or is due  (meaning unchanged)
    all_day      BOOLEAN     NOT NULL DEFAULT false,   -- render as a date, never a time
    tags         TEXT[]      NOT NULL DEFAULT '{}',
    content_hash TEXT        NOT NULL,   -- see "content_hash definition" below
    extra        JSONB       NOT NULL DEFAULT '{}',
    raw          TEXT,                   -- original payload, purged after 90 days
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT items_source_unique UNIQUE (source, source_id),
    CONSTRAINT items_source_check   CHECK (source IN ('GMAIL','RSS','ICS','API','PASTE',
                                                      'MANUAL','FILE_SYNC')),
    CONSTRAINT items_type_check     CHECK (type IN ('NEWSLETTER','JOB','CONTEST','NOTICE',
                                                    'SCHEDULE','FILE','NOTE')),
    CONSTRAINT items_category_check CHECK (category IS NULL OR category IN
                                          ('JOB_INFO','CAREER_COLUMN',
                                           'TECH_COLUMN','UNCLASSIFIED')),
    -- only newsletters are classification targets (REQ-001 §2.3)
    CONSTRAINT items_category_target CHECK (category IS NULL OR type = 'NEWSLETTER'),
    -- an interval cannot end before it starts (ADR-019)
    CONSTRAINT items_interval_order  CHECK (starts_at IS NULL OR due_at IS NULL
                                            OR starts_at <= due_at)
);

CREATE INDEX items_occurred_at_idx  ON items (occurred_at DESC);
CREATE INDEX items_category_idx     ON items (category, occurred_at DESC)
                                     WHERE category IS NOT NULL;
CREATE INDEX items_due_at_idx       ON items (due_at) WHERE due_at IS NOT NULL;
CREATE INDEX items_starts_at_idx    ON items (starts_at) WHERE starts_at IS NOT NULL;
CREATE INDEX items_tags_idx         ON items USING GIN (tags);
CREATE INDEX items_content_hash_idx ON items (content_hash);
CREATE INDEX items_raw_purge_idx    ON items (occurred_at) WHERE raw IS NOT NULL;
-- basic unified search (B8). Korean morphology is a separate problem, see below
CREATE INDEX items_title_trgm_idx   ON items USING GIN (title gin_trgm_ops);
CREATE INDEX items_body_trgm_idx    ON items USING GIN (body_text gin_trgm_ops);

CREATE TABLE collection_runs (
    id            BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    status        TEXT        NOT NULL,  -- RUNNING | SUCCESS | PARTIAL | FAILED
    fetched_count INT         NOT NULL DEFAULT 0,
    saved_count   INT         NOT NULL DEFAULT 0,
    error         TEXT,
    CONSTRAINT collection_runs_status_check
        CHECK (status IN ('RUNNING','SUCCESS','PARTIAL','FAILED'))
);

CREATE INDEX collection_runs_started_idx ON collection_runs (started_at DESC);
-- powers "last successful collection" (FR-12, NFR-6 conditions A and B)
CREATE INDEX collection_runs_success_idx ON collection_runs (started_at DESC)
                                          WHERE status IN ('SUCCESS','PARTIAL');

-- FR-13: where incremental collection remembers how far it got
CREATE TABLE collector_state (
    key        TEXT        PRIMARY KEY,  -- e.g. 'gmail:last_internal_date'
    value      TEXT        NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE usage_events (          -- supports PRD-000 metrics M-1..M-3 (FR-11, FR-14)
    id         BIGSERIAL PRIMARY KEY,
    kind       TEXT        NOT NULL,  -- DASHBOARD_OPEN | MANUAL_ENTRY | COVERAGE_AUDIT
    item_id    BIGINT      REFERENCES items(id) ON DELETE SET NULL,
    note       TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT usage_events_kind_check
        CHECK (kind IN ('DASHBOARD_OPEN','MANUAL_ENTRY','COVERAGE_AUDIT'))
);

CREATE INDEX usage_events_kind_idx ON usage_events (kind, created_at DESC);
-- one DASHBOARD_OPEN per calendar day (KST), so M-3 counts days not page loads
CREATE UNIQUE INDEX usage_events_open_daily_idx
    ON usage_events ((created_at AT TIME ZONE 'Asia/Seoul')::date)
    WHERE kind = 'DASHBOARD_OPEN';

-- ---------------------------------------------------------------- ADR-019
-- Reminders. Absolute fire times, so the sender is an indexed query.

CREATE TABLE reminders (
    id         BIGSERIAL   PRIMARY KEY,
    item_id    BIGINT      NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    fire_at    TIMESTAMPTZ NOT NULL,   -- absolute, computed at creation
    offset_min INT,                    -- what it was derived from, for regeneration
    channel    TEXT        NOT NULL,   -- WEBHOOK | DASHBOARD
    sent_at    TIMESTAMPTZ,            -- NULL = pending
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reminders_channel_check CHECK (channel IN ('WEBHOOK','DASHBOARD'))
);

-- the sender's only query: cheap, and it shrinks as reminders are sent
CREATE INDEX reminders_pending_idx ON reminders (fire_at) WHERE sent_at IS NULL;

-- ---------------------------------------------------------------- ADR-020
-- File synchronisation. Content-addressed: the S3 object key IS the hash.

CREATE TABLE devices (
    id           TEXT        PRIMARY KEY,   -- uuid generated by the agent on first run
    name         TEXT        NOT NULL,      -- 'macbook', 'ipad-web'
    last_seen_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE blobs (
    content_hash  TEXT        PRIMARY KEY,  -- sha256 hex; also the S3 key suffix
    size_bytes    BIGINT      NOT NULL,
    s3_key        TEXT        NOT NULL,
    storage_class TEXT        NOT NULL DEFAULT 'STANDARD',
    ref_count     INT         NOT NULL DEFAULT 0,   -- 0 = garbage-collectable (B19)
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT blobs_size_positive CHECK (size_bytes >= 0),
    CONSTRAINT blobs_refcount_sane CHECK (ref_count >= 0)
);

CREATE INDEX blobs_unreferenced_idx ON blobs (first_seen_at) WHERE ref_count = 0;

CREATE TABLE files (
    id                 BIGSERIAL   PRIMARY KEY,
    path               TEXT        NOT NULL,   -- '수업자료/운영체제/week03.pdf'
    current_version_id BIGINT,                 -- FK added after file_versions exists
    deleted_at         TIMESTAMPTZ,            -- soft delete; blobs are never dropped here
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT files_path_unique UNIQUE (path)
);

CREATE TABLE file_versions (
    id           BIGSERIAL   PRIMARY KEY,
    file_id      BIGINT      NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    content_hash TEXT        NOT NULL REFERENCES blobs(content_hash),
    parent_id    BIGINT      REFERENCES file_versions(id),  -- version chain, for L3 later
    size_bytes   BIGINT      NOT NULL,
    mtime        TIMESTAMPTZ,                 -- the source file's own modification time
    device_id    TEXT        NOT NULL REFERENCES devices(id),
    uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT file_versions_unique UNIQUE (file_id, content_hash)
);

ALTER TABLE files ADD CONSTRAINT files_current_version_fk
    FOREIGN KEY (current_version_id) REFERENCES file_versions(id);

CREATE INDEX file_versions_file_idx   ON file_versions (file_id, uploaded_at DESC);
CREATE INDEX file_versions_device_idx ON file_versions (device_id, uploaded_at DESC);
CREATE INDEX files_path_trgm_idx      ON files USING GIN (path gin_trgm_ops);
```

### Why `parent_id` and `device_id` exist in v1

v1 has one writer (a laptop agent) and resolves no conflicts, so neither column is *used*
yet. They are created now because ADR-015 makes migrations forward-only: adding a column
later is cheap, but a version created today without an ancestor pointer can never be asked
"did these two edits descend from a common ancestor?" — which is the whole question L3 has to
answer. Capturing the lineage costs a few bytes per row and is the difference between L3
being an addition and L3 being a rewrite. See ADR-020.

> `MISSED_ITEM` was removed as a `usage_events.kind`. PRD-000 §4.1 explains why: a missed
> item is by definition one the user never saw, so self-reporting cannot measure it. The
> `COVERAGE_AUDIT` kind replaces it with an external-ground-truth comparison.

## `content_hash` definition

```
content_hash = sha256(
    normalise(title) || '\x1f' ||
    normalise(org)   || '\x1f' ||
    coalesce(to_char(due_at AT TIME ZONE 'UTC', 'YYYY-MM-DD'), '')
)
```

`normalise(s)`:

1. Unicode NFC normalisation (Korean text from different sources arrives in both NFC and NFD;
   macOS filenames and some mail clients produce NFD, and the two are byte-different)
2. Lowercase
3. Strip every character that is not a letter or a digit (removes whitespace, punctuation,
   brackets, and decorations like `[모집]`)
4. `NULL` → empty string

**`url` is deliberately excluded.** The purpose of this hash is to detect the same posting
arriving from two different senders, and in that case the URLs differ by construction —
each source links to its own detail page, usually with its own tracking parameters.
Including `url` would have made the hash exactly as unique as the row itself.

`due_at` is included at **day** granularity because two sources announcing the same contest
agree on the deadline date but not on the time.

The function must be **deterministic and versioned**: if the normalisation rules ever change,
add `content_hash_v INT NOT NULL DEFAULT 1` in a forward migration and recompute, rather than
silently changing the meaning of stored hashes.

## `category` semantics

| `type` | `category` | Meaning |
|---|---|---|
| `NEWSLETTER` | `JOB_INFO` / `CAREER_COLUMN` / `TECH_COLUMN` | Classified successfully by sender rule |
| `NEWSLETTER` | `UNCLASSIFIED` | Classification was attempted and **failed** — this is the population block B21 measures |
| anything else | `NULL` | Not a classification target. Never counted in B21 |

The `items_category_target` CHECK constraint enforces this at the database level so the
distinction cannot decay through a code path that forgets it.

**B21's trigger query** is therefore:

```sql
SELECT count(*) FROM items
WHERE type = 'NEWSLETTER' AND category = 'UNCLASSIFIED';
```

## Enum values and UI labels

| `category` | Korean label shown in UI |
|---|---|
| `JOB_INFO` | 취업정보 (default tab) |
| `CAREER_COLUMN` | 자기계발칼럼 |
| `TECH_COLUMN` | 테크칼럼 |
| `UNCLASSIFIED` | 미분류 |

| `type` | Korean badge |
|---|---|
| `NEWSLETTER` | 뉴스레터 |
| `JOB` | 채용 |
| `CONTEST` | 공모전 |
| `NOTICE` | 공지 (학교 공지사항, RSS) |
| `SCHEDULE` | 일정 (학사일정, 붙여넣기로 등록된 일정) |
| `FILE` | 파일 (동기화된 자료) |
| `NOTE` | reserved, not shown in v1 |

## Time semantics (ADR-019)

`starts_at` and `due_at` form a **half-open interval where both ends are optional**:

| `starts_at` | `due_at` | Meaning | Example |
|---|---|---|---|
| NULL | set | a deadline | 공모전 마감 8/31 18:00 |
| set | set | an interval | 수강신청 8/25 ~ 8/27 |
| set | NULL | a point event | 개강 9/1, 동아리 회의 |
| NULL | NULL | not time-bound | a newsletter |

`all_day = true` means the stored timestamp is **00:00 Asia/Seoul converted to UTC** and the
presentation layer must render a date with no time. Getting this wrong shows *8월 31일* for an
event stated as *9월 1일* — an off-by-one that is invisible until a date is missed, which is
the "silently wrong data" failure class ADR-010 names as this project's worst. It gets a
dedicated unit test.

Deadline proximity (REQ-001 FR-6) is measured against `due_at` where present, falling back to
`starts_at` for point events.

## Files as items

Every synced file also gets an `items` row with `type = 'FILE'`, `source = 'FILE_SYNC'`,
`source_id = files.id`, `title` = the file name, and `extra->>'file_id'` pointing back. This
is what makes unified search (B8) cover files without a second search implementation — the
payoff ADR-003 predicted when it argued for one table.

Enums are English in the database and in code. Korean appears only in the presentation
layer, because the source material is Korean and the user reads Korean.

## Incremental collection (FR-13)

v1 uses the **timestamp-cursor** approach, not the Gmail History API.

```
key   = 'gmail:last_internal_date'
value = the internalDate (epoch ms) of the newest message successfully processed
```

Each run queries `users.messages.list` with `q = after:<epoch_seconds - 3600>` — a one-hour
overlap so that messages delivered out of order are not skipped. Duplicates from the overlap
are absorbed by `ON CONFLICT (source, source_id) DO NOTHING`.

The cursor advances **only on `SUCCESS` or `PARTIAL`**, and only to the newest message that
was actually saved. A `FAILED` run leaves the cursor untouched, so the next run re-reads the
same window.

**Rejected: `users.history.list`.** It is the correct long-term answer and is cheaper, but a
`historyId` expires after roughly a week, which forces a full-resynchronisation fallback path
that has to be written and tested anyway. For a once-a-day collector over one mailbox the
timestamp cursor costs nothing measurable and has one code path instead of two. Revisit if
the interval ever drops below one hour.

## Deduplication semantics

Two distinct kinds of duplicate exist:

1. **Re-collection of the same message** — the same Gmail message fetched twice.
   Prevented by `UNIQUE (source, source_id)`. On conflict: ignore, do not update.
2. **The same posting arriving from two different sources** — e.g. Wevity and Linkareer both
   announce one contest. **Not handled in v1.** `content_hash` is computed and stored so
   that, once real data shows how often this happens, cross-source deduplication can be
   added without a backfill. The measurement query:

```sql
SELECT content_hash, count(*), array_agg(DISTINCT source)
FROM items GROUP BY content_hash HAVING count(*) > 1;
```

## Known limitation — Korean full-text search

ADR-003 claims that unified search is largely free once everything lives in `items`. That is
true of the *structure*, not of *search quality*. PostgreSQL's built-in full-text search does
not perform Korean morphological analysis, so compound-word queries will behave poorly.
Options (`pg_trgm`, `pg_bigm`, an external index) are deferred to the search milestone and
must be evaluated then. This is recorded so the claim is not mistaken for a solved problem.

## Migration policy

Alembic, **forward-only** (ADR-015). Every schema change is a migration; no manual DDL
against any environment, including local. Migrations run automatically at application start
in local development and as an explicit, separate step in deployment.

Every migration must be **backwards compatible with the previous application version**, so
that `kubectl rollout undo` is a safe operation:

1. add a column nullable, deploy
2. backfill, deploy
3. switch reads, deploy
4. drop the old column in a later release

## Retention job

`raw` is set to `NULL` where `occurred_at < now() - interval '90 days'` (SEC-6). The job runs
daily as part of the collector CronJob, before collection, and is idempotent. The partial
index `items_raw_purge_idx` keeps it cheap.

**Backups are subject to the same 90-day rule** — see SEC-001 §"Retention and backups".
