# ADR-004 — Decision Principle: Control Over Convenience

**Status**: Accepted
**Date**: 2026-08-21
**Related**: PRD-000, all infrastructure ADRs

## Context
The project's second required goal is to become a cloud engineer (Cloud / DevOps / SRE).
Managed AWS services are designed to hide exactly the layers that this role is expected to
understand. A design optimised purely for delivery speed would therefore defeat one of the
two required goals.

## Decision
**DP-1: when two options produce a similar result, choose the less automated one.** Layers
that a managed AWS service would hide are built by hand by default.

Managed or automated solutions are permitted in exactly three cases:

1. Doing it by hand would create **greater security risk** (e.g. manual TLS certificate
   issuance and renewal — use cert-manager).
2. The task has **no learning value and consumes significant time** (e.g. self-hosting CI
   runners).
3. The failure mode is **irreversible** (e.g. billing and payment controls).

**Whenever an exception is used, the ADR must include a paragraph describing what would have
been built by hand.** This keeps the convenience without discarding the understanding.

## Rationale
- Directly serves the stated career goal.
- Reduces cost as a side effect: ingress-nginx instead of ALB and in-cluster PostgreSQL
  instead of RDS each save more than the entire monthly budget.
- Produces genuine incident experience, which is what SRE interviews probe.

## Trade-offs
| Gained | Given up |
|---|---|
| Deep understanding of networking, orchestration, storage | Slower delivery |
| Substantially lower cost | Operational burden falls entirely on one person |
| Real operational stories | Some choices are non-standard for a production team |

## Alternatives rejected
- **Managed-first** — faster, but the layers hidden are precisely the ones being studied.
- **No exceptions at all** — unbounded scope; "do everything yourself" has no natural
  stopping point and would eventually consume the project.

## Boundary note
DP-1 governs infrastructure. It is not applied to application-layer libraries: SQLAlchemy and
Alembic are used rather than hand-written SQL migration scripts, because migration errors are
silent and destructive and the learning value there is low relative to the risk.
