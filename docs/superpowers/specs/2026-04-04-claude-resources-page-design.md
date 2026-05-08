# Claude Resources Page — Design Spec

## Overview

A new interactive resource hub page (`claude-resources.html`) for smallbusinessaicoach.com. The page showcases three Claude AI educational resources with an inline email gate that locks interactive features behind lead capture.

## Page Structure

### Navigation
- Add "Claude Resources" to the main nav between "Scorecard" and "Blog"
- Active state styling matches existing nav pattern
- Update nav on all site pages for consistency

### Hero Section
- **Eyebrow:** "Free Resource Library"
- **Headline:** Master *Claude AI* for Your Business
- **Subhead:** Interactive guides, mental models, and comparison tools to help you leverage Claude AI — whether you're a complete beginner or ready to build systems.
- Style: eggshell background, centered text, Playfair Display headline with italic burgundy accent on "Claude AI"
- No CTA button in hero (the email gate serves as the CTA)

### Section 1: Claude Code = Tiny Agency (VISIBLE — teaser)
Fully visible without email capture. Acts as the teaser that demonstrates value.

**Content:**
- Eyebrow: "Mental Model"
- Headline: Claude Code = Tiny Agency
- Subtitle: The mental model that changed everything
- Three cards in a row:
  - **Projects** — Your actual work. Separate folders. (Examples: Website copy, TikTok series, client proposals)
  - **Skills** — Specialists on retainer. Work across projects. (Examples: Copywriter, editor, script reviewer)
  - **Workflows** — Your SOPs. How you want things done. (Examples: Content creation process, review steps)
- Manager box (burgundy background):
  - Label: "THE MANAGER"
  - Title: Claude Code
  - Text: Reads your workflows. Knows your skills. Works on your projects. You set up the system.
- Pull quote: "I stopped asking it to do everything and started building a team."

**Interactivity:** Animated flow — arrows connecting the three cards down to the manager box. CSS animations on scroll (fade-in cards, draw arrows).

### Email Gate
Positioned between Section 1 and Section 2. Burgundy gradient background.

- **Headline:** Unlock the Full Interactive Toolkit
- **Body:** Get instant access to the comparison tool, starter guide, and all interactive features — plus a PDF version delivered to your inbox.
- **Form:** Email input + "Unlock Now" button (gold)
- **Fine print:** No spam. Unsubscribe anytime.

**Behavior on submit:**
1. Validate email format (client-side)
2. POST to Airtable API (store email, timestamp, source: "claude-resources")
3. POST to Resend API (send follow-up email with PDF attachment)
4. Gate element fades out
5. Sections 2 and 3 unlock (blur removed, interactivity enabled)
6. Store unlock state in localStorage so returning visitors don't see the gate again

**Error handling:**
- If Airtable/Resend fails: still unlock the content (don't punish the user), log error to console
- Show inline error message only for invalid email format

### Section 2: Chat vs Cowork vs Code (LOCKED until email)
Interactive comparison of Claude's three interfaces.

**Content:**
- Eyebrow: "Claude Ecosystem"
- Headline: Chat vs Cowork vs Code
- Subtitle: Same AI brain. Three very different ways to use it. Here's how to pick the right one for you.

**Three product cards (clickable/expandable):**

1. **Claude Chat** — "The conversation"
   - Description: The AI assistant you know. Ask questions, get answers, create content — all in a chat window.
   - Analogy: "Like texting a really smart friend"
   - Skill level: Beginner (1/5 bar)
   - Who it's for: Everyone. If you can type a message, you can use Claude Chat.

2. **Cowork** — "The assistant"
   - Description: Claude Code's power in a friendly interface. Give it a folder, describe the task, walk away. Come back to finished work.
   - Analogy: "Like hiring a virtual assistant who works on your computer"
   - Skill level: Intermediate (3/5 bar)
   - Who it's for: Non-technical business owners, creators, solopreneurs — anyone who wants AI to DO the work, not just talk about it.

3. **Claude Code** — "The developer tool"
   - Description: The command-line powerhouse. Full terminal access, GitHub integration, and unlimited computer control for developers.
   - Analogy: "Like giving a developer the keys to your entire computer"
   - Skill level: Advanced (5/5 bar)
   - Who it's for: Developers and technical users comfortable with a terminal.

**Feature comparison table (static table with column highlighting on hover):**

| Feature | Chat | Cowork | Code |
|---------|------|--------|------|
| Access your files | - | ✓ | ✓ |
| Works autonomously | - | ✓ | ✓ |
| Parallel sub-tasks | - | ✓ | ✓ |
| No technical skills needed | ✓ | ✓ | - |
| Creates files in your folders | - | ✓ | ✓ |
| Browse the web | ✓ | ✓ | ✓ |
| Plugins / Skills | - | ✓ | ✓ |
| Works on Windows | ✓ | - | ✓ |
| Mobile access | ✓ | - | - |
| Sandboxed (safe by default) | ✓ | ✓ | - |

**The Bottom Line (3 summary cards):**
- Chat: Use Chat when you need answers, ideas, or content created inside a conversation.
- Cowork: Use Cowork when you want finished files delivered to your computer — without touching a terminal.
- Code: Use Code when you're a developer who wants full control and unlimited power.
- Footer text: *Same AI. Same brain. Three different levels of autonomy. Pick the one that matches how you work.*

**Interactivity:**
- Cards expand on click to reveal full details (analogy, skill bar, who it's for)
- Feature table highlights column on hover
- "Tap to expand" affordance on cards

### Section 3: Your Starter Guide (LOCKED until email)
Interactive 5-step beginner guide to Claude Code.

**Content:**
- Eyebrow: "Getting Started"
- Headline: Your Claude Code Starter Guide
- Subtitle: No coding experience needed. Tap each step.

**5 tabbed steps (clickable navigation: 01 | 02 | 03 | 04 | 05):**

1. **What is Claude Code?** — It's Claude — but on your computer
   - Instead of chatting in a browser, Claude works directly on your machine
   - It creates real files, builds apps, and runs actual tasks
   - You don't write code — you describe what you want in plain English

2. **Always Start with /plan** — Blueprints before construction
   - Type /plan before asking Claude to build anything
   - It maps out the approach, steps, and files it'll create
   - You review and approve before it starts — no surprises
   - *Includes terminal demo block showing /plan command*

3. **Set Up Your Folder** — Future you will thank you
   - Create a project folder with a clear name
   - Open your terminal and navigate to that folder
   - Everything Claude builds stays organised in one place
   - *Includes terminal demo block showing mkdir + cd commands*

4. **Start With Something Annoying** — Don't build a SaaS. Fix one thing.
   - Pick a task that's repetitive, boring, or takes too long
   - A weekly spreadsheet. A manual report. A content template.
   - Tell Claude about it. Let it build you a solution.

5. **You'll Break Things** — That's the process, not the problem
   - Everyone breaks things. Every day. Including me.
   - Claude doesn't judge — it helps you fix it
   - The only difference is willingness to try again

**Interactivity:**
- Tabbed navigation (numbered buttons 01-05)
- Active tab highlighted in gold
- Content area transitions between steps (fade or slide)
- Terminal demo blocks are static HTML `<pre>` elements styled as dark rounded boxes with colored syntax (not actual terminals — purely visual)

### Footer
Standard site footer matching existing pages.

## Technical Implementation

### File
- `claude-resources.html` — single HTML file, inline styles, matches existing site pattern

### Dependencies
- Tailwind CSS via CDN (existing)
- Google Fonts: Playfair Display + Inter (existing)
- No additional JS libraries

### APIs (called client-side)

**Airtable:**
- Endpoint: `https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}`
- Method: POST
- Payload: `{ fields: { Email: "...", Source: "claude-resources", Timestamp: "..." } }`
- Auth: Bearer token (will need to be provided by user)

**Resend:**
- Endpoint: `https://api.resend.com/emails`
- Method: POST
- Payload: email address, subject, HTML body, PDF attachment URL
- Auth: API key (will need to be provided by user)

**Security note:** API keys will be exposed client-side. For production, these should go through a serverless function (e.g., Vercel/Netlify edge function, or a simple proxy). For MVP, direct client-side calls work but keys are visible in source. Will flag this to user during implementation.

### State Management
- `localStorage.setItem('claude-resources-unlocked', 'true')` after successful email submission
- On page load, check localStorage — if unlocked, skip the gate and show all sections
- No server-side session needed

### Locked Section Behavior
- Sections 2 and 3 are rendered in the DOM but visually obscured:
  - `filter: blur(4px)` on content
  - Semi-transparent overlay with lock badge
  - `pointer-events: none` on interactive elements
- On unlock: remove overlay, remove blur, enable pointer-events
- CSS transition for smooth unlock animation

### PDF Generation
- Static PDF of all three sections, generated during implementation using Playwright (render the page content to PDF)
- Hosted in the site's assets folder (e.g., `assets/claude-resources-guide.pdf`)
- Resend sends a download link to the hosted PDF
- PDF should match the brand template: burgundy/eggshell/gold, Playfair + Inter

### Nav Update
- Add "Claude Resources" link to nav in all existing HTML pages:
  - index.html, about.html, workshops.html, scorecard.html, blog.html, webinar.html, claudepoweruser.html, terms.html, privacy-policy.html, thank-you.html
  - All blog post HTML files in blog/

## Brand Compliance
- Background: Eggshell `#F7F3EE` (page) + White `#FFFFFF` (alternating sections)
- Accent: Burgundy `#7D2240` (headlines, hover states, manager box, gate gradient)
- CTA/Highlight: Gold `#C9A847` (eyebrows, buttons, active tab, dividers)
- Text: Charcoal `#1C1C1C`
- Muted: `#6B6560`
- Headlines: Playfair Display (serif)
- Body: Inter (sans-serif)
- No dark backgrounds for main page sections (brand rule)
- Email gate uses burgundy gradient (this is a component, not a page background)

## Success Criteria
- Page loads fast, all interactive elements work without JS framework
- Email capture stores to Airtable, triggers Resend follow-up
- Returning visitors (localStorage) see full content without gate
- Responsive: works on mobile (375px) through desktop (1920px)
- Nav updated consistently across all pages
- Matches existing site's visual quality and patterns
