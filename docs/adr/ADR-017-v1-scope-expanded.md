# ADR-017 — v1 Scope, Re-decided: All Three Capabilities, at Their First Useful Level

**Status**: Accepted — **amends ADR-001**
**Date**: 2026-08-22
**Related**: ADR-001 (amended), ADR-003, ADR-018, ADR-019, ADR-020, PRD-000, REQ-001, BLOCKS-001

## Context

`ADR-001` limited v1 to job and announcement collection. It gave three reasons. Two of them
still hold. **One of them was factually wrong, and only the owner could know that:**

> *"It is the capability with the highest daily value to the user, which drives habit
> formation."*

The owner has stated the opposite. In priority order, the three capabilities are:

1. **Schedule and materials in one place** — academic calendar, school notices, club and
   department announcements, with reminders so nothing is forgotten
2. **Unified search**
3. Job postings and newsletters

So the sequencing decision was correct for reasons that were partly wrong, which means it has
to be re-derived rather than assumed.

A second problem surfaced at the same time. The repository was named
**"Job & Newsletter Aggregator"**, and the document set had drifted into describing that as
the product rather than as the first slice of it. Naming is not cosmetic: a document set that
calls itself a job aggregator will, six months from now, quietly justify a decision that
forecloses the other two capabilities, and nobody will notice.

Third, investigating the highest-priority capability revealed that it is **not one thing.**
Its sub-sources differ by more than an order of magnitude in difficulty:

| Sub-source | Channel | Difficulty | Notes |
|---|---|---|---|
| School notices | RSS or email | **Low** | Same pipeline as job collection. Different URL, same code |
| Academic calendar | a static page, updated once per semester | **Low** | Not a feed. Closer to "paste once a semester" than to polling |
| Deadline reminders | reuse the webhook path from ADR-012 | **Low** | The alerting infrastructure already exists by design |
| Class timetable | manual entry, once per semester | **Low**, but needs recurrence in the schema |
| KakaoTalk club/department schedules | **no read API exists** | **High** | See ADR-018 |
| Course material files | object storage, client agent | **High** | See below — the assessment of this one changed |

**The majority of the highest-priority capability is cheap and shares the existing pipeline.**
Deferring all of it to "after B15" was throwing away the best value-per-effort in the project
on the strength of a scope line that was drawn before this was understood.

### File synchronisation is not what ADR-001 assumed it was

`ADR-001` deferred file synchronisation as "the largest and least understood piece", and used
that to justify the whole scope line. The owner has since stated that it is **one of the most
important capabilities**, for two reasons that both bear on this decision:

- it solves a real problem — course materials scattered across an LMS, a laptop and a tablet;
- it is **the richest cloud-engineering curriculum in the project** — object storage, IAM,
  delegated authorisation, content addressing, client state, and eventually distributed
  conflict resolution.

The second reason is decisive, because goal 2 of this project is a *required* condition, not a
bonus. A capability that teaches more cloud engineering than any other block is not a
candidate for indefinite deferral.

And the original assessment was too coarse in the same way the schedule capability was.
Synchronisation is a ladder (`ADR-020`):

| Level | Capability | Difficulty |
|---|---|---|
| **L0** | Web locker — upload and download in a browser | Moderate |
| **L1** | One-way agent — a watched laptop folder uploads automatically | Moderate |
| L2 | Pull sync — another device downloads what it lacks | High |
| L3 | Two-way with conflict resolution | **Very high** |

What ADR-001 called "the largest unknown" is **L3**. L0 and L1 are ordinary engineering with
a well-understood shape, and they already deliver "course materials in one place".

## Decision

**v1 covers all three capabilities, each at its first genuinely useful level.**

Concretely, v1 now includes:

1. Gmail collection (unchanged from ADR-001)
2. **RSS collection of school notices** — promoted from the old block B15 into Phase 1
3. **Unstructured input by paste or screenshot** — covers the academic calendar, KakaoTalk
   content, and anything else with no machine channel (**ADR-018**)
4. **A time view and deadline reminders** over `starts_at` / `due_at` (**ADR-019**)
5. **Basic unified search** — substring and trigram matching. Korean morphological analysis
   remains deferred (DATA-001, ADR-003)
6. **File synchronisation at L0 + L1** — a web locker plus a one-way laptop agent, on
   content-addressed S3 storage (**ADR-020**)

Still **out** of v1:

- **File sync L2 and L3** — pull sync to a second device, and two-way editing with conflict
  resolution. These are named milestones with their own future ADRs, not vague intentions.
- Semantic / embedding search.
- Class timetable recurrence — deferred with the schema left ready (ADR-019).
- LMS-authenticated automatic download of course materials. The agent watches a local folder;
  getting files *into* that folder is manual in v1.

The repository is reframed as **Schedule Manager**, a personal information hub with three
capabilities, and the "Job & Newsletter Aggregator" title is retired.

### What "v1" now means, and why the word still applies

v1 is no longer a small scope. It is roughly twenty blocks. That is a deliberate consequence
of the project charter — *"this project is not limited to a short-term MVP… it will be
continuously improved based on real usage"* — and of goal 2 being required rather than
optional. The blocks stay small; there are simply more of them, they are ordered so that
something usable exists from block B5 onward, and nothing in the sequence has to be finished
before the next thing becomes useful.

## Rationale

### Why ingest still comes first, on corrected grounds

The original "highest daily value" argument is dead. Two better ones remain, and one is new:

1. **Every read view needs a filled table.** The time view and search are queries over
   `items` (ADR-003). Building either before something fills the table produces a beautiful
   empty screen. This is structural, not a matter of priority.
2. **The high-priority capability's easy half *is* ingest.** School notices arrive through the
   same collector as job postings, differing only in the source adapter. Prioritising the
   schedule capability therefore does not mean abandoning ingest — it means **adding one more
   source adapter and then building the view.** The two are not in competition.
3. **The risky half of the schedule capability had no known channel at all.** KakaoTalk has no
   read API. Sequencing the schedule capability first, before that was investigated, would
   have put an unsolved channel problem on the critical path — exactly the mistake ADR-002
   avoided with scraping.

### Why expand rather than swap

Making the schedule capability v1 *instead of* collection was considered and rejected: it
gives the most-wanted thing first, but every screen in it reads from a table that nothing is
filling, so the work would have started with ingest anyway — just with a less honest roadmap.

### Why file sync belongs in v1 despite being the hardest thing here

Three reasons, in order of weight:

1. **Goal 2 is a required condition.** File synchronisation teaches more transferable cloud
   engineering per block than anything else in the roadmap — object storage, prefix-scoped
   IAM, presigned URLs, content addressing, client-side state that survives crashes. Deferring
   the best available curriculum indefinitely would be optimising the project against its own
   stated purpose.
2. **L0 and L1 are not the hard part.** ADR-001's "largest unknown" verdict was about conflict
   resolution, which stays out of v1. A locker and a one-way agent are ordinary work.
3. **It lands after the AWS blocks, so it costs nothing early.** L0 needs S3, which needs an
   AWS account, so it naturally falls in Phase 3 (block B14 onward) — after the infrastructure
   the project was going to build anyway. It is a payoff for that work, not a competitor to it.

### Why the naming change matters

`PRD-000` §2 already frames the three capabilities correctly as ingest / time output /
content output. The concept was never wrong; only the label was. Aligning the label with the
concept costs one commit now and prevents a class of silent scope decisions later.

## Trade-offs

| Gained | Given up |
|---|---|
| The capability the owner actually wants arrives inside v1, not after fifteen blocks | Phase 1 grows from six blocks to nine; the first AWS block moves later in the app track |
| School notices and the academic calendar are covered by code that mostly already existed | More surface to keep working before any of it is deployed |
| The paste channel solves KakaoTalk **and** the academic calendar **and** any future source with no API, with one feature | An LLM dependency and a small recurring cost enter v1 (ADR-018) |
| The name stops biasing future decisions | A block renumbering, and a document set revised twice in two days |
| Reminders reuse the ADR-012 alerting path at near-zero marginal cost | The schema grows before it has ever held a row (ADR-019, ADR-020) |
| File sync gives the infrastructure work a concrete payoff and the best learning in the project | v1 is now ~20 blocks; "v1" describes a direction, not a short sprint |

**On the renumbering**: with zero lines of code written and no block completed, renumbering is
free today and expensive at any later point. Doing it now is the cheap option, not the
disruptive one.

## Alternatives rejected

- **Keep ADR-001's scope, fix only the naming and the dead premise.** Smallest change, and the
  roadmap stays stable. Rejected because it leaves the owner's top-priority capability behind
  fifteen blocks for no reason that survives inspection — the cheap half of it needs one
  source adapter and one view.
- **Make the schedule capability v1 and defer collection.** Delivers the most-wanted thing
  first. Rejected: the read views query a table that collection fills, so the work reorders
  itself back into ingest-first in practice, and the roadmap would misdescribe what is
  happening.
- **Expand to all three capabilities *fully*, including two-way file sync and semantic
  search.** Rejected for ADR-001's original third reason, which survives: conflict resolution
  is the largest and least understood piece, and pulling it in now reintroduces the schedule
  risk that deferring it removed. Designing a merge policy before a single real conflict has
  been observed is speculative — the same objection ADR-003 raised against cross-source
  deduplication and ADR-021 raises against premature AI classification.
- **Add the school-notice source but keep the time view out of v1.** Cheapest expansion, but
  it delivers school notices into a list that sorts by arrival date — which is not what
  "학사일정을 한눈에" means. The view is the point.
- **Keep file sync out of v1 and revisit after B22.** The status quo. Rejected: it defers the
  project's best cloud curriculum on a difficulty assessment that turned out to apply only to
  L3, and it leaves goal 2 dependent on the infrastructure blocks alone.

## Consequences

- `ADR-001` is marked **Amended by ADR-017**. Its scope decision is superseded; its reasoning
  about file synchronisation is retained and reaffirmed above.
- `README.md`, `PRD-000` §4, `REQ-001` §1 and `BLOCKS-001` are revised.
- Blocks are renumbered once; see `BLOCKS-001` §3 for the old → new mapping.
- Three follow-on decisions were required by this one and are recorded separately:
  **ADR-018** (unstructured input channel), **ADR-019** (scheduling model) and
  **ADR-020** (file synchronisation architecture).

## Open questions

- **File sync L2 and L3.** L2 (pull to a second device) is triggered when the owner reports
  wanting a file on the iPad that is not there. L3 (two-way) is triggered by the first real
  divergence recorded in `file_versions` — which v1's "keep both, resolve nothing" policy is
  designed to produce as evidence.
- **LMS-authenticated download** of course materials, so files arrive in the watched folder
  without manual saving. Depends on what the university's LMS actually permits; investigate
  when L1 is in daily use.
- Whether the class timetable justifies recurrence support, or whether pasting a semester's
  schedule once (ADR-018) is sufficient. Decide when the first semester's data exists.
