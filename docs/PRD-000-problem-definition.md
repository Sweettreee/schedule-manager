# PRD-000 — Problem Definition

**Status**: Approved
**Last updated**: 2026-08-25 (M-2's target aligned with §4.1, which defines it)

## 1. The problem

Information the owner needs is scattered across at least five places (Saramin, Linkareer,
JobKorea, university notice boards, Wevity) plus an email inbox. Nothing aggregates them.
The result is three concrete costs.

| ID | Problem | Cost |
|---|---|---|
| P-1 | **Input cost** — the same information is re-typed by hand into notes, calendars, spreadsheets | Time, and errors introduced during copying |
| P-2 | **Fear of missing something** — no single place shows everything, so deadlines may pass unnoticed | Anxiety, repeated re-checking of the same sites, real missed deadlines |
| P-3 | **Scattered material** — files, links and schedules live in different tools | Retrieval takes longer than the task itself |

## 2. Root cause

All three reduce to one thing: **a human is being used as a transport layer between systems.**
The value is not in the typing; the value is in deciding what to apply to. Every keystroke
spent moving data between tools is waste.

This framing is what makes the three planned capabilities one product rather than three:

| Capability | Its actual role | Owner's priority |
|---|---|---|
| Schedule & files | **Time output** — retrieve items along a time axis | **1st** |
| Unified search | **Content output** — retrieve items along a content axis | **2nd** |
| Job/contest collection | **Ingest** — pull items in from outside | 3rd |

**Priority is not build order, and this is worth being explicit about.** The time view and
search are both *queries over the table that ingest fills*, so something has to fill it first
regardless of which matters most. What priority changes is **which sources** are collected and
**how early the views appear** — and it changed both: school notices moved from an
extensibility test into a core Phase 1 source, and the time view and search entered v1.
See ADR-017.

File synchronisation sits slightly apart: it is ingest of a different kind, and it is also the
project's richest cloud-engineering curriculum, which is why it is in v1 rather than deferred
(ADR-020).

## 3. Who this is for

One user: the owner. Not a multi-tenant product. No collaboration features. Web first.

## 4. Success metrics

Measured from real usage, not from feature completion.

| ID | Metric | Target | How it is measured |
|---|---|---|---|
| M-1 | Manual re-entry of information | ≤ 3 items per week | `usage_events.kind = 'MANUAL_ENTRY'`, **plus** the coverage audit below |
| M-2 | Postings that existed but never reached the dashboard | **Coverage ≥ 90% for every audited source, and no source below 70% for two consecutive audits** (§4.1 derives this) | **Coverage audit** (§4.1) — *not* self-reporting |
| M-3 | Days per week the dashboard is opened | ≥ 5 | `usage_events.kind = 'DASHBOARD_OPEN'`, one per day |
| M-4 | Deployments | ≥ 1 per month (the project must stay alive) | git tags / Flux reconcile history |
| M-5 | Monthly operating cost | ≤ 30,000 KRW (see NFR-1) | AWS Cost Explorer, monthly review |

**Measurement requirement**: M-1 and M-3 cannot be measured unless the system records them.
The dashboard must therefore log access days and provide a way to record "I had to enter this
by hand". This is a v1 requirement, not an afterthought (REQ-001 FR-11).

### 4.1 Why M-2 cannot be self-reported — the coverage audit

A missed posting is, by definition, one the user never saw. Asking the user to press a
"I missed this" button measures only the missed items they later happened to discover, so it
systematically undercounts and the undercount reads as success. The same flaw applies weakly
to M-1: logging manual entry has the same friction the metric is trying to eliminate.

The fix is to compare against an external ground truth.

**Coverage audit — weekly, about 10 minutes:**

1. Open one source site (rotate: Wevity → JobKorea → 고용24/Saramin → university notices;
   from B23, Worknet and Saramin join the rotation — for those two the comparison can run
   in code against the API, per ADR-021, without ceasing to be an external reference).
2. Take the **10 most recent postings** from the last 7 days.
3. For each, query the local `items` table by title/organisation.
4. Record the result as one `usage_events` row with
   `kind = 'COVERAGE_AUDIT'`, `note = '<source>: 8/10'`.
5. Anything missing is a defect: find out why (not subscribed / filtered out / parse failure)
   and, per ADR-010's bug rule, add it as an anonymised fixture with a failing test.

M-2's real target is therefore: **coverage ≥ 90% for every audited source, and no source
below 70% for two consecutive audits.**

This is also the honest SRE question — *can a system know what it failed to see?* — and the
answer is that it cannot without an external reference. That is why the audit exists.

## 5. Explicit non-goals

- Not a service for other users
- Not a mobile app (web first)
- Not a replacement for applying to jobs — only for finding and tracking them
- **Availability is not a metric.** A few hours of downtime per month is acceptable and is
  deliberately traded away for cost. What is *not* acceptable is the collector failing
  silently; see NFR-6 and ADR-012.

## 6. Why a silent collector failure is the worst outcome

If collection stops, the dashboard does not go blank — it keeps showing yesterday's data.
The user then feels *more* confident that nothing was missed, while missing everything.
This failure mode is worse than the original problem and drives the `collection_runs`
design in DATA-001 and the liveness design in ADR-012.

**Corollary (added 2026-08-22).** A system cannot report its own death. If the whole node,
cluster or CronJob is gone, no `FAILED` row is ever written and no internal alert can fire.
Detection must therefore include a component that lives **outside** this system. That is
ADR-012, and it is not optional.
