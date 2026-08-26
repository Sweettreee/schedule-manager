"""Paths and constants shared by the collector.

The Gmail scope is a module constant on purpose. A scope that widens quietly is a
least-privilege regression, and a value buried inside a call site — or inside a secret — is a
value no test can assert. That is the same lesson `SOURCES-001` §2.1 draws from the LMS
`preset_time` parameter, and it applies here for the same reason.
"""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

# api/src/schedule_manager/config.py -> api/
API_ROOT = Path(__file__).resolve().parents[2]

# Gitignored, both by name and by directory (see .gitignore).
SECRETS_DIR = API_ROOT / ".secrets"
CLIENT_SECRET_PATH = SECRETS_DIR / "client_secret.json"
TOKEN_PATH = SECRETS_DIR / "gmail_token.json"

# ADR-007: least privilege. Reading mail is the whole requirement.
GMAIL_SCOPES: tuple[str, ...] = ("https://www.googleapis.com/auth/gmail.readonly",)

# CLAUDE.md §4: timestamps are stored in UTC and converted to KST only for display.
KST = ZoneInfo("Asia/Seoul")
