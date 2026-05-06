"""Render 4 branded outcome-illustration PNGs for the 3-Workflow Starter Kit PDF.

These are NOT screenshots of Claude's UI. They are stylized illustrations of
the OUTPUT shape (a triaged inbox table, a project sidebar mock, etc.) in
Alice's brand. The print captions say "What the output looks like" so we
don't claim they're product captures.

Output → Brand Assets/lead-magnet-screenshots/
"""

from __future__ import annotations

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "Brand Assets" / "lead-magnet-screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SHARED_CSS = """
<style>
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Nunito','Helvetica Neue',Arial,sans-serif;background:#FDFBF5;padding:40px;color:#2B1A1F}
  .frame{max-width:1080px;margin:0 auto;background:#fff;border-radius:18px;border:1px solid #EFE8E3;box-shadow:0 24px 50px -22px rgba(122,21,48,.18);overflow:hidden}
  .frame-bar{display:flex;align-items:center;gap:8px;padding:14px 18px;background:#F7F3EE;border-bottom:1px solid #EFE8E3}
  .frame-dot{width:10px;height:10px;border-radius:50%;background:#D9CFC4}
  .frame-dot.r{background:#E07673}.frame-dot.y{background:#E6C472}.frame-dot.g{background:#7A9E87}
  .frame-title{margin-left:14px;font-size:12px;color:#6B5A5F;font-weight:600;letter-spacing:.04em}
  .frame-body{padding:28px 32px}
  .h{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:22px;color:#2B1A1F;margin-bottom:14px;letter-spacing:-.015em}
  .sub{font-size:13px;color:#6B5A5F;margin-bottom:18px}
  table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
  th{text-align:left;padding:11px 12px;background:linear-gradient(135deg,rgba(193,53,88,.06),rgba(212,168,74,.10));color:#7A1530;font-weight:800;letter-spacing:.06em;text-transform:uppercase;font-size:10px;border-bottom:1.5px solid #EFE8E3}
  td{padding:13px 12px;border-bottom:1px solid #EFE8E3;vertical-align:top}
  tr:last-child td{border-bottom:none}
  .pill{display:inline-block;font-size:9px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;padding:3px 8px;border-radius:999px}
  .pill-reply{background:rgba(122,21,48,.12);color:#7A1530}
  .pill-fyi{background:rgba(91,141,184,.18);color:#3a6a91}
  .pill-archive{background:#EFE8E3;color:#6B5A5F}
  .pill-delegate{background:rgba(212,168,74,.22);color:#A87B1F}
  .pill-high{background:#E07673;color:#fff}
  .pill-med{background:rgba(230,196,114,.45);color:#7A1530}
  .pill-low{background:#EFE8E3;color:#8B7D81}
  .reply{color:#2B1A1F;font-style:italic;line-height:1.45}
  .summary{margin-top:18px;padding:14px 18px;background:linear-gradient(135deg,rgba(230,196,114,.18),rgba(193,53,88,.08));border-radius:10px;border:1px solid #E6C472;font-size:13px;color:#2B1A1F}
  .summary strong{color:#7A1530}
</style>
"""

# ── 1. INBOX TRIAGE OUTPUT ──
INBOX = SHARED_CSS + """
<div class="frame">
  <div class="frame-bar">
    <span class="frame-dot r"></span><span class="frame-dot y"></span><span class="frame-dot g"></span>
    <span class="frame-title">claude.ai · The Inbox Triage Workflow · output</span>
  </div>
  <div class="frame-body">
    <h2 class="h">Inbox triaged · 8 emails · 30 seconds</h2>
    <table>
      <thead><tr><th>#</th><th>From</th><th>Subject</th><th>Class</th><th>Urg.</th><th>Suggested reply</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Sarah · client</td><td>⚠ proposal q's before Fri</td><td><span class="pill pill-reply">Reply</span></td><td><span class="pill pill-high">High</span></td><td class="reply">"Sarah, sending revised scope by Thu EOD. Two questions on timeline coming separately."</td></tr>
        <tr><td>2</td><td>Stripe</td><td>Payment received · invoice #2104</td><td><span class="pill pill-archive">Archive</span></td><td><span class="pill pill-low">Low</span></td><td>—</td></tr>
        <tr><td>3</td><td>Mark · supplier</td><td>April invoice attached</td><td><span class="pill pill-delegate">Delegate</span></td><td><span class="pill pill-med">Med</span></td><td class="reply">Forward to bookkeeper. Use Workflow 04 (Invoice Killer).</td></tr>
        <tr><td>4</td><td>LinkedIn</td><td>5 new connection requests</td><td><span class="pill pill-fyi">FYI</span></td><td><span class="pill pill-low">Low</span></td><td>—</td></tr>
        <tr><td>5</td><td>Jen · prospect</td><td>Discovery call follow-up</td><td><span class="pill pill-reply">Reply</span></td><td><span class="pill pill-high">High</span></td><td class="reply">"Jen, great chat. Calendar link below for next Tue or Thu — 30 min works."</td></tr>
        <tr><td>6</td><td>Substack</td><td>Newsletter scheduled</td><td><span class="pill pill-archive">Archive</span></td><td><span class="pill pill-low">Low</span></td><td>—</td></tr>
        <tr><td>7</td><td>Amir · partner</td><td>Webinar promo swap</td><td><span class="pill pill-reply">Reply</span></td><td><span class="pill pill-med">Med</span></td><td class="reply">"Amir, yes to swap. Send your blurb + dates and I'll mirror."</td></tr>
        <tr><td>8</td><td>Calendly</td><td>New booking · Mon 3pm</td><td><span class="pill pill-fyi">FYI</span></td><td><span class="pill pill-med">Med</span></td><td>Auto-confirmed. Send pre-call note.</td></tr>
      </tbody>
    </table>
    <div class="summary"><strong>3 to reply to today · 2 to skim · 3 to archive.</strong> ≈ 30 seconds vs 18 min reading them all manually.</div>
  </div>
</div>
"""

# ── 2. PROJECT SIDEBAR ──
PROJECT = SHARED_CSS + """
<style>
  .project-grid{display:grid;grid-template-columns:280px 1fr;gap:24px}
  .sidebar{background:#F7F3EE;border-radius:14px;padding:22px;border:1px solid #EFE8E3}
  .side-h{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:16px;margin-bottom:6px;color:#2B1A1F}
  .side-tag{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#A87B1F;font-weight:800;margin-bottom:18px}
  .side-section-h{font-size:9px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#6B5A5F;margin:18px 0 8px}
  .file-row{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:#fff;margin-bottom:5px;font-size:12px;color:#2B1A1F;border:1px solid #EFE8E3}
  .file-icon{width:18px;height:18px;border-radius:4px;background:linear-gradient(135deg,#7A1530,#C13558);color:#fff;font-size:9px;font-weight:800;display:inline-flex;align-items:center;justify-content:center}
  .panel{padding:8px 4px}
  .panel-h{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:18px;color:#2B1A1F;margin-bottom:10px}
  .instructions{background:#FFFDF6;border-left:3px solid #D4A84A;border-radius:0 10px 10px 0;padding:14px 16px;font-size:12px;line-height:1.55;color:#2B1A1F;margin-bottom:14px}
  .instructions code{font-family:'JetBrains Mono','Menlo',monospace;font-size:11px;background:#EFE8E3;padding:1px 5px;border-radius:3px}
  .new-chat{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:999px;background:linear-gradient(135deg,#7A1530,#C13558,#E6C472);color:#fff;font-size:12px;font-weight:700;margin-top:6px}
</style>
<div class="frame">
  <div class="frame-bar">
    <span class="frame-dot r"></span><span class="frame-dot y"></span><span class="frame-dot g"></span>
    <span class="frame-title">claude.ai · Projects · The SOP-to-AI-Trainer setup</span>
  </div>
  <div class="frame-body">
    <h2 class="h">Your business. Trained into a Project. Used forever.</h2>
    <div class="project-grid">
      <div class="sidebar">
        <div class="side-h">Stafford Bakery · Knowledge Base</div>
        <div class="side-tag">Project · 6 files</div>
        <div class="side-section-h">Project files</div>
        <div class="file-row"><span class="file-icon">P</span> Brand voice guide.pdf</div>
        <div class="file-row"><span class="file-icon">P</span> Customer onboarding SOP.pdf</div>
        <div class="file-row"><span class="file-icon">P</span> Pricing &amp; offer matrix.pdf</div>
        <div class="file-row"><span class="file-icon">P</span> Top 5 best emails (samples).pdf</div>
        <div class="file-row"><span class="file-icon">P</span> Refund &amp; complaint script.pdf</div>
        <div class="file-row"><span class="file-icon">P</span> What we never do.txt</div>
        <div class="side-section-h">Custom instructions</div>
        <div style="font-size:11px;color:#6B5A5F;line-height:1.5">"You are my AI assistant for Stafford Bakery. Match my brand voice. Use docs as truth…"</div>
      </div>
      <div class="panel">
        <div class="panel-h">Why this changes everything</div>
        <div class="instructions">Every chat in this project automatically pulls from the 6 files in the sidebar. Type <code>"draft a follow-up to Tuesday's wholesale lead"</code> and Claude already knows your tone, your pricing, and your offer matrix. No more re-pasting context.</div>
        <div class="instructions">When a new customer asks about returns, type <code>"reply to this email about a wedding cake refund"</code> and the response uses your refund script verbatim.</div>
        <span class="new-chat">+ Start chat in this project</span>
      </div>
    </div>
  </div>
</div>
"""

# ── 3. MARKETING LOOP OUTPUT ──
MARKETING = SHARED_CSS + """
<style>
  .ml-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  .ml-col-h{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:15px;color:#7A1530;margin-bottom:10px;display:flex;align-items:center;gap:8px}
  .ml-col-h .num{font-size:11px;background:linear-gradient(135deg,#7A1530,#C13558,#E6C472);color:#fff;font-weight:800;padding:3px 10px;border-radius:999px;letter-spacing:.06em}
  .reel-card{background:#fff;border:1px solid #EFE8E3;border-radius:10px;padding:14px 16px;margin-bottom:8px;font-size:12px;line-height:1.5}
  .reel-card .label{font-size:9px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:#A87B1F;margin-bottom:4px}
  .reel-card .hook{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:13px;color:#2B1A1F;margin-bottom:6px}
  .reel-card .body{color:#6B5A5F;margin-bottom:6px}
  .reel-card .cta{font-size:10px;color:#7A1530;font-weight:700}
  .news{background:linear-gradient(180deg,#FFFDF6 0%,#fff 100%);border:1px solid #E6C472;border-radius:12px;padding:18px}
  .news .subj{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:15px;color:#2B1A1F;margin-bottom:6px}
  .news .meta{font-size:10px;color:#A87B1F;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px}
  .news p{font-size:12px;color:#2B1A1F;line-height:1.55;margin-bottom:9px}
  .news .lnk{color:#7A1530;font-weight:700}
</style>
<div class="frame">
  <div class="frame-bar">
    <span class="frame-dot r"></span><span class="frame-dot y"></span><span class="frame-dot g"></span>
    <span class="frame-title">claude.ai · The Weekly Marketing Loop · output</span>
  </div>
  <div class="frame-body">
    <h2 class="h">5 reel scripts + 1 newsletter outline · ≈ 90 seconds.</h2>
    <p class="sub">Topic this week: "How small biz owners use AI for client follow-ups." Pain: scattered, in your head. Offer: the live workshop on June 3.</p>
    <div class="ml-grid">
      <div>
        <div class="ml-col-h"><span class="num">5 REELS</span> Short-form scripts</div>
        <div class="reel-card">
          <div class="label">Reel 01 · Confessional</div>
          <div class="hook">"I forgot to follow up with three clients last month."</div>
          <div class="body">"Here's the one prompt I started using so it stopped happening."</div>
          <div class="cta">CTA: Comment 'FOLLOW' for the prompt.</div>
        </div>
        <div class="reel-card">
          <div class="label">Reel 02 · Contrarian</div>
          <div class="hook">"Stop building a CRM. You don't need one yet."</div>
          <div class="body">"If you're under 30 clients, AI + a Google Doc beats Hubspot."</div>
          <div class="cta">CTA: Save this for the inevitable conversation.</div>
        </div>
        <div class="reel-card">
          <div class="label">Reel 03 · Checklist</div>
          <div class="hook">"3 things AI does better than a human assistant."</div>
          <div class="body">"And one thing it shouldn't touch."</div>
          <div class="cta">CTA: Send to the friend who keeps overhiring.</div>
        </div>
        <div class="reel-card">
          <div class="label">Reel 04 · Story</div>
          <div class="hook">"My client got 12 hours back her first week."</div>
          <div class="body">"Here's exactly what we changed in her business."</div>
          <div class="cta">CTA: Workshop link in bio.</div>
        </div>
        <div class="reel-card">
          <div class="label">Reel 05 · Stat</div>
          <div class="hook">"4 hours a week. That's the average."</div>
          <div class="body">"Of what owners spend on follow-ups they could automate."</div>
          <div class="cta">CTA: Start with this one prompt →</div>
        </div>
      </div>
      <div>
        <div class="ml-col-h"><span class="num">NEWSLETTER</span> Sunday send</div>
        <div class="news">
          <div class="meta">Subject · 47 chars · zero clickbait</div>
          <div class="subj">The follow-ups you forgot last week.</div>
          <div class="meta">Opening line</div>
          <p>"I'll bet you can name three clients you meant to circle back to last week. I can name three of mine too."</p>
          <div class="meta">Body · 3 short paragraphs</div>
          <p>The reason isn't memory or discipline. It's that follow-up lives in your head, where it competes with everything else for the same 15 minutes between meetings…</p>
          <p>Last month I built a 3-prompt loop that catches every follow-up before it slips. It's not a CRM. It's a thing you already have (Claude) plus a doc you already wrote (your offer)…</p>
          <p>If you want to build it on YOUR business with me beside you, I'm running a free 60-minute workshop on June 3.</p>
          <div class="meta">Closing link</div>
          <p>→ <span class="lnk">Save my seat (free) →</span></p>
        </div>
      </div>
    </div>
  </div>
</div>
"""

# ── 4. INVOICE CSV OUTPUT ──
INVOICE = SHARED_CSS + """
<style>
  .csv{font-family:'JetBrains Mono','Menlo',monospace;font-size:11px;line-height:1.7;background:#1F1A1B;color:#F2EBE0;padding:18px 22px;border-radius:12px;overflow-x:hidden}
  .csv .h{color:#E6C472;font-weight:800}
  .csv .row{color:#F2EBE0}
  .csv .flag{color:#E07673;font-style:italic}
  .csv-label{font-size:10px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:#A87B1F;margin-bottom:8px}
  .meta-strip{display:flex;gap:18px;margin-top:14px;font-size:11px;color:#6B5A5F}
  .meta-strip strong{color:#7A1530;font-weight:800}
</style>
<div class="frame">
  <div class="frame-bar">
    <span class="frame-dot r"></span><span class="frame-dot y"></span><span class="frame-dot g"></span>
    <span class="frame-title">claude.ai · The Invoice Killer · output (paste-ready CSV)</span>
  </div>
  <div class="frame-body">
    <h2 class="h">10 messy OCR'd invoices → 10 clean CSV rows.</h2>
    <p class="sub">Ready to bulk-import into QuickBooks, Xero, Wave, or paste into a spreadsheet. Anything ambiguous gets flagged in the last column.</p>
    <div class="csv-label">▶ Output</div>
    <div class="csv">
      <div class="h">supplier,invoice_no,inv_date,due_date,currency,subtotal,tax,tax_rate,total,line_items,bank_iban,REVIEW_FLAGS</div>
      <div class="row">Atlas Paper Co.,INV-4421,2026-04-28,2026-05-28,CAD,842.10,109.47,13%,951.57,40 boxes A4 paper @ 21.05,IE29 AIBK 9311…,</div>
      <div class="row">Murray Coffee Roasters,A2078,2026-04-30,2026-05-15,CAD,1240.00,161.20,13%,1401.20,2 sacks Ethiopian @ 620.00,—,<span class="flag">missing: bank_iban</span></div>
      <div class="row">Eastside Print,EP-9912,2026-05-01,2026-05-31,CAD,318.00,41.34,13%,359.34,500 letterheads + 200 cards,IE82 BOFI 9000…,</div>
      <div class="row">Goodwin Cleaning,2026-04-W18,2026-04-29,2026-05-13,CAD,640.00,83.20,13%,723.20,4× weekly clean (April),IE61 ULSB 9870…,</div>
      <div class="row">Foley Logistics,FL-22041,2026-04-26,2026-05-26,CAD,2105.50,273.72,13%,2379.22,3 deliveries (Mar+Apr),IE29 AIBK 9311…,<span class="flag">tax math off by 0.00 (ok)</span></div>
      <div class="row">Vert Designs,V-1109,2026-04-25,2026-05-25,EUR,1100.00,253.00,23%,1353.00,Brand refresh consult,DE89 3704 0044…,</div>
      <div class="row">Linwood Hardware,89215,2026-04-22,2026-05-22,CAD,89.45,11.63,13%,101.08,misc supplies,—,<span class="flag">missing: bank_iban</span></div>
      <div class="row">Pacific Roasters,PR-3041,2026-04-19,2026-05-19,CAD,510.00,66.30,13%,576.30,1 sack Colombia @ 510.00,IE61 ULSB 9870…,</div>
      <div class="row">Quinn Refrigeration,QR-1188,2026-04-18,2026-05-18,CAD,4200.00,546.00,13%,4746.00,Walk-in freezer service,IE82 BOFI 9000…,<span class="flag">due date < invoice date — verify</span></div>
      <div class="row">Sterling Energy,SE-77202,2026-04-15,2026-05-15,CAD,1860.40,241.85,13%,2102.25,Electricity April,—,</div>
    </div>
    <div class="meta-strip"><span><strong>10 invoices</strong> in ≈ 90 seconds</span><span><strong>3 flagged</strong> for review (you spot-check)</span><span><strong>Paste</strong> straight into QuickBooks</span></div>
  </div>
</div>
"""

JOBS = [
    ("wf1-inbox-triage.png",   INBOX,     1180, 920),
    ("wf2-claude-project.png", PROJECT,   1180, 720),
    ("wf3-marketing-loop.png", MARKETING, 1180, 1380),
    ("wf4-invoice-killer.png", INVOICE,   1180, 880),
]


def render_all() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for filename, html, width, height in JOBS:
            ctx = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2,
            )
            page = ctx.new_page()
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(600)
            out = OUT_DIR / filename
            page.screenshot(path=str(out), full_page=True, type="png", omit_background=False)
            ctx.close()
            print(f"✓ {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
        browser.close()
    print(f"\nAll {len(JOBS)} illustrations rendered to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    render_all()
