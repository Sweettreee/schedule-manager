# WORKFLOW.md — How work is done in this project

**Last revised**: 2026-08-26 (uv toolchain — ADR-026 — replaces the pip/venv commands).

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

- **App track** (B1 → … → B8, plus B23, B24, **B26**; then B20 → B21) depends on **collected
  item volume**, which accumulates in wall-clock time and cannot be hurried. Since ADR-022 this
  is no longer mail-only: B3's scraper can backfill a notice board's existing pages, where a
  mailbox can only grow forward in time.
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

- `make test` in `api/` for the API and collector (it runs `pytest` through uv); unit tests plus
  testcontainers-backed integration tests. **Every Python command goes through `api/Makefile`,
  never bare `uv run`** — ADR-026 explains why, and the Makefile refuses to run if you forget.
- TDD is mandatory for filter and classification rules (ADR-010).
- Fixtures derived from real email must be anonymised per SEC-001 before being committed.
  Raw, un-anonymised mail lives only under `fixtures/raw/`, which is in `.gitignore`.
- CI runs lint, unit tests and integration tests on every pull request, and installs with
  `uv sync --locked` so a stale `uv.lock` fails the build instead of being re-resolved.

## Database migrations

Forward-only (ADR-015). To undo a bad schema change, write a **new** migration that corrects
it. `downgrade()` bodies are `raise NotImplementedError`. Application rollback
(`kubectl rollout undo`) therefore requires that every migration be **backwards compatible
with the previous application version** — add columns nullable, backfill, switch reads, and
only drop in a later release.

## Documentation rules

- Documents in English; **Korean is correct** for UI strings, enum labels (`DATA-001`), and goal
  statements where the Korean states the felt need more precisely than a translation would —
  *"까먹지 않는다"* is the requirement, not decoration. Do not translate those for consistency.
- ADRs are numbered in the order decisions are made. Numbers are never reserved in advance
  for decisions not yet taken.
- **Blocks follow the same rule** (`BLOCKS-001` §3): numbers are assigned in creation order,
  and execution order is defined by the roadmap tables. A new block is appended, never
  inserted, so renumbering never happens again.
- An ADR is never edited to reverse a decision — write a new ADR and mark the old one
  `Amended by ADR-XXX` or `Superseded by ADR-XXX`. Correcting a factual error or adding a
  cross-reference is not a reversal and may be edited in place.
  **This holds even for a same-day revision made before any implementation.** `ADR-022` was
  revised in place hours after being written, which left one file containing two contradictory
  ladders and a decision that reversed itself; a reference to "ADR-022" then meant two different
  things. It was split into `ADR-022` + `ADR-023` on 2026-08-25. The cost of a second ADR is one
  file; the cost of an ambiguous reference is every document that cites it.
- Incidents and outages get a short write-up in `docs/incidents/`. **This includes planned
  GameDay drills** — see `docs/GAMEDAY-001-failure-drills.md`. For an SRE portfolio these
  are among the most valuable artefacts in the repository, and waiting for organic failures
  on a single-user system would leave the folder empty for months.

## Monthly operations review

Once a month (see OPS-001 §7): spend vs. ceiling, FX assumption still valid, orphaned
resources, backup freshness, SLO error-budget burn, and anything learned recorded in
`docs/incidents/` or a new ADR.
