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

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from schedule_manager.config import CLIENT_SECRET_PATH, GMAIL_SCOPES, TOKEN_PATH

logger = logging.getLogger(__name__)


class MissingRefreshTokenError(RuntimeError):
    """Google returned credentials that cannot be renewed without a human.

    ADR-007: an OAuth app left in "Testing" publishing status issues refresh tokens that
    expire after seven days. The collector then stops on day eight while the dashboard keeps
    serving the previous data — the silent failure `PRD-000` calls worse than the original
    problem. So a missing refresh token is an error here, never a warning.
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
            "Google returned credentials without a refresh token, so this grant dies in "
            "seven days (ADR-007). Check that the OAuth consent screen is published "
            "'In production' rather than left in 'Testing', then delete "
            f"{TOKEN_PATH} and authorise again."
        )

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
        creds.refresh(Request())
        _write_token(creds, token_path)
        return creds

    logger.info("no stored token; starting the browser consent flow")
    creds = _authorise(client_secret_path)
    _require_refresh_token(creds)
    _write_token(creds, token_path)
    return creds