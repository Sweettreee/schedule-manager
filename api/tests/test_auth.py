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
from google.auth.exceptions import RefreshError

from schedule_manager import cli, config
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


def _refresh_raising(exc: Exception):
    """A credential whose refresh fails the way google-auth fails."""

    def _refresh(request: object) -> None:
        raise exc

    return _refresh


def test_a_dead_grant_is_reported_as_needing_reauthorisation(monkeypatch, tmp_path) -> None:
    """ADR-027: `invalid_grant` means the stored token is finished and a human is needed."""
    token_path = tmp_path / "gmail_token.json"
    dead = SimpleNamespace(
        valid=False,
        refresh_token="a-refresh-token",
        refresh=_refresh_raising(
            RefreshError("('invalid_grant: Token has been expired or revoked.', {...})")
        ),
    )
    monkeypatch.setattr(auth, "_load_saved", lambda path: dead)
    monkeypatch.setattr(auth, "Request", lambda: None)

    with pytest.raises(auth.ReauthorisationRequiredError):
        auth.get_credentials(token_path=token_path)

    assert not token_path.exists(), "a failed refresh must not overwrite the stored token"


def test_a_transient_refresh_failure_is_not_reported_as_reauthorisation(
    monkeypatch, tmp_path
) -> None:
    """The other half of ADR-027, and the more expensive one to get wrong.

    Telling the owner to re-authorise after a network blip would have them delete a healthy
    token, and needless re-authorisation evicts one of Google's 100 refresh tokens per
    client. So anything that is not `invalid_grant` propagates untouched.
    """
    token_path = tmp_path / "gmail_token.json"
    flaky = SimpleNamespace(
        valid=False,
        refresh_token="a-refresh-token",
        refresh=_refresh_raising(RefreshError("Connection aborted: read timeout")),
    )
    monkeypatch.setattr(auth, "_load_saved", lambda path: flaky)
    monkeypatch.setattr(auth, "Request", lambda: None)

    with pytest.raises(RefreshError):
        auth.get_credentials(token_path=token_path)


def test_cli_reports_reauthorisation_with_its_own_exit_code(monkeypatch, capsys) -> None:
    """A dead grant must exit distinguishably, not as an unhandled traceback."""

    def _raise(limit: int) -> None:
        raise auth.ReauthorisationRequiredError("re-authorise, see RUNBOOK-001")

    monkeypatch.setattr(cli, "list_recent", _raise)

    assert cli.main(["list"]) == 3
    assert "re-authorise" in capsys.readouterr().err
