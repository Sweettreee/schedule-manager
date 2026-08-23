# BLOCKS-001 — Block Roadmap

**Status**: Approved
**Last updated**: 2026-08-22 (ADR-017 scope expansion; then ADR-021 source channels)
**Related**: REQ-001, SOURCES-001, ADR-017 … ADR-021

## 1. Principles

1. Every block leaves a visible result. No block produces only documents.
2. Every block fits in one to three working sessions.
3. A block can be started knowing only the block before it **in its own track**.
4. Every block ends by updating `STATUS.md`.
5. Every block that touches infrastructure carries a **GameDay drill**
   (`docs/GAMEDAY-001-failure-drills.md`) and produces an incident write-up.
6. **Something is usable from B5 onward.** No block leaves the system in a state where the
   owner cannot open it and get value.

**Weighting note**: the target role is Cloud/DevOps/SRE, so infrastructure blocks are
deliberately given more room than application-feature blocks. The application only needs to
be good enough to be used daily.

## 2. Three tracks

The blocks are gated by different things, so they are not one chain:

- **App track (B1–B8, B23, B24)** — gated by **wall-clock time**. B4 writes sender classification
  rules and B20 writes body parsers; neither has a specification until real mail has accumulated.
  B23 and B24 are additional source adapters that slot in wherever their dependency allows.
- **Infra track (B9–B17)** — gated only by the previous infra block. Needs no mail.
- **File track (B14, B18, B19, B25)** — gated by the infra track reaching AWS and a deployed API.

```
B0 (continuous: mail accumulates from day 1; source investigation → SOURCES-001)
 │
 ├── APP ──── B1 ─ B2 ─ B3 ─[30+ msgs]─ B4 ─ B5 ─ B6 ─ B7 ─ B8
 │                    │                            │    │
 │                    └── B23 (APIs, any time) ────┘    └── B24 (LMS calendar)
 │                                            │
 ├── INFRA ───────────────────────────────────┴─ B9 ─ B10 ─ B11 ─ B12 ─ B13 ─┬─ B15 ─ B16 ─ B17
 │                                                                            │
 └── FILE ───────────────────────────────────────────────────────────────── B14 ──── B18 ─ B19
                                                                                       │
                                                                    B25 (conditional) ─┘
     QUALITY ──────────────────────────────────────────────────────────────────────── B20 ─ B21 ─ B22
```

Rules: never two blocks at once **inside** a track; B9 requires B5 (there must be something to
containerise); B14 requires B13 (S3 plus a deployed API); B18 requires B14; B23 requires B3;
B24 requires B7; **B25 requires B18 and a passed gate** (`SOURCES-001` §4).

**When the app track is waiting for mail, work the infra track.** Since the target role is
SRE, this is not a compromise — it is the preferred allocation.

## 3. Numbering policy

**Block numbers are assigned in creation order. Execution order is defined by the tables in
this document, not by the numbers.**

This is the same rule ADRs already follow (`WORKFLOW.md`): ADR-017 amends ADR-001 but is
numbered after it. Applying it to blocks means a new block can be inserted anywhere in the
sequence without renumbering anything — which is what makes the promise below keepable.

The cost is that a bare number no longer tells you the order. The roadmap tables do.

Blocks were renumbered **once**, on 2026-08-22, while zero code existed and no block was
complete. Under the policy above there is no reason to ever do it again. The mapping below
exists so older notes remain readable.

| Old | New | Note |
|---|---|---|
| B0 | B0 | unchanged |
| B1 | B1 | unchanged |
| B2 | B2 | unchanged |
| B15 | **B3** | RSS promoted from "extensibility proof" to a core source (ADR-017) |
| B3 | B4 | |
| B4 | B5 | |
| — | **B6** | new: paste/screenshot ingest (ADR-018) |
| — | **B7** | new: time view and reminders (ADR-019) |
| — | **B8** | new: basic unified search |
| B5 | B9 | |
| B6 | B10 | |
| B7 | B11 | |
| B8 | B12 | |
| B9 | B13 | |
| — | **B14** | new: file locker L0 (ADR-020) |
| B10 | B15 | |
| B11 | B16 | |
| B12 | B17 | |
| — | **B18** | new: sync agent L1 (ADR-020) |
| — | **B19** | new: version history and restore |
| B13 | B20 | |
| B14 | B21 | |
| — | **B22** | new: Korean search quality |
| — | **B23** | new: public recruitment APIs — Worknet, Saramin (ADR-021) |
| — | **B24** | new: LMS calendar ICS + forum RSS (ADR-021) |
| — | **B25** | new: agent-side authenticated fetch — **conditional** (ADR-021) |

## 4. Phase 0 — Foundation

| Block | Work | Visible result |
|---|---|---|
| B0 | Dedicated Gmail account, subscribe to sources, **investigate every source's channel per `SOURCES-001` §3**, initialise the repository | Mail starts accumulating; `SOURCES-001` matrix filled in; repository exists |

B0 is **started**, not finished. Its output — accumulated mail — is the input to B4 and B20.

> The school-channel investigation returned to B0 (it was moved out on 2026-08-22 and back in
> the same day). Under ADR-001's old scope, school notices were a B15 extensibility test and
> the investigation blocked the first block for no reason. Under ADR-017 they are a **core
> source consumed in B3**, so identifying the channel belongs at the start. What B0 must
> produce is an answer, including "there is no feed, use the paste channel" — not a working
> integration.

## 5. Phase 1 — the application (local, 0 KRW)

| Block | Track | Work | Visible result |
|---|---|---|---|
| B1 | App | Gmail OAuth (published app, 2-day timebox per ADR-007) | Message subjects print in the terminal |
| B2 | App | Message → Item, PostgreSQL in Docker, incremental collection, deduplication, `collection_runs`. **Full schema including ADR-019 and ADR-020 tables** | Normalised rows accumulate |
| B3 | App | **RSS collector** — school notices. Second source adapter over the same pipeline | School notices land in the same table as mail |
| B4 | App | Classification and filter rules, **TDD**. *Entry: ≥ 30 messages from ≥ 3 senders* | Items land in the correct tab |
| B5 | App | FastAPI + Next.js: list, four tabs, deadline highlighting, last-success indicator and staleness banner, usage events, coverage-audit entry | **A screen used every day** |
| B6 | App | **Paste / screenshot ingest** with LLM extraction and mandatory confirmation (ADR-018) | 카톡 메시지·학사일정을 붙여넣으면 일정으로 등록된다 |
| B7 | App | **Time view and reminders** (ADR-019): week/month view over `starts_at`/`due_at`, reminder rows, delivery via the ADR-012 webhook path | 마감이 다가오면 알림이 온다 |
| B8 | App | **Basic unified search** — `pg_trgm` substring matching across title, org, body, tags | 한 검색창에서 전부 찾힌다 |
| **B23** | App | **Public recruitment APIs** — Worknet (공공데이터포털) and Saramin Open API (ADR-021). Runs any time after B3 | 채용 정보가 기다리지 않고 질의로 들어온다 |
| **B24** | App | **LMS calendar ICS + forum RSS** (ADR-021). Runs after B7 | 과제·시험 마감이 자동으로 일정 뷰에 |

By **B5** the "한 곳에서 다 본다" need is met. By **B7** the highest-priority capability —
schedules with reminders — is delivered. Several weeks of real usage here produce the data
later decisions depend on.

**Optional rehearsal**: AWS Educate / Academy labs can be used during this phase to practise
VPC, EC2 and security-group creation before doing it for real in B11. Lab resources are wiped
when the session ends, which makes them ideal for making mistakes in.

## 6. Phase 2 — AWS (the main learning phase)

| Block | Work | Visible result | GameDay |
|---|---|---|---|
| B9 | Dockerise both services (arm64); run the **full production composition** on local k3d — cert-manager, Flux, VictoriaMetrics, MinIO — and **measure memory against the ARCH-001 gate** | Same stack on Kubernetes locally, still 0 KRW | — |
| B10 | AWS account (**Paid plan**), MFA, IAM user, region, budget alarms $1/$5/$20, **credit expiry recorded in STATUS** | Spending safety net | — |
| B11 | Networking and compute by hand in the console: VPC, subnets, route table, IGW, security groups, key pair, EC2, **separate data EBS volume** | A server reachable over SSH | — |
| B12 | k3s (`--disable traefik,servicelb,metrics-server`), ingress-nginx, cert-manager TLS, Basic Auth | HTTPS URL that asks for a password | GD-1 |
| B13 | Deploy api, web, PostgreSQL StatefulSet on the data volume, CronJob collector, **dead man's switch ping**, daily `pg_dump` to S3, timed restore drill | **The real thing, running in the cloud** | GD-2, GD-3 |

## 7. Phase 3 — Files, IaC and delivery

| Block | Track | Work | Visible result | GameDay |
|---|---|---|---|---|
| B14 | File | **File locker L0** (ADR-020): S3 bucket, prefix-scoped IAM, presigned PUT/GET, `blobs`/`files`/`file_versions`/`devices`, `items` integration | 브라우저에서 올리고 받는다. 파일이 검색된다 | — |
| B15 | Infra | Reproduce B11–B14 infrastructure in Terraform via **`import`** (ADR-016) | `terraform plan` is empty against the live account | GD-4 |
| B16 | Infra | GitHub Actions CI/CD → **ghcr.io**, split the infrastructure repository, Flux, migrate secrets to SOPS | Push to `main` deploys itself | GD-5 |
| B17 | Infra | Observability: **VictoriaMetrics + node-exporter**, freshness SLO dashboard, alerting to Discord | Failures are noticed before data is missed | GD-6, GD-7 |
| B18 | File | **Sync agent L1** (ADR-020): watch a laptop folder, hash, skip-if-known, presigned direct upload, crash-safe local state, multipart for large files | 노트북 폴더에 넣으면 자동으로 올라간다 | — |
| B19 | File | **Version history and restore**; blob reference counting and garbage-collection policy | 지난주 버전으로 되돌린다 | GD-8 |
| **B25** | File | **Agent-side authenticated fetch — conditional.** Only if the five-condition gate in `SOURCES-001` §4 passes | 수업자료가 손 없이 동기화 폴더에 | — |

**B14 sits between the deployment block and the IaC block deliberately.** It is the first
concrete payoff for having built the cloud infrastructure, and putting it before B15 means
Terraform has an S3 bucket and an IAM policy to import as well — more surface for the block
that teaches import.

## 8. Phase 4 — Quality (only meaningful once data exists)

| Block | Work | Entry condition |
|---|---|---|
| B20 | Parse posting bodies into seven fields: title, organisation, deadline, link, requirements, field, description | ≥ 100 collected messages |
| B21 | Measure `type='NEWSLETTER' AND category='UNCLASSIFIED'` volume and misclassification logs, then decide whether AI classification is justified — **write the ADR either way** | B20 done, ≥ 4 weeks of data |
| B22 | Korean search quality: evaluate `pg_trgm` vs `pg_bigm` vs an external index against real queries (ADR-003 open question) | B8 in daily use, ≥ 3 months of data |

## 9. Beyond v1 — named milestones, not vague intentions

| Milestone | Trigger |
|---|---|
| **File sync L2** (pull to a second device) | The owner wants a file on the iPad that is not there |
| **File sync L3** (two-way, conflict resolution) | The first real divergence appears in `file_versions` — v1's "keep both, resolve nothing" policy exists to produce this evidence |
| **LMS-authenticated download** of course materials | L1 in daily use, and the LMS turns out to permit it |
| **Class timetable recurrence** (`rrule`) | A semester's schedule proves annoying to maintain as individual rows |
| **Semantic search** (embeddings) | B22 shows lexical search is the bottleneck, not the index |

Each gets its own ADR when its trigger fires. None is scheduled now, because the project is
explicitly continuous rather than finished.

## 10. Cost outlook

| Phase | Expected monthly cost |
|---|---|
| 0–1 | ≈0 KRW — no cloud resources; the only spend is LLM extraction from B6, capped at ~$0.3/month (FR-17) |
| 2 onward | ~30,900 KRW list price (ARCH-001 cost model), **0 while credits last**, brought to ~21,700 KRW by ARCH-001 lever 1 |

The number that matters is not the forecast but the **credit expiry date**, recorded in
`STATUS.md` at B10. See OPS-001 §3.
