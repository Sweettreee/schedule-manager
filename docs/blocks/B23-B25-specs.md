# Block Specifications — B23, B24, B25 (additional source channels)

**Status**: Approved
**Created**: 2026-08-22
**Related**: ADR-021, SOURCES-001, ADR-019, ADR-020

> **Numbering**: these are numbered in creation order, not execution order
> (`BLOCKS-001` §3). Their position in the sequence is in the roadmap table.

| Block | Runs after | Status |
|---|---|---|
| **B23** — public recruitment APIs | B3 (any time after) | Confirmed |
| **B24** — LMS calendar and notices | B7 | Confirmed, pending B0 findings |
| **B25** — agent-side authenticated fetch | B18 | **Conditional** — gate in §B25 |

---

## B23 — Public recruitment APIs (Worknet, Saramin)

**Goal**: job postings arrive by **query** rather than by waiting for an email.

**Why this is worth a block.** Email subscription delivers what the sender chooses to send,
when they choose to send it. An API answers a question — *cloud, entry level, last 7 days* —
so `FR-3`'s filter rules operate on a result set that was already narrowed correctly. It also
makes part of the coverage audit (PRD-000 §4.1) executable in code.

### Tasks

1. **Obtain keys** (do this first; approval takes time):
   - 공공데이터포털 (data.go.kr) → 한국고용정보원 워크넷 채용정보 API. Register, get the
     service key, note the daily cap.
   - `oapi.saramin.co.kr` → apply, receive the access key. **500 calls/day.** Pricing is not
     published in the guide — confirm at application and record it in `SOURCES-001` §6.
2. **`ApiSource` adapter** behind the `Source` abstraction from B3. HTTP GET → JSON → Item.
   Two implementations, one shared shape.
3. **Query configuration in one place** (FR-2): keyword, region, date window, per source.
   Adding a query must not require a code change.
4. **Cursor per source** in `collector_state` (`worknet:last_seen`, `saramin:last_seen`) so
   collection stays incremental (FR-13).
5. **Quota guard.** Track calls per source per day; refuse to exceed the published cap and
   record it as `PARTIAL`, not `FAILED` — a quota stop is not a fault.
6. **Retry with backoff** on 429/5xx. Two APIs with different error shapes is the point at
   which a shared retry layer earns its place (ADR-021 open question).
7. `type = 'JOB'`, `category` stays `NULL` (only newsletters are classification targets,
   REQ-001 §2.3). `content_hash` per DATA-001 — cross-source duplicates with the email
   sources are **expected and measurable here for the first time**.
8. Add both to the coverage-audit rotation.

### Acceptance criteria

- One collection run pulls Gmail + RSS + two APIs and writes **one** `collection_runs` row.
- A source hitting its quota records `PARTIAL`; the others still complete.
- The second run fetches strictly fewer new items than the first.
- No API key appears in git, logs, or `raw`.
- A posting present in both an email source and an API produces **two rows with the same
  `content_hash`** — verify the measurement query in DATA-001 returns them. This is the first
  real data for the cross-source deduplication decision that ADR-003 deferred.

### Tests (required)

- Integration: recorded JSON fixture → Item → database; re-run deduplicated.
- Unit: quota guard — the 501st call in a day does not fire.
- Unit: backoff on a stubbed 429.
- **Never call the real APIs in tests** (ADR-010's rule, extended from Gmail to every source).

### Cost

**$0.** Both APIs are free at this volume. The quota guard exists because an accidental loop
would get the key suspended, not because it would cost money.

### Not in this block

Scraping anything. Saramin's website is explicitly excluded now that its API is used
(SOURCES-001 §7).

---

## B24 — LMS calendar and notices

**Goal**: 과제·시험 마감이 자동으로 일정 뷰에 들어온다 — **with no password stored anywhere.**

Depends on B7 (the time view) — deadlines with nowhere to display them are not a deliverable.
Depends on B0 having found the URLs.

### Tasks

1. **ICS adapter.** Fetch the personal iCalendar URL, parse with a standard library
   (`icalendar` / `ics`), map to Items:

   | iCalendar | Item column |
   |---|---|
   | `DTSTART` | `starts_at` |
   | `DTEND` / `DUE` | `due_at` |
   | `VALUE=DATE` (no time) | `all_day = true` |
   | `SUMMARY` | `title` |
   | `UID` | `source_id` |
   | `DESCRIPTION` | `body_text` |

   The mapping is near-direct because `ADR-019`'s model was derived from the same standard.
2. `source = 'ICS'`, `type = 'SCHEDULE'`. The enum value already exists — B2 created it
   (DATA-001), so **no migration is needed here.** That is the forward-only policy paying off.
3. **Recurring events**: v1 does not support recurrence (ADR-019). Expand `RRULE` occurrences
   **only within the next 90 days** and mark them `extra->>'from_rrule' = true` so a future
   recurrence migration can identify and replace them. Do not store them as if hand-entered.
4. **Forum RSS adapter** — reuse B3's RSS source. `type = 'NOTICE'`.
5. **The ICS URL is a secret** (SEC-13 pattern): anyone holding it can read the calendar.
   Store it like any other secret; never log it.
6. Reminders (B7) apply automatically to imported deadlines — no new code.

### Acceptance criteria

- An assignment deadline visible in the LMS appears in the week view with the same date.
- **An all-day LMS event renders on the correct KST date** — the off-by-one from ADR-019 is
  the specific failure to check here, and it is invisible until a date is missed.
- Re-running collection creates no duplicates (`UID` → `source_id`).
- An event deleted in the LMS is handled explicitly — decide and document whether it is
  removed or marked stale. **Do not leave it undefined**: a deadline that no longer exists but
  still alerts is noise, and one that silently vanishes is worse.
- No password is stored anywhere in the system.

### Tests (required)

- Integration: ICS fixture → Items with correct `starts_at`/`due_at`/`all_day`.
- Unit: an all-day event created in KST round-trips through UTC to the same calendar date.
- Unit: a timed event with a `TZID` other than Asia/Seoul converts correctly.

### If B0 found no ICS export

Then this block builds the ICS adapter against **any** public calendar feed as a proof, the
LMS deadlines come through the paste channel (B6), and B25's gate condition 3 is satisfied for
deadlines. **Record the substitution in `STATUS.md` — do not silently skip the block.**

---

## B25 — Agent-side authenticated fetch — **CONDITIONAL**

**Goal**: course material files arrive in the sync folder without being downloaded by hand.

> **This block does not start until all five gate conditions are recorded as met.**
> If any fails, the block is closed as "not justified" and that is a successful outcome, not
> a failure — write it up either way, like B21.

### Gate (SOURCES-001 §4, ADR-021 §3)

| # | Condition | Evidence required |
|---|---|---|
| 1 | Terms contain no prohibition on automated access | The clause, quoted, with a date |
| 2 | Own account, **read-only** | Design review: no submit/modify/delete code path exists |
| 3 | Rungs 1–5 insufficient for **files specifically** | B0 and B24 findings recorded in SOURCES-001 |
| 4 | The friction is **measured** | `usage_events` shows manual download as a recurring weekly cost |
| 5 | Failure is loud | Design: zero results ⇒ error |

Condition 4 is the one most likely to fail, and that is deliberate. If downloading files by
hand turns out to cost five minutes a week, this block trades a university credential for
75 minutes a semester. **State the trade explicitly in the write-up before building it.**

### Tasks (only after the gate passes)

1. Credentials in the **OS keychain** (macOS Keychain via `keyring`). **Never in a file, never
   in the database, never transmitted to the server.**
2. Session login inside the **agent** (B18). If the LMS is Moodle, prefer its web-service
   token flow over form login even if only partly enabled.
3. Download new course files into the **already-watched sync folder**. Nothing else is needed
   — the existing L1 agent uploads them (ADR-020). **No new pipeline.**
4. **Loud failure**: zero files found, or a login page returned where content was expected,
   is an error that alerts. Never a silent success.
5. Rate-limit politely: one login per run, sequential downloads, no parallel hammering.
6. A **kill switch**: one config flag disables the whole feature without touching the agent's
   other duties.

### Acceptance criteria

- The server holds no university credential — verified by grepping the database and the
  cluster secrets.
- Killing network access mid-download leaves no partial file in the sync folder.
- A deliberately wrong password produces a clear error, not an empty run reported as success.
- The kill switch works.

### Tests (required)

- Unit: the parser against a **saved, anonymised** page fixture. Never against the live LMS.
- Unit: empty result ⇒ raises, does not return `[]`.

### Cost

$0 in money. The real cost is a stored university credential and per-semester maintenance —
which is what the gate exists to price.
