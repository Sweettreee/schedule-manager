# api — collector and API

Python service for Schedule Manager. At **B1** it does one thing: print the most recent
messages from the collection mailbox.

## Setup

Prerequisites: [`uv`](https://docs.astral.sh/uv/) and `make`. No system Python is needed — uv
fetches the interpreter pinned in `.python-version` (3.13.11).

1. Put the desktop OAuth client credentials from the Google Cloud Console at
   `api/.secrets/client_secret.json`. The directory is gitignored — **never commit it.**

2. Install:

   ```bash
   cd api
   make sync
   ```

3. Run. The first run opens a browser for consent; later runs reuse the stored refresh token.

   ```bash
   make run
   ```

## Everyday commands

| Command | What it does |
|---|---|
| `make sync` | Create/refresh `venv/` from `uv.lock`, dev group included |
| `make test` | `pytest` |
| `make lint` | `ruff check` + `black --check`, as CI runs them |
| `make fmt` | Apply `ruff --fix` and `black` |
| `make run` | `schedule-manager list --limit 10` |
| `make clean` | Delete the environment and caches |

To add a dependency, use `uv add <package>` (or `uv add --dev <package>`) rather than editing
`pyproject.toml` by hand — it updates `uv.lock` in the same step. Commit both files.

No test calls the Gmail API. Recorded, anonymised fixtures only — see `CLAUDE.md` §3.

## Notes

- **Always go through `make`, never bare `uv run`.** The virtualenv is `venv/`, **not** `.venv/`,
  and uv's default is `.venv/`. Under this iCloud-synced Desktop folder a dot-prefixed directory
  gets the macOS `UF_HIDDEN` flag reapplied to it, and Python's `site` module silently skips
  hidden `.pth` files — which is exactly where an editable install puts its path. The symptom is
  `ModuleNotFoundError: No module named 'schedule_manager'` while `pytest` still passes, because
  pytest sets its own path.

  `Makefile` exports `UV_PROJECT_ENVIRONMENT=venv` for this reason; uv accepts that setting only
  as an environment variable, so it cannot live in `pyproject.toml`. Every target also refuses to
  run while a `.venv` exists. If you hit that guard: `make clean && make sync`. Full reasoning and
  the reproduction in **ADR-026**.

- The scope is `gmail.readonly` and lives in `src/schedule_manager/config.py` as a single
  constant, so a widened scope fails a test rather than passing unnoticed.
- If Google ever returns a grant with no refresh token, the CLI errors out instead of storing
  it. That is the ADR-007 trap: a Testing-status app's token expires after seven days and the
  collector then fails silently.
