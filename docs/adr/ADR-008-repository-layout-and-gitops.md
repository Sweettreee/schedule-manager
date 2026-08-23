# ADR-008 — Repository Layout and GitOps

**Status**: Accepted
**Date**: 2026-08-21
**Related**: ADR-004, ADR-005, ARCH-001

## Context
GitOps is a core Cloud/DevOps/SRE competency. But splitting repositories by itself is not
GitOps: two repositories with `kubectl apply` run by hand is just two folders. GitOps
requires a controller that watches the infrastructure repository and reconciles the cluster
to match it.

## Decision
**Two repositories** — an application repository and an infrastructure repository — with
**Flux** as the GitOps controller.

**The split happens at the start of Phase 2, not now.** During Phase 1 everything is local
and the infrastructure repository would be empty.

## Rationale
- The split only produces learning when paired with a controller, so the two decisions are
  made together.
- Flux is chosen over ArgoCD purely on memory: ArgoCD with its UI needs roughly 500 MiB–1 GiB
  and does not fit the 2 GiB node; Flux runs in roughly 100–200 MiB.
- The genuinely instructive problem — how a CI pipeline propagates a new image tag into the
  infrastructure repository — only appears in this arrangement.
- Delaying the split to Phase 2 costs nothing: moving folders into a new repository is cheap,
  while maintaining an empty second repository is pure overhead.

## Trade-offs
| Gained | Given up |
|---|---|
| Real GitOps: cluster state is reconciled from git | Changes spanning app and manifests need two PRs and ordering care |
| Cluster is reproducible from git after total loss | Roughly 10–30 minutes of overhead per deployment-related block |
| Directly relevant interview experience | One to two extra sessions in the CI/CD block |

## Alternatives rejected
- **Monorepo throughout** — simplest, and fine for a solo project, but skips the GitOps
  pattern that is a stated learning goal.
- **Splitting immediately** — no benefit while the infrastructure repository is empty.
- **Three repositories (api / web / infra)** — independent deployment per service, but
  excessive coordination cost for one person.
- **ArgoCD** — better UI and more common in job postings, but does not fit the memory budget.
  Worth revisiting if the node is ever resized.
