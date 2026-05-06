"""Content Hub FastAPI app.

Run:  uvicorn content-hub.app:app --port 4000
"""

import json
import threading
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import calendar_view, db
from .config import BASE_DIR, BRAND, CHANNELS
from .fetchers.market_news import market_news_view
from .jobs.create_worker import render_approved

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.globals["BRAND"] = BRAND
templates.env.globals["CHANNELS"] = CHANNELS

app = FastAPI(title="Content Hub")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    weeks = db.list_weeks()
    current = weeks[0]["id"] if weeks else None
    if not current:
        return templates.TemplateResponse(request, "empty.html")
    return RedirectResponse(url=f"/week/{current}")


@app.get("/week/{week_id}", response_class=HTMLResponse)
def week_view(request: Request, week_id: str, channel: str = "linkedin"):
    if channel not in CHANNELS:
        channel = "linkedin"
    weeks = db.list_weeks()
    posts = db.posts_for(week_id, channel)
    pasted = db.get_pasted_urls(week_id, channel)
    job = db.latest_job_for(week_id, channel)
    return templates.TemplateResponse(
        request,
        "week.html",
        {
            "week_id": week_id,
            "channel": channel,
            "weeks": weeks,
            "posts": posts,
            "pasted": pasted,
            "job": job,
        },
    )


@app.get("/week/{week_id}/channel/{channel}", response_class=HTMLResponse)
def channel_fragment(request: Request, week_id: str, channel: str):
    posts = db.posts_for(week_id, channel)
    pasted = db.get_pasted_urls(week_id, channel)
    job = db.latest_job_for(week_id, channel)
    return templates.TemplateResponse(
        request,
        "channel_tab.html",
        {
            "week_id": week_id,
            "channel": channel,
            "posts": posts,
            "pasted": pasted,
            "job": job,
        },
    )


@app.post("/select/{week_id}/{channel}/{post_id}")
def toggle_select(week_id: str, channel: str, post_id: str, selected: str = Form("off")):
    is_selected = selected == "on"
    db.toggle_selection(week_id, channel, post_id, is_selected)
    return Response(status_code=204)


@app.post("/paste/{week_id}/{channel}")
def save_paste(week_id: str, channel: str, urls: str = Form("")):
    db.set_pasted_urls(week_id, channel, urls)
    return Response(status_code=204)


@app.post("/create/{week_id}/{channel}", response_class=HTMLResponse)
def create_batch(request: Request, week_id: str, channel: str):
    selected = db.selected_posts(week_id, channel)
    pasted = [u for u in db.get_pasted_urls(week_id, channel).splitlines() if u.strip()]
    payload = {
        "post_ids": [p["id"] for p in selected],
        "pasted_urls": pasted,
    }
    db.enqueue_job(week_id, channel, payload)
    job = db.latest_job_for(week_id, channel)
    return templates.TemplateResponse(
        request,
        "components/job_status.html",
        {"week_id": week_id, "channel": channel, "job": job},
    )


@app.get("/job_status/{week_id}/{channel}", response_class=HTMLResponse)
def job_status(request: Request, week_id: str, channel: str):
    job = db.latest_job_for(week_id, channel)
    return templates.TemplateResponse(
        request,
        "components/job_status.html",
        {"week_id": week_id, "channel": channel, "job": job},
    )


@app.post("/approve/{job_id}", response_class=HTMLResponse)
def approve_job(request: Request, job_id: int):
    """Approve text drafts — triggers render + Drive upload in background."""
    with db.conn() as c:
        row = c.execute("SELECT week_id, channel, status FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"job {job_id} not found")
    db.mark_job(job_id, "rendering")
    threading.Thread(target=render_approved, args=(job_id,), daemon=True).start()
    return templates.TemplateResponse(
        request,
        "components/job_status.html",
        {"week_id": row["week_id"], "channel": row["channel"], "job": {"id": job_id, "status": "rendering"}},
    )


@app.get("/archive", response_class=HTMLResponse)
def archive(request: Request):
    weeks = db.list_weeks()
    return templates.TemplateResponse(request, "archive.html", {"weeks": weeks})


@app.get("/market-news", response_class=HTMLResponse)
def market_news(request: Request):
    ctx = market_news_view()
    return templates.TemplateResponse(
        request, "market_news.html",
        {"digest": ctx["digest"], "warm_queue": ctx["warm_queue"]},
    )


@app.get("/post-times", response_class=HTMLResponse)
def post_times(request: Request):
    return templates.TemplateResponse(request, "post_times.html", {})


# ── MARKETING CALENDAR ──────────────────────────────────────────────────────

@app.get("/calendar", response_class=HTMLResponse)
def calendar_index(request: Request):
    from datetime import date as _date
    return RedirectResponse(url=f"/calendar/{_date.today().strftime('%Y-%m')}")


@app.get("/calendar/{yyyy_mm}", response_class=HTMLResponse)
def calendar_month(request: Request, yyyy_mm: str):
    if len(yyyy_mm) != 7 or yyyy_mm[4] != "-":
        raise HTTPException(400, "Month must be YYYY-MM")
    ctx = calendar_view.build_month_view(yyyy_mm)
    ctx["months"] = calendar_view.list_visible_months(yyyy_mm)
    ctx["upcoming"] = calendar_view.upcoming_7_days()
    return templates.TemplateResponse(request, "calendar.html", ctx)


@app.post("/calendar/event")
def add_event(
    title: str = Form(...),
    date: str = Form(...),                      # YYYY-MM-DD
    time: str = Form(""),                        # HH:MM, optional
    category: str = Form("custom"),
    url: str = Form(""),
    notes: str = Form(""),
    redirect_to: str = Form("/calendar"),
):
    start_at = f"{date}T{time}:00" if time else date
    db.insert_event(
        title=title.strip(), start_at=start_at, category=category,
        url=url.strip() or None, notes=notes.strip() or None,
    )
    return RedirectResponse(url=redirect_to, status_code=303)


@app.delete("/calendar/event/{event_id}", response_class=HTMLResponse)
def remove_event(request: Request, event_id: int):
    db.delete_event(event_id)
    # Re-render an empty cell so HTMX can swap; the user's reload will refresh fully
    return HTMLResponse("<div class=\"cal-day is-in-month\"><div class=\"cal-day-head\"><span class=\"cal-day-num\"></span></div></div>")


@app.get("/drafts/{job_id}", response_class=HTMLResponse)
def view_drafts(request: Request, job_id: int):
    """Aggregated local view of every artifact produced by a job."""
    with db.conn() as c:
        row = c.execute(
            "SELECT week_id, channel, result_json FROM jobs WHERE id=?",
            (job_id,),
        ).fetchone()
    if not row:
        raise HTTPException(404, f"job {job_id} not found")
    result = json.loads(row["result_json"] or "{}")
    artifacts = result.get("artifacts") or []

    sections: list[dict] = []
    for a in artifacts:
        folder = BASE_DIR / (a.get("local_folder") or "")
        if a.get("kind") == "video":
            filenames = ("description.md", "transcript.md")
        else:
            filenames = ("post.md", "caption.md")
        for fname in filenames:
            p = folder / fname
            if p.exists():
                sections.append({
                    "label": f"{a.get('title') or fname} — {fname}",
                    "body": p.read_text(encoding="utf-8"),
                })

    if not sections:
        raise HTTPException(404, "no local files for this job")

    return templates.TemplateResponse(
        request,
        "drafts.html",
        {
            "job_id": job_id,
            "week_id": row["week_id"],
            "channel": row["channel"],
            "sections": sections,
        },
    )
