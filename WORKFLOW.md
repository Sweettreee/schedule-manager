# WORKFLOW.md — How work is done in this project

**Last revised**: 2026-08-22 (after REVIEW-001, then ADR-017).

## Branching and commits

- `main` is always deployable. No direct pushes.
- One short-lived branch per block: `block/B4-classification-rules`.
- Pull request into `main`, CI must pass, self-merge is fine.
- Conventional Commits, in English:
  `feat:` `fix:` `docs:` `chore:` `refactor:` `test:` `ci:`
- Tag `main` at the end of each block: `b4-classification-rules`.

## Three tracks

Blocks are not a single chain. Three tracks run in parallel because they depend on different
inputs (BLOCKS-001 §2):

- **App track** (B1 → … → B8, plus B23, B24; then B20 → B21) depends on **collected mail
  volume**, which accumulates in wall-clock time and cannot be hurried.
- **Infra track** (B9 → B10 → … → B17) depends only on the previous infra block.
- **File track** (B14 → B18 → B19, plus conditional B25) depends on the infra track reaching
  a deployed API and S3.

When the app track is waiting for data, work the infra track. Never work two blocks at once
inside the same track.

## Definition of Done (every block)

A block is not finished until all of the following are true:

1. The visible outcome named in `BLOCKS-001` can be demonstrated.
2. Tests required by ADR-010 exist and pass in CI.
3. Any **GameDay drill** assigned to this block (`docs/GAMEDAY-001-failure-drills.md`) has
   been run, and its write-up exists in `docs/incidents/`.
4. Code merged into `main` through a pull request.
5. `STATUS.md` updated — what changed, what is next, what is blocked.
6. Any new decision recorded as an ADR, numbered sequentially.
7. `main` tagged.

Step 5 is the one that makes it possible to stop for a month and come back. Skipping it is
the single most expensive shortcut available in this project.

## Working with Claude Code

Per ADR and project charter, in every session:

1. Claude explains what it intends to do, why, what alternatives exist, and the trade-offs.
2. The owner approves.
3. Claude writes the code and shows the diff.
4. The owner reviews the diff before anything is committed.

Claude never commits or pushes without explicit approval. See `CLAUDE.md`.

## Testing

- `pytest` for the API and collector; unit tests plus testcontainers-backed integration tests.
- TDD is mandatory for filter and classification rules (ADR-010).
- Fixtures derived from real email must be anonymised per SEC-001 before being committed.
  Raw, un-anonymised mail lives only under `fixtures/raw/`, which is in `.gitignore`.
- CI runs lint, unit tests and integration tests on every pull request.

## Database migrations

Forward-only (ADR-015). To undo a bad schema change, write a **new** migration that corrects
it. `downgrade()` bodies are `raise NotImplementedError`. Application rollback
(`kubectl rollout undo`) therefore requires that every migration be **backwards compatible
with the previous application version** — add columns nullable, backfill, switch reads, and
only drop in a later release.

## Documentation rules

- Documents in English; UI strings in Korean.
- ADRs are numbered in the order decisions are made. Numbers are never reserved in advance
  for decisions not yet taken.
- **Blocks follow the same rule** (`BLOCKS-001` §3): numbers are assigned in creation order,
  and execution order is defined by the roadmap tables. A new block is appended, never
  inserted, so renumbering never happens again.
- An ADR is never edited to reverse a decision — write a new ADR and mark the old one
  `Amended by ADR-XXX` or `Superseded by ADR-XXX`. Correcting a factual error or adding a
  cross-reference is not a reversal and may be edited in place.
- Incidents and outages get a short write-up in `docs/incidents/`. **This includes planned
  GameDay drills** — see `docs/GAMEDAY-001-failure-drills.md`. For an SRE portfolio these
  are among the most valuable artefacts in the repository, and waiting for organic failures
  on a single-user system would leave the folder empty for months.

## Monthly operations review

Once a month (see OPS-001 §7): spend vs. ceiling, FX assumption still valid, orphaned
resources, backup freshness, SLO error-budget burn, and anything learned recorded in
`docs/incidents/` or a new ADR.
