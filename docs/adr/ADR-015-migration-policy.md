# ADR-015 — Database Migration Policy: Forward-Only

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-003, ADR-010, DATA-001, WORKFLOW.md

## Context

`DATA-001` says migrations run automatically at application start in local development and as
an explicit step in deployment. What it did not say is **what happens when a deployment is
rolled back.**

From block B16, pushing to `main` deploys automatically (NFR-5). A bad release will happen.
`kubectl rollout undo` restores the previous *application* image in seconds — but the schema
has already moved. Two failure modes follow, and both are silent:

1. The old application version meets a schema it does not understand (a renamed or dropped
   column) and fails at query time, not at start-up, so the rollback appears to succeed.
2. An Alembic `downgrade()` is run to "undo" the migration, and it drops a column that the
   new version already wrote data into. **That data is gone**, and nothing reports it.

`ADR-010` identifies the worst failure class in this project as *silently wrong data*, not
exceptions. Destructive downgrades are the purest example of that class.

## Decision

**Migrations are forward-only.**

1. `downgrade()` bodies are `raise NotImplementedError`. They are never written, never run.
2. To undo a schema change, write a **new** migration that corrects it.
3. Every migration must be **backwards compatible with the immediately previous application
   version**, so that an application rollback is always safe. Destructive changes are split
   across releases:
   - release *n*: add the new column, nullable, dual-write
   - release *n+1*: backfill, switch reads
   - release *n+2*: stop writing the old column
   - release *n+3*: drop it
4. Migrations run as an **explicit, separate step before** the new application pods start —
   not as a side effect of application start-up in the cluster. In local development,
   running at start-up is fine and convenient.
5. No manual DDL against any environment, including local. If the schema and the migration
   history disagree, the migration history wins.

## Rationale

- **Application rollback is the operation that must always work.** Making every schema change
  compatible with the previous release is what makes `kubectl rollout undo` a safe reflex
  rather than a gamble. That is a real production discipline, not a formality.
- **A `downgrade()` is almost never tested.** It is written once, never exercised, and then
  executed for the first time during an incident, on production, under stress. The
  expected-value calculation is bad.
- **Data loss is irreversible; a wrong column is not.** Leaving an unused column in place
  until the next release costs nothing.
- **Migration-on-start-up is unsafe with more than one replica** and, more importantly, makes
  the migration's failure look like a pod crash-loop rather than a deployment failure.
  Separating it makes the failure legible.
- It is cheap to adopt now, at zero rows. Adopting it after the first destructive downgrade
  is how most teams adopt it.

## Trade-offs

| Gained | Given up |
|---|---|
| Application rollback is always safe | Removing a column takes several releases instead of one |
| No untested destructive code path exists | The schema carries deprecated columns for a while |
| Failed migrations are visible as deploy failures, not crash-loops | One more step in the delivery pipeline (B11) |
| Data can never be destroyed by an automated rollback | Requires discipline the tooling does not enforce |

## Alternatives rejected

- **Reversible migrations with real `downgrade()` bodies** — the Alembic default and
  textbook-correct. Rejected because in a solo project the downgrade path will never be
  tested, and an untested destructive path is worse than no path.
- **Migrations at application start-up in the cluster** — simpler pipeline, one fewer moving
  part. Rejected because it couples schema change to pod scheduling and hides migration
  failures inside crash-loops.
- **Manual migrations applied by hand at deploy time** — maximum control, and consistent with
  ADR-004's spirit. But ADR-004's own boundary note already exempts the migration layer:
  *"migration errors are silent and destructive and the learning value there is low relative
  to the risk."* Manual DDL is exactly the failure this exempts.
- **Blue-green databases** — full isolation between versions, but doubles storage and needs
  replication on a node that does not have the memory for it (ARCH-001).

## Consequences for other documents

- `WORKFLOW.md` §"Database migrations" states the rule and the four-step column-removal dance.
- `DATA-001` §"Migration policy" states the compatibility requirement.
- `CLAUDE.md` §4 forbids writing a destructive `downgrade()`.
- Block B2 creates the first migration under this rule and is where the
  `raise NotImplementedError` convention is established.

## Open questions

- Whether to add a CI check that fails a PR containing a non-empty `downgrade()` body.
  Cheap to write, and it turns a convention into a constraint. Revisit at B16 when CI exists.
