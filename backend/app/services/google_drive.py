import os
import tempfile
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.core.config import settings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_drive_service():

    credentials = Credentials(
        token=None,
        refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    service = build(
        "drive",
        "v3",
        credentials=credentials,
    )

    return service


def get_or_create_folder( folder_name: str, parent_folder_id: str):

    folder = find_folder(folder_name, parent_folder_id)

    if folder:
        return folder

    return create_folder(folder_name, parent_folder_id)

import base64
import requests


def image_url_to_data_uri(image_url: str | None) -> str | None:
    if not image_url:
        return None

    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "image/png")
        encoded = base64.b64encode(response.content).decode("utf-8")

        return f"data:{content_type};base64,{encoded}"

    except Exception:
        return None


def list_folder_contents(folder_id: str):

    service = get_drive_service()

    response = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id,name,mimeType)",
        ).execute()
    )

    return response.get("files", [])


def upload_or_replace_file( file_path: str, filename: str, parent_folder_id: str, mime_type: str | None = None):
    service = get_drive_service()

    existing = (
        service.files()
        .list(
            q=(
                f"'{parent_folder_id}' in parents "
                f"and name='{filename}' "
                f"and trashed=false"
            ),
            fields="files(id,name)",
        )
        .execute()
        .get("files", [])
    )

    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True,
    )

    if existing:
        file_id = existing[0]["id"]

        uploaded_file = (
            service.files()
            .update(
                fileId=file_id,
                media_body=media,
                fields="id,name,webViewLink,webContentLink",
            )
            .execute()
        )

    else:
        metadata = {
            "name": filename,
            "parents": [parent_folder_id],
        }

        uploaded_file = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,webViewLink,webContentLink",
            )
            .execute()
        )

    # Make the file publicly readable
    try:
        service.permissions().create(
            fileId=uploaded_file["id"],
            body={
                "type": "anyone",
                "role": "reader",
            },
        ).execute()
    except Exception:
        pass

    return uploaded_file


def create_folder(folder_name: str, parent_folder_id: str):

    service = get_drive_service()

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }

    folder = (
        service.files()
        .create(
            body=metadata,
            fields="id,name",
        )
        .execute()
    )

    return folder


def find_folder(folder_name: str, parent_folder_id: str):

    service = get_drive_service()

    response = (
        service.files()
        .list(
            q=(
                f"'{parent_folder_id}' in parents "
                f"and name='{folder_name}' "
                f"and mimeType='application/vnd.google-apps.folder' "
                f"and trashed=false"
            ),
            fields="files(id,name)",
        )
        .execute()
    )

    folders = response.get("files", [])

    return folders[0] if folders else None


def upload_pdf_bytes(
    pdf_bytes: bytes,
    filename: str,
    parent_folder_id: str,
):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name

        return upload_or_replace_file(
            file_path=temp_path,
            filename=filename,
            parent_folder_id=parent_folder_id,
            mime_type="application/pdf",
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
