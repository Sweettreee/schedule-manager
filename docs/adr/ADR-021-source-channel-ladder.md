# ADR-021 — Source Channel Ladder: Official APIs First, and Where Authenticated Fetching Runs

**Status**: Accepted — **extends ADR-002**
**Date**: 2026-08-22
**Related**: ADR-002 (extended), ADR-004, ADR-009, ADR-017, ADR-018, ADR-020, ARCH-001, SEC-001, SOURCES-001

## Context

`ADR-002` built a three-rung channel ladder — **Gmail first, RSS where clearly permitted,
scraping only as a last resort** — because scraping the large job boards carries legal
exposure that could end the project. That reasoning is intact and this ADR does not touch it.

But the ladder was missing a rung, and the omission cost real coverage. Investigation on
2026-08-22 found:

| Finding | Consequence |
|---|---|
| **Saramin operates an official Open API** (`oapi.saramin.co.kr`), access key, **500 calls/day** | `REQ-001` §4 listed Saramin as *"scraping likely prohibited → Excluded"*. Scraping being prohibited and no API existing are different facts, and the document conflated them |
| **Worknet / 고용24 publishes a recruitment API on 공공데이터포털** (한국고용정보원) | A government open-data source — the legally cleanest channel available anywhere in this project |
| **The university LMS appears to be Moodle-based** — `lms.chungbuk.ac.kr/mod/ubboard/…` follows Moodle's `/mod/<plugin>/` URL structure | Moodle offers **per-user iCalendar export** and forum RSS: tokenised, read-only URLs that need **no stored credentials** |

So the honest statement of the gap: **ADR-002 asked "can we scrape this?" when it should first
have asked "is there a sanctioned API?"** For three sources the answer was yes, and one of
them had been excluded from the project entirely.

A second question arrives with the same investigation. If any source ever does require an
authenticated session, **where does that code run?** The document set had no answer, and the
default assumption — on the server, like every other collector — turns out to be wrong on
three independent grounds.

## Decision

### 1. A six-rung ladder, tried top-down

| Rung | Channel | Why it ranks here | Sources |
|---|---|---|---|
| **1** | **Official API** | The provider built it for this. Stable contract, versioned, explicit terms | Saramin, Worknet |
| **2** | **Personal tokenised feed** | My own data, through a URL I issued. No credential is stored anywhere | LMS calendar ICS, LMS forum RSS |
| **3** | **Public feed** | Published for anyone to subscribe to | School notice RSS |
| **4** | **Email subscription** | The provider sends it. Legal, but latency depends on their schedule | Wevity, JobKorea, Linkareer |
| **5** | **Paste / screenshot** | No machine channel exists (ADR-018) | KakaoTalk, academic calendar |
| **6** | **Authenticated fetch, own account only** | Conditions in §3 below, all of them | LMS course materials (conditional) |
| ✗ | **Scraping a commercial site** | **Permanently prohibited.** ADR-002's reasoning stands | JobKorea, Saramin web, Linkareer |

**A lower rung may only be used after every higher rung has been checked and recorded as
unavailable in `SOURCES-001`.** "I didn't look" is not "unavailable".

### 2. Investigation before integration

Every new source is investigated *before* any adapter is written, and the answer — including
"nothing exists" — is recorded in `SOURCES-001`. This is a B0 activity and is repeated
whenever a source is added.

### 3. Authenticated fetching runs on the client, never on the server

If rung 6 is ever used, the code runs **inside the laptop sync agent** (B18), not in the
cluster:

- Credentials live in the **OS keychain** on the laptop and are **never transmitted to the
  server**.
- The agent sends only the resulting Items and files, through the interfaces that already
  exist.
- The server keeps no university credential, ever.

Rung 6 additionally requires **all** of:

1. The service's terms contain no prohibition on automated access.
2. Access is limited to the user's own account and to **reading**. Never submit, modify or
   delete.
3. Higher rungs have been checked and recorded as insufficient.
4. The friction being solved is **recorded**, not assumed — `usage_events` shows it is a real
   weekly cost (the same evidence rule as ADR-018 and B21).
5. Failure is loud: an empty result is treated as failure, not success.

### 4. Immediate consequences

- `REQ-001` §4 is corrected: Saramin moves from *Excluded* to *rung 1*.
- Worknet is added as a new source.
- **B23** (public recruitment APIs), **B24** (LMS calendar and notices) are added to the
  roadmap. **B25** (agent-side authenticated fetch) is added as **conditional**, gated on the
  five conditions above.

## Rationale

### Why an API rung belongs above everything

- **Terms are explicit.** An API has a published contract; scraping has an inference about
  what a provider would tolerate. The difference is the entire reason `ADR-002` exists.
- **Format stability.** APIs version and break loudly. HTML changes silently and returns an
  empty list, which is precisely the silent-failure class `PRD-000` §6 and `ADR-010` name as
  this project's worst outcome.
- **Query, don't wait.** Email subscription delivers what the sender decides to send when they
  decide to send it. An API answers a question: *cloud, entry level, last 7 days*. `FR-3`'s
  filter rules become far more precise against a queried result set than against an inbox.
- **It makes the coverage audit partly automatic.** `PRD-000` §4.1 has the owner manually
  comparing ten postings a week against the database. With Saramin's API that comparison can
  be run in code for that source — the audit stops being entirely manual without stopping
  being an external reference.
- **Cost is zero and quotas are ample.** 500 calls/day against a collector that runs once a
  day is not a constraint.

### Why authenticated fetching cannot run on the server

Three independent reasons, any one of which is sufficient:

1. **Blast radius.** The Gmail token is `readonly` on a dedicated collection account
   (`SEC-3`, `SEC-4`); a leak exposes that mailbox. A university account credential exposes
   grades, course registration, academic records and payment information. Putting it in the
   same database as everything else would make a single compromise catastrophic in a way
   nothing else in this system is.
2. **Memory.** Authenticated sites generally need a real browser session. Headless Chromium
   costs roughly 300–500 MiB. The `ARCH-001` ledger has **415 MiB of headroom in total**.
   It does not fit — this is arithmetic, not preference.
3. **Failure locality.** A scraper breaks when a page changes. On the server that becomes a
   cluster incident; on the laptop it is a script that failed while the owner was sitting in
   front of it.

The agent already exists as a component (B18), already manages local state that survives
crashes, already runs on a machine with a browser, and `SEC-18` already establishes the
principle that **the agent holds secrets the server does not**. Rung 6 is that principle
extended, not a new architecture.

### Why the ICS rung is better than it looks

`ADR-019` defined the time model as `starts_at` / `due_at` / `all_day`. iCalendar's
`DTSTART` / `DTEND` / `VALUE=DATE` is the same shape, because the calendar standard is where
that shape comes from. The LMS calendar adapter is therefore close to a direct mapping rather
than an interpretation — which is exactly the property that makes a source trustworthy.

And it needs **no password**. For the capability the owner ranked first — never missing a
deadline — the highest-value source turns out to be the one with the lowest security cost.

## Trade-offs

| Gained | Given up |
|---|---|
| Saramin returns to the project; Worknet is added; both legally unambiguous | Two more API keys to obtain, store and rotate |
| LMS deadlines arrive with **zero credentials stored** | Depends on the LMS admin having left calendar export enabled |
| Queried sources make filtering precise and the coverage audit partly automatic | Two more source adapters to keep working |
| A written rule that keeps the project out of the legal risk ADR-002 identified | Investigation work before every new source, including sources that turn out to have nothing |
| Authenticated fetch, if ever used, cannot leak a university credential from the server | Rung 6 lives in the agent, so it only runs when the laptop is on |
| The memory ledger is untouched | Course materials stay manual until B25's conditions are met, if ever |

## Alternatives rejected

- **Leave ADR-002 as it stands.** Cheapest. Rejected on a factual error: a source was excluded
  from the project on the belief that no channel existed, when an official API did.
- **Server-side authenticated scraping with credentials in a Kubernetes Secret.** The obvious
  implementation. Rejected on all three grounds in §"Why authenticated fetching cannot run on
  the server" — any one would have been enough.
- **Scrape the job boards now that the pipeline is proven.** Rejected outright and
  permanently. `ADR-002` identified a single takedown as project-ending, and having an
  official API available makes the argument for scraping the same site indefensible.
- **Scrape the university academic calendar page.** Defensible — a public page, not
  commercially protected — but it means maintaining a scraper subject to `NFR-7` and to page
  layout, to capture two updates a year. The paste channel (ADR-018) already covers it.
  Revisit only if the calendar proves to change more often than expected.
- **Use Moodle Web Services instead of ICS.** Strictly better if available: it would reach
  course materials through an official API, with no credential storage and no scraping —
  collapsing rung 6 into rung 1. Not chosen because **site administrators must enable web
  services and rarely do for students.** B0 checks; if it turns out to be enabled, this ADR
  should be superseded, and that would be a good outcome.
- **A browser extension that harvests pages the owner is already viewing.** Neat, and it
  sidesteps authentication entirely. Rejected: a second platform to build and maintain, in a
  project whose learning budget is aimed at cloud infrastructure.

## Open questions

- **Saramin API pricing and personal-use terms.** The published guide states the 500/day limit
  and the access-key requirement but not pricing. Confirm at application time (B0/B23) and
  record in `SOURCES-001`.
- **Whether Moodle Web Services is enabled** for students on this LMS. If yes, this ADR is
  superseded for the LMS portion. Checked in B0.
- **Whether the Worknet dataset's granularity is useful.** Government job data skews toward
  employers who post there; it may add little for the owner's field. Measure coverage overlap
  with the email sources after one month of B23, and drop the source if it adds nothing —
  a source that contributes no unique items is maintenance for nothing.
- **Rate-limit handling as a shared concern.** Two APIs with different quotas and different
  error shapes suggests a common retry/backoff layer in the `Source` abstraction. Decide when
  the second API adapter is written, not before.
