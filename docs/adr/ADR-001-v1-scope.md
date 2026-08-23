# ADR-001 — Scope of v1

**Status**: Accepted — **amended by ADR-017 (2026-08-22)**
**Date**: 2026-08-20
**Related**: PRD-000, REQ-001, ADR-017

> **Amendment note.** The scope decision below is superseded by **ADR-017**, which expands v1
> to all three capabilities. One of the rationale bullets here — *"it is the capability with
> the highest daily value to the user"* — was factually wrong, and only the owner could know
> that; he has since stated the reverse ordering. The bullet about file synchronisation being
> the largest unknown was **half right**: it is true of two-way conflict resolution, and not
> true of a web locker or a one-way agent (ADR-020). The "build ingest first" sequencing
> survives, but on re-derived grounds. Left unedited below as the record of what was believed
> on 2026-08-20.

## Context
The product has three intended capabilities: job/announcement collection, schedule and file
management, and unified search. Building all three at once produces three half-finished
features and no usable tool.

## Decision
v1 is limited to **job and announcement collection**. Schedule and file synchronisation move
to later milestones.

## Rationale
- Collection is the ingest side of the pipeline; the other two are read views over the same
  data, so building collection first makes them cheaper later (ADR-003).
- It is the capability with the highest daily value to the user, which drives habit formation.
- File synchronisation is the largest and least understood piece; deferring it removes the
  largest source of schedule risk.

## Trade-offs
| Gained | Given up |
|---|---|
| A usable tool within weeks | P-3 (scattered files) unaddressed for now |
| Reduced risk and clearer learning sequence | The "one place for everything" promise is delayed |

## Alternatives rejected
- **Build all three in parallel** — three unfinished features, no usable product, and
  resuming after a pause becomes very expensive.
- **Start with file sync** — highest complexity, lowest immediate payoff.
