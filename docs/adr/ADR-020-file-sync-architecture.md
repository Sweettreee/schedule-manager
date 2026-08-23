# ADR-020 — File Synchronisation: Content-Addressed Storage with Presigned Direct Transfer

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-003, ADR-004, ADR-005, ADR-014, ADR-015, ADR-017, ARCH-001, SEC-001

## Context

The owner has named file synchronisation as one of the most important capabilities, for two
reasons that both matter here: it solves a real problem (course materials scattered across
an LMS, a laptop and a tablet), and it is **the single richest cloud-engineering curriculum
in the project** — object storage, IAM, delegated authorisation, content addressing,
client-side state, and eventually distributed conflict resolution.

`ADR-001` deferred it as "the largest and least understood piece", and that was correct as a
statement about *full* synchronisation. It is not correct about all of it. Synchronisation is
a ladder, and the rungs differ enormously in difficulty:

| Level | Capability | Hard part |
|---|---|---|
| **L0** | Web locker — upload and download in a browser | Object storage, IAM, presigned URLs |
| **L1** | One-way agent — a laptop folder is watched and uploaded automatically | Filesystem watching, hashing, incremental state, retry/idempotency |
| **L2** | Pull sync — another device downloads what it does not have | Manifests, drift detection |
| **L3** | Two-way with conflict resolution | Causality tracking, merge policy, deletion semantics |

Stated constraints:

- **v1 target: L0 + L1.** L2 and L3 are later milestones of a project explicitly described as
  long-running and incrementally improved, not a short MVP.
- **Devices: a laptop plus an iPad/tablet, both used for editing.**
- **Volume: course materials, roughly 2–5 GB per semester.**
- The node is a `t4g.small` with about 415 MiB of spare memory (ARCH-001) and a 10 GiB data
  volume that already holds PostgreSQL.
- The monthly ceiling is 30,000 KRW and already tight.

### The honest problem with the stated target

**L1 alone does not deliver "editing on two devices".** A one-way agent pushes from the
laptop; nothing brings an iPad's edits back. Worse, an iPad cannot realistically run a sync
agent at all — iOS does not give a background app the filesystem access this requires.

So the real shape of v1 is:

> **Laptop → agent → cloud → iPad reads and uploads through the browser.**

That is a coherent and useful system, and it is honest to call it what it is: a **one-writer**
system with web access everywhere else. Two-device *editing* arrives at L3.

This matters for a decision that must be made now, not later: because migrations are
forward-only (ADR-015), the storage model has to be able to represent multi-device,
multi-version history from the first migration, **even though v1 does not use it.**

## Decision

**Content-addressed blob storage in S3, with metadata in PostgreSQL, and file bytes moving
directly between client and S3 via presigned URLs — never through the EC2 node.**

Four tables, created together in the file milestone's first migration:

| Table | Holds |
|---|---|
| `blobs` | one row per distinct content, keyed by `sha256`. The S3 object key **is** the hash |
| `files` | one row per logical path, pointing at the current version |
| `file_versions` | every version ever seen: which blob, which device, when |
| `devices` | registered devices, so every version knows its origin |

**Upload protocol** (this is the part worth learning):

```
1. client hashes the file locally              → sha256
2. client asks the API: "do you have <sha256>?"
3a. yes  → API links a new file_version to the existing blob.
           ZERO bytes transferred. Done.
3b. no   → API returns a presigned S3 PUT URL (5-minute expiry)
4.  client uploads DIRECTLY to S3. The bytes never touch the EC2 node.
5.  client confirms; API verifies size/ETag and commits the blob row.
```

Download is the mirror: the API returns a presigned GET URL and the browser or agent fetches
from S3 directly.

**Every file also becomes an `items` row with `type = 'FILE'`**, so unified search covers
files without a second search implementation (ADR-003).

**v1 conflict policy**: none is *resolved*, but conflicts are never *lost*. If two versions of
the same path arrive from different devices, both are retained as `file_versions` rows and the
UI shows the divergence. Deleting is a soft delete (`deleted_at`), never a blob deletion.

**Level scope**: L0 in block B14, L1 in block B18, version history and restore in B19.
L2 and L3 are Phase 4+ milestones with their own ADRs.

## Rationale

### Why bytes must not pass through the node

The node has 2 GiB of RAM and about 415 MiB spare. Proxying a 200 MB lecture video through a
FastAPI process would either buffer it into memory or spool it onto the same 10 GiB volume
PostgreSQL lives on. Both are how a small node dies.

Presigned URLs are the correct answer and are also **exactly the concept worth learning**:
the server never sees the bytes, but still decides who may write what, where, and for how
long. It is delegated authorisation, and it generalises far beyond this project.

### Why content addressing

- **Deduplication is free.** The same lecture PDF downloaded twice, or the same file present in
  two folders, stores once.
- **Re-uploading an unchanged file costs zero bytes** — step 3a. For an agent that rescans a
  folder on every run, this is the difference between a cheap sync and a bandwidth bill.
- **Version history is free.** Keeping every `file_versions` row costs a few hundred bytes
  each; the blobs are shared. "Restore last week's version" becomes a metadata operation.
- **Integrity is free.** The key *is* the checksum, so corruption is detectable by definition.
- This is how Git, Dropbox, IPFS and every serious sync system works. Learning it once pays
  out repeatedly.

### Why the metadata split (S3 for bytes, PostgreSQL for structure)

Object storage cannot answer "what changed since Tuesday" or "show me every version of this
path". A relational table can, cheaply, and it is already running. Keeping the two separate
is the standard pattern and makes each side replaceable.

### Why device identity and versions exist in v1 even though v1 has one writer

Adding a column later is easy under ADR-015. **Retrofitting *meaning* is not.** If v1 stores
"the current bytes for a path" with no device or version, then L3 later cannot answer "did
these two edits descend from a common ancestor?" for any file that existed before the change.
Recording `device_id` and a version chain from the first row costs almost nothing now and is
the difference between L3 being an addition and L3 being a rewrite.

### Cost

At 5 GB in `ap-northeast-2`:

| Line | Estimate |
|---|---|
| S3 Standard storage, 5 GB | ~$0.13/month |
| PUT/POST requests (agent, ~2,000/month) | <$0.01 |
| GET requests | <$0.01 |
| Egress to the internet | Covered by AWS's 100 GB/month free allowance at this volume |
| **Added to ARCH-001** | **≈ $0.2/month** |

Egress is the line that can bite, and it is bounded here by the 2–5 GB working set. A hard
guardrail is added to OPS-001: an S3 storage alarm at 10 GB and an egress alarm, because the
failure mode is a buggy agent in a retry loop, not normal use.

### Learning value, stated explicitly

This is why the capability is in v1 rather than deferred:

| Block | What is actually learned |
|---|---|
| B14 (L0) | S3 buckets and policies, prefix-scoped IAM, presigned URLs, SSE encryption, lifecycle rules, CORS |
| B18 (L1) | Filesystem watching, incremental hashing, client-side state that survives crashes, idempotent retry, multipart upload |
| B19 | Version history, restore, blob garbage collection by reference count |
| L2/L3 later | Manifests, drift detection, causality, merge policy — distributed-systems fundamentals |

## Trade-offs

| Gained | Given up |
|---|---|
| Files never touch the 2 GiB node; the node cannot be killed by a large upload | A more complex, three-round-trip upload protocol than a naive POST |
| Deduplication, version history and integrity checking all fall out of one design choice | Blob garbage collection becomes a real problem (solved by `ref_count` in B19) |
| L2 and L3 become additions rather than rewrites | Four tables and a device registry exist before v1 uses most of them |
| The richest cloud curriculum in the project, on real data the owner cares about | Phase 3 grows; the project gets longer before it is "finished" — accepted, since it is explicitly never finished |
| ~$0.2/month | A new egress-shaped cost risk that needs its own alarm |

**The sharpest given-up**: v1 is honestly a one-writer system. The iPad reads through the
browser and can upload, but "edit the same file on both devices and have it just work" is L3.
Calling v1 "iCloud-like" would be overselling it, and this ADR declines to.

## Alternatives rejected

- **Store files in PostgreSQL as `bytea` / large objects.** One system instead of two, and
  backups cover files automatically. Rejected: it would put 5 GB on the 10 GiB data volume
  that PostgreSQL shares, blow up every `pg_dump` (breaking the 4-hour RTO in OPS-001), and
  make the database the bottleneck for every download.
- **Store files on the EBS data volume and serve them from the node.** Simplest, no S3, and
  maximally DP-1. Rejected on two counts: it consumes the same volume PostgreSQL needs, and
  it puts file bytes through a 2 GiB node. It also skips object storage, which is the single
  most transferable cloud skill on the list — this is not a layer worth avoiding, it is the
  layer worth learning.
- **Upload through the API and have the API forward to S3.** Simpler client, one round trip.
  Rejected: memory and disk pressure on the node, and it discards the presigned-URL concept
  that is the whole point of the exercise.
- **Path-addressed storage (S3 key = the file path).** Simplest mental model. Rejected: no
  deduplication, no version history without a naming scheme invented on the spot, no integrity
  guarantee, and renames become copies.
- **Use an existing sync tool (Syncthing, rclone, Nextcloud).** Solves the problem today and
  well. Rejected under ADR-004 with no exception applying: the owner's stated reason for
  wanting this feature is to *build* it. Nextcloud additionally needs several hundred MiB the
  memory ledger does not have.
- **iCloud / Google Drive with an API integration.** Zero infrastructure. Rejected for the
  same reason, and it makes the project dependent on a consumer sync product's API terms.
- **Full L3 two-way sync in v1.** What the owner ultimately wants. Rejected as a *v1* target
  because conflict resolution without real usage data is speculative design — the same
  reasoning ADR-003 applied to cross-source deduplication and ADR-017 applied to AI
  classification. Build L0/L1, generate real conflicts, then design L3 against them.

## If a managed service was chosen (ADR-004 requirement)

S3 is a managed service, so this clause applies.

Built by hand this would mean running an object store — MinIO or Ceph — on the node: its own
process, its own disks, replication or acceptance of single-disk data loss, its own IAM-like
policy layer, its own TLS, and its own backup. MinIO alone wants several hundred MiB, which
the ARCH-001 ledger does not have, and it would sit on the same 10 GiB volume as PostgreSQL,
recreating the exact problem this ADR exists to avoid.

This falls under **ADR-004 exception 2** (significant time, low marginal learning *relative to
the alternative use of that time*): the transferable skill is using object storage correctly —
policies, presigned URLs, lifecycle, storage classes — not reimplementing one. The
understanding is preserved by recording here what a self-hosted object store would have to
provide: content-addressed placement, durable replication, an authorisation layer capable of
issuing scoped time-limited grants, and lifecycle management.

MinIO does return as a **local development dependency** (docker-compose) so that L0 and L1 can
be built and tested before any AWS spend — the same "prove it locally first" pattern as
block B9.

## Open questions

- **Blob garbage collection policy.** `ref_count` reaching zero makes a blob unreferenced, but
  deleting immediately makes "undo a delete" impossible. Proposed: unreferenced blobs move to
  a lifecycle-managed prefix and expire after 30 days. Decide in B19 with real numbers.
- **Storage class.** Everything starts in S3 Standard. Whether last-semester's materials should
  transition to Standard-IA or Glacier Instant Retrieval is a question for the first monthly
  review after B14, not now.
- **Large-file threshold for multipart upload.** Conventionally 100 MB; confirm against actual
  lecture-video sizes in B18.
- **L3 conflict policy.** Deliberately undecided. The trigger to design it is the first real
  conflict observed in `file_versions`, which is exactly the evidence v1's "keep both, resolve
  nothing" policy is designed to produce.
