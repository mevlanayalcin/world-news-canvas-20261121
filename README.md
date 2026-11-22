# World News Canvas — Saturday 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/mevlanayalcin/world-news-canvas-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/mevlanayalcin/world-news-canvas-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

**Full 24-Hour Edition · Saturday 21 November 2026 · 23:59 UTC.**
Forty stories across seven editorial regions. The numbers on the atlas match the thirteen illustrated cards. A pin locates the event or the named reporting desk; the bitcoin quote has no geographic pin.

## The close

[SOURCES.tsv](SOURCES.tsv) is the edition ledger. Each row gives a card or wire number, the UTC date or documented minute, the credit printed on the page, the source URL and the specific fact it supports. Dates without minutes are intentional. A Saturday bulletin about an earlier event qualifies as an update, not as a new event.

- **Mercury:** At 19:01 UTC [ESA Operations](https://bsky.app/profile/operations.esa.int/post/3n2tryfkof22f) said the burn *should* have ended. [The mission](https://x.com/BepiColombo/status/2124224949409677608) gave 21:37 UTC as the **expected** acquisition of signal. Although [Nature](https://www.nature.com/articles/d41586-026-03803-8) reported arrival, the [ESA Operations post confirming capture](https://bsky.app/profile/operations.esa.int/post/3n2uftyw2f22t) is stamped **00:56:52 UTC Sunday**. That is the announcement time, not a measured signal-lock time. The Saturday page asserts neither capture nor loss of contact.
- **Antalya:** The 23:39 UTC Reuters dispatch reported a new package, not its adoption. The local dateline was already Sunday. Objections were due at 03:00 UTC and a plenary was scheduled for 06:00 UTC Sunday.
- **Junín:** Use the national totals in COEN–INDECI report 6 (18:00 Peru / 23:00 UTC), not the earlier AP report or regional subtotals. The depth and epicentre are both from Peru's IGP; they are not mixed with a USGS solution.
- **Gulf and Africa:** Keep the coalition's Riyadh and western-region accounts separate from Friday's Jazan interceptions. Bahrain reported an industrial fire without disclosing the site. The Dar Hamar committee's allegations from West Kordofan are attributed, not an independently established toll. Bayelsa's Saturday story is the governor's inquiry into Friday's sinking.
- **Scoreboard and markets:** Wellington is Saturday's **Day 3 stumps**, Las Vegas is **qualifying**, Newcastle is **full time**, and Boca–Mineiro is **in play** at the UTC cutoff. Coinbase's $60,086 is the last BTC-USD trade in the Saturday bucket, not a Sunday tick or a worldwide closing price.

## Reproduce

`node main.ts` (Node 22) checks the committed 1024 × 1024 PNG and copies its bytes to `/output/entry.png`, or to `$MAKEFUN_OUTPUT_DIR/entry.png` when set. No fonts, Python, clock or network are needed at runtime.

To rebuild the press image locally, run `python3 -B tools/render.py` with Pillow and the Noto Serif, Lato and Liberation Sans Narrow fonts. The renderer checks source dates, figure references, pin IDs and separation, text collisions, margins and the 1 MiB limit. `--report /tmp/layout.json` emits geometry for inspection without adding build files to the repository.

Illustrations are original. The local [Natural Earth 1:110m land polygons](https://github.com/nvkelso/natural-earth-vector/blob/v5.1.2/geojson/ne_110m_land.geojson) are [public domain](https://www.naturalearthdata.com/about/terms-of-use/); leader lines preserve the precise dateline anchors when adjacent numbers need separating.
