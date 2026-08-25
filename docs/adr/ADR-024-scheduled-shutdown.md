# ADR-024 — Scheduled Nightly Shutdown, 02:00–08:00 KST

**Status**: Accepted
**Date**: 2026-08-25
**Related**: ARCH-001 (lever 1), ADR-005, **ADR-013 (answers its M-3 objection)**, ADR-012,
OPS-001, PRD-000 §5 / M-3, REQ-001 NFR-1, GAMEDAY-001 GD-4

## Context

`REQ-001` NFR-1 is a **Must**: monthly operating cost ≤ **30,000 KRW**, evaluated at the FX
assumption in `ARCH-001` (1 USD = 1,400 KRW → ≈ USD 21.4).

`ARCH-001`'s cost model totals **≈ $22.1 ≈ 30,900 KRW** and says so plainly: *"This is over the
ceiling — by about 900 KRW, or 3% — and the document says so rather than rounding down."*

So the target architecture has **failed its own Must requirement since the day it was written**,
and `OPS-001` §3 forecloses the easy escape: *"The ceiling is not adjusted to fit the spend."*

`ARCH-001` already lists four cost levers and calls the first one **"the default lever"**:

> *"**Scheduled shutdown outside usage hours** — viable because availability is explicitly not a
> requirement (PRD-000 §5)."*

It was recorded as a contingency to pull if a budget alarm fired. That is one alarm too late:
the design is out of compliance *before* any alarm, and a lever nobody has committed to is not a
plan.

### The objection this ADR has to answer

`ADR-013` rejected a `t4g.medium` + nightly-shutdown option, and one of its reasons applies to
this decision too:

> *"It also adds a shutdown scheduler to operate and makes the dashboard unavailable at night,
> **which conflicts with metric M-3**."*

`ARCH-001` raises the same check: *"the dashboard is unreachable while stopped — check this
against M-3 (dashboard opened ≥ 5 days/week) before adopting."*

**M-3 is a real metric, not a formality**: `PRD-000` measures habit formation by days the
dashboard is opened, and the whole product depends on the owner actually looking at it.

## Decision

**The EC2 instance is stopped from 02:00 to 08:00 KST every day, by design — not as a
contingency.**

Four consequences follow, and all four are part of this decision:

1. **The collector CronJob runs shortly after start-up**, not on a fixed hour that may fall
   inside the stopped window. Target: **08:05 KST**, once daily.
2. **One Elastic IP, permanently attached.** An auto-assigned public IPv4 address is *released*
   when an instance stops, so the address would change every morning — breaking DNS and TLS.
   See §"The addressing consequence".
3. **The window is revisited at the first monthly operations review** (`OPS-001` §7) against
   **measured** M-3 data. Changing it costs one cron edit.
4. **`ARCH-001` lever 1 is now spent.** Levers 2–4 (Reserved Instance, smaller instance, spot)
   remain available as contingencies; this one is no longer in reserve.

### Cost effect

The instance runs **18 of 24 hours**. Only the compute line changes; storage and the IPv4
address are billed whether the instance runs or not.

| Line | Before | After |
|---|---|---|
| EC2 `t4g.small`, Seoul | $15.2 | **$11.4** |
| Everything else (EBS ×2, IPv4, S3, LLM, transfer) | $6.9 | $6.9 |
| **Total** | **≈ $22.1 ≈ 30,900 KRW** | **≈ $18.3 ≈ 25,600 KRW** |

> **NFR-1 is satisfied by the design for the first time**, with roughly **15% margin** instead of
> a 3% breach.

`30,900 KRW` survives in the documents only as the labelled **list price without the shutdown**,
because it is the number the escalation ladder measures against if the schedule ever stops
working.

### Why 02:00–08:00 specifically

- **It is the window least likely to cost an M-3 day.** A single-user dashboard checked as a
  daily habit is checked in the morning, the evening, or late at night — 02:00–08:00 is the only
  six-hour block that reliably contains none of those.
- **Six hours, not ten.** `ARCH-001`'s lever-1 sketch assumed a 10-hour window and produced
  ≈21,700 KRW. Six hours produces ≈25,600 KRW, which is **still inside the ceiling with margin**,
  and buys back four hours of availability for 3,900 KRW of headroom that was not needed.
- **Collection lands before the working day.** An 08:05 run means the freshest data is present
  the first time the dashboard is opened.

## The addressing consequence

**This is the part that was missing from `ARCH-001` lever 1, and it is why this needs an ADR
rather than a cost-model edit.**

A public IPv4 address auto-assigned to an instance is released when the instance stops. A
different one is assigned on start. A nightly shutdown therefore means **the server's address
changes every morning**, which breaks:

- any DNS A record pointing at it,
- Let's Encrypt HTTP-01 challenges and therefore certificate renewal (`SEC-2`, B12),
- any bookmark or agent configuration holding the address.

The two documents that mention Elastic IPs disagreed:

- `B10-B11-specs` §B11 acceptance: *"**no Elastic IP** exists in the account"*
- `CLAUDE.md` §5: *"Never create: … **Elastic IPs left unattached**"* — which permits an attached one

**Resolution: allocate exactly one Elastic IP and keep it attached.** `B10-B11-specs`'s
acceptance criterion is corrected to *"exactly one Elastic IP exists and is attached"*; the
monthly orphan check in `OPS-001` §7 continues to look for **unattached** ones, which is what the
rule was always about.

**Cost impact: zero.** AWS bills all public IPv4 addresses at $0.005/hour whether in use or not,
so `ARCH-001`'s existing $3.7/month line is correct either way.

The remaining piece — **which hostname** the address answers to — is **not decided here.** No
document in this set names a domain, registrar or DNS provider, and this ADR does not invent
one. It is recorded as an open question in `STATUS` §4 and as an entry condition on B12.

## Rationale

- **A Must requirement should be satisfied by the design, not by a footnote.** A ceiling that is
  only met after an alarm fires is not a ceiling.
- **Availability was already traded away deliberately.** `PRD-000` §5: *"A few hours of downtime
  per month is acceptable and is deliberately traded away for cost."* This spends exactly that
  trade, at the hours it costs least.
- **The freshness SLO is untouched.** `REQ-001` §7's SLI is
  `now() − last_successful_collection < 30 hours`, measured against a **daily** collection. A
  collector running at 08:05 every day never approaches 30 hours. Stopping the instance does not
  burn error budget; **stopping collection would**, and collection is unaffected.
- **`ADR-012` layer C still works.** healthchecks.io's 30-hour grace period is compared against a
  24-hour ping interval. The shutdown does not change the interval.
- **`ADR-013`'s objection is answered, not ignored.** Its two costs were (a) a scheduler to
  operate and (b) M-3 conflict. (a) is one EventBridge rule or one cron entry — real, and
  accepted; (b) is addressed by choosing a window that contains no plausible dashboard visit, and
  by committing to re-check it against measured data at the first monthly review. What `ADR-013`
  actually rejected was `t4g.medium` **plus** a shutdown — paying more for a bigger instance and
  then shutting it down — not a shutdown on the instance already chosen.

## Trade-offs

| Gained | Given up |
|---|---|
| NFR-1 satisfied by design, with ~15% margin instead of a 3% breach | The dashboard is unreachable 02:00–08:00 KST |
| Lever 1 becomes a commitment instead of a promise | Lever 1 is now spent; only levers 2–4 remain in reserve |
| A stable address, and the Elastic IP contradiction resolved | One more resource to create, tag, import into Terraform (B15) and reattach in GD-4 |
| The hours were chosen against M-3 rather than for maximum saving | A window fixed before a single day of real usage data exists |
| Collection lands at 08:05, so the dashboard is freshest when opened | A start-up dependency: if the instance fails to start, the collector never runs — caught by `ADR-012` layer C, not by A or B |

## Alternatives rejected

- **Accept the 3% overage as a dated exception.** Honest, and it was `ARCH-001`'s position.
  Rejected: `NFR-1` is a Must and `OPS-001` §3 refuses to move the ceiling, so accepting the
  overage means the document set knowingly ships a requirement it fails.
- **Defer the window to B10 and decide with measured figures.** Genuinely attractive — the data
  would be real. Rejected because the compliance gap exists *now*, in the documents a future
  session builds from, and B10 is roughly ten blocks away.
- **A 10-hour window (00:00–10:00), matching `ARCH-001`'s original sketch.** Saves a further
  ~3,900 KRW/month and requires no recomputation of the figures already written. Rejected: it
  costs four hours of morning and late-evening availability to buy headroom under a ceiling that
  six hours already clears.
- **Reserved Instance (lever 2) instead.** Similar saving with no availability cost at all.
  Rejected for now on `ARCH-001`'s own sequencing: it requires a 12-month commitment and should
  only be taken after the design has stabilised and credits are close to gone.
- **`t4g.micro` (lever 3).** Not viable — the `ARCH-001` ledger needs 835 MiB of requests against
  a 1 GiB instance. Already recorded as rejected so it is not re-proposed.
- **Dynamic IP plus a boot-time dynamic-DNS update.** No Elastic IP, maximally DP-1, and it would
  teach DNS automation. Rejected: it adds a moving part to the morning start-up path during which
  the dashboard and certificate renewal both fail, to avoid a resource that costs the same as the
  address it replaces.

## If a managed service was chosen (ADR-004 requirement)

No managed service is adopted. The schedule is a cron entry or an EventBridge rule calling
`StopInstances` / `StartInstances` — operated by hand, in the same spirit as everything else on
this node. No AWS Instance Scheduler solution stack is deployed; that would be a CloudFormation
stack with its own Lambda and DynamoDB table, which `CLAUDE.md` §5 prohibits and which would cost
more than it saves.

## Consequences for other documents

- `ARCH-001` — cost model rebuilt at ≈$18.3 ≈25,600 KRW; lever 1 marked **adopted**, see this ADR;
  Elastic IP line reconciled.
- `REQ-001` NFR-1 — evaluated against the design figure; the ceiling itself is unchanged.
- `OPS-001` §1 gains the Elastic IP allocation step; §3's escalation figures updated; §7 gains the
  M-3-vs-window re-check.
- `B10-B11-specs` §B11 — Elastic IP added; the "no Elastic IP" acceptance line corrected.
- `GAMEDAY-001` GD-4 — instance rebuild must reattach the Elastic IP.
- `ADR-013` — gains a cross-reference to this ADR answering its M-3 objection.
- `BLOCKS-001` §10, `STATUS`, `README`, `CLAUDE.md` §5 — figures updated.

## Open questions

- **The hostname.** No domain, registrar or DNS provider is named anywhere in this document set,
  and cert-manager (B12) cannot issue a certificate without one. Recorded in `STATUS` §4 and as a
  B12 entry condition. **Not invented here.**
- **Whether the window costs an M-3 day.** Re-check at the first monthly review (`OPS-001` §7)
  with real `usage_events.kind = 'DASHBOARD_OPEN'` data. If it does, widen the running hours and
  take the cost back out of lever 2.
- **Where the schedule runs.** A cron entry on the node cannot start the node. It must therefore
  be an EventBridge scheduled rule (or equivalent) outside the instance. Decide the exact
  mechanism at B11/B13; the requirement — that it lives outside the thing it starts — is decided
  here, and it is the same reasoning as `ADR-012`.
