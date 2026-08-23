# Incidents

One file per incident: `YYYY-MM-DD-<short-slug>.md`.

Two kinds live here and both are welcome:

- **Unplanned** — something broke.
- **Planned (GameDay)** — a drill from `docs/GAMEDAY-001-failure-drills.md`. Mark these with
  `Type: GameDay (GD-n)` so they are not mistaken for real outages.

An unexpected AWS bill is an incident too (OPS-001 §3).

## Template

```markdown
# <Title> — YYYY-MM-DD

**Type**: Unplanned | GameDay (GD-n)
**Block**: Bn
**Duration**: HH:MM (detection to recovery)
**Impact**: what stopped working, and for whom (usually: collection stopped for N hours)
**Detected by**: alert A / alert B / dead man's switch / dashboard banner / I happened to look

## Prediction (GameDay only — written before injecting)

What I expected to happen.

## Timeline (KST)

| Time | Event |
|---|---|
| 09:00 | ... |

## What actually happened

Facts. No blame, no speculation presented as fact.

## Root cause

The mechanism, not the trigger. "The CronJob was deleted" is a trigger;
"nothing outside the cluster was watching, so deletion was undetectable" is a cause.

## What surprised me

The gap between the prediction and reality. **This is the most valuable section — write it
first while it is still fresh.**

## Recovery

Steps taken, and how long each took. Note anything that had to be done by hand which was
supposed to be automatic.

## Follow-ups

- [ ] concrete action, with a block or a date
- [ ] ADR-XXX if a decision changed

## Metrics touched

Error budget consumed (REQ-001 §7): N minutes of ~438.
RPO/RTO observed vs. target (OPS-001 §5).
```

## Why this folder matters

For a Cloud/DevOps/SRE portfolio, a folder of honest incident write-ups says more than any
feature list. It shows that failures were expected, detected, measured and learned from —
which is the actual job. The "What surprised me" section is what distinguishes a write-up
from a changelog entry.
