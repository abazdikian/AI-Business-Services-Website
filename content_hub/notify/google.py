"""Auth shim — re-use Gmail + Drive token/credentials already set up
in social-pipeline/, extended with the Slides scope. If the on-disk token
is missing the Slides scope (first run), triggers a one-time browser
re-consent.
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import PROJECT_ROOT

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/calendar.readonly",
]

SOCIAL_DIR = PROJECT_ROOT / "social-pipeline"
TOKEN_FILE = SOCIAL_DIR / "token.json"
CREDS_FILE = SOCIAL_DIR / "credentials.json"


def _has_required_scopes(creds: Credentials) -> bool:
    granted = set(creds.scopes or [])
    return all(s in granted for s in SCOPES)


def _creds() -> Credentials:
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token and _has_required_scopes(creds):
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        except Exception:
            creds = None

    if not creds or not creds.valid or not _has_required_scopes(creds):
        if not CREDS_FILE.exists():
            raise FileNotFoundError(
                f"{CREDS_FILE} missing — can't run OAuth flow without client secrets."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def gmail_service():
    return build("gmail", "v1", credentials=_creds())


def drive_service():
    return build("drive", "v3", credentials=_creds())


def slides_service():
    return build("slides", "v1", credentials=_creds())


def calendar_service():
    return build("calendar", "v3", credentials=_creds())
