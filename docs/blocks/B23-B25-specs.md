# Block Specifications — B23, B24, B25 (additional source channels)

**Status**: Approved
**Created**: 2026-08-22
**Last updated**: 2026-08-25 (**B24 reduced to ICS only** — B0 established the LMS has no forum
RSS, so the RSS adapter is removed from the project entirely. Earlier the same day: three stale
cross-references corrected; B24's RSS dependency fixed)
**Related**: ADR-021, ADR-022, **ADR-023**, SOURCES-001, ADR-019, ADR-020

> **Numbering**: these are numbered in creation order, not execution order
> (`BLOCKS-001` §3). Their position in the sequence is in the roadmap table.

| Block | Runs after | Status |
|---|---|---|
| **B23** — public recruitment APIs | B3 (any time after) | Confirmed |
| **B24** — LMS calendar | B7 | **Confirmed 2026-08-24 (ICS).** **Scope reduced 2026-08-25: ICS only** — the LMS does not support forum RSS |
| **B25** — agent-side authenticated fetch | B18 | **Conditional** — gate in §B25 |

> **Rung naming (ADR-022 rev. 2).** Rungs are named, not numbered (`SOURCES-001` §1). The gate
> these specs call "rung 6" is the **`AGENT`** rung, `SOURCES-001` §5; its five conditions are
> unchanged. The Wevity scraper is **B26**, a separate spec file.

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
     published in the guide — confirm at application and record it in `SOURCES-001` §7 (the quota and
     key register; §6 is the procedure for adding a source).
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

- One collection run pulls **Gmail + the school-board scraper + two APIs** and writes **one**
  `collection_runs` row. *(Corrected 2026-08-25: this said "Gmail + RSS". ADR-022 moved the RSS
  adapter to B24, which runs after B7 — so at B23 there is no RSS source, and the criterion as
  written was unsatisfiable.)*
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

**Scraping.** Under ADR-022 scraping is permitted on the `SCRAPE/MAIL` rung, but not here:
**Saramin's website stays excluded** because this block holds its official API key, and scraping a site whose API you
already hold is indefensible (`SOURCES-001` §8). The Wevity scraper is **B26**.
JobKorea stays email-only on decided case law.

---

## B24 — LMS calendar

**Goal**: 과제·시험 마감이 자동으로 일정 뷰에 들어온다 — **with no password stored anywhere.**

**Scope reduced 2026-08-25.** This block was "LMS calendar *and notices*". The notices half
depended on a Moodle forum RSS feed that **this LMS does not provide** (`SOURCES-001` §2), so
the block is **the ICS adapter and nothing else**. LMS course notices are `PASTE` (B6).

Depends on B7 (the time view) — deadlines with nowhere to display them are not a deliverable.

**B0 findings, 2026-08-24 (`SOURCES-001` §2, §2.1):** the LMS is **Moodle core under a
coursemos / UBION wrapper**. The Calendar nav item is hidden by the theme but the route is
live. The export feed is confirmed working:

```
https://lms.chungbuk.ac.kr/calendar/export_execute.php
    ?userid=<userid>&authtoken=<token>&preset_what=all&preset_time=recentupcoming
```

**No cookie or header is required — the `authtoken` parameter is the entire credential.**

### 0. Two non-negotiables before any other task

**(a) `preset_time=recentupcoming` is the only permitted value. `monthnow` is prohibited.**

`monthnow` is fixed to the current calendar month. It does not error — it returns HTTP 200, a
well-formed non-empty `.ics` that parses cleanly, **while next month's deadlines are simply
absent**. `NFR-17` does not fire, because the result is not empty; it is truncated. The
dashboard looks healthy while the project's highest-priority capability silently fails.

Required, per `NFR-19`:

1. **The Secret holds base URL, `userid` and `authtoken` as three separate values** — never the
   assembled URL. `preset_what` and `preset_time` are assembled in code, because a parameter
   buried inside a secret is a parameter **no test can assert**.
2. **`preset_time` is a constant in the adapter, not a configuration setting.** There is no
   legitimate second value, so offering the choice only creates a way to get it wrong.
3. **Startup validation**: if the assembled URL does not carry `preset_time=recentupcoming`, the
   adapter **refuses to run.** A truncated feed is worse than no feed — no feed is visible, a
   truncated one is not.
4. **A unit test asserts the assembled URL contains `preset_time=recentupcoming`** and never
   `monthnow`.
5. **`max(DTSTART)` is recorded per run.** Not a hard failure — a month with genuinely no
   deadlines is legitimate — but a collapse of the horizon back to the current month must be
   observable.

**(b) The token is a credential and must be masked everywhere.**

See `docs/incidents/2026-08-24-lms-token-near-miss.md`. **The token in use at the time of
writing is pending rotation and must be rotated before this block wires it into anything.**

- `authtoken` is **masked in every log line, exception message and traceback.** A fetch failure
  that prints the URL has written the credential into the log — this is a code requirement, not
  a guideline.
- The ICS URL is **never rendered in the dashboard**, including in an error banner.
- Rotate again at the end of the block if the token was used during development.

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
2. `source = 'ICS'`, `type = 'SCHEDULE'`. Both enum values are created by **B2's first
   migration** (DATA-001), so **no migration is needed here** — provided B2 actually shipped the
   full enum, which now also includes `'SCRAPE'`. That is the forward-only policy paying off, and
   it only pays off if B2 creates every value the roadmap already knows about.
3. **Recurring events**: v1 does not support recurrence (ADR-019). Expand `RRULE` occurrences
   **only within the next 90 days** and mark them `extra->>'from_rrule' = true` so a future
   recurrence migration can identify and replace them. Do not store them as if hand-entered.
4. **No forum RSS adapter. Removed from this block on 2026-08-25.** This block used to build
   "the first and only RSS adapter in the project". **B0 established that the LMS does not
   support forum RSS**, so there is no source for it — and since no other RSS source exists
   anywhere in this project either (`SOURCES-001` §1.1), **no RSS adapter is written at all.**
   LMS course notices fall to `PASTE` (B6). `source = 'RSS'` stays in the DATA-001 enum unused
   and on purpose, because migrations are forward-only (DATA-001, ADR-015).
5. **The ICS URL is a secret** (SEC-13 pattern): anyone holding it can read the calendar.
   Store it per §0(b); never log it.
6. Reminders (B7) apply automatically to imported deadlines — no new code.
7. **The forum RSS question is closed** (`SOURCES-001` §2, 2026-08-25): the LMS does not
   support it, and LMS course notices are therefore `PASTE` (B6), not this block. The
   check-the-route-not-the-nav lesson still holds for anything else on this LMS — the theme
   hides the Calendar link while leaving `/calendar/export.php` live.

### Acceptance criteria

- An assignment deadline visible in the LMS appears in the week view with the same date.
- **An all-day LMS event renders on the correct KST date** — the off-by-one from ADR-019 is
  the specific failure to check here, and it is invisible until a date is missed.
- Re-running collection creates no duplicates (`UID` → `source_id`).
- **The assembled request URL contains `preset_time=recentupcoming`** and the run records a
  `max(DTSTART)` that extends beyond the current calendar month (given the LMS holds such an
  event).
- **No log line, error message or traceback produced by a forced fetch failure contains the
  token** — verified by deliberately breaking the URL and reading the output.
- An event deleted in the LMS is handled explicitly — decide and document whether it is
  removed or marked stale. **Do not leave it undefined**: a deadline that no longer exists but
  still alerts is noise, and one that silently vanishes is worse.
- No password is stored anywhere in the system.

### Tests (required)

- Integration: ICS fixture → Items with correct `starts_at`/`due_at`/`all_day`.
- Unit: an all-day event created in KST round-trips through UTC to the same calendar date.
- Unit: a timed event with a `TZID` other than Asia/Seoul converts correctly.
- **Unit: the assembled URL contains `preset_time=recentupcoming` and never `monthnow`**
  (`NFR-19`).
- **Unit: the adapter refuses to start when handed a URL whose `preset_time` is anything else** —
  the startup guard, asserted rather than assumed.
- **Unit: the token is masked in the exception raised by a failed fetch** — assert the raw
  token string is absent from the formatted message.

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

### Gate — the `AGENT` rung (SOURCES-001 **§5**, ADR-021 §3)

*(Corrected 2026-08-25: this cited `SOURCES-001` §4, which is the nine-condition **scraping**
gate. The five-condition authenticated-fetch gate is **§5**.)*

| # | Condition | Evidence required |
|---|---|---|
| 1 | Terms contain no prohibition on automated access | The clause, quoted, with a date |
| 2 | Own account, **read-only** | Design review: no submit/modify/delete code path exists |
| 3 | `API`, `FEED`, `SCRAPE/MAIL` and `PASTE` all insufficient for **files specifically** | B0 and B24 findings recorded in SOURCES-001 |
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
