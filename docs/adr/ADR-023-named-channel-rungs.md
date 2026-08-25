# ADR-023 — Channel Rungs Are Named, Not Numbered; `FEED` and `SCRAPE/MAIL` Merged

**Status**: Accepted
**Date**: 2026-08-24 (extracted into its own record 2026-08-25)
**Related**: ADR-002, ADR-018, ADR-021, **ADR-022 (revises)**, SOURCES-001, REQ-001 §4

> **Provenance.** This decision was originally written as `ADR-022` §0, a same-day in-place
> revision of `ADR-022`. That made `ADR-022` a file containing two contradictory ladders and a
> decision that reversed itself, which `WORKFLOW.md` forbids. It is extracted here so that a
> reference to `ADR-022` means one thing and a reference to `ADR-023` means the other.
> **Nothing in the decision changed during the extraction.**

## Context

`ADR-022` permitted scraping behind a nine-condition gate and placed it at rung 4, **above**
email subscription, on a "query beats waiting" argument. Two problems surfaced the same day.

### 1. The numbers had been reassigned three times in three days

`ADR-021` numbered the ladder 1–6. `ADR-022` renumbered it 1–7. This revision would have
renumbered it again. **Each reassignment silently invalidated cross-references in a dozen
files** — a document saying "rung 4" meant *email* on Friday, *scraping* on Sunday, and would
have meant something else again on Monday.

This is the same failure `BLOCKS-001` §3 solved for block numbers by assigning them in creation
order and defining execution order in a table instead.

### 2. The scraping-above-email ordering was wrong about ordering

`ADR-022`'s argument — a source you query beats a mailbox you wait for — **is right about
latency and control and wrong about ordering.** Ranking scraping above email implies email
should be dropped wherever scraping works. In practice which channel fits is a property of the
source, and using both is often correct:

| Source | Channel actually wanted |
|---|---|
| **Wevity** | **both** — the scraper for control, the email for redundancy |
| **JobKorea** | email only — scraping excluded on decided case law |
| **Linkareer** | email only — scraping excluded by owner decision |

Under a ranked ladder, Wevity using both needed an explanation every time it was written down.

`ADR-022` §6 ("Gmail is kept") was already arguing that **coverage redundancy beats ordering**.
The ladder simply did not say what §6 said.

### 3. Nothing ever turned on the tokenised/public feed distinction

`ADR-021` ranked personal tokenised feeds (rung 2) above public feeds (rung 3). Both are a URL
returning structured data with no credential worth protecting beyond the URL itself, and **no
source has ever needed the tie broken.** Recorded finding: **no public RSS/Atom source has been
found anywhere in this project.** The only confirmed feed source is the LMS calendar ICS.

## Decision

### 1. Rungs are identified by **name**, never by number

| Order | Name | Channel |
|---|---|---|
| 1 | **`API`** | Official API |
| 2 | **`FEED`** | A feed — personal tokenised (ICS, tokenised RSS) **or** public (RSS/Atom) |
| 3 | **`SCRAPE/MAIL`** | **Permitted scraping and email subscription — peers, not ranked** |
| 4 | **`PASTE`** | Paste / screenshot → LLM extraction with mandatory confirmation (ADR-018) |
| — | **`AGENT`** | Agent-side authenticated fetch — conditional |
| ✗ | — | Scraping behind a login, or any redistribution — prohibited permanently |

Write `SCRAPE/MAIL`, not "rung 3". The **Order** column exists only because the ladder is tried
top-down; it is not an identifier and must never be used as one.

### 2. `FEED` absorbs the former tokenised-feed and public-feed rungs

One rung. The distinction was never load-bearing.

### 3. Scraping and email are **peers** on `SCRAPE/MAIL`

Either or both may be used for a source. Using both needs no justification.

### 4. `PASTE` is the floor, and it is not manual

Pasted content goes through LLM extraction with mandatory confirmation (`ADR-018`), so the last
resort still produces structured items rather than typing. Two whole categories of the owner's
schedule — club/KakaoTalk events and the academic calendar — live there **permanently, by
design**. `PASTE` is a designed terminal state, not a failure.

### 5. The operative table lives in `SOURCES-001`, not here

`SOURCES-001` §1 is the authority. This ADR records **why** the ladder has this shape; the
ladder itself is live policy that has moved three times, and live policy in an immutable record
forces either stale ADRs or edited ADRs. This ADR is the last edit either way.

## Rationale

- **Names do not move.** A cross-reference written today survives the next restructuring.
- **The ladder now says what `ADR-022` §6 already said**: redundant channels over one source are
  a feature, because the owner's ranked worst failure is missing information.
- **It removes a standing exception.** Wevity's dual channel was correct and needed an
  explanatory note under every previous version of the ladder.
- **It records an absence honestly.** "No public feed exists anywhere in this project" is a
  finding, and merging the feed rungs is what that finding licenses.

## Trade-offs

| Gained | Given up |
|---|---|
| Cross-references survive future restructuring | A bare name no longer tells you the try-order; the table does |
| Wevity's dual channel needs no justification | The "query beats waiting" latency argument is no longer visible in the ladder's shape |
| One fewer rung to reason about | The tokenised/public distinction is lost if it ever turns out to matter |
| The ladder matches `ADR-022` §6's own reasoning | A fourth ladder revision in four days |

## Alternatives rejected

- **Renumber once more and stop.** What was attempted twice already. Every renumbering was also
  intended to be the last one.
- **Keep scraping ranked above email, override per source.** Coherent, and it preserves
  `ADR-002`'s ordering. Rejected as dishonest bookkeeping: if the correct choice for three of
  four sources is the lower rung, the ladder is recording the wrong order and every source needs
  an exception note.
- **Keep the tokenised/public feed split against future need.** Costs nothing to keep, but it is
  a distinction with no observed instance, and the project's rule is to decide from evidence.
- **Drop the ladder and decide per source.** The ladder's whole value is `SOURCES-001` §1's rule
  that a lower rung requires the higher ones to be **checked and recorded** as unavailable.
  Without ordering, "I didn't look" becomes indistinguishable from "nothing exists".

## What this ADR does **not** change

`ADR-022`'s nine-condition scrape gate, the empty-result-is-failure rule, the
no-headless-browser-on-the-node rule, JobKorea's exclusion on decided case law, and the decision
to keep Gmail are all untouched.

## Open questions

None. The per-source questions this restructuring touched are recorded in `SOURCES-001` §2 and
in `ADR-022`'s open questions.
