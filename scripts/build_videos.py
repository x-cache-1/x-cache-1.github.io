"""Generate the X-Cache project page comparison videos.

We emit *two* videos per scenario:

    <scenario>_baseline.mp4   — the no-cache full-compute rollout
    <scenario>_cache.mp4      — the X-Cache rollout (same seed, same conditioning)

Both videos are rendered at the *same* canvas size and pixel layout, with no
chrome burned into the frame. The site runtime overlays them, sync-locks
playback, and lets the user pick between three creative comparison modes:

    • wipe    — drag a seam to reveal one or the other
    • diff    — `mix-blend-mode: difference` collapses identical pixels to
                black so cache-induced perturbations glow on a dark void
                (this is the page's "X-Ray" view of approximation error)
    • shadow  — both layers playback overlaid with low opacity so they form
                a single phantom image; if the two streams were identical
                the silhouette would be perfectly sharp

Keeping the two videos pixel-aligned and chrome-free is what makes the diff
mode work. All HUD chrome (frame counter, scenario tag, KV-update marker,
PSNR readout) is rendered as HTML over the video, not into it.

Usage:
    python x-cache/scripts/build_videos.py \\
        --src "/path/to/wm_v2.0 (X-Cache tech report)" \\
        --out x-cache/public/videos
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

# ----- constants -----------------------------------------------------------

# Map scenario id → (debug_cache_dir suffix, debug_torch_dir suffix, session id, label)
SCENARIOS = {
    "urban": (
        "debug_cache_offline_dataset_config",
        "debug_torch_offline_dataset_config",
        "c-06531d14-a7ea-3149-869b-2e84eb77e4fb_4",
        "URBAN STREET",
    ),
    "highway": (
        "debug_cache_offline_dataset_config_wh_hwisp_9m",
        "debug_torch_offline_dataset_config_wh_hwisp_9m",
        "c-1cf27392-301d-32b3-aef6-03d78491a89d_4",
        "HIGHWAY",
    ),
    "uturn": (
        "debug_cache_offline_dataset_config_uturn",
        "debug_torch_offline_dataset_config_uturn",
        "c-1a177b86-b403-3505-8409-46906bb08b36_4",
        "U-TURN",
    ),
}

# Native 7-cam composite is ≈2438×2216 ≈ 1.10:1.  We resize to a pure 1280×1160
# for the web (still ~1.1 aspect, fits comfortably on laptop and mobile).
PANEL_W = 1280
PANEL_H = 1160
FPS     = 12

FRAME_RE = re.compile(r"frame_(\d+)_gen_\d+_combined\.png$")


def find_frames(dir_path: Path) -> list[Path]:
    pairs = []
    for p in dir_path.iterdir():
        m = FRAME_RE.search(p.name)
        if m:
            pairs.append((int(m.group(1)), p))
    pairs.sort()
    return [p for _, p in pairs]


def fit_panel(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize-then-center-crop so the image fills target W×H, no letterbox.
    Source aspect (~1.10) is essentially identical to the 1280×1160 target,
    so this is a near-pure resize."""
    src_w, src_h = img.size
    src_ar = src_w / src_h
    tgt_ar = target_w / target_h
    if src_ar > tgt_ar:
        new_h = target_h
        new_w = int(round(src_w * (new_h / src_h)))
    else:
        new_w = target_w
        new_h = int(round(src_h * (new_w / src_w)))
    img = img.resize((new_w, new_h), Image.BICUBIC)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def render_frames(frame_paths: list[Path], tmp: Path, max_frames: int | None = None) -> int:
    """Resize each PNG into the temp directory as JPGs ready for ffmpeg."""
    n = len(frame_paths) if max_frames is None else min(len(frame_paths), max_frames)
    for i in range(n):
        img = Image.open(frame_paths[i]).convert("RGB")
        panel = fit_panel(img, PANEL_W, PANEL_H)
        panel.save(tmp / f"f_{i:05d}.jpg", quality=88)
        if (i + 1) % 50 == 0 or i == n - 1:
            print(f"    · resized {i + 1}/{n}", flush=True)
    return n


def encode(tmp: Path, out_path: Path) -> None:
    """ffmpeg encode H.264 yuv420p, sized to even dimensions."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(FPS),
        "-i", str(tmp / "f_%05d.jpg"),
        "-vf", f"scale={PANEL_W}:{PANEL_H}:flags=lanczos",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-r", str(FPS),
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def render_poster(frame_path: Path, out_path: Path) -> None:
    img = Image.open(frame_path).convert("RGB")
    panel = fit_panel(img, PANEL_W, PANEL_H)
    panel.save(out_path, quality=85)


def build_scenario(src_root: Path, out_dir: Path, scen_id: str) -> None:
    cache_suffix, torch_suffix, session, label = SCENARIOS[scen_id]
    cache_frames_dir = src_root / cache_suffix / session / "vis_generated_frames"
    torch_frames_dir = src_root / torch_suffix / session / "vis_generated_frames"

    cache_list = find_frames(cache_frames_dir)
    torch_list = find_frames(torch_frames_dir)
    n = min(len(cache_list), len(torch_list))
    if n == 0:
        raise SystemExit(f"[fail] {scen_id}: no frame pairs under {src_root}")

    print(f"[{scen_id}] {label}  ·  {n} paired frames")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_baseline = out_dir / f"{scen_id}_baseline.mp4"
    out_cache    = out_dir / f"{scen_id}_cache.mp4"
    out_poster   = out_dir / f"{scen_id}_poster.jpg"

    # Baseline pass
    print(f"  baseline → {out_baseline.name}")
    with tempfile.TemporaryDirectory(prefix=f"xc_{scen_id}_b_") as tmp:
        tmp = Path(tmp)
        n_actual = render_frames(torch_list[:n], tmp)
        encode(tmp, out_baseline)

    # Cache pass
    print(f"  cache    → {out_cache.name}")
    with tempfile.TemporaryDirectory(prefix=f"xc_{scen_id}_c_") as tmp:
        tmp = Path(tmp)
        render_frames(cache_list[:n], tmp)
        encode(tmp, out_cache)

    # Poster from a mid-clip cache frame
    render_poster(cache_list[n // 2], out_poster)

    print(f"[{scen_id}] done  ·  baseline={out_baseline.name}  cache={out_cache.name}  poster={out_poster.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True,
                    help="path to wm_v2.0 (X-Cache tech report) directory")
    ap.add_argument("--out", required=True,
                    help="output dir, e.g. x-cache/public/videos")
    ap.add_argument("--scenarios", nargs="*", default=None,
                    help="subset to build, e.g. urban highway")
    args = ap.parse_args()

    src = Path(args.src).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"src not found: {src}")
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not found on PATH")

    targets = args.scenarios or list(SCENARIOS.keys())
    for scen in targets:
        build_scenario(src, out, scen)


if __name__ == "__main__":
    sys.exit(main() or 0)
