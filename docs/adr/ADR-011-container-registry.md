# ADR-011 — Container Registry: GitHub Container Registry

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-004, ADR-008, ARCH-001, OPS-001, SEC-001

## Context

Block B9 builds container images, B13 pulls them into the cluster, and B16 has CI push new
tags that Flux propagates. **No document in this set said where images are stored.** The
architecture diagram had no registry, the cost model had no line for one, and the "never
create" list in `CLAUDE.md` did not mention ECR.

This is not a cosmetic gap. The choice has three consequences at once: monthly cost, a pull
credential that must be managed as a secret, and — in one case — a rate limit that makes
deployments fail non-deterministically.

Constraints: the budget ceiling is 30,000 KRW/month and already tight (ARCH-001); the
repositories already live on GitHub (ADR-008); the node has 2 GiB of RAM and cannot build
images itself.

## Decision

**Container images are published to GitHub Container Registry (`ghcr.io`) as private
packages, built by GitHub Actions, and pulled by the cluster with a read-only token stored
as an `imagePullSecret`.**

`ECR` is added to the prohibited-resource list in `CLAUDE.md` §5.

## Rationale

- **Free at this scale**, including private packages. The registry line in the cost model is
  $0, which matters when the total is within a rounding error of the ceiling.
- **Same identity as CI.** GitHub Actions can push with the built-in `GITHUB_TOKEN`; no
  additional cloud credential, no key rotation across providers.
- **No anonymous pull rate limit.** Docker Hub throttles anonymous pulls, so every node
  restart or image re-pull draws from a shared quota and deployments fail at unpredictable
  times. That failure mode is invisible in testing and appears during incidents.
- **Consistent with ADR-008's two-repository plan** — the registry lives alongside both.
- It does not hide any layer the owner is trying to learn: pushing, tagging, digests and
  pull secrets are all still done by hand.

## Trade-offs

| Gained | Given up |
|---|---|
| Zero cost; the budget line stays at $0 | No ECR experience, which appears in some job postings |
| One credential system instead of two | Registry availability is now coupled to GitHub |
| No rate-limit surprises during deploys | Images are outside AWS, so pulls cross the internet (negligible for two small images once a deploy) |

## Alternatives rejected

- **Amazon ECR** — the AWS-native answer and the one with the most résumé value, but it adds
  a storage and data-transfer line to a cost model with no room, and pulling from a public
  subnet without a VPC endpoint means internet egress anyway. Reconsider if the budget ever
  loosens, or as a short exercise in a lab account.
- **Docker Hub (free tier)** — free, but anonymous and free-tier pull limits turn image pulls
  into an intermittent, hard-to-diagnose deployment failure. Rejected on reliability, not
  cost.
- **Building images on the node** — no registry needed at all, but a Next.js production build
  will not fit in a 2 GiB node alongside everything else (ARCH-001 ledger). Not viable.
- **A self-hosted registry in the cluster** — maximum DP-1 purity, but it consumes memory
  that the ledger does not have and creates a bootstrap problem: the registry's own image
  has to come from somewhere.

## If a managed service was chosen (ADR-004 requirement)

`ghcr.io` is a managed registry, so this clause applies. Built by hand, this would mean
running `registry:2` behind TLS with authentication, its own persistent volume, garbage
collection of untagged layers, and a backup story — roughly 150–250 MiB of the node's memory
and a bootstrap dependency on itself.

The learning that would come from that is storage and TLS operation, both of which are
already exercised by the PostgreSQL StatefulSet (B9) and cert-manager (B8). Under ADR-004
exception 2 — significant time, low marginal learning — the managed option is accepted.

## Open questions

- Whether to mirror images into the cluster with a pull-through cache if pull latency ever
  becomes noticeable. Not expected at one deploy per day.
