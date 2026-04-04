"""
Gmail API Authentication — supports local files or environment variables.

Local: reads credentials.json + token.json from this directory.
Remote: reads GMAIL_CREDENTIALS_JSON + GMAIL_TOKEN_JSON env vars.
"""

import os
import json
import tempfile
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """Return an authenticated Gmail API service instance."""
    creds = None

    # Try env vars first (for remote/scheduled execution)
    token_json_env = os.environ.get("GMAIL_TOKEN_JSON")
    if token_json_env:
        token_data = json.loads(token_json_env)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            if token_json_env:
                print("[AUTH] Token refreshed (env var mode — update GMAIL_TOKEN_JSON with new token)")
            else:
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
        else:
            # Need fresh auth — only works locally
            creds_json_env = os.environ.get("GMAIL_CREDENTIALS_JSON")
            if creds_json_env:
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                tmp.write(creds_json_env)
                tmp.close()
                creds_file = tmp.name
            elif os.path.exists(CREDENTIALS_FILE):
                creds_file = CREDENTIALS_FILE
            else:
                raise FileNotFoundError(
                    f"No credentials found. Set GMAIL_CREDENTIALS_JSON env var "
                    f"or place credentials.json in {BASE_DIR}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

            if not token_json_env:
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
                print(f"[AUTH] Token saved to {TOKEN_FILE}")

    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    print("Authenticating with Gmail API...")
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    print(f"Authenticated as: {profile['emailAddress']}")
    print("Gmail API connection successful!")
