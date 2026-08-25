# Block Specification — B26 (commercial scraping adapter — Wevity)

**Status**: Approved
**Created**: 2026-08-24
**Last updated**: 2026-08-25 (condition 2 recorded as an absence finding; "inherited from B3"
marked as planned, since B3 does not exist yet)
**Related**: ADR-022, SOURCES-001 §2 / §4, ADR-003, ADR-012, REQ-001 NFR-7 / NFR-17 / NFR-18

> **Numbering**: creation order, not execution order (`BLOCKS-001` §3).

| Block | Runs after | Status |
|---|---|---|
| **B26** — Wevity scraper | **B3** | ✅ **Gate passed 2026-08-24** — §1 |

---

## B26 — Wevity (`SCRAPE/MAIL`, scraping half)

**Goal**: 공모전·인턴·대외활동 공고가 메일을 기다리지 않고 **질의로** 들어온다.

**Why this is a separate block from B3.** B3 builds the scraping machinery against the safest
possible target — a non-commercial university notice board. B26 points that machinery at a
commercial site. The machinery should not be designed and legally stress-tested in the same
block; if the gate is going to fail a source, it should fail it against an adapter that already
works elsewhere.

**Why it is worth a block at all.** Email subscription delivers what the sender decides to send,
when they decide to send it, filtered by their relevance model. `ADR-021` made this argument to
rank APIs above email; `ADR-022` §"Context" extends it to scraping. The owner's stated priority is
that **missing information is the worst failure in this capability**, and email has the weakest
coverage guarantee of any channel in the set.

### 1. Entry gate — check this first

**Do not write the adapter until all nine `SOURCES-001` §4 conditions are recorded as passing.**

| # | Condition | Status entering B26 |
|---|---|---|
| 1 | `robots.txt` permits the exact paths under `User-agent: *` | ✅ **Recorded 2026-08-24** — `User-agent: *` → `Allow: /` |
| 2 | **Terms of service contain no prohibition on automated collection** | ✅ **Passed as a recorded absence** — terms read by the owner **2026-08-24**, finding: no automated-collection clause. Same form of answer as the school board's (`SOURCES-001` §2.2), where an absence established by a full walk is a complete answer. *Still owed for completeness: the ToS URL, so a future session can re-check without re-deriving. Not blocking* |
| 3 | Public, unauthenticated pages only | ✅ Category list pages are public |
| 4 | Honest `User-Agent`, no rotation | **Will be inherited from B3's `HttpFetcher`** — B3 is not built yet |
| 5 | ≥ 3 s delay, one run/day, capped pagination | **Will be inherited from B3** |
| 6 | Conditional requests | **Will be inherited from B3** |
| 7 | Empty result is `FAILED` | **Will be inherited from B3** (NFR-17) |
| 8 | Personal use only, no redistribution | Dashboard is Basic-Auth'd to one person (SEC-001) |
| 9 | No headless browser on the server | ✅ Wevity is server-rendered |

✅ **All nine conditions pass as of 2026-08-24. This block is unblocked**, and runs whenever B3
is done.

**If the terms are later found to prohibit automated collection**, Wevity's scraping half is
withdrawn and this block closes. It then runs on the email subscription it already has (B0 task 2). **Record
the drop in `SOURCES-001` §2 and §8 — do not silently skip it**, and note it in `STATUS.md`
rather than leaving an unstarted block on the roadmap. That outcome is not costly: B23's `API` sources carry the job capability, and Wevity's contest coverage still arrives by email — later and
unfiltered, but it arrives.

> **Linkareer was removed from this block on 2026-08-24 by owner decision.** It had passed
> conditions 1, 3 and 9 — `robots.txt` permits the four target list paths, and the pages proved
> **server-rendered** (data embedded in the HTML, no endpoint call needed), so the memory
> objection did not apply. **Its ToS was never read, so condition 2 was never satisfied**, and it
> was excluded rather than cleared. Under `SOURCES-001` §1 a source may always be placed lower
> than the ladder allows. It sits on the **email half of `SCRAPE/MAIL`** — alerts, if they
> exist — and is dropped entirely if they do not (`SOURCES-001` §8).

### 2. Wevity — the only source in this block

Server-rendered. `requests` + parser, no browser.

1. Adapter behind B3's `Source` abstraction, using B3's `HttpFetcher` unchanged. **`source =
   'SCRAPE'`** (DATA-001), never `'RSS'`.
2. **Honour `Crawl-delay: 3`.** It is declared for `GPTBot`, not for `*` — we adopt it as the
   floor for every source anyway (ADR-022 condition 5). Declaring a delay for one crawler and not
   another is not permission to hammer as the other.
3. Four categories from B0: 웹·모바일·IT, 게임·SW, 과학·공학, 취업·창업. **Configuration, not code**
   (FR-2).
4. `source_id` = the stable id in the posting permalink, never the row position.
5. `type = 'JOB'` for 채용, `type = 'CONTEST'` for 공모전 per DATA-001's enum; `category` stays
   `NULL` (REQ-001 §2.3).
6. `starts_at` / `due_at` per ADR-019 from the posting's 접수기간. **A parsed deadline that would
   land in the past is a failed row, counted** — it almost always means the date format changed.

### 3. Do not narrow the fetch server-side

If Wevity offers keyword or filter parameters on its list URLs, **do not use them to reduce what
is fetched.** Server-side filtering means anything the filter misses disappears with no trace —
the same silent-omission class as the LMS `monthnow` problem (`NFR-19`, `SOURCES-001` §2.1).
Fetch the category lists, filter locally with `FR-3`'s rules.

Category selection is different and is fine: the four categories *are* the subscription, they are
configuration (FR-2), and they are recorded.

### 4. Remaining tasks

1. **Cursor**: `collector_state['scrape:wevity:last_seen']`, plus stored HTTP validators.
2. **NFR-17 applies.** Wevity returning zero while the school board returns rows is a `PARTIAL`
   run with Wevity `FAILED` — not a quiet `SUCCESS`.
3. **Add Wevity to the coverage-audit rotation** (PRD-000 §4.1).
4. `content_hash` per DATA-001. **Wevity now arrives through two channels** — its email
   subscription and this scraper. **Both are the same rung** (`SCRAPE/MAIL`), so using both needs
   no justification — it is deliberate redundancy (ADR-022 §0, §6). The duplicate
   rows are the measurement, not the bug.

### 5. Acceptance criteria

- One collection run pulls Gmail + school board + Wevity and writes **one** `collection_runs` row.
- One source failing records `PARTIAL`; the others complete.
- The second run fetches strictly fewer new items than the first.
- **A zero-parsed-rows result records `FAILED` for that source and leaves its cursor unchanged.**
- **Measured**: ≥ 3 s between consecutive requests, and the run stays within the configured page
  cap.
- **A Wevity posting that arrived by both email and scraper produces two rows with the same
  `content_hash`** — run DATA-001's measurement query and record the count. This is the first
  real data for ADR-003's deferred cross-source deduplication question.
- `SOURCES-001` §2 and §7 updated with the ToS finding, the crawl budget, and the date verified.

### 6. Tests (required)

- Integration: saved HTML (or JSON) fixture → Item → database; re-run deduplicated.
- Integration: **zero-parsed-rows → `FAILED` for that source, `PARTIAL` run, cursor unchanged.**
- Integration: the same posting from the email fixture and the scrape fixture yields **one
  `content_hash`, two rows** — asserted, because it is the measurement the ADR-003 decision needs.
- Unit: a malformed row is skipped, counted, and does not kill the run.
- Unit: a 접수기간 that parses to a past date is a counted failed row.
- Unit: no configured path resolves outside the four permitted category lists — a guard test, so
  a future configuration edit cannot walk somewhere the `robots.txt` finding did not cover.
- Unit: the honest `User-Agent` is on every request and contains none of the blocked crawler
  names.
- **Never fetch the live sites in tests** (ADR-010, extended to every source).

### 7. Cost

**$0.** No new AWS resource, nothing billed per hour. One daily run of a few dozen conditional
GETs is inside the noise of the ARCH-001 ledger. The rate limit and page cap exist because an
accidental loop would get the crawler blocked and would be rude — not because it would cost money.

### 8. Not in this block

- **JobKorea.** Email only, on decided case law (`SOURCES-001` §8). Re-examined under
  ADR-022's permissive policy and still excluded. **Do not re-open on `robots.txt` evidence.**
- **Linkareer.** Removed by owner decision 2026-08-24 (§1). Email only if alerts exist,
  otherwise dropped. **Do not re-open without the owner asking and the ToS being read.**
- **Saramin's website.** Its `API` rung is already in use (B23).
- Any headless browser on the server.
- Any UA rotation, proxy rotation, or retry-past-a-block. A block is an answer (ADR-022
  condition 4).
