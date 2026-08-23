# ADR-007 — Gmail Authentication: OAuth with a Published App

**Status**: Accepted
**Date**: 2026-08-21
**Related**: ADR-002, SEC-001

## Context
The collector must read a Gmail mailbox unattended, once per day, indefinitely.

There is a specific trap here. A Google Cloud OAuth app left in **Testing** publishing status
issues refresh tokens that **expire after seven days**. The collector would then stop on day
eight — and because the dashboard keeps displaying the previous data, the failure is silent.
That is precisely the failure mode PRD-000 identifies as worse than the original problem.

## Decision
Use the **Gmail API with OAuth 2.0**, with the Google Cloud OAuth app set to **In production**
publishing status, scope limited to `gmail.readonly`, against a dedicated Gmail account.
The refresh token is stored as a secret per ADR-009.

## Rationale
- Publishing the app removes the seven-day refresh token expiry.
- OAuth2 and token lifecycle management were named in REQ-001 as learning objectives.
- `gmail.readonly` is the least privilege that satisfies the requirement.
- The residual risk of silent failure is covered by `collection_runs` plus webhook alerting.

## Trade-offs
| Gained | Given up |
|---|---|
| Tokens do not expire on a timer | More Google Cloud Console setup |
| Real OAuth2 experience | An "unverified app" warning must be clicked through at consent |
| Least-privilege scope | A Google Cloud project must be maintained alongside AWS |

## Alternatives rejected
- **IMAP with an app password** — much simpler and never expires, but discards the OAuth2
  learning objective entirely. This remains the fallback if Google's policy makes publishing
  impractical.
- **OAuth in Testing status with manual weekly re-authentication** — guarantees the exact
  silent-failure mode the project is designed to prevent.
- **Gmail push notifications via Pub/Sub** — lower latency and interesting, but requires a
  public HTTPS endpoint and a second cloud dependency for a workload that runs once a day.
  Revisit if the collection interval ever needs to approach real time.

## Open questions
Google's verification requirements change. Confirm the current publishing rules for
restricted scopes at the start of block B1, before building around them.

## Fallback trigger (added 2026-08-22, REVIEW-001)

`gmail.readonly` is a **restricted scope**. Google's verification process for restricted
scopes can require a third-party security assessment, which is not practical for an
individual student developer. The original ADR named IMAP + app password as the fallback but
gave no condition for choosing it, which risks an open-ended fight with a console.

> **Timebox: 2 working days.** If publishing the app to production is not working by then,
> execute the IMAP + app-password fallback, record it as a new ADR amending this one, and
> continue. What is lost is the OAuth2 token-lifecycle learning objective; what is preserved
> is the project.

This is written down in advance so the decision is made by a rule rather than by fatigue.
