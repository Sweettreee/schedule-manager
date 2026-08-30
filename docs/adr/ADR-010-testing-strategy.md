# ADR-010 — Testing Strategy: Conditional TDD

**Status**: Accepted
**Date**: 2026-08-21
**Related**: REQ-001, DATA-001

## Context
The project charter requires tests with every implementation. The question is how much and in
what style. TDD pays off in proportion to two things: whether the expected output is known
before the code exists, and how much of the code is pure logic. Assessed by area:

| Area | Expected output known in advance? | TDD fit |
|---|---|---|
| Filter rules (CS include, AI ∩ ¬CS exclude) | Yes — specified in REQ-001 | Excellent |
| Classification rules (sender to tab) | Yes | Excellent |
| Deduplication | Yes, but needs a database | Moderate |
| Email body parsing | **No** — the shape is discovered by reading real mail | Poor initially |
| Gmail OAuth integration | No | Poor |
| Next.js UI | No — judged visually | Poor |
| k3s, Terraform, Flux, observability | Not applicable | None |

Two structural facts follow. First, this codebase has low pure-logic density; most of it sits
against external boundaries. Second, parsing cannot be driven by tests first, because the
specification does not exist until real messages have been read.

## Decision
**Conditional TDD, with unit and integration tests.**

1. **TDD is mandatory** for filter and classification rules.
2. **Test-after** for parsing, API endpoints and UI.
3. **Integration tests against a real PostgreSQL** via testcontainers, covering exactly three
   paths: (a) mail fixture to Item to database, with re-collection correctly ignored;
   (b) the list API returning correct results for tab, sort and date filters;
   (c) incremental collection — the second run fetches strictly fewer messages than the
   first, and a `FAILED` run does not advance the cursor (added 2026-08-22 with FR-13; a
   cursor that advances on failure silently skips a day of mail, which is the same class of
   silently-wrong-data failure this ADR exists to catch).
4. **No browser E2E tests.**
5. **Bug rule**: on finding a misclassification or parse error, first add the offending
   message as an anonymised fixture and write a failing test, then fix the rule. This is the
   only form of TDD that reliably survives in a solo project.
6. The Gmail API is never called in tests; recorded anonymised fixtures are used.
7. **"Poor TDD fit" never means "no tests"** *(added 2026-08-30)*. An area this ADR rates poorly
   still gets every assertion that can be made **without a network** — above all the ones that
   protect a **safety property**: a scope that must not widen, a secret that must not be written
   outside its gitignored directory, a credential that must be rejected rather than stored. Those
   are not design-driving tests, which is why TDD does not fit; they are regression locks on
   properties whose breach is silent. `CLAUDE.md` §2 rule 4 forbids calling work done without
   tests, and this item is how that rule and the table above coexist.

## Rationale
- The worst failure mode here is not an exception but **silently wrong data** — a duplicate
  stored twice, a timestamp off by nine hours, a `jsonb` field written in the wrong shape.
  Mocked unit tests pass straight through all of those; only a real database catches them.
- Integration tests are cheap here because Docker is already familiar, and running them in CI
  is itself relevant SRE experience.
- Full TDD was rejected because TDD discipline is not one of the project's three goals, and
  the time it consumes comes directly out of cloud learning.

## Trade-offs
| Gained | Given up |
|---|---|
| Catches the failure class that actually threatens this project | Roughly 1.5x the time of unit tests alone |
| Regression safety as rules accumulate | UI regressions are not caught automatically |
| CI pipeline experience with service containers | Slower CI runs |

## Alternatives rejected
- **Unit tests only** — cannot verify the `UNIQUE` constraint behaviour, timezone conversion,
  or `text[]`/`jsonb` handling, which is where the real risk lives.
- **Full TDD** — impossible for parsing and inapplicable to infrastructure, which together
  are most of the work.
- **Adding browser E2E** — low value for a single-user dashboard, high maintenance cost.

## Worked example — B1 *(added 2026-08-30)*

`B1` is the first block to exercise decision item 7, so it is worth naming. The table above rates
Gmail OAuth a **poor** TDD fit and `B0-B8-specs` §B1 asks only for a smoke run — yet the block
ships six unit tests. They are not a contradiction: none of them drove a design decision, and
none of them calls Google. Each locks a property whose breach would be invisible — the
`gmail.readonly` scope widening, the token landing outside `.secrets/`, or a refresh-token-less
grant being stored and then dying silently on day eight (the `ADR-007` trap).
