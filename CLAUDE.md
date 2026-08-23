# CLAUDE.md — operating rules for Claude Code in this repository

Read this file completely before doing anything. It is the contract for this project.
**Last revised**: 2026-08-23 (source list aligned with ADR-021; previously revised after
REVIEW-001, then ADR-017).

## 1. What this project is

**Schedule Manager** — a personal information hub. Gmail, school-notice RSS, official APIs
(Worknet, Saramin — ADR-021), an LMS iCalendar feed and pasted content are collected into a
single `items` table, shown on a time axis with reminders, made searchable, and accompanied
by file synchronisation to S3.

The owner's goals, in priority order:

1. Solve a real personal problem (information is scattered across five sources and must be
   copied by hand).
2. Learn cloud engineering for a **Cloud / DevOps / SRE** career. This is a required
   condition, not a nice-to-have.
3. Applied AI, introduced only when operational data justifies it.

Three capabilities, all over the same `items` table, in the owner's priority order:
**time view** (schedules, materials, reminders), **search**, then **ingest** (job postings and
newsletters). File synchronisation spans ingest and is the project's richest cloud curriculum.
**v1 delivers all three at their first useful level, plus file sync L0+L1** — see ADR-017.

## 2. Hard rules — do not violate these

1. **Explain before writing.** Before creating or modifying any file, state: what you will
   do, why this approach, what the alternatives are, and the trade-offs, costs and risks.
   Wait for explicit approval. Then write, then show the diff.
2. **Never commit without approval.** Never push to `main` directly.
3. **Never commit secrets or personal data.** No OAuth tokens, no client secrets, no real
   email content. Test fixtures must be anonymised (see `WORKFLOW.md` and SEC-001).
4. **Never mark work complete without tests.** See the testing policy below.
5. **Respect ADR-004 (control over convenience).** If you are about to propose a managed
   AWS service that hides a layer the owner wants to learn, say so explicitly and justify
   it against the three allowed exceptions in ADR-004.
6. **One block at a time.** Do not implement work belonging to a later block, even if it
   seems trivial to add now.
7. **Update `STATUS.md` at the end of every block.** The project is designed to be paused
   and resumed; `STATUS.md` is the resume point.
8. **Never weaken a safety property to make a block pass.** Specifically: the freshness
   alerting in ADR-012, the `UNIQUE (source, source_id)` constraint, and the anonymisation
   rule in SEC-001. If one of these blocks progress, stop and raise it.

## 3. Testing policy (ADR-010)

- **TDD is mandatory** for classification rules and filter rules. The specification already
  exists in `REQ-001`, so write the failing test first.
- **Test-after** for parsing, API endpoints, and integration paths.
- **Integration tests** run against a real PostgreSQL via testcontainers. Three paths are
  mandatory: (a) mail fixture → Item → DB → re-collection is ignored as duplicate;
  (b) list API returns correct results for tab, sort, and date filters;
  (c) incremental collection: the second run fetches strictly fewer messages than the first.
- **No browser E2E tests.**
- **Bug rule**: when a misclassification or parse error is found, first add the offending
  message as an anonymised fixture and write a failing test, then fix the rule.
- Never call the real Gmail API in tests. Use recorded, anonymised response fixtures.

## 4. Style and conventions

- Documents and code in English. UI labels in Korean (see the enum table in `DATA-001`).
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`,
  `ci:`).
- Timestamps: store `timestamptz` in UTC, convert to KST only at the presentation layer.
- Python: type hints required, `ruff` + `black`. TypeScript: `eslint` + `prettier`.
- **Database changes are forward-only migrations** (ADR-015). Never write a `downgrade()`
  that drops or rewrites data; never run manual DDL against any environment.
- Every non-obvious technical decision gets an ADR in `docs/adr/`, numbered sequentially in
  the order decisions are made. Do not reserve numbers for future decisions.
- **File bytes never pass through the API** (NFR-12, ADR-020). Any proposal that streams,
  buffers or proxies a user file through FastAPI is wrong by construction on a 2 GiB node.
- **Pasted content never reaches a log, metric, trace or incident write-up** (SEC-15). It may
  contain other people's messages.

## 5. Cost rules

- Monthly ceiling is **30,000 KRW**, evaluated at the FX assumption recorded in `ARCH-001`
  (currently 1 USD = 1,400 KRW → an effective ceiling of about **USD 21.4/month**).
  Any proposal that could exceed it must be flagged before implementation, with the
  estimated monthly figure in **both** USD and KRW.
- Never create: NAT Gateway, ALB/NLB, RDS, EKS, ECR, Elastic IPs left unattached, or any
  resource billed per hour that is not in `ARCH-001`.
  (ECR is excluded because container images live in **ghcr.io** — ADR-011.)
- **Metered spend needs a code-level cap, not just an alarm.** LLM extraction is capped at 300
  calls/month (FR-17) and file storage is alarmed at 10 GB (NFR-13), because the realistic
  failure is a retry loop and an alarm does not stop one.
- If a task seems to require one of those, stop and raise it as an ADR instead.
- When a block creates a resource that bills per hour, say so in the block summary:
  *"from now on this costs $X/hour."*

## 6. What "done" means

A block is done when: code merged to `main` via PR, tests pass in CI, the visible outcome
described in `BLOCKS-001` is demonstrable, any GameDay drill assigned to the block has been
run and written up in `docs/incidents/`, `STATUS.md` updated, and any new decision recorded
as an ADR.

## 7. Where to start right now

Read, in this order: `STATUS.md` → `docs/BLOCKS-001-roadmap.md` → the spec file for the
current block in `docs/blocks/`. The current block is named at the top of `STATUS.md`.
Do not read further ahead than the current block's spec.
