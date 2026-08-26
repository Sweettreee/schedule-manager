"""B1 unit tests.

ADR-010 calls B1 exploratory and asks only for a smoke run, but `CLAUDE.md` rule 4 forbids
calling work done without tests. These are the assertions that are worth making without a
network: the scope cannot widen unnoticed, the token cannot land outside the gitignored
directory, and a grant that would die in seven days is rejected rather than stored.

No test here touches the Gmail API.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from schedule_manager import config
from schedule_manager.gmail import auth


def test_scope_is_read_only_and_nothing_else() -> None:
    assert config.GMAIL_SCOPES == ("https://www.googleapis.com/auth/gmail.readonly",)


def test_no_scope_grants_write_access() -> None:
    assert all(scope.endswith(".readonly") for scope in config.GMAIL_SCOPES)


def test_token_stays_inside_the_gitignored_secrets_directory() -> None:
    assert config.TOKEN_PATH.parent == config.SECRETS_DIR
    assert config.SECRETS_DIR.name == ".secrets"
    assert config.CLIENT_SECRET_PATH.parent == config.SECRETS_DIR


def test_stale_credentials_without_a_refresh_token_are_rejected(monkeypatch) -> None:
    """The ADR-007 trap: a Testing-status grant expires after seven days, silently."""
    stale = SimpleNamespace(valid=False, refresh_token=None)
    monkeypatch.setattr(auth, "_load_saved", lambda path: stale)

    with pytest.raises(auth.MissingRefreshTokenError):
        auth.get_credentials()


def test_valid_stored_credentials_are_reused_without_reauthorising(monkeypatch) -> None:
    """Acceptance criterion 1: running on a later day must not prompt again."""
    stored = SimpleNamespace(valid=True, refresh_token="a-refresh-token")
    monkeypatch.setattr(auth, "_load_saved", lambda path: stored)

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("the consent flow must not run when a valid token is stored")

    monkeypatch.setattr(auth, "_authorise", fail)

    assert auth.get_credentials() is stored


def test_expired_credentials_are_refreshed_and_rewritten(monkeypatch, tmp_path) -> None:
    refreshed: list[str] = []
    token_path = tmp_path / "gmail_token.json"

    expired = SimpleNamespace(
        valid=False,
        refresh_token="a-refresh-token",
        refresh=lambda request: refreshed.append("refreshed"),
        to_json=lambda: '{"token": "x"}',
    )
    monkeypatch.setattr(auth, "_load_saved", lambda path: expired)
    monkeypatch.setattr(auth, "Request", lambda: None)

    assert auth.get_credentials(token_path=token_path) is expired
    assert refreshed == ["refreshed"]
    assert token_path.exists()
