# World News Canvas — Saturday 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/mevlanayalcin/world-news-canvas-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/mevlanayalcin/world-news-canvas-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

An original editorial front-page visual summary of Saturday 21 November 2026 world news built for [make.fun](https://make.fun/bounty/news-image-20261121).

## How it is built

- `tools/stories.py` holds the 35 stories (each dated 21 Nov 2026 UTC, with a certainty tag and named sources), the headline figures, the UTC timeline and the date-check lists.
- `tools/render.py` draws the page at 2048 px with Pillow, using the vector scenes in `tools/art.py` and the locator map in `tools/worldmap.py`, then saves a 1024 x 1024 progressive JPEG as `entry.png`. The build stops if any text overflows or overlaps, or any map pins touch.
- `main.ts` (Node 22, no network) checks `entry.png` and copies it to `$MAKEFUN_OUTPUT_DIR` (default `/output`).

Rebuild with `python3 tools/render.py`, then run `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts`.
