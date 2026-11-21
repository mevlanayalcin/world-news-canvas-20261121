"""Render the Saturday 21 November 2026 Broadsheet Atlas (v3).

    python3 tools/render.py [--out entry.png] [--report /tmp/report.json] [--thumb /tmp/thumb.png]

Draws at 2x (2048 px) and downsamples via LANCZOS to 1024 x 1024, then writes
a deterministic progressive 4:4:4 JPEG stored as entry.png (matching main.ts).
Strict layout assertions run on every build: zero text overlaps, zero margin
overflows, zero map pin collisions, and >= 8 px right-margin slack on every brief.
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

# Signature v3 Archival Broadsheet Palette
PAPER = "#FAF6EE"
TILE_BG = "#F2ECE0"
TILE_BORDER = "#D7CEBC"
RULE = "#D5CCB9"
INK = "#131B26"
BODY_INK = "#1E2733"
BRIEF_INK = "#131C26"
MUTED = "#56606E"
FOLIO_BG = "#182A40"
FOLIO_GOLD = "#F0C66E"
VERMILION = "#A82824"
SLATE_INDIGO = "#1F4A6E"

MAP_OCEAN = "#18364A"
MAP_GRID = "#254A63"
MAP_LAND = (239, 231, 214, 255)   # #EFE7D6
MAP_COAST = (184, 172, 150, 255)  # #B8AC96
MAP_WATER = (24, 54, 74, 255)     # #18364A

TAG_STYLE = {
    "CONFIRMED": ("#156E5E", "#E6F5F1"),
    "OFFICIAL":  ("#1F4A6E", "#E8F0F7"),
    "REPORTED":  ("#9A5B0A", "#FDF3E3"),
    "CLAIM":     ("#6A3F7A", "#F4ECF8"),
}

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
            # Always align tracked glyphs on font-metrics ascender/middle/baseline so '·' / '–' never float
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

    # Signature Midnight Slate-Indigo prestige folio bar
    b.rect(M, 8, W - M, 25, fill=FOLIO_BG)
    bl = b.text(M + 8, 16.7, "GLOBAL DISPATCH · EDITION 21 NOV", "sans_k", 8.6, FOLIO_GOLD,
                anchor="lm", spacing=1.0, label="kicker")
    stats = (f"{len(S.STORIES)} VERIFIED STORIES · {len(counts)} REGIONS · {beats} BEATS · "
             f"{S.DAY_LABEL.upper()}")
    br = b.text(W - M - 8, 16.7, stats, "sans_b", 8.4, "#F5F1E8", anchor="rm", label="stats")
    if bl[2] + 12 > br[0]:
        raise SystemExit(f"LAYOUT: masthead folio bar collides ({bl[2]:.1f} vs {br[0]:.1f})")

    # Commanding bold serif masthead spanning page width
    tsize = 66.5
    while tsize > 48.0 and b.measure(S.DAY_LABEL, "serif_b", tsize) > CW - 10:
        tsize -= 0.5
    b.text(W / 2, 51.0, S.DAY_LABEL, "serif_b", tsize, INK, anchor="mm", label="title")

    deck_size = 11.4
    while deck_size > 9.8 and b.measure(S.DECK, "serif_i", deck_size) > CW - 6:
        deck_size -= 0.2
    b.text(W / 2, 100.5, S.DECK, "serif_i", deck_size, "#293342", anchor="mm", label="deck")
    b.fit("deck", b.measure(S.DECK, "serif_i", deck_size), CW)
    b.hline(M, W - M, 109.5, VERMILION, 1.5)
    b.hline(M, W - M, 112.0, INK, 0.6)
    return tsize


def kpi_row(b, y0=115, y1=158):
    n = len(S.KPIS)
    gap = 6.0
    tw = (CW - (n - 1) * gap) / n
    for i, k in enumerate(S.KPIS):
        x = M + i * (tw + gap)
        accent = VERMILION if i % 2 == 0 else SLATE_INDIGO
        b.rect(x, y0, x + tw, y1, fill=TILE_BG, outline=TILE_BORDER, width=0.7)
        b.rect(x, y0, x + tw, y0 + 2.6, fill=accent)
        bf = b.text(x + 7.5, y0 + 5.0, k["figure"], "serif_b", 20.0, INK, anchor="lt",
                    label=f"kpi{i}")
        b.fit(f"kpi{i}", bf[2], x + tw, 4)
        for j, cap in enumerate(k["caption"]):
            bx = b.text(x + 7.5, y0 + 25.0 + j * 9.5, cap, "sans", 8.8, BODY_INK, anchor="lt",
                        label=f"kpi{i}c{j}")
            b.fit(f"kpi{i}c{j}", bx[2], x + tw, 4)


def region_bar(b, y0=162, y1=176):
    counts = S.region_counts()
    total = sum(counts.values())
    assert total == len(S.STORIES) == 39

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
        bx = b.text(x + seg / 2, (y0 + y1) / 2 + 0.3, txt, "sans_k", 8.4, "#FFFFFF", anchor="mm",
                    label=f"rb-{key}")
        b.fit(f"rb-{key}", bx[2], x + seg, 3)
        x += seg


def art_attrib(b, x, y_bot, w, text, size, h):
    pad_x = 5.0
    tw = b.measure(text, "sans_b", size) + 2 * pad_x
    x0 = x + w - tw
    x1 = x + w
    b.rect(x0, y_bot - h, x1, y_bot, fill=(19, 27, 38, 225))
    b.text((x0 + x1) / 2, y_bot - h / 2 + 0.2, text, "sans_b", size, "#F5F2EB", anchor="mm",
           label=f"chip:{text}")


def tag_pill(b, xr, cy, tag, size, h):
    fg, bg = TAG_STYLE[tag]
    pad_x = 5.0 if size >= 7.0 else 4.0
    tw = b.measure(tag, "sans_k", size) + 2 * pad_x
    x0 = xr - tw
    b.rect(x0, cy - h / 2, xr, cy + h / 2, fill=bg, outline=fg, width=0.75, r=h / 2)
    b.text((x0 + xr) / 2, cy + 0.25, tag, "sans_k", size, fg, anchor="mm", label=f"tag:{tag}")
    return x0


def meta_line(b, x, y, w, st, size, badge_r, lead):
    col = region_color(st["region"])
    b.circle(x + badge_r, y, badge_r, col)
    b.text(x + badge_r, y + 0.3, str(st["id"]), "sans_k", badge_r * 1.15, "#FFFFFF", anchor="mm",
           label=f"badge{st['id']}")
    px0 = tag_pill(b, x + w, y, st["tag"], 7.1 if lead else 6.4, 13.0 if lead else 11.6)
    label = f"{st['place']} · {st['beat'].upper()}" if lead else st["place"]
    tx = x + badge_r * 2 + 4.5
    avail = px0 - tx - 4.0
    sz = size
    while sz > 6.2 and b.measure(label, "sans_k", sz) > avail:
        sz -= 0.2
    bx = b.text(tx, y + 0.25, label, "sans_k", sz, col, anchor="lm", label=f"dateline{st['id']}")
    b.fit(f"dateline{st['id']}", bx[2], px0, 3.0)


def card(b, st, x, y, w, art_h, lead):
    col = region_color(st["region"])
    im = art.draw_scene(st["id"], w, art_h, out_scale=K)
    b.img.paste(im, (round(x * K), round(y * K)))
    b.rect(x, y, x + w, y + art_h, outline="#C4BAA7", width=0.6)

    if lead:
        art_attrib(b, x, y + art_h, w, st["chip"], size=7.6, h=12.5)
        # Full-width deep-vermilion kicker band RIGHT BELOW art (zero art collision, massive 300px pop!)
        bh = 23.0
        by0 = y + art_h
        b.rect(x, by0, x + w, by0 + bh, fill=VERMILION)
        # Crisp warm-ivory right stat pill inside banner band
        sub_txt = st["sub"]
        spw = b.measure(sub_txt, "sans_k", 9.0) + 11.0
        sx0 = x + w - spw - 4.0
        b.rect(sx0, by0 + 3.2, x + w - 4.0, by0 + bh - 3.2, fill=PAPER, r=2.0)
        b.text((sx0 + x + w - 4.0) / 2, by0 + bh / 2 + 0.2, sub_txt, "sans_k", 9.0, INK,
               anchor="mm", label=f"sub:{st['id']}")
        # Giant bold white kicker headline left-aligned
        bsz = 15.2
        while bsz > 11.5 and b.measure(st["banner"], "sans_k", bsz) > (sx0 - x - 12.0):
            bsz -= 0.25
        bx = b.text(x + 7.0, by0 + bh / 2 + 0.35, st["banner"], "sans_k", bsz, "#FFFFFF",
                    anchor="lm", label=f"banner:{st['id']}")
        b.fit(f"banner:{st['id']}", bx[2], sx0, 4.0)
        bar_bot = by0 + bh
    else:
        art_attrib(b, x, y + art_h, w, st["chip"], size=6.8, h=11.0)
        # Full-width region-colored kicker band RIGHT BELOW art
        bh = 18.0
        by0 = y + art_h
        b.rect(x, by0, x + w, by0 + bh, fill=col)
        bsz = 11.8
        while bsz > 9.4 and b.measure(st["banner"], "sans_k", bsz) > (w - 10.0):
            bsz -= 0.2
        bx = b.text(x + 5.5, by0 + bh / 2 + 0.3, st["banner"], "sans_k", bsz, "#FFFFFF",
                    anchor="lm", label=f"banner:{st['id']}")
        b.fit(f"banner:{st['id']}", bx[2], x + w, 4.0)
        bar_bot = by0 + bh

    my = bar_bot + (9.5 if lead else 8.5)
    meta_line(b, x, my, w, st, 8.1 if lead else 7.2, 6.2 if lead else 5.2, lead)

    hy = my + (8.6 if lead else 7.2)
    hsize, hlh = (17.5, 19.2) if lead else (12.2, 13.5)
    hl = rich_wrap(b, tokens(st["headline"], "serif_b", hsize, INK), w)
    if len(hl) > 2:
        raise SystemExit(f"LAYOUT: headline {st['id']} needs {len(hl)} lines (max 2)")
    for i, ln in enumerate(hl):
        _, right = b.runs(x, hy + hsize * 0.94 + i * hlh, ln, f"h{st['id']}:{i}")
        b.fit(f"h{st['id']}:{i}", right, x + w)

    sy = hy + hsize * 0.94 + (len(hl) - 1) * hlh + (14.2 if lead else 11.6)
    ssize, slh = (9.6, 11.3) if lead else (8.5, 10.1)
    toks = tokens(st["summary"], "sans", ssize, "#252E3A")
    src = f"({st['sources']})".split()
    toks += [(t, "sans_i", ssize, MUTED) for t in src]
    sl = rich_wrap(b, toks, w)
    limit = 3 if lead else 2
    if len(sl) > limit:
        raise SystemExit(f"LAYOUT: summary {st['id']} needs {len(sl)} lines (max {limit})")
    end = draw_wrapped(b, x, sy, sl, slh, f"s{st['id']}", w)
    return end


def world_map(b, x, y, w, h):
    b.text(x, y, "WORLD ATLAS · ALL 39 STORIES MAPPED", "sans_k", 9.1, INK, anchor="lt",
           spacing=0.4, label="map-title")
    my = y + 15.0
    box = (x, my, w, h)
    b.rect(x, my, x + w, my + h, fill=MAP_OCEAN, outline="#102535", width=0.8)

    for lat in (-30, 0, 30, 60):
        _, py = worldmap.project(0, lat, box)
        b.hline(x, x + w, py, MAP_GRID, 0.5)
    for lon in (-120, -60, 0, 60, 120, 180):
        px, _ = worldmap.project(lon, 0, box)
        b.vline(px, my, my + h, MAP_GRID, 0.5)

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
    b.rect(x, my, x + w, my + h, outline="#102535", width=0.8)

    # Briefs 14-39 as crisp white-ringed regional dots underneath pins 1-13
    for st in S.STORIES[13:]:
        if st.get("lat") is None or st.get("lon") is None:
            continue
        dx, dy = worldmap.project(st["lon"], st["lat"], box)
        if not (x + 3 <= dx <= x + w - 3 and my + 3 <= dy <= my + h - 3):
            raise SystemExit(f"LAYOUT: brief dot {st['id']} outside map box ({dx:.1f}, {dy:.1f})")
        b.circle(dx, dy, 2.6, region_color(st["region"]), "#FFFFFF", 0.6)

    # Collision-free numbered pins 1-13 with crisp white leader lines
    R = 6.5
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

    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            dist = math.hypot(placed[i][0] - placed[j][0], placed[i][1] - placed[j][1])
            if dist < 2 * R + 0.5:
                raise SystemExit(f"LAYOUT: pins {placed[i][2]['id']} and {placed[j][2]['id']} collide")

    for (cx, cy, st), (tx, ty) in zip(placed, truths):
        if math.hypot(cx - tx, cy - ty) > 0.5:
            b.d.line([(tx * K, ty * K), (cx * K, cy * K)], fill=(255, 255, 255, 200),
                     width=max(1, round(0.9 * K)))
            b.circle(tx, ty, 1.8, "#FFFFFF", MAP_OCEAN, 0.5)
    for cx, cy, st in placed:
        b.circle(cx, cy, R, region_color(st["region"]), "#FFFFFF", 1.0)
        b.text(cx, cy + 0.3, str(st["id"]), "sans_k", 7.4, "#FFFFFF", anchor="mm", record=False)
        b.pins.append((round(cx, 2), round(cy, 2), R, st["id"]))

    # Caption + balanced 2-row 7-region legend (4 + 3)
    cap_y = my + h + 9.5
    b.text(x, cap_y, "Numbered pins: illustrated 1–13  ·  Dots: briefs 14–39", "sans_b", 7.6,
           "#3C4654", anchor="lm", label="map-cap")
    ky = cap_y + 13.0
    for row_items in (S.REGIONS[:4], S.REGIONS[4:]):
        kx = x
        for key, label, col in row_items:
            b.circle(kx + 3.5, ky, 3.4, col)
            bx = b.text(kx + 9.0, ky + 0.2, label, "sans_b", 7.5, MUTED, anchor="lm", label=f"key-{key}")
            b.fit(f"map-key-{key}", bx[2], x + w)
            kx = bx[2] + 9.5
        ky += 12.2
    return ky - 4


def briefs(b, x, y, w):
    b.text(x, y, "ALSO ON SATURDAY 21 NOVEMBER 2026 — 26 MORE STORIES", "sans_k", 9.1, INK,
           anchor="lt", spacing=0.4, label="briefs-title")
    rows = 13
    col_gap = 14.0
    colw = (w - col_gap) / 2
    lh = 16.2
    items = S.STORIES[13:]
    assert len(items) == 26
    for i, st in enumerate(items):
        c, r = divmod(i, rows)
        cx = x + c * (colw + col_gap)
        cy = y + 23.0 + r * lh
        col = region_color(st["region"])
        b.circle(cx + 6.2, cy, 6.2, col)
        b.text(cx + 6.2, cy + 0.3, str(st["id"]), "sans_k", 6.8, "#FFFFFF", anchor="mm",
               label=f"bd{st['id']}")
        runs = [
            (st["place"], "nar_b", 10.8, BRIEF_INK),
            (" " + st["brief"], "nar", 10.8, BRIEF_INK),
            ("  " + st["sources"], "nar_i", 10.4, MUTED),
        ]
        _, right = b.runs(cx + 15.8, cy + 0.2, runs, f"brief{st['id']}", anchor_v="m")
        b.fit(f"brief{st['id']}", right, cx + colw, 8.0)
        if r < rows - 1:
            b.hline(cx + 15.8, cx + colw, cy + lh / 2, "#E8E1D3", 0.5)
    end_y = y + 23.0 + (rows - 1) * lh + 7.0
    b.vline(x + colw + col_gap / 2, y + 15, end_y, RULE, 0.7)
    return end_y


def _split_lead(toks):
    out = []
    for s, f, z, c in toks:
        for w in s.split(" "):
            if w:
                out.append((w, f, z, c))
    return out


def date_check(b, y0, y1):
    b.rect(M, y0, W - M, y1, fill="#FFF8F5", outline=VERMILION, width=1.15, r=3)
    pw = 78
    ym = (y0 + y1) / 2
    b.rect(M + 7, ym - 9, M + 7 + pw, ym + 9, fill=VERMILION, r=8.5)
    b.text(M + 7 + pw / 2, ym + 0.3, "DATE CHECK", "sans_k", 8.4, "#FFFFFF", anchor="mm",
           label="dc-pill")
    x = M + pw + 15
    maxw = W - M - 8 - x
    t1 = [("Excluded (Fri 20 Nov & earlier):", "nar_b", 9.8, VERMILION)] + \
        [(w, "nar", 9.8, INK) for w in " · ".join(S.EXCLUDED_FRIDAY).split(" ")]
    t2 = [("Not confirmed when drawn:", "nar_b", 9.8, VERMILION)] + \
        [(w, "nar", 9.8, INK) for w in " · ".join(S.NOT_YET).split(" ")]
    l1 = rich_wrap(b, _split_lead(t1), maxw)
    l2 = rich_wrap(b, _split_lead(t2), maxw)
    lines = l1 + l2
    if len(lines) > 3:
        raise SystemExit(f"LAYOUT: date check needs {len(lines)} lines (max 3)")
    n_lines = len(lines)
    lh = 14.5 if n_lines == 2 else (y1 - y0 - 7) / 3
    block_h = (n_lines - 1) * lh
    # Optically center the 2 or 3 text lines vertically inside the DATE CHECK box
    y_first = (y0 + y1) / 2 - block_h / 2 + 3.4
    draw_wrapped(b, x, y_first, lines, lh, "datecheck", maxw)


def verification_bar(b, y0, y1):
    b.rect(M, y0, W - M, y1, fill="#EFE9DC", outline="#DDD4C2", width=0.6, r=2)
    cy = (y0 + y1) / 2 + 0.2
    items = [
        ("HOW WE CHECKED:", None, ""),
        ("CONFIRMED", "CONFIRMED", "= 2+ independent outlets"),
        ("OFFICIAL", "OFFICIAL", "= on-the-record statement"),
        ("REPORTED", "REPORTED", "= single outlet or NGO"),
        ("CLAIM", "CLAIM", "= one party's unverified account"),
    ]
    # Measure total width to center horizontally inside the bar
    total_w = b.measure(items[0][0], "sans_k", 7.8) + 8.0
    for idx, (tag, key, desc) in enumerate(items[1:]):
        if idx > 0:
            total_w += 10.0
        total_w += b.measure(tag, "sans_k", 7.0) + 9.0 + 4.0 + b.measure(desc, "sans", 7.9)
    cx = M + (CW - total_w) / 2
    b.text(cx, cy, items[0][0], "sans_k", 7.8, INK, anchor="lm", label="vk-head")
    cx += b.measure(items[0][0], "sans_k", 7.8) + 8.0
    for idx, (tag, key, desc) in enumerate(items[1:]):
        if idx > 0:
            b.text(cx + 3.0, cy, "·", "sans_k", 8.5, MUTED, anchor="mm", record=False)
            cx += 10.0
        fg, bg = TAG_STYLE[key]
        pw = b.measure(tag, "sans_k", 7.0) + 9.0
        b.rect(cx, cy - 5.4, cx + pw, cy + 5.4, fill=bg, outline=fg, width=0.7, r=5.2)
        b.text(cx + pw / 2, cy + 0.1, tag, "sans_k", 7.0, fg, anchor="mm", label=f"vk-p-{key}")
        cx += pw + 4.0
        bx = b.text(cx, cy, desc, "sans", 7.9, BODY_INK, anchor="lm", label=f"vk-d-{key}")
        cx = bx[2]
    b.fit("vk-bar", cx, W - M, 4.0)


def footer(b, y):
    left = ("Every story happened, or was first reported, on Saturday 21 November 2026 (UTC). "
            "Sources are named beside every story.")
    right = "Original editorial drawings & cartography"
    bl = b.text(M, y, left, "sans_i", 8.2, "#35404E", anchor="lm", label="footer-l")
    br = b.text(W - M, y, right, "sans_b", 8.2, "#35404E", anchor="rm", label="footer-r")
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
    kpi_row(b, 115, 158)
    region_bar(b, 162, 176)

    # Lead cards 1-3 (unobstructed art + full-width vermilion kicker bar + verification pills)
    y = 182
    lw, gap = 320, (CW - 3 * 320) / 2
    ends = []
    for i, st in enumerate(S.STORIES[:3]):
        ends.append(card(b, st, M + i * (lw + gap), y, lw, 94, True))
    y = max(ends) + 7.0
    b.hline(M, W - M, y, RULE, 0.85)
    y += 6.0

    # Secondary cards 4-13 (2 rows x 5)
    sw, sgap = 188, (CW - 5 * 188) / 4
    for row in range(2):
        ends = []
        for c in range(5):
            st = S.STORIES[3 + row * 5 + c]
            ends.append(card(b, st, M + c * (sw + sgap), y, sw, 54, False))
        y = max(ends) + 6.5
        b.hline(M, W - M, y, RULE, 0.85)
        y += 6.0

    bottom_top = y
    map_w, map_h = 334, 172
    map_end = world_map(b, M, bottom_top, map_w, map_h)
    br_end = briefs(b, M + map_w + 18, bottom_top, CW - map_w - 18)
    b.vline(M + map_w + 9, bottom_top, max(map_end, br_end), RULE, 0.8)

    y = max(map_end, br_end) + 6.5
    dc_h = 47.0
    date_check(b, y, y + dc_h)
    vk_y0 = y + dc_h + 4.5
    vk_y1 = vk_y0 + 16.5
    verification_bar(b, vk_y0, vk_y1)
    fy = vk_y1 + 9.5
    if fy + 5 > H - 2:
        raise SystemExit(f"LAYOUT: page overflows (footer_y={fy:.1f})")
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
        vk_y0=round(vk_y0, 2),
        vk_y1=round(vk_y1, 2),
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
        f"vk={report['vk_y0']}..{report['vk_y1']}, footer={report['footer_y']}, "
        f"{len(report['texts'])} text boxes, {len(report['pins'])} pins"
    )


if __name__ == "__main__":
    main()
