# CLAUDE.md — operating rules for Claude Code in this repository

Read this file completely before doing anything. It is the contract for this project.
**Last revised**: 2026-08-30 (§6 reduced to a pointer — `WORKFLOW.md` now holds the only
Definition of Done. Earlier: §0 added, the five-gate session procedure, at the owner's
direction — it governs every other rule here. ADR-026: uv is the Python toolchain; §4
states the rule).

## 0. How a session runs with the owner — the five gates

**This section governs every other rule in this file.** §2 rule 1 ("explain before writing")
is its one-line form; this is the procedure, and where the two differ this section wins.

The owner is learning cloud engineering (§1, goal 2 — a required condition, not a
nice-to-have) and does not hold the background knowledge for most blocks in advance. **Code
the owner cannot read is a failed deliverable even when it is correct**, because it produces
a system the owner cannot operate, debug, or defend. Speed is not the constraint here;
comprehension is.

**Never skip a gate. Never combine two gates in one message. Never begin gate N+1 before the
owner has answered gate N.**

### Gate 1 — Prerequisite knowledge, as a list to go and study

Before describing any work, assume the owner knows **nothing** about the technologies it
touches.

- Produce a **list of what to learn**, not the teaching itself. A tutorial written inline is
  unreadable, goes stale, and duplicates primary sources the owner should be reading directly.
- Each item carries three things: **the term**, **one line on why this block needs it**, and
  **where to look** — an official docs page, or the exact concept name to search.
- Split into **"must know before we start"** and **"useful context"**, with a rough time cost
  for each group.
- Name what would otherwise be silently assumed: file formats, protocols, CLI tools, and the
  specific language features the coming code actually uses.

### Gate 2 — Comprehension check, run as an interview

When the owner reports having studied, **do not move to the plan. Check first.**

- Ask in small batches and wait for answers; do not dump every question at once.
- Ask **"why" and "what breaks if"** questions, not definitions. The goal is to find the gaps
  that would make the plan unreadable, not to award a score.
- If an answer is wrong or thin, say so plainly, give the correction, point back at the
  source, and re-ask. Passing the gate matters more than passing it quickly.
- **State explicitly when the gate is passed**, and name anything still shaky that the owner
  should keep an eye on while reading the code.

### Gate 3 — The build plan, reviewed and confirmed

Only now describe the work:

- The **visible outcome** — what will be observably true that is not true now.
- **Every file created or modified**, each with a one-line statement of its job.
- The approach, the **alternatives considered**, and the trade-offs, costs and risks (§2
  rule 1).
- What is deliberately **out of scope** for this block, and which block owns it instead
  (§2 rule 6).
- **What the owner must do by hand** — accounts, consoles, keys, subscriptions.

**Then stop and wait for explicit confirmation. A question from the owner is not a
confirmation.**

### Gate 4 — Build

Write code only after that confirmation, and only what the plan named. If something
unforeseen appears mid-build, stop and return to Gate 3 for that piece rather than deciding
alone.

### Gate 5 — Walkthrough, file by file — the session is not over without it

The owner intends to read every line, so hand over what makes that possible. Per file:

1. **Path and purpose** — one sentence on why this file exists at all.
2. **Structure** — each function or class: what goes in, what comes out, why it is there.
3. **The non-obvious lines** — anything not self-evident, above all anything that exists
   because of an ADR or a spec rule, **with the reference named**.
4. **How to run it and how to see its result.**
5. **What the owner does next**, as concrete numbered steps.

**A block is not done (§6) until Gate 5 has been delivered and the owner says it landed.**

## 1. What this project is

**Schedule Manager** — a personal information hub. Everything the owner needs from several
scattered sources is collected into a single `items` table, shown on a time axis with reminders,
made searchable, and accompanied by file synchronisation to S3.

**Where the data comes from is decided by the channel ladder in `docs/SOURCES-001-channel-policy.md`
§1, which is the only authoritative statement of it.** Do not restate the ladder, the scraping
gate (§4) or the authenticated-fetch gate (§5) in any other file — they moved three times in
three days and every restatement went stale within days. Link instead.

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
   **The full procedure is §0 — the five gates. Follow it; this rule is only its summary.**
2. **Never commit without approval.** Never push to `main` directly.
3. **Never commit secrets or personal data.** No OAuth tokens, no client secrets, no real
   email content. Test fixtures must be anonymised (see `WORKFLOW.md` and SEC-001).
4. **Never mark work complete without tests.** See the testing policy below.
5. **Respect ADR-004 (control over convenience).** If you are about to propose a managed
   AWS service that hides a layer the owner wants to learn, say so explicitly and justify
   it against the three allowed exceptions in ADR-004.
6. **One block at a time, within a lane.** The roadmap runs three parallel lanes — app, infra,
   file (`BLOCKS-001` §2) — and never two blocks at once *inside* one lane. Do not implement
   work belonging to a later block in **any** lane, even if it seems trivial to add now.
7. **Update `STATUS.md` at the end of every block.** The project is designed to be paused
   and resumed; `STATUS.md` is the resume point.
8. **Never weaken a safety property to make a block pass.** Specifically: the freshness
   alerting in ADR-012, the `UNIQUE (source, source_id)` constraint, and the anonymisation
   rule in SEC-001. If one of these blocks progress, stop and raise it.

## 3. Testing policy

**The policy is `ADR-010`; the working practice is `WORKFLOW.md` §"Testing".** Read them rather
than this section. The three points that most often get skipped:

- **TDD is mandatory** for classification and filter rules — their specification already exists
  in `REQ-001` §2.2/§2.3, so the failing test is writable before the code.
- **Never call a real external API in tests** — not Gmail, not the recruitment APIs, not a live
  site. Recorded, anonymised fixtures only.
- **Bug rule**: on finding a misclassification or parse error, add the offending input as an
  anonymised fixture with a failing test *first*, then fix the rule.

## 4. Style and conventions

- Documents and code in English. UI labels in Korean (see the enum table in `DATA-001`).
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`,
  `ci:`).
- Timestamps: store `timestamptz` in UTC, convert to KST only at the presentation layer.
- Python: type hints required, `ruff` + `black`. TypeScript: `eslint` + `prettier`.
- **Python is operated with `uv`, driven through `api/Makefile`** (ADR-026). `make sync`,
  `make test`, `make lint`, `make run`. Never propose `python3 -m venv` or `pip install`, and
  never run bare `uv run` — the environment must be `venv/`, not `.venv/`, or editable imports
  break silently under this iCloud folder. Add dependencies with `uv add`, and commit `uv.lock`.
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
- **The design currently costs ≈ USD 18.3 ≈ 25,600 KRW**, and it only fits because the instance
  is stopped 02:00–08:00 KST (**ADR-024**). Without that shutdown the same design lists at
  ≈ 30,900 KRW and breaches the ceiling. Treat the shutdown as load-bearing, not as an
  optimisation someone can quietly drop.
- Never create: NAT Gateway, ALB/NLB, RDS, EKS, ECR, or any resource billed per hour that is
  not in `ARCH-001`.
  (ECR is excluded because container images live in **ghcr.io** — ADR-011.)
- **Elastic IPs**: exactly **one**, permanently attached, required by ADR-024 because a stopped
  instance loses its auto-assigned address. Never create a second, and never leave one
  unattached — an unattached Elastic IP bills for nothing and is on the monthly orphan check
  (`OPS-001` §7).
- **Metered spend needs a code-level cap, not just an alarm.** LLM extraction is capped at 300
  calls/month (FR-17) and file storage is alarmed at 10 GB (NFR-13), because the realistic
  failure is a retry loop and an alarm does not stop one.
- If a task seems to require one of those, stop and raise it as an ADR instead.
- When a block creates a resource that bills per hour, say so in the block summary:
  *"from now on this costs $X/hour."*

## 6. What "done" means

**The Definition of Done lives in `WORKFLOW.md` §"Definition of Done", and that is the only
copy.** Read it there. This section deliberately restates none of it: two lists existed until
2026-08-30 and had already drifted apart by one criterion, and the one that was wrong was this
one.

Two things in it are easy to miss. **Gate 5 (§0) is a criterion** — a block whose code the owner
cannot read is not done. And the **CI requirement applies from B16 onward**; before that, `make
lint` and `make test` locally are what "tests pass" means, because `.github/` does not exist yet.

## 7. Where to start right now

Read, in this order: `STATUS.md` → `docs/BLOCKS-001-roadmap.md` → the spec file for the block
you have been pointed at, in `docs/blocks/`. The current block of each lane is named at the top
of `STATUS.md`.

**Do not read past the current block of the lane you are working.** Reading the current block of
a *different* lane is fine and often necessary — the lanes run in parallel, so "the current
block" is not a single thing.
