"""
Monitor Gmail for replies to the weekly digest email.
"""

import os
import re
import json
import base64
from gmail_auth import get_gmail_service
from config import LAST_THREAD_FILE, PROCESSED_REPLIES_FILE, DIGEST_DATA_DIR


def _load_thread_id():
    try:
        with open(LAST_THREAD_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def _load_processed():
    try:
        with open(PROCESSED_REPLIES_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_processed(processed):
    os.makedirs(DIGEST_DATA_DIR, exist_ok=True)
    with open(PROCESSED_REPLIES_FILE, "w") as f:
        json.dump(list(processed), f)


def _parse_numbers(text):
    """Extract post numbers from reply text."""
    text = re.sub(r'(?i)(items?|posts?|numbers?|picks?)[:\s]*', '', text)
    numbers = [int(n) for n in re.findall(r'\d+', text)]
    return [n for n in numbers if 1 <= n <= 20]


def check_for_reply():
    """Check for new reply to digest thread. Returns 0-based indices or None."""
    thread_id = _load_thread_id()
    if not thread_id:
        print("[Monitor] No thread ID found")
        return None

    processed = _load_processed()
    service = get_gmail_service()

    try:
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        messages = thread.get("messages", [])

        if len(messages) < 2:
            print("[Monitor] No reply yet")
            return None

        for msg in messages[1:]:
            msg_id = msg["id"]
            if msg_id in processed:
                continue

            payload = msg.get("payload", {})
            body_text = ""

            if payload.get("body", {}).get("data"):
                body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
            else:
                for part in payload.get("parts", []):
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                        break

            if not body_text:
                continue

            numbers = _parse_numbers(body_text)
            if numbers:
                processed.add(msg_id)
                _save_processed(processed)
                print(f"[Monitor] Found reply with picks: {numbers}")
                return [n - 1 for n in numbers]
            else:
                print(f"[Monitor] Reply found but no numbers: {body_text[:100]}")
                processed.add(msg_id)
                _save_processed(processed)

    except Exception as e:
        print(f"[Monitor] Error: {e}")

    return None


if __name__ == "__main__":
    result = check_for_reply()
    if result:
        print(f"Selected (0-based): {result}")
    else:
        print("No actionable reply found.")
