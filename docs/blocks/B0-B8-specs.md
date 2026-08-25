# Block Specifications — B0 to B8 (Foundation and the Application)

**Last updated**: 2026-08-25 (**B0's last three non-mail items closed**: no forum RSS, Web
Services disabled, `User-Agent` fixed. Earlier the same day: B0 made finishable, findings and
site facts moved to `SOURCES-001` as the single copy, `source='SCRAPE'` adopted)

Detailed enough for Claude Code to start from. Infrastructure blocks are in
`B10-B11-specs.md`; blocks from B12 onward are specified when reached.

---

## B0 — Foundation

**Goal**: every source has a **recorded rung, by name, with dated evidence**; subscriptions are
live; the crawler `User-Agent` is fixed; the repository exists.

**B0 is finishable, and finishing it is the point.** Its product is *evidence*, and evidence can
be complete — a recorded rung with a dated finding per source, whatever the finding is.

> **What is *not* part of B0: the accumulation of items.** Once subscriptions are live and B3's
> scraper runs, items keep arriving for the whole life of the project, and that accumulation
> gates **B4** (≥ 30 items) and **B20** (≥ 100 items). It is a standing condition of the app
> lane (`BLOCKS-001` §2 and §4), **not** a task inside B0. An earlier version of this spec
> conflated the two, which made B0 permanently un-completable while still carrying nine
> acceptance criteria.

Start B0 today; do not wait for anything.

> **Re-scoped 2026-08-24 by ADR-022.** B0 used to be "subscribe to things, and find out whether a
> feed exists". Now that scraping is permitted, the question per source is *which rung, on
> what evidence* — so B0's product is a **dated `robots.txt` snapshot and a quoted terms-of-service
> clause for every candidate source**. Subscriptions still happen, because Gmail is kept as a
> redundant channel (ADR-022 §6), but they are no longer what makes B0 done.

**Tasks**

1. **Create the dedicated collection Gmail account.** Enable 2FA and set recovery options — if
   this account is lost, the entire mail channel is lost.

2. **Subscribe from that address** to Wevity (Web/Mobile/IT, Game/SW, Science/Engineering,
   Employment/Startup) and JobKorea job alerts. Check whether Linkareer offers email alerts —
   since it was excluded from scraping, **this is now its only possible channel.**
   - **Wevity uses both halves of `SCRAPE/MAIL` deliberately** — the scraper for control, the
     email for redundancy. They are peers, so using both needs no justification (ADR-022 §0).
   - **JobKorea's subscription is not optional** — it is the only channel for that source
     (ADR-022 §5 — the email half of `SCRAPE/MAIL`).
   - **Wevity's is redundancy**, kept deliberately alongside the B26 scraper so a silent scraper
     break does not become missing information (ADR-022 §6). Duplicates across the two channels
     are expected and measurable via `content_hash` (DATA-001).

3. **Run the §3 checklist for every source in `SOURCES-001` §2 and fill in the matrix.** This is
   the largest part of B0. Work **top-down the ladder** — official API → tokenised feed → public
   `API` → `FEED` → `SCRAPE/MAIL` → `PASTE` — and stop at the first rung whose gate passes.
   **`PASTE` is a complete and legitimate answer**, and it is where two whole categories of the
   owner's schedule live permanently.

   For each source, record with the **date checked**:

   | Evidence | Where it goes |
   |---|---|
   | `robots.txt` — the relevant lines verbatim, or **"404 → unrestricted (RFC 9309 §2.3.1.3)"** | `SOURCES-001` §2 notes |
   | **Terms of service — the automated-collection clause quoted, or its absence recorded, with the URL read** | `SOURCES-001` §2 notes. **This is the condition that decides the source** |
   | Does the list page render server-side? (`curl` it; are the rows in the response body?) | §2 notes — decides scraping vs. ADR-022 §4.2's fallback chain |
   | Is there a JSON/GraphQL endpoint the page itself calls? (DevTools → Network → XHR) | §2 notes — cheaper and far more stable than HTML |
   | Any decided case law or public dispute about scraping it? | §2 notes |
   | Chosen rung, and why the higher ones were rejected | §2 row |

   - **For any source to be scraped, walk all nine conditions in `SOURCES-001` §4** and record
     each. A source failing any one of them uses the **email half of `SCRAPE/MAIL`**, or falls to
     **`PASTE`** — **that is a successful B0 outcome, not a failure.**
   - **"There is nothing, use paste" remains a valid and complete answer** — but it must be
     *recorded*, because a recorded "none" is what licenses moving down the ladder.

4. **Sources with a known answer already** — confirm, do not re-derive:

   | Source | Status entering B0 | What B0 still owes |
   |---|---|---|
   | **School notice board** | `robots.txt` **404**, no RSS/Atom → **`SCRAPE/MAIL`, scraping** | Confirm the list page renders server-side (`curl`). Record the list URL, the row selector shape, and the pagination parameter. **B3 is built against this** |
   | **Wevity** | ✅ **`SCRAPE/MAIL` — all nine scraping conditions pass; uses *both* channels** | Optional: paste the ToS URL and wording into `SOURCES-001` §2 to complete the evidence record |
   | **Linkareer** | **`SCRAPE/MAIL`, email only — scraping excluded 2026-08-24 (owner's decision)** | Only: do email alerts exist? If not, the source is dropped (`SOURCES-001` §8). **Do not re-investigate scraping** |
   | **JobKorea** | **`SCRAPE/MAIL`, email only — decided** | Nothing but the subscription. **Do not re-investigate scraping**; the exclusion is on case law, not on `robots.txt` (`SOURCES-001` §8) |
   | **고용24 / Worknet, Saramin** | **`API`** | Submit the key applications — see task 5 |
   | **Academic calendar, KakaoTalk** | **`PASTE`** — permanent, by design | Nothing. Scraping being permitted does not make it preferred |

5. **Apply for the API keys now** — approval takes time:
   - 공공데이터포털 (data.go.kr) → 한국고용정보원 워크넷 채용정보. Note the daily cap.
   - `oapi.saramin.co.kr` → access key. **Record Saramin's pricing answer**; the guide does not
     publish it. Put it in `SOURCES-001` §7.

6. **LMS, in this exact order — stop at the first hit** (`SOURCES-001` §3):
   1. Calendar → iCal export / subscription URL. If present, deadlines are solved with **no
      password**. Treat the URL as a secret (SEC-13 pattern).
   2. Notice board / forum → RSS feed URL. **Answered 2026-08-25: the LMS does not support
      forum RSS.** It was the only remaining RSS candidate in the project, so **no RSS source
      exists anywhere here and no RSS adapter is built** — B24 is ICS only, and LMS course
      notices fall to `PASTE` (`SOURCES-001` §1.1, §2).
   3. Site administration → **Web services**: enabled for students? Almost certainly not, but the
      check costs five minutes and if enabled it reaches course materials through an official API
      and **supersedes the `AGENT` rung entirely.** **Say so loudly** — it would be the best
      available outcome. **Answered 2026-08-25: disabled.** The `AGENT` rung (`SOURCES-001` §5,
      B25) remains the only path to course materials, and remains conditional.
   4. Only if 1–3 all fail: evaluate the **`AGENT`** rung against `SOURCES-001` §5.

7. **Fix the crawler `User-Agent` string** and record it in `SOURCES-001` §7.
   **Done 2026-08-25** — `schedule-manager/0.1 (personal use; +kimnoell1225@gmail.com)`.
   `SOURCES-001` §7 is the record; B3 sets it in one place. Shape:
   `schedule-manager/<version> (personal use; +<contact email>)`.
   It must contain no crawler name this project is not — no `Claude`, `anthropic-ai`, `GPTBot`.
   **Not to evade a block: because claiming to be a crawler you are not is a false identifier**,
   and ADR-022 condition 4 forbids it. A site that blocks the honest UA sends that source to
   the email half of `SCRAPE/MAIL`, or to `PASTE`.

8. **Initialise the repository** with this document set, `.gitignore`, `CLAUDE.md`, `README.md`.
   Enable GitHub **secret scanning with push protection** (SEC-14).

9. **Record in `STATUS.md`**: subscriptions and their dates, the per-source rung decisions (by
   name), the
   LMS answer, and the API key application dates.

**Progress as of 2026-08-25 — B0 is partially complete**

**The findings themselves live in `SOURCES-001` §2, dated, and nowhere else.** They were being
maintained in five files at once. Read the matrix there; this spec tracks only what B0 still
owes:

| Still owed | Blocks |
|---|---|
| **Email subscriptions — activate and report, JobKorea's included.** The dedicated Gmail account, JobKorea's alert (that source's *only* channel), Wevity's alert (redundancy), and whether Linkareer offers alerts at all (its only remaining channel — if none, it is dropped) | B1/B2 |
| 사람인 API key — approval pending; record the pricing answer on approval | B23's second source |

**This is the whole of what B0 still owes, and it is all mail.** Everything else is resolved:
school board ✅ `SCRAPE/MAIL` (**B3 unblocked**), LMS calendar ICS ✅ `FEED` (**B24**),
**LMS forum RSS ✅ answered 2026-08-25 — not supported**, **LMS Web Services ✅ answered
2026-08-25 — disabled**, **crawler `User-Agent` ✅ fixed 2026-08-25 (`SOURCES-001` §7)**,
고용24 key ✅ received (**B23 startable**), Linkareer scraping excluded by owner decision,
Wevity gate ✅ passed (**B26 unblocked**).

**Two of those answers were negative, and a negative answer is a complete one.** No forum RSS
means the project has **no RSS source at all**, so B24 is ICS only and no RSS adapter is written
anywhere (`SOURCES-001` §1.1). Web Services being disabled means the `AGENT` gate (§5, B25) is
the only remaining path to course materials.

A **near-miss** was recorded during this investigation:
`docs/incidents/2026-08-24-lms-token-near-miss.md`. **The LMS token is pending rotation.**

**Acceptance criteria**

- **`SOURCES-001` §2 has, for every source: a chosen rung by name, a dated `robots.txt` finding, and a
  dated terms-of-service finding.** A quoted prohibition is as complete an answer as a quoted
  permission.
- **Every source to be scraped has all nine `SOURCES-001` §4 conditions recorded**, including
  the server-side-render check.
- The school notice board has a recorded list URL and a confirmed server-side render — **B3
  cannot start without this.**
- The LMS question has a written answer, whatever it is, for all three steps.
- The two API key applications are submitted (approval may still be pending).
- At least two email subscriptions are active and at least one message has arrived. JobKorea's is
  one of them.
- The crawler `User-Agent` string is fixed and recorded.
- `git log` shows the initial documentation commit.

**Not in this block**: any code. **No test fetches beyond a single manual `curl` per source** to
answer the render check — a `curl` is investigation, a loop is a collector, and collectors are B3.

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
   index included — **including `'SCRAPE'` in the `items_source_check` constraint**, which B3
   needs and which cannot be added later without a migration plus a backfill of mislabelled rows.
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

## B3 — Scraper adapter (school notice board)

**Goal**: school notices land in the same table as mail, through the same pipeline — and the
scraping gate machinery exists once, correctly, for every scraper that follows.

> **Re-scoped 2026-08-24 by ADR-022.** This block was "RSS collector", with a fallback of "if B0
> found no feed, prove the adapter against an arbitrary public feed and route school notices to
> paste". B0 found no feed **and no `robots.txt`**, and paste for a board that updates weekly is a
> permanent manual tax on the highest-priority capability. So the block builds the **scraper**
> instead, and the RSS adapter moves to **B24**, where the LMS forum feed actually exists.

**Why the school board and not a job site.** It is the safest scraping target in the project:
non-commercial `.ac.kr`, no database interest, no case law, `robots.txt` absent (RFC 9309 →
unrestricted), and the owner is its intended audience. Building the gate machinery here means
B26 inherits a working rate limiter, a working conditional-request path and a working
empty-result alarm, rather than inventing them against a commercial site.

This block also remains the cheapest possible proof that **ADR-003's one-table design extends**.
If adding a second source type needs more than a new adapter, ADR-003 was wrong and now is when
to find out — and an HTML adapter tests that harder than a second feed adapter would have.

**Entry condition**: ✅ **satisfied 2026-08-24.** B0 recorded the list URL and confirmed the rows
are present in a plain `curl` response (`SOURCES-001` §2.2). **This block can start.**

**Configuration: `SOURCES-001` §2.2.** The list and detail URLs, the row anchor, the `source_id`
attribute, the pagination parameter, the observed volume, and the separate **backfill vs daily
page caps** are all recorded there with the date verified — together with the nine gate
conditions. **They are not restated here**, so a site redesign changes exactly one file.

Two of those facts decide how this block is written, so they are named rather than merely linked:

- **`source_id` is `nttNo` from the detail link, never the row's 번호 column**, which shifts as
  posts are added. Getting this wrong produces duplicate rows on every renumbering.
- **The search parameters (`searchCnd` / `searchKrwd`) are deliberately unused.** Server-side
  keyword filtering means anything the keyword misses disappears with no trace — the same
  silent-omission class as the LMS `monthnow` problem (`NFR-19`). Fetch the list, filter locally.

**Backfill and daily collection are separate settings with separate caps**, because 630 pages
× 3 s ≈ 32 minutes is a reasonable one-off and an absurd daily job.

**Tasks**

1. **A `Source` abstraction** with two implementations: `GmailSource` (refactored from B2) and
   `ScrapeSource`. Both yield Items; everything downstream is shared.
2. **A shared `HttpFetcher` used by every scraping adapter** — this is the reusable part, and it is
   the reason the block exists:
   - the honest `User-Agent` from `SOURCES-001` §7, set in **one** place;
   - a **≥ 3 s** inter-request delay (ADR-022 condition 5), enforced in the fetcher, not left to
     each adapter to remember;
   - `If-Modified-Since` / `If-None-Match` from stored validators, and **304 handled as
     "nothing new", not as an error**;
   - a configured **page cap**;
   - **one run per day**.
3. **Parse the list page** → Item. **`source = 'SCRAPE'`** (DATA-001 — the enum value exists from
   B2's migration; do **not** reuse `'RSS'`, which means a real feed). `source_id` = the notice's
   stable id from its permalink, never the row position. `type = 'NOTICE'`; `category` stays
   `NULL` (REQ-001 §2.3).
4. **`collector_state['scrape:<source>:last_seen']`** plus the stored HTTP validators, for
   incremental behaviour (FR-13).
5. **Sources configured in one place, addable without a code change** (FR-2): base URL, list path,
   row selector, `source_id` attribute, pagination parameter, **daily page cap and backfill page
   cap as separate settings**.
6. **Implement NFR-17 — empty result is failure** (ADR-022 §3, `SOURCES-001` §4.1). This is the
   part that makes scraping admissible, so it is not optional:
   - track per source whether it has **ever** returned ≥ 1 item;
   - zero items from such a source → that source is `FAILED`, the run is `PARTIAL`;
   - **the cursor does not advance** on a zero-item result;
   - a parsed row **missing `title` or `url`** is a failed row and is **counted**, not skipped
     silently;
   - two consecutive zero-item runs raise the ADR-012 alert.
7. **A malformed row is skipped and counted**; one bad row never kills the run.

**Acceptance criteria**

- One collection run pulls from Gmail and the school board, writing **one** `collection_runs` row
  covering both.
- The board failing while Gmail succeeds records `PARTIAL`, not `FAILED`.
- Adding a second scrape source requires editing configuration only.
- **A run whose parse yields zero rows records `FAILED` for that source and leaves the cursor
  unchanged** — verified by pointing the selector at something that matches nothing.
- The second run issues conditional requests and does no more than the configured page cap of
  fetches.
- **Measured**: ≥ 3 s elapses between consecutive requests.
- The daily run stays within the daily page cap; the backfill is a separate, explicitly invoked
  path and cannot be triggered by the scheduler.

**Tests (required)**

- Integration: saved HTML fixture → Item → database; re-run deduplicated.
- Integration: **zero-parsed-rows → `FAILED` for that source, `PARTIAL` run, cursor unchanged.**
  This is the NFR-17 regression test and the most important test in the block.
- Integration: a 304 response is "nothing new", not a failure, and does not reset the
  has-ever-returned-rows flag.
- Unit: a malformed row is skipped, the run survives, and the skip is **counted**.
- Unit: a row missing `title` or `url` is counted as a failed row, not silently dropped.
- Unit: the rate limiter enforces ≥ 3 s (with a fake clock).
- Unit: the `User-Agent` is the configured honest string, and appears on every request.
- Unit: `source_id` comes from `nttNo`, not the row's 번호 column — a fixture where the two
  disagree, so a renumbered board cannot produce duplicate rows.
- Unit: the scheduled path cannot exceed the daily page cap, whatever the backfill cap is set
  to.
- **Never fetch the live site in tests** — saved HTML fixtures only (ADR-010's rule, extended
  from Gmail to every source).

**Not in this block**: Wevity (B26 — and it needs B0's ToS finding first). Any
headless browser, ever (ADR-022 §4.2).

---

## B4 — Classification and filter rules (TDD)

**Goal**: items appear under the correct tab.

**Entry condition**: at least **30 collected items from at least 3 distinct sources or senders.**
Rules written against five samples are guesses. If unmet, work the infra track (B9).

> Widened from "30 messages from 3 senders" by ADR-022: collection is no longer mail-only, so the
> condition counts items from any channel. This also makes the condition reachable by **collecting**
> rather than only by waiting — B3's scraper can backfill a notice board's existing pages, where a
> mailbox can only grow forward in time. Note that classification rules still apply to
> `type = 'NEWSLETTER'` only (REQ-001 §2.3), so the newsletter senders remain the binding
> constraint for the rules themselves.

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
`type='JOB'` item ends with `category IS NULL`. Add one asserting a **`type='NOTICE'` item from
the scraper** also ends with `category IS NULL` — the classifier must ignore non-newsletter
sources entirely.

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
