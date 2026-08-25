# GAMEDAY-001 — Planned Failure Drills

**Status**: Approved
**Last updated**: 2026-08-25 (GD-4 gains the Elastic IP reassociation step — ADR-024)
**Related**: WORKFLOW.md (DoD step 3), BLOCKS-001 §5, OPS-001, REQ-001 §7, ADR-024

## Why this document exists

`WORKFLOW.md` states that incident write-ups are among the most valuable artefacts in this
repository — for an SRE portfolio, more valuable than any feature. But a single-user system
that works will not produce incidents for months, and `docs/incidents/` would stay empty
until something breaks by accident, at the worst possible moment, with no rehearsal.

So the failures are **scheduled**. Each is attached to the block that builds the thing being
broken, and each is part of that block's Definition of Done.

A drill is not "I deleted a pod and it came back." A drill is: predict, break, observe,
measure, and write down the gap between what you predicted and what happened. **The gap is
the finding.** A drill where everything went as expected and nothing was learned should be
recorded as such in one paragraph — that is a valid result — but a drill that surfaces a gap
produces a follow-up task or an ADR.

## Procedure for every drill

1. **Predict, in writing, before touching anything.** What will break, what will recover on
   its own, how long it will take, what will alert.
2. **Set a stopwatch.**
3. **Inject the failure.**
4. **Observe without fixing** for as long as is safe. What did you *actually* see first —
   the alert, the dashboard, or nothing?
5. **Recover**, timing each step.
6. **Write it up** in `docs/incidents/YYYY-MM-DD-<slug>.md` using the template in
   `docs/incidents/README.md`.
7. **File the follow-ups.** A drill with no follow-up is either a perfect system or an
   incurious operator.

Never run a drill when you are about to be away, and never run one against a system whose
last backup is older than 24 hours.

## The drills

### GD-1 — Certificate and ingress failure (block B12)

| | |
|---|---|
| **Inject** | Delete the TLS Secret that cert-manager issued, then request the site over HTTPS |
| **Predict** | Browser TLS error; cert-manager re-issues within minutes; Let's Encrypt rate limits may bite if repeated |
| **Measures** | Time to re-issue. Whether anything alerted, or whether you only knew because you looked |
| **The point** | ADR-004 accepts cert-manager under exception 1 precisely because a missed renewal breaks the site silently. This drill tests whether that assumption holds |

### GD-2 — Database pod destruction (block B13)

| | |
|---|---|
| **Inject** | `kubectl delete pod postgres-0 --force` |
| **Predict** | StatefulSet recreates it; the PVC reattaches; API returns 5xx for N seconds then recovers; no data loss |
| **Measures** | Seconds of API unavailability. Row count before and after. Whether the API reconnects on its own or needs a restart |
| **The point** | Connection-pool behaviour after a backend disappears is the single most common cause of "the database came back but the app didn't" |

### GD-3 — Restore from backup, timed (block B13)

| | |
|---|---|
| **Inject** | Create a scratch database and restore yesterday's dump into it |
| **Predict** | Restore completes in under X minutes; schema matches the current migration head |
| **Measures** | **Wall-clock time against the 4-hour RTO** (OPS-001 §5). How stale the newest row is, against the 24-hour RPO |
| **The point** | This is the drill that converts "we have backups" into a number. Also the only way to discover that a dump is unrestorable before you need it |

### GD-4 — Instance destruction and rebuild (block B15)

| | |
|---|---|
| **Inject** | Terminate the EC2 instance. Rebuild with `terraform apply`, reattach the data volume, **reassociate the Elastic IP**, reinstall k3s, let Flux reconcile |
| **Predict** | The data EBS volume survives (ADR-014); the Elastic IP survives termination and reassociates, so DNS and TLS need no change (ADR-024); everything else is rebuilt from git; total recovery within RTO |
| **Measures** | Full RTO. **Whether the address really came back** — if it did not, every certificate and bookmark is now wrong and the nightly shutdown is unsafe. Every manual step you had to take that Terraform or Flux did not cover — **that list is the real output of this drill** |
| **The point** | This is the drill that proves whether "reproducible from git" is true or aspirational. Almost nobody passes it the first time, which is why it is worth doing |

> Run this one **before** the credits run out, while a mistake costs nothing.

### GD-5 — Bad deploy and rollback (block B16)

| | |
|---|---|
| **Inject** | Push a commit that builds a working image but crashes on startup (e.g. a missing env var) |
| **Predict** | Flux reconciles it, the pod CrashLoopBackOffs, the old ReplicaSet keeps serving because the readiness probe fails, no user-visible outage |
| **Measures** | Whether the deploy was actually safe, or whether the old pod was terminated before the new one was ready. Time to roll back, and by what mechanism (git revert vs `kubectl rollout undo`) |
| **The point** | Tests whether readiness probes and update strategy are configured, or merely present |

### GD-6 — The silent death (block B17) — **the most important drill**

| | |
|---|---|
| **Inject** | `kubectl delete cronjob collector`. Then do nothing at all |
| **Predict** | No `FAILED` row is ever written, so mechanism A never fires. Mechanism B fires when staleness passes interval × 1.5. Mechanism C fires from healthchecks.io after the grace period |
| **Measures** | **Which alert arrived first, and how long it took.** Whether the dashboard banner appeared |
| **The point** | PRD-000 §6 names silent collector failure as the worst possible outcome, worse than the original problem. ADR-012 claims to prevent it. **This drill is the only evidence that the claim is true.** If no alert arrives, ADR-012 is not implemented, regardless of what the code looks like |

Repeat GD-6 after any change to the collector, the CronJob schedule, or the alerting path.

### GD-7 — Disk exhaustion (block B17)

| | |
|---|---|
| **Inject** | `fallocate -l 8G /mnt/data/ballast` until the data volume is ~95% full |
| **Predict** | PostgreSQL refuses writes; the collector run fails and records `FAILED`; mechanism A alerts |
| **Measures** | Whether any alert fires *before* writes fail, or only after. Whether the system recovers cleanly once the ballast file is removed |
| **The point** | Disk is the classic slow-motion outage. A single-node system with a 10 GiB data volume and 90-day raw retention will approach this in real life; better to meet it deliberately |

### GD-8 — File loss and restore (block B19)

| | |
|---|---|
| **Inject** | Overwrite a synced file on the laptop with garbage and let the agent upload it. Then restore the previous version from the dashboard |
| **Predict** | The bad version uploads as a new `file_versions` row; the previous version is still present and restorable; the blob for the old content was never deleted |
| **Measures** | Whether restore actually returns the original bytes (verify by hash, not by eye). How many clicks it took. Whether the agent then re-uploads the restored content or recognises it as known |
| **The point** | Version history is only real if restore works. This also tests the subtle case that breaks naive sync clients: after a restore, the *server* has content the *laptop* does not — which is the first taste of the L2/L3 problem, met deliberately rather than by accident |

> Also run the destructive variant once, with a backup verified first: delete a `blobs` row's
> S3 object directly and confirm the system reports a missing blob rather than serving a
> corrupt file.

## Summary table

| Drill | Block | What it proves |
|---|---|---|
| GD-1 | B12 | TLS renewal is really automatic |
| GD-2 | B13 | Stateful workload survives pod loss |
| GD-3 | B13 | Backups restore, within RTO |
| GD-4 | B15 | Infrastructure is reproducible; data survives the node |
| GD-5 | B16 | Deploys are safe and reversible |
| GD-6 | B17 | **The silent failure that this project exists to prevent is actually detected** |
| GD-7 | B17 | Resource exhaustion is noticed before it becomes data loss |
| GD-8 | B19 | File version history restores real bytes, and divergence is survivable |
