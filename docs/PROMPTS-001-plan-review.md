# PROMPTS-001 — Reusable Plan-Review Prompt

**Status**: Approved
**Created**: 2026-08-23
**Last updated**: 2026-08-25 (absorbed the scoring rubric from REVIEW-001, which was deleted)
**Related**: WORKFLOW.md, STATUS.md §8

## Purpose

A reusable prompt for having an AI examine and improve this project's planning documents.
Built from Anthropic's prompting best practices
(<https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>).
Run it whenever the document set has been revised substantially — after a scope change, a
batch of new ADRs, or a renumbering. Record the outcome as a dated row in `STATUS.md` §8, and
apply the accepted findings to the documents themselves.

> **Do not keep the review output as a permanent document.** Two were kept
> (`REVIEW-001`, `REVIEW-002`) and both became liabilities: their findings were applied, so they
> described defects that no longer existed, in documents that had been rewritten, using block
> numbers from before a renumbering. They were deleted on 2026-08-25. **A review is an event, not
> an artefact** — the artefact is the corrected document set plus one line in the revision log.

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
docs/adr/ADR-001 … ADR-026 (there is no ADR-025), docs/blocks/*, and api/.
STATUS.md section 8 is the revision log; treat findings already
recorded as applied there as closed, and do not re-raise them.
</documents>

<context>
- Goal 1: solve a real personal problem. Goal 2 (required, not optional):
  learn cloud engineering for a Cloud/DevOps/SRE career.
- Constraints: AWS, one t4g.small (2 GiB), ceiling 30,000 KRW/month at the
  FX assumption in ARCH-001; blocks are small and verifiable; the owner
  implements everything and approves every change first.
- Blocks and ADRs are numbered in creation order, not execution order;
  execution order lives in BLOCKS-001's tables.
- SOURCES-001 is the single authority for the channel ladder and both
  gates. A restatement of either anywhere else is a defect, not a
  convenience.
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

## Scoring rubric (from REVIEW-001)

`REVIEW-001` scored the document set out of 100 across eight weighted axes. The **weights were
set by each axis's contribution to the project's two required conditions** — a tool that is
actually used, and Cloud/DevOps/SRE learning — which is why architecture-under-constraint (C)
outweighs everything and learning-design (G) and maintainability (H) are small.

The rubric is reusable and is kept here; the 2026-08-21 findings it produced were all applied
and the review document itself was deleted on 2026-08-25 (`STATUS.md` §8).

**Quoted verbatim from `REVIEW-001` §1.2**, in the original Korean, so the wording that produced
the 2026-08-21 scores is not silently altered by a translation:

| # | 축 | 무엇을 보는가 | 가중 |
|---|---|---|---|
| A | 문제 정의 → 해법 정합성 | PRD의 문제가 요구사항·스키마·블록까지 인과로 이어지는가 | 15 |
| B | 요구사항의 검증가능성 | 각 FR/NFR이 "충족됨"을 판정할 수 있는 형태인가 | 15 |
| C | 아키텍처 ↔ 제약 정합성 | 메모리·비용·단일노드 제약 안에서 설계가 실제로 성립하는가 | 20 |
| D | 의사결정 품질 (ADR) | 대안 검토의 성실성, trade-off의 정직성, 재검토 트리거 | 15 |
| E | 로드맵 실행가능성 | 블록 크기·의존성·선행조건·되돌릴 수 없는 지점의 배치 | 15 |
| F | 운영/보안/비용 가드레일의 실효성 | 규칙이 실제로 사고를 막는가, 아니면 사후 통지만 하는가 | 10 |
| G | 학습목표 달성 설계 | SRE 포트폴리오로서 무엇이 남는가 | 5 |
| H | 문서 체계 유지보수성 | 일관성, 추적성, 갱신 규칙, 재개 가능성 | 5 |

**Severity bands**, also from `REVIEW-001`:

- **Critical** — proceeding as written fails one of the project's declared goals. Fix before B0.
- **Major** — a specific block will be blocked by it. Fix before that block.
- **Minor** — quality. Fix when convenient.

**The 2026-08-21 baseline was 73/100**, with C (architecture ↔ constraints) at 11/20 the lowest
score — the memory ledger did not add up. That is the number a later run can be compared against.
