# SOURCES-001 — Source Matrix and Channel Policy

**Status**: Approved
**Created**: 2026-08-22
**Last updated**: 2026-08-25 (B0 findings closed: **no forum RSS**, **Web Services disabled**,
**`User-Agent` fixed** — §1.1, §2, §7. Earlier the same day: this document became the single
authority for the ladder and both gates; B3's site facts absorbed into §2.2; Wevity condition 2)
**Related**: ADR-002, ADR-018, ADR-021, ADR-022, **ADR-023**, REQ-001 §4

> **This document is the authority.** The ladder (§1), the scraping gate (§4) and the
> authenticated-fetch gate (§5) are stated here and **nowhere else**. `ADR-021`, `ADR-022` and
> `ADR-023` record *why* they have this shape; `REQ-001`, `README`, `CLAUDE.md`, `STATUS` and the
> block specs point here rather than restating. If a copy is found elsewhere, it is stale by
> definition — delete it and link.

This document is the register of **where every piece of information comes from**, and the
procedure for adding a new source. It is updated whenever a source is investigated, added,
changed or dropped — including when the answer is "nothing exists".

## 1. The ladder (ADR-022, restructured by ADR-023)

Try top-down. A lower rung may be used only after every higher rung has been checked and
recorded here as unavailable. **"I didn't look" is not "unavailable".**

| Order | Name | Channel | Credential cost |
|---|---|---|---|
| **1** | **`API`** | Official API | an API key |
| **2** | **`FEED`** | A feed — personal tokenised (ICS, tokenised RSS) **or** public (RSS/Atom) | **none** |
| **3** | **`SCRAPE/MAIL`** | **Permitted scraping (gate in §4) and email subscription — peers, not ranked.** Use whichever fits the source, or **both** | none |
| **4** | **`PASTE`** | Paste / screenshot → **LLM extraction with mandatory confirmation** (ADR-018) | none |
| — | **`AGENT`** | Authenticated fetch, own account, **agent-side only** (gate in §5) | **a real account credential** — conditional, B25 |
| ✗ | — | Scraping **behind a login**, or **redistributing** collected content | prohibited permanently |

**Rungs are identified by name, not by number** (ADR-023). The **Order** column exists only
because the ladder is tried top-down; it is **not an identifier** and must never be used as one.
The numbers were reassigned three times (ADR-021, ADR-022, ADR-023) and each reassignment
silently broke cross-references across a dozen files; the names will not move. Write
`SCRAPE/MAIL`, not "rung 3" — the same reasoning as the block-numbering policy in
`BLOCKS-001` §3.

### 1.1 What changed on 2026-08-24, and why (ADR-023)

Two rungs merged and one moved.

**`FEED` absorbed the old "tokenised feed" and "public feed" rungs.** They were ranked 2 and 3.
Nothing ever turned on the distinction — both are a URL that returns structured data with no
credential worth protecting beyond the URL itself — and no source has ever needed the tie
broken. **No RSS or Atom feed exists anywhere in this project — this is now a closed finding,
not a gap.** The LMS forum was the last candidate and it was checked on **2026-08-25**: the LMS
does not support forum RSS. **The LMS calendar ICS is the only `FEED` source this project has**,
and the `RSS` half of the rung is empty by evidence.

**Scraping and email merged into `SCRAPE/MAIL`, as peers** (`ADR-023`). `ADR-022` had ranked
scraping above email, arguing that a source you query beats a mailbox you wait for. That argument is right
about *latency and control* and wrong about *ordering*, because it implied email should be
dropped wherever scraping works. In practice which one fits is a property of the source:

- **Wevity** may use **both** — the scraper for control, the email for redundancy. Under the old
  ordering this needed an explanation. As peers it needs none. **In practice only the scraper is
  planned**: the email half was deferred on 2026-08-30 and sits in `STATUS.md` §6 with a trigger.
  The point stands regardless — the ladder permits both, and nothing had to justify the pairing.
- **JobKorea** uses **email only** — scraping is excluded on decided case law (§8).
- **Linkareer** uses **email only** — scraping excluded by owner decision (§8).

**`PASTE` is the last resort and it is not a manual one.** Pasted text goes through LLM
extraction with mandatory confirmation (ADR-018), so the fallback still produces structured
items rather than typing. That is what makes it an acceptable floor.

### 1.2 Which rungs each kind of information uses

The ladder is general; this is the actual allocation.

| Information | Rungs used | Sources |
|---|---|---|
| **Jobs and contests** | `API` → `SCRAPE/MAIL` → `PASTE` | 고용24, Saramin (API); 학교 공지, Wevity (scrape); Wevity, JobKorea, Linkareer (mail) |
| **Personal schedule — 과제·시험 마감** | `FEED` → `PASTE` | LMS calendar ICS; anything the ICS misses is pasted |
| **LMS course notices (강의 공지)** | `PASTE` only | No forum RSS (2026-08-25) and the board is behind a login, where scraping is permanently prohibited (§1). `AGENT` (B25) is the only alternative and it is conditional |
| **Club / department / KakaoTalk schedules** | `PASTE` only | No machine channel exists — KakaoTalk's API is send-only (ADR-018) |
| **Academic calendar** | `PASTE` only | A page updated twice a year; an adapter would rot between uses |

**`FEED` is empty for jobs and contests, and that is a recorded finding, not an oversight** —
no job or contest source investigated so far publishes RSS or Atom.

**`PASTE` is not a failure state.** It is the designed floor for every source that has no
machine channel, and two whole categories of the owner's schedule live there permanently.

**A higher rung still wins where one exists**, and `SCRAPE/MAIL` is *permitted*, not
*preferred*: where the thing being collected changes twice a year, `PASTE` still beats an
adapter that rots.

**`robots.txt` is condition 1 of nine, and it is not the deciding one.** It has no legal force
in Korea. The **terms of service** decide (§4 condition 2). `Allow: /` is permission from a
crawler-directive file, not from the site's lawyers.

## 2. Source matrix

Status values: **Confirmed** (verified, working) · **Planned** (channel known, not built) ·
**To investigate** (B0) · **Excluded** (with a reason).

### Schedules and school

| Source | Rung | Channel | Status | Block | Notes |
|---|---|---|---|---|---|
| **LMS deadlines (과제·시험)** | **`FEED`** | Moodle **iCalendar export URL** | **✅ Confirmed 2026-08-24** | **B24** | Moodle core under a **coursemos / UBION (유비온)** commercial wrapper (`M.cfg` → `"theme":"coursemos"`; plugins `ubion`, `ubboard`, `ubonline`, `ubirregular`, `ubassistant`, `ubsend`, `ubmanual`). **The Calendar nav item is hidden by the theme, but the route is live**: `/calendar/view.php` and `/calendar/export.php` both work. Feed shape: `/calendar/export_execute.php?userid=<userid>&authtoken=<token>&preset_what=all&preset_time=recentupcoming`. **`preset_time` MUST be `recentupcoming`** — see §2.1. No cookie or header needed: **the `authtoken` query parameter is the entire credential** (SEC-13 URL-as-secret). **Token pending rotation** — see `docs/incidents/2026-08-24-lms-token-near-miss.md` |
| **LMS course notices** | **`PASTE`** | **paste → LLM extraction** | **✅ Confirmed 2026-08-25 — no feed** | **B6** | **The LMS does not support forum RSS** (owner, 2026-08-25). Moodle standard forum RSS was expected to exist and does not on this installation. With `FEED` closed, the next rung down is `SCRAPE/MAIL` — but **the course boards sit behind a login, and scraping behind a login is permanently prohibited** (§1). So the rung is `PASTE`. **`AGENT` (§5, B25) is the only alternative and it is conditional.** This closes the last RSS candidate in the project — see §1.1 |
| LMS course materials (files) | **`AGENT`** | agent-side authenticated fetch | **Conditional** | B25 | Only if all five **§5** conditions hold. **Moodle Web Services is disabled for students — confirmed 2026-08-25.** It would have superseded this rung entirely with an official API (§3 LMS step 3, ADR-021 §186); it does not exist here, so the `AGENT` gate is the only remaining path to course materials |
| **School notice board** | **`SCRAPE/MAIL`** | **HTML scraping** (server-rendered list page) | **✅ Confirmed 2026-08-24** | **B3** | 충북대 공지사항(전체). **All nine §4 conditions, the URLs, selectors, pagination and page caps are recorded in §2.2 — the single copy.** B3's spec links here rather than restating them |
| Academic calendar (수강신청·시험기간) | `PASTE` | **paste → LLM extraction** | Planned | B6 | A page updated ~once a semester. Not a feed; polling two changes a year is not worth a scraper |
| Club / department schedules | `PASTE` | **paste / screenshot → LLM extraction** | Planned | B6 | KakaoTalk has **no read API** — verified 2026-08-22 (ADR-018) |

### Jobs and contests

| Source | Rung | Channel | Status | Block | Notes |
|---|---|---|---|---|---|
| **Worknet / 고용24** | **`API`** | 공공데이터포털 open API (한국고용정보원) | **Planned** | B23 | Government open data. Legally the cleanest source in the project. Auth key only |
| **Saramin** | **`API`** | `oapi.saramin.co.kr` Open API | **Planned** | B23 | **500 calls/day**, access key after application. Pricing not published — confirm on application. *Previously excluded in error* |
| **Wevity** | **`SCRAPE/MAIL`** | **scraping *and* email — both, deliberately** | **Planned** | **B26** | `robots.txt` 2026-08-24: `User-agent: *` → `Allow: /`; `Crawl-delay: 3` declared for `GPTBot` and adopted as the **global floor**. **§4 condition 2: PASSED as a recorded absence** — terms read by the owner **2026-08-24**, finding: *no clause prohibiting automated collection*. This is the same form of answer as the school board's (§2.2 condition 2): **an absence, recorded with a date, is a complete answer to condition 2.** *Still owed for completeness: the ToS URL, so a future session can re-check without re-deriving — this does not block B26.* Categories: 웹·모바일·IT, 게임·SW, 과학·공학, 취업·창업. **All nine conditions pass → B26 unblocked.** **Email half deferred 2026-08-30** — it was redundancy for a source the scraper already covers; trigger in `STATUS.md` §6. The rung is unchanged |
| **Linkareer** | **`SCRAPE/MAIL` — email only** | email alerts | **Excluded from scraping 2026-08-24 (owner's decision)** | B0 | `robots.txt` permits the four target list paths and the page proved **server-rendered** (data embedded in HTML, no endpoint call needed), so it **passed conditions 1, 3 and 9** — it was technically viable. **Excluded by owner decision, with the ToS unread.** Under §1 that is a legitimate stop: a source may always be placed on a lower rung than the ladder allows. **Deferred 2026-08-30**: nobody has checked whether email alerts exist, and until someone does this source contributes nothing. It is not dropped — dropping needs the answer — it is parked, with a trigger in `STATUS.md` §6 |
| **JobKorea** | **`SCRAPE/MAIL` — email only** | job-alert email | **Planned** | B0/B2 | **Scraping excluded on decided case law**, not on assumption: 잡코리아 v 사람인 (저작권법 데이터베이스제작자 권리 + 부정경쟁방지법, damages awarded) concerns scraping job postings from this board. `robots.txt` *does* allow `/recruit/joblist` and `/Recruit/GI_Read` under `User-agent: *`, but blanket-blocks `GPTBot`/`ClaudeBot`/`anthropic-ai`/`CCBot`/`DeepSeek`/`Amazonbot` — a site actively policing automated access. The `API` rung (고용24, Saramin) covers the same space. **Do not re-open on `robots.txt` evidence alone** |
| Saramin (web) | ✗ | — | **Excluded** | — | Superseded by its `API` rung. Scraping a site whose official API you already hold is indefensible |
| Campuspick | ✗ | — | Excluded | — | App-only, no email evidence |

### 2.1 LMS calendar — `preset_time` has exactly one permitted value

```
preset_time=recentupcoming
```

**This is the only value this project uses.** It is computed relative to request time (recent +
upcoming) and matches the export screen's "current + next 2 months" option.

**`monthnow` is prohibited.** It is recorded here rather than left out, so a future session does
not rediscover it on the export screen and try it — the same reason §8 keeps dropped sources.
Why it is prohibited is the whole reason `NFR-19` exists: it is **fixed to the current calendar
month**, so next month's deadlines leave the feed with no re-export, no warning and no error.

**Why this needs its own section.** `monthnow` does not fail — that is the whole problem. It
returns HTTP 200, a well-formed `.ics`, and a non-empty event list. It parses. **`NFR-17`
(empty result is failure) does not fire, because the result is not empty — it is truncated.**
The dashboard looks correct while next month's 과제 마감 is simply absent, which is the
project's highest-priority capability failing invisibly.

`NFR-17` catches *zero*. This is *not enough*, and they are different failure classes.
**`NFR-19`** generalises the countermeasure to every source with a scope parameter.

**Consequences for B24**, all five required:

1. **The Secret holds the base URL, `userid` and `authtoken` only.** `preset_what` and
   `preset_time` are assembled in code. Storing the whole URL as one secret hides the
   parameters inside the secret where **no test can assert them**.
2. **`preset_time` is a constant in the adapter, not a configuration setting.** There is no
   legitimate second value, so offering the choice only creates a way to get it wrong.
3. **Startup validation**: if the assembled URL does not carry `preset_time=recentupcoming`, the
   adapter **refuses to run.** A truncated feed is worse than no feed — no feed is visible, a
   truncated one is not.
4. **A unit test asserts the assembled URL contains `preset_time=recentupcoming`**, and never
   `monthnow`.
5. **`max(DTSTART)` is recorded per run**, so a collapse of the collection horizon back to the
   current month is visible. It is not a hard runtime failure — a month with genuinely no
   deadlines is legitimate — but it must be observable.

### 2.2 School notice board — scraping gate record and configuration (verified 2026-08-24)

**This section is the single copy of these facts.** `B0-B8-specs` §B3 links here rather than
restating them, so a site redesign changes one place.

#### Confirmed configuration

충북대 공지사항(전체).

| Setting | Value |
|---|---|
| List URL | `https://www.cbnu.ac.kr/www/selectBbsNttList.do?key=813&bbsNo=8` |
| Detail URL | `https://www.cbnu.ac.kr/www/selectBbsNttView.do?key=813&bbsNo=8&nttNo={id}` |
| Row anchor | `<a>` inside `<td class="p-subject">` |
| `source_id` | `nttNo` from the detail link — **never the row's 번호 column**, which shifts as posts are added |
| Row fields | 번호, 카테고리, 제목, 파일, 부서, 작성일, 조회수 |
| Pagination | `pageIndex` |
| Volume at check | **6,296 posts / 630 pages @ 10 per page** (2026-08-24) |
| Stack | jQuery 1.12.4, no SPA — server-rendered |
| Search params | `searchCnd` (SJ/ADITFIELD8/CN) + `searchKrwd` — **deliberately unused, see below** |
| `items.source` value | **`'SCRAPE'`** (DATA-001) |

**Backfill and daily collection are different numbers.** 630 pages × 3 s ≈ 32 minutes: fine as a
deliberate one-off, absurd as a daily job. They are configured separately.

| Run | Page cap | Trigger |
|---|---|---|
| **Backfill** | up to 630 | manual, once, explicitly invoked |
| **Daily** | 2–3 | the scheduled collector |

A board producing a handful of posts a day never needs more than the first few pages.

#### The nine conditions

| # | Condition | Finding |
|---|---|---|
| 1 | `robots.txt` permits the paths | **Absent — HTTP 404**, verified twice (`curl` returned a 404 error body; browser showed the site's custom 404 page). **RFC 9309 §2.3.1.3 → unrestricted.** No crawl rules exist at all, neither allow nor disallow |
| 2 | **ToS contains no automated-collection prohibition** | **No terms of service exist.** Full navigation walk (대학/대학원, 입학/취업, 연구/산학, 학사안내, 대학생활, 홍보센터, 대학안내, 행정서비스, footer 바로가기) found no 이용약관 page. **개인정보처리방침** (`key=668`) read in full — 14 articles, covering personal-data collection, retention, third-party provision and cookies; **no clause on automated access, crawling, bots or scraping.** `key=207` (보안업무처리규정) is an internal staff regulation, not public-access terms — not applicable. **An absence established by a full walk, not by not looking** |
| 3 | Public, unauthenticated only | ✅ List and detail pages are public |
| 4 | Honest `User-Agent` | ✅ **String fixed 2026-08-25 — see §7.** Inherited from B3's `HttpFetcher`, set in one place |
| 5 | ≥ 3 s delay, one run/day, capped pagination | Enforced in B3's fetcher. **Backfill and daily caps are different numbers — see B3 spec** |
| 6 | Conditional requests | B3 stores validators; server support to be observed on first run |
| 7 | Empty result is `FAILED` | `NFR-17`, implemented in B3 |
| 8 | Personal use only | ✅ Basic-Auth'd dashboard, one reader (SEC-001) |
| 9 | No headless browser | ✅ **Server-rendered.** `curl` (no JS) returns the rows: table caption `대학생활-공지사항 목록 - 번호, 카테고리, 제목, 파일, 부서, 작성일, 조회수 정보 제공`, titles as plain text in `<a>` inside `<td class="p-subject">`. Stack is jQuery 1.12.4 — not React/Vue |

**An official `API` was assumed absent, not verified.** No evidence of one exists for this
CMS board. Recorded honestly as an assumption; if an API surfaces, it supersedes this row.

**`searchCnd` / `searchKrwd` are deliberately not used.** Server-side keyword filtering means
anything the keyword misses disappears with no trace — the same silent-omission class as
`monthnow`. Fetch the list, filter locally.

**Privacy note.** Rows carry 부서 (department) names, not individuals. Stored fields are the
notice's own metadata; `SEC-6`'s 90-day `raw` purge applies as to any other source.

**Correction recorded.** An earlier tentative read of the fetched HTML suggested the page was
RSS-capable. It is not — no `<link rel="alternate" type="application/rss+xml">` exists anywhere
in the source. The correction is kept here so the question is not re-opened.

## 3. B0 investigation checklist

Run this for every source. **Record the answer even when it is "none".** A recorded "none" is
what licenses moving down the ladder; an unrecorded one is a gap.

| # | Question | Why it matters |
|---|---|---|
| 1 | Is there an official API? Documentation URL? | `API` candidate |
| 2 | Authentication: key / OAuth / tokenised URL / login? | Determines the whole security design |
| 3 | Quota and pricing? | Saramin is 500/day; public data portals typically cap daily traffic |
| 4 | **Do the terms permit personal, automated use? Quote the clause, or record its absence, with the URL and the date read** | **The legal basis (NFR-7), and the condition that actually decides whether a source may be scraped** |
| 5 | Is there a feed (RSS/Atom/ICS), public or personal-tokenised? | `FEED` |
| 6 | Is email subscription offered? | `SCRAPE/MAIL` — a peer of scraping, and often cheaper |
| 7 | **`robots.txt` — paste the relevant lines and the date fetched. A 404 is a pass** (RFC 9309 §2.3.1.3) | NFR-7, and §4 condition 1 |
| 8 | **Does the list page render server-side?** `curl` it and look for the rows in the response body | Decides scraping vs. the §4.2 fallback chain. **No headless browser on the server** |
| 9 | **Is there a JSON/GraphQL endpoint the page itself calls?** (DevTools → Network → XHR) | Cheaper and far more stable than HTML parsing |
| 10 | **Is there decided case law or a public dispute about scraping this site?** | JobKorea is the reason this question exists |
| 11 | If none of the above: which rung is the fallback? | `SCRAPE/MAIL`, else `PASTE` — and `PASTE` is a complete answer |

### LMS-specific order — check in this sequence and stop at the first hit

1. **Calendar → "iCal 내보내기" / export / subscription URL.** If present, deadlines are
   solved with no password. Copy the URL; treat it as a secret (`SEC-13` pattern).
2. **Notice board / forum → RSS icon or feed URL.** **Answered 2026-08-25: not supported.**
3. **Site administration → Web services** — is the Moodle Web Services API enabled for
   students? Almost certainly not, but the check costs five minutes and, if enabled, it
   reaches course materials through an official API and **supersedes the agent-side rung
   entirely**. That would be the best available outcome.
   **Answered 2026-08-25: disabled.** The `AGENT` rung (§5) stands as the only path to course
   materials, and it remains conditional.
4. Only if 1–3 all fail: evaluate the **`AGENT`** rung against **§5**.

## 4. Scraping gate — the `SCRAPE/MAIL` rung's scraping half (ADR-022 §2)

**All nine must hold, recorded in §2 with the date checked.** A source failing any condition
**uses the email half of the rung instead, or falls to `PASTE`.** Re-check when a site
redesigns or changes its terms.

| # | Condition |
|---|---|
| 1 | **`robots.txt` permits the exact paths** under `User-agent: *`, with the lines quoted and dated in §2. **A 404 is a pass** — RFC 9309 §2.3.1.3: an unavailable `robots.txt` means any resource may be fetched |
| 2 | **The terms of service contain no prohibition on automated collection** — clause quoted, or absence recorded, with URL and date. **This is the deciding condition, not condition 1** |
| 3 | **Public, unauthenticated pages only.** No login, no session, no paywall, and no path the site's own `robots.txt` scopes to accounts |
| 4 | **Honest `User-Agent`** naming this tool and a contact address. No impersonation of a browser or another crawler, no UA rotation, no proxy rotation. **If a site blocks the honest UA, that source uses email or `PASTE` instead** — a block is an answer, not an obstacle |
| 5 | **Rate limit**: ≥ **3 s** between requests (Wevity's declared `Crawl-delay: 3` is the floor for *every* source), **one run per day**, pagination capped at a configured page count |
| 6 | **Conditional requests** — `If-Modified-Since` / `If-None-Match` — wherever offered, plus the `collector_state` cursor, so a run does not re-walk history |
| 7 | **An empty result is `FAILED`, never `SUCCESS`** — see §4.1. Non-negotiable |
| 8 | **Personal use only.** No redistribution, republication, bulk export, or second consumer. The dashboard is Basic-Auth'd to one person (SEC-001) |
| 9 | **No headless browser on the server.** `ARCH-001` leaves 415 MiB headroom; Chromium costs 300–500 MiB. It is arithmetic, not preference |

### 4.1 Empty result is failure — the operational core

HTML changes silently. A selector that stops matching returns `[]`, the run records `SUCCESS`,
the freshness clock resets, and the dashboard looks healthy while collection is dead. That is
the worst failure class in this project (`PRD-000` §6, `ADR-012`) and it was `ADR-021`'s
strongest argument against scraping. Adopting scraping means answering it.

For **every** scraped source:

- Zero items from a source that has **ever** returned more than zero → that source is `FAILED`
  and the run is `PARTIAL`.
- The **cursor does not advance** on a zero-item result.
- **Two consecutive** zero-item runs raise the `ADR-012` alert.
- A parsed row **missing `title` or `url`** is a failed row, counted, and the count is asserted
  in tests. Silent field-dropping is the same disease as an empty list.

### 4.2 If a page needs JavaScript

In this order — a browser on the node is not on the list:

1. **Call the JSON/GraphQL endpoint the page itself calls.** Cheaper and more stable than
   parsing rendered HTML. Where a page embeds its data as JSON in the HTML itself (Next.js
   `__NEXT_DATA__` and similar), **parse that rather than DOM selectors** — it is typed and far
   more resistant to redesigns.
2. **Run it in the laptop sync agent** (B18) — it has a browser and a screen, and a breakage
   there is a script the owner is watching, not a cluster incident.
3. **Paste** (ADR-018).

---

## 5. Authenticated-fetch gate — the `AGENT` rung

**All five must hold. Record each in the block write-up.**

| # | Condition |
|---|---|
| 1 | The service's terms contain **no prohibition on automated access** |
| 2 | Own account only, and **read-only** — never submit, modify or delete |
| 3 | `API`, `FEED`, `SCRAPE/MAIL` and `PASTE` all checked and recorded as insufficient for this specific need |
| 4 | The friction is **recorded in `usage_events`**, not assumed — the same evidence rule as ADR-018 and B21 |
| 5 | Failure is loud: an empty result is treated as failure, never as success |

**Where it runs**: inside the laptop sync agent (B18). Credentials live in the **OS keychain**
and are **never transmitted to the server**. See ADR-021 §3 and SEC-19.

> Numbered rung **6** in `ADR-021` §1 (its conditions are in `ADR-021` §3), then **7** in
> `ADR-022` §1, now named **`AGENT`** by `ADR-023`. **The five conditions have never changed
> across all three** — which is exactly why it is named rather than numbered.

## 6. Adding a new source later

1. Run §3. Record the result here — including "nothing exists".
2. Pick the highest available rung.
3. If it is `API`, `FEED` or `SCRAPE/MAIL`, it is an adapter behind the existing `Source`
   abstraction (B3). If a new
   source needs more than an adapter, **that is a finding worth recording** — ADR-003's
   one-table claim would be under strain.
4. **If it involves scraping, satisfy all nine conditions in §4 first** and record each in §2.
5. If it is `AGENT`, satisfy §5 first and write an ADR.
6. Add it to the coverage audit rotation (PRD-000 §4.1).
7. Update this table and `REQ-001` §4.

## 7. Quotas, keys, and crawl budget register

Filled in as sources are activated. Keys themselves live in secrets storage (ADR-009), never
here.

| Source | Key held where | Quota / crawl budget | Renewal | Last verified |
|---|---|---|---|---|
| **Worknet / 고용24 (공공데이터포털)** | **k8s Secret (B23)** | *(daily cap — record on first use)* | | **Key received 2026-08-24** |
| **Saramin** | *(B23)* | 500 / day | | **Application submitted 2026-08-24 — approval pending.** Record the pricing answer on approval |
| **LMS calendar ICS** | **k8s Secret (B24)** — base URL + `userid` + `authtoken` **as separate values**, never the assembled URL (§2.1) | n/a | **Rotation pending** — see `docs/incidents/2026-08-24-lms-token-near-miss.md` | 2026-08-24 (export route confirmed live) |
| School notice board | n/a | ≥ 3 s delay, 1 run/day, *(daily page cap + separate backfill cap — B3)* | n/a | 2026-08-24 (`robots.txt` 404, no ToS, no feed, SSR) |
| Wevity | n/a | ≥ 3 s delay, 1 run/day, *(page cap — B26)* | n/a | **2026-08-24 — all nine §4 conditions pass.** ToS cleared by owner's determination; clause text not transcribed |

### `User-Agent` — fixed 2026-08-25

```
schedule-manager/0.1 (personal use; +kimnoell1225@gmail.com)
```

**This is the value. One value, set in one place, honest, no rotation** (§4 condition 4). It is
used by every scraped source — the school notice board (B3) and Wevity (B26) — and B3's
`HttpFetcher` is the one place it is set.

- **The version advances with the project's version**; the contact address does not change
  without a note here. The address is the dedicated collection account, and it is deliberately
  public: it is sent in the header of every request this project makes, which is the point of
  condition 4.
- It must never contain `Claude`, `anthropic-ai`, `GPTBot`, or any other name a site's
  `robots.txt` blocks — **not to evade the block, but because claiming to be a crawler you are
  not is a false identifier.**
- A site that blocks this honest UA sends that source to email or `PASTE`. **A block is an
  answer, not an obstacle.**

## 8. Sources dropped, and why

Kept so a future session does not re-investigate a closed question.

| Source | Dropped | Reason | Would reopen if |
|---|---|---|---|
| KakaoTalk API | 2026-08-22 | Message API is **send-only**; no read endpoint exists in the platform | Kakao publishes a read API |
| Saramin web scraping | 2026-08-22 | Superseded by the official API | never |
| **JobKorea scraping** | 2026-08-20, **re-confirmed 2026-08-24 under ADR-022** | **Decided case law** — 잡코리아 v 사람인, 저작권법 데이터베이스제작자 권리 + 부정경쟁방지법, damages awarded, on scraping job postings from this board. `robots.txt` permitting `/recruit/joblist` does **not** touch database producer's rights. The site also blanket-blocks AI and scraper bots. **Re-examined under a policy that permits scraping, and still excluded** | JobKorea publishes an official API, or changes its terms to permit automated personal collection. **Not on `robots.txt` evidence** |
| **Linkareer scraping** | 2026-08-24 | **Owner's decision.** It was technically viable — `robots.txt` permits the four target list paths, the pages are server-rendered so no browser is needed, and conditions 1, 3 and 9 passed. **The ToS was never read, so condition 2 was never satisfied**, and the source was excluded rather than cleared. Placing a source below the rung the ladder allows is always permitted (§1) | The owner wants the coverage and reads the ToS. Linkareer remains available on the **email half of `SCRAPE/MAIL`** if alerts exist — **whether they do was deferred, unanswered, on 2026-08-30** (`STATUS.md` §6) |
| Campuspick | 2026-08-20 | App-only, no email or feed evidence | a feed or email alert appears |
