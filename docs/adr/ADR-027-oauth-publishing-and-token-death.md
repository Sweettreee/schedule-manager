# ADR-027 — Gmail OAuth: Publishing Confirmed, and Token Death Made Actionable

**Status**: Accepted
**Date**: 2026-09-02
**Amends**: ADR-007
**Related**: ADR-010, ADR-012, `docs/RUNBOOK-001-gmail-reauthorisation.md`

## Context

ADR-007 chose OAuth with the app published "In production", and closed with two loose ends:

1. An **open question** — Google's verification rules for restricted scopes change, so the
   current rules had to be reconfirmed at the start of B1.
2. A **two-working-day timebox**, after which the IMAP + app-password fallback would fire.

Both were resolved on 2026-09-02, and a third issue surfaced while resolving them: ADR-007
addressed the refresh token that is *never issued*, and said nothing about the refresh token
that is issued, works for months, and then dies.

## Decision

**1. The OAuth main path stands. The IMAP fallback is not triggered.**
The app is published **In production, unverified**. Verification is not pursued.

**2. ADR-007's fallback clause is retained, marked not triggered.**
It is not deleted. The rule that decided this block is worth more on the record than the two
lines it costs, and the condition could recur if Google's policy changes again.

**3. A refresh token that Google stops accepting raises `ReauthorisationRequiredError`,
and the CLI exits 3.**
Recovery is `docs/RUNBOOK-001-gmail-reauthorisation.md`. This is distinct from
`MissingRefreshTokenError`, which is about a grant that was wrong the moment it was issued.

**4. Only `invalid_grant` is converted. Every other `RefreshError` propagates untouched.**

## Rationale

**On publishing (findings, 2026-09-02):**

- The seven-day refresh-token expiry applies to the combination **Testing publishing status +
  External user type + more than basic scopes**. Verification status is not one of the
  conditions. Publishing to production removes it.
  Source: `developers.google.com/identity/protocols/oauth2` — "Refresh token expiration".
- **Verification is not required to publish.** `Published + External + Unverified` is a
  reachable, usable state. The cost is a one-time "unverified app" warning at consent and a
  cap of 100 users — irrelevant at one user.
  Source: `support.google.com/cloud/answer/13464323`.
- The console's "your app requires verification" banner is guidance, not a block.
- Personal use is named in Google's own documentation as an exemption. This is not a
  workaround.

So the expensive path (verification) was never on the critical path, and the cheap one
(a publishing-status radio button) is all ADR-007 ever required.

**On token death.** Publishing removes the seven-day timer but not every way a grant ends:

| Cause | Reachable here? |
|---|---|
| Mailbox password changed — revokes tokens carrying Gmail scopes | Yes, and likely |
| 100 refresh tokens per account × client ID; the oldest is evicted **without warning** | Yes — repeated re-authorisation during development can silently kill the operating token |
| Six months without use | Unlikely (daily collector) |
| Grant revoked by the user | Yes, deliberately |

Before this ADR, all four surfaced as an unhandled `RefreshError` traceback. Loud, but it
named neither the cause nor the fix, at 08:05 on a machine with no browser.

**On the narrow catch (decision 4).** google-auth raises `RefreshError` both for a dead grant
and for a transient network failure. Converting all of them would tell the owner to
re-authorise whenever the network blinked — deleting a healthy token, and burning one of the
100 refresh tokens to replace it. The failure mode of over-catching is worse than that of
under-catching, so the catch is narrow.

## Trade-offs

| Gained | Given up |
|---|---|
| Refresh tokens do not expire on a timer | A one-time "unverified app" warning at consent |
| A dead grant names its cause and its fix | One more exception type for later blocks to handle |
| A network blip is never mistaken for a dead grant | The discriminator is a string, not a typed field |

## Alternatives rejected

- **IMAP + app password** (ADR-007's fallback) — not needed; the blocking question was answered.
- **Reuse `MissingRefreshTokenError` for both cases** — the two have different causes and
  different remedies, and one message covering both serves neither at 08:05.
- **Delete the dead token and re-run the consent flow automatically** — on a headless node
  there is no browser to consent in, so this would hang rather than recover, and it hides the
  failure. `CLAUDE.md` §2 rule 8.
- **Convert every `RefreshError`** — see decision 4.

## Open questions

1. **The `invalid_grant` discriminator is a substring match**, because google-auth carries the
   OAuth error code in the exception's arguments rather than in a typed field. If Google
   rewords the response, a dead grant is misreported as a transient failure. Unit tests fix
   the branching logic but cannot detect the rewording; only a real failure would.
2. **Separate OAuth clients for development and production** — Google recommends splitting
   them, partly because of the 100-token limit. One client is in use today. Deferred with a
   trigger in `STATUS.md` §6.
3. ~~**The consent screen's scope list is empty**~~ — **answered by the first live run,
   2026-09-02.** The flow completed and Google granted `gmail.readonly`, which appeared in the
   loopback callback, with nothing declared in the console. The scope is requested by the client
   at runtime from `config.GMAIL_SCOPES`, and that is sufficient. Declaring it in the console
   remains worth doing for accuracy, but nothing depends on it.

   A separate 403 did follow: `accessNotConfigured`, because the **Gmail API had never been
   enabled on the Cloud project**. Enabling an API is independent of both the consent screen and
   the grant — a third switch, and B1 task 1's second half. Handling that class of `HttpError`
   belongs to **B2**, where `collection_runs` gives a failed call somewhere to be recorded.

## Detection

Nothing in this ADR notices a dead grant on its own — it only makes the failure legible once
someone runs the collector. Unattended detection is the ADR-012 dead man's switch, which is
**B13**, and B13 must exist before collection runs unattended.
