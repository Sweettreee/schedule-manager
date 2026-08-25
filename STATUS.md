# STATUS — Project Status

**Last updated**: 2026-08-25
**Current stage**: **B0 complete except its email subscriptions. B1 is the next block.**
The last three non-mail items closed on 2026-08-25: the LMS does not support forum RSS, Moodle
Web Services is disabled for students, and the crawler `User-Agent` is fixed. The documentation
set was consolidated earlier the same day so that each rule has one authoritative home (§8).
**Next action: B1 — Gmail OAuth.**

> **Claude Code, start here.** Read `CLAUDE.md` in full, then this file, then
> `docs/BLOCKS-001-roadmap.md`, then the spec for the current block in `docs/blocks/`.
> Do not read past the current block's spec.

## 1. Next action

**B1 — Gmail OAuth and reading mail locally.** Spec: `docs/blocks/B0-B8-specs.md` §B1.
**Before starting, reconfirm Google's OAuth publishing rules and start the ADR-007 two-day
clock** (§4 item 12). The app lane runs B1 → B2 → B3, and no code exists yet.

**B0's remaining work is its email subscriptions, and it rides along with B1.** The dedicated
collection Gmail account is B1's account too, so creating it, enabling 2FA and subscribing
(JobKorea's alert above all — it is that source's only channel) happens naturally at the start
of B1. Everything else B0 owed is closed (§1.1).

**B3 is unblocked on evidence but not yet startable** — it needs B2's pipeline and schema to
have a table to write into. B26 follows B3. When the app lane waits on data volume, work the
infra lane (`BLOCKS-001` §2).

### 1.1 Where the B0 findings live

**`SOURCES-001` §2 — the source matrix — is the record**, with a dated rung and a dated
terms-of-service finding per source. It was being duplicated in five files; it is now in one.

Resolved: school notice board ✅ `SCRAPE/MAIL` (**B3 unblocked**) · LMS calendar ICS ✅ `FEED`
(**B24**) · **LMS forum RSS ✅ answered 2026-08-25 — not supported** · **LMS Web Services ✅
answered 2026-08-25 — disabled** · **crawler `User-Agent` ✅ fixed 2026-08-25** · 고용24 key ✅
received (**B23 startable with one source**) · Linkareer scraping excluded by owner decision ·
Wevity gate ✅ passed (**B26 unblocked**).

**Two of the 2026-08-25 answers were negative, and both changed the roadmap.** No forum RSS
means **no RSS source exists anywhere in this project**, so B24 drops to ICS only and **no RSS
adapter is ever written** (`SOURCES-001` §1.1); LMS course notices fall to `PASTE` (B6). Web
Services being disabled leaves the conditional `AGENT` gate (§5, B25) as the only path to course
materials.

**Still owed by B0: §4 items 3 and 4 — the email subscriptions, and nothing else.**

### 1.2 What B0 asked for, restated

B0's product changed on 2026-08-24. It was *"subscribe to sources, find out whether a feed
exists"*. It is now **"produce the evidence that decides each source's rung"** — a dated
`robots.txt` snapshot and a **quoted terms-of-service clause** for every candidate source.
Subscriptions still happen (Gmail is kept as a redundant channel), but they are no longer the
acceptance criterion.

Of the three items that blocked downstream work, **two are resolved** (§1.1): the school board
`curl` check ✅ and Linkareer's render question ✅. **Wevity's terms of service is the one that
remains**, and it decides whether B26 exists at all.

The full remaining list is §4. B0 is *started*, not finished: data accumulates from day one and is the input to B4 and B20.
Once B0's repository work is committed, three tracks run in parallel
(`docs/BLOCKS-001-roadmap.md` §2) — when the app track waits for data volume, work the infra
track.

**Nothing is blocking B0. Start today.**

## 2. What this project is

**Schedule Manager** — a personal information hub with three capabilities over one `items`
table, in the owner's priority order:

| Priority | Capability | v1 level |
|---|---|---|
| 1 | Schedules and materials in one place, with reminders | Week/month view + deadline reminders (B7) |
| 2 | Unified search | Trigram substring search (B8) |
| 3 | Job postings and newsletters | **Official APIs + scraping** + Gmail + paste (B23, B3, B26, B2, B6) |
| — | **File synchronisation** — also the richest cloud curriculum here | L0 locker (B14) + L1 laptop agent (B18) |

## 3. Decided — index

**This is a navigation index, not a second source of truth.** Each row names a decision and where
it lives; the reasoning is in the reference and nowhere else. If this table and a referenced
document disagree, **the document wins** — this one is hand-maintained and will drift.

| Area | Decision | Reference |
|---|---|---|
| Problem | Input cost, fear of missing items, scattered material — root cause is manual data transport | PRD-000 |
| **v1 scope** | All three capabilities at their first useful level, plus file sync L0+L1 | **ADR-017** |
| **Channel ladder** | `API` → `FEED` → `SCRAPE/MAIL` → `PASTE`, plus conditional `AGENT`. **Named, not numbered** | **SOURCES-001 §1** (authority); ADR-022, ADR-023 |
| **Scraping** | Permitted behind a nine-condition gate whose deciding condition is the **ToS**, not `robots.txt` | **SOURCES-001 §4**; ADR-022 |
| **Empty result = failure** | Zero items from a source that has ever returned more is `FAILED`; the cursor does not advance | REQ-001 NFR-17 |
| **Scope parameters asserted** | A truncated result returns 200, parses, and is non-empty — NFR-17 does not catch it | REQ-001 NFR-19 |
| **No browser on the node** | Chromium 300–500 MiB vs 415 MiB headroom. Arithmetic, not preference | ADR-022 §4, ARCH-001 |
| JobKorea | Email only, on decided case law — re-examined under a permissive policy and still excluded | SOURCES-001 §8 |
| Linkareer | Scraping excluded by owner decision, ToS unread. Email only, or dropped | SOURCES-001 §8 |
| Credential locality | No university or commercial account credential is ever stored on the server | ADR-021 §3, SEC-19 |
| Data model | Single `items` table, shared columns + `extra jsonb`; `UNIQUE(source, source_id)` | ADR-003, DATA-001 |
| Time model | `starts_at` + `due_at` as an optional-ended interval; `all_day`; reminders as rows | ADR-019 |
| File sync | Content-addressed blobs in S3; presigned direct transfer; bytes never touch the node | ADR-020 |
| KakaoTalk | No read API exists. Paste/screenshot with LLM extraction and mandatory confirmation | ADR-018 |
| AI in v1 | Extraction yes; classification deferred to B21 | ADR-018, REQ-001 §6 |
| Guiding principle | DP-1 control over convenience, with three exceptions | ADR-004 |
| Platform | k3s on one EC2 `t4g.small`, Seoul; self-managed PostgreSQL and ingress | ADR-005 |
| Stack | FastAPI + Next.js, two containers; SQLAlchemy + Alembic | ADR-006 |
| Gmail auth | OAuth `gmail.readonly`, published app; 2-day timebox then IMAP fallback | ADR-007 |
| Repos | Two repositories + Flux, split at B16 | ADR-008 |
| Secrets | k8s Secrets first, SOPS + age from B16 | ADR-009 |
| Testing | Conditional TDD; unit plus three integration paths; no browser E2E | ADR-010 |
| Container registry | ghcr.io, private, free. ECR prohibited | ADR-011 |
| Collector liveness | External dead man's switch + internal alerts + banner. N = 1 | ADR-012 |
| Observability | VictoriaMetrics single-node, 7-day retention; Grafana on demand | ADR-013 |
| Data durability | Separate EBS data volume, delete-on-termination = false | ADR-014 |
| Migrations | Forward-only; every migration backwards compatible with the previous release | ADR-015 |
| Terraform | Import over rebuild; S3 state, no DynamoDB | ADR-016 |
| **Scheduled shutdown** | **Instance stopped 02:00–08:00 KST by design; one attached Elastic IP; collector at 08:05** | **ADR-024** |
| Dashboard auth | Basic Auth at ingress | SEC-001 |
| Retention | `raw` purged after 90 days, in backups too | SEC-001 |
| Backups | Daily `pg_dump` to S3; RPO ≤ 24h, RTO ≤ 4h | OPS-001 |
| **Cost** | **Design ≈ $18.3 ≈ 25,600 KRW**, inside the 30,000 ceiling — **only with the shutdown**. List price without it: ≈30,900 KRW | ARCH-001, ADR-024 |
| Availability | Not a metric — replaced by a freshness SLO: 99%/month at a 30-hour threshold | REQ-001 §7 |
| Measurement | M-2 measured by weekly coverage audit: ≥90% per source, none below 70% twice | PRD-000 §4.1 |
| Failure drills | Eight GameDay drills attached to blocks B12–B19 | GAMEDAY-001 |
| Target role | Cloud / DevOps / SRE | BLOCKS-001 |

## 4. Open — needs the owner to act

1. **⚠ Rotate the LMS calendar token.** A live `authtoken` was exposed in a chat transcript on
   2026-08-24 — see `docs/incidents/2026-08-24-lms-token-near-miss.md`. No system was
   compromised, but the token is a **read credential for the personal LMS calendar** and the
   exposure window stays open until it is rotated. Do this on `/calendar/export.php` **before
   B24 wires it into anything.** If the theme has removed the reset control, **that is itself a
   finding** — record it in `SOURCES-001` §2.

2. **⚠ Choose a domain name and DNS provider. Needed by B12.** *(Raised 2026-08-25.)*
   **No document in this set names a domain, a registrar or a DNS provider**, yet `SEC-2`,
   `ARCH-001` and the B12 spec all require TLS from Let's Encrypt via cert-manager — and an ACME
   challenge needs a hostname. This was invisible until `ADR-024` made the address stable enough
   to point a name at. Decide: the domain, where DNS is hosted, and whether the ~$12–15/year
   registration goes into the `ARCH-001` cost model. **B12 cannot start without it.**

3. **Dedicated collection Gmail account, and the JobKorea job-alert subscription.** JobKorea is
   **email-only** (`SOURCES-001` §8), so this subscription is not optional — without it that
   source has no channel at all. Create the account with 2FA and recovery options first: if it
   is lost, the whole mail channel is lost. **The last thing B0 owes, together with item 4.**
   Happens at the start of **B1**, which uses the same account.

4. **Wevity email alerts, and whether Linkareer offers alerts at all.** Wevity's is deliberate
   redundancy alongside the B26 scraper; **Linkareer's is now its only remaining channel** — if
   none exists, that source is dropped entirely (`SOURCES-001` §8).

5. **사람인 API key** — approval pending. Record the pricing answer on approval, in
   `SOURCES-001` §7; the guide does not publish it.

6. **Remaining source investigation** — `SOURCES-001` §3 for the academic calendar and anything
   still unrecorded.

7. **Discord webhook** — create the channel and webhook URL. Needed for **B7** (reminders) and
   **B13** (alerting).

8. **healthchecks.io account and check** — free tier, one check, 30-hour grace. Needed for
   **B13** (ADR-012).

9. **LLM provider choice** — evaluate against real Korean date expressions; record price and
   the no-training-on-input commitment. Needed for **B6** (ADR-018, SEC-15).

10. **AWS student programme** — confirm whether any grants credits on a *real* personal
    account. Educate and Academy labs cannot host this. Needed for **B10**.

11. **Seoul region pricing** — confirm in the Pricing Calculator during **B10**.

12. **Google OAuth publishing rules** — reconfirm at the start of **B1**; start the 2-day clock.
    **This is the immediate next action.**

### Not blocking, but owed for completeness

- **Wevity's terms-of-service URL.** Condition 2 is **passed** — the terms were read on
  2026-08-24 and contain no automated-collection clause, which is a complete answer in the same
  form as the school board's. Pasting the URL into `SOURCES-001` §2 lets a future session
  re-check the finding without re-deriving it. **B26 proceeds either way.**

## 5. Dates to record (fill in at B10)

**The credit expiry date is the most important operational date in this project** — on that
day the monthly bill goes from 0 to about $22 with no warning from AWS.

| Field | Value |
|---|---|
| AWS account created | *(YYYY-MM-DD)* |
| Credits received | *(USD)* |
| **Credit expiry date** | *(creation + 12 months)* |
| 60-day pre-expiry review | *(expiry − 60 days)* — OPS-001 §3 |
| EC2 instance id | |
| Root / data volume ids | |
| S3 bucket name | |
| **Elastic IP — allocation id and address** (ADR-024) | |
| **Shutdown schedule created (mechanism + rule name)** | |
| SSH key fingerprint | |
| Availability zone | |

## 6. Open — decide later, with a trigger

**This is the register of every deferred decision in the project — as pointers.** The reasoning
for each sits in the document that deferred it, usually that ADR's own "Open questions" section,
**which is authoritative**. Three separate lists of deferred work used to exist with no stated
hierarchy; this is the index to one of them.

| Question | Revisit when | Recorded in |
|---|---|---|
| **Domain name / DNS provider** | **Before B12** — cert-manager cannot issue without a hostname | §4 item 2, SEC-2 |
| File sync **L2** (pull to a second device) | The owner wants a file on the iPad that is not there | ADR-020, BLOCKS-001 §9 |
| File sync **L3** (two-way, conflict resolution) | The first real divergence appears in `file_versions` | ADR-020, BLOCKS-001 §9 |
| LMS-authenticated download | L1 in daily use, and the LMS turns out to permit it | ADR-020, BLOCKS-001 §9 |
| Class timetable recurrence (`rrule`) | A semester proves annoying to maintain as individual rows | ADR-019, BLOCKS-001 §9 |
| Semantic / embedding search | B22 shows lexical search is the bottleneck, not the index | BLOCKS-001 §9 |
| Cross-source deduplication via `content_hash` | **B26 + one month**, with counts — Wevity arrives by email *and* scraper by design | ADR-003, ADR-022 |
| Korean full-text search approach (`pg_trgm` / `pg_bigm` / external) | B22, against real queries | ADR-003, DATA-001 |
| AI classification | B21, once newsletter `UNCLASSIFIED` volume is known | ADR-018, REQ-001 §6 |
| Relaxing the paste confirmation step | Only with measured precision — **never for `due_at`** | ADR-018 |
| Blob garbage-collection policy | B19, with real unreferenced-blob counts | ADR-020 |
| S3 storage class for old semesters | First monthly review after B14 | ADR-020 |
| Large-file multipart threshold | B18, against actual lecture-video sizes | ADR-020 |
| **B25 — agent-side authenticated LMS fetch** | All five gate conditions met — especially #4, that manual downloading is a *measured* weekly cost. **Now the only path to course materials** — Web Services is disabled (2026-08-25) | SOURCES-001 §5 |
| Whether Linkareer returns at all | The owner wants the coverage and reads the ToS | SOURCES-001 §8 |
| Re-reading each scraped source's terms of service | First monthly review, with the real cost of the check known | ADR-022, OPS-001 §7 |
| Dropping Worknet if it adds no unique items | One month after B23, by coverage overlap | ADR-021 |
| Shared retry/backoff layer in `Source` | When the second API adapter is written (B23) | ADR-021 |
| Alerting on `PARTIAL` runs | B17, once `PARTIAL` frequency is known | ADR-012 |
| kube-state-metrics; 7-day retention sufficiency | After the first monthly review, if headroom allows | ADR-013 |
| EBS snapshots in addition to `pg_dump` | B13, once dump sizes are known | ADR-014 |
| CI check rejecting non-empty `downgrade()` | B16 | ADR-015 |
| `mkfs`/`fstab` in user-data vs a documented manual step | B15 | ADR-016 |
| Reserved Instance (lever 2) vs the current shutdown | 60 days before credit expiry, with measured figures | ARCH-001, ADR-024 |
| **Whether the 02:00–08:00 window costs an M-3 day** | First monthly review, with real `DASHBOARD_OPEN` data | ADR-024, OPS-001 §7 |

### 6.1 Closed by answer — kept because the questions shaped decisions

`REVIEW-001` (2026-08-21) ended with five things its author could not decide. All five were
answered, and each answer became a decision. They are kept here because **the questions explain
why those ADRs exist**, and the review document itself was deleted on 2026-08-25.

Quoted verbatim from `REVIEW-001` Part 6 — *"내가 판단할 수 없어 남겨두는 항목이다"*:

| # | The question, as asked | How it was answered |
|---|---|---|
| 1 | **B12 관측성 방식** — VictoriaMetrics 자체 운영(a) / 외부 무료 티어(b) / 인스턴스 상향 + 야간 정지(c) 중 어느 쪽인가 | **(a)** — `ADR-013`: VictoriaMetrics single-node, Grafana on demand. Option (c)'s nightly stop later returned on its own merits as `ADR-024`, on the `t4g.small` rather than a larger instance |
| 2 | **데이터 소실 허용 범위** — "노드 장애 = 전체 중단"은 수용했는데, **데이터 소실도 수용하는가?** | **No.** `ADR-014`: a separate EBS data volume with `delete-on-termination = false`. `ADR-005` now says explicitly that outage is accepted and data loss is not |
| 3 | **환율 가정** — NFR-1의 30,000원을 어떤 환율 기준으로 관리할 것인가 | **1 USD = 1,400 KRW**, recorded in `ARCH-001` and reviewed monthly. Breaching *either* the KRW or the USD figure triggers the `OPS-001` §3 ladder |
| 4 | **Dead man's switch의 외부 의존 수용 여부** — ADR-004(DP-1) 위반인가, 예외 1인가 | **Exception 1.** `ADR-012`: a self-hosted watchdog on the same infrastructure provides false assurance, which is more dangerous than none |
| 5 | **STATUS Open 1번(대학 이름)** — 왜 미해결로 남아 있는지 | Closed. The university is 충북대; the LMS is `lms.chungbuk.ac.kr` and the notice board `www.cbnu.ac.kr` (`SOURCES-001` §2) |

## 7. Document index

45 files. **No document restates the channel ladder, either gate, or the B0 findings** — those
live in `SOURCES-001` and everything else links.

| Document | Status |
|---|---|
| README.md | Current |
| CLAUDE.md | Current — hard rules only; policy is pointed to, not restated |
| WORKFLOW.md | Current |
| STATUS.md | This document |
| .gitignore | Current |
| docs/PRD-000-problem-definition.md | Approved |
| docs/REQ-001-requirements.md | **v6.0**, approved — LMS notices row corrected to `PASTE`/B6 |
| docs/DATA-001-item-schema.md | Approved (rev. 4 — `SCRAPE` enum; file tables provisional) |
| docs/ARCH-001-target-architecture.md | Approved — cost model rebuilt on ADR-024 |
| docs/SEC-001-security-baseline.md | Approved |
| docs/OPS-001-cost-guardrails.md | Approved |
| **docs/SOURCES-001-channel-policy.md** | **Approved — the authority for the ladder (§1), the scraping gate (§4), the `AGENT` gate (§5) and the source register (§2)** |
| docs/GAMEDAY-001-failure-drills.md | Approved, 8 drills |
| docs/BLOCKS-001-roadmap.md | Approved — **B24 reduced to ICS only** |
| docs/PROMPTS-001-plan-review.md | Reusable review prompt **+ the REVIEW-001 scoring rubric** |
| docs/blocks/B0-B8-specs.md | Approved — B0 owes only its email subscriptions |
| docs/blocks/B10-B11-specs.md | Approved — decisions marked **[DECIDED]**, defaults marked *[EXAMPLE]* |
| docs/blocks/B23-B25-specs.md | Approved — **B24's forum-RSS half removed** |
| docs/blocks/B26-spec.md | Approved — Wevity only |
| docs/incidents/README.md | Template |
| docs/incidents/2026-08-24-lms-token-near-miss.md | **Near-miss — token rotation pending (§4 item 1)** |
| docs/adr/ADR-000-template.md | — |
| docs/adr/ADR-001 | Accepted, **amended by ADR-017** |
| docs/adr/ADR-002 | Accepted, **extended by ADR-021, amended by ADR-022** |
| docs/adr/ADR-003 … ADR-020 | Accepted (ADR-005 amended by ADR-014; ADR-013 cross-references ADR-024) |
| docs/adr/ADR-021 | Accepted — **§1's ladder fully superseded by ADR-022 + ADR-023**; §3 still governs |
| docs/adr/ADR-022 | Accepted — scraping permitted, nine-condition gate. **§1 restructured by ADR-023** |
| **docs/adr/ADR-023-named-channel-rungs.md** | **Accepted** — rungs named, `FEED` and `SCRAPE/MAIL` merged |
| **docs/adr/ADR-024-scheduled-shutdown.md** | **Accepted** — 02:00–08:00 KST stop, Elastic IP, NFR-1 satisfied |

**Deleted 2026-08-25**: `docs/REVIEW-001-plan-assessment.md`, `docs/REVIEW-002-prompt-driven-review.md`.
Both self-declared all findings applied. The rubric moved to `PROMPTS-001`; the five open
confirmations moved to §6.1; the events remain in §8. See `PROMPTS-001` §"Applying the output"
for why a review is an event rather than an artefact.

## 8. Revision log

| Date | Change |
|---|---|
| **2026-08-25 (pm)** | **B0's last three non-mail items answered, and two of the answers were negative.** **(1) The LMS does not support forum RSS.** It was the project's last RSS candidate, so **no RSS or Atom source exists anywhere in this project** — a closed finding, not a gap (`SOURCES-001` §1.1). Consequences: **B24 drops from "LMS calendar ICS + forum RSS" to ICS only**, **no RSS adapter is written anywhere** (B23-B25-specs §B24 items 4 and 7 deleted), and **LMS course notices fall to `PASTE` (B6)** — the next rung down is `SCRAPE/MAIL`, but the course boards are behind a login and scraping behind a login is permanently prohibited. **`source = 'RSS'` is kept in the DATA-001 enum, deliberately and unused**: migrations are forward-only (ADR-015), an unused enum value costs nothing, and adding one later costs a migration. **(2) Moodle Web Services is disabled for students**, so it does not supersede the `AGENT` rung as ADR-021 §186 hoped — the conditional §5 gate (B25) is the only remaining path to course materials. **(3) The crawler `User-Agent` is fixed**: `schedule-manager/0.1 (personal use; +kimnoell1225@gmail.com)`, recorded in `SOURCES-001` §7 as the single value, set in one place by B3's `HttpFetcher` — **B3's condition-4 blocker cleared**. **No ADR was written**: these are B0's product — evidence — and the roadmap change follows from the evidence rather than from a decision. **B0 now owes only its email subscriptions** (§4 items 3–4), which ride along with B1. **Next action moves from B3 to B1** — B3 was unblocked on evidence, but the app lane is B1 → B2 → B3 and no code exists |
| **2026-08-25** | **Documentation consolidated.** No decision reversed; four were *made* because the consolidation surfaced contradictions. **Duplication removed**: the channel ladder existed in 8 places, the scraping gate in 4, the empty-result rule in 6, the B0 findings table in 5 — each now has one authority (`SOURCES-001`, `REQ-001`, `ADR-010`, `ADR-018`) and pointers elsewhere. **Defects fixed**: `FR-15` still mandated RSS for a board proven to have no feed; `B23`'s acceptance criterion named an RSS source that does not exist at B23; three stale cross-references in `B23-B25-specs`; `ADR-021`'s supersession note contradicted `ADR-023`; `PRD-000` M-2 carried two different targets. **New decisions**: **`ADR-023`** extracted `ADR-022`'s same-day self-revision into its own record, because one file held two contradictory ladders; **`ADR-024`** adopted the 02:00–08:00 KST shutdown into the design, which brings the cost from ≈30,900 KRW (a 3% NFR-1 breach since the day it was written) to **≈25,600 KRW**, and which required **one attached Elastic IP** — reconciling `CLAUDE.md` §5 with `B11`'s flat prohibition. **`'SCRAPE'` added to `DATA-001`'s `source` enum** before B2 writes the migration; without it every scraped row would have been mislabelled permanently. **B0 made finishable** — "items keep accumulating" became a standing lane condition rather than a task holding the block open. **Gap recorded, not filled**: no domain or DNS provider is named anywhere, and B12's TLS depends on one (§4 item 2). **`REVIEW-001` and `REVIEW-002` deleted**, rubric and open confirmations preserved |
| **2026-08-24** | **Collection channel policy changed: scraping is permitted at rung 4, above email (ADR-022).** Owner ran a `robots.txt` review of all commercial sources and stated a priority: **missing information is the most critical failure in the job-hunting capability**. Findings: Wevity and Linkareer permit the target paths; JobKorea permits `/recruit/joblist` but has decided case law; **the school notice board has neither a feed nor a `robots.txt`**. ADR-002 had checked only JobKorea and assumed the other two matched — the same "assumption recorded as a finding" error ADR-021 corrected for Saramin's API. **Outcome**: a nine-condition scrape gate whose deciding condition is the **terms of service**, not `robots.txt`; **empty result = `FAILED`** promoted to NFR-17 as the countermeasure for silent parse breakage; no headless browser on the node (ARCH-001 arithmetic); **JobKorea kept at email-only on case law**; **Gmail kept** as a redundant channel because coverage redundancy is the owner's stated priority. **B0 re-run** with a ToS-and-`robots.txt` checklist; **B3 re-scoped from RSS collector to scraper adapter** against the school board; RSS moved to B24; **B26 added** (Wevity, Linkareer), conditional on B0's ToS findings. Cost impact: **zero** |
| **2026-08-24 (late)** | **Ladder restructured on the owner's correction (ADR-022 §0, rev. 2).** **Rungs are now named, not numbered** — `API` · `FEED` · `SCRAPE/MAIL` · `PASTE` · conditional `AGENT` — because numbers had been reassigned three times in three days and each reassignment silently broke cross-references across a dozen files. **`FEED` absorbs the former tokenised-feed and public-feed rungs** (nothing turned on the distinction; **no public RSS/Atom source has been found anywhere in this project**). **Scraping and email merged into one rung as peers** — ADR-022's "query beats waiting" argument was right about latency and wrong about ordering, since it implied dropping email wherever scraping works, when Wevity deliberately uses both. **`PASTE` is the floor and is not manual** — LLM extraction with confirmation (ADR-018); the academic calendar and KakaoTalk schedules live there permanently by design. **Wevity's scraping gate passed** on the owner's determination of the terms → **B26 unblocked**. **`monthnow` hardened from "never use" to prohibited**: `preset_time` becomes a constant rather than a setting, and the adapter **refuses to start** if the assembled URL carries any other value. Gate conditions, the empty-result rule, the no-browser rule, JobKorea's exclusion and keeping Gmail are all unchanged |
| **2026-08-24 (pm)** | **First B0 findings applied.** **School notice board confirmed at rung 4** — `robots.txt` 404, **no terms of service exist at all** (established by a full navigation walk; 개인정보처리방침 read in full, no automated-access clause), server-rendered, selectors and pagination recorded → **B3 unblocked and startable.** **LMS iCalendar export confirmed at rung 2** — Moodle core under a coursemos/UBION wrapper, Calendar nav hidden by the theme but `/calendar/export.php` live. **`preset_time` identified as a correctness parameter**: `monthnow` silently truncates to the current month while returning a valid, non-empty, parseable feed — **NFR-17 does not catch a truncated result**, so **NFR-19 was added** (scope parameters are pinned, tested, and their horizon recorded). **고용24 API key received**; 사람인 pending. **Linkareer excluded from scraping by owner decision** despite passing conditions 1, 3 and 9 (server-rendered, no browser needed), ToS unread → rung 5, and **B26 reduced to Wevity alone**, still blocked on Wevity's ToS. **Near-miss recorded**: a live LMS `authtoken` was exposed in a chat transcript via a markdown link whose display text was blanked but whose href was not — no system compromise, **token rotation pending**, and B24 gains a hard requirement to mask the token in all logs and to store base URL / userid / token as three separate secret values |
| 2026-08-23 | Consistency review (REVIEW-002) via the reusable prompt in PROMPTS-001. Ten findings, all applied: five stale block references from the renumbering (ARCH-001 credit-date block B6→B10; B10-B11-specs Terraform B10→B15 ×3 and VictoriaMetrics B12→B17; ADR-013 B12→B17; DATA-001 B14→B21), cost figures in BLOCKS-001 §10 aligned to ARCH-001 (30,900 / 21,700), CLAUDE.md source list aligned with ADR-021, PRD-000 audit rotation gains the B23 API sources, OPS-001 §4 documents the B13→B17 mechanism-B gap, EC2/EBS tags renamed to `schedule-manager`. No decision changed |
| 2026-08-21 | Planning documents completed and approved |
| 2026-08-22 (am) | External review (REVIEW-001): 3 Critical, 9 Major, 8 Minor. All addressed — memory ledger completed and observability re-decided (ADR-013), silent-failure detection closed (ADR-012), registry decided (ADR-011), data durability decided (ADR-014), migration and Terraform policies added (ADR-015/016), schema corrected, GameDay drills and a freshness SLO added, cost ceiling given an FX basis and an escalation ladder |
| 2026-08-22 (eve) | Source channel investigation → ADR-021, SOURCES-001, blocks B23–B25. Saramin restored via its official API; Worknet added; LMS iCalendar identified. Block numbering policy changed to creation-order |
| 2026-08-22 (pm) | Owner restated capability priorities: schedules and search matter more than job collection, and file sync is a top capability and the main cloud-learning vehicle. **ADR-001's "highest daily value" premise was wrong and is amended by ADR-017.** v1 expanded to all three capabilities plus file sync L0/L1. KakaoTalk investigated — no read API exists — resolved by paste/screenshot with LLM extraction (ADR-018). Scheduling model decided (ADR-019). File sync architecture decided (ADR-020). Repository reframed from "Job & Newsletter Aggregator" to **Schedule Manager**. **Blocks renumbered once**; mapping in BLOCKS-001 §3 |

### 2026-08-22 (evening) — source channels

Investigated whether sources could be pulled directly rather than only through Gmail.
**ADR-002's ladder was missing its top rung.** Findings:

- **Saramin operates an official Open API** (500 calls/day). It had been excluded from the
  project as *"scraping likely prohibited"* — scraping being prohibited and no API existing
  are different facts.
- **Worknet publishes a recruitment API** through 공공데이터포털 (한국고용정보원).
- The **LMS appears Moodle-based**, which means a per-user **iCalendar export URL** — deadlines
  with **no stored password**.
- **Authenticated fetching cannot run on the server**: credential blast radius (a university
  account, not a readonly mailbox), headless-browser memory (300–500 MiB against 415 MiB of
  headroom), and failure locality. If ever built, it runs in the laptop agent (B25).

Written up as **ADR-021** (extends ADR-002) and **SOURCES-001** (the source register).
Blocks **B23/B24/B25** added. **Block numbering policy changed** to creation-order, matching
ADRs, so no renumbering is ever needed again.

## 9. Monthly operations review log

*(Starts after B10. One dated section per month — see OPS-001 §7.)*
