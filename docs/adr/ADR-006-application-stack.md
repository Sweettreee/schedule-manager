# ADR-006 — Application Stack: FastAPI + Next.js

**Status**: Accepted
**Date**: 2026-08-21
**Related**: ADR-005, ARCH-001

## Context
The owner can already write Python, TypeScript and SQL. The target role is Cloud/DevOps/SRE,
so the application language is not itself a career-critical choice. The node has 2 GiB of RAM
shared between k3s, PostgreSQL and every application pod.

## Decision
**FastAPI (Python) for the API and collector, Next.js for the UI, deployed as two
containers.** SQLAlchemy with Alembic for database access and migrations.

## Rationale
- **Memory.** Approximate idle footprints: FastAPI 80–150 MiB, Node/Next.js 100–200 MiB,
  Go 20–50 MiB, JVM/Spring Boot 250–450 MiB even after tuning. Spring Boot plus Next.js plus
  PostgreSQL plus k3s does not fit comfortably in 2 GiB and would force a larger instance,
  breaking the budget. The language choice is therefore also a cost decision.
- **AI roadmap.** Later blocks introduce LLM classification and embedding-based search;
  Python's ecosystem is decisively stronger there.
- **Korean text handling.** Parsing and morphological analysis libraries are more mature in
  Python.
- **Two containers rather than one** deliberately buys complexity: it forces real use of
  Services, ingress routing and inter-service communication, which is the Kubernetes practice
  the project is for.
- **Existing skill.** Learning a new language and cloud engineering simultaneously would make
  both shallow.

## Trade-offs
| Gained | Given up |
|---|---|
| Small memory footprint, fits the budget | No JVM ecosystem experience |
| Strong path to the AI milestones | Spring Boot's direct value in the Korean backend job market |
| Meaningful Kubernetes practice from two services | Longer builds and more moving parts than a single container |

## Alternatives rejected
- **Spring Boot + Next.js** — genuine career value for Korean backend roles, but requires a
  4 GiB instance, exceeding the budget, and its learning curve would consume the time
  budgeted for cloud work. Reconsider if the target role changes to backend developer.
- **Go + Next.js** — the best fit for cloud-native tooling and the lightest option; rejected
  only because the owner has no Go experience and the AI milestones would be harder.
- **NestJS + Next.js** — a single language across the stack; rejected for the AI roadmap.
- **Single container (FastAPI + Jinja2/HTMX)** — simplest and cheapest, but too little
  Kubernetes surface to learn from.
