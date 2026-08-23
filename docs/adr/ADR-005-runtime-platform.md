# ADR-005 — Runtime Platform: k3s on a Single EC2 Instance

**Status**: Accepted — **amended by ADR-014**
**Date**: 2026-08-21
**Related**: ADR-004, ARCH-001, ADR-013, ADR-014

## Context
Kubernetes experience is a stated goal. The monthly ceiling is 30,000 KRW (~$21).
EKS charges $0.10 per hour for the control plane alone — roughly $73/month before a single
pod runs, more than three times the entire budget. Kubernetes and cost minimisation are
therefore not simultaneously achievable through the managed path.

## Decision
Run **k3s on a single EC2 `t4g.small` instance** in `ap-northeast-2`, installed and operated
by hand. PostgreSQL runs in-cluster as a StatefulSet with an EBS-backed PVC. Ingress is
ingress-nginx on the node. Local development uses k3d or kind at zero cost.

## Rationale
- Fits the budget: roughly $22/month all-in versus $75+ for EKS.
- A single node is not production-grade Kubernetes, but it still exercises kubectl,
  Deployments, Services, Ingress, PVCs, rollouts, resource limits and failure recovery.
- Because k3s does not hide the pieces EKS manages, the learning density is arguably higher.
- Directly consistent with ADR-004.

## Trade-offs
| Gained | Given up |
|---|---|
| Real cluster operation within budget | No multi-node scheduling, no real HA |
| Full control of every layer | Node failure means total **outage** — accepted, since availability is not a requirement |
| Cost far below the ceiling for the compute layer | All upgrades and backups are manual |

**Outage is accepted; data loss is not.** This distinction was implicit and is now explicit.
Node failure taking the site down for hours is within PRD-000 §5. Node failure destroying
collected postings is not, because a lost week of postings is a week of missed deadlines —
the exact thing the system exists to prevent. PostgreSQL therefore lives on a separate,
`delete-on-termination = false` EBS volume: **ADR-014**.

## Alternatives rejected
- **EKS always on** — ~$73/month control plane; abandons the cost ceiling.
- **EKS for one month then delete** — realistic experience, but blows the budget for that
  month and leaves nothing running.
- **ECS Fargate** — cheaper and simpler, but it is not Kubernetes and hides the orchestration
  layer being studied.
- **Lambda + DynamoDB (serverless)** — by far the cheapest and a legitimate design for a
  once-a-day collector, but it eliminates the container and orchestration learning that is
  the point of the exercise.

## What would have been built by hand (ADR-004 clause)
Not applicable — this ADR chooses the manual option throughout. The one automated component
accepted is cert-manager for TLS, under exception 1; by hand this would mean generating a
CSR, completing an ACME challenge, installing the certificate and scheduling renewal before
expiry, where a missed renewal silently breaks the site.
