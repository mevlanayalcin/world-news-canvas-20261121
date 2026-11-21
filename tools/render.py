"""Render the Saturday 21 November 2026 front page (v2).

    python3 tools/render.py [--out entry.png] [--report /tmp/report.json] [--thumb /tmp/thumb.png]

Draws at 2x (2048 px) and downsamples via LANCZOS to 1024 x 1024, then writes
a progressive 4:4:4 JPEG (stored as entry.png, matching main.ts). Strict layout
assertions run on every build: zero text overlaps, zero margin overflows, zero
map pin collisions, and >= 8 px right-margin slack on every brief.
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art  # noqa: E402
import stories as S  # noqa: E402
import worldmap  # noqa: E402

K = 2  # drawing scale (2048 x 2048 -> 1024 x 1024)
W = H = 1024
M = 16
CW = W - 2 * M  # 992

PAPER = "#FAF8F3"
RULE = "#D6CFC0"
INK = "#14181F"
BODY_INK = "#1E232B"
BRIEF_INK = "#121820"
MUTED = "#59606E"
CRIMSON = "#B52323"
MAP_OCEAN = "#13294B"
MAP_GRID = "#223D66"
MAP_LAND = (232, 222, 200, 255)   # #E8DEC8
MAP_COAST = (184, 170, 144, 255)  # #B8AA90
MAP_WATER = (19, 41, 75, 255)     # #13294B

FD = "/usr/share/fonts/truetype"
FONTS = {
    "serif_b": f"{FD}/noto/NotoSerif-Bold.ttf",
    "serif_i": f"{FD}/noto/NotoSerif-Italic.ttf",
    "sans": f"{FD}/lato/Lato-Regular.ttf",
    "sans_m": f"{FD}/lato/Lato-Medium.ttf",
    "sans_b": f"{FD}/lato/Lato-Bold.ttf",
    "sans_k": f"{FD}/lato/Lato-Black.ttf",
    "sans_i": f"{FD}/lato/Lato-Italic.ttf",
    "nar": f"{FD}/liberation/LiberationSansNarrow-Regular.ttf",
    "nar_b": f"{FD}/liberation/LiberationSansNarrow-Bold.ttf",
    "nar_i": f"{FD}/liberation/LiberationSansNarrow-Italic.ttf",
}
_font_cache = {}


def font(key, size):
    k = (key, round(size, 2))
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONTS[key], round(size * K))
    return _font_cache[k]


def region_color(key):
    for k, _, c in S.REGIONS:
        if k == key:
            return c
    raise KeyError(key)


class Board:
    def __init__(self):
        self.img = Image.new("RGB", (W * K, H * K), PAPER)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.texts = []  # (x0, y0, x1, y1, label)
        self.pins = []
        self.fits = []   # (label, right edge, container right, required margin, actual slack)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0, r=0):
        box = [x0 * K, y0 * K, x1 * K, y1 * K]
        kw = dict(fill=fill, outline=outline, width=max(1, round(width * K)) if outline else 0)
        if r:
            self.d.rounded_rectangle(box, radius=r * K, **kw)
        else:
            self.d.rectangle(box, **kw)

    def hline(self, x0, x1, y, color=RULE, width=1.0):
        self.d.line([(x0 * K, y * K), (x1 * K, y * K)], fill=color, width=max(1, round(width * K)))

    def vline(self, x, y0, y1, color=RULE, width=1.0):
        self.d.line([(x * K, y0 * K), (x * K, y1 * K)], fill=color, width=max(1, round(width * K)))

    def circle(self, cx, cy, r, fill, outline=None, width=1.0):
        self.d.ellipse([(cx - r) * K, (cy - r) * K, (cx + r) * K, (cy + r) * K], fill=fill,
                       outline=outline, width=max(1, round(width * K)) if outline else 0)

    def measure(self, s, fkey, size, spacing=0.0):
        f = font(fkey, size)
        if spacing and len(s) > 1:
            return sum(f.getlength(ch) / K for ch in s) + spacing * (len(s) - 1)
        return f.getlength(s) / K

    def text(self, x, y, s, fkey, size, fill=INK, anchor="la", label=None, record=True,
             spacing=0.0):
        f = font(fkey, size)
        if spacing:
            total = self.measure(s, fkey, size, spacing)
            if anchor[0] == "r":
                x -= total
            elif anchor[0] == "m":
                x -= total / 2
            # Use font-metrics ascender/baseline anchor so punctuation ('·', '–', '—') never floats!
            v_anc = "a" if anchor[1] == "t" else anchor[1]
            cx = x
            for ch in s:
                self.d.text((cx * K, y * K), ch, font=f, fill=fill, anchor="l" + v_anc)
                cx += f.getlength(ch) / K + spacing
            bb = self.d.textbbox((x * K, y * K), s, font=f, anchor="l" + v_anc)
            box = (x, bb[1] / K, x + total, bb[3] / K)
        else:
            self.d.text((x * K, y * K), s, font=f, fill=fill, anchor=anchor)
            bb = self.d.textbbox((x * K, y * K), s, font=f, anchor=anchor)
            box = tuple(v / K for v in bb)
        if record:
            self.texts.append(box + (label or s[:40],))
        return box

    def runs(self, x, y, runs, label, anchor_v="s"):
        """Draw [(text, fkey, size, colour)] left to right on one baseline."""
        cx = x
        boxes = []
        for s, fkey, size, col in runs:
            if not s:
                continue
            b = self.text(cx, y, s, fkey, size, col, anchor="l" + anchor_v, label=label, record=False)
            boxes.append(b)
            cx += self.measure(s, fkey, size)
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
               max(b[3] for b in boxes))
        self.texts.append(box + (label,))
        return box, cx

    def fit(self, label, right, limit, margin=0.0):
        slack = limit - right
        self.fits.append((label, round(right, 2), round(limit, 2), round(margin, 2), round(slack, 2)))
        if right > limit - margin + 1e-6:
            raise SystemExit(
                f"LAYOUT: '{label}' ends at {right:.1f}, limit {limit - margin:.1f} (slack {slack:.1f})"
            )


def rich_wrap(board, tokens, maxw):
    """tokens: [(word, fkey, size, colour)] -> lines of runs, greedy wrap on spaces."""
    lines, cur, curw = [], [], 0.0
    for word, fkey, size, col in tokens:
        ww = board.measure(word, fkey, size)
        sp = board.measure(" ", fkey, size) if cur else 0.0
        if cur and curw + sp + ww > maxw:
            lines.append(cur)
            cur, curw = [], 0.0
            sp = 0.0
        if cur:
            cur.append((" ", fkey, size, col))
        cur.append((word, fkey, size, col))
        curw += sp + ww
    if cur:
        lines.append(cur)
    return lines


def tokens(text, fkey, size, col):
    return [(w, fkey, size, col) for w in text.split()]


def draw_wrapped(board, x, y, lines, lh, label, maxw):
    for i, ln in enumerate(lines):
        _, right = board.runs(x, y + i * lh, ln, f"{label}:{i}")
        board.fit(f"{label}:{i}", right, x + maxw)
    return y + (len(lines) - 1) * lh


# ------------------------------------------------------------------ blocks
def masthead(b):
    counts = S.region_counts()
    beats = len({s["beat"] for s in S.STORIES})
    bl = b.text(M, 12, "THE WORLD IN ONE DAY", "sans_k", 10.5, CRIMSON, anchor="lt", spacing=1.4,
                label="kicker")
    stats = (f"{len(S.STORIES)} STORIES · {len(counts)} REGIONS · {beats} BEATS · "
             f"EVERY ONE DATED {S.DAY_LABEL.upper()}")
    br = b.text(W - M, 12, stats, "sans_b", 9.2, INK, anchor="rt", label="stats")
    if bl[2] + 12 > br[0]:
        raise SystemExit(f"LAYOUT: masthead top bar collides ({bl[2]:.1f} vs {br[0]:.1f})")
    b.hline(M, W - M, 25, INK, 1.2)

    # Auto-size commanding serif masthead from 69px down to fit within CW - 8
    tsize = 69.0
    while tsize > 48.0 and b.measure(S.DAY_LABEL, "serif_b", tsize) > CW - 8:
        tsize -= 0.5
    b.text(W / 2, 53.5, S.DAY_LABEL, "serif_b", tsize, INK, anchor="mm", label="title")

    deck_size = 11.8
    while deck_size > 10.0 and b.measure(S.DECK, "serif_i", deck_size) > CW - 4:
        deck_size -= 0.2
    b.text(W / 2, 102.0, S.DECK, "serif_i", deck_size, "#262B33", anchor="mm", label="deck")
    b.fit("deck", b.measure(S.DECK, "serif_i", deck_size), CW)
    b.hline(M, W - M, 112, INK, 1.2)
    b.hline(M, W - M, 114.5, INK, 0.5)
    return tsize


def kpi_row(b, y0=118, y1=157):
    n = len(S.KPIS)
    cw = CW / n
    for i, k in enumerate(S.KPIS):
        x = M + i * cw
        # Bold 3px crimson vertical left accent bar
        b.rect(x + 1.0, y0 + 2, x + 4.0, y1 - 2, fill=CRIMSON)
        bf = b.text(x + 10, y0 - 1.5, k["figure"], "serif_b", 21.5, INK, anchor="lt", label=f"kpi{i}")
        b.fit(f"kpi{i}", bf[2], x + cw, 4)
        for j, cap in enumerate(k["caption"]):
            bx = b.text(x + 10, y0 + 21.5 + j * 10.0, cap, "sans", 9.3, BODY_INK, anchor="lt",
                        label=f"kpi{i}c{j}")
            b.fit(f"kpi{i}c{j}", bx[2], x + cw, 4)


def region_bar(b, y0=161, y1=175):
    counts = S.region_counts()
    total = sum(counts.values())
    assert total == len(S.STORIES) == 39

    # Proportional widths with floor of 82px per segment, renormalized to exact CW
    floor_w = 82.0
    keys = [k for k, _, _ in S.REGIONS]
    widths = {k: CW * counts[k] / total for k in keys}
    for _ in range(10):
        locked = {k: floor_w for k, w in widths.items() if w <= floor_w}
        free = [k for k in keys if k not in locked]
        rem = CW - sum(locked.values())
        free_sum = sum(counts[k] for k in free)
        new_w = dict(locked)
        for k in free:
            new_w[k] = rem * counts[k] / free_sum
        if all(abs(new_w[k] - widths[k]) < 1e-6 for k in keys):
            widths = new_w
            break
        widths = new_w

    x = float(M)
    for idx, (key, label, col) in enumerate(S.REGIONS):
        seg = (W - M - x) if idx == len(S.REGIONS) - 1 else widths[key]
        x0 = x + (0.6 if idx > 0 else 0.0)
        x1 = x + seg - (0.6 if idx < len(S.REGIONS) - 1 else 0.0)
        b.rect(x0, y0, x1, y1, fill=col)
        txt = f"{label} {counts[key]}"
        bx = b.text(x + seg / 2, (y0 + y1) / 2 + 0.3, txt, "sans_k", 8.8, "#FFFFFF", anchor="mm",
                    label=f"rb-{key}")
        b.fit(f"rb-{key}", bx[2], x + seg, 3)
        x += seg


def art_banner(b, x, y, text, size, h, max_w):
    sz = size
    pad_x = 7.0 if size >= 15 else 5.5
    while sz > 10.5 and (b.measure(text, "sans_k", sz) + 2 * pad_x) > max_w:
        sz -= 0.25
    tw = b.measure(text, "sans_k", sz) + 2 * pad_x
    # Subtle drop shadow for crisp pop on any sky
    b.rect(x + 1.2, y + 1.4, x + tw + 1.2, y + h + 1.4, fill=(0, 0, 0, 80))
    b.rect(x, y, x + tw, y + h, fill=CRIMSON, outline="#FFFFFF", width=1.0)
    b.text(x + tw / 2, y + h / 2 + 0.4, text, "sans_k", sz, "#FFFFFF", anchor="mm",
           label=f"banner:{text}")
    return tw


def art_subchip(b, x, y, text, h=17):
    pad_x = 6.0
    tw = b.measure(text, "sans_b", 10.2) + 2 * pad_x
    b.rect(x + 1.0, y + 1.2, x + tw + 1.0, y + h + 1.2, fill=(0, 0, 0, 55))
    b.rect(x, y, x + tw, y + h, fill="#FFFFFF", outline=(20, 24, 31, 140), width=0.6)
    b.text(x + tw / 2, y + h / 2 + 0.2, text, "sans_b", 10.2, INK, anchor="mm",
           label=f"sub:{text}")
    return tw


def art_attrib(b, x, y_bot, w, text, align_right, size, h):
    pad_x = 5.5
    tw = b.measure(text, "sans_b", size) + 2 * pad_x
    x0 = (x + w - tw) if align_right else x
    x1 = (x + w) if align_right else (x + tw)
    b.rect(x0, y_bot - h, x1, y_bot, fill=(20, 24, 31, 235))
    b.text((x0 + x1) / 2, y_bot - h / 2 + 0.2, text, "sans_b", size, "#FFFFFF", anchor="mm",
           label=f"chip:{text}")


def meta_line(b, x, y, w, st, size, badge_r):
    col = region_color(st["region"])
    b.circle(x + badge_r, y, badge_r, col)
    b.text(x + badge_r, y + 0.3, str(st["id"]), "sans_k", badge_r * 1.15, "#FFFFFF", anchor="mm",
           label=f"badge{st['id']}")
    label = f"{st['place']} · {st['beat'].upper()}"
    tx = x + badge_r * 2 + 5
    avail = (x + w) - tx
    sz = size
    fkey = "sans_k"
    while sz > 6.8 and b.measure(label, fkey, sz) > avail - 1:
        sz -= 0.2
    bx = b.text(tx, y + 0.3, label, fkey, sz, col, anchor="lm", label=f"dateline{st['id']}")
    b.fit(f"dateline{st['id']}", bx[2], x + w, 0.5)


def card(b, st, x, y, w, art_h, lead):
    im = art.draw_scene(st["id"], w, art_h, out_scale=K)
    b.img.paste(im, (round(x * K), round(y * K)))
    b.rect(x, y, x + w, y + art_h, outline="#BEB6A4", width=0.6)

    if lead:
        art_banner(b, x + 5, y + 5, st["banner"], 17.0, 25, w - 10)
        art_subchip(b, x + 5, y + 34, st["sub"], h=17)
        art_attrib(b, x, y + art_h, w, st["chip"], align_right=False, size=8.5, h=15)
    else:
        art_banner(b, x + 4, y + 4, st["banner"], 12.6, 19, w - 8)
        art_attrib(b, x, y + art_h, w, st["chip"], align_right=True, size=7.6, h=13)

    my = y + art_h + (10.0 if lead else 8.5)
    meta_line(b, x, my, w, st, 8.8 if lead else 7.6, 6.8 if lead else 5.8)

    hy = my + (9.5 if lead else 8.2)
    hsize, hlh = (19.2, 20.6) if lead else (13.0, 14.5)
    hl = rich_wrap(b, tokens(st["headline"], "serif_b", hsize, INK), w)
    if len(hl) > 2:
        raise SystemExit(f"LAYOUT: headline {st['id']} needs {len(hl)} lines (max 2)")
    for i, ln in enumerate(hl):
        _, right = b.runs(x, hy + hsize * 0.94 + i * hlh, ln, f"h{st['id']}:{i}")
        b.fit(f"h{st['id']}:{i}", right, x + w)

    sy = hy + hsize * 0.94 + (len(hl) - 1) * hlh + (15.0 if lead else 12.6)
    ssize, slh = (10.0, 11.9) if lead else (8.9, 10.6)
    toks = tokens(st["summary"], "sans", ssize, "#262C36")
    src = f"({st['sources']})".split()
    toks += [(t, "sans_i", ssize, MUTED) for t in src]
    sl = rich_wrap(b, toks, w)
    limit = 3 if lead else 2
    if len(sl) > limit:
        raise SystemExit(f"LAYOUT: summary {st['id']} needs {len(sl)} lines (max {limit})")
    end = draw_wrapped(b, x, sy, sl, slh, f"s{st['id']}", w)
    return end


def world_map(b, x, y, w, h):
    b.text(x, y, "GLOBAL ATLAS · PINS 1–13 & BRIEFS 14–39", "sans_k", 9.5, INK, anchor="lt",
           spacing=0.4, label="map-title")
    my = y + 16
    box = (x, my, w, h)
    b.rect(x, my, x + w, my + h, fill=MAP_OCEAN, outline="#0D1E38", width=0.8)

    # Subtle graticule lines over deep navy ocean
    for lat in (-30, 0, 30, 60):
        _, py = worldmap.project(0, lat, box)
        b.hline(x, x + w, py, MAP_GRID, 0.5)
    for lon in (-120, -60, 0, 60, 120, 180):
        px, _ = worldmap.project(lon, 0, box)
        b.vline(px, my, my + h, MAP_GRID, 0.5)

    # Clip land & inland seas cleanly inside map box
    layer = Image.new("RGBA", b.img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for pts in worldmap.LAND.values():
        ld.polygon([tuple(v * K for v in worldmap.project(lo, la, box)) for lo, la in pts],
                   fill=MAP_LAND, outline=MAP_COAST)
    for pts in worldmap.WATER.values():
        ld.polygon([tuple(v * K for v in worldmap.project(lo, la, box)) for lo, la in pts],
                   fill=MAP_WATER, outline=MAP_COAST)
    mask = Image.new("L", b.img.size, 0)
    ImageDraw.Draw(mask).rectangle([x * K, my * K, (x + w) * K, (my + h) * K], fill=255)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", b.img.size, 0), mask)
    layer.putalpha(alpha)
    b.img.paste(layer, (0, 0), layer)
    b.d = ImageDraw.Draw(b.img, "RGBA")
    # Crisp dark frame around map box
    b.rect(x, my, x + w, my + h, outline="#0D1E38", width=0.8)

    # First plot briefs 14-39 as crisp 2.6px region-colored dots with 0.6px white rings
    for st in S.STORIES[13:]:
        if st.get("lat") is None or st.get("lon") is None:
            continue
        dx, dy = worldmap.project(st["lon"], st["lat"], box)
        if not (x + 3 <= dx <= x + w - 3 and my + 3 <= dy <= my + h - 3):
            raise SystemExit(f"LAYOUT: brief dot {st['id']} outside map box ({dx:.1f}, {dy:.1f})")
        b.circle(dx, dy, 2.6, region_color(st["region"]), "#FFFFFF", 0.6)

    # Numbered pins 1-13 with collision-avoidance solver & subtle white leader lines
    R = 6.6
    gap = 2 * R + 1.8
    placed = []
    truths = []
    for st in S.STORIES[:13]:
        tx, ty = worldmap.project(st["lon"], st["lat"], box)
        truths.append((tx, ty))

    for idx, st in enumerate(S.STORIES[:13]):
        tx, ty = truths[idx]
        best = None
        for ring in range(0, 10):
            rr = ring * 7.8
            for k in range(16 if ring else 1):
                a = math.radians(-90 + k * 22.5 + (ring % 2) * 11.25)
                cx, cy = tx + math.cos(a) * rr, ty + math.sin(a) * rr
                if not (x + R + 1.5 <= cx <= x + w - R - 1.5 and my + R + 1.5 <= cy <= my + h - R - 1.5):
                    continue
                if any(math.hypot(cx - px, cy - py) < gap for px, py, _ in placed):
                    continue
                best = (cx, cy)
                break
            if best:
                break
        if best is None:
            raise SystemExit(f"LAYOUT: no room for pin {st['id']}")
        placed.append((best[0], best[1], st))

    # Verify zero pin collisions strictly
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            dist = math.hypot(placed[i][0] - placed[j][0], placed[i][1] - placed[j][1])
            if dist < 2 * R + 0.5:
                raise SystemExit(f"LAYOUT: pins {placed[i][2]['id']} and {placed[j][2]['id']} collide ({dist:.1f})")

    for (cx, cy, st), (tx, ty) in zip(placed, truths):
        if math.hypot(cx - tx, cy - ty) > 0.5:
            b.d.line([(tx * K, ty * K), (cx * K, cy * K)], fill=(255, 255, 255, 195),
                     width=max(1, round(0.9 * K)))
            b.circle(tx, ty, 1.8, "#FFFFFF", "#13294B", 0.5)
    for cx, cy, st in placed:
        b.circle(cx, cy, R, region_color(st["region"]), "#FFFFFF", 1.0)
        b.text(cx, cy + 0.3, str(st["id"]), "sans_k", 7.6, "#FFFFFF", anchor="mm", record=False)
        b.pins.append((round(cx, 2), round(cy, 2), R, st["id"]))

    # Caption + balanced 2-row 7-region legend (4 + 3) under map
    cap_y = my + h + 11
    b.text(x, cap_y, "Numbered pins: stories 1–13  ·  Dots: briefs 14–39", "sans_b", 7.8, "#444C58",
           anchor="lm", label="map-cap")
    ky = cap_y + 14.5
    for row_items in (S.REGIONS[:4], S.REGIONS[4:]):
        kx = x
        for key, label, col in row_items:
            b.circle(kx + 3.5, ky, 3.6, col)
            bx = b.text(kx + 9.5, ky + 0.2, label, "sans_b", 7.8, MUTED, anchor="lm", label=f"key-{key}")
            b.fit(f"map-key-{key}", bx[2], x + w)
            kx = bx[2] + 10.5
        ky += 13.5
    return ky - 4


def briefs(b, x, y, w):
    b.text(x, y, "ALSO ON SATURDAY 21 NOVEMBER 2026 — 26 MORE STORIES", "sans_k", 9.5, INK,
           anchor="lt", spacing=0.4, label="briefs-title")
    rows = 13
    col_gap = 14.0
    colw = (w - col_gap) / 2  # 315px when w=644
    lh = 17.0
    items = S.STORIES[13:]
    assert len(items) == 26
    for i, st in enumerate(items):
        c, r = divmod(i, rows)
        cx = x + c * (colw + col_gap)
        cy = y + 25.0 + r * lh
        col = region_color(st["region"])
        b.circle(cx + 6.5, cy, 6.5, col)
        b.text(cx + 6.5, cy + 0.3, str(st["id"]), "sans_k", 7.0, "#FFFFFF", anchor="mm",
               label=f"bd{st['id']}")
        runs = [
            (st["place"], "nar_b", 11.0, BRIEF_INK),
            (" " + st["brief"], "nar", 11.0, BRIEF_INK),
            ("  " + st["sources"], "nar_i", 10.6, MUTED),
        ]
        _, right = b.runs(cx + 16.5, cy + 0.2, runs, f"brief{st['id']}", anchor_v="m")
        b.fit(f"brief{st['id']}", right, cx + colw, 8.0)
        if r < rows - 1:
            b.hline(cx + 16.5, cx + colw, cy + lh / 2, "#EAE4D7", 0.5)
    end_y = y + 25.0 + (rows - 1) * lh + 8.0
    b.vline(x + colw + col_gap / 2, y + 17, end_y, RULE, 0.7)
    return end_y


def _split_lead(toks):
    out = []
    for s, f, z, c in toks:
        for w in s.split(" "):
            if w:
                out.append((w, f, z, c))
    return out


def date_check(b, y0, y1):
    b.rect(M, y0, W - M, y1, fill="#FFF7F5", outline=CRIMSON, width=1.1, r=3)
    pw = 78
    ym = (y0 + y1) / 2
    b.rect(M + 7, ym - 9, M + 7 + pw, ym + 9, fill=CRIMSON, r=8.5)
    b.text(M + 7 + pw / 2, ym + 0.3, "DATE CHECK", "sans_k", 8.5, "#FFFFFF", anchor="mm",
           label="dc-pill")
    x = M + pw + 16
    maxw = W - M - 8 - x
    t1 = [("Excluded (Fri 20 Nov):", "nar_b", 10.0, CRIMSON)] + \
        [(w, "nar", 10.0, INK) for w in " · ".join(S.EXCLUDED_FRIDAY).split(" ")]
    t2 = [("Not yet confirmed / upcoming:", "nar_b", 10.0, CRIMSON)] + \
        [(w, "nar", 10.0, INK) for w in " · ".join(S.NOT_YET).split(" ")]
    l1 = rich_wrap(b, _split_lead(t1), maxw)
    l2 = rich_wrap(b, _split_lead(t2), maxw)
    lines = l1 + l2
    if len(lines) > 3:
        raise SystemExit(f"LAYOUT: date check needs {len(lines)} lines (max 3)")
    lh = (y1 - y0 - 8) / max(len(lines), 3)
    draw_wrapped(b, x, y0 + 5 + lh * 0.72, lines, lh, "datecheck", maxw)


def footer(b, y):
    left = ("Every story happened, or was first reported, on Saturday 21 November 2026. "
            "Officials' counts and single-side claims are attributed.")
    right = "Sources named beside each story · Original drawings"
    bl = b.text(M, y, left, "sans_i", 8.4, "#3A404A", anchor="lm", label="footer-l")
    br = b.text(W - M, y, right, "sans_b", 8.4, "#3A404A", anchor="rm", label="footer-r")
    if bl[2] + 12 > br[0]:
        raise SystemExit(f"LAYOUT: footer halves collide ({bl[2]:.1f} vs {br[0]:.1f})")


def overlaps(texts):
    bad = []
    for i in range(len(texts)):
        a = texts[i]
        for j in range(i + 1, len(texts)):
            c = texts[j]
            if a[0] < c[2] - 0.25 and c[0] < a[2] - 0.25 and a[1] < c[3] - 0.25 and c[1] < a[3] - 0.25:
                bad.append((a[4], c[4]))
    return bad


def build():
    S.validate()
    b = Board()
    tsize = masthead(b)
    kpi_row(b, 118, 157)
    region_bar(b, 160, 175)

    # Lead cards 1-3
    y = 181
    lw, gap = 320, (CW - 3 * 320) / 2
    ends = []
    for i, st in enumerate(S.STORIES[:3]):
        ends.append(card(b, st, M + i * (lw + gap), y, lw, 114, True))
    y = max(ends) + 7.5
    b.hline(M, W - M, y, RULE, 0.85)
    y += 6.5

    # Secondary cards 4-13 (2 rows x 5)
    sw, sgap = 188, (CW - 5 * 188) / 4
    for row in range(2):
        ends = []
        for c in range(5):
            st = S.STORIES[3 + row * 5 + c]
            ends.append(card(b, st, M + c * (sw + sgap), y, sw, 66, False))
        y = max(ends) + 7.0
        b.hline(M, W - M, y, RULE, 0.85)
        y += 6.5

    bottom_top = y
    map_w, map_h = 330, 178
    map_end = world_map(b, M, bottom_top, map_w, map_h)
    br_end = briefs(b, M + map_w + 18, bottom_top, CW - map_w - 18)
    b.vline(M + map_w + 9, bottom_top, max(map_end, br_end), RULE, 0.8)

    y = max(map_end, br_end) + 8
    dc_h = 48
    if y + dc_h + 16 > H:
        dc_h = max(44, H - y - 16)
    date_check(b, y, y + dc_h)
    fy = y + dc_h + 12
    if fy + 6 > H - 2:
        raise SystemExit(f"LAYOUT: page overflows ({fy:.1f})")
    footer(b, fy)

    bad = overlaps(b.texts)
    if bad:
        raise SystemExit(f"LAYOUT: overlapping text {bad[:8]}")
    for t in b.texts:
        if t[0] < M - 0.5 or t[2] > W - M + 0.5 or t[1] < 0 or t[3] > H:
            raise SystemExit(f"LAYOUT: text outside page margins {t}")

    out = b.img.resize((W, H), Image.LANCZOS)
    brief_slacks = [f[4] for f in b.fits if f[0].startswith("brief")]
    report = dict(
        texts=b.texts,
        pins=b.pins,
        fits=b.fits,
        masthead_px=tsize,
        bottom_top=round(bottom_top, 2),
        map_end=round(map_end, 2),
        briefs_end=round(br_end, 2),
        date_check_y0=round(y, 2),
        date_check_y1=round(y + dc_h, 2),
        footer_y=round(fy, 2),
        min_brief_slack=min(brief_slacks) if brief_slacks else None,
        story_count=len(S.STORIES),
        region_counts=S.region_counts(),
    )
    return out, report


def save_jpeg(img, path, quality=91):
    img.save(path, "JPEG", quality=quality, subsampling=0, progressive=True, optimize=True)
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--out", default=os.path.join(root, "entry.png"))
    ap.add_argument("--report")
    ap.add_argument("--thumb")
    ap.add_argument("--quality", type=int, default=91)
    a = ap.parse_args()
    img, report = build()
    q = a.quality
    size = save_jpeg(img, a.out, q)
    while size > 450 * 1024 and q > 82:
        q -= 1
        size = save_jpeg(img, a.out, q)
    if a.thumb:
        img.resize((300, 300), Image.LANCZOS).save(a.thumb, "PNG")
    report.update(quality=q, size=size)
    if a.report:
        with open(a.report, "w") as fh:
            json.dump(report, fh, indent=2)
    print(
        f"wrote {a.out}: {size} bytes ({size / 1024:.1f} KB), JPEG q{q}, "
        f"masthead={report['masthead_px']}px, min_brief_slack={report['min_brief_slack']}px, "
        f"bottom_top={report['bottom_top']}, dc={report['date_check_y0']}..{report['date_check_y1']}, "
        f"footer={report['footer_y']}, {len(report['texts'])} text boxes, {len(report['pins'])} pins"
    )


if __name__ == "__main__":
    main()
