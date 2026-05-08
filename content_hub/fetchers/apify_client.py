"""Thin Apify REST wrapper — runs an actor sync and returns dataset items."""

import logging
import time
from typing import Any

import httpx

from ..config import APIFY_TOKEN

log = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"


def run_actor(actor_id: str, input_payload: dict, timeout_secs: int = 300) -> list[dict]:
    """Run an Apify actor synchronously and return its dataset items.

    actor_id is the store slug, e.g. "clockworks/tiktok-scraper".
    """
    if not APIFY_TOKEN:
        log.warning("APIFY_TOKEN not set — returning empty list for %s", actor_id)
        return []

    safe_id = actor_id.replace("/", "~")
    url = f"{APIFY_BASE}/acts/{safe_id}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN, "timeout": timeout_secs}

    try:
        with httpx.Client(timeout=timeout_secs + 30) as client:
            r = client.post(url, params=params, json=input_payload)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        log.error("Apify actor %s failed: %s", actor_id, e)
        return []


def retry_run(actor_id: str, input_payload: dict, attempts: int = 2) -> list[dict]:
    for i in range(attempts):
        items = run_actor(actor_id, input_payload)
        if items:
            return items
        if i < attempts - 1:
            time.sleep(5)
    return []


def safe(d: dict, *keys: str, default: Any = None) -> Any:
    """Walk nested dict keys safely."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur if cur is not None else default
