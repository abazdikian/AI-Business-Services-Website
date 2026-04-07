"""
Upload graphics to Google Drive, organized by week.
"""

import os
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from gmail_auth import get_drive_service

DRIVE_PARENT_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")


def _find_or_create_folder(service, name, parent_id=None):
    """Find a folder by name under parent, or create it."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  [Drive] Created folder: {name}")
    return folder["id"]


def _upload_file(service, file_path, folder_id):
    """Upload a single file to a Drive folder."""
    filename = os.path.basename(file_path)
    mime_types = {".png": "image/png", ".pdf": "application/pdf"}
    ext = os.path.splitext(filename)[1].lower()
    mime_type = mime_types.get(ext, "application/octet-stream")
    metadata = {"name": filename, "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type)
    uploaded = service.files().create(
        body=metadata, media_body=media, fields="id, webViewLink"
    ).execute()
    print(f"  [Drive] Uploaded: {filename}")
    return uploaded.get("webViewLink", "")


def upload_post_graphics(post_dir, post_slug, week_label=None):
    """Upload all graphics in a post directory to Google Drive. Returns folder URL."""
    if not DRIVE_PARENT_FOLDER_ID:
        print("[WARN] DRIVE_FOLDER_ID not set — skipping Drive upload")
        return None
    service = get_drive_service()
    if not week_label:
        week_label = f"Week of {datetime.now().strftime('%Y-%m-%d')}"
    week_folder_id = _find_or_create_folder(service, week_label, DRIVE_PARENT_FOLDER_ID)
    post_folder_id = _find_or_create_folder(service, post_slug, week_folder_id)
    for filename in sorted(os.listdir(post_dir)):
        filepath = os.path.join(post_dir, filename)
        if os.path.isfile(filepath) and not filename.startswith("."):
            _upload_file(service, filepath, post_folder_id)
    return f"https://drive.google.com/drive/folders/{post_folder_id}"


if __name__ == "__main__":
    print("Google Drive uploader ready.")
    if DRIVE_PARENT_FOLDER_ID:
        service = get_drive_service()
        print(f"Authenticated. Parent folder: {DRIVE_PARENT_FOLDER_ID}")
    else:
        print("Set DRIVE_FOLDER_ID env var to enable uploads.")
