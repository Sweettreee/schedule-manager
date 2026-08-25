# LMS calendar token exposed in a chat transcript — 2026-08-24

**Type**: Unplanned — **near-miss** (no system compromise)
**Block**: B0
**Duration**: n/a — no outage. Exposure window is open until the token is rotated.
**Impact**: A live Moodle calendar `authtoken` for `lms.chungbuk.ac.kr` was pasted into an
assistant chat session. That token is a **read credential for the owner's personal LMS
calendar** — 과제·시험 마감, course names, and any personal calendar events. Nothing in the
Schedule Manager system was affected; no project data, account or infrastructure was touched.
**Detected by**: noticed during the same session, while writing up the B0 LMS finding.

## What actually happened

While investigating whether the LMS offers an iCalendar export (`SOURCES-001` `FEED` rung), the
export URL was shared in chat inside a markdown link:

```
[<token blanked in the display text>](https://lms.chungbuk.ac.kr/calendar/export_execute.php?userid=…&authtoken=<REAL TOKEN>&…)
```

The **display text** had the token blanked. The **href** did not. Markdown renders the display
text and hides the URL, so the paste looked redacted while carrying the live credential.

The token was therefore transmitted to, and may persist in, the chat transcript and the model
provider's logs.

No real token value appears in this write-up, in `SOURCES-001`, or anywhere else in the
repository — and none ever should (`SEC-001`, `CLAUDE.md` hard rule 3).

## Root cause

**The credential is shaped like a URL, so it was handled like a URL.**

Moodle's calendar export needs no cookie and no header: the `authtoken` query parameter *is*
the entire credential. Anyone holding the URL can read the calendar. This is the `SEC-13`
"URL-as-secret" pattern, and this incident is a demonstration of exactly why that pattern is
called out separately from ordinary secrets — a `password` field prompts caution by its name;
a link does not.

The trigger was the markdown link. The cause is that **a redaction was applied to the visible
half of a two-part construct**, which is a general property of markdown links, not a slip
specific to this token.

## What surprised me

That the blanking *looked* like it worked. The rendered output was genuinely redacted — the
mistake was invisible in exactly the medium being used to check it. A redaction you can verify
by looking is not a redaction; it has to be verified in the raw text.

Also: the LMS hides the Calendar nav item but leaves `/calendar/export.php` live. The
credential was reachable through a route the UI does not advertise, which is worth remembering
when reasoning about what a wrapper theme has actually disabled versus merely hidden.

## Recovery

- [ ] **Rotate the token** on the Moodle export screen (`/calendar/export.php`) before B24
      wires it into anything. If the `coursemos`/UBION theme has removed the reset control,
      **that is itself a finding** — record it in `SOURCES-001` §2, because it would mean the
      credential cannot be rotated by the owner.
- [x] Confirmed no token value reached the repository, git history, or any project document.

## Follow-ups

- [ ] **B24 — the Secret stores base URL, `userid` and `authtoken` as three separate values**,
      never the assembled URL. This is required by `SOURCES-001` §2.1 for a different reason
      (so `preset_time` can be asserted in a test) and it helps here too: the parts are
      individually redactable.
- [ ] **B24 — `authtoken` must be masked in every log line, exception message and traceback.**
      A fetch failure that prints the URL writes the credential into the log. This is a
      concrete code requirement, not a guideline.
- [ ] **B24 — never render the ICS URL in the dashboard**, including in an error banner.
- [ ] Rotate the token again at the end of B24 if it was used during development, on the
      assumption that development artefacts leak.

## Metrics touched

None. No error budget consumed (`REQ-001` §7) — collection was not running and no SLO applies
yet. RPO/RTO not applicable.

## Why this is written up at all

Nothing broke, and it would have been easy to fix quietly. It is here because a near-miss with
a clear mechanism is worth more than an incident with a murky one, and because the mechanism
generalises: **this project will hold more URL-shaped credentials** — any tokenised feed added
later. The handling rule needs to exist before the next one, not after. *(Updated 2026-08-25:
this originally named the LMS forum RSS feed as the next such credential. It does not exist —
the LMS has no forum RSS. The rule stands on the ICS feed alone.)*
