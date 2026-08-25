# ARCH-001 — Target Architecture, Memory Ledger and Cost Model

**Status**: Approved (Phase 2 target)
**Last updated**: 2026-08-25 (ADR-024: nightly shutdown adopted into the design; cost model
rebuilt; Elastic IP added)
**Related**: ADR-004, ADR-005, ADR-006, ADR-008, ADR-011 … ADR-014, ADR-018, ADR-020, **ADR-024**

## Changes in this revision

The previous memory table omitted the operating system, cert-manager, the collector pod and
the observability stack. Adding them showed the design did **not** fit in 2 GiB. This
revision (a) makes the ledger complete, (b) replaces Prometheus+Grafana with
VictoriaMetrics (ADR-013), (c) adds the container registry that was missing from the whole
document set (ADR-011), (d) adds the separate data volume (ADR-014), and (e) states the FX
assumption behind the KRW ceiling.

---

## Phase 1 — local (cost: 0 KRW)

```
[ Gmail API ]
      |
      v
[ collector (Python, local process or container) ]
      |
      v
[ PostgreSQL in Docker ]  <----  [ FastAPI ]  <----  [ Next.js ]  -> localhost:3000
```

Nothing runs in the cloud. The pipeline is proven here first, and several weeks of real
usage produce the data on which later decisions are based.

## Phase 2 — AWS (target)

```
   [ GitHub ]                                  [ healthchecks.io ]
   |  Actions: build + push                    |  dead man's switch (ADR-012)
   |         |                                 |  alerts if no ping in 30h
   v         v                                 ^
[ ghcr.io ]  [ infra repo ] <--- Flux ---+     | ping on every successful run
   |  images    manifests                |     |
   |                                     |     |
   +------------- pull ------------+     |     |
                                   |     |     |
                Internet           v     v     |
                    |     +--------------------|-----------+
                    v     |  EC2 t4g.small, ap-northeast-2 |
        [ ingress-nginx ] |  Ubuntu 24.04 LTS (arm64)      |
          TLS: cert-manager / Let's Encrypt                |
          Basic Auth (k8s Secret)                          |
                          |  k3s (single node)             |
                          |   +- web        (Next.js)      |
                          |   +- api        (FastAPI)      |
                          |   +- collector  (CronJob, 24h) |
                          |   +- postgres   (StatefulSet)  |
                          |   +- victoria-metrics + node-exporter (ADR-013)
                          |   +- flux controllers          |
                          +--------------------------------+
                             |                    |
              root EBS 12GiB |                    | data EBS 10 GiB (ADR-014)
              OS, k3s, images|                    | /mnt/data -> PostgreSQL PVC
                                                  |
                                                  v
                                          [ S3 ] daily pg_dump
                                                 + content-addressed file blobs

   File transfer never passes through the node (NFR-12, ADR-020):

   [ laptop agent ] --1. "do you have sha256:abc?"--> [ api ]
                    <--2a. yes: linked, 0 bytes-------
                    <--2b. no: presigned PUT URL------
                    -----3. PUT bytes DIRECTLY------> [ S3 ]
```

Deliberately **not** used, per ADR-004 and ADR-005: EKS, ECS/Fargate, RDS, ALB, NAT Gateway,
ACM, ECR. Each is replaced by something operated by hand, which is the point.

---

## Memory ledger — the real constraint

`t4g.small` has 2,048 MiB. After kernel and firmware reservation, roughly **1,950 MiB** is
usable. Two figures matter and they are not the same:

- **System floor** — the OS plus k3s itself, before any workload: **~700 MiB**
- **Workload budget** — what is left for pods: **1,950 − 700 = 1,250 MiB**

`requests` are what the scheduler reserves and are the number that must fit.
`limits` are ceilings and may sum above RAM (deliberate overcommit); they exist to stop one
pod taking the node down.

| Component | requests | limits | Notes |
|---|---|---|---|
| postgres | 200 Mi | 400 Mi | `shared_buffers=128MB`, `max_connections=30` |
| api (FastAPI) | 100 Mi | 200 Mi | 2 uvicorn workers |
| web (Next.js) | 120 Mi | 250 Mi | production build, standalone output |
| ingress-nginx | 60 Mi | 120 Mi | |
| cert-manager (3 pods) | 60 Mi | 120 Mi | controller + webhook + cainjector |
| flux (4 controllers) | 100 Mi | 200 Mi | source, kustomize, helm, notification |
| victoria-metrics | 80 Mi | 150 Mi | 7-day retention (ADR-013) |
| node-exporter | 15 Mi | 30 Mi | DaemonSet |
| collector (CronJob) | 100 Mi | 200 Mi | only while a run is in flight |
| **Total requests** | **835 Mi** | | vs. a 1,250 Mi workload budget → **415 Mi headroom (33%)** |
| grafana (on demand) | — | 150 Mi | scaled to 0 replicas by default; started only when a dashboard is actually being read |

**Rules that keep this true:**

1. Every pod has both `requests` and `limits`. A pod without them is a bug.
2. k3s is installed with `--disable traefik --disable servicelb --disable metrics-server`.
   Traefik is replaced by ingress-nginx, servicelb is unnecessary on a single node, and
   metrics-server is replaced by node-exporter + VictoriaMetrics. This alone saves
   roughly 150–200 MiB.
3. **Swap is off.** The previous revision suggested enabling swap "as a safety net"; that
   was wrong on two counts — kubelet refuses to start with swap enabled unless explicitly
   configured, and PostgreSQL paged to swap degrades by orders of magnitude, turning a
   memory problem into a mystery latency problem. The safety net is `limits` plus the B9
   measurement gate, not swap.
4. This table is a **ledger, not an estimate**. Block B9 replaces every figure with a
   measured value and records the measurement date. Any block that adds a pod adds a row
   first.

### The B9 gate

Block B9 runs the **full production composition locally on k3d** — including cert-manager,
Flux and VictoriaMetrics, not just the three application pods — and measures actual usage.

> **Gate**: if measured steady-state usage exceeds **1,250 MiB**, this document is rewritten
> and `t4g.small` is re-decided **before** the AWS account is created in B10.

The previous "roughly 1.2 GiB" figure was measuring a different system: the app-only stack
without the platform components that dominate the ledger.

---

## Cost model

**Verified 2026-08-21. Figures are estimates to be confirmed in the AWS Pricing Calculator
during block B10 and replaced with actuals from Cost Explorer after the first full month.**

### FX assumption

> **1 USD = 1,400 KRW**, reviewed monthly (OPS-001 §7).
> The 30,000 KRW ceiling is therefore an effective **USD 21.4/month**.

This assumption exists because the ceiling is denominated in KRW while every cost is billed
in USD. Without it, "30,000 KRW" is not a testable condition, and a 5% FX move breaches a
"hard ceiling" with no change to the architecture at all.

### Monthly estimate

**The instance runs 18 of 24 hours** — stopped 02:00–08:00 KST, by design (**ADR-024**). Only the
compute line is affected; storage and the IPv4 address bill whether the instance runs or not.

| Item | USD | Note |
|---|---|---|
| EC2 `t4g.small` on-demand, Seoul, **18 h/day** | **~11.4** | $15.2 at 24×7 × 0.75. Seoul is ~20–25% above `us-east-1`'s $0.0168/hr |
| EBS gp3 root, 12 GiB | ~1.1 | OS, k3s, container images |
| EBS gp3 data, 10 GiB (ADR-014) | ~0.9 | PostgreSQL PVC |
| **Elastic IP, permanently attached** (ADR-024) | ~3.7 | $0.005/hr since 2024, billed in use or not. Required because a stopped instance loses an auto-assigned address |
| S3 daily backups (<1 GiB, lifecycle-expired) | <0.2 | |
| **S3 file storage, 5 GB Standard (ADR-020)** | **~0.15** | course materials, one semester |
| **S3 requests (agent, ~2k PUT + GET/month)** | **<0.02** | |
| **LLM extraction (ADR-018)** | **~0.3** | capped at 300 calls/month; worst case ~$1 |
| Data transfer out (single user) | <0.5 | file egress at 5 GB sits inside AWS's 100 GB/month allowance |
| Container registry (ghcr.io) | **0** | ADR-011 — this line is why ECR was rejected |
| Dead man's switch (healthchecks.io free) | **0** | ADR-012 |
| **Total** | **≈ 18.3** | **≈ 25,600 KRW at 1,400** |

**The design is inside the 30,000 KRW ceiling, with about 15% margin** — and it is inside only
because of the shutdown. Run 24×7, the same architecture totals **≈ $22.1 ≈ 30,900 KRW**, which
breaches NFR-1 by about 3%. That list figure is kept deliberately: it is what `OPS-001` §3's
escalation ladder measures against if the schedule ever stops working.

The overage was in this design from the day it was written, and the document said so rather than
rounding down. **ADR-024 fixes it by spending a trade the project had already made** —
`PRD-000` §5 declares availability a non-goal — rather than by moving the ceiling, which
`OPS-001` §3 forbids.

### Credits change the sequencing, not the arithmetic

New AWS accounts choose a **Free plan** or a **Paid plan**; both receive $100 in credits at
sign-up plus up to $100 more for completing onboarding activities, and credits expire
12 months after account creation. The old 12-month free tier applies only to accounts created
before 15 July 2025.

**Choose the Paid plan.** The Free plan ends after six months or when credits run out, and
the account is then closed automatically — which would destroy a project intended to run
continuously. On the Paid plan the same credits apply, but nothing is deleted when they run
out.

$100–$200 of credits covers roughly the first **five to nine months**. During that window the
real spend is zero, and — critically — the *measured* cost from Cost Explorer replaces every
estimate in this table. The decision about which lever to pull is therefore made from real
numbers, not from this forecast.

> **The credit expiry date is the single most important date in this project's operations.**
> On that day the monthly bill goes from 0 to about $18.3 with no warning from AWS.
> It is recorded in `STATUS.md` as a dated field the moment the account is created (B10),
> and OPS-001 §3 defines what happens 60 days before it.

### Levers, in the order they should be pulled

1. **Scheduled shutdown outside usage hours** — **ADOPTED, not held in reserve. See ADR-024.**
   The instance is stopped **02:00–08:00 KST** (6 hours), cutting EC2 by 25% and bringing the
   total to **≈ $18.3 ≈ 25,600 KRW**. Availability is explicitly not a requirement (PRD-000 §5),
   which is what makes this spendable.
   Three consequences, all part of the decision: the collector runs at **08:05**, shortly after
   start-up; an **Elastic IP is required**, because a stopped instance loses its auto-assigned
   address; and the window is **re-checked against measured M-3 data** at the first monthly
   review (OPS-001 §7). A wider window (10 hours → ≈21,700 KRW) was available and was not taken
   — six hours already clears the ceiling, and the extra four hours of availability are worth
   more than headroom that is not needed.
   **This lever is now spent. Levers 2–4 are what remains in reserve.**
2. **Reserved Instance (1yr)** — `t4g.small` drops roughly 40%. Requires a 12-month
   commitment, so only after the design has stabilised and the credits are close to gone.
3. **Drop to `t4g.micro` (1 GiB)** — halves compute but the memory ledger above shows the
   workload alone needs 835 MiB of requests. **Not viable.** Recorded so it is not
   re-proposed.
4. **Spot instance** — cheapest, but interruption handling is extra work; good learning,
   deferred.

### Cost lines that are easy to forget

Checked monthly (OPS-001 §7): orphaned EBS volumes and snapshots, unattached Elastic IPs,
S3 versions retained by lifecycle rules, and CloudWatch log ingestion if anything ever ships
logs there.

---

## Storage layout (ADR-014)

| Volume | Size | Mount | Contents | Survives instance termination |
|---|---|---|---|---|
| Root EBS gp3 | 12 GiB | `/` | Ubuntu, k3s, containerd image cache | **No** (delete-on-termination) |
| Data EBS gp3 | 10 GiB | `/mnt/data` | PostgreSQL PVC via local-path | **Yes** (delete-on-termination = false) |
| S3 bucket | — | — | daily dumps + file blobs (separate prefixes, separate lifecycle rules) | **Yes** |

**User files are not on the node's disks.** The 10 GiB data volume holds PostgreSQL only.
Putting 5 GB of course materials there would eat half the volume PostgreSQL needs and bloat
every `pg_dump`, breaking the 4-hour RTO. See ADR-020.

k3s's local-path provisioner is configured with `/mnt/data/local-path-provisioner` as its
storage root, so the PostgreSQL PVC lands on the durable volume without needing the EBS CSI
driver. Node replacement is: terminate instance → create new instance → attach the data
volume → mount at `/mnt/data` → install k3s → Flux reconciles everything else.

This is exercised as a GameDay drill in B15 (`docs/GAMEDAY-001-failure-drills.md`).
