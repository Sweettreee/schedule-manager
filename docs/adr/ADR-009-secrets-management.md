# ADR-009 — Secrets Management: Staged Adoption of SOPS

**Status**: Accepted
**Date**: 2026-08-21
**Related**: ADR-004, ADR-008, SEC-001

## Context
Two secrets matter: the Gmail OAuth refresh token and the PostgreSQL password. Code must go
to GitHub; secrets must not. Note that Kubernetes Secrets are base64-encoded, not encrypted —
anyone with cluster access can read them.

## Decision
**Staged.** Start with Kubernetes Secrets kept out of git via `.gitignore`. **Migrate to
SOPS + age encrypted secrets committed to the infrastructure repository during the CI/CD
block (B16)**, when Flux is introduced.

## Rationale
- SOPS is the correct destination: it makes the cluster reproducible from git alone, which is
  what GitOps requires, and it costs nothing.
- Introducing it on day one would add an unfamiliar tool alongside AWS, k3s and Terraform,
  all new at once, making failures hard to attribute.
- By block B16 the need is concrete: Flux cannot reconcile a secret that is not in git, so
  the tool is learned at the moment its purpose is obvious.

## Trade-offs
| Gained | Given up |
|---|---|
| Fewer simultaneous unknowns early | One migration day later |
| SOPS learned when its purpose is evident | A window where secrets exist only on one machine |
| Ends at a fully reproducible cluster | The age master key becomes a single point of failure |

## Alternatives rejected
- **SOPS from day one** — correct, and only about half a day; rejected only on cognitive load
  sequencing. Acceptable to bring forward if B16 slips far.
- **AWS SSM Parameter Store** — free and audited, but conflicts directly with ADR-004 and
  couples local development to AWS.
- **HashiCorp Vault** — far beyond the needs of a single-user system, and the memory budget
  cannot absorb it.

## Mandatory follow-up
When SOPS is adopted, the age private key must be backed up outside the machine that
generated it. Losing it makes every encrypted secret permanently unreadable.
