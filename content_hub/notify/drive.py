"""Drive helpers — per-channel folders, per-video subfolders, file upload.

Layout in Drive:
    DRIVE_FOLDER_ID /
      content-hub-drafts /
        <week_id> /
          <channel> /
            <draft-slug>.md           (LI/TT/IG)
            <video-title-slug> /      (YT only — one per video)
              transcript.md
              description.md
              <slides deck>
"""

import logging
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from ..config import DRIVE_FOLDER_ID, DRIVE_ROOT_NAME
from .google import drive_service

log = logging.getLogger(__name__)
FOLDER_MIME = "application/vnd.google-apps.folder"


def _find_or_create_folder(svc, name: str, parent_id: str) -> str:
    safe = name.replace("'", "\\'")
    q = (
        f"name='{safe}' and mimeType='{FOLDER_MIME}' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    hits = svc.files().list(q=q, fields="files(id)").execute().get("files", [])
    if hits:
        return hits[0]["id"]
    body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
    return svc.files().create(body=body, fields="id").execute()["id"]


def channel_folder(week_id: str, channel: str) -> dict | None:
    if not DRIVE_FOLDER_ID:
        log.warning("DRIVE_FOLDER_ID not set — Drive disabled")
        return None
    svc = drive_service()
    root = _find_or_create_folder(svc, DRIVE_ROOT_NAME, DRIVE_FOLDER_ID)
    week_f = _find_or_create_folder(svc, week_id, root)
    chan_f = _find_or_create_folder(svc, channel, week_f)
    return {
        "folder_id": chan_f,
        "folder_url": f"https://drive.google.com/drive/folders/{chan_f}",
    }


def video_folder(week_id: str, channel: str, video_slug: str) -> dict | None:
    parent = channel_folder(week_id, channel)
    if not parent:
        return None
    svc = drive_service()
    vf = _find_or_create_folder(svc, video_slug, parent["folder_id"])
    return {
        "folder_id": vf,
        "folder_url": f"https://drive.google.com/drive/folders/{vf}",
    }


def upload_file(local_path: Path, parent_folder_id: str,
                mimetype: str = "text/markdown") -> dict:
    svc = drive_service()
    media = MediaFileUpload(str(local_path), mimetype=mimetype)
    f = svc.files().create(
        body={"name": local_path.name, "parents": [parent_folder_id]},
        media_body=media,
        fields="id, webViewLink",
    ).execute()
    log.info("Uploaded %s", local_path.name)
    return {"file_id": f["id"], "file_url": f.get("webViewLink")}
