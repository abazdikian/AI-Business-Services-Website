"""PNG carousel slides → single PDF (LinkedIn document-carousel format).

LinkedIn accepts PDF carousels uploaded as documents. Each slide becomes
one page at its native PNG dimensions (1080×1350 for 4:5).
"""

from __future__ import annotations

import logging
from pathlib import Path

import img2pdf

log = logging.getLogger(__name__)


def build_carousel_pdf(image_paths: list[Path], out_path: Path) -> Path:
    """Combine image_paths into a single PDF, one page per image."""
    if not image_paths:
        raise ValueError("no images to build PDF from")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = img2pdf.convert([str(p.resolve()) for p in image_paths])
    out_path.write_bytes(data)
    log.info("built %s (%d pages, %d bytes)",
             out_path.name, len(image_paths), out_path.stat().st_size)
    return out_path
