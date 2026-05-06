"""Render-side helpers for the Marketing Calendar — assembles month grids
from the events table, recurring rules JSON, and (later) gcal sync.

No HTTP handling here; consumed by app.py routes.
"""

from __future__ import annotations

import calendar as cal_lib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from . import db
from .config import BASE_DIR

RECURRING_FILE = BASE_DIR / "recurring_events.json"
DEFAULT_TIME_LABEL_FMT = "%-I%P"  # "8pm"


# ── recurring rules loader ──────────────────────────────────────────────────

def load_recurring() -> dict:
    if not RECURRING_FILE.exists():
        return {"rules": [], "daily_post_reminders": {"enabled": False}, "category_colors": {}}
    return json.loads(RECURRING_FILE.read_text())


def _color_for(category: str, override_color: str | None, recurring: dict) -> tuple[str, str]:
    if override_color:
        return override_color, "#FFFFFF"
    palette = recurring.get("category_colors", {})
    swatch = palette.get(category) or palette.get("custom") or {"bg": "#6B5A5F", "fg": "#FFFFFF"}
    return swatch["bg"], swatch["fg"]


# ── time helpers ────────────────────────────────────────────────────────────

def _fmt_time_label(dt: datetime) -> str:
    h = dt.hour
    if h == 0:
        return "12am"
    if h < 12:
        return f"{h}am"
    if h == 12:
        return "12pm"
    return f"{h - 12}pm"


def _parse_iso(s: str) -> datetime:
    """Tolerant ISO parser. Accepts 'YYYY-MM-DD' (date-only) and full ISO datetimes."""
    if len(s) == 10:
        return datetime.fromisoformat(s)
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.fromisoformat(s.split("+")[0].split("Z")[0])


# ── month layout ────────────────────────────────────────────────────────────

def _month_bounds(yyyy_mm: str) -> tuple[date, date]:
    y, m = (int(x) for x in yyyy_mm.split("-"))
    first = date(y, m, 1)
    last_day = cal_lib.monthrange(y, m)[1]
    last = date(y, m, last_day)
    return first, last


def _month_grid_dates(first: date, last: date) -> list[list[date]]:
    """Return a list of week-rows (each = 7 dates), starting Monday, padded with prior/next month."""
    start = first - timedelta(days=first.weekday())  # back to Monday
    end_padding = (6 - last.weekday()) % 7
    end = last + timedelta(days=end_padding)
    weeks: list[list[date]] = []
    cur = start
    while cur <= end:
        week = [cur + timedelta(days=i) for i in range(7)]
        weeks.append(week)
        cur += timedelta(days=7)
    return weeks


# ── event compilation per day ───────────────────────────────────────────────

def _materialize_recurring_for_range(first: date, last: date, recurring: dict) -> dict[date, list[dict]]:
    """Expand recurring rules into per-day event lists for the visible window."""
    out: dict[date, list[dict]] = {}
    rules = recurring.get("rules", [])
    daily = recurring.get("daily_post_reminders", {})

    cur = first
    while cur <= last:
        weekday = cur.weekday()
        bucket: list[dict] = []

        for r in rules:
            if r.get("weekday") == weekday:
                hh, mm = (int(x) for x in r.get("time", "09:00").split(":"))
                bg, fg = _color_for(r.get("category", "content"), r.get("color"), recurring)
                bucket.append({
                    "id": f"recurring-{r['id']}-{cur.isoformat()}",
                    "title": r["title"],
                    "time_label": _fmt_time_label(datetime(cur.year, cur.month, cur.day, hh, mm)),
                    "color_bg": bg, "color_fg": fg,
                    "source": "recurring",
                    "url": r.get("url"),
                    "notes": r.get("notes", ""),
                    "_sort": (hh, mm),
                })

        if daily.get("enabled"):
            for ch_name, ch_cfg in (daily.get("channels") or {}).items():
                if weekday in ch_cfg.get("weekdays", []):
                    hh, mm = (int(x) for x in ch_cfg.get("time", "12:00").split(":"))
                    bg, fg = _color_for("content", None, recurring)
                    bucket.append({
                        "id": f"daily-{ch_name}-{cur.isoformat()}",
                        "title": f"{ch_cfg.get('label', 'Post')} ({ch_name})",
                        "time_label": _fmt_time_label(datetime(cur.year, cur.month, cur.day, hh, mm)),
                        "color_bg": "#EFE8DE", "color_fg": "#5E141D",
                        "source": "recurring",
                        "url": None,
                        "notes": f"Daily reminder · peak time per /post-times",
                        "_sort": (hh, mm),
                    })

        if bucket:
            out[cur] = bucket
        cur += timedelta(days=1)
    return out


def _events_to_chips(events: list[dict], recurring: dict) -> dict[date, list[dict]]:
    """Convert raw events table rows into per-day chip dicts."""
    out: dict[date, list[dict]] = {}
    for ev in events:
        try:
            dt = _parse_iso(ev["start_at"])
        except Exception:
            continue
        d = dt.date()
        bg, fg = _color_for(ev.get("category", "custom"), ev.get("color"), recurring)
        time_label = _fmt_time_label(dt) if dt.time() != datetime.min.time() else None
        chip = {
            "id": ev["id"],
            "title": ev["title"],
            "time_label": time_label,
            "color_bg": bg, "color_fg": fg,
            "source": ev.get("source", "manual"),
            "url": ev.get("url"),
            "notes": ev.get("notes", ""),
            "_sort": (dt.hour, dt.minute),
        }
        out.setdefault(d, []).append(chip)
    return out


def build_month_view(yyyy_mm: str, today: date | None = None) -> dict:
    """Returns the full template context for a single month tab."""
    today = today or date.today()
    first, last = _month_bounds(yyyy_mm)
    weeks = _month_grid_dates(first, last)
    visible_start = weeks[0][0]
    visible_end = weeks[-1][-1]

    recurring = load_recurring()
    rec_chips = _materialize_recurring_for_range(visible_start, visible_end, recurring)

    raw_events = db.events_in_range(visible_start.isoformat(), (visible_end + timedelta(days=1)).isoformat())
    ev_chips = _events_to_chips(raw_events, recurring)

    # Merge recurring + concrete events per day; sort within day by time
    days_grid: list[list[dict]] = []
    for week in weeks:
        row = []
        for d in week:
            chips = sorted((rec_chips.get(d, []) + ev_chips.get(d, [])), key=lambda c: c.get("_sort", (0, 0)))
            row.append({
                "num": d.day,
                "date": d.isoformat(),
                "in_month": (first <= d <= last),
                "is_today": (d == today),
                "is_weekend": d.weekday() >= 5,
                "events": chips,
            })
        days_grid.append(row)

    # Event count for tab badge — concrete + recurring
    event_count = sum(len(rec_chips.get(d, [])) + len(ev_chips.get(d, [])) for w in weeks for d in w if first <= d <= last)

    return {
        "current_month": yyyy_mm,
        "current_label": first.strftime("%B %Y"),
        "weeks": days_grid,
        "event_count": event_count,
        "categories": recurring.get("category_colors", {}),
    }


def list_visible_months(yyyy_mm: str) -> list[dict]:
    """Build the 2-tab list: current month + next month, regardless of which is requested."""
    today = date.today()
    current = today.strftime("%Y-%m")
    y, m = (int(x) for x in current.split("-"))
    nm_y, nm_m = (y + 1, 1) if m == 12 else (y, m + 1)
    next_id = f"{nm_y:04d}-{nm_m:02d}"

    out = []
    for mid in (current, next_id):
        view = build_month_view(mid, today)
        out.append({
            "id": mid,
            "label": datetime.strptime(mid + "-01", "%Y-%m-%d").strftime("%B"),
            "event_count": view["event_count"],
        })
    return out


def upcoming_7_days(today: date | None = None) -> list[dict]:
    """Flat list of the next 7 days' events (concrete + recurring), for the side panel."""
    today = today or date.today()
    end = today + timedelta(days=7)
    recurring = load_recurring()
    rec = _materialize_recurring_for_range(today, end, recurring)
    raw = db.events_in_range(today.isoformat(), (end + timedelta(days=1)).isoformat())
    ev = _events_to_chips(raw, recurring)

    out: list[dict] = []
    for offset in range(8):
        d = today + timedelta(days=offset)
        all_chips = sorted((rec.get(d, []) + ev.get(d, [])), key=lambda c: c.get("_sort", (0, 0)))
        for c in all_chips:
            out.append({
                "date_label": d.strftime("%a %b ") + str(d.day),
                "title": c["title"],
                "color_bg": c["color_bg"],
                "color_fg": c["color_fg"],
            })
    return out[:14]  # cap at ~2 weeks worth of items
