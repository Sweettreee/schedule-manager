# Schedule Manager

A personal information hub. It collects what matters from scattered sources, shows it on a
time axis with reminders, makes all of it searchable, and keeps files in sync across devices.

This repository exists for two reasons, and **both are required conditions**:

1. **Solve a real problem** — stop being the transport layer between five websites, an inbox,
   a group chat and a laptop folder.
2. **Learn cloud engineering** — AWS, containers, Kubernetes, IaC, CI/CD, observability,
   object storage. Target role: **Cloud / DevOps / SRE**.

## Three capabilities, one table

Per `PRD-000` §2, the three capabilities are one product seen from three directions, all built
over a single `items` table (`ADR-003`):

| Capability | Role | v1 level (ADR-017) |
|---|---|---|
| **Schedules and materials** | time output | Week/month view + deadline reminders |
| **Unified search** | content output | Trigram substring search across everything |
| **Job postings and newsletters** | ingest | **Official APIs** + Gmail + scraped public pages + paste/screenshot |
| **File synchronisation** | ingest **and** the project's richest cloud curriculum | L0 web locker + L1 one-way laptop agent |

Deferred with named triggers, not vaguely: file sync L2/L3, Korean morphological search,
embedding search, recurring events, LMS-authenticated download. See `BLOCKS-001` §9.

## Read these first

| If you want to know | Read |
|---|---|
| What problem this solves and why | `docs/PRD-000-problem-definition.md` |
| What v1 must do | `docs/REQ-001-requirements.md` |
| Where the project currently stands | `STATUS.md` |
| What to build next | `docs/BLOCKS-001-roadmap.md`, `docs/blocks/` |
| Where a given piece of information comes from | `docs/SOURCES-001-channel-policy.md` |
| Why a technology was chosen | `docs/adr/` |
| How we work (branches, tests, DoD) | `WORKFLOW.md` |
| The rules Claude Code must follow | `CLAUDE.md` |

## Repository layout

```
/
  api/                  FastAPI service + collector          (from B1)
  web/                  Next.js UI                           (from B5)
  agent/                file sync client                     (from B18)
  infra/                k8s manifests, Terraform             (from B9; own repo from B16)
  docs/
    PRD-000-problem-definition.md
    REQ-001-requirements.md
    DATA-001-item-schema.md
    ARCH-001-target-architecture.md
    SEC-001-security-baseline.md
    OPS-001-cost-guardrails.md
    SOURCES-001-channel-policy.md      the source register — and the authority on channels
    GAMEDAY-001-failure-drills.md
    BLOCKS-001-roadmap.md
    PROMPTS-001-plan-review.md         reusable review prompt + scoring rubric
    adr/                ADR-000 template, ADR-001 … ADR-026 (025 unused)
    blocks/             B0-B8, B10-B11, B23-B25, B26
    incidents/          incident write-ups (see README there)
  CLAUDE.md
  WORKFLOW.md
  README.md
  STATUS.md
  .gitignore
```

## Current state

**B0 complete. B1 in progress.**

`api/` holds the collector's first slice — OAuth credential handling, a header-only Gmail reader,
a CLI and six unit tests — and `make lint`, `make test` pass. **The OAuth flow has never been
run**, so B1's acceptance criterion (two runs on different days without re-authenticating) is not
yet met, and the Google-side setup is still ahead.

**Next action: B1.** See `STATUS.md`, which is the resume point and the only place the current
state is maintained.

The planning set was reviewed twice (2026-08-22, 2026-08-23), rescoped by `ADR-017`, had its
channel policy rewritten by `ADR-022`/`ADR-023`, consolidated on 2026-08-25 so that each rule has
exactly one authoritative home, and reconciled with the code on 2026-08-30. `STATUS.md` §8
carries the full revision log.

## Stack (decided, see ADRs)

- **API**: Python 3.13.11 / FastAPI / SQLAlchemy + Alembic (forward-only migrations, ADR-015).
  Operated with **uv** through `api/Makefile` — `make sync`, `make test`, `make lint`, `make run`.
  Never bare `uv run`; see `api/README.md` and ADR-026
- **UI**: Next.js
- **DB**: PostgreSQL — Docker locally; in-cluster StatefulSet on a PVC backed by a dedicated
  EBS data volume on AWS (ADR-014)
- **Files**: content-addressed blobs in S3, presigned direct transfer (ADR-020).
  MinIO locally.
- **Extraction**: an external LLM for paste/screenshot input only, capped and
  confirmation-gated (ADR-018)
- **Sources**: a named ladder tried top-down — **`API`** → **`FEED`** → **`SCRAPE/MAIL`** →
  **`PASTE`**, plus a conditional **`AGENT`** rung. Scraping behind a login and any
  redistribution are prohibited permanently.
  **The ladder, the nine-condition scraping gate and the per-source register live in
  [`docs/SOURCES-001-channel-policy.md`](docs/SOURCES-001-channel-policy.md) — the one
  authoritative copy.** Why it has this shape: ADR-021, ADR-022, ADR-023
- **Runtime**: Docker → local k3d → k3s on a single EC2 `t4g.small` (ADR-005)
- **Registry**: GitHub Container Registry, ghcr.io (ADR-011)
- **Observability**: VictoriaMetrics single-node + node-exporter; Grafana on demand (ADR-013)
- **Liveness**: external dead man's switch + in-app staleness banner (ADR-012)
- **IaC**: console first, then Terraform via `import` (ADR-016)
- **Delivery**: GitHub Actions → Flux (GitOps, separate infra repo from B16)
- **Schedule**: the instance is stopped **02:00–08:00 KST** by design; the collector runs at
  08:05 (ADR-024)
- **Budget ceiling**: 30,000 KRW / month at an assumed 1 USD = 1,400 KRW (ARCH-001).
  **The design costs ≈ 25,600 KRW**, and fits only because of the shutdown above

## Local secrets

The Gmail refresh token is written to `api/.secrets/gmail_token.json`, which is in
`.gitignore` and never committed. See `docs/blocks/B0-B8-specs.md` §B1 and ADR-009.
