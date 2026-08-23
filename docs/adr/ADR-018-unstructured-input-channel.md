# ADR-018 — Unstructured Input: Paste and Screenshot with LLM Extraction

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-002, ADR-003, ADR-010, ADR-017, REQ-001, SEC-001, ARCH-001

## Context

Two of the highest-priority sources have **no machine channel at all**.

**KakaoTalk.** Club and department schedules arrive in group chats. The official Kakao
Developers documentation describes a **send-only** messaging API: messages can be sent to
oneself ("나와의 채팅방") or to friends, and there is **no API anywhere in the platform to read
or retrieve messages from a chat room**. This is the same shape of problem `ADR-002` faced
with JobKorea scraping — the obvious channel is closed — except that here there is no email
fallback, because the content never leaves KakaoTalk.

**The academic calendar.** 수강신청 기간, 개강, 종강, 시험기간 live on a university page that
is updated roughly once a semester. It is not a feed. Polling it daily to catch two changes a
year would be building a scraper to solve a copy-paste problem.

The residual channels for KakaoTalk were assessed:

| Option | Verdict |
|---|---|
| Export chat to `.txt` and upload | Legal, reliable, manual |
| **Paste text or a screenshot into the dashboard** | Legal, reliable, lowest friction |
| Android notification-listener app | Requires building an Android app; only catches messages that raise a notification; terms-of-service grey area |
| Desktop client automation | Fragile; terms-of-service risk |

The owner chose: **paste the text or drop a screenshot, and have the system work out what it
means and register it.**

That decision generalises further than KakaoTalk. It is a channel for *any* source with no
API — the academic calendar, a poster photographed on a noticeboard, a professor's
announcement slide, a message from any other messenger.

## Decision

**A "붙여넣기" input: the user pastes text or drops a screenshot, an LLM extracts structured
fields, the user confirms or edits the result, and it is saved as an `items` row with
`source = 'PASTE'`.**

Specifics:

1. **Text and images both accepted.** Screenshots go to a vision-capable model directly; no
   separate OCR stack is installed. Running Tesseract on a 2 GiB node to feed a model that
   reads images natively would be work in exchange for a worse result.
2. **Extraction output is a strict schema**, not prose: `title`, `org`, `starts_at`, `due_at`,
   `all_day`, `type`, `tags`, and a `confidence` per field.
3. **Human confirmation is mandatory.** The extraction populates a form; the user reviews and
   saves. Nothing is written to `items` without a click. Low-confidence fields are highlighted.
4. **The raw paste is stored in `raw`** and falls under the same 90-day purge as mail (SEC-6),
   so a bad extraction can be re-run when the prompt improves — the same reasoning that
   preserves `raw` for email in ADR-003.
5. **A hard monthly call cap** is enforced in the API, defaulting to 300 calls. Exceeding it
   disables extraction and alerts, rather than spending money.
6. **Rules are tried first where they are cheap**: a pasted blob that is unambiguously a
   KakaoTalk export (a known line format) is parsed by rule, and only free-form content
   reaches the model.

## Rationale

### Why this is not a violation of the "no AI in v1" principle

`REQ-001` §6 and block B21 establish that LLM classification is adopted only once
misclassification data proves rules are insufficient. That principle is intact, and this is
not an exception to it — it is the same principle applied to a different problem.

The distinction is **whether the input has a stable format**:

| | Newsletter classification (B21) | Paste extraction (this ADR) |
|---|---|---|
| Input | Mail from a known sender, same template every week | Arbitrary human writing: *"담주 화욜 3시 동방에서 회의"* |
| Can a rule work? | **Yes** — sender address alone gets most of it, free and exact | **No.** There is no format to write a rule against |
| Is more data needed to decide? | **Yes** — that is why B21 waits | **No.** The input is already known to be unstructured |

Waiting for evidence makes sense when a cheap solution might turn out to be sufficient. Here
the cheap solution is known in advance to be insufficient, so waiting would collect evidence
for a conclusion already reached. **The principle is "decide from evidence", not "delay by
default".**

### Why human confirmation is not optional

An extraction that silently writes a wrong deadline is worse than no extraction, because the
user then trusts it. That is the same failure shape `PRD-000` §6 identifies as the project's
worst outcome: **confident wrongness beats visible absence.** A confirmation step converts a
silent data error into a visible one, at the cost of one click.

It also makes the feature testable. `ADR-010` puts parsing in the "test-after" category
precisely because its specification is discovered from real inputs; confirmation gives a
natural place to capture the cases where extraction was wrong, which become fixtures.

### Why an external API rather than a local model

A model small enough to run in the ~415 MiB of spare RAM on a `t4g.small` (ARCH-001) would
extract Korean dates and event names badly. This is not a close call. The alternative is not
"local model" but "no feature".

### Cost

On-demand only — a few pastes a week, not a polling loop.

| | |
|---|---|
| Expected volume | 20–60 calls/month |
| Cap | 300 calls/month, enforced in code |
| Cost at the cap, small model, ~2k tokens/call | well under **$1/month** |
| Added to ARCH-001 | **≈ $0.3/month expected, $1 worst case** |

The cap exists because the realistic failure mode is a bug in a retry loop, not usage.

## Trade-offs

| Gained | Given up |
|---|---|
| KakaoTalk, the academic calendar, posters and any future API-less source all covered by one feature | An external LLM dependency and a recurring cost enter v1 |
| Zero terms-of-service risk — the user is pasting their own screen | The input is manual; this is not "automatic collection" |
| A general escape hatch: any source can always be captured, however weird | A confirmation step on every paste |
| Wrong extractions are visible and become test fixtures | Prompt quality becomes an operational concern with no test suite of its own initially |
| The raw paste is retained, so extraction improves retroactively | 90 days of pasted personal content sits in the database |

**The honest cost**: the project description says information is collected *automatically*.
For these two sources it is not, and no legal channel exists that would make it so. This ADR
chooses a manual step over either an unlawful one or an absent feature.

## Privacy — this needs explicit treatment

Pasted KakaoTalk content contains **other people's messages**. That is third-party personal
data leaving the system and being sent to a model provider. This is a materially different
situation from the owner's own mail, and it is not resolved by the fact that the owner could
read it in the app.

Controls, recorded in SEC-001:

1. **Paste only what is needed** — the message about the schedule, not the whole day's chat.
   The UI states this at the input, not in a settings page nobody reads.
2. **Use a provider with a no-training-on-input commitment**, and record which provider and
   which commitment in the block's write-up. Re-check at each monthly review.
3. **Raw pastes are purged after 90 days**, in backups as well (SEC-001 retention rules).
4. **Never send a paste anywhere other than the extraction call.** No logging of raw content
   to metrics, traces, or incident write-ups.
5. **Screenshots follow the same rules** and are not retained as images beyond extraction —
   only the extracted fields and the OCR text persist.

## Alternatives rejected

- **KakaoTalk chat export (`.txt`) upload.** Legal and reliable, and it captures a whole
  conversation at once rather than one message. Rejected as the *primary* path only because
  the export flow is several steps on a phone and the value is usually one message — but it is
  **retained as a supported input format** for bulk backfill, and the rule-based parser in
  decision point 6 exists for it.
- **Android notification-listener app.** Near-real-time and automatic. Rejected: it requires
  building and maintaining an Android application — a second platform, in a project whose
  learning budget is aimed at cloud infrastructure — catches only messages that raise a
  notification, and sits in a terms-of-service grey area of exactly the kind ADR-002 chose to
  stay out of.
- **Desktop KakaoTalk window automation.** Rejected on fragility and terms of service.
- **Manual form entry with no extraction.** Zero cost, zero dependency, no privacy question.
  Rejected because it is the status quo the project exists to eliminate: `PRD-000` P-1 is
  literally "the same information is re-typed by hand".
- **Rule-based parsing of free-form Korean.** Attempted mentally against real examples
  (*"담주 화욜"*, *"이번주 금 저녁"*, *"25일까지"*) and abandoned. A rule set that handles these
  is a worse language model.
- **Scraping the university academic calendar page.** Defensible — it is a public page and,
  unlike JobKorea, university notice boards are not commercially protected — but it means
  writing and maintaining a scraper, subject to `NFR-7` (robots.txt) and to the page's layout,
  to capture two updates a year. The paste channel already exists. Revisit only if the
  calendar turns out to change more often than expected.

## Open questions

- **Which model and provider.** Decide in block B6 against actual Korean date-expression
  samples, and record the choice, the price, and the data-handling commitment as part of the
  block. The owner has prior experience with the Claude API, which is the starting candidate.
- **Whether extraction should also run on low-confidence email parses** (block B20) once the
  rule-based parser exists. That would be a second use of the same capability and should be
  decided from B20's error data, not now.
- **Whether the confirmation step can be relaxed** for high-confidence extractions after
  enough accuracy data accumulates. Revisit only with measured precision, and never for
  `due_at` — a wrong deadline is the failure this system exists to prevent.
