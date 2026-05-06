#!/usr/bin/env python3
"""
Replace site nav + footer with Brand Refresh v2 canonical markup across all pages.
Injects <link rel="stylesheet" href="assets/chrome.css"> into <head>.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGES = {
    "index.html": None,
    "about.html": "about",
    "blog.html": "blog",
    "workshops.html": "workshops",
    "accelerator.html": "workshops",
    "scorecard.html": "scorecard",
    "claude-resources.html": "resources",
    "claudepoweruser.html": "resources",
    "ai-challenge.html": "resources",
    "ai-roi-calculator.html": "resources",
    "ai-stack.html": "resources",
    "webinar.html": None,
    "privacy-policy.html": None,
    "terms.html": None,
    "thank-you.html": None,
}

FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,500;1,9..144,600&family=Nunito:wght@400;500;600;700;800&display=swap" rel="stylesheet" />'
)

CHROME_LINK = '<link rel="stylesheet" href="assets/chrome.css" />'

LINKEDIN_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.852 3.37-1.852 3.601 0 4.267 2.37 4.267 5.455v6.288zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.063 2.063 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
INSTAGRAM_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'
TIKTOK_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005.8 20.1a6.34 6.34 0 0010.86-4.43V8.21a8.15 8.15 0 004.77 1.52V6.31a4.77 4.77 0 01-1.84-.62z"/></svg>'

LINKS = [
    ("about",     "about.html",              "About"),
    ("workshops", "workshops.html",          "Work With Me"),
    ("scorecard", "scorecard.html",          "Scorecard"),
    ("resources", "claude-resources.html",   "Resources"),
    ("blog",      "blog.html",               "Blog"),
]

def build_nav(active_key):
    link_items = []
    for key, href, label in LINKS:
        cls = ' class="active"' if key == active_key else ''
        link_items.append(f'      <li><a href="{href}"{cls}>{label}</a></li>')
    links_html = "\n".join(link_items)
    nav = f'''<nav class="site-nav">
    <a href="index.html" class="site-nav-brand" aria-label="Alice Bazdikian — home">
      <span class="site-nav-mono">ab</span>
      <span class="site-nav-brand-text">
        <span class="site-nav-brand-name">Alice Bazdikian</span>
        <span class="site-nav-brand-tag">AI Strategist + Educator</span>
      </span>
    </a>
    <ul class="site-nav-links">
{links_html}
      <li class="site-nav-social" aria-label="Social media">
        <a href="https://www.linkedin.com/in/alice-bazdikian" target="_blank" rel="noopener" aria-label="LinkedIn">{LINKEDIN_SVG}</a>
        <a href="https://www.instagram.com/smallbusinessaicoach/" target="_blank" rel="noopener" aria-label="Instagram">{INSTAGRAM_SVG}</a>
        <a href="https://www.tiktok.com/@smallbusinessaicoach" target="_blank" rel="noopener" aria-label="TikTok">{TIKTOK_SVG}</a>
      </li>
      <li>
        <a href="https://calendly.com/abazdikian/diagnostic" target="_blank" rel="noopener" class="site-nav-cta">Book a Diagnostic</a>
      </li>
    </ul>
    <button class="site-nav-hamburger" id="nav-hamburger" aria-label="Toggle navigation" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
  </nav>

  <!-- MOBILE MENU -->
  <div class="site-mobile-menu" id="mobile-menu" aria-hidden="true">
    <a href="about.html">About</a>
    <a href="workshops.html">Work With Me</a>
    <a href="scorecard.html">Scorecard</a>
    <a href="claude-resources.html">Resources</a>
    <a href="blog.html">Blog</a>
    <a href="ai-roi-calculator.html">AI ROI Calculator</a>
    <a href="ai-stack.html">AI Stack Template</a>
    <a href="ai-challenge.html">5-Day AI Challenge</a>
    <a href="https://calendly.com/abazdikian/diagnostic" target="_blank" rel="noopener" class="site-mobile-cta">Book a Diagnostic</a>
  </div>'''
    return nav

FOOTER = f'''<footer class="site-footer">
    <div class="site-footer-inner">
      <div class="site-footer-grid">
        <div class="site-footer-brand-block">
          <div class="site-footer-brand-row">
            <span class="site-footer-mono">ab</span>
            <div>
              <div class="site-footer-brand-name">Alice Bazdikian</div>
              <div class="site-footer-brand-tag">AI Strategist + Educator</div>
            </div>
          </div>
          <p class="site-footer-brand-desc">Helping entrepreneurs and businesses navigate the AI revolution — without the overwhelm.</p>
          <div class="site-footer-socials">
            <a href="https://www.linkedin.com/in/alice-bazdikian" target="_blank" rel="noopener" aria-label="LinkedIn">{LINKEDIN_SVG}</a>
            <a href="https://www.instagram.com/smallbusinessaicoach/" target="_blank" rel="noopener" aria-label="Instagram">{INSTAGRAM_SVG}</a>
            <a href="https://www.tiktok.com/@smallbusinessaicoach" target="_blank" rel="noopener" aria-label="TikTok">{TIKTOK_SVG}</a>
          </div>
        </div>
        <div class="site-footer-col">
          <h4 class="site-footer-col-head">Explore</h4>
          <a href="about.html">About</a>
          <a href="workshops.html">Work With Me</a>
          <a href="scorecard.html">Scorecard</a>
          <a href="blog.html">Blog</a>
        </div>
        <div class="site-footer-col">
          <h4 class="site-footer-col-head">Free Tools</h4>
          <a href="scorecard.html">AI Readiness Scorecard</a>
          <a href="ai-roi-calculator.html">ROI Calculator</a>
          <a href="ai-stack.html">AI Stack Template</a>
          <a href="ai-challenge.html">5-Day Challenge</a>
        </div>
        <div class="site-footer-col">
          <h4 class="site-footer-col-head">Contact</h4>
          <a href="https://calendly.com/abazdikian/diagnostic" target="_blank" rel="noopener">Book a Diagnostic</a>
          <a href="mailto:alice@alicebazdikian.com">alice@alicebazdikian.com</a>
          <a href="https://www.linkedin.com/in/alice-bazdikian" target="_blank" rel="noopener">LinkedIn</a>
          <a href="https://www.instagram.com/smallbusinessaicoach/" target="_blank" rel="noopener">Instagram</a>
        </div>
      </div>
      <div class="site-footer-bottom">
        <div>© 2026 Alice Bazdikian. All rights reserved.</div>
        <div class="site-footer-legal">
          <a href="privacy-policy.html">Privacy Policy</a>
          <a href="terms.html">Terms</a>
        </div>
      </div>
    </div>
  </footer>'''


def inject_chrome_link(html):
    if 'assets/chrome.css' in html:
        return html
    # Insert after Fraunces/Nunito fonts link if present, else before </head>
    if 'family=Fraunces' in html:
        return re.sub(
            r'(family=Fraunces[^"]*"\s*rel="stylesheet"\s*/?>)',
            r'\1\n  ' + CHROME_LINK,
            html, count=1
        )
    # Otherwise replace old Playfair+Inter link with Fraunces+Nunito + chrome link
    if 'family=Playfair' in html:
        html = re.sub(
            r'<link\s+href="https://fonts\.googleapis\.com/css2\?family=Playfair[^"]*"\s*rel="stylesheet"\s*/?>',
            FONTS_LINK + '\n  ' + CHROME_LINK,
            html, count=1
        )
        return html
    # Otherwise insert before </head>
    return html.replace('</head>', f'  {CHROME_LINK}\n</head>', 1)


def replace_nav(html, active_key):
    # Match the first <nav ...>...</nav> block. Greedy up to </nav>.
    # But pages may wrap nav in a <div class="nav-wrapper"> or announce band.
    # Strategy: find first <nav ...> and its matching </nav>, then include optional
    # trailing <div class="mobile-menu">...</div> since we replace that too.

    # Replace nav-wrapper with nav block too if present
    nav_pattern = re.compile(
        r'(<div\s+class="nav-wrapper">\s*)?<nav\b[^>]*>.*?</nav>(\s*</div>)?',
        re.DOTALL
    )
    m = nav_pattern.search(html)
    if not m:
        return html, False

    # Also try to swallow the mobile-menu div that follows and the announce band
    end = m.end()
    rest = html[end:]
    # Mobile menu
    mm = re.match(r'\s*<!--\s*MOBILE MENU\s*-->\s*<div\s+class="mobile-menu"[^>]*>.*?</div>', rest, re.DOTALL)
    if mm:
        end += mm.end()
    else:
        mm = re.match(r'\s*<div\s+class="mobile-menu"[^>]*>.*?</div>', rest, re.DOTALL)
        if mm:
            end += mm.end()

    new_nav = build_nav(active_key)
    return html[:m.start()] + new_nav + html[end:], True


def replace_footer(html):
    # Replace first <footer ...>...</footer>
    pattern = re.compile(r'<footer\b[^>]*>.*?</footer>', re.DOTALL)
    m = pattern.search(html)
    if not m:
        return html, False
    return html[:m.start()] + FOOTER + html[m.end():], True


def process(page, active_key):
    path = ROOT / page
    if not path.exists():
        print(f"SKIP (missing): {page}")
        return
    html = path.read_text(encoding='utf-8')
    orig = html
    html = inject_chrome_link(html)
    html, nav_ok = replace_nav(html, active_key)
    html, footer_ok = replace_footer(html)
    if html != orig:
        path.write_text(html, encoding='utf-8')
        print(f"OK  {page:30s} nav={nav_ok} footer={footer_ok}")
    else:
        print(f"--  {page:30s} (no change)")


if __name__ == '__main__':
    targets = sys.argv[1:] or list(PAGES.keys())
    for page in targets:
        process(page, PAGES.get(page))
