# SEC-001 — Security and Privacy Baseline

**Status**: Approved
**Last updated**: 2026-08-25 (paste-privacy controls delegated to ADR-018; SEC-2 gains the
unresolved-hostname note)

## What is at stake

The database contains the full text of personal email. The dashboard is publicly reachable
from block B12 onward. A leaked Gmail refresh token grants read access to an entire mailbox.
Tokens accidentally pushed to GitHub are harvested by automated scanners within minutes.

## Controls

| ID | Control | Where |
|---|---|---|
| SEC-1 | Dashboard requires HTTP Basic Auth via ingress-nginx, credentials in a k8s Secret | B12 |
| SEC-2 | TLS terminated at ingress, certificates from Let's Encrypt via cert-manager. **Blocked on an unresolved dependency: no hostname is decided anywhere in this document set**, and an ACME challenge needs one. It also needs a *stable* address, which is why ADR-024 requires the Elastic IP. See `STATUS` §4 | B12 |
| SEC-3 | Gmail scope is `gmail.readonly` only — never a write or send scope | B1 |
| SEC-4 | A dedicated Gmail account is used for collection, isolated from the primary account | B0 |
| SEC-5 | Secrets are never committed in plaintext; staged approach per ADR-009 | B1 onward |
| SEC-6 | `raw` bodies purged after 90 days by a scheduled job, **and absent from any backup older than 90 days** (§ below) | B13 |
| SEC-7 | Test fixtures anonymised: sender addresses, names, phone numbers and URLs replaced | B2 |
| SEC-8 | SSH access by key only; password authentication disabled; security group restricts SSH to the owner's IP | B11 |
| SEC-9 | Database is not exposed outside the cluster — no NodePort, no public listener | B13 |
| SEC-10 | Daily `pg_dump` to S3; bucket has public access blocked, versioning enabled, and a lifecycle rule that expires objects (§ below) | B13 |
| SEC-11 | IAM: no use of the root account after initial setup; a dedicated IAM user with MFA | B10 |
| SEC-12 | Container images are pushed to a **private** ghcr.io package; the cluster pulls with a read-only token stored as an `imagePullSecret` (ADR-011) | B13 |
| SEC-13 | The dead man's switch ping URL is a secret — anyone holding it can suppress the alert by pinging it themselves. Stored like any other secret (ADR-012) | B13 |
| SEC-14 | Secret scanning enabled on the GitHub repositories (push protection on) | B0 |
| SEC-15 | **Pasted content may contain third parties' messages.** It goes only to the extraction call — never to logs, metrics, traces or incident write-ups. Provider must carry a no-training-on-input commitment, re-checked at each monthly review | B6 |
| SEC-16 | The file bucket blocks all public access, uses SSE at rest, and is reachable only through **presigned URLs with a 5-minute expiry**. No object is ever made public | B14 |
| SEC-17 | The API's IAM policy is scoped to the file **prefix** and to `GetObject`/`PutObject` only — no `DeleteObject`, no bucket-level rights, no access to the backup prefix | B14 |
| SEC-18 | The sync agent holds **no AWS credentials**. It receives short-lived presigned URLs from the API and nothing else | B18 |
| SEC-19 | **University and commercial account credentials are never stored on the server** — not in the database, not in a k8s Secret, not in SOPS. They live only in the laptop's OS keychain and are used only by the agent (ADR-021 §3) | B25 |
| SEC-20 | API keys for public data sources (Worknet, Saramin) and the LMS calendar token URL are secrets: never in git, never in logs, never in `raw` | B23, B24 |

## Retention and backups — resolving the conflict

SEC-6 says raw mail bodies are deleted after 90 days. A weekly-or-daily `pg_dump` that
includes the `raw` column would preserve that deleted content in S3 indefinitely, silently
voiding the policy. The live database would be clean and the backup would not.

**Rule**: the retention promise applies to *all* copies, not just the live one.

Implementation:

1. **Two dumps, not one.**
   - `full-YYYY-MM-DD.dump` — everything including `raw`. **S3 lifecycle expiry: 30 days.**
   - `nodata-raw-YYYY-MM-DD.dump` — `pg_dump --exclude-table-data` is not column-granular,
     so this is produced by dumping a view/`COPY` of `items` with `raw` set to `NULL`, plus
     all other tables in full. **S3 lifecycle expiry: 400 days.**
2. The 30-day expiry on the full dump is stricter than the 90-day live policy, which is the
   safe direction: no `raw` content can survive longer in a backup than it would have lived.
3. Restore drills (OPS-001 §5) use the full dump when it exists and the raw-free dump
   otherwise. A restore from the raw-free dump loses only reparse capability, not any
   parsed field.
4. Bucket versioning is enabled for accidental-overwrite protection; the lifecycle rule
   must therefore also expire **noncurrent versions**, or the deleted content survives as
   an old version.

## Pasted content — a third-party privacy problem, stated plainly

Every other input to this system is the owner's own data. Pasted KakaoTalk content is not: it
contains **messages written by other people who did not consent to this system.** The fact
that the owner can read them in the app does not make forwarding them to a model provider the
same act.

**The five controls that reduce it are specified in `ADR-018` §"Privacy" and enforced by SEC-15
above.** They are not restated here — they were being maintained in four places
(`ADR-018`, this document, `REQ-001` NFR-14, `CLAUDE.md` §4), which is three too many for a rule
about other people's messages.

The test that belongs here, because no other document states it:

> **If a paste would be uncomfortable to show the person who wrote it, it should not be pasted.**

That is more useful than any rule this document could write, and it is the one part of this
control that cannot be implemented in code.

## File storage — what the presigned model protects against

The API can hand out a URL that permits one operation, on one object, for five minutes. It
never holds the bytes and the agent never holds an AWS credential. Two consequences worth
stating:

- **A compromised agent cannot enumerate or delete the bucket.** It can only use URLs the API
  chose to issue.
- **A leaked presigned URL expires.** The blast radius is one object for five minutes, not
  the store.

The bucket keeps backups and file blobs under **separate prefixes with separate IAM policies**,
so the API's file credentials cannot reach the backups that exist to recover from the API.

## Dashboard authentication rationale

Basic Auth was chosen over Google sign-in for v1. It costs five minutes, requires no second
OAuth integration, and exercises Kubernetes Secrets and ingress annotations directly. Its
weakness is that credentials are shared rather than federated, which is acceptable for a
single-user system behind TLS. Google sign-in remains the upgrade path if the dashboard is
ever shared.

## Anonymisation rule for fixtures

Un-anonymised mail is kept under `fixtures/raw/`, which is in `.gitignore` and never
committed. Anonymised fixtures live in `fixtures/anonymised/`.

Before any real email becomes a test fixture:

1. Replace sender and recipient addresses with `sender@example.test` style values.
2. Replace personal names, phone numbers, and any application IDs.
3. Keep structure, HTML markup, encoding quirks and Korean text intact — these are exactly
   what the parser must handle.
4. Record the transformation in the fixture header comment.

## Incident handling

Any credential exposure is treated as an incident: **revoke first**, then rotate, then write
an entry in `docs/incidents/`. Rotation procedures belong in `OPS-001` §6.

Revocation targets, by secret:

| Secret | Revoke by |
|---|---|
| Gmail refresh token | Google Account → Security → Third-party access → remove the app |
| PostgreSQL password | `ALTER ROLE ... PASSWORD`, then update the k8s Secret and restart |
| ghcr.io pull token | GitHub → Settings → Developer settings → revoke the token |
| age private key (from B16) | Re-encrypt every SOPS file with a new key; the old key can decrypt any copy already pulled, so treat every secret it protected as exposed |
| healthchecks.io ping URL | Regenerate the check's URL |
| AWS IAM access key | IAM → deactivate, then delete |
