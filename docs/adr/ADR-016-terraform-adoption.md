# ADR-016 — Terraform Adoption: Import over Rebuild

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-004, ADR-005, ADR-008, ADR-014, GAMEDAY-001

## Context

Block B15 says: "Reproduce B11–B14 infrastructure in Terraform." Blocks B11–B14 build everything
by hand in the console, deliberately (ADR-004). So at B15 there is live infrastructure with
real data on it, and no Terraform state.

"Reproduce" can mean two incompatible things, and the roadmap did not say which:

1. **Import** — write the configuration to match what exists, then `terraform import` each
   resource into state until `terraform plan` shows no changes.
2. **Rebuild** — `terraform apply` from scratch into a clean slate, deleting the hand-built
   resources.

They differ in downtime, in risk to the database, and in what is learned. The choice also
drags in a second undecided question: **where Terraform state lives.**

## Decision

**Import.** B15 writes configuration for the existing resources and imports them until
`terraform plan` reports no changes against the live account. Nothing is destroyed.

**State lives in S3** with versioning enabled, in the same bucket family as the backups but a
separate prefix, using S3's native state locking. **No DynamoDB table is created.**

## Rationale

### Why import

- **The database is on the hand-built data volume (ADR-014).** A rebuild means detaching and
  reattaching a volume holding weeks of collected postings, at a point in the project where
  the restore path has been drilled exactly once. Import touches nothing.
- **Import is where the learning is.** Anyone can `terraform apply` a tutorial. Reconciling
  configuration against infrastructure that already exists — discovering that the console set
  seventeen attributes you did not write down, that `plan` wants to replace the instance
  because of one default, that some attributes cannot be imported at all — is the actual
  skill. It is also the situation every real job presents: infrastructure exists, and it is
  not in code.
- **`terraform plan` returning empty against live infrastructure is a stronger visible result**
  than `apply` succeeding into an empty account. It proves the code describes reality.
- **It preserves the tags placed in B11.** `ManagedBy=console-b11` marks what has not yet been
  imported, so progress is measurable: the block is done when nothing carries that tag
  unimported.
- Rebuild capability is not lost — it is **tested separately and deliberately** by GameDay
  GD-4, which terminates the instance and rebuilds it from Terraform. That drill is the right
  place to find out whether the code really works, because it is scheduled, backed up, and
  expected to fail the first time.

### Why S3 state without DynamoDB

- State contains resource attributes and must not sit in git; the repository is on GitHub and
  the infra repository is reconciled by Flux (ADR-008), so a local state file would be both
  unshareable and unbacked-up.
- S3 versioning gives state history, which is the recovery mechanism that actually matters.
- Terraform supports S3-native locking, so the classic DynamoDB lock table is no longer
  required. A single-operator project has no concurrent-apply problem to solve anyway, and
  `CLAUDE.md` §5 forbids creating resources not listed in `ARCH-001`.
- Cost: a few kilobytes in an existing bucket. Effectively zero.

## Trade-offs

| Gained | Given up |
|---|---|
| No downtime, no risk to collected data | Import is slower and more tedious than starting clean |
| Learns the real-world "brownfield" IaC problem | Misses the satisfying "from nothing" apply — recovered in GD-4 |
| `plan` empty against live infra proves the code | Some console-set attributes may be un-importable and need documenting as drift |
| No DynamoDB table, no extra resource | No experience with the DynamoDB locking pattern, which is still common in older setups |

## Alternatives rejected

- **Rebuild from scratch** — cleaner code and a faster block, but it risks the data volume and
  discards the brownfield-reconciliation learning, which is the harder and more transferable
  skill. It is also unnecessary: GD-4 exercises the rebuild path safely later.
- **`terraform import` blocks in configuration (declarative import) only** — a good modern
  workflow and worth using where it fits, but plan-time import blocks are still best combined
  with iterative refinement; treat them as the mechanism, not an alternative decision.
- **Local state file** — simplest, no bucket. Rejected: no backup, no history, and it lives on
  a laptop that is not the deployment target.
- **Terraform Cloud free tier** — free, managed state, nice UI. Rejected under ADR-004: state
  management is a layer worth operating, no exception applies, and it adds a third-party
  dependency to the recovery path.
- **Pulumi or CDK** — legitimate and arguably nicer, but Terraform is what appears in
  Cloud/DevOps/SRE job postings, and this project's second required goal is employability.
- **Skipping IaC entirely** — the infrastructure is small enough to rebuild by hand. Rejected
  outright: reproducibility from code is a core competency for the target role, and GD-4's
  value depends on it.

## Scope note

Terraform manages **infrastructure** — VPC, subnets, routes, security groups, EC2, EBS
volumes, S3 buckets, IAM. It does **not** manage what runs inside Kubernetes; that is Flux's
job (ADR-008). The boundary is the node: Terraform makes the machine and its disks exist,
Flux makes the workloads exist. Straddling that line with a Terraform Kubernetes provider
would give two controllers opinions about the same objects.

The `mkfs` and `fstab` steps from ADR-014 sit exactly on the boundary. Decide at B15 whether
they become EC2 user-data (reproducible, but hides the manual step being learned) or stay a
documented manual step (honest, but a gap in "reproducible from nothing"). Record the choice
in the block's write-up.

## Open questions

- Whether to add `tflint` / `checkov` to CI at B16. Cheap, and static analysis findings on
  one's own infrastructure make good incident-adjacent material for a portfolio.
