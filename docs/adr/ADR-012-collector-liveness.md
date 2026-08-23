# ADR-012 — Collector Liveness: External Dead Man's Switch

**Status**: Accepted
**Date**: 2026-08-22
**Related**: PRD-000 §6, REQ-001 NFR-6, ADR-004, ADR-007, OPS-001, GAMEDAY-001

## Context

`PRD-000` §6 names the worst possible outcome precisely: the collector stops, the dashboard
keeps serving yesterday's data, and the user feels *more* confident that nothing was missed
while missing everything. Every other design choice in this project defers to that.

The mechanism that was supposed to prevent it: every run writes a `collection_runs` row, and
after N consecutive `FAILED` rows the collector posts to a Discord webhook.

**That mechanism cannot detect the worst case.** `collection_runs` only records runs that
*started*. If the CronJob is deleted, the node is down, k3s has crashed, or the namespace was
wiped, **no row is written at all** — so "N consecutive failures" never becomes true and no
alert is ever sent. The dashboard, if it is even up, shows the last successful timestamp and
nothing else.

Stated generally: **a system cannot report its own death.** Any watchdog that runs inside the
thing it watches shares the thing's failure modes.

Two secondary problems in the same mechanism: `N` was never given a value (at a 24-hour
interval, N = 2 means 48+ hours of silence before anyone is told), and the user-facing
safeguard — a timestamp in the dashboard header — depends on the user noticing a number,
when PRD-000 says the user's problem is that they stop checking once they feel safe.

## Decision

**Three layers, all required. No single one is sufficient.**

| # | Layer | Runs where | Condition |
|---|---|---|---|
| A | Failure alert | inside the collector | latest run `FAILED` → Discord immediately. **N = 1** |
| B | Staleness alert | inside the cluster (VictoriaMetrics rule, from B17) | `now() − last_success > interval × 1.5` → Discord |
| C | **Dead man's switch** | **outside the cluster** (healthchecks.io free tier) | collector HTTP-GETs a ping URL on every successful run; if no ping arrives within a 30-hour grace period, healthchecks.io alerts Discord by itself |
| D | Staleness banner | the dashboard | when B's condition holds, a red banner at the top of every page, not just a timestamp |

Layer C is available from **block B13** — it needs no monitoring stack, only an outbound
HTTP GET. Layer B arrives with B17.

## Rationale

- **C is the only layer that survives the failure it is meant to catch.** A, B and D all
  live inside the system; if the node is gone, all three are gone with it. The 30-hour grace
  period is the 24-hour interval plus 25%, matching the SLI threshold in REQ-001 §7 so the
  alert and the SLO cannot disagree.
- **N = 1 for layer A.** At a 24-hour interval, the next chance to succeed is a day away.
  Waiting for a second failure means the first notification arrives after two missed days.
  There is no alert-fatigue argument here: this is one collector running once a day.
- **D exists because a number is not a signal.** The user is not a monitoring system.
- Cost: **$0.** healthchecks.io's free tier covers a single check comfortably.
- This is verified, not assumed: **GameDay GD-6** deletes the CronJob and measures which
  alert arrives first. If none does, this ADR is not implemented, whatever the code says.

## Trade-offs

| Gained | Given up |
|---|---|
| The failure mode PRD-000 calls worst-case is actually detectable | A third-party dependency in the alerting path |
| Detection works even when the entire cluster is gone | The ping URL is a secret — anyone holding it can silence the alarm by pinging it |
| Zero cost, and available from B13 rather than B17 | Three mechanisms to keep working instead of one |
| The alert threshold and the SLO share one number | A false alarm if the external service itself has an outage |

## Alternatives rejected

- **Internal-only detection (the original design)** — cannot detect the case it exists for.
  This is not a matter of degree; it is structurally blind.
- **A second EC2 instance running a watchdog** — the purist DP-1 answer, fully self-operated.
  It doubles the compute bill to run one HTTP check, which breaks the ceiling for a workload
  of a few bytes a day.
- **A Lambda + EventBridge health check** — cheap and AWS-native, but it lives in the same
  account and region and shares a blast radius with the thing it watches; and it introduces
  serverless, which ADR-005 deliberately excluded.
- **Email instead of Discord** — needs domain verification and deliverability care; Discord
  is a webhook URL.
- **Gmail push notifications via Pub/Sub as a liveness signal** — conflates delivery with
  collection, and ADR-007 already rejected Pub/Sub for this workload.

## If a managed service was chosen (ADR-004 requirement)

healthchecks.io is a managed service, so this clause applies.

Built by hand this would mean a second machine — in a different failure domain from the
first, or the exercise is pointless — running a scheduler, a state store for "when did I last
hear from it", an alert dispatcher, and its own monitoring, because a watchdog that dies
silently is worse than none. That is a second EC2 instance, roughly doubling the compute bill
to send one HTTP request per day.

This falls under **ADR-004 exception 1** (doing it by hand creates greater risk): a
self-hosted watchdog on the same infrastructure provides false assurance, which is more
dangerous than no watchdog. The understanding is preserved by writing down, here, exactly
what the service does: it stores a deadline, and it fires when a timer expires without being
reset. That is the whole mechanism.

## Open questions

- Whether layer A should also fire on `PARTIAL` runs. Deferred until real data shows how
  often `PARTIAL` occurs; alerting on every partial failure may be noise, and never alerting
  may hide a source that has silently stopped. Revisit at B17 with the numbers.
