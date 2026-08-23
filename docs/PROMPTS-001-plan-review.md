# PROMPTS-001 — Reusable Plan-Review Prompt

**Status**: Approved
**Created**: 2026-08-23
**Related**: WORKFLOW.md, REVIEW-001, REVIEW-002

## Purpose

A reusable prompt for having an AI examine and improve this project's planning documents.
Built from Anthropic's prompting best practices
(<https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>).
Run it whenever the document set has been revised substantially — after a scope change, a
batch of new ADRs, or a renumbering — and record the output as the next `REVIEW-NNN`.

## Design of the prompt (why it is shaped this way)

| Technique | Where it appears |
|---|---|
| Role prompting | "senior architect reviewing a learning project" — focuses on trade-offs, not style |
| Long-context ordering | documents first, instructions last |
| XML structure | `<documents>` / `<context>` / `<instructions>` so content and instructions cannot mix |
| Motivation, not just task | the goals and constraints section — changes what "good feedback" means |
| Explicit criteria | four named defect classes instead of "review my plan" |
| Quote-before-conclude | every finding must quote the passage it is about — prevents hallucinated critiques |
| Positive output framing | says what the output is, not what to avoid |
| Self-check | verify each finding against the documents before reporting it |

## The prompt

```text
You are a senior software architect reviewing the planning documents of a
personal learning project before implementation begins.

<documents>
Read, in this order: STATUS.md, CLAUDE.md, WORKFLOW.md, README.md,
docs/PRD-000, docs/REQ-001, docs/ARCH-001, docs/DATA-001, docs/BLOCKS-001,
docs/OPS-001, docs/SEC-001, docs/SOURCES-001, docs/GAMEDAY-001,
docs/adr/ADR-001 … ADR-021, docs/blocks/*.
Treat docs/REVIEW-001 as historical input (it predates the block
renumbering); do not re-raise findings it already closed.
</documents>

<context>
- Goal 1: solve a real personal problem. Goal 2 (required, not optional):
  learn cloud engineering for a Cloud/DevOps/SRE career.
- Constraints: AWS, one t4g.small (2 GiB), ceiling 30,000 KRW/month at the
  FX assumption in ARCH-001; blocks are small and verifiable; the owner
  implements everything and approves every change first.
- Blocks and ADRs are numbered in creation order, not execution order;
  execution order lives in BLOCKS-001's tables.
</context>

<instructions>
Examine the documents for exactly these four defect classes:

1. Cross-document contradictions — two documents stating different facts
   (numbers, block references, source lists, decisions). Quote both sides.
2. Scope or sequencing risks — a block that cannot run when the roadmap
   says it can, an entry condition that cannot be met, a dependency the
   tables miss.
3. Constraint violations — anything that breaks the memory ledger, the
   cost ceiling, or a stated security/privacy rule.
4. Missing pieces — a gap a production plan would cover that no document
   addresses and no "decide later" trigger names.

For each finding: quote the exact passage(s), name the file(s), explain
why it is a defect given the goals above, and propose the smallest
concrete fix. Rank findings by impact. Before reporting, re-verify each
finding against the documents and drop any not directly supported by a
quote. If a section survives scrutiny, do not pad the review with
invented issues — a short list of real defects is the desired output.

Output: a ranked findings table (severity, files, quote, why, fix),
then the proposed edits per file.
</instructions>
```

## Applying the output

1. Findings are triaged by the owner; accepted ones become edits or new ADRs.
2. The run is recorded as `docs/REVIEW-NNN-*.md` with findings and what was changed.
3. `STATUS.md` gets a revision-log entry.
4. Per WORKFLOW.md: correcting a factual error or a stale cross-reference in an ADR is an
   in-place edit; reversing a decision requires a new ADR.
