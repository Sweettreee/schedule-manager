# STATUS — Project Status

**Last updated**: 2026-08-23
**Current stage**: Planning complete, revised three times, then swept for consistency
(REVIEW-002). **Next action: block B0.**

> **Claude Code, start here.** Read `CLAUDE.md` in full, then this file, then
> `docs/BLOCKS-001-roadmap.md`, then the spec for the current block in `docs/blocks/`.
> Do not read past the current block's spec.

## 1. Next action

**Block B0 — Foundation.** Spec: `docs/blocks/B0-B8-specs.md` §B0.

B0 is *started*, not finished: mail accumulates from day one and is the input to B4 and B20.
Once B0's repository work is committed, three tracks run in parallel
(`docs/BLOCKS-001-roadmap.md` §2) — when the app track waits for mail volume, work the infra
track.

**Nothing is blocking B0. Start today.**

## 2. What this project is

**Schedule Manager** — a personal information hub with three capabilities over one `items`
table, in the owner's priority order:

| Priority | Capability | v1 level |
|---|---|---|
| 1 | Schedules and materials in one place, with reminders | Week/month view + deadline reminders (B7) |
| 2 | Unified search | Trigram substring search (B8) |
| 3 | Job postings and newsletters | Gmail + RSS + **official APIs** + paste (B2, B3, B6, B23) |
| — | **File synchronisation** — also the richest cloud curriculum here | L0 locker (B14) + L1 laptop agent (B18) |

## 3. Decided

| Area | Decision | Reference |
|---|---|---|
| Problem | Input cost, fear of missing items, scattered material; root cause is manual data transport | PRD-000 |
| **v1 scope** | **All three capabilities at their first useful level, plus file sync L0+L1** | **ADR-017** |
| **Channel ladder** | **Official API → tokenised feed → public feed → email → paste → (conditional) agent-side auth. Commercial-site scraping prohibited** | **ADR-021, SOURCES-001** |
| Sources corrected | **Saramin has an official Open API** (was excluded in error); **Worknet** added; **LMS iCalendar** for deadlines | ADR-021 |
| Credential locality | **No university or commercial account credential is ever stored on the server** — OS keychain on the laptop only | ADR-021, SEC-19 |
| Data model | Single `items` table, shared columns + `extra jsonb`; `UNIQUE(source, source_id)`; `content_hash` excludes `url`; `category` nullable and newsletter-only | ADR-003, DATA-001 |
| **Time model** | **`starts_at` + `due_at` as an optional-ended interval; `all_day` flag; reminders as rows** | **ADR-019** |
| **File sync** | **Content-addressed blobs in S3; presigned direct transfer; bytes never touch the node** | **ADR-020** |
| **KakaoTalk** | **No read API exists (verified). Paste/screenshot with LLM extraction and mandatory confirmation** | **ADR-018** |
| **AI in v1** | **Extraction: yes, because rules cannot parse free-form Korean. Classification: still deferred to B21** | ADR-018, REQ-001 §6 |
| Guiding principle | DP-1 control over convenience, with three exceptions | ADR-004 |
| Platform | k3s on one EC2 `t4g.small`, Seoul; self-managed PostgreSQL and ingress | ADR-005 |
| Stack | FastAPI + Next.js, two containers; SQLAlchemy + Alembic | ADR-006 |
| Gmail auth | OAuth `gmail.readonly`, published app; **2-day timebox then IMAP fallback** | ADR-007 |
| Repos | Two repositories + Flux, split at B16 | ADR-008 |
| Secrets | k8s Secrets first, SOPS + age from B16 | ADR-009 |
| Testing | Conditional TDD; unit plus three integration paths; no browser E2E | ADR-010 |
| Container registry | ghcr.io, private, free. ECR prohibited | ADR-011 |
| Collector liveness | External dead man's switch + internal alerts + banner. **N = 1** | ADR-012 |
| Observability | VictoriaMetrics single-node, 7-day retention; Grafana on demand | ADR-013 |
| Data durability | Separate EBS data volume, delete-on-termination = false | ADR-014 |
| Migrations | Forward-only; every migration backwards compatible with the previous release | ADR-015 |
| Terraform | Import over rebuild; S3 state, no DynamoDB | ADR-016 |
| Dashboard auth | Basic Auth at ingress | SEC-001 |
| Retention | `raw` purged after 90 days, **in backups too** | SEC-001 |
| Backups | **Daily** `pg_dump` to S3; RPO ≤ 24h, RTO ≤ 4h | OPS-001 |
| Cost | 30,000 KRW ceiling **at 1 USD = 1,400 KRW**; escalation ladder defined; **~30,900 KRW list price, over by ~3%** | ARCH-001, OPS-001 |
| Availability | Not a metric — replaced by a **freshness SLO: 99%/month at a 30-hour threshold** | REQ-001 §7 |
| Measurement | M-2 measured by **weekly coverage audit**, not self-reporting | PRD-000 §4.1 |
| Failure drills | **Eight** GameDay drills attached to blocks B12–B19 | GAMEDAY-001 |
| Target role | Cloud / DevOps / SRE | BLOCKS-001 |

## 4. Open — needs the owner to act

1. **Linkareer and JobKorea alert settings** — check after logging in. Needed for **B0**.
2. **Source investigation** — run `SOURCES-001` §3 for every source and fill in the matrix.
   This is now the largest part of B0. Includes: university notice channel, academic calendar,
   and the **LMS check in order** (iCal export → forum RSS → Moodle Web Services).
3. **API key applications** — 공공데이터포털 (Worknet) and `oapi.saramin.co.kr`. Apply early;
   approval takes time. Record Saramin's pricing answer — the guide does not publish it.
4. **Discord webhook** — create the channel and webhook URL. Needed for **B7** (reminders) and
   **B13** (alerting).
5. **healthchecks.io account and check** — free tier, one check, 30-hour grace. Needed for
   **B13** (ADR-012).
6. **LLM provider choice** — evaluate against real Korean date expressions; record price and
   the no-training-on-input commitment. Needed for **B6** (ADR-018, SEC-15).
7. **AWS student programme** — confirm whether any grants credits on a *real* personal
   account. Educate and Academy labs cannot host this. Needed for **B10**.
8. **Seoul region pricing** — confirm in the Pricing Calculator during **B10**.
9. **Google OAuth publishing rules** — reconfirm at the start of **B1**; start the 2-day clock.

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
| Public IP | |
| SSH key fingerprint | |

## 6. Open — decide later, with a trigger

| Question | Revisit when |
|---|---|
| **File sync L2** (pull to a second device) | The owner wants a file on the iPad that is not there |
| **File sync L3** (two-way, conflict resolution) | The first real divergence appears in `file_versions` |
| **LMS-authenticated download** | L1 in daily use, and the LMS turns out to permit it |
| Class timetable recurrence (`rrule`) | A semester proves annoying to maintain as individual rows |
| Blob garbage-collection policy | B19, with real unreferenced-blob counts |
| S3 storage class for old semesters | First monthly review after B14 |
| Cross-source deduplication via `content_hash` | Once data shows how often it happens |
| Korean full-text search approach | B22 |
| AI classification | B21, once newsletter `UNCLASSIFIED` volume is known |
| Relaxing the paste confirmation step | Only with measured precision — **never for `due_at`** |
| Reserved Instance vs. scheduled shutdown | 60 days before credit expiry, with measured figures |
| Alerting on `PARTIAL` runs | B17, once `PARTIAL` frequency is known |
| **B25 — agent-side authenticated LMS fetch** | **All five gate conditions in `SOURCES-001` §4 met — especially #4, that manual downloading is a *measured* weekly cost, not an assumed one** |
| Whether Moodle Web Services is enabled for students | B0. If yes, it supersedes ADR-021 rung 6 and reaches files through an official API |
| Dropping Worknet if it adds no unique items | One month after B23, by coverage overlap |
| Shared retry/backoff layer in `Source` | When the second API adapter is written (B23) |
| kube-state-metrics | After the first monthly review, if headroom allows |
| EBS snapshots in addition to `pg_dump` | B13, once dump sizes are known |
| CI check rejecting non-empty `downgrade()` | B16 |
| `mkfs`/`fstab` in user-data vs. documented manual step | B15 |

## 7. Document index

| Document | Status |
|---|---|
| README.md | Current (reframed as Schedule Manager) |
| CLAUDE.md | Current |
| WORKFLOW.md | Current |
| STATUS.md | This document |
| .gitignore | Current |
| docs/PRD-000-problem-definition.md | Approved |
| docs/REQ-001-requirements.md | v4.0, approved |
| docs/DATA-001-item-schema.md | Approved (rev. 3) |
| docs/ARCH-001-target-architecture.md | Approved |
| docs/SEC-001-security-baseline.md | Approved |
| docs/OPS-001-cost-guardrails.md | Approved |
| docs/SOURCES-001-channel-policy.md | Approved (new) — the source register |
| docs/GAMEDAY-001-failure-drills.md | Approved, 8 drills |
| docs/BLOCKS-001-roadmap.md | Approved (renumbered) |
| docs/REVIEW-001-plan-assessment.md | External review — **uses pre-renumbering block numbers** |
| docs/REVIEW-002-prompt-driven-review.md | Prompt-driven review 2026-08-23 — all findings applied |
| docs/PROMPTS-001-plan-review.md | Reusable plan-review prompt (new) |
| docs/blocks/B0-B8-specs.md | Approved (supersedes B0-B5-specs) |
| docs/blocks/B10-B11-specs.md | Approved (renumbered from B6-B7) |
| docs/blocks/B23-B25-specs.md | Approved (new) |
| docs/incidents/README.md | Template |
| docs/adr/ADR-000-template.md | — |
| docs/adr/ADR-001 | Accepted, **amended by ADR-017** |
| docs/adr/ADR-002 | Accepted, **extended by ADR-021** |
| docs/adr/ADR-003 … ADR-016 | Accepted |
| docs/adr/ADR-017 … ADR-021 | Accepted 2026-08-22 |

## 8. Revision log

| Date | Change |
|---|---|
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
