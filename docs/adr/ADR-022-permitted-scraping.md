# ADR-022 — Permitted Scraping as a Sanctioned Rung

**Status**: Accepted — **restructured by ADR-023 (2026-08-25)**
**Date**: 2026-08-24
**Related**: ADR-002 (amended), ADR-021 (rung ✗ superseded), **ADR-023 (restructures §1)**,
ADR-004, ADR-012, ARCH-001, REQ-001 §4, SOURCES-001, PRD-000 §6

> **Restructure note (ADR-023).** This ADR's §1 ladder — numbered rungs, with scraping ranked
> above email — was replaced the same day it was written. **`ADR-023` carries that decision**:
> rungs are named rather than numbered, `FEED` absorbs both former feed rungs, and scraping and
> email became **peers** on `SCRAPE/MAIL`. That revision originally lived here as a §0, which made
> this file a record containing two contradictory ladders and a decision that reversed itself —
> against `WORKFLOW.md`'s rule that an ADR is never edited to reverse a decision. It was extracted
> on 2026-08-25.
>
> **Everything else in this ADR stands unchanged**: the nine-condition gate (§2), the
> empty-result rule (§3), the no-browser-on-the-node rule (§4), JobKorea's exclusion (§5) and
> keeping Gmail (§6).
>
> **The operative ladder and gate live in `SOURCES-001` §1 and §4.** This ADR records why.

---

## Context

`ADR-002` (2026-08-20) made Gmail the primary channel and put scraping at the bottom as a
"last resort", and `ADR-021` (2026-08-22) hardened that into a permanent prohibition:
*"Scraping a commercial site — permanently prohibited."*

Two things have since changed.

### 1. The prohibition rested on an unexamined premise

`ADR-002` reasoned: *"JobKorea prohibits scraping explicitly and relevant case law exists.
Saramin and Linkareer are likely to prohibit it as well."* The word doing the work is
**likely**. One source was investigated; the other two were assumed to match it. This is the
same error `ADR-021` corrected for Saramin's API — an assumption recorded as a finding — and
it produced the same kind of cost: sources excluded on a belief rather than on a check.

A `robots.txt` review on 2026-08-24 found:

| Source | `robots.txt` finding |
|---|---|
| **Wevity** | `User-agent: *` → `Allow: /`. A `Crawl-delay: 3` is declared for `GPTBot` |
| **Linkareer** | `Allow: /` with `Disallow:` limited to `/stem/learn/` (login-scoped: 수강내역, 프로필, 결제, internal APIs). The four target list paths — `/list/contest`, `/list/activity`, `/list/intern`, `/list/recruit` — are all permitted. A sitemap index is published |
| **JobKorea** | AI/LLM bots (`GPTBot`, `ClaudeBot`, `anthropic-ai`) and known scrapers (`CCBot`, `DeepSeek`, `Amazonbot`) are blocked. Under `User-agent: *`, login and personal paths (`/login/`, `/my/`, `/corp/`) are disallowed but `/recruit/joblist` and `/Recruit/GI_Read` are **explicitly allowed** |
| **School notice board** | **No `robots.txt` exists**, and the board publishes **no RSS or Atom feed** |

So the assumption was wrong for two of three commercial sites, and the source the owner ranks
as core — the school notice board — has no feed at all, which `ADR-021`'s ladder answers with
`PASTE` for a board that updates weekly.

### 2. `robots.txt` is not the constraint `ADR-002` relied on

`ADR-002` cited **terms of service and case law**, not `robots.txt`. `robots.txt` carries no
legal force in Korea; it is a crawler-directive convention. Finding `Allow: /` therefore does
not discharge `ADR-002`'s argument — it only removes one of two obstacles.

The obstacle that remains is the **이용약관 automated-collection clause**, and for job boards
specifically, **데이터베이스제작자의 권리** (저작권법) and **부정경쟁방지법**. 잡코리아 v 사람인
is real, decided, and about exactly this content type — job postings scraped from a Korean job
board — with damages awarded. It concerned a competitor republishing at commercial scale,
which is a materially different profile from a single student collecting for personal reading
and redistributing nothing. But it establishes that JobKorea litigates this, and
`Allow: /recruit/joblist` does not touch database producer's rights.

### 3. The owner's priority reorders the trade-off

Recorded 2026-08-24: **missing information is the most critical failure in the job-hunting
capability, above all others.** `PRD-000` already names silent under-collection as the worst
outcome; the owner now states that for jobs it outranks the maintenance cost of an adapter.

Email subscription is the channel with the worst coverage guarantee in the whole set. It
delivers what the sender decides to send, when they decide to send it, in a format they can
change without notice, filtered by their own relevance model. `ADR-021` made precisely this
argument to rank APIs above email ("Query, don't wait"). The argument does not stop applying
because the transport is HTML instead of JSON.

## Decision

**Scraping is permitted, for a source that passes the gate in §2, and it ranks above email
subscription.** `ADR-021`'s ✗ row is superseded. `ADR-002`'s legal reasoning is *not* discarded
— it is converted from a blanket prohibition into a per-source, evidence-recorded test.

### 1. The ladder gains a scraping rung

Permitted scraping enters the ladder as a sanctioned channel rather than a prohibited one, and
the ✗ row is narrowed to the two things that are actually indefensible: **reaching content the
provider put behind authentication**, and **republishing what was collected**.

The ladder as first written here ranked scraping at rung 4, above email at rung 5. **That
ordering was replaced the same day by `ADR-023`**, which made the two peers on `SCRAPE/MAIL` and
replaced numbers with names.

> **The operative ladder is `SOURCES-001` §1.** It is not restated here, and it is not restated
> in `REQ-001`, `README`, `CLAUDE.md` or `STATUS` either — all of them link. The ladder moved
> three times in three days; one copy is the only version of this that survives contact with a
> fourth revision.

Tried top-down, as before. **A lower rung may be used only after every higher rung has been
checked and recorded in `SOURCES-001` as unavailable. "I didn't look" is not "unavailable".**

### 2. The scrape gate — all nine conditions must hold

A source may be scraped only if **all nine** conditions hold, each recorded in `SOURCES-001` §2
with the date checked. A source failing any condition uses the email half of `SCRAPE/MAIL`
instead, or falls to `PASTE`. Conditions are re-checked when a site redesigns or changes terms.

> **The nine conditions are listed in `SOURCES-001` §4.** They are not restated here — this ADR
> decides that a gate exists and what it is for; the register states what it contains, because
> that is the list an implementer works from.

Two of them carry the weight and are worth naming in the decision itself:

- **Condition 2 — the terms of service** contain no prohibition on automated collection, quoted
  or its absence recorded, with the date and URL. **This is the condition that decides a source,
  not condition 1.** `robots.txt` carries no legal force in Korea; `Allow: /` is permission from
  a crawler-directive file, not from the site's lawyers.
- **Condition 7 — an empty result is `FAILED`**, never `SUCCESS`. See §3. This is the condition
  that makes scraping admissible at all.

### 3. Empty result is failure

This is the operational core of the ADR and applies to every scraping adapter without exception.

HTML changes silently. A selector that stops matching returns `[]`, the run records `SUCCESS`,
the freshness clock resets, and the dashboard looks healthy while collection is dead. That is
the exact failure class `PRD-000` §6 and `ADR-012` name as this project's worst outcome, and
it is the strongest argument `ADR-021` made against scraping. Adopting scraping means
answering it, not inheriting it.

Therefore, for every scraped source:

- A run returning **zero items** from a source that has ever returned more than zero is
  recorded as **`FAILED` for that source**, and the run as `PARTIAL`.
- The **cursor does not advance** on a zero-item result.
- Two consecutive zero-item runs for one source raise the alert defined in `ADR-012`.
- A parse that yields a row **missing `title` or `url`** is a failure of that row, counted, and
  the count is asserted in tests. Silent field-dropping is the same disease as an empty list.

### 4. No headless browser on the server — this is arithmetic

`ARCH-001`'s memory ledger leaves **415 MiB of headroom** on the `t4g.small`. Headless
Chromium costs **300–500 MiB**. It does not fit. `ADR-021` §3 already rejected server-side
browser automation on this ground and two others; nothing here changes that.

Consequence: a scraped source must be reachable with `requests` + a parser (~50 MiB). If a page
requires JavaScript to render its list, the options are, **in this order**:

1. **Call the JSON endpoint the page itself calls.** A JS-rendered list is fetching its data
   from somewhere; that endpoint is usually a plain unauthenticated GET. **Linkareer is a
   Next.js application and must be checked for this first** — it is both cheaper and more
   stable than parsing rendered HTML.
2. **Run it in the laptop sync agent** (B18's process), which has a browser and a screen, and
   where a breakage is a script the owner is sitting in front of rather than a cluster
   incident. Same placement argument as `ADR-021` §3.
3. **Paste** (ADR-018).

A browser on the node is not on the list.

### 5. Per-source outcome

| Source | Rung | Reason |
|---|---|---|
| **School notice board** | **`SCRAPE/MAIL`** (scraping) | No `robots.txt` (RFC 9309 pass) and no feed. Non-commercial `.ac.kr`, no database interest, no case law, and the owner is the intended audience. **The safest target in the set** — so it is where the gate machinery is built (B3) |
| **Wevity** | **`SCRAPE/MAIL`** (both halves) | `Allow: /`, `Crawl-delay: 3` honoured as the global floor. ToS check outstanding in B0 |
| **Linkareer** | **`SCRAPE/MAIL`** (scraping — *later withdrawn by owner decision, see Resolutions*) | Target paths permitted; the `Disallow:` set is login-scoped, which is condition 3 agreeing with us. JSON-endpoint check required before any HTML parsing. ToS check outstanding in B0 |
| **JobKorea** | **`SCRAPE/MAIL` — email half only** | `robots.txt` permits `/recruit/joblist`, but this is the one source with **decided case law against scraping its postings**. The blanket AI/scraper-bot blocklist also shows a site that actively polices automated access. Coverage here comes from job-alert email, plus 고용24 and Saramin on `API` |
| 고용24, Saramin | `API` | Unchanged (ADR-021) |
| Saramin web | ✗ | Unchanged — scraping a site whose official API you already hold is indefensible |

**JobKorea is a decision, not an oversight.** It is recorded here so a future session does not
re-open it on `robots.txt` evidence alone.

### 6. Gmail is kept

Gmail stays as an active channel, not a demoted fallback — `ADR-007`, B1 and B2 are untouched.
Two reasons:

1. **Coverage redundancy is the point.** The owner's stated priority is that missing
   information is the worst failure in this capability. A scraper that breaks silently is a
   real risk even with §3's countermeasure; the mailbox keeps arriving while it is broken.
   Two independent channels over one source is a feature here, and `content_hash` (DATA-001)
   already makes the overlap measurable rather than annoying.
2. It is the only channel needing no per-source adapter, it carries newsletters that have no
   other channel, and it is where the OAuth and token-lifecycle learning lives (`ADR-007`).

## Rationale

- **It converts an assumption into a test.** `ADR-002`'s conclusion may still be right for a
  given source — JobKorea's is. The gate makes that a recorded finding per source instead of a
  blanket rule covering sources nobody checked.
- **It matches the owner's stated priority.** Missing information is the ranked failure.
  Email has the weakest coverage guarantee of any channel in the set; a queried source is
  strictly better on the dimension the owner cares most about.
- **It unblocks the core source.** School notices are a core source under `ADR-017` and had no
  channel above `PASTE`. Paste for a weekly notice board would have been a permanent manual tax
  on the highest-priority capability.
- **It keeps the legal reasoning that mattered.** Login-gated content and redistribution stay
  permanently prohibited, and condition 2 makes the ToS — not `robots.txt` — the deciding
  evidence. That is what `ADR-002` was actually about.
- **It buys a second `Source` implementation shape.** `ADR-003`'s one-table claim is tested
  harder by an HTML adapter than by a second feed adapter.
- **Cost is zero.** No new AWS resource, nothing billed per hour. Egress and CPU for one daily
  run of a few dozen conditional GETs are inside the `ARCH-001` ledger's noise.

## Trade-offs

| Gained | Given up |
|---|---|
| School notices get a real channel instead of manual paste | An HTML adapter to maintain per source, breaking on redesigns |
| Query control: pagination, date windows, categories — instead of waiting for a sender | The legal certainty of a blanket prohibition, replaced by a per-source record |
| Coverage no longer bounded by what each site chooses to email | Nine gate conditions to check and re-check whenever a site changes its terms |
| Redundant channels on overlapping sources — a silent scraper break is survivable | Duplicate rows across channels, and the `content_hash` overlap question arrives sooner than planned |
| The silent-failure rule (§3) becomes explicit policy for **all** sources, not just scrapers | Every scraping adapter needs a "has this source ever returned rows?" state check |
| JobKorea's risk is now a written, reasoned exclusion rather than an assumption applied to three sites | JobKorea coverage stays at email latency |

## Alternatives rejected

- **Leave `ADR-021`'s prohibition in place.** Cheapest and safest. Rejected: it excluded two
  commercial sources on an unverified assumption, and left the owner's highest-priority source
  — the school board, which has no feed and no `robots.txt` — on the paste channel.
- **Scrape JobKorea too, since `robots.txt` allows the path.** Rejected. It is the one source
  where the ToS-and-case-law argument has already been tested in court on this content type,
  and `API` plus the email half of `SCRAPE/MAIL` cover the same space. `robots.txt` is condition 1 of nine.
- **Drop Gmail and go scrape-plus-API only.** Rejected on the owner's own priority: two
  independent channels are the defence against silent under-collection, which is the ranked
  worst failure. It would also delete `ADR-007`'s learning block for no gain.
- **Rank scraping *below* email, and override per source.** Coherent, and it keeps `ADR-002`'s
  ordering intact. Rejected as dishonest bookkeeping: if the correct choice for three of four
  sources is the lower rung, the ladder is recording the wrong order and every source needs an
  exception note. Better to change the order and say why.
- **Headless browser on the node for JS-rendered pages.** Rejected on `ARCH-001` arithmetic —
  300–500 MiB into 415 MiB of total headroom, competing with PostgreSQL and the API.
- **Rotate User-Agents / route through proxies to survive bot blocks.** Rejected on principle,
  and it is why condition 4 exists. A site blocking an honest identifier has answered the
  question; the answer is the email half of `SCRAPE/MAIL`, not a disguise. This also keeps the project's `NFR-7` claim
  truthful rather than nominal.
- **Scrape the academic calendar page now that scraping is allowed.** Still rejected, on
  `ADR-021`'s original reasoning: an adapter subject to layout drift to capture two updates a
  year. Paste (B6) remains correct. The gate makes scraping *permitted*, not *preferred*.

## Consequences

- **`SOURCES-001`** §1 ladder replaced; §2 matrix re-rung; §3 checklist gains the ToS-quote and
  `robots.txt`-snapshot requirements; **§4 becomes the authoritative statement of the scrape
  gate**; §7 register gains a UA and crawl-delay column per source; §8 gains the JobKorea row.
- **`REQ-001`** §4 source table updated. `NFR-7` strengthened: `robots.txt` **and** terms,
  recorded per source. `NFR-8` rewritten to the new ladder. **`NFR-17` added**: an empty
  collection result from a source that has previously returned rows is a failure.
- **`ADR-002`** marked amended. **`ADR-021`** rung ✗ marked superseded in part; §3 (agent-side
  authenticated fetch) and the API-first rung are untouched and still govern.
- **B0** is re-run: the checklist is now `robots.txt` snapshot + ToS clause per source, not
  subscription setup. Subscriptions still happen — Gmail is kept — but they are no longer the
  acceptance criterion.
- **B3** changes from "RSS collector" to **"scraper adapter, built against the school notice
  board"**, and carries the gate machinery: honest UA, rate limiter, conditional requests,
  cursor, and the §3 empty-result rule. The RSS adapter moves to **B24**, where a real feed
  exists (LMS forum RSS).
- **B26** is added: a commercial scraping adapter reusing B3's machinery. Depends on B3 and on
  B0's ToS findings. *(Scoped to Wevity alone on 2026-08-24 — see Resolutions.)*
- **B23** unchanged. Its "Not in this block: scraping anything" line is narrowed to Saramin's
  website specifically.

## Resolutions — B0 findings, 2026-08-24

Recorded here because these answer questions this ADR left open on the same day it was written.
The **decision** above is unchanged; only which sources land where. Rung names per §0.

| Question | Answer |
|---|---|
| **School board HTML parseable without a browser?** | ✅ **Yes.** `curl` returns the rows; jQuery 1.12.4, no SPA. `robots.txt` **404** (RFC 9309 → unrestricted) and **no terms of service exist at all** — established by a full navigation walk, not by not looking. All nine conditions recorded in `SOURCES-001` §2.2. **`SCRAPE/MAIL` confirmed; B3 unblocked** |
| **Linkareer JSON endpoint?** | Moot. The pages proved **server-rendered** — data embedded in the HTML — so condition 9 passed without needing an endpoint. **But the owner excluded Linkareer from scraping on 2026-08-24 with the ToS unread.** It sits on the email half of `SCRAPE/MAIL`. §1 permits placing a source below the rung the ladder allows; it does not permit the reverse |
| **Wevity ToS** | ✅ **Cleared by the owner's determination, 2026-08-24** — no prohibition on automated collection. All nine conditions pass; **B26 unblocked**, as a single-source block. *The clause text was not transcribed into `SOURCES-001` §2, so the evidence record is thinner than condition 2 asks for* |

**A finding this ADR did not anticipate — see `SOURCES-001` §2.1 and `NFR-19`.** The LMS
calendar export takes a `preset_time` parameter. The wrong value (`monthnow`) returns HTTP 200,
a well-formed non-empty `.ics` that parses cleanly, **while silently omitting next month's
deadlines**. §3's rule — empty result is failure — **does not catch this**, because the result
is not empty; it is truncated. `NFR-19` was added to cover scope parameters generally, across
the LMS window, the school board's search parameters, and B23's API date ranges. §3 remains
correct and remains necessary; it is simply not sufficient on its own.

## Open questions

- **Transcribing Wevity's terms clause.** The owner determined on 2026-08-24 that Wevity's terms
  carry no prohibition on automated collection, and B26 proceeds on that. The **wording and URL
  were not written into `SOURCES-001` §2**, so the record is thinner than condition 2 specifies.
  Paste them in when convenient — the point of condition 2 is that a future session can re-check
  the finding without re-deriving it.
- **Redundancy measurement.** Once Gmail and a scraper cover the same source, `content_hash`
  overlap becomes measurable. Revisit ADR-003's deferred cross-source deduplication question
  after one month of B26, with counts.
- **Re-checking terms.** A site can change its terms without telling anyone. Add a ToS re-read
  to the monthly operations review (OPS-001 §7)? Decide at the first monthly review, with the
  real cost of the check known rather than guessed.
