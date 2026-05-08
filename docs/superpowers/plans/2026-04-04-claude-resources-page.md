# Claude Resources Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive Claude Resources page with email-gated content, tabbed guides, expandable cards, and Airtable/Resend integrations.

**Architecture:** Single HTML file (`claude-resources.html`) with inline CSS and vanilla JS, matching the existing site pattern. Three content sections: "Tiny Agency" (visible teaser), "Chat vs Cowork vs Code" (locked), and "Starter Guide" (locked). Email gate between section 1 and 2 stores leads to Airtable and triggers a Resend follow-up email with PDF link. localStorage remembers unlocked state.

**Tech Stack:** HTML, inline CSS, vanilla JS, Tailwind CSS vars (manual), Google Fonts (Playfair Display + Inter), Airtable REST API, Resend REST API.

**Spec:** `docs/superpowers/specs/2026-04-04-claude-resources-page-design.md`

---

## File Structure

| File | Purpose |
|------|---------|
| `claude-resources.html` | The new page (create) |
| `index.html` | Add nav link (modify lines ~1687-1694, ~1702-1707) |
| `about.html` | Add nav link (modify) |
| `workshops.html` | Add nav link (modify) |
| `scorecard.html` | Add nav link (modify) |
| `blog.html` | Add nav link (modify) |
| `webinar.html` | Add nav link (modify) |
| `claudepoweruser.html` | Add nav link (modify) |
| `terms.html` | Add nav link (modify) |
| `privacy-policy.html` | Add nav link (modify) |
| `thank-you.html` | Add nav link (modify) |
| `blog/*.html` | Add nav link to all blog posts (modify) |

---

### Task 1: Create page skeleton with nav, hero, and footer

**Files:**
- Create: `claude-resources.html`

- [ ] **Step 1: Create the HTML file with head, GTM, fonts, CSS variables, nav, hero, and footer**

Create `claude-resources.html` with the full page skeleton. This includes the `<head>` (GTM, meta, fonts), CSS root variables, nav markup (matching index.html but with "Claude Resources" as active link), hero section, and footer. All CSS is inline in a `<style>` block.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({"gtm.start":
new Date().getTime(),event:"gtm.js"});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!="dataLayer"?"&l="+l:"";j.async=true;j.src=
"https://www.googletagmanager.com/gtm.js?id="+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,"script","dataLayer","GTM-53LWP97Z");</script>
<!-- End Google Tag Manager -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Resources — Interactive AI Guides | Alice Bazdikian</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta name="description" content="Interactive guides, mental models, and comparison tools to help you leverage Claude AI for your business. Free resource library by Alice Bazdikian." />
<link rel="canonical" href="https://smallbusinessaicoach.com/claude-resources.html" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,600;1,700;1,900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
  html { scroll-behavior: smooth; }

  :root {
    --eggshell: #F7F3EE;
    --surface:  #FFFFFF;
    --charcoal: #1C1C1C;
    --burgundy: #7D2240;
    --burg-dk:  #651B33;
    --burg-lt:  #9e2d52;
    --gold:     #C9A847;
    --gold-dk:  #B8952E;
    --muted:    #6B6560;
    --border:   rgba(28,28,28,0.09);
  }

  body {
    background: var(--eggshell);
    color: var(--charcoal);
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 16px;
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }

  /* ── NAV (copied from index.html) ── */
  .nav {
    position: sticky; top: 0; z-index: 50;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 2.5rem; height: 68px;
    background: rgba(247,243,238,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }
  .nav-brand { display: flex; flex-direction: column; }
  .nav-brand-name { font-family: 'Playfair Display', serif; font-size: 1.125rem; font-weight: 700; color: var(--charcoal); line-height: 1.2; }
  .nav-brand-tag { font-size: 0.625rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); font-weight: 500; }
  .nav-links { list-style: none; display: flex; align-items: center; gap: 2rem; }
  .nav-links a { font-size: 0.8125rem; font-weight: 500; color: var(--charcoal); text-decoration: none; transition: color 0.2s; }
  .nav-links a:hover { color: var(--burgundy); }
  .nav-links a.active { color: var(--burgundy); font-weight: 600; }
  .btn-nav-outline { border: 1px solid var(--border); padding: 0.4rem 1rem; border-radius: 100px; }
  .btn-nav {
    background: var(--gold); color: var(--charcoal) !important;
    padding: 0.5rem 1.25rem; border-radius: 100px;
    font-weight: 700 !important; font-size: 0.75rem !important;
    letter-spacing: 0.02em;
    box-shadow: 0 2px 8px rgba(201,168,71,0.25);
    transition: background 0.2s, transform 0.15s;
  }
  .btn-nav:hover { background: var(--gold-dk); transform: translateY(-1px); }
  .nav-hamburger { display: none; background: none; border: none; cursor: pointer; padding: 0.5rem; flex-direction: column; gap: 5px; }
  .nav-hamburger span { display: block; width: 22px; height: 2px; background: var(--charcoal); border-radius: 2px; transition: transform 0.3s, opacity 0.3s; }
  .mobile-menu { display: none; position: fixed; top: 68px; left: 0; right: 0; background: var(--eggshell); padding: 1.5rem 2rem; flex-direction: column; gap: 1.25rem; z-index: 49; border-bottom: 1px solid var(--border); box-shadow: 0 8px 24px rgba(28,28,28,0.1); }
  .mobile-menu a { font-size: 1rem; color: var(--charcoal); text-decoration: none; font-weight: 500; }
  .mobile-menu .mob-cta { background: var(--gold); color: var(--charcoal); padding: 0.75rem 1.5rem; border-radius: 100px; text-align: center; font-weight: 700; margin-top: 0.5rem; }

  /* ── HERO ── */
  .hero { padding: 5rem 2rem 3.5rem; text-align: center; background: var(--eggshell); }
  .hero-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--gold); margin-bottom: 1.5rem;
  }
  .hero-eyebrow::before {
    content: ''; width: 22px; height: 1.5px; background: var(--gold);
  }
  .hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2rem, 4.5vw, 3.5rem);
    font-weight: 900; line-height: 1.1;
    letter-spacing: -0.03em; color: var(--charcoal);
    margin-bottom: 1.25rem; max-width: 700px; margin-left: auto; margin-right: auto;
  }
  .hero h1 em { font-style: italic; color: var(--burgundy); }
  .hero-sub {
    font-size: 1.0625rem; color: var(--muted);
    max-width: 560px; margin: 0 auto;
    line-height: 1.7;
  }

  /* ── SHARED SECTION STYLES ── */
  .section { padding: 4.5rem 2rem; }
  .section-alt { background: var(--surface); }
  .section-inner { max-width: 780px; margin: 0 auto; }
  .section-inner-wide { max-width: 1000px; margin: 0 auto; }
  .eyebrow {
    font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--gold);
    margin-bottom: 0.875rem;
    display: flex; align-items: center; gap: 0.625rem;
  }
  .eyebrow::before { content: ''; display: inline-block; width: 22px; height: 1.5px; background: var(--gold); flex-shrink: 0; }
  .section-heading {
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.75rem, 3vw, 2.5rem);
    font-weight: 700; line-height: 1.15;
    letter-spacing: -0.03em; color: var(--charcoal);
    margin-bottom: 0.5rem;
  }
  .section-heading em { font-style: italic; color: var(--burgundy); }
  .section-sub { font-size: 0.9375rem; color: var(--muted); line-height: 1.7; margin-bottom: 2rem; }

  /* ── FOOTER ── */
  footer {
    background: var(--charcoal); padding: 3rem 2.5rem 1.5rem;
  }
  .footer-inner { max-width: 1100px; margin: 0 auto; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1.5rem; margin-bottom: 2rem; }
  .footer-brand-name { font-family: 'Playfair Display', serif; font-size: 1.125rem; font-weight: 700; color: #fff; }
  .footer-brand-tag { font-size: 0.625rem; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(255,255,255,0.4); margin-top: 2px; }
  .footer-nav { display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center; }
  .footer-nav a { font-size: 0.8125rem; color: rgba(255,255,255,0.55); text-decoration: none; transition: color 0.2s; }
  .footer-nav a:hover { color: #fff; }
  .footer-linkedin { display: inline-flex; }
  .footer-copy { max-width: 1100px; margin: 0 auto; font-size: 0.6875rem; color: rgba(255,255,255,0.25); text-align: center; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.06); }

  /* ── RESPONSIVE ── */
  @media (max-width: 768px) {
    .nav { padding: 0 1.25rem; }
    .nav-links { display: none; }
    .nav-hamburger { display: flex; }
    .mobile-menu.open { display: flex; }
    .hero { padding: 3.5rem 1.5rem 2.5rem; }
    .section { padding: 3rem 1.5rem; }
    .footer-inner { flex-direction: column; gap: 1rem; }
    .footer-nav { gap: 1rem; }
  }
</style>
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-53LWP97Z" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->

  <!-- ═══════════ NAVIGATION ═══════════ -->
  <nav class="nav">
    <a href="/" style="text-decoration:none">
      <div class="nav-brand">
        <span class="nav-brand-name">Alice Bazdikian</span>
        <span class="nav-brand-tag">AI Strategist</span>
      </div>
    </a>
    <ul class="nav-links">
      <li><a href="about.html">About</a></li>
      <li><a href="workshops.html" class="btn-nav-outline">Work With Me</a></li>
      <li><a href="scorecard.html">Scorecard</a></li>
      <li><a href="claude-resources.html" class="active">Claude Resources</a></li>
      <li><a href="blog.html">Blog</a></li>
      <li><a href="https://calendly.com/abazdikian/diagnostic" class="btn-nav">Book a Diagnostic</a></li>
    </ul>
    <button class="nav-hamburger" id="nav-hamburger" aria-label="Toggle navigation" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
  </nav>

  <!-- MOBILE MENU -->
  <div class="mobile-menu" id="mobile-menu" aria-hidden="true">
    <a href="about.html">About</a>
    <a href="workshops.html">Work With Me</a>
    <a href="scorecard.html">Scorecard</a>
    <a href="claude-resources.html" style="color:var(--burgundy);font-weight:600;">Claude Resources</a>
    <a href="blog.html">Blog</a>
    <a href="https://calendly.com/abazdikian/diagnostic" class="mob-cta">Book a Diagnostic</a>
  </div>

  <!-- ═══════════ HERO ═══════════ -->
  <section class="hero">
    <p class="hero-eyebrow">Free Resource Library</p>
    <h1>Master <em>Claude AI</em> for Your Business</h1>
    <p class="hero-sub">Interactive guides, mental models, and comparison tools to help you leverage Claude AI — whether you're a complete beginner or ready to build systems.</p>
  </section>

  <!-- SECTIONS GO HERE (Tasks 2-5) -->

  <!-- ═══════════ FOOTER ═══════════ -->
  <footer>
    <div class="footer-inner">
      <div>
        <div class="footer-brand-name">Alice Bazdikian</div>
        <div class="footer-brand-tag">AI Strategist + Educator</div>
      </div>
      <nav class="footer-nav">
        <a href="about.html">About</a>
        <a href="workshops.html">Work With Me</a>
        <a href="scorecard.html">Scorecard</a>
        <a href="claude-resources.html">Claude Resources</a>
        <a href="mailto:alice@alicebazdikian.com">Contact</a>
        <a href="https://www.linkedin.com/in/alice-bazdikian" class="footer-linkedin" aria-label="LinkedIn" target="_blank" rel="noopener">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6z"/>
            <rect x="2" y="9" width="4" height="12"/>
            <circle cx="4" cy="4" r="2"/>
          </svg>
        </a>
      </nav>
    </div>
    <p class="footer-copy">© 2026 Alice Bazdikian · All rights reserved · <a href="privacy-policy.html" style="color:rgba(255,255,255,0.4);text-decoration:none;">Privacy Policy</a> · <a href="terms.html" style="color:rgba(255,255,255,0.4);text-decoration:none;">Terms</a></p>
  </footer>

  <!-- NAV TOGGLE SCRIPT -->
  <script>
    const hamburger = document.getElementById('nav-hamburger');
    const mobileMenu = document.getElementById('mobile-menu');
    hamburger.addEventListener('click', () => {
      const open = mobileMenu.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', open);
      mobileMenu.setAttribute('aria-hidden', !open);
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Verify the page renders correctly**

Start the dev server and screenshot:

```bash
node serve.mjs &
node screenshot.mjs http://localhost:3000/claude-resources.html skeleton
```

Expected: page with nav (Claude Resources highlighted), hero section, and footer. Visually matches the site's existing style.

- [ ] **Step 3: Commit**

```bash
git add claude-resources.html
git commit -m "feat: add claude-resources.html skeleton with nav, hero, footer"
```

---

### Task 2: Build Section 1 — Claude Code = Tiny Agency

**Files:**
- Modify: `claude-resources.html` (add section HTML + CSS)

- [ ] **Step 1: Add the Tiny Agency section CSS**

Add the following CSS inside the existing `<style>` block, before the `/* ── RESPONSIVE ── */` comment:

```css
  /* ── SECTION 1: TINY AGENCY ── */
  .agency-cards {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
  }
  .agency-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px; padding: 1.75rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
  }
  .agency-card:hover {
    border-color: rgba(125,34,64,0.2);
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(125,34,64,0.08);
  }
  .agency-card-icon { font-size: 1.75rem; margin-bottom: 0.75rem; }
  .agency-card h3 {
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: var(--burgundy);
    margin-bottom: 0.5rem;
  }
  .agency-card p { font-size: 0.8125rem; color: var(--charcoal); line-height: 1.5; margin-bottom: 0.5rem; }
  .agency-card .examples {
    font-size: 0.75rem; color: var(--muted); font-style: italic;
    border-top: 1px dashed var(--border); padding-top: 0.5rem; margin-top: 0.5rem;
  }
  .agency-arrows {
    display: flex; justify-content: center; gap: 3rem;
    margin-bottom: 1.5rem; color: var(--burgundy); font-size: 1.25rem;
  }
  .agency-arrows span {
    display: flex; flex-direction: column; align-items: center; gap: 2px;
  }
  .agency-arrows span::after { content: ''; width: 2px; height: 20px; background: var(--burgundy); opacity: 0.3; }
  .manager-box {
    background: var(--burgundy); border-radius: 12px;
    padding: 1.75rem 2rem; text-align: center; color: var(--eggshell);
    position: relative; overflow: hidden;
  }
  .manager-box::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse 60% 80% at 50% 50%, rgba(201,168,71,0.1) 0%, transparent 70%);
    pointer-events: none;
  }
  .manager-label {
    font-size: 0.625rem; letter-spacing: 0.2em; text-transform: uppercase;
    opacity: 0.6; margin-bottom: 0.375rem;
  }
  .manager-box h3 {
    font-family: 'Playfair Display', serif; font-size: 1.375rem;
    font-weight: 700; margin-bottom: 0.625rem; position: relative;
  }
  .manager-box p { font-size: 0.875rem; opacity: 0.85; line-height: 1.6; position: relative; }
  .pull-quote {
    margin-top: 1.75rem; padding: 1rem 1.5rem;
    border-left: 3px solid var(--gold);
    font-family: 'Playfair Display', serif;
    font-size: 1rem; font-style: italic;
    color: var(--muted); line-height: 1.6;
  }

  @media (max-width: 768px) {
    .agency-cards { grid-template-columns: 1fr; }
    .agency-arrows { display: none; }
  }
```

- [ ] **Step 2: Add the Tiny Agency section HTML**

Insert this between the hero `</section>` and the `<!-- SECTIONS GO HERE -->` comment:

```html
  <!-- ═══════════ SECTION 1: TINY AGENCY ═══════════ -->
  <section class="section section-alt" id="tiny-agency">
    <div class="section-inner-wide">
      <p class="eyebrow">Mental Model</p>
      <h2 class="section-heading">Claude Code = <em>Tiny Agency</em></h2>
      <p class="section-sub">The mental model that changed everything</p>

      <div class="agency-cards">
        <div class="agency-card">
          <div class="agency-card-icon">📁</div>
          <h3>Projects</h3>
          <p>Your actual work. Separate folders.</p>
          <div class="examples">Website copy, TikTok series, client proposals</div>
        </div>
        <div class="agency-card">
          <div class="agency-card-icon">🧠</div>
          <h3>Skills</h3>
          <p>Specialists on retainer. Work across projects.</p>
          <div class="examples">Copywriter, editor, script reviewer</div>
        </div>
        <div class="agency-card">
          <div class="agency-card-icon">⚙️</div>
          <h3>Workflows</h3>
          <p>Your SOPs. How you want things done.</p>
          <div class="examples">Content creation process, review steps</div>
        </div>
      </div>

      <div class="agency-arrows">
        <span>↓</span>
        <span>↓</span>
        <span>↓</span>
      </div>

      <div class="manager-box">
        <p class="manager-label">The Manager</p>
        <h3>Claude Code</h3>
        <p>Reads your workflows. Knows your skills. Works on your projects. You set up the system.</p>
      </div>

      <blockquote class="pull-quote">
        "I stopped asking it to do everything and started building a team."
      </blockquote>
    </div>
  </section>
```

- [ ] **Step 3: Screenshot and verify**

```bash
node screenshot.mjs http://localhost:3000/claude-resources.html tiny-agency
```

Expected: eggshell hero, then white section with 3 cards in a row, arrows, burgundy manager box, and pull quote. Cards should have hover effects.

- [ ] **Step 4: Commit**

```bash
git add claude-resources.html
git commit -m "feat: add Tiny Agency section to Claude Resources page"
```

---

### Task 3: Build the Email Gate

**Files:**
- Modify: `claude-resources.html` (add gate HTML + CSS + JS)

- [ ] **Step 1: Add the email gate CSS**

Add inside `<style>`, before `/* ── RESPONSIVE ── */`:

```css
  /* ── EMAIL GATE ── */
  .email-gate {
    background: linear-gradient(135deg, var(--burgundy) 0%, #3D1020 100%);
    padding: 4rem 2rem; text-align: center;
  }
  .email-gate-inner { max-width: 520px; margin: 0 auto; }
  .email-gate h2 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.5rem, 3vw, 2rem);
    font-weight: 700; color: var(--eggshell);
    margin-bottom: 0.75rem; line-height: 1.2;
  }
  .email-gate p {
    color: rgba(247,243,238,0.75);
    font-size: 0.9375rem; line-height: 1.7;
    margin-bottom: 1.75rem;
  }
  .email-form {
    display: flex; gap: 0.5rem;
    max-width: 440px; margin: 0 auto;
  }
  .email-form input {
    flex: 1; padding: 0.875rem 1.25rem;
    border-radius: 100px; border: 2px solid transparent;
    font-family: 'Inter', sans-serif; font-size: 0.875rem;
    background: rgba(247,243,238,0.95); color: var(--charcoal);
    outline: none; transition: border-color 0.2s;
  }
  .email-form input:focus { border-color: var(--gold); }
  .email-form input::placeholder { color: var(--muted); }
  .email-form button {
    background: var(--gold); color: var(--charcoal);
    padding: 0.875rem 1.75rem; border-radius: 100px;
    border: none; font-family: 'Inter', sans-serif;
    font-size: 0.875rem; font-weight: 700;
    cursor: pointer; white-space: nowrap;
    box-shadow: 0 4px 16px rgba(201,168,71,0.35);
    transition: background 0.2s, transform 0.15s;
  }
  .email-form button:hover { background: var(--gold-dk); transform: translateY(-1px); }
  .email-form button:active { transform: translateY(0); }
  .email-form button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .email-gate-note {
    color: rgba(247,243,238,0.4); font-size: 0.75rem; margin-top: 0.875rem;
  }
  .email-gate-error {
    color: #ff9f9f; font-size: 0.8125rem; margin-top: 0.5rem; display: none;
  }
  .email-gate.hidden {
    display: none;
  }

  /* ── LOCKED OVERLAY ── */
  .locked-wrapper { position: relative; }
  .locked-wrapper.locked .locked-content { filter: blur(5px); pointer-events: none; user-select: none; }
  .locked-overlay {
    position: absolute; inset: 0;
    background: rgba(247,243,238,0.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 10; border-radius: 0;
  }
  .lock-badge {
    background: var(--burgundy); color: var(--eggshell);
    padding: 0.75rem 1.5rem; border-radius: 100px;
    font-size: 0.8125rem; font-weight: 600;
    display: flex; align-items: center; gap: 0.5rem;
    box-shadow: 0 4px 20px rgba(125,34,64,0.3);
  }
  .locked-wrapper.unlocked .locked-overlay { display: none; }
  .locked-wrapper.unlocked .locked-content { filter: none; pointer-events: auto; user-select: auto; }

  @media (max-width: 768px) {
    .email-form { flex-direction: column; }
    .email-form button { width: 100%; }
  }
```

- [ ] **Step 2: Add the email gate HTML**

Insert after the Tiny Agency section closing `</section>`:

```html
  <!-- ═══════════ EMAIL GATE ═══════════ -->
  <section class="email-gate" id="email-gate">
    <div class="email-gate-inner">
      <h2>Unlock the Full Interactive Toolkit</h2>
      <p>Get instant access to the comparison tool, starter guide, and all interactive features — plus a PDF version delivered to your inbox.</p>
      <form class="email-form" id="email-form" onsubmit="return handleEmailSubmit(event)">
        <input type="email" id="email-input" placeholder="your@email.com" required autocomplete="email" />
        <button type="submit" id="email-btn">Unlock Now</button>
      </form>
      <p class="email-gate-error" id="email-error"></p>
      <p class="email-gate-note">No spam. Unsubscribe anytime.</p>
    </div>
  </section>
```

- [ ] **Step 3: Add the email gate JavaScript**

Add this before the closing `</body>` tag, after the nav toggle script:

```html
  <!-- EMAIL GATE LOGIC -->
  <script>
    // ── Config (replace with real keys before launch) ──
    const AIRTABLE_BASE_ID = 'YOUR_BASE_ID';
    const AIRTABLE_TABLE_NAME = 'Leads';
    const AIRTABLE_API_KEY = 'YOUR_AIRTABLE_API_KEY';
    const RESEND_API_KEY = 'YOUR_RESEND_API_KEY';
    const PDF_URL = 'https://smallbusinessaicoach.com/assets/claude-resources-guide.pdf';

    // ── Check if already unlocked ──
    function checkUnlocked() {
      if (localStorage.getItem('claude-resources-unlocked') === 'true') {
        unlockContent();
      }
    }

    function unlockContent() {
      const gate = document.getElementById('email-gate');
      if (gate) gate.classList.add('hidden');
      document.querySelectorAll('.locked-wrapper').forEach(el => {
        el.classList.remove('locked');
        el.classList.add('unlocked');
      });
    }

    async function handleEmailSubmit(e) {
      e.preventDefault();
      const emailInput = document.getElementById('email-input');
      const btn = document.getElementById('email-btn');
      const errorEl = document.getElementById('email-error');
      const email = emailInput.value.trim();

      // Validate
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errorEl.textContent = 'Please enter a valid email address.';
        errorEl.style.display = 'block';
        return false;
      }

      errorEl.style.display = 'none';
      btn.disabled = true;
      btn.textContent = 'Unlocking...';

      // Store to Airtable
      try {
        await fetch(`https://api.airtable.com/v0/${AIRTABLE_BASE_ID}/${AIRTABLE_TABLE_NAME}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            fields: {
              Email: email,
              Source: 'claude-resources',
              Timestamp: new Date().toISOString()
            }
          })
        });
      } catch (err) { console.error('Airtable error:', err); }

      // Send email via Resend
      try {
        await fetch('https://api.resend.com/emails', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${RESEND_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            from: 'Alice Bazdikian <alice@smallbusinessaicoach.com>',
            to: [email],
            subject: 'Your Claude AI Resource Guide',
            html: `<p>Hi there!</p><p>Thanks for unlocking the Claude Resources toolkit. Here's your PDF guide:</p><p><a href="${PDF_URL}">Download Your Claude AI Guide (PDF)</a></p><p>If you have any questions about using Claude for your business, I'd love to chat.</p><p>— Alice</p><p><a href="https://calendly.com/abazdikian/diagnostic">Book a Free AI Diagnostic</a></p>`
          })
        });
      } catch (err) { console.error('Resend error:', err); }

      // Unlock regardless of API success
      localStorage.setItem('claude-resources-unlocked', 'true');
      unlockContent();
      return false;
    }

    // Check on page load
    checkUnlocked();
  </script>
```

- [ ] **Step 4: Screenshot and verify**

```bash
node screenshot.mjs http://localhost:3000/claude-resources.html email-gate
```

Expected: burgundy gradient email gate with headline, description, email input + gold button, and fine print.

- [ ] **Step 5: Commit**

```bash
git add claude-resources.html
git commit -m "feat: add email gate with Airtable/Resend integration"
```

---

### Task 4: Build Section 2 — Chat vs Cowork vs Code

**Files:**
- Modify: `claude-resources.html` (add section HTML + CSS + JS)

- [ ] **Step 1: Add the Chat vs Cowork vs Code CSS**

Add inside `<style>`, before `/* ── RESPONSIVE ── */`:

```css
  /* ── SECTION 2: ECOSYSTEM COMPARISON ── */
  .eco-cards {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 1rem; margin-bottom: 2.5rem;
  }
  .eco-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 14px; padding: 1.75rem;
    cursor: pointer; position: relative; overflow: hidden;
    transition: border-color 0.25s, transform 0.2s, box-shadow 0.25s;
  }
  .eco-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--burgundy); transform: scaleX(0);
    transition: transform 0.3s;
  }
  .eco-card:hover::before, .eco-card.expanded::before { transform: scaleX(1); }
  .eco-card:hover {
    border-color: rgba(125,34,64,0.2); transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(125,34,64,0.1);
  }
  .eco-card-icon { font-size: 1.25rem; margin-bottom: 0.625rem; }
  .eco-card h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem; font-weight: 700; color: var(--charcoal);
    margin-bottom: 0.25rem;
  }
  .eco-card-subtitle { font-size: 0.75rem; color: var(--burgundy); font-weight: 500; margin-bottom: 0.75rem; }
  .eco-card-desc { font-size: 0.875rem; color: var(--muted); line-height: 1.65; }
  .eco-card-expand {
    font-size: 0.75rem; color: var(--gold); font-weight: 600;
    margin-top: 0.75rem; display: flex; align-items: center; gap: 4px;
  }
  .eco-card-expand::after { content: '↓'; transition: transform 0.2s; }
  .eco-card.expanded .eco-card-expand::after { transform: rotate(180deg); }

  .eco-card-details {
    display: none; margin-top: 1rem; padding-top: 1rem;
    border-top: 1px solid var(--border);
  }
  .eco-card.expanded .eco-card-details { display: block; }
  .eco-analogy {
    background: rgba(125,34,64,0.05); border-radius: 8px;
    padding: 0.75rem 1rem; font-size: 0.8125rem; color: var(--burgundy);
    font-style: italic; margin-bottom: 0.75rem;
  }
  .eco-skill-label { font-size: 0.625rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 0.375rem; }
  .eco-skill-bar { display: flex; gap: 4px; margin-bottom: 0.75rem; }
  .eco-skill-bar span {
    width: 28px; height: 6px; border-radius: 3px;
    background: var(--border);
  }
  .eco-skill-bar span.filled { background: var(--burgundy); }
  .eco-who-label { font-size: 0.625rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 0.25rem; }
  .eco-who { font-size: 0.8125rem; color: var(--charcoal); line-height: 1.6; }

  /* Feature Table */
  .feature-table-wrap { overflow-x: auto; margin-bottom: 2.5rem; }
  .feature-table {
    width: 100%; border-collapse: collapse; font-size: 0.875rem;
  }
  .feature-table thead th {
    font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--burgundy);
    padding: 0.75rem 1rem; text-align: center;
    border-bottom: 2px solid var(--burgundy);
  }
  .feature-table thead th:first-child { text-align: left; color: var(--muted); }
  .feature-table tbody td {
    padding: 0.75rem 1rem; text-align: center;
    border-bottom: 1px solid var(--border);
    color: var(--charcoal);
    transition: background 0.15s;
  }
  .feature-table tbody td:first-child { text-align: left; font-weight: 500; }
  .feature-table tbody tr:hover td { background: rgba(125,34,64,0.03); }
  .feature-check { color: var(--burgundy); font-weight: 700; }
  .feature-dash { color: var(--border); }

  /* Bottom Line Cards */
  .bottom-line { text-align: center; margin-bottom: 1rem; }
  .bottom-line h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem; font-weight: 700; color: var(--charcoal);
    margin-bottom: 1.25rem;
  }
  .bl-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem; }
  .bl-card {
    border-radius: 12px; padding: 1.5rem;
    border: 1px solid var(--border);
  }
  .bl-card:nth-child(1) { background: rgba(125,34,64,0.04); border-color: rgba(125,34,64,0.12); }
  .bl-card:nth-child(2) { background: rgba(201,168,71,0.06); border-color: rgba(201,168,71,0.15); }
  .bl-card:nth-child(3) { background: rgba(107,101,96,0.05); border-color: rgba(107,101,96,0.12); }
  .bl-card-icon { font-size: 1.25rem; margin-bottom: 0.5rem; }
  .bl-card p { font-size: 0.8375rem; color: var(--muted); line-height: 1.6; }
  .bl-footer {
    font-size: 0.8125rem; color: var(--muted); font-style: italic;
    text-align: center; margin-top: 0.5rem;
  }

  @media (max-width: 768px) {
    .eco-cards { grid-template-columns: 1fr; }
    .bl-cards { grid-template-columns: 1fr; }
  }
```

- [ ] **Step 2: Add the Section 2 HTML**

Insert after the email gate `</section>`:

```html
  <!-- ═══════════ SECTION 2: CHAT vs COWORK vs CODE ═══════════ -->
  <section class="section" id="ecosystem">
    <div class="locked-wrapper locked">
      <div class="locked-overlay">
        <div class="lock-badge">🔒 Enter your email above to unlock</div>
      </div>
      <div class="locked-content">
        <div class="section-inner-wide">
          <p class="eyebrow">Claude Ecosystem</p>
          <h2 class="section-heading">Chat vs Cowork vs Code</h2>
          <p class="section-sub">Same AI brain. Three very different ways to use it. Here's how to pick the right one for you.</p>

          <div class="eco-cards">
            <!-- Chat -->
            <div class="eco-card" onclick="toggleEcoCard(this)">
              <div class="eco-card-icon">💬</div>
              <h3>Claude Chat</h3>
              <p class="eco-card-subtitle">The conversation</p>
              <p class="eco-card-desc">The AI assistant you know. Ask questions, get answers, create content — all in a chat window.</p>
              <p class="eco-card-expand">Tap to expand</p>
              <div class="eco-card-details">
                <div class="eco-analogy">"Like texting a really smart friend"</div>
                <p class="eco-skill-label">Technical Skill Required</p>
                <div class="eco-skill-bar"><span class="filled"></span><span></span><span></span><span></span><span></span></div>
                <p class="eco-who-label">Who It's For</p>
                <p class="eco-who">Everyone. If you can type a message, you can use Claude Chat.</p>
              </div>
            </div>

            <!-- Cowork -->
            <div class="eco-card" onclick="toggleEcoCard(this)">
              <div class="eco-card-icon">🤝</div>
              <h3>Cowork</h3>
              <p class="eco-card-subtitle">The assistant</p>
              <p class="eco-card-desc">Claude Code's power in a friendly interface. Give it a folder, describe the task, walk away. Come back to finished work.</p>
              <p class="eco-card-expand">Tap to expand</p>
              <div class="eco-card-details">
                <div class="eco-analogy">"Like hiring a virtual assistant who works on your computer"</div>
                <p class="eco-skill-label">Technical Skill Required</p>
                <div class="eco-skill-bar"><span class="filled"></span><span class="filled"></span><span class="filled"></span><span></span><span></span></div>
                <p class="eco-who-label">Who It's For</p>
                <p class="eco-who">Non-technical business owners, creators, solopreneurs — anyone who wants AI to DO the work, not just talk about it.</p>
              </div>
            </div>

            <!-- Code -->
            <div class="eco-card" onclick="toggleEcoCard(this)">
              <div class="eco-card-icon">⚡</div>
              <h3>Claude Code</h3>
              <p class="eco-card-subtitle">The developer tool</p>
              <p class="eco-card-desc">The command-line powerhouse. Full terminal access, GitHub integration, and unlimited computer control for developers.</p>
              <p class="eco-card-expand">Tap to expand</p>
              <div class="eco-card-details">
                <div class="eco-analogy">"Like giving a developer the keys to your entire computer"</div>
                <p class="eco-skill-label">Technical Skill Required</p>
                <div class="eco-skill-bar"><span class="filled"></span><span class="filled"></span><span class="filled"></span><span class="filled"></span><span class="filled"></span></div>
                <p class="eco-who-label">Who It's For</p>
                <p class="eco-who">Developers and technical users comfortable with a terminal.</p>
              </div>
            </div>
          </div>

          <!-- Feature Table -->
          <div class="feature-table-wrap">
            <table class="feature-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Chat</th>
                  <th>Cowork</th>
                  <th>Code</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Access your files</td><td class="feature-dash">—</td><td class="feature-check">✓</td><td class="feature-check">✓</td></tr>
                <tr><td>Works autonomously</td><td class="feature-dash">—</td><td class="feature-check">✓</td><td class="feature-check">✓</td></tr>
                <tr><td>Parallel sub-tasks</td><td class="feature-dash">—</td><td class="feature-check">✓</td><td class="feature-check">✓</td></tr>
                <tr><td>No technical skills needed</td><td class="feature-check">✓</td><td class="feature-check">✓</td><td class="feature-dash">—</td></tr>
                <tr><td>Creates files in your folders</td><td class="feature-dash">—</td><td class="feature-check">✓</td><td class="feature-check">✓</td></tr>
                <tr><td>Browse the web</td><td class="feature-check">✓</td><td class="feature-check">✓</td><td class="feature-check">✓</td></tr>
                <tr><td>Plugins / Skills</td><td class="feature-dash">—</td><td class="feature-check">✓</td><td class="feature-check">✓</td></tr>
                <tr><td>Works on Windows</td><td class="feature-check">✓</td><td class="feature-dash">—</td><td class="feature-check">✓</td></tr>
                <tr><td>Mobile access</td><td class="feature-check">✓</td><td class="feature-dash">—</td><td class="feature-dash">—</td></tr>
                <tr><td>Sandboxed (safe by default)</td><td class="feature-check">✓</td><td class="feature-check">✓</td><td class="feature-dash">—</td></tr>
              </tbody>
            </table>
          </div>

          <!-- The Bottom Line -->
          <div class="bottom-line">
            <h3>The Bottom Line</h3>
            <div class="bl-cards">
              <div class="bl-card">
                <div class="bl-card-icon">💬</div>
                <p>Use <strong>Chat</strong> when you need answers, ideas, or content created inside a conversation.</p>
              </div>
              <div class="bl-card">
                <div class="bl-card-icon">🤝</div>
                <p>Use <strong>Cowork</strong> when you want finished files delivered to your computer — without touching a terminal.</p>
              </div>
              <div class="bl-card">
                <div class="bl-card-icon">⚡</div>
                <p>Use <strong>Code</strong> when you're a developer who wants full control and unlimited power.</p>
              </div>
            </div>
            <p class="bl-footer">Same AI. Same brain. Three different levels of autonomy. Pick the one that matches how you work.</p>
          </div>
        </div>
      </div>
    </div>
  </section>
```

- [ ] **Step 3: Add the eco-card toggle JS**

Add this in the existing `<script>` block (before `checkUnlocked();`):

```javascript
    function toggleEcoCard(el) {
      el.classList.toggle('expanded');
    }
```

- [ ] **Step 4: Screenshot and verify**

```bash
node screenshot.mjs http://localhost:3000/claude-resources.html ecosystem
```

Expected: Section appears blurred with a lock badge overlay (since localStorage won't have the key). To test the unlocked view, temporarily add `localStorage.setItem('claude-resources-unlocked', 'true')` in the console and reload.

- [ ] **Step 5: Commit**

```bash
git add claude-resources.html
git commit -m "feat: add Chat vs Cowork vs Code comparison section"
```

---

### Task 5: Build Section 3 — Starter Guide

**Files:**
- Modify: `claude-resources.html` (add section HTML + CSS + JS)

- [ ] **Step 1: Add the Starter Guide CSS**

Add inside `<style>`, before `/* ── RESPONSIVE ── */`:

```css
  /* ── SECTION 3: STARTER GUIDE ── */
  .guide-tabs {
    display: flex; gap: 0.5rem;
    justify-content: center; margin-bottom: 2rem;
  }
  .guide-tab {
    width: 44px; height: 44px;
    border-radius: 10px; border: 1.5px solid var(--border);
    background: var(--surface); color: var(--charcoal);
    font-family: 'Inter', sans-serif; font-size: 0.8125rem; font-weight: 700;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: background 0.2s, border-color 0.2s, color 0.2s, transform 0.15s;
  }
  .guide-tab:hover { border-color: var(--gold); transform: translateY(-1px); }
  .guide-tab.active {
    background: var(--gold); color: var(--charcoal);
    border-color: var(--gold);
    box-shadow: 0 3px 12px rgba(201,168,71,0.3);
  }

  .guide-step {
    display: none;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 2rem 2.25rem;
    max-width: 680px; margin: 0 auto;
    animation: fadeIn 0.3s ease;
  }
  .guide-step.active { display: block; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

  .guide-step-icon { font-size: 1.5rem; margin-bottom: 0.75rem; }
  .guide-step-label {
    font-size: 0.625rem; letter-spacing: 0.15em; text-transform: uppercase;
    color: var(--gold); font-weight: 700; margin-bottom: 0.375rem;
  }
  .guide-step h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.375rem; font-weight: 700; color: var(--charcoal);
    margin-bottom: 0.375rem; line-height: 1.3;
  }
  .guide-step-subtitle {
    font-size: 0.875rem; font-style: italic; color: var(--muted);
    margin-bottom: 1.25rem;
  }
  .guide-points { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
  .guide-points li {
    display: flex; gap: 0.75rem; align-items: flex-start;
    font-size: 0.9375rem; color: var(--charcoal); line-height: 1.6;
  }
  .guide-point-num {
    width: 24px; height: 24px; border-radius: 50%;
    background: rgba(201,168,71,0.15); color: var(--gold);
    font-size: 0.6875rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 2px;
  }

  /* Terminal Demo */
  .terminal-demo {
    background: #1e1e2e; border-radius: 10px;
    padding: 1.25rem 1.5rem; margin-top: 1.5rem;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.8125rem; line-height: 1.8;
    overflow-x: auto;
  }
  .terminal-demo .dots {
    display: flex; gap: 6px; margin-bottom: 0.75rem;
  }
  .terminal-demo .dots span {
    width: 10px; height: 10px; border-radius: 50%;
  }
  .terminal-demo .dots span:nth-child(1) { background: #ff5f56; }
  .terminal-demo .dots span:nth-child(2) { background: #ffbd2e; }
  .terminal-demo .dots span:nth-child(3) { background: #27c93f; }
  .terminal-demo .cmd { color: #cdd6f4; }
  .terminal-demo .prompt { color: #6c7086; }
  .terminal-demo .success { color: #a6e3a1; }
  .terminal-demo .comment { color: #585b70; }

  .guide-footer {
    text-align: center; font-size: 0.75rem; color: var(--muted);
    margin-top: 1.5rem;
  }
```

- [ ] **Step 2: Add the Starter Guide HTML**

Insert after the ecosystem section closing `</section>`:

```html
  <!-- ═══════════ SECTION 3: STARTER GUIDE ═══════════ -->
  <section class="section section-alt" id="starter-guide">
    <div class="locked-wrapper locked">
      <div class="locked-overlay">
        <div class="lock-badge">🔒 Enter your email above to unlock</div>
      </div>
      <div class="locked-content">
        <div class="section-inner-wide">
          <p class="eyebrow">Getting Started</p>
          <h2 class="section-heading">Your Claude Code <em>Starter Guide</em></h2>
          <p class="section-sub">No coding experience needed. Tap each step.</p>

          <div class="guide-tabs">
            <button class="guide-tab active" onclick="showStep(0)" data-step="0">01</button>
            <button class="guide-tab" onclick="showStep(1)" data-step="1">02</button>
            <button class="guide-tab" onclick="showStep(2)" data-step="2">03</button>
            <button class="guide-tab" onclick="showStep(3)" data-step="3">04</button>
            <button class="guide-tab" onclick="showStep(4)" data-step="4">05</button>
          </div>

          <!-- Step 01 -->
          <div class="guide-step active" data-step="0">
            <div class="guide-step-icon">📋</div>
            <p class="guide-step-label">Step 01</p>
            <h3>What is Claude Code?</h3>
            <p class="guide-step-subtitle">It's Claude — but on your computer</p>
            <ol class="guide-points">
              <li><span class="guide-point-num">1</span>Instead of chatting in a browser, Claude works directly on your machine</li>
              <li><span class="guide-point-num">2</span>It creates real files, builds apps, and runs actual tasks</li>
              <li><span class="guide-point-num">3</span>You don't write code — you describe what you want in plain English</li>
            </ol>
          </div>

          <!-- Step 02 -->
          <div class="guide-step" data-step="1">
            <div class="guide-step-icon">📋</div>
            <p class="guide-step-label">Step 02</p>
            <h3>Always Start with /plan</h3>
            <p class="guide-step-subtitle">Blueprints before construction</p>
            <ol class="guide-points">
              <li><span class="guide-point-num">1</span>Type /plan before asking Claude to build anything</li>
              <li><span class="guide-point-num">2</span>It maps out the approach, steps, and files it'll create</li>
              <li><span class="guide-point-num">3</span>You review and approve before it starts — no surprises</li>
            </ol>
            <div class="terminal-demo">
              <div class="dots"><span></span><span></span><span></span></div>
              <div class="prompt">~/ my-project $ claude</div>
              <div class="cmd">> /plan build me a weekly report generator</div>
              <div class="success">✓ Planning mode activated...</div>
              <div class="cmd">Here's my approach:</div>
              <div class="cmd">&nbsp;&nbsp;1. Create project structure</div>
              <div class="cmd">&nbsp;&nbsp;2. Build data input template</div>
              <div class="cmd">&nbsp;&nbsp;3. Generate formatted report output</div>
              <div class="cmd">&nbsp;&nbsp;4. Add export to PDF</div>
              <div class="success">Shall I proceed? (y/n)</div>
            </div>
          </div>

          <!-- Step 03 -->
          <div class="guide-step" data-step="2">
            <div class="guide-step-icon">📂</div>
            <p class="guide-step-label">Step 03</p>
            <h3>Set Up Your Folder</h3>
            <p class="guide-step-subtitle">Future you will thank you</p>
            <ol class="guide-points">
              <li><span class="guide-point-num">1</span>Create a project folder with a clear name</li>
              <li><span class="guide-point-num">2</span>Open your terminal and navigate to that folder</li>
              <li><span class="guide-point-num">3</span>Everything Claude builds stays organised in one place</li>
            </ol>
            <div class="terminal-demo">
              <div class="dots"><span></span><span></span><span></span></div>
              <div class="prompt">~ $ mkdir weekly-report</div>
              <div class="prompt">~ $ cd weekly-report</div>
              <div class="prompt">~/weekly-report $ claude</div>
              <div class="success">✓ Ready. Working in ~/weekly-report</div>
              <div class="comment">📁 Everything Claude builds stays right here ✓</div>
            </div>
          </div>

          <!-- Step 04 -->
          <div class="guide-step" data-step="3">
            <div class="guide-step-icon">🎯</div>
            <p class="guide-step-label">Step 04</p>
            <h3>Start With Something Annoying</h3>
            <p class="guide-step-subtitle">Don't build a SaaS. Fix one thing.</p>
            <ol class="guide-points">
              <li><span class="guide-point-num">1</span>Pick a task that's repetitive, boring, or takes too long</li>
              <li><span class="guide-point-num">2</span>A weekly spreadsheet. A manual report. A content template.</li>
              <li><span class="guide-point-num">3</span>Tell Claude about it. Let it build you a solution.</li>
            </ol>
          </div>

          <!-- Step 05 -->
          <div class="guide-step" data-step="4">
            <div class="guide-step-icon">🔧</div>
            <p class="guide-step-label">Step 05</p>
            <h3>You'll Break Things</h3>
            <p class="guide-step-subtitle">That's the process, not the problem</p>
            <ol class="guide-points">
              <li><span class="guide-point-num">1</span>Everyone breaks things. Every day. Including me.</li>
              <li><span class="guide-point-num">2</span>Claude doesn't judge — it helps you fix it</li>
              <li><span class="guide-point-num">3</span>The only difference is willingness to try again</li>
            </ol>
          </div>

          <p class="guide-footer">smallbusinessaicoach.com — AI implementation for women in business</p>
        </div>
      </div>
    </div>
  </section>
```

- [ ] **Step 3: Add the step toggle JS**

Add this in the existing `<script>` block (before `checkUnlocked();`):

```javascript
    function showStep(index) {
      document.querySelectorAll('.guide-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.guide-step').forEach(s => s.classList.remove('active'));
      document.querySelector(`.guide-tab[data-step="${index}"]`).classList.add('active');
      document.querySelector(`.guide-step[data-step="${index}"]`).classList.add('active');
    }
```

- [ ] **Step 4: Screenshot and verify**

```bash
node screenshot.mjs http://localhost:3000/claude-resources.html starter-guide
```

Expected: Section appears blurred/locked. Test unlocked state by setting localStorage in browser console. When unlocked: tabbed navigation (01-05), step content with terminal demos.

- [ ] **Step 5: Commit**

```bash
git add claude-resources.html
git commit -m "feat: add Starter Guide tabbed section to Claude Resources"
```

---

### Task 6: Update navigation across all site pages

**Files:**
- Modify: `index.html`, `about.html`, `workshops.html`, `scorecard.html`, `blog.html`, `webinar.html`, `claudepoweruser.html`, `terms.html`, `privacy-policy.html`, `thank-you.html`, `blog/*.html`

- [ ] **Step 1: Identify all nav-links blocks across the site**

Run this search to locate the exact line where "Scorecard" appears in each nav:

```bash
grep -rn 'href="scorecard.html">Scorecard</a></li>' *.html blog/*.html
```

This will show each file and line number where the nav link needs updating.

- [ ] **Step 2: Add "Claude Resources" nav link to each file**

In every file found, add this line immediately after the Scorecard `</li>`:

```html
      <li><a href="claude-resources.html">Claude Resources</a></li>
```

Also find the mobile menu in each file (search for `<div class="mobile-menu"`) and add this line after the Scorecard link:

```html
    <a href="claude-resources.html">Claude Resources</a>
```

Also update the footer nav in each file — add after the Scorecard footer link:

```html
        <a href="claude-resources.html">Claude Resources</a>
```

- [ ] **Step 3: Verify nav consistency**

```bash
grep -c 'claude-resources.html' *.html blog/*.html
```

Expected: Every HTML file should show at least 2 matches (desktop nav + mobile menu). Files with footers should show 3.

- [ ] **Step 4: Screenshot homepage to verify nav**

```bash
node screenshot.mjs http://localhost:3000 nav-updated
```

Expected: Nav shows "About | Work With Me | Scorecard | Claude Resources | Blog | Book a Diagnostic"

- [ ] **Step 5: Commit**

```bash
git add *.html blog/*.html
git commit -m "feat: add Claude Resources to navigation across all pages"
```

---

### Task 7: Full page visual QA and responsive testing

**Files:**
- Modify: `claude-resources.html` (any CSS fixes)

- [ ] **Step 1: Screenshot full page at desktop width (1920px)**

```bash
node screenshot.mjs http://localhost:3000/claude-resources.html full-desktop
```

Verify: hero, Tiny Agency section, email gate, locked sections 2 & 3, footer all render correctly.

- [ ] **Step 2: Test unlocked state**

Open browser, go to `http://localhost:3000/claude-resources.html`, open console, run:

```javascript
localStorage.setItem('claude-resources-unlocked', 'true');
location.reload();
```

Screenshot the unlocked page:

```bash
node screenshot.mjs http://localhost:3000/claude-resources.html full-unlocked
```

Verify: email gate hidden, sections 2 & 3 fully visible and interactive (cards expand, tabs switch).

- [ ] **Step 3: Screenshot mobile view (375px)**

Use Playwright to screenshot at 375px width. Verify:
- Nav shows hamburger
- Hero stacks properly
- Cards stack to single column
- Email form input + button stack vertically
- Feature table scrolls horizontally
- Guide tabs remain accessible

- [ ] **Step 4: Fix any visual issues found**

Apply CSS fixes as needed. Common issues to check:
- Text overflow on mobile
- Card padding consistency
- Table readability at small sizes
- Button touch targets (min 44px)

- [ ] **Step 5: Commit any fixes**

```bash
git add claude-resources.html
git commit -m "fix: responsive and visual QA fixes for Claude Resources page"
```

---

### Task 8: Final review and cleanup

- [ ] **Step 1: Verify all interactive features work**

Test in browser:
1. Eco cards expand/collapse on click
2. Guide tabs switch between steps 01-05
3. Email form validates and shows error on invalid email
4. After entering email: gate disappears, sections unlock
5. Refresh page: sections remain unlocked (localStorage)
6. Clear localStorage: gate reappears

- [ ] **Step 2: Verify API placeholders are clearly marked**

Search for `YOUR_` in the file:

```bash
grep 'YOUR_' claude-resources.html
```

Expected: 3 matches — `YOUR_BASE_ID`, `YOUR_AIRTABLE_API_KEY`, `YOUR_RESEND_API_KEY`. These need to be replaced with real keys before launch.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete Claude Resources interactive page with email gate"
```
