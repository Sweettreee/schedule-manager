# ADR-026 — uv as the Python Toolchain, with a Non-Dot Environment Directory

**Status**: Accepted
**Date**: 2026-08-26
**Related**: ADR-004 (control over convenience), ADR-006 (application stack), ADR-010 (testing
strategy), ADR-011 (container registry), WORKFLOW.md §Testing, `api/README.md`

## Context

The owner decided on 2026-08-26 that this project is operated with **uv**. Until now `api/`
carried the default Python workflow: `python3 -m venv venv` followed by
`pip install -e '.[dev]'`, recorded in `api/README.md`. No environment had actually been created
yet and `api/` was still untracked, so the switch costs nothing today and would cost a rewrite of
every command in every document later.

Two facts constrain how uv is adopted here.

**1. There is no lockfile today.** `pip install -e '.[dev]'` resolves dependencies afresh on every
machine and every run. `pyproject.toml` pins only floors (`google-api-python-client>=2.150`), so
the collector that CI tests and the collector that runs on the node are not guaranteed to be the
same set of packages. For a project whose second goal is a Cloud/DevOps/SRE career (`CLAUDE.md`
§1), an unreproducible build is the wrong default to be teaching itself.

**2. uv's default environment directory breaks this repository.** The repository lives under an
iCloud-synced `Desktop` folder. macOS applies the `UF_HIDDEN` flag to dot-prefixed directories
there, and CPython's `site` module skips `.pth` files that carry it — which is exactly where an
editable install records the path to `src/`. `api/README.md` already documents this trap and the
symptom it produces: `ModuleNotFoundError: No module named 'schedule_manager'` while `pytest`
still passes, because pytest sets `pythonpath` itself. uv defaults to `.venv`.

This was re-verified on 2026-08-26 rather than taken on trust, and all three steps reproduced:

- `uv venv .venv` produced a `_virtualenv.pth` that was **already flagged `hidden` at creation**,
  while the same file inside `venv/` was not.
- `chflags hidden` on the editable `.pth` reproduced the `ModuleNotFoundError` exactly.
- After `chflags -R nohidden .venv && rm -rf .venv`, an empty `.venv/lib/python3.13/` skeleton
  **reappeared minutes later, flagged `hidden`**. The flag is reapplied, so clearing it by hand
  is not a fix.

uv accepts the environment directory only through the `UV_PROJECT_ENVIRONMENT` environment
variable. There is no `pyproject.toml` key for it, so the setting has to be supplied by something
outside the project file on every invocation.

## Decision

**uv is the Python toolchain for this project** — environments, resolution, locking and command
execution. `uv.lock` is committed. The interpreter is pinned to **3.13.11** in
`api/.python-version`. The project environment stays at **`api/venv`**, never `.venv`, and
`UV_PROJECT_ENVIRONMENT=venv` is exported by **`api/Makefile`**, which is the entry point for
every Python command: `make sync`, `make test`, `make lint`, `make fmt`, `make run`.

Dev dependencies move from `[project.optional-dependencies]` to PEP 735 `[dependency-groups]`,
which `uv sync` installs by default.

## Rationale

uv gives the lockfile the project did not have, and it gives it without adding a service, a
daemon or a hosted anything — `ADR-004` is not engaged, because nothing is hidden that the owner
wanted to learn. Resolution and installation stay visible in `uv.lock`, which is a plain readable
file in the repository.

Pinning 3.13.11 rather than leaving the interpreter to whatever `python3` resolves to matters
because the system `python3` on this machine is **3.14.2**, while `requires-python` is `>=3.11`.
Without a pin, local development, CI and the container image can each land on a different minor
version and only discover it through a runtime failure. `requires-python` is deliberately left at
`>=3.11` so the lock still resolves across the supported range; the pin is about which
interpreter this machine uses, not about narrowing what the package supports.

The Makefile is chosen over the two alternatives for supplying `UV_PROJECT_ENVIRONMENT` because it
is the only one that lives in the repository. It is version-controlled, it is identical on any
machine that clones the repo, and it touches no global state. It also gives the guard a place to
live: `make` refuses to run if a `.venv` directory exists, because that means uv was invoked
outside `make` and the environment will work today and fail silently in a week.

## Trade-offs

| Gained | Given up |
|---|---|
| A committed `uv.lock` — reproducible installs across laptop, CI and node | A second manifest to keep current; `uv add`, not hand-edited `[project.dependencies]` |
| Interpreter pinned to one version everywhere | 3.13.11 must be re-pinned deliberately when it ages out |
| Much faster resolve/install than pip | A tool outside the standard library, on its own release cadence |
| One entry point (`make`) that cannot forget the env var | Typing `uv run` directly still creates `.venv`; the guard catches it on the next `make`, not at the moment of the mistake |
| `uv sync` installs the dev group with no extra flag | `pip install '.[dev]'` no longer installs dev deps — the extra is gone |

## Alternatives rejected

**Keep pip + venv.** Rejected: it is what produced the current unlocked state, and the owner has
decided otherwise. Nothing about it was load-bearing.

**Export `UV_PROJECT_ENVIRONMENT=venv` from `~/.zshrc`.** Rejected: it is invisible to the
repository, so a fresh clone silently behaves differently, and it redirects **every** uv project
on the machine to `venv/` — where another repository's `.gitignore` may list only `.venv` and
would then commit an environment. The owner accepted the Makefile's residual risk on the grounds
that this is a single-person project; that argument does not extend to changing a global default
for unrelated repositories.

**Document the export in `api/README.md` and rely on typing it.** Rejected: the failure it guards
against is silent and delayed. The `.pth` is skipped without a warning, and the bug surfaces days
later as a `ModuleNotFoundError` that `pytest` cannot reproduce. This trap has already cost the
owner one debugging session; a README line is not a control.

**Keep `.venv` and clear the flag after each sync.** Rejected on the evidence above: the skeleton
reappeared flagged `hidden` after deletion, so the flag is reapplied by the environment and any
`chflags` step is a race, not a fix.

**Make the project virtual (`[tool.uv] package = false`) to avoid `.pth` entirely.** Rejected:
it removes the editable install, and with it the `schedule-manager` console script that `FR`-level
work and `api/README.md` both use.

## If a managed service was chosen (ADR-004 requirement)

Not applicable. uv is a local CLI. No AWS-managed or hosted service is introduced, and no layer
the owner wanted to learn is hidden — dependency resolution becomes *more* visible than it was
under pip, because the result is written to a readable `uv.lock` in the repository.

## Open questions

- **CI does not exist yet** (`.github/` is absent). When it is created, it must run
  `uv sync --locked` so a stale `uv.lock` fails the build instead of being silently re-resolved.
  Revisit at **B16**, the block that introduces CI/CD (`BLOCKS-001` §7). Until then `WORKFLOW.md`
  §"Definition of Done" reads "tests pass" as `make lint` and `make test` run locally.
- **The container image** should install from `uv.lock` and use the same 3.13.11 base, so the
  node runs what CI tested. Revisit at the infra-lane block that builds the image (`ADR-011`).
- **`quickstart.py` at the repository root** — **closed 2026-08-30. No such file exists**, tracked
  or untracked. B1 answered the question by not keeping it, so there is nothing left to decide.
