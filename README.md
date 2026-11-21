# World News Canvas — Saturday 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/mevlanayalcin/world-news-canvas-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/mevlanayalcin/world-news-canvas-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

An original editorial front-page visual summary of Saturday 21 November 2026 world news built for [make.fun](https://make.fun/bounty/news-image-20261121).

## How it is built

- `tools/stories.py` holds 39 verified pure-Saturday stories across all 7 regions and 31 beats (each dated 21 Nov 2026 UTC with zero Friday leaks, named sources, and calibrated `CONFIRMED` / `OFFICIAL` / `REPORTED` / `CLAIM` verification tiers), 6 headline KPIs, and the `DATE CHECK` exclusion lists.
- `tools/render.py` draws the original Broadsheet Atlas front page at 2048 px with Pillow — combining a slate-indigo folio bar, 66.5 px serif masthead, 6 archival KPI tiles, 13 unobstructed silkscreen-editorial illustrated cards (`tools/art.py`) paired with full-width 300 px-readable kicker bands and color-coded verification pills, a deep slate-teal world atlas (`tools/worldmap.py`, 13 collision-free pins plus 25 brief dots), 26 two-column briefs, a `DATE CHECK` gate box, and an explicit `HOW WE CHECKED` verification legend — then saves a deterministic 1024 × 1024 progressive 4:4:4 JPEG as `entry.png`. Strict geometry checks enforce zero text overlaps, zero margin overflows, zero pin collisions, and >= 8 px right-margin slack on every brief.
- `main.ts` (Node 22, no network) validates `entry.png` and copies it unchanged to `$MAKEFUN_OUTPUT_DIR` (default `/output`).

Rebuild with `python3 tools/render.py`, then run `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts`.
