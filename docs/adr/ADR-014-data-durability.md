# ADR-014 — Data Durability: A Separate EBS Data Volume

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-004, ADR-005 (amends), ARCH-001, OPS-001, SEC-001, GAMEDAY-001

## Context

`ADR-005` accepts that a single node means "node failure means total outage". `ARCH-001`
showed `postgres (StatefulSet + PVC on EBS)` and a single line item, "EBS gp3 20 GiB".

Those two statements are compatible with two very different implementations, and nobody had
chosen between them:

| Implementation | Where the data actually lives | If the instance is terminated |
|---|---|---|
| k3s default `local-path` provisioner | a directory on the node's **root** EBS volume | **destroyed** — root volumes default to delete-on-termination |
| `aws-ebs-csi-driver` with dynamically provisioned volumes | an independent EBS volume per PVC | survives, reattaches |

So the question ADR-005 never answered: **outage is accepted, but is data loss accepted?**

It is not. A lost database is a lost backlog of postings, and a week of lost postings is a
week of missed deadlines — the specific harm this system exists to prevent (PRD-000 P-2, M-2).
Availability was traded away deliberately; durability never was.

Backups alone do not close this. With a daily dump the exposure is up to 24 hours of
collection (OPS-001 RPO), and every instance replacement would become a restore operation
rather than a reattach.

## Decision

**PostgreSQL data lives on a second, dedicated EBS gp3 volume (10 GiB) with
`delete-on-termination = false`, mounted at `/mnt/data`, with k3s's `local-path` provisioner
configured to use `/mnt/data/local-path-provisioner` as its storage root.**

The root volume stays at 12 GiB with delete-on-termination `true` and holds only the OS, k3s
and the container image cache — all of which are reproducible.

The EBS CSI driver is **not** installed.

## Rationale

- **The recovery story becomes a reattach, not a restore.** Node replacement is: terminate,
  launch, attach the data volume, mount by UUID, install k3s, let Flux reconcile. The
  database comes back as it was, with zero data loss, well inside the 4-hour RTO.
- **local-path over the CSI driver** keeps DP-1 intact (ADR-004). The CSI driver is a
  controller that creates and attaches volumes automatically — convenient, and exactly the
  layer worth understanding. Doing it by hand means learning EBS attach/detach, device naming
  under NVMe, filesystem creation, `blkid`, and `fstab` semantics — including the `nofail`
  option, without which a missing volume makes the instance unbootable into an SSH-able
  state. That is a genuinely useful afternoon.
- **The dynamic provisioning the CSI driver provides has no value here.** There is one
  stateful workload and one node. Dynamic volume creation solves a problem this architecture
  does not have.
- **Cost is negligible**: splitting 22 GiB across two volumes instead of one costs the same
  per GiB; the only change is about $0.9/month for the extra headroom.
- **It is testable.** GameDay **GD-4** terminates the instance and rebuilds it. Either the
  data comes back or this ADR is wrong, and it is much better to find that out in a drill
  than during a real failure.

## Trade-offs

| Gained | Given up |
|---|---|
| The database survives losing the node | One more resource to create, tag and remember |
| Instance replacement is a reattach (minutes), not a restore (hours) | The volume is AZ-bound: a new instance must launch in `ap-northeast-2a` |
| Hands-on EBS, filesystem and fstab experience (ADR-004) | No EBS CSI driver experience, which does appear in job postings |
| Backups become a second line of defence rather than the only one | A manual mount step exists that Terraform will need to reproduce or document (B15) |

The AZ constraint is the sharpest edge: if `ap-northeast-2a` has a capacity problem, recovery
requires a snapshot-and-restore into another AZ rather than a reattach. That path is exercised
by GD-3 (timed restore), so it is not untested.

## Alternatives rejected

- **k3s default local-path on the root volume** — simplest, zero extra resources, and the
  status quo. Rejected because it silently makes instance termination a data-loss event, and
  because "we accepted the outage" would then be quietly extended into "we accepted the data
  loss", which nobody decided.
- **`aws-ebs-csi-driver` with dynamic provisioning** — the production-standard answer and the
  one that would transfer best to a multi-node cluster. Rejected under DP-1: it automates
  precisely the storage-attachment layer worth learning, while solving a scaling problem that
  does not exist at one node and one PVC. Reconsider if the cluster ever gains a second node.
- **RDS** — removes the problem entirely and is explicitly prohibited by `CLAUDE.md` §5 on
  both cost (~$15+/month) and ADR-004 grounds.
- **Backups only, no separate volume** — accepts up to 24 hours of loss on every instance
  replacement and makes every rebuild a restore. Backups remain, but as the second line.
- **EFS** — multi-AZ and survives everything, but it is a managed NFS service with per-GB and
  per-request pricing, and PostgreSQL on NFS is a well-known bad idea.

## Implementation

Specified in `docs/blocks/B10-B11-specs.md` §B11 task 5, including the `fstab` line and the
mandatory reboot verification. Terraform reproduces it at B15 (ADR-016), where the manual
`mkfs` step must be either scripted in user-data or documented as a deliberate manual step —
a decision to record when B15 is reached.

## Open questions

- Whether to take periodic **EBS snapshots** of the data volume in addition to `pg_dump`.
  A snapshot is crash-consistent, not transaction-consistent, so it is not a substitute for
  a dump, but it makes whole-volume recovery faster. Cost is a few cents a month. Revisit at
  B13 once dump sizes are known.
