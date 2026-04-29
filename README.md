# X-Cache · Project Page

Astro-built project page for the X-Cache technical report (XPeng AI Infra).
Editorial-tech aesthetic, fully localised in English and Chinese, with a custom
wipe / diff / shadow video comparator that lets the reader inspect the
"lossless" claim pixel by pixel.

## Quick start

```bash
cd x-cache
npm install         # one-time
npm run dev         # local dev server on http://localhost:4321
npm run build       # → dist/  (static, deployable to any CDN)
npm run preview     # preview the built bundle
```

The default route `/` redirects to `/en/`. The locale switcher in the nav
toggles between `/en/` and `/zh/`.

## Layout

```
x-cache/
├── astro.config.mjs           # i18n routing — /en/ + /zh/
├── package.json               # astro ^5
├── src/
│   ├── i18n/                  # en.json + zh.json — every string lives here
│   ├── layouts/Layout.astro   # html shell, fonts, fade-in observer
│   ├── components/            # Hero, Intro, Principle, Architecture,
│   │                          # Safety, Compare, Demos, Results, Footer
│   ├── pages/
│   │   ├── index.astro        # static-friendly redirect → /en/
│   │   ├── en/index.astro
│   │   └── zh/index.astro
│   └── styles/global.css      # one stylesheet, no Tailwind
├── public/
│   ├── figures/               # favicon + Open Graph SVG
│   └── videos/                # built comparison videos (see below)
└── scripts/
    └── build_videos.py        # frame-pair → mp4 builder
```

## The video comparator

Each scenario ships *three* mp4s — `<scenario>_baseline.mp4`,
`<scenario>_cache.mp4`, and `<scenario>_heatmap.mp4`. The two main streams
are 1920×800 12 fps cinematic 7-camera composites built from the world
model's *raw* per-camera output (no HUD, no BEV, no trajectory chrome,
no perception annotations). The heatmap is a 960×400 turbo-pseudocolour
view of the per-pixel diff, encoded with a slight gaussian blur to keep
file size in check.

The runtime in `Demos.astro` overlays the three tracks in a single stage
and offers four modes:

| Mode    | What it does                                                                 |
|---------|------------------------------------------------------------------------------|
| Wipe    | Drag the seam to reveal baseline (left) ↔ X-Cache (right)                     |
| Diff    | `mix-blend-mode: difference` over a stage-level brightness amplifier — identical pixels collapse to black; cache-induced residual glows |
| Shadow  | Duotone overlay (cache red-shifted, baseline blue-shifted) over `mix-blend-mode: lighten` — a "phantom" view |
| Heatmap | Swap the cache layer for the precomputed turbo-pseudocolour diff. Honest linear scaling × 12: pure-zero pixels stay black, real disagreements light up navy → green → orange |

The comparator also ships a draggable scrubber bar with chunk-tick markers,
keyboard shortcuts (←/→ to step one frame, space to play/pause), and an
animated DiT-block ribbon at the top-right of the stage that visualises
which of the model's 27 blocks are computed vs. reused at the current frame.

All chrome (frame counter, scenario tag, skip pill, ribbon) is rendered as
HTML over the videos, *not* burned into the frame, so diff and heatmap
modes show only the model-side delta.

## Regenerating the demo videos

```bash
# run from the repo root, with the held-out wm_v2.0 dump on disk
python x-cache/scripts/build_videos.py \
    --src "/root/workspace/yixiao.zeng@xiaopeng.com/wm_inference_offline_test_results/wm_v2.0 (X-Cache tech report)" \
    --out x-cache/public/videos
```

For a single scenario:

```bash
python x-cache/scripts/build_videos.py \
    --src "..." --out x-cache/public/videos --scenarios uturn
```

The script reads `debug_torch_<config>/<session>/raw_cameras/` for the
baseline and `debug_cache_<config>/<session>/raw_cameras/` for the X-Cache
rollout. It composes the seven per-camera PNGs into a 1920×800 cinematic
grid (`side_0 | front_0 | side_3` on top, `side_1 | front_1 | rear_0 | side_2`
below), encodes baseline + cache mp4s, then computes the turbo-pseudocolour
diff and encodes a half-resolution heatmap mp4 alongside.

Pass `--heatmap-only` to refresh just the diff video while keeping existing
baseline/cache mp4s — useful when iterating on the heatmap colour ramp.
