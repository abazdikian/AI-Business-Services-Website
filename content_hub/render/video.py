"""PNG slides → MP4 slideshow for TikTok/Reels.

Each slide displays for SLIDE_DURATION_SECS. H.264/yuv420p for broad
compatibility (IG/TT upload, QuickTime preview). No audio.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

SLIDE_DURATION_SECS = 5
OUTPUT_FPS = 30


def build_slideshow_mp4(image_paths: list[Path], out_path: Path,
                        duration_secs: int = SLIDE_DURATION_SECS) -> Path:
    """Chain image_paths into an MP4 with `duration_secs` per slide.

    Uses -loop 1 per input + filter_complex concat so each slide has an
    exact duration — the concat demuxer was adding a trailing frame.
    Raises RuntimeError on ffmpeg failure.
    """
    if not image_paths:
        raise ValueError("no images to build slideshow from")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = len(image_paths)

    cmd: list[str] = ["ffmpeg", "-y"]
    for p in image_paths:
        cmd += ["-loop", "1", "-t", str(duration_secs), "-i", str(p.resolve())]

    concat_inputs = "".join(f"[{i}:v]" for i in range(n))
    filter_complex = (
        f"{concat_inputs}concat=n={n}:v=1:a=0[v];"
        f"[v]fps={OUTPUT_FPS},format=yuv420p[vout]"
    )
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-movflags", "+faststart",
        str(out_path),
    ]
    log.info("rendering slideshow → %s (%d slides × %ds)",
             out_path.name, n, duration_secs)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")
    log.info("built %s (%d bytes)", out_path.name, out_path.stat().st_size)
    return out_path
