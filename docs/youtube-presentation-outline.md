# One Weekend + First Time Using Claude Code (With No Coding Knowledge) = Two Awesome Websites

## YouTube Video Presentation Outline

---

## THE NUMBERS

| Metric | Result |
|---|---|
| **Time span** | March 8 - April 12, 2026 (~5 weekends) |
| **Git commits** | 78 |
| **HTML pages** | 15 |
| **Blog posts** | 10 |
| **Lead magnet pages** | 4 (Scorecard, ROI Calculator, AI Stack, 5-Day Challenge) |
| **Lines of code written by Alice** | 0 |
| **Coding knowledge required** | None |

---

## WHAT WAS BUILT

### Site 1: smallbusinessaicoach.com (Alice's AI coaching business)
- Full marketing website with 15 pages
- Blog engine with 10 posts loaded from JSON
- 4 interactive lead magnets
- AI-powered social media content pipeline
- Automated weekly email digest system
- LinkedIn carousel rendering pipeline

### Site 2: AL Pro Solar Sales Funnel (B2B solar company - Quebec)
- LinkedIn automation with carousel generator
- Email outreach automation (Wave 1 + Wave 2)
- French-language content system

---

## PLUGINS & SKILLS INSTALLED (The "App Store")

### 7 Plugins installed (one-time setup, used across every session):

| Plugin | What It Does |
|---|---|
| **Superpowers** | Planning, brainstorming, debugging, code review, TDD workflows |
| **Frontend Design** | Generates production-grade HTML/CSS — the main website builder |
| **Playwright** | Browser automation — takes screenshots, tests pages, renders PDFs |
| **Context7** | Fetches live documentation for any library/framework |
| **Claude-Mem** | Persistent memory across sessions — remembers past work |
| **Last30Days** | Deep research across Reddit, X, YouTube, news sources |
| **Remotion Superpowers** | Video generation from code |

### 20 Skills installed (specialized capabilities):

| Skill | What It Does |
|---|---|
| **SEO suite** (12 skills) | Full SEO: audits, schema, sitemaps, content, technical, local, images, hreflang, geo, programmatic, competitor pages, DataForSEO |
| **Hormozi-Style Marketing** | Campaign planning, ad copy, funnels, offers, personas — the $100M Offers framework |
| **LinkedIn** | Profile fetching, post creation, messaging, company search |
| **Frontend Design** | Anti-generic design guardrails, brand-aware UI generation |

---

## THE PROMPTS — IN ORDER

### Weekend 1 (March 8-9): Foundation

**Prompt 1: "Build me a 4-page AI services website"**
- What it built: Homepage, About, Services, Contact
- Assets needed: One professional headshot (`_MCK3991.jpg`)
- Result: Initial commit — 4-page AI services website

**Prompt 2: "Connect the scorecard to Supabase"**
- What it built: Interactive quiz with scoring logic + database backend
- Assets needed: Supabase project URL + anon key
- Result: AI Readiness Scorecard page

**Prompt 3: "Add a blog section with an AI maturity framework article"**
- What it built: Blog listing page + first blog post
- Assets needed: None (content generated from prompt)

**Prompt 4: "Major site update - SEO, workshops, blog hero, PDF download, About page"**
- What it built: Workshops page, PDF lead magnet, About page redesign
- Assets needed: PDF file (The_AI_First_Business_deck.pdf uploaded to Supabase storage)

---

### Weekend 2 (March 15-16): Webinar Funnel + Sales Page

**Prompt 5: "Add a Claude Cowork webinar funnel page"**
- What it built: Full webinar landing page with countdown, registration form, Supabase integration
- Assets needed: Webinar date/time, Zoom link

**Prompt 6: (Multiple styling prompts)** — "Restyle webinar page to match brand", "Update hero subtitle copy", "Restyle countdown band"
- What it did: Refined the webinar page through 6-7 rapid iterations
- Lesson: Small styling tweaks are fast — just describe what you want changed

**Prompt 7: "Add a Claude Power User standalone funnel page"**
- What it built: Sales page for a paid product ($47 USD)
- Assets needed: Stripe API key, product description
- Result: Full checkout flow with Stripe integration + thank-you page

---

### Weekend 3 (March 22-28): SEO + Content System

**Prompt 8: "/seo-audit" (the SEO skill)**
- What it did: Full automated SEO audit across 9 categories
- What it built: robots.txt, sitemap.xml, JSON-LD schema on every page, privacy policy, terms, cookie consent, llms.txt
- Assets needed: None — the skill audits and fixes automatically

**Prompt 9: "Add Claude Resources page"**
- What it built: Resource hub with "Chat vs Cowork vs Code" comparison, starter guide, Tiny Agency section
- Assets needed: None

**Prompt 10: "Replace Tailwind CDN with compiled CSS"**
- What it did: Reduced page load from 300KB JS to 7.3KB CSS
- Lesson: Performance optimization prompts work great

---

### Weekend 4 (March 29 - April 5): Content Pipeline + Lead Magnets

**Prompt 11: "Build a social media content pipeline that scrapes Reddit, Anthropic blog, and RSS feeds, drafts posts, and emails me a weekly digest"**
- What it built: Full Python pipeline with 7 modules:
  - Reddit fetcher, Anthropic blog scraper, RSS aggregator
  - Claude API content drafter (repurposes into 5 formats per post)
  - Gmail API sender with branded HTML template
  - Weekly automation via macOS LaunchAgent
- Assets needed: Reddit API credentials, Gmail OAuth, Claude API key, RSS feed URLs
- Result: Automated Sunday digest email with curated AI content

**Prompt 12: "Add an AI Stack Template lead magnet page"**
- What it built: Interactive tool recommendation page with email gate

**Prompt 13: "Add an AI ROI Calculator"**
- What it built: Interactive calculator — input hours/rate, get savings estimate + PDF report

**Prompt 14: "Add a 5-Day AI Challenge landing page"**
- What it built: Challenge signup page with day-by-day preview + email sequence outline

**Prompt 15: "Add Free Tools dropdown to nav, footer resources, smart bottom bar"**
- What it did: Wired all 4 lead magnets into a unified nav dropdown across all pages

---

### Weekend 5 (April 11-12): Social Graphics + Offer Redesign

**Prompt 16: "Build branded HTML templates for social media graphics and render them with Playwright"**
- What it built: LinkedIn carousel renderer (HTML to PDF + PNG slides), quote graphic template, Instagram templates
- Assets needed: Brand fonts, colors, logo

**Prompt 17: "Add Drive uploader, reply monitor, and graphics orchestrator"**
- What it built: Google Drive upload integration, batch rendering pipeline
- Assets needed: Google Drive API credentials, folder ID

**Prompt 18: "Use the /hormozi-style skill to review my website and jamout.ai and make a proposal"**
- What it did: Full competitive analysis, revenue modeling, new offer stack design
- Assets needed: Competitor URL, Hormozi-Style-Marketing-Playbook.docx
- Result: 4-tier offer stack, A.I.R. Method framework, ad-to-website funnel map

**Prompt 19: "Redesign"** (one word!)
- What it built: Complete homepage redesign with:
  - New hero ("Go from AI-overwhelmed to AI-confident in 30 days")
  - A.I.R. Method section (Audit, Implement, Run)
  - 4-tier pricing cards with visible pricing
  - Problem section, updated FAQ, new CTA band

**Prompt 20: "All"** (after showing the workshops page alignment issues)
- What it did: Rewrote workshops.html to match the new homepage

**Prompt 21: "Programs and workshops don't align, there are too many options. Maybe the programs stay and workshops go"**
- What it did: Simplified — workshops.html became a redirect

**Prompt 22: "Also join the accelerator gives no information about the accelerator"**
- What it built: Full long-form Accelerator sales page (accelerator.html) with:
  - Hero with pricing + urgency
  - Week-by-week A.I.R. Method breakdown
  - "What's Included" grid (6 items)
  - Dual pricing (Individual $997 / Team $3,997+)
  - 8-question FAQ
  - Application CTA

**Prompt 23: "Create a blog post from this: [pasted video script]"**
- What it built: Full blog post with 9 sections, YouTube embed, sidebar TOC, Accelerator CTA
- Assets needed: YouTube video URL, video script/notes

---

## ASSETS YOU NEED BEFORE STARTING

### Day 1 essentials (to get a site live):
- 1 professional headshot (used across hero, about, author bios)
- Your brand colors (3-4 hex codes)
- Business name + tagline
- 2-3 paragraphs about what you do
- A Vercel account (free) for hosting

### Week 1 additions (to add interactivity):
- Supabase account (free tier) — for forms, quiz scoring, email capture
- Calendly link (free) — for booking CTAs
- Google Tag Manager ID — for analytics

### Week 2+ additions (to build the funnel):
- Stripe account — if selling anything directly
- A PDF lead magnet (or Claude Code will help you create one)
- Testimonials (names, titles, quotes)
- Gmail OAuth credentials — if building email automation

### Optional power tools:
- Google Drive API credentials — for content pipeline uploads
- Reddit API credentials — for content sourcing
- Claude API key — for AI-powered content drafting pipeline

---

## THE FULL PAGE MAP (What Exists Now)

```
smallbusinessaicoach.com/
|-- index.html              <- Homepage (4-tier offers, A.I.R. Method)
|-- accelerator.html        <- Sales page (30-Day Accelerator)
|-- workshops.html          <- Redirects to homepage #offers
|-- about.html              <- About Alice
|-- blog.html               <- Blog listing (loads from posts.json)
|-- blog/                   <- 10 blog posts
|-- scorecard.html          <- AI Readiness Scorecard (interactive quiz)
|-- ai-roi-calculator.html  <- ROI Calculator (interactive tool)
|-- ai-stack.html           <- AI Stack Template (lead magnet)
|-- ai-challenge.html       <- 5-Day AI Challenge (lead magnet)
|-- claude-resources.html   <- Claude guides hub
|-- claudepoweruser.html    <- Sales page ($47 product)
|-- webinar.html            <- Webinar registration
|-- thank-you.html          <- Post-purchase page
|-- privacy-policy.html     <- Legal
|-- terms.html              <- Legal
|-- robots.txt              <- SEO
|-- sitemap.xml             <- SEO
|-- llms.txt                <- AI search optimization
|-- social-pipeline/        <- Automated content system
    |-- run_pipeline.py     <- Weekly orchestrator
    |-- render_graphics.py  <- Carousel/quote renderer
    |-- templates/          <- HTML templates for social graphics
```

---

## THE ONE-LINER PROMPTS THAT DID THE MOST

| Prompt | What Happened |
|---|---|
| `"redesign"` | Entire homepage rebuilt with new offer stack |
| `"all"` | Workshops page rewritten to align |
| `"yes"` | Accelerator sales page + workshops redirect + homepage CTAs updated |
| `"/seo-audit"` | 30+ SEO fixes across entire site in one pass |
| `"looks good"` | Session saved to memory for next time |

---

## KEY TAKEAWAY FOR THE VIDEO

### The pattern is always the same:

1. **Describe what you want** in plain English (no code, no technical terms)
2. **Claude Code builds it** — HTML, CSS, JS, Python, APIs, whatever's needed
3. **You review the screenshot** and say what to change
4. **Repeat** until it looks right

You never touch code. You never Google syntax. You never debug. You just describe and decide.

**78 commits. 15 pages. 10 blog posts. 4 lead magnets. 1 automated content pipeline. Zero lines of code written by a human.**
