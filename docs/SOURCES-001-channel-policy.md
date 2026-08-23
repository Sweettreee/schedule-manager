# SOURCES-001 — Source Matrix and Channel Policy

**Status**: Approved
**Created**: 2026-08-22
**Related**: ADR-002, ADR-018, ADR-021, REQ-001 §4

This document is the register of **where every piece of information comes from**, and the
procedure for adding a new source. It is updated whenever a source is investigated, added,
changed or dropped — including when the answer is "nothing exists".

## 1. The ladder (ADR-021)

Try top-down. A lower rung may be used only after every higher rung has been checked and
recorded here as unavailable. **"I didn't look" is not "unavailable".**

| Rung | Channel | Credential cost |
|---|---|---|
| 1 | Official API | an API key |
| 2 | Personal tokenised feed (ICS, RSS with token) | **none** |
| 3 | Public feed (RSS/Atom) | none |
| 4 | Email subscription | none (mailbox already exists) |
| 5 | Paste / screenshot (ADR-018) | none |
| 6 | Authenticated fetch, own account, **agent-side only** | **a real account credential** |
| ✗ | Scraping a commercial site | prohibited permanently |

## 2. Source matrix

Status values: **Confirmed** (verified, working) · **Planned** (channel known, not built) ·
**To investigate** (B0) · **Excluded** (with a reason).

### Schedules and school

| Source | Rung | Channel | Status | Block | Notes |
|---|---|---|---|---|---|
| LMS deadlines (과제·시험) | 2 | Moodle **iCalendar export URL** | **To investigate** | B24 | URL pattern `lms.chungbuk.ac.kr/mod/ubboard/…` indicates Moodle. Per-user tokenised URL, no password |
| LMS course notices | 2 | Moodle **forum RSS** | To investigate | B24 | |
| LMS course materials (files) | 6 | agent-side authenticated fetch | **Conditional** | B25 | Only if §4 conditions all hold |
| School notice board | 3 | RSS/Atom, or email subscription | To investigate | B3 | Email subscription is cheaper than RSS if offered |
| Academic calendar (수강신청·시험기간) | 5 | **paste** | Planned | B6 | A page updated ~once a semester. Not a feed; polling two changes a year is not worth a scraper |
| Club / department schedules | 5 | **paste / screenshot** | Planned | B6 | KakaoTalk has **no read API** — verified 2026-08-22 (ADR-018) |

### Jobs and contests

| Source | Rung | Channel | Status | Block | Notes |
|---|---|---|---|---|---|
| **Worknet / 고용24** | **1** | 공공데이터포털 open API (한국고용정보원) | **Planned** | B23 | Government open data. Legally the cleanest source in the project. Auth key only |
| **Saramin** | **1** | `oapi.saramin.co.kr` Open API | **Planned** | B23 | **500 calls/day**, access key after application. Pricing not published — confirm on application. *Previously excluded in error* |
| Wevity | 4 | email subscription | Planned | B0/B2 | Categories: 웹·모바일·IT, 게임·SW, 과학·공학, 취업·창업 |
| JobKorea | 4 | job-alert email | Planned | B0/B2 | Scraping explicitly prohibited, case law exists (ADR-002). Email only |
| Linkareer | 4 | email alerts | **To investigate** | B0 | Must log in to check whether alerts exist |
| Saramin (web) | ✗ | — | **Excluded** | — | Superseded by the API at rung 1 |
| Campuspick | ✗ | — | Excluded | — | App-only, no email evidence |

## 3. B0 investigation checklist

Run this for every source. **Record the answer even when it is "none".** A recorded "none" is
what licenses moving down the ladder; an unrecorded one is a gap.

| # | Question | Why it matters |
|---|---|---|
| 1 | Is there an official API? Documentation URL? | Rung 1 candidate |
| 2 | Authentication: key / OAuth / tokenised URL / login? | Determines the whole security design |
| 3 | Quota and pricing? | Saramin is 500/day; public data portals typically cap daily traffic |
| 4 | Do the terms permit personal, automated use? | The legal basis (NFR-7) |
| 5 | Is there a public feed (RSS/Atom/ICS)? | Rungs 2–3 |
| 6 | Is email subscription offered? | Rung 4 — often cheaper than a feed |
| 7 | `robots.txt` | NFR-7 |
| 8 | If none of the above: what is the fallback rung? | Usually 5 (paste) |

### LMS-specific order — check in this sequence and stop at the first hit

1. **Calendar → "iCal 내보내기" / export / subscription URL.** If present, deadlines are
   solved with no password. Copy the URL; treat it as a secret (`SEC-13` pattern).
2. **Notice board / forum → RSS icon or feed URL.**
3. **Site administration → Web services** — is the Moodle Web Services API enabled for
   students? Almost certainly not, but the check costs five minutes and, if enabled, it
   reaches course materials through an official API and **supersedes ADR-021's rung 6
   entirely**. That would be the best available outcome.
4. Only if 1–3 all fail: evaluate rung 6 against §4.

## 4. Rung 6 gate — authenticated fetch

**All five must hold. Record each in the block write-up.**

| # | Condition |
|---|---|
| 1 | The service's terms contain **no prohibition on automated access** |
| 2 | Own account only, and **read-only** — never submit, modify or delete |
| 3 | Rungs 1–5 checked and recorded as insufficient for this specific need |
| 4 | The friction is **recorded in `usage_events`**, not assumed — the same evidence rule as ADR-018 and B21 |
| 5 | Failure is loud: an empty result is treated as failure, never as success |

**Where it runs**: inside the laptop sync agent (B18). Credentials live in the **OS keychain**
and are **never transmitted to the server**. See ADR-021 §3 and SEC-19.

## 5. Adding a new source later

1. Run §3. Record the result here — including "nothing exists".
2. Pick the highest available rung.
3. If it is rung 1–4, it is an adapter behind the existing `Source` abstraction (B3). If a new
   source needs more than an adapter, **that is a finding worth recording** — ADR-003's
   one-table claim would be under strain.
4. If it is rung 6, satisfy §4 first and write an ADR.
5. Add it to the coverage audit rotation (PRD-000 §4.1).
6. Update this table and `REQ-001` §4.

## 6. Quotas and keys register

Filled in as sources are activated. Keys themselves live in secrets storage (ADR-009), never
here.

| Source | Key held where | Quota | Renewal | Last verified |
|---|---|---|---|---|
| Worknet (공공데이터포털) | *(B23)* | *(daily cap)* | | |
| Saramin | *(B23)* | 500 / day | | |
| LMS calendar ICS | *(B24)* | n/a | token may be regenerable | |

## 7. Sources dropped, and why

Kept so a future session does not re-investigate a closed question.

| Source | Dropped | Reason | Would reopen if |
|---|---|---|---|
| KakaoTalk API | 2026-08-22 | Message API is **send-only**; no read endpoint exists in the platform | Kakao publishes a read API |
| Saramin web scraping | 2026-08-22 | Superseded by the official API | never |
| JobKorea scraping | 2026-08-20 | Explicitly prohibited, case law exists (ADR-002) | never |
| Campuspick | 2026-08-20 | App-only, no email or feed evidence | a feed or email alert appears |
