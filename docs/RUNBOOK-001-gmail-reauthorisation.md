# RUNBOOK-001 — Re-authorising the Gmail collector

**Created**: 2026-09-02 · **Decided in**: ADR-027 · **Applies to**: the collection mailbox
only

## When to use this

`make run` (or the collector) fails with **exit code 3** and a message beginning:

> Google no longer accepts the stored refresh token…

That means the stored refresh token used to work and no longer does. It does **not** mean the
network is down — a transient failure is deliberately not reported this way (ADR-027,
decision 4).

**Not this runbook:**

- **Exit code 2**, "returned credentials without a refresh token" → the grant was wrong when
  issued. Check the consent screen's publishing status first; see ADR-007.
- **Exit code 2**, "OAuth client secret not found" → `api/.secrets/client_secret.json` is
  missing.
- A `RefreshError` traceback → a network or Google-side failure. Retry later. Do not
  re-authorise; see step 0.

## Step 0 — do not re-authorise reflexively

Google allows **100 refresh tokens per account × client ID**, and evicts the oldest **without
warning** when the limit is reached. Every unnecessary re-authorisation moves the operating
token one place closer to eviction. Confirm the exit code is 3 before continuing.

## Step 1 — establish which cause fired

| Ask | If yes |
|---|---|
| Was the collection account's password changed recently? | That is the cause. Continue. |
| Was access revoked at `myaccount.google.com/permissions`? | That is the cause. Continue. |
| Have many authorisations been run against this client recently? | Likely the 100-token limit. Continue, and read ADR-027 open question 2. |
| None of the above, and the collector has been idle for six months? | Idle expiry. Continue. |

Record the answer — it belongs in the `STATUS.md` entry for the incident.

## Step 2 — confirm the consent screen is still "In production"

Google Cloud Console → APIs & Services → OAuth consent screen.

If it reads **Testing**, that is the real fault: any token issued now expires in seven days
(ADR-007). Set it back to **In production** before going further.

## Step 3 — delete the dead token

```
rm api/.secrets/gmail_token.json
```

Only this file. Do **not** delete `client_secret.json` — it is the OAuth client itself, not
the grant, and re-downloading it from the console is a separate job.

## Step 4 — re-authorise

```
cd api && make run
```

A browser opens. Sign in **as the collection account**, not a personal account. At "Google
hasn't verified this app", choose **Advanced → Go to Schedule Manager (unsafe)**. That warning
is expected and is documented in ADR-007's trade-offs.

## Step 5 — verify the repair

```
ls -l api/.secrets/gmail_token.json                     # expect -rw-------  (0600)
grep -c refresh_token api/.secrets/gmail_token.json     # expect 1
cd api && make run                                      # expect messages, no browser
```

If the third command opens a browser again, the grant carried no refresh token. Stop and read
ADR-007 — the usual cause is a consent screen in Testing status.

**Never print the file's contents to a terminal, a log or an issue.** `CLAUDE.md` §2 rule 3.

## Step 6 — record it

Add to `STATUS.md`: the date, the cause from step 1, and the new token's issue date. The issue
date matters because token age is not recoverable from the file — the JSON carries no expiry
information, so the only record of when a grant began is the one written down.

## What must never be done

- **Downgrading the failure to a warning to make a run succeed.** The loud failure is the
  safety property; `CLAUDE.md` §2 rule 8 forbids weakening it.
- **Automating this runbook into the collector.** On a headless node there is no browser to
  consent in, so an automatic retry hangs instead of recovering (ADR-027, alternatives).
