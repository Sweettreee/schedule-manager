"""OAuth 2.0 credential handling for the collection mailbox (ADR-007)."""

# auth.py 's role
# Open a browser to display the Google login screen (to receive an authorization code)
# Exchange that code for an access token + refresh token
# When the access token expires, use the refresh token to reissue a new access token
# Save/load the refresh token to/from api/.secrets/gmail_token.json

from __future__ import annotations

import logging
import os
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from schedule_manager.config import CLIENT_SECRET_PATH, GMAIL_SCOPES, TOKEN_PATH

logger = logging.getLogger(__name__)


class MissingRefreshTokenError(RuntimeError):
    """Google issued a grant that cannot be renewed, so it dies within the hour.

    ADR-007: an OAuth app left in "Testing" publishing status issues refresh tokens that
    expire after seven days, and a repeat authorisation without `prompt=consent` returns no
    refresh token at all. Either way the collector eventually stops while the dashboard keeps
    serving the previous data — the silent failure `PRD-000` calls worse than the original
    problem. So this is an error here, never a warning.
    """


class ReauthorisationRequiredError(RuntimeError):
    """A refresh token that used to work is no longer accepted by Google.

    Distinct from `MissingRefreshTokenError`, which is about a grant that was wrong the
    moment it was issued. This one is about a grant that has since died, and the response is
    different: a human has to run the consent flow again (ADR-027, RUNBOOK-001).
    """


def _load_saved(path: Path) -> Credentials | None:
    if not path.exists():
        return None
    return Credentials.from_authorized_user_file(str(path), list(GMAIL_SCOPES))


def _write_token(creds: Credentials, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(path, 0o600)


def _require_refresh_token(creds: Credentials) -> None:
    if not getattr(creds, "refresh_token", None):
        raise MissingRefreshTokenError(
            "Google returned credentials without a refresh token. Without one the grant "
            "cannot be renewed and stops working in about an hour (ADR-007). The usual "
            "causes are an OAuth consent screen still in 'Testing' publishing status, or a "
            "repeat authorisation that did not force the consent screen. Check the "
            "publishing status reads 'In production', then delete "
            f"{TOKEN_PATH} and authorise again."
        )


def _is_invalid_grant(exc: RefreshError) -> bool:
    """Is this a dead grant, or merely a bad day on the network?

    google-auth reports both through `RefreshError` and carries the OAuth error code in the
    exception's arguments rather than in a typed field, so the string is the only
    discriminator available. ADR-027 records this as a known fragility: if Google reworded
    the response, this returns False and a dead grant would be reported as a transient
    failure instead.
    """
    return "invalid_grant" in str(exc).lower()


def _refresh(creds: Credentials) -> None:
    """Renew the access token, turning a dead grant into an actionable error.

    Only `invalid_grant` is converted. Anything else — a timeout, DNS, a 5xx from Google —
    is re-raised untouched, because telling the owner to re-authorise every time the network
    blinks would have them delete a healthy token. That costs more than it looks: Google
    allows 100 refresh tokens per client, and needless re-authorisation silently evicts the
    oldest one (ADR-027).
    """
    try:
        creds.refresh(Request())
    except RefreshError as exc:
        if not _is_invalid_grant(exc):
            raise
        raise ReauthorisationRequiredError(
            "Google no longer accepts the stored refresh token, so the collector cannot "
            "renew its access. This happens when the mailbox password is changed, when the "
            "grant is revoked, after six months of disuse, or when this client's "
            "100-refresh-token limit evicts the oldest one. Follow "
            "docs/RUNBOOK-001-gmail-reauthorisation.md to re-authorise."
        ) from exc


def _authorise(client_secret_path: Path) -> Credentials:
    if not client_secret_path.exists():
        raise FileNotFoundError(
            f"OAuth client secret not found at {client_secret_path}. Download the desktop "
            "client credentials from the Google Cloud Console and save them there. The "
            "directory is gitignored; the file must never be committed."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), list(GMAIL_SCOPES))
    # access_type=offline is what makes Google issue a refresh token at all; prompt=consent
    # forces a fresh one even when this account has already granted the app before.
    return flow.run_local_server(port=0, access_type="offline", prompt="consent")


def get_credentials(
    *,
    token_path: Path = TOKEN_PATH,
    client_secret_path: Path = CLIENT_SECRET_PATH,
) -> Credentials:
    """Return usable credentials, refreshing or authorising as needed.

    The stored refresh token is what lets this run unattended on later days, which is B1's
    first acceptance criterion.
    """
    creds = _load_saved(token_path)

    if creds is not None:
        if creds.valid:
            return creds
        _require_refresh_token(creds)
        logger.info("stored access token is stale; refreshing")
        _refresh(creds)
        _write_token(creds, token_path)
        return creds

    logger.info("no stored token; starting the browser consent flow")
    creds = _authorise(client_secret_path)
    _require_refresh_token(creds)
    _write_token(creds, token_path)
    return creds
