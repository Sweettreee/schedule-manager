# OPS-001 — Cost Guardrails and Operations

**Status**: Approved
**Last updated**: 2026-08-25 (ADR-024: lever 1 adopted, so the $20 trigger needed a new action;
Elastic IP step added; §4 delegated to REQ-001 §3.1)
**Related**: ARCH-001, REQ-001 §7, ADR-012, ADR-013, ADR-018, ADR-020, **ADR-024**

## 1. Account setup (block B10)

1. **First, check whether a student programme applies.** AWS Educate gives sandboxed labs
   and AWS Academy Learner Lab gives a time-limited classroom account — **neither can host a
   continuously running project**, because lab resources stop when the session ends and are
   wiped at the end of the course. They are useful as a *rehearsal environment* for B11–B12
   (see BLOCKS-001 §4), not as the runtime. If a programme that grants credits on a **real**
   personal AWS account is available, record the amount and expiry in `STATUS.md` and revise
   the ARCH-001 cost model accordingly.
2. Create the AWS account choosing the **Paid plan**, not the Free plan.
   The Free plan closes the account after six months or when credits are exhausted; that
   would delete a project intended to run indefinitely. Both plans receive the same credits.
3. Enable MFA on the root account, then stop using root.
4. Create an IAM user with MFA for daily work. Use short-lived credentials where possible.
5. Region: `ap-northeast-2` (Seoul) — lowest latency for the user, and the data is personal
   so keeping it in-country is preferable.
5a. **Allocate one Elastic IP and keep it attached to the instance** (ADR-024). A stopped
   instance loses an auto-assigned public IPv4 address, and the instance is stopped nightly by
   design. Cost is unchanged — AWS bills every public IPv4 address at the same rate whether it
   is auto-assigned or elastic. **Exactly one, never unattached.**
6. Enable Cost Explorer and set the billing alert email.
7. **Record in `STATUS.md`, as dates**: account creation date, credit amount, and
   **credit expiry date** (creation + 12 months).

## 2. Budget alarms

Create three AWS Budgets alarms: **$1, $5, $20**.

**These alarms notify; they do not block.** By the time a $20 alarm fires, $20 has already
been spent. Real protection comes from the resource discipline in `CLAUDE.md` §5 and from
the escalation ladder below, which converts a notification into a defined action.

Note that "set up a cost budget in AWS Budgets" is also one of the onboarding activities
that earns account credits, so this step pays for itself.

## 3. Escalation ladder

A notification is not a guardrail until someone knows what to do when it arrives.

| Trigger | Action | Deadline |
|---|---|---|
| **$1 alarm** in the first month | List every running resource and diff it against ARCH-001. Anything not in ARCH-001 is deleted or becomes an ADR | 24 hours |
| **$5 alarm** | Identify the specific line item in Cost Explorer that exceeded the forecast. Write it up in `docs/incidents/` — an unexpected bill is an incident | 48 hours |
| **$20 alarm** | **Lever 1 is already spent** (the nightly shutdown is the design — ADR-024), so this alarm means the design's own figure has been exceeded. **First verify the shutdown is actually running** — a schedule that silently stopped is the most likely cause and puts the bill straight back at the 30,900 KRW list price. If it is running, identify the line item and pull **lever 2** or widen the shutdown window | same day |
| Month closes **above 30,000 KRW or above USD 21.4** | Write an ADR proposing lever 2 (Reserved Instance) or a design change. **The ceiling is not adjusted to fit the spend.** Note the design figure is ≈25,600 KRW, so a breach means something is running that ARCH-001 does not list, or the shutdown is not working | first week of the next month |
| **60 days before credit expiry** | Re-run the cost model with **measured** Cost Explorer figures. Lever 1 is already in the design, so the decision is whether **lever 2** (Reserved Instance) is now worth its 12-month commitment. This is a calendar item, not a reaction | 60 days out |
| FX moves such that USD 21.4 ≠ 30,000 KRW by more than 5% | Update the assumption in ARCH-001 and re-evaluate | monthly review |
| **S3 file storage passes 10 GB** (NFR-13) | Review what is being synced; check for an agent retry loop; consider Standard-IA for last semester | 48 hours |
| **S3 egress in a month exceeds 20 GB** | Stop the agent first, diagnose second. Normal use at a 5 GB working set is nowhere near this — an overshoot means a loop, not usage | same day |
| **LLM extraction hits the 300-call monthly cap** (FR-17) | Extraction disables itself and alerts. Investigate before raising the cap | 48 hours |

Three of these guard against the same shape of failure: **a bug in a retry loop spends money
much faster than a person can.** Storage and call caps are enforced in code, not just alarmed,
because an alarm that fires at 3am does not stop a loop.

## 4. Freshness monitoring and alerting

**The three mechanisms and their firing conditions are specified in `REQ-001` §3.1**, and the
reasoning for why the third cannot be replaced by the first two is in `ADR-012`. They are not
restated here. This section covers only what is operational: the delivery channel, when each
mechanism becomes available, and the gap between those dates.

Alerts are delivered to a **Discord webhook** — chosen over email because it needs no domain
verification and costs nothing. Mechanism C delivers via healthchecks.io → Discord, **from
outside the cluster**, which is the whole point of it.

Metrics are collected by VictoriaMetrics (ADR-013) from block B17. Until B17, mechanisms A
and C are implemented directly in the collector — C in particular is available from **B13**,
because it needs no monitoring stack, only an HTTP GET.

**Known interim gap (B13 → B17)**: mechanism B has no home until VictoriaMetrics exists, so
between B13 and B17 only A and C run. This is acceptable at the default 24-hour interval
because C's 30-hour grace fires *before* B would (24h × 1.5 = 36h), so nothing is detected
later than it would be with B present. The gap is real only if the collection interval is
shortened below 24h before B17 — in that case, do not rely on C alone; either bring B17
forward or accept the slower detection knowingly and record it in `STATUS.md`.

## 5. Backup and restore

- **Daily** `pg_dump` uploaded to S3 (block B13). Weekly was the previous plan; at up to six
  days of loss it directly contradicts the reason this system exists — a lost week of
  collected postings is a week of missed deadlines. A dump of this database is a few MB, so
  daily costs essentially nothing.
- Two dumps with different retention, per SEC-001 §"Retention and backups".
- **Recovery objectives, stated as numbers so a drill can pass or fail:**
  - **RPO ≤ 24 hours** — at most one day of collected items lost.
  - **RTO ≤ 4 hours** — from "instance is gone" to "dashboard serving current data".
- **A backup that has never been restored is not a backup.** A restore drill into a scratch
  database is part of B13's definition of done, is **timed against the RTO**, and is repeated
  whenever the schema changes significantly.
- Node loss and data loss are different events. ADR-014 (separate EBS data volume) means an
  instance can be destroyed and rebuilt without touching the database; backups cover the
  volume itself being lost or corrupted.

## 6. Secret rotation

Rotation procedure for each secret is listed in SEC-001 §"Incident handling". Rotate on a
schedule as well as on exposure:

| Secret | Routine rotation |
|---|---|
| PostgreSQL password | at each major schema milestone, or yearly |
| ghcr.io pull token | yearly, or when the token's scope changes |
| Basic Auth credentials | yearly |
| Gmail refresh token | not rotated on a schedule — rotation forces a re-consent flow; rotate on exposure only |
| age private key | on exposure only; **the key is backed up off-machine at creation** (ADR-009) |

## 7. Monthly operations review

Once a month, in one sitting, and recorded as a dated section in `STATUS.md`:

1. **Spend** vs. the 30,000 KRW / USD 21.4 ceiling, from Cost Explorer actuals.
2. **FX assumption** still within 5%.
3. **Days until credit expiry.**
4. **Orphaned resources**: unattached EBS volumes, old snapshots, unattached Elastic IPs,
   noncurrent S3 versions.
5. **Backup freshness**: newest object in the S3 bucket is less than 48 hours old.
6. **SLO error budget** (REQ-001 §7): staleness minutes consumed this month out of ~7h18m.
   **If the budget is exhausted, the next block's first task is reliability work, not
   features.**
7. **Memory ledger** (ARCH-001): measured usage vs. the recorded figures.
7a. **Shutdown window vs. M-3** (ADR-024): did the 02:00–08:00 KST stop cost a
    `DASHBOARD_OPEN` day this month? If it did, widen the running hours and take the cost back
    out of lever 2. Also confirm the schedule actually ran — a silently stopped schedule is a
    ~5,300 KRW/month regression that no alarm below $20 will catch.
8. **File store** (from B14): total bytes, unreferenced blob count, egress for the month.
9. **Extraction** (from B6): calls used out of the cap, and re-verify the provider's
   no-training commitment (SEC-15).
10. Anything learned recorded in `docs/incidents/` or a new ADR.
