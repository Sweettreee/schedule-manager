# REQ-001 — Requirements Specification (v1)

**Version**: v5.0
**Status**: Approved
**Last updated**: 2026-08-22

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-08-20 | Initial |
| v1.1 | 2026-08-20 | Gmail-first channel, Item model, newsletter classification |
| v2.0 | 2026-08-21 | Translated to English; availability metric removed; FR-11 added; NFR-6 rewritten as freshness visibility |
| v3.0 | 2026-08-22 | REVIEW-001 fixes: NFR-1 currency, NFR-2 load condition, NFR-6 fully specified (N=1 + staleness condition), FR-13 incremental collection, FR-14 coverage audit, §2.1 screen structure, §7 freshness SLO |
| v4.0 | 2026-08-22 | ADR-017 scope expansion: all three capabilities enter v1. FR-15…FR-22 added (RSS, paste ingest, time view, reminders, search, file locker, sync agent, version history). NFR-12 file-transfer constraint |
| v5.0 | 2026-08-22 | ADR-021 source channel ladder. **Saramin corrected from *Excluded* to an official API.** Worknet and LMS iCalendar added. FR-24…FR-27, NFR-15, NFR-16 |

## 1. Scope of v1

**v1 = Schedule Manager: one place that collects what matters, shows it on a time axis with
reminders, lets it be searched, and keeps files in sync.**

All three capabilities named in PRD-000 §2 are in v1, each at its **first genuinely useful
level** (ADR-017). This replaces the earlier "collection only" scope from ADR-001.

| Capability | v1 level | Deferred |
|---|---|---|
| **Ingest** | Gmail, school-notice RSS, **official APIs (Worknet, Saramin)**, **LMS iCalendar**, paste/screenshot | LMS-authenticated file download (**B25, conditional**) |
| **Time output** | Week/month view, deadline reminders | Recurring events (`rrule`) |
| **Content output** | Trigram substring search | Korean morphology, embeddings |
| **Files** | L0 web locker + L1 one-way laptop agent | L2 pull sync, L3 two-way with conflict resolution |

v1 must be both a learning vehicle and a tool that is actually used daily. Satisfying only
one of the two counts as failure.

| What v1 produces | Learning value | Practical value |
|---|---|---|
| Gmail + RSS collectors | OAuth2, token lifecycle, feed parsing | Nothing is missed |
| Paste/screenshot ingest | Structured extraction, human-in-the-loop design | Sources with no API are still captured |
| Time view + reminders | Interval modelling, idempotent scheduled delivery | **까먹지 않는다** — the stated core need |
| File sync L0/L1 | **S3, prefix-scoped IAM, presigned URLs, content addressing, client agent state** | 수업자료가 한 곳에 |
| k3s on EC2, self-managed | Networking, containers, orchestration, IaC | Reachable from anywhere |
| CI/CD + GitOps | Delivery automation, Flux | Improvements ship continuously |
| Unified Item model | Data modelling, extensible schema | Time view, search and files reuse it directly |
| A screen worth opening daily | — | Habit formation |

## 2. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Collect Gmail notifications and newsletters automatically on a schedule | Must |
| FR-2 | Allow the user to add and remove collection sources (subscriptions) | Must |
| FR-3 | Filter collected items by rule (see §2.2) | Must |
| FR-4 | Deduplicate items | Must |
| FR-5 | Show all items in one list (pull model, no push) | Must |
| FR-6 | Visually distinguish items with an approaching deadline | High |
| FR-7 | Let the user save items of interest | Medium |
| FR-8 | Notifications to the user | Low — v2+ |
| FR-9 | Classify newsletters into four tabs and display them (see §2.3) | Must |
| FR-10 | Let the user configure the collection interval (default 24h, range 1–24h) | Must |
| FR-11 | Record usage signals needed for PRD-000 metrics: daily access, "entered manually" count | Must |
| FR-12 | Always display the timestamp of the last successful collection, **and show a warning banner when it is stale** (see NFR-6) | Must |
| FR-13 | **Collect incrementally** — each run fetches only messages newer than the last successful collection point, which is persisted | Must |
| FR-14 | Provide a screen to record a **coverage audit** result (PRD-000 §4.1): source, checked count, found count, note | Must |
| FR-15 | Collect **school notices via RSS** into the same `items` table, using the same dedup and run-recording path as Gmail | Must |
| FR-16 | Accept **pasted text or a dropped screenshot**, extract structured fields, and present them for **mandatory user confirmation** before saving (ADR-018) | Must |
| FR-17 | Enforce a **monthly cap on extraction calls** (default 300); on reaching it, disable extraction and alert rather than spend | Must |
| FR-18 | Show a **time view** (week and month) of items with `starts_at` or `due_at`, rendering all-day items as dates (ADR-019) | Must |
| FR-19 | Let the user set **reminders** relative to an item's deadline, delivered via the ADR-012 webhook path and shown in the dashboard. Regenerate pending reminders when a deadline changes | Must |
| FR-20 | **Unified search** across title, organisation, body and file path, returning items of every type in one result list | Must |
| FR-21 | **File locker (L0)**: upload and download files in the browser. Bytes transfer **directly between client and object storage**; a file already stored is linked without re-uploading (ADR-020) | Must |
| FR-22 | **Sync agent (L1)**: watch a folder on the laptop and upload changes automatically, with crash-safe local state and idempotent retry | Must |
| FR-23 | **Version history**: every upload of a path is retained as a version, and any version can be restored | High |
| FR-24 | Collect from **official public APIs** (Worknet, Saramin) by query — keyword, region and date window configurable without a code change (ADR-021) | Must |
| FR-25 | Respect each source's **published quota** with a code-level guard; a quota stop records `PARTIAL`, not `FAILED` | Must |
| FR-26 | Import **LMS deadlines from an iCalendar feed**, mapping `DTSTART`/`DTEND`/all-day to `starts_at`/`due_at`/`all_day` (ADR-019, ADR-021) | Must |
| FR-27 | Any **authenticated fetch** runs in the laptop agent with credentials in the OS keychain, never transmitted to or stored on the server (ADR-021 §3) | Must, if built |

### 2.1 Screen structure (clarifies FR-5, FR-6, FR-9)

One list screen. Its controls, and which column each maps to:

| UI element | Backed by | Notes |
|---|---|---|
| Four tabs across the top | `items.category` | 취업정보 / 자기계발칼럼 / 테크칼럼 / 미분류. Default tab: 취업정보 |
| A badge on each row | `items.type` | NEWSLETTER / JOB / CONTEST — so non-newsletter items are visible inside the tabs rather than hidden |
| Row highlight | `items.due_at` | D-3 or less: strong highlight. D-7 or less: mild. No `due_at`: none |
| Pin/star toggle | `items.extra->>'saved'` | FR-7 |
| Header strip, always visible | `collection_runs` | "마지막 수집: 2026-08-22 09:00 (3시간 전)" + warning banner when stale |
| Sort | `occurred_at` desc (default), `due_at` asc | `is_cloud` items sort to the top within the chosen order (FR-3) |
| Date-range filter | `occurred_at` | |

Items whose `type` is not `NEWSLETTER` are **not** assigned a `category` and are reachable
only via the 취업정보 tab's "전체" toggle and via search. See DATA-001 §"category semantics".

### 2.2 FR-3 filter rules

- **Include**: `is_cs == true` (regardless of AI relevance)
- **Exclude**: `is_ai == true AND is_cs == false` (e.g. AI-ethics essay contests)
- **Sort to top**: `is_cloud == true`

These rules are fully specified, so they are implemented test-first (ADR-010).

### 2.3 FR-9 classification

- Values: `JOB_INFO` / `CAREER_COLUMN` / `TECH_COLUMN` / `UNCLASSIFIED`
- Korean UI labels: 취업정보 / 자기계발칼럼 / 테크칼럼 / 미분류
- Default tab: `JOB_INFO`
- v1 classifies by sender-address rules (zero cost, high precision)
- **Classification is attempted only for `type = 'NEWSLETTER'`.** Every other type keeps
  `category = NULL`, meaning "not a classification target". This matters because block B21
  decides whether to adopt AI based on how much genuinely *failed* classification, and
  counting non-targets would corrupt that evidence.
- Unmatched newsletters accumulate as `UNCLASSIFIED`; once enough have accumulated,
  evaluate AI classification (roadmap block B21)

## 3. Non-functional requirements

| ID | Requirement | Value |
|---|---|---|
| NFR-1 | Monthly operating cost | **≤ 30,000 KRW**, evaluated at the FX assumption recorded in ARCH-001 (currently 1 USD = 1,400 KRW → effective ceiling ≈ **USD 21.4**). Breaching *either* the KRW figure or the USD figure triggers the escalation ladder in OPS-001 §3 |
| NFR-2 | Dashboard response | **p95 < 2s** for the list screen with **10,000 rows in `items`**, measured from the EC2 node's public URL, cold cache |
| NFR-3 | Collection interval | Default 24h, user-adjustable 1–24h |
| NFR-4 | Partial failure | Allowed; remaining sources continue, run marked `PARTIAL` |
| NFR-5 | Deployment | Push to `main` → automatic deploy |
| NFR-6 | **Freshness visibility and alerting** | See §3.1 — fully specified, replaces the previous "99% availability" target |
| NFR-7 | Legal | Respect robots.txt and terms of service |
| NFR-8 | Channels | Gmail primary, RSS secondary, scraping last resort (ADR-002) |
| NFR-9 | Authentication | The dashboard is publicly reachable and contains personal mail content; it must not be exposed without authentication (SEC-001) |
| NFR-10 | Data retention | Raw message bodies deleted after 90 days, **in backups as well as in the live database** (SEC-001) |
| NFR-11 | Recovery objectives | **RPO ≤ 24 hours, RTO ≤ 4 hours** (OPS-001 §5) |
| NFR-12 | File transfer | File bytes **never pass through the API node**. Upload and download use presigned URLs directly against object storage (ADR-020). A 2 GiB node must not be able to be killed by a large file |
| NFR-13 | File storage budget | Design point **5 GB**; alarm at **10 GB**. Egress alarmed separately — the realistic failure is a retry loop, not usage |
| NFR-14 | Extraction privacy | Pasted content may contain **third parties' messages**. Only the extraction call may receive it; never logs, metrics or traces. Provider must carry a no-training-on-input commitment (SEC-001) |
| NFR-15 | Channel selection | Every source uses the **highest available rung** of the ADR-021 ladder. A lower rung requires the higher ones to be checked and recorded as unavailable in `SOURCES-001` |
| NFR-16 | Credential locality | **No credential granting access to a university or commercial account is ever stored on the server.** Such credentials live only in the laptop's OS keychain (ADR-021 §3, SEC-19) |

### 3.1 NFR-6 — freshness, fully specified

The dashboard must never look healthy while collection is dead. Three mechanisms, and all
three are required because each covers a failure the others miss.

| # | Mechanism | Condition | Catches |
|---|---|---|---|
| A | **Failure alert** | The most recent `collection_runs` row has `status = 'FAILED'` → alert immediately (**N = 1**, not N > 1) | The collector ran and failed |
| B | **Staleness alert** | `now() - last_success > collection_interval × 1.5` → alert | The collector ran but produced nothing; scheduling drift |
| C | **Dead man's switch** | The collector pings an **external** service on every success. No ping within the grace period → the **external** service alerts | The collector never ran at all — node down, k3s down, CronJob deleted. Neither A nor B can fire in this case, because nothing is running to evaluate them |

Alerts go to a Discord webhook (OPS-001 §4). Mechanism C is specified in **ADR-012**.

**N = 1 rationale**: at the default 24-hour interval, requiring two consecutive failures
means at least 48 hours of silence before anyone is told. For a deadline-tracking system,
48 hours is long enough to miss the thing the system exists to catch.

**FR-12 is the fourth layer, for the user**: the dashboard shows the last successful
collection time on every page, and when condition B holds it shows a red banner at the top.
The banner exists because the header timestamp alone requires the user to notice a number —
and PRD-000 says the user's problem is precisely that they stop checking once they feel safe.

## 4. Source status

| Source | Status | v1 handling |
|---|---|---|
| **University notices** | RSS likely; channel identified in **B0**, consumed in **B3** | **Core source**, not an extensibility test |
| **LMS deadlines** | Moodle **iCalendar export URL** — tokenised, no password (ADR-021) | **B24** |
| **LMS notices** | Moodle forum RSS | B24 |
| **Worknet / 고용24** | **공공데이터포털 공식 API** (한국고용정보원) | **B23** — legally the cleanest source in the project |
| **Academic calendar** | A page updated once a semester, not a feed | **Paste channel** (B6). Polling two changes a year is not worth a scraper |
| **KakaoTalk (club / department)** | **No read API exists** — the Kakao Message API is send-only | **Paste / screenshot** (B6, ADR-018) |
| Wevity | Category-based mailing confirmed | Subscribe immediately (B0) |
| Linkareer | Email alerts unconfirmed | User to verify after login (B0) |
| JobKorea | Job alert emails exist; scraping prohibited | Email only (B0) |
| **Saramin** | **Official Open API** — `oapi.saramin.co.kr`, 500 calls/day (ADR-021) | **B23.** *Previously excluded in error: scraping being prohibited is not the same fact as no API existing* |
| Campuspick | App-only, no email evidence | Excluded from v1 |
| Course material files | Local folder watched by the sync agent | **B18**. Getting files into the folder is manual unless **B25**'s gate passes |

## 5. Data model

All collected items are normalised into the `items` table. See `DATA-001` for the schema
and `ADR-003` for the rationale.

## 6. AI in v1 — two different problems, two different answers

| | Newsletter **classification** | Paste **extraction** (FR-16) |
|---|---|---|
| Input | Mail from a known sender, same template weekly | Arbitrary human writing: *"담주 화욜 3시 동방에서 회의"* |
| Can a rule work? | **Yes** — sender address alone gets most of it, free and exact | **No.** There is no format to write a rule against |
| Is more evidence needed to decide? | **Yes** | **No.** The input is already known to be unstructured |
| v1 answer | **Rules only.** LLM deferred to block B21 | **LLM, with mandatory human confirmation** |

The principle is *"decide from evidence"*, not *"delay by default"*. Waiting makes sense when
a cheap solution might turn out to be sufficient; here it is known in advance not to be.
Full reasoning in **ADR-018**; the classification decision remains as originally specified and
is made at block B21 with real `UNCLASSIFIED` volume.

## 7. Service level objective

PRD-000 §5 removes availability as a goal. It does not remove the need for a measurable
target — it moves the target from *"is the site up"* to *"is the data fresh"*.

> **SLI**: the fraction of one-minute samples in a calendar month for which
> `now() − last_successful_collection < 30 hours`.
>
> **SLO**: **99% per calendar month.**
> Error budget: about **7 hours 18 minutes** of staleness per month.

Implications, and why this is worth defining:

- The dashboard being unreachable does **not** burn error budget. Collection stopping does.
  That is exactly the priority PRD-000 states.
- 30 hours = the 24-hour interval plus 25% slack, so an ordinary late run does not burn
  budget but a skipped day does.
- When the budget is exhausted in a month, the next block's first task is reliability work,
  not features. This is written into `OPS-001` §7.
- Measured from the same VictoriaMetrics series that drives alert B (ADR-013), so the SLO
  and the alert cannot disagree.
