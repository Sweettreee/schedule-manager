# Block Specifications — B0 to B8 (Foundation and the Application)

**Last updated**: 2026-08-22 (rewritten after ADR-017; supersedes `B0-B5-specs.md`)

Detailed enough for Claude Code to start from. Infrastructure blocks are in
`B10-B11-specs.md`; blocks from B12 onward are specified when reached.

---

## B0 — Foundation

**Goal**: mail starts accumulating, the school's channels are known, and the repository exists.

**B0 is started, not finished.** Mail keeps arriving for the whole life of the project, and
that accumulation is the input to B4 and B20. Start it today; do not wait for anything.

**Tasks**

1. Create a dedicated Gmail account for collection. Enable 2FA and set recovery options —
   if this account is lost, the entire pipeline is lost.
2. Subscribe from that address to: Wevity (Web/Mobile/IT, Game/SW, Science/Engineering,
   Employment/Startup categories), JobKorea job alerts, and Linkareer alerts if they exist.
3. **Investigate every source's channel** using the checklist in `SOURCES-001` §3, and fill
   in the matrix. This is now the largest part of B0, because ADR-021 makes channel choice a
   decision rather than an assumption.
   - Work **top-down the ladder**: official API → tokenised feed → public feed → email →
     paste. Stop at the first hit and record it.
   - **LMS, in this exact order** (`SOURCES-001` §3): calendar iCal export URL → forum RSS →
     Moodle Web Services. Stop at the first that works. If web services turn out to be
     enabled for students, say so loudly — it supersedes ADR-021's rung 6 entirely.
   - **Apply for the API keys now**, because approval takes time: 공공데이터포털 (Worknet) and
     `oapi.saramin.co.kr`. Record Saramin's pricing answer — the guide does not publish it.
   - Check `robots.txt` and terms while you are there (NFR-7), so B3 and B23 do not have to.
   - **"There is nothing, use paste" is a valid and complete answer** — but it must be
     *recorded*, because a recorded "none" is what licenses moving down the ladder.
4. Initialise the repository with this document set, `.gitignore`, `CLAUDE.md`, `README.md`.
   Enable GitHub **secret scanning with push protection** (SEC-14).
5. Record in `STATUS.md`: subscriptions and their dates, and the school-channel findings.

**Acceptance criteria**
- At least three sources are subscribed and at least one message has arrived.
- `SOURCES-001` §2 has a status for **every** source, and §3's checklist is answered for each.
- The two API key applications are submitted (approval may still be pending).
- The LMS question has a written answer, whatever it is.
- `git log` shows the initial documentation commit.

**Not in this block**: any code.

---

## B1 — Gmail OAuth and reading mail locally

**Goal**: message subjects from the collection account print in the terminal.

**Tasks**
1. Create a Google Cloud project, enable the Gmail API.
2. Configure the OAuth consent screen. **Set publishing status to "In production"** — in
   Testing status refresh tokens expire after seven days (ADR-007).
3. Scope: `gmail.readonly` only.
4. Desktop OAuth flow; persist the refresh token to `api/.secrets/gmail_token.json`
   (gitignored).
5. A CLI command listing the most recent N messages: date, sender, subject.

**Timebox — decided in advance (ADR-007)**

> **2 working days.** If publishing to production is not working by then, execute the
> IMAP + app-password fallback, record it as a new ADR amending ADR-007, and continue.
> The project does not stall on a Google policy.

**Acceptance criteria**
- Running the command twice on different days works without re-authentication.
- No token, client secret or client id is present in git.

**Tests**: smoke run only; this block is exploratory by nature (ADR-010).

---

## B2 — Message to Item, storage, deduplication, incremental collection

**Goal**: normalised rows accumulate in PostgreSQL, and repeated runs get cheaper.

**Tasks**
1. `docker-compose.yml` with PostgreSQL 16 **and MinIO** (MinIO is unused until B14, but
   having it in the local stack from the start means B14 is not also a docker-compose block).
2. Alembic migration creating **the full schema from `DATA-001`**: `items` (including
   `starts_at`, `all_day`), `collection_runs`, `collector_state`, `usage_events`,
   `reminders`, `devices`, `blobs`, `files`, `file_versions` — every CHECK constraint and
   index included.
   - Yes, most of these are unused until B7 and B14. Create them now anyway: migrations are
     forward-only (ADR-015) and ADR-020 explains why lineage columns must exist from the
     first row rather than be retrofitted.
   - `downgrade()` raises `NotImplementedError`.
3. Converter: Gmail message → Item. Strip HTML to `body_text`, keep the original in `raw`,
   set `occurred_at` from the message date in UTC, compute `content_hash` per `DATA-001`
   (NFC → lowercase → strip non-alphanumeric; **`url` is not part of the hash**).
4. **Incremental collection (FR-13)**: read `collector_state['gmail:last_internal_date']`,
   query with `q=after:<cursor - 1 hour>`, advance the cursor only on `SUCCESS`/`PARTIAL`.
5. Insert with `ON CONFLICT (source, source_id) DO NOTHING`.
6. Write a `collection_runs` row for every run, including `PARTIAL`.
7. Daily `raw` purge for rows older than 90 days (SEC-6), before collection, idempotent.
8. Anonymised fixtures per SEC-001; originals stay in `fixtures/raw/` (gitignored).

**Acceptance criteria**
- Running collection twice adds no duplicate rows.
- **The second run fetches strictly fewer messages than the first.**
- A run failing on one message stores the others and records `PARTIAL`.
- A fully failed run leaves the cursor unchanged.
- All timestamps stored in UTC.

**Tests (required)**
- Integration: fixture → Item → database; re-run ignored as duplicate.
- Integration: `occurred_at` round-trips and renders as KST.
- Integration: incremental cursor — fetch count drops, no rows lost, `FAILED` does not advance.
- Unit: HTML-to-text including Korean text and encoding edge cases.
- Unit: `content_hash` — two records differing only by `url` hash the same; NFC and NFD
  spellings of one Korean title hash the same.
- Unit: **all-day timezone** — an all-day item created as 9월 1일 KST renders as 9월 1일 after
  a UTC round trip, not 8월 31일 (ADR-019).

---

## B3 — RSS collector (school notices)

**Goal**: school notices land in the same table as mail, through the same pipeline.

This block exists early because school notices are a **core source** under ADR-017, and
because it is the cheapest possible proof that ADR-003's one-table design extends. If adding a
second source type needs more than a new adapter, ADR-003 was wrong and now is when to find
out.

**Tasks**
1. A `Source` abstraction with two implementations: `GmailSource` (refactored from B2) and
   `RssSource`. Both yield Items; everything downstream is shared.
2. RSS/Atom parsing; `source_id` = the entry guid; `type = 'NOTICE'`; `category` stays NULL.
3. `collector_state['rss:<feed>:last_seen']` for incremental behaviour.
4. Feeds configured in one place, addable without a code change (FR-2).
5. **If B0 found no feed**, this block instead implements the RSS adapter against any public
   feed as a proof, and the school's notices come through the paste channel in B6. Record the
   substitution in `STATUS.md` — do not silently skip the block.

**Acceptance criteria**
- One collection run pulls from Gmail and RSS, writing one `collection_runs` row covering both.
- A feed failing while Gmail succeeds records `PARTIAL`, not `FAILED`.
- Adding a second feed requires editing configuration only.

**Tests (required)**
- Integration: RSS fixture → Item → database; re-run deduplicated.
- Unit: a malformed entry is skipped without killing the run.

---

## B4 — Classification and filter rules (TDD)

**Goal**: items appear under the correct tab.

**Entry condition**: at least **30 collected messages from at least 3 distinct senders.**
Rules written against five samples are guesses. If unmet, work the infra track (B9).

**Tasks**
1. Sender-address rules producing `category`. **Applied only to `type = 'NEWSLETTER'`**;
   every other type keeps `category = NULL` (REQ-001 §2.3).
2. Filter flags `is_cs`, `is_ai`, `is_cloud` from keyword rules, stored in `extra`.
3. Apply REQ-001 §2.2: include when `is_cs`; exclude when `is_ai AND NOT is_cs`; sort
   `is_cloud` to the top.
4. Unmatched newsletters become `UNCLASSIFIED`, queryable for B21.

**Acceptance criteria**
- Every rule in REQ-001 §2.2 and §2.3 has at least one passing test.
- Unmatched **newsletters** are counted; non-newsletter items are not.

**Tests (required, test-first)**
Write the failing test before the rule. Include the documented negative cases (an AI ethics
essay contest and an AI marketing contest must both be excluded) and one case asserting a
`type='JOB'` item ends with `category IS NULL`.

---

## B5 — API and dashboard

**Goal**: a screen worth opening every day.

**Tasks**
1. FastAPI: list items with tab, sort and date-range filters; toggle saved; record usage
   events; report last successful collection **and whether it is stale**.
2. Next.js per REQ-001 §2.1: four tabs with Korean labels, a `type` badge per row, deadline
   highlighting (FR-6), saved items (FR-7), a persistent "마지막 수집" indicator (FR-12) and a
   **red staleness banner** past interval × 1.5.
3. Usage recording (FR-11): dashboard opens (one per KST day), manual-entry count.
4. Coverage-audit entry screen (FR-14).
5. Collection interval setting, 1–24 hours, default 24 (FR-10).

**Acceptance criteria**
- List screen p95 under 2 seconds with **10,000 seeded rows** (NFR-2).
- With the collection timestamp artificially aged, the banner appears.
- Opening the dashboard records exactly one usage event per KST day across several loads.

**Tests (required)**
- Integration: list API correct for each tab, sort order and date range.
- Integration: staleness flag flips at the interval × 1.5 boundary.
- Unit: deadline proximity across timezone boundaries.

> **The infra track unblocks here.** B9 can start as soon as B5 merges.

---

## B6 — Paste and screenshot ingest

**Goal**: 카톡 메시지나 학사일정을 붙여넣으면 일정으로 등록된다.

Implements ADR-018. This is the channel for every source with no API.

**Tasks**
1. An input accepting **pasted text or a dropped image**.
2. **Rules first where they are cheap**: a blob matching the KakaoTalk export line format is
   parsed by rule; only free-form content reaches the model.
3. LLM extraction returning a **strict schema**: `title`, `org`, `starts_at`, `due_at`,
   `all_day`, `type`, `tags`, plus a per-field `confidence`. Images go to a vision-capable
   model — **no separate OCR stack** (ARCH-001 has no memory for one).
4. **A confirmation form. Nothing is written to `items` without a click.** Low-confidence
   fields are visually flagged.
5. Save as `source = 'PASTE'`, `source_id` = a generated uuid, `raw` = the original paste
   (90-day purge applies).
6. **Monthly call cap, default 300, enforced in the API** (FR-17). On reaching it, extraction
   disables itself and alerts. This is a code-level guard, not an alarm — the realistic
   failure is a retry loop, and an alarm does not stop one.
7. Provider selection: evaluate against **real Korean date expressions** — "담주 화욜 3시",
   "이번주 금 저녁", "25일까지", "8/25~8/27". Record the provider, the price, and its
   **no-training-on-input commitment** in the block write-up (SEC-15).

**Acceptance criteria**
- Pasting a KakaoTalk-style message produces a correctly dated draft for confirmation.
- Pasting a semester's academic calendar produces multiple drafts.
- A screenshot of the same content produces an equivalent result.
- Rejecting the form writes nothing.
- Simulating 301 calls in a month disables extraction and fires an alert.
- No raw paste appears in any log, metric or trace (grep the logs to prove it).

**Tests (required)**
- Unit: the KakaoTalk export parser, on an anonymised fixture.
- Unit: the cap — call 301 times against a stubbed extractor, assert disablement.
- Integration: confirmed draft → `items` row with correct `starts_at`/`due_at`/`all_day`.
- **Extraction accuracy is not unit-tested against the live model.** Wrong extractions become
  fixtures under ADR-010's bug rule as they are found.

---

## B7 — Time view and reminders

**Goal**: 마감이 다가오면 알림이 온다. This is the highest-priority capability's payoff.

Implements ADR-019.

**Tasks**
1. Week and month views over items with `starts_at` or `due_at`. Intervals render as spans;
   all-day items render as dates with **no time shown**.
2. Reminder creation: pick offsets (e.g. 3 days, 1 day, 2 hours before). Store absolute
   `fire_at` rows plus `offset_min`.
3. **Regenerate pending reminders when an item's `due_at` changes.** Easy to forget; it is an
   acceptance criterion for that reason.
4. A sender job — part of the existing collector CronJob — running
   `WHERE sent_at IS NULL AND fire_at <= now()`, delivering, then stamping `sent_at`.
   **Reuses the ADR-012 Discord webhook path**; no new alerting infrastructure.
5. Dashboard reminders in-page as well as by webhook.

**Acceptance criteria**
- An item with a deadline three days out, given a "1 day before" reminder, fires once and
  only once — verified by running the sender twice.
- Moving the deadline regenerates the pending reminder.
- Deleting an item deletes its pending reminders (`ON DELETE CASCADE`).
- An all-day event created as 9월 1일 shows as 9월 1일 in the month view.

**Tests (required)**
- Integration: sender idempotence — two consecutive runs send once.
- Integration: `due_at` change regenerates pending, leaves sent rows alone.
- Unit: interval overlap query returns items spanning a week boundary.

---

## B8 — Basic unified search

**Goal**: 한 검색창에서 메일·공지·일정·파일이 전부 찾힌다.

**Tasks**
1. A search endpoint over `items` using `pg_trgm` similarity on `title` and `body_text`, plus
   exact matching on `tags` and `org`.
2. One result list across every `type`, with a type badge and a relevance ordering.
3. Filters: type, date range, source.
4. Files are included automatically because every file has an `items` row (DATA-001
   §"Files as items") — this block should need **no file-specific code**, and if it does,
   that is a finding worth recording.

**Acceptance criteria**
- A Korean substring query returns matches from at least two different `type` values.
- Search p95 under 2 seconds with 10,000 seeded rows.
- **The known limitation is documented in the UI**, not just in `DATA-001`: compound-word
  Korean queries behave poorly, and B22 addresses it.

**Tests (required)**
- Integration: a seeded corpus returns expected hits for three representative queries.
- Integration: results include a `type='FILE'` item.

> `DATA-001` §"Known limitation" already states that unified search is free *structurally* but
> not in *quality*. This block delivers the structure. Do not let it be mistaken for the
> finished capability — that is B22.
