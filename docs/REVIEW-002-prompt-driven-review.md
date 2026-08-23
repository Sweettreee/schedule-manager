# REVIEW-002 — Prompt-Driven Document Review (2026-08-23)

**Status**: Complete — all findings applied
**Date**: 2026-08-23
**Method**: the review prompt in `docs/PROMPTS-001-plan-review.md`, run against the full
document set. REVIEW-001's findings were treated as closed and not re-raised.
**Scope**: documentation only. No decision is reversed; per WORKFLOW.md, every edit below is
a factual/cross-reference correction or an addition, so ADRs were edited in place where
touched.

## Summary

Ten findings: five stale block references left over from the one-time renumbering
(2026-08-22), two cost-figure drifts, two documents never updated after ADR-021, and one
undocumented alerting gap. No contradiction was found in any *decision* — the defects are
all in cross-references and derived figures, which is what a same-day triple revision
(REVIEW-001 → ADR-017 → ADR-021) predictably leaves behind.

## Findings and fixes

### F-1 (Major) — ARCH-001 said credit expiry is recorded "at B6"

> "It is recorded in `STATUS.md` as a dated field the moment the account is created (B6)"

B6 is the *paste ingest* block. Account creation is **B10** (old B6, renumbered by ADR-017).
ARCH-001 calls this "the single most important date in this project's operations" — the one
sentence saying when to record it pointed at the wrong block.
**Fix**: B6 → B10. Also aligned "about $21.6" to the cost table's own total, $22.1.

### F-2 (Major) — B10-B11-specs said Terraform reproduces B11 "in B10"

> "built by hand so that every layer is understood before Terraform reproduces it in B10"
> "in B10, anything still tagged `console-b11` is something Terraform has not yet imported"

Terraform is **B15** (ADR-016). Three occurrences, all leftovers from the old numbering in a
file that was itself renamed by the renumbering. A future session following this spec would
have looked for Terraform work in the account-setup block.
**Fix**: three occurrences B10 → B15.

### F-3 (Major) — B10-B11-specs: "VictoriaMetrics covers it from B12"

Observability deploys at **B17** (ADR-013, OPS-001 §4). B12 is k3s/ingress/TLS. Old B12 →
new B17.
**Fix**: B12 → B17.

### F-4 (Minor) — ADR-013 trade-off table: "B12 becomes buildable"

The same stale mapping inside ADR-013, whose own context section correctly says B17
throughout. In-place edit is permitted: cross-reference correction, not a reversal.
**Fix**: B12 → B17.

### F-5 (Minor) — DATA-001: "Never counted in B14"

B14 is the *file locker*. The classification-evidence block is **B21** (old B14) — the same
section's trigger query already says B21.
**Fix**: B14 → B21.

### F-6 (Major) — BLOCKS-001 §10 cost figures disagree with ARCH-001

> BLOCKS-001: "~30,400 KRW list price … brought to ~22,000 KRW by ARCH-001 lever 1"
> ARCH-001: "**≈ 22.1** … **≈ 30,900 KRW at 1,400**" and lever 1 → "**$15.5 ≈ 21,700 KRW**"

Two documents, three different derived figures. ARCH-001 is the cost model of record.
**Fix**: BLOCKS-001 aligned to 30,900 / 21,700, with a pointer to ARCH-001.

### F-7 (Minor) — BLOCKS-001 §10: Phase 0–1 was "0 KRW" and "$0.3/month" in one cell

Self-contradictory as written.
**Fix**: reworded to "≈0 KRW — the only spend is LLM extraction from B6, capped ~$0.3/month".

### F-8 (Major) — CLAUDE.md §1 never learned about ADR-021

> "Gmail, school-notice RSS and pasted content are collected"

CLAUDE.md is the contract every session reads first, and it omitted two of the five v1
channels (official APIs, LMS iCalendar) that STATUS, REQ-001 and README all list.
**Fix**: source list updated; revision line dated.

### F-9 (Minor) — PRD-000 coverage-audit rotation predates ADR-021

The rotation (Wevity → JobKorea → Linkareer → university notices) never gained the API
sources, even though B23's acceptance criteria and SOURCES-001 §5 both add sources to the
rotation, and ADR-021 explicitly claims the audit becomes "partly automatic".
**Fix**: rotation note added — Worknet and Saramin join from B23, comparable in code.

### F-10 (Major) — the B13→B17 alerting gap existed but was undocumented

REQ-001 §3.1 says all three freshness mechanisms are required. OPS-001 §4 says B is a
VictoriaMetrics alert rule and VictoriaMetrics arrives at B17 — so between B13 (first cloud
deploy) and B17, mechanism B does not exist, and no document said so. Checked against the
numbers, the gap is benign at the default interval: C fires at 30h, before B's 36h
(24h × 1.5). It is only real if the interval is shortened before B17.
**Fix**: OPS-001 §4 now states the interim gap, why it is acceptable at 24h, and what to do
if the interval is shortened before B17.

### Also fixed while there (cosmetic drift)

B11's resource tags still said `Project=job-aggregator`; the repository was reframed as
Schedule Manager by ADR-017 and B15's Terraform would have codified the stale name.
Changed to `Project=schedule-manager` (two tables). Zero cost now — the block has not run.

## Not changed, deliberately

- **REVIEW-001** keeps its pre-renumbering block numbers; STATUS.md's document index already
  flags this. Rewriting an external review would falsify the record.
- No decision, scope line, or ADR status was altered. Nothing here met the bar for a new ADR.

## Follow-ups

- None blocking B0. The renumbering-leftover class is now empty as far as this review found;
  if another stale number surfaces, fix it in place and note it in `STATUS.md`.
