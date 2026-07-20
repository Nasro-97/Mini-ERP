from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

BASE_DIR = Path(__file__).resolve().parents[2]
CLIENT_SECRET_FILE = BASE_DIR / "credentials" / "oauth-client.json"

flow = InstalledAppFlow.from_client_secrets_file(
    CLIENT_SECRET_FILE,
    scopes=SCOPES,
)

creds = flow.run_local_server(port=0)

print("Refresh Token:")
print(creds.refresh_token)

print("\nAccess Token:")
print(creds.token)

