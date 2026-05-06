"""Render the lead-magnet print HTML to PDF via Playwright headless Chrome.

Source:  assets/lead-magnets/source/3-workflows-starter-kit-print.html
Output:  assets/lead-magnets/3-workflows-starter-kit.pdf

Usage:
    python scripts/render_lead_magnet_pdf.py
    python scripts/render_lead_magnet_pdf.py --source <path> --output <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "assets/lead-magnets/source/3-workflows-starter-kit-print.html"
DEFAULT_OUTPUT = ROOT / "assets/lead-magnets/3-workflows-starter-kit.pdf"


def render_pdf(source: Path, output: Path) -> None:
    if not source.exists():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        sys.exit(1)
    output.parent.mkdir(parents=True, exist_ok=True)

    file_url = f"file://{source.resolve()}"
    print(f"Rendering {source.name} → {output.name}")
    print(f"  source: {file_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1200, "height": 1500})
        page = ctx.new_page()
        page.goto(file_url, wait_until="networkidle")
        page.emulate_media(media="print")
        # Give Google Fonts a moment to fully apply
        page.wait_for_timeout(1500)
        page.pdf(
            path=str(output),
            format="Letter",         # 8.5 × 11 in
            print_background=True,    # honor CSS gradients + colored boxes
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        browser.close()

    size_kb = output.stat().st_size // 1024
    print(f"Done. {output.relative_to(ROOT)} ({size_kb} KB)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    render_pdf(args.source, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
