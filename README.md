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

Each scenario ships *two* mp4s — `<scenario>_baseline.mp4` and
`<scenario>_cache.mp4`, both at 1280×1160, 12 fps, identical pixel layout.
The runtime in `Demos.astro` overlays them inside a single stage and offers
three modes:

| Mode    | What it does                                                                 |
|---------|------------------------------------------------------------------------------|
| Wipe    | Drag the seam to reveal baseline (left) ↔ X-Cache (right)                     |
| Diff    | `mix-blend-mode: difference` — identical pixels collapse to black; the residual glows on a dark void, amplified ≈7× by a stage-level filter so the imperceptible drift becomes visible |
| Shadow  | Duotone overlay (cache red-shifted, baseline blue-shifted) over `mix-blend-mode: lighten` — a "phantom" view; if the streams were pixel-identical, this would resolve to one sharp silhouette |

All chrome (frame counter, scenario tag, skip-rate, speedup pill) is rendered
as HTML over the videos, *not* burned into the frame, so diff mode shows only
the model-side delta.

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

The script reads `debug_torch_<config>/<session>/vis_generated_frames/` for
the baseline and `debug_cache_<config>/<session>/vis_generated_frames/` for
the X-Cache rollout, fits them into the 1280×1160 panel, and emits H.264
yuv420p mp4 + a poster JPG ready for the static site.
