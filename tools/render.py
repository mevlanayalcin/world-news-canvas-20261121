"""Render the full 24-hour Saturday Broadsheet Atlas (v11).

    python3 -B tools/render.py [--out entry.png] [--report /tmp/report.json] [--thumb /tmp/thumb.png]

Draws at 2x (2048 px) and downsamples via LANCZOS to 1024 x 1024, then writes
a lossless, deterministic RGB PNG (matching main.ts).
Strict layout assertions run on every build: zero text overlaps, zero margin
overflows, zero map pin collisions, >= 8 px right-margin slack on every brief,
and strict floors on dateline and caption typography.
"""
import argparse
import json
import math
import os
import struct
import sys
import zlib

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art  # noqa: E402
import stories as S  # noqa: E402
import worldmap  # noqa: E402

K = 2  # drawing scale (2048 x 2048 -> 1024 x 1024)
W = H = 1024
M = 16
CW = W - 2 * M  # 992

# Vertical budget. Caption bars sit inside the art height.
LEAD_ART, LEAD_BAR = 102.0, 17.5
SEC_ART, SEC_BAR = 67.0, 16.0
SEC_BODY = 9.5
WIRE_LH = 16.0

# Signature Archival Broadsheet Palette
PAPER = "#FAF6EE"
TILE_BG = "#F2ECE0"
TILE_BORDER = "#D7CEBC"
RULE = "#D5CCB9"
INK = "#131B26"
BODY_INK = "#1E2733"
BRIEF_INK = "#131C26"
MUTED = "#525C6A"
FOLIO_BG = "#182A40"
FOLIO_GOLD = "#F0C66E"
VERMILION = "#B22222"
SLATE_INDIGO = "#1F4A6E"
KPI_SUB = "#1A1A1A"
KPI_FACE = ("sans_s", 10.2, 0.25)
CAPTION_BG = "#141923"
CAPTION_INK = "#FFFFFF"
CAPTION_MIN = 10.5

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
    "UNCONFIRMED": ("#96382E", "#F9EBE6"),
}

FD = "/usr/share/fonts/truetype"
FONTS = {
    "serif_b": f"{FD}/noto/NotoSerif-Bold.ttf",
    "serif_i": f"{FD}/noto/NotoSerif-Italic.ttf",
    "sans": f"{FD}/lato/Lato-Regular.ttf",
    "sans_m": f"{FD}/lato/Lato-Medium.ttf",
    "sans_s": f"{FD}/lato/Lato-Semibold.ttf",
    "sans_b": f"{FD}/lato/Lato-Bold.ttf",
    "sans_k": f"{FD}/lato/Lato-Black.ttf",
    "sans_i": f"{FD}/lato/Lato-Italic.ttf",
    "nar": f"{FD}/liberation/LiberationSansNarrow-Regular.ttf",
    "nar_b": f"{FD}/liberation/LiberationSansNarrow-Bold.ttf",
    "nar_i": f"{FD}/liberation/LiberationSansNarrow-Italic.ttf",
}
_font_cache = {}


def font(key, size):
    """Sizes land on the 2x canvas grid, so the effective step is half a pixel."""
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
        self.anchors = []
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

    b.rect(M, 8, W - M, 24.5, fill=FOLIO_BG)
    bl = b.text(M + 8, 16.4, "GLOBAL DISPATCH  /  FULL 24-HOUR EDITION", "sans_k", 9.0, FOLIO_GOLD,
                anchor="lm", spacing=1.0, label="kicker")
    clock_x = W - M - 86
    b.rect(clock_x, 8, W - M, 24.5, fill=FOLIO_GOLD)
    b.text(clock_x + 43, 16.4, S.CLOCK, "sans_k", 11.0, FOLIO_BG, anchor="mm", label="press-clock")
    stats = f"{len(S.STORIES)} STORIES   /   {len(counts)} REGIONS      ·      SATURDAY CLOSE"
    br = b.text(clock_x - 8, 16.4, stats, "sans_k", 9.0, "#F5F1E8", anchor="rm", label="stats")
    if bl[2] + 12 > br[0]:
        raise SystemExit(f"LAYOUT: masthead folio bar collides ({bl[2]:.1f} vs {br[0]:.1f})")

    # Commanding bold serif masthead spanning page width.
    tsize = 57.5
    while tsize > 46.0 and b.measure(S.DAY_LABEL, "serif_b", tsize) > CW - 10:
        tsize -= 0.5
    b.text(W / 2, 47.0, S.DAY_LABEL, "serif_b", tsize, INK, anchor="mm", label="title")

    deck_size = 11.4
    while deck_size > 9.8 and b.measure(S.DECK, "serif_i", deck_size) > CW - 6:
        deck_size -= 0.2
    b.text(W / 2, 90.0, S.DECK, "serif_i", deck_size, "#293342", anchor="mm", label="deck")
    b.fit("deck", b.measure(S.DECK, "serif_i", deck_size), CW)
    b.hline(M, W - M, 97.5, VERMILION, 1.5)
    b.hline(M, W - M, 99.9, INK, 0.6)
    return tsize


def utc_timeline(b, y0, y1):
    """Chronological Saturday UTC strip backed directly by SOURCES.tsv minutes."""
    b.rect(M, y0, W - M, y1, fill="#F5EFE2", outline="#D4C9B4", width=0.75, r=2.0)
    bw = 64.0
    b.rect(M, y0, M + bw, y1, fill=FOLIO_BG, r=2.0)
    b.rect(M + bw - 3, y0, M + bw, y1, fill=FOLIO_BG)
    ym = (y0 + y1) / 2
    b.text(M + bw / 2, ym - 5.2, "THE DAY", "sans_k", 8.8, FOLIO_GOLD, anchor="mm", spacing=0.6,
           label="tl-head0")
    b.text(M + bw / 2, ym + 5.6, "IN UTC", "sans_k", 8.8, "#FFFFFF", anchor="mm", spacing=0.6,
           label="tl-head1")

    n = len(S.TIMELINE)
    x_start = M + bw + 2.0
    span = (W - M) - x_start
    cell = span / n
    for i, (sid, hhmm, label) in enumerate(S.TIMELINE):
        cx0 = x_start + i * cell
        if i > 0:
            b.vline(cx0, y0 + 3.5, y1 - 3.5, "#DDD3C0", 0.6)
        dot_col = VERMILION if i in (0, 1, 6) else SLATE_INDIGO
        b.circle(cx0 + 8.5, y0 + 8.5, 2.3, dot_col)
        bt = b.text(cx0 + 14.8, y0 + 8.6, f"{hhmm}Z", "sans_b", 10.5, dot_col, anchor="lm",
                    spacing=0.2, label=f"tl-t{i}")
        br = b.text(cx0 + cell - 6.0, y0 + 8.6, f"#{sid:02d}", "sans_b", 8.8, "#4A5462",
                    anchor="rm", label=f"tl-r{i}")
        b.fit(f"tl-t{i}", bt[2], br[0], 3.0)
        bl = b.text(cx0 + 7.0, y0 + 20.6, label, "sans_b", 9.6, INK, anchor="lm",
                    label=f"tl-l{i}")
        b.fit(f"tl-l{i}", bl[2], cx0 + cell, 4.0)


def kpi_row(b, y0, y1):
    n = len(S.KPIS)
    gap = 6.0
    tw = (CW - (n - 1) * gap) / n
    for i, k in enumerate(S.KPIS):
        x = M + i * (tw + gap)
        accent = VERMILION if i % 2 == 0 else SLATE_INDIGO
        b.rect(x, y0, x + tw, y1, fill=TILE_BG, outline=TILE_BORDER, width=0.7)
        b.rect(x, y0, x + tw, y0 + 2.5, fill=accent)
        bf = b.text(x + 7.5, y0 + 18.2, k["figure"], "serif_b", 18.5, INK, anchor="ls",
                    label=f"kpi{i}")
        ix = b.text(x + tw - 6, y0 + 18.2, f"#{k['story']:02d}", "sans_k", 9.2, "#3A4452",
                    anchor="rs", label=f"kpi-ref{i}")
        b.fit(f"kpi-ref{i}", bf[2], ix[0], 4)
        for j, cap in enumerate(k["caption"]):
            face, size, spacing = KPI_FACE
            bx = b.text(x + 7.5, y0 + 29.6 + j * 10.4, cap, face, size, KPI_SUB, anchor="ls",
                        spacing=spacing, label=f"kpi{i}c{j}")
            b.fit(f"kpi{i}c{j}", bx[2], x + tw, 4)


def region_bar(b, y0, y1):
    counts = S.region_counts()
    total = sum(counts.values())
    assert total == len(S.STORIES)

    floor_w = 84.0
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
        bx = b.text(x + seg / 2, (y0 + y1) / 2 + 0.3, txt, "sans_k", 9.0, "#FFFFFF", anchor="mm",
                    label=f"rb-{key}")
        b.fit(f"rb-{key}", bx[2], x + seg, 3)
        x += seg


def art_ribbon(b, x, y, text, size, h, max_w, sid):
    sz = size
    pad_x = 7.5 if size >= 15 else 5.5
    while sz > 10.5 and (b.measure(text, "sans_k", sz) + 2 * pad_x) > max_w:
        sz -= 0.25
    tw = b.measure(text, "sans_k", sz) + 2 * pad_x
    b.rect(x + 1.5, y + 1.8, x + tw + 1.5, y + h + 1.8, fill=(0, 0, 0, 115))
    b.rect(x, y, x + tw, y + h, fill=VERMILION if sid <= 3 else FOLIO_BG,
           outline="#FFFFFF", width=1.1)
    b.text(x + tw / 2, y + h / 2 + 0.4, text, "sans_k", sz, "#FFFFFF", anchor="mm",
           label=f"banner:{sid}")
    return tw


def art_subpill(b, x, y, text, size, h, sid):
    pad_x = 6.0 if size >= 9.5 else 4.8
    tw = b.measure(text, "sans_k", size) + 2 * pad_x
    b.rect(x + 1.0, y + 1.2, x + tw + 1.0, y + h + 1.2, fill=(0, 0, 0, 65), r=2.0)
    b.rect(x, y, x + tw, y + h, fill="#FFFFFF", outline=(19, 27, 38, 175), width=0.7, r=2.0)
    b.text(x + tw / 2, y + h / 2 + 0.2, text, "sans_k", size, INK, anchor="mm",
           label=f"sub:{sid}")
    return tw


def art_caption(b, x, y_bot, w, text, size, h, pad, sid):
    """Full-width credit strip: white on near-black, never below CAPTION_MIN."""
    if size < CAPTION_MIN:
        raise SystemExit(f"LAYOUT: caption {sid} set at {size}px, floor is {CAPTION_MIN}px")
    b.rect(x, y_bot - h, x + w, y_bot, fill=CAPTION_BG)
    bx = b.text(x + pad, y_bot - h / 2 + 0.2, text, "sans_b", size, CAPTION_INK, anchor="lm",
                spacing=0.15, label=f"chip:{sid}")
    b.fit(f"chip:{sid}", bx[2], x + w, pad)


def tag_pill(b, xr, cy, tag, size, h, sid):
    fg, bg = TAG_STYLE[tag]
    pad_x = 5.0 if size >= 8.0 else 4.0
    tw = b.measure(tag, "sans_k", size) + 2 * pad_x
    x0 = xr - tw
    b.rect(x0, cy - h / 2, xr, cy + h / 2, fill=bg, outline=fg, width=0.75, r=h / 2)
    b.text((x0 + xr) / 2, cy + 0.25, tag, "sans_k", size, fg, anchor="mm", label=f"tag:{sid}")
    return x0


def meta_line(b, x, y, w, st, size, badge_r, lead):
    col = region_color(st["region"])
    b.circle(x + badge_r, y, badge_r, col)
    b.text(x + badge_r, y + 0.3, str(st["id"]), "sans_k", badge_r * 1.3, "#FFFFFF", anchor="mm",
           label=f"badge{st['id']}")
    px0 = tag_pill(b, x + w, y, st["tag"], 8.5 if lead else 7.5, 14.0 if lead else 12.4, st["id"])
    label = f"{st['place']} · {st['beat'].upper()}" if lead else st["place"]
    tx = x + badge_r * 2 + 4.5
    avail = px0 - tx - 3.5
    # Open Lato-Bold with a strict 8.5px floor keeps long datelines (BHUBANESWAR, DARMSTADT) razor-sharp.
    fkey = "sans_k" if lead else "sans_b"
    sp = 0.0 if lead else 0.15
    sz = size
    while sz > 8.5 and b.measure(label, fkey, sz, sp) > avail:
        sz -= 0.2
    if b.measure(label, fkey, sz, sp) > avail:
        sp = 0.0
    bx = b.text(tx, y + 0.25, label, fkey, sz, col, anchor="lm", spacing=sp, label=f"dateline{st['id']}")
    b.fit(f"dateline{st['id']}", bx[2], px0, 3.0)


def card(b, st, x, y, w, art_h, lead):
    bar_h = LEAD_BAR if lead else SEC_BAR
    im = art.draw_scene(st["scene"], w, art_h, out_scale=K, base=art_h - bar_h)
    b.img.paste(im, (round(x * K), round(y * K)))
    b.rect(x, y, x + w, y + art_h, outline="#BEB4A0", width=0.65)

    if lead:
        art_ribbon(b, x + 5, y + 5, st["banner"], 17.2, 26, w - 10, st["id"])
        art_subpill(b, x + 5, y + 34.5, st["sub"], 10.2, 17.5, st["id"])
        art_caption(b, x, y + art_h, w, st["chip"], 11.5, bar_h, 8.0, st["id"])
    else:
        rib_max = {
            "caboverde": w - 62, "trade": w - 58, "bandasea": w - 46,
        }.get(st["scene"], w - 8)
        art_ribbon(b, x + 4, y + 4, st["banner"], 13.2, 20.5, rib_max, st["id"])
        art_caption(b, x, y + art_h, w, st["chip"], 11.0, bar_h, 7.0, st["id"])

    my = y + art_h + (9.2 if lead else 8.4)
    meta_line(b, x, my, w, st, 9.0 if lead else 8.7, 7.0 if lead else 6.2, lead)

    hy = my + (8.0 if lead else 6.8)
    hsize, hlh = (17.8, 19.2) if lead else (12.5, 13.7)
    hl = rich_wrap(b, tokens(st["headline"], "serif_b", hsize, INK), w)
    if len(hl) > 2:
        raise SystemExit(f"LAYOUT: headline {st['id']} needs {len(hl)} lines (max 2)")
    for i, ln in enumerate(hl):
        _, right = b.runs(x, hy + hsize * 0.94 + i * hlh, ln, f"h{st['id']}:{i}")
        b.fit(f"h{st['id']}:{i}", right, x + w)

    sy = hy + hsize * 0.94 + (len(hl) - 1) * hlh + (13.6 if lead else 11.8)
    ssize, slh = (10.2, 11.8) if lead else (SEC_BODY, SEC_BODY + 1.8)
    toks = tokens(st["summary"], "sans", ssize, BODY_INK)
    src = f"({st['sources']})".split()
    toks += [(t, "sans_i", ssize, MUTED) for t in src]
    sl = rich_wrap(b, toks, w)
    limit = 3 if lead else 2
    if len(sl) > limit:
        raise SystemExit(f"LAYOUT: summary {st['id']} needs {len(sl)} lines (max {limit})")
    end = draw_wrapped(b, x, sy, sl, slh, f"s{st['id']}", w)
    return end


def world_map(b, x, y, w, h):
    b.text(x, y, "WORLD ATLAS  /  THE ILLUSTRATED DISPATCHES", "sans_k", 9.3, INK, anchor="lt",
           spacing=0.35, label="map-title")
    my = y + 14.5
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
    land, lakes = worldmap.outlines()
    for pts in land:
        ld.polygon([tuple(v * K for v in worldmap.project(lo, la, box)) for lo, la in pts],
                   fill=MAP_LAND, outline=MAP_COAST)
    for pts in lakes:
        ld.polygon([tuple(v * K for v in worldmap.project(lo, la, box)) for lo, la in pts],
                   fill=MAP_WATER, outline=MAP_COAST)
    mask = Image.new("L", b.img.size, 0)
    ImageDraw.Draw(mask).rectangle([x * K, my * K, (x + w) * K, (my + h) * K], fill=255)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", b.img.size, 0), mask)
    layer.putalpha(alpha)
    b.img.paste(layer, (0, 0), layer)
    b.d = ImageDraw.Draw(b.img, "RGBA")
    b.rect(x, my, x + w, my + h, outline="#102535", width=0.8)

    geo_leads = S.STORIES[:S.LEADS]
    R = 7.2
    gap = 2 * R + 2.4
    placed = []
    truths = []
    for st in geo_leads:
        tx, ty = worldmap.project(st["lon"], st["lat"], box)
        truths.append((tx, ty))

    for idx, st in enumerate(geo_leads):
        tx, ty = truths[idx]
        best = None
        # In dense clusters, offset the numbered badge while keeping the leader dot on the true coordinate.
        bearing = {
            "cop": -45, "gulf": 25, "trade": 165, "baltic": -40,
            "mercury": -80, "football": -135, "caboverde": -135,
            "sinaloa": 120, "bandasea": -30,
        }.get(st["scene"], -90)
        for ring in range(4):
            rr = ring * 14
            for k in range(16 if ring else 1):
                a = math.radians(bearing + (-1 if k % 2 else 1) * ((k + 1) // 2) * 22.5)
                cx, cy = tx + math.cos(a) * rr, ty + math.sin(a) * rr
                if not (x + R + 1.5 <= cx <= x + w - R - 1.5 and my + R + 1.5 <= cy <= my + h - R - 1.5):
                    continue
                if any(math.hypot(cx - px, cy - py) < gap for px, py, _ in placed):
                    continue
                if any(j != idx and math.hypot(cx - px, cy - py) < R + 2.5
                       for j, (px, py) in enumerate(truths)):
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
        b.anchors.append(dict(id=st["id"], place=st["place"], lat=st["lat"], lon=st["lon"],
                              x=round(tx, 2), y=round(ty, 2)))
        if math.hypot(cx - tx, cy - ty) > 0.5:
            line = [(tx * K, ty * K), (cx * K, cy * K)]
            b.d.line(line, fill="#FBF7EE", width=round(2.5 * K))
            b.d.line(line, fill=FOLIO_BG, width=K)
            b.circle(tx, ty, 2.0, FOLIO_BG, "#FFFFFF", 0.7)
    for cx, cy, st in placed:
        b.circle(cx, cy, R, region_color(st["region"]), "#FFFFFF", 1.0)
        b.text(cx, cy + 0.3, str(st["id"]), "sans_k", 9.0, "#FFFFFF", anchor="mm", label=f"pin{st['id']}")
        b.pins.append((round(cx, 2), round(cy, 2), R, st["id"]))
    assert [pin[3] for pin in b.pins] == [s["id"] for s in S.STORIES if "headline" in s]

    cap_y = my + h + 9.5
    bx = b.text(x, cap_y, "1–13 match the cards. Leader dots mark datelines or event sites.", "sans_b",
                9.2, "#2F3946", anchor="lm", label="map-cap")
    b.fit("map-cap", bx[2], x + w)
    ky = cap_y + 13.5
    kx = x
    for key, label, col in S.REGIONS:
        b.circle(kx + 3.3, ky, 3.3, col)
        bx = b.text(kx + 8.6, ky + 0.2, label, "nar_b", 9.2, "#2F3946", anchor="lm", label=f"key-{key}")
        b.fit(f"map-key-{key}", bx[2], x + w)
        kx = bx[2] + 5.6
    return ky + 6.5


def briefs(b, x, y, w):
    items = S.STORIES[S.LEADS:]
    b.text(x, y, f"THE SATURDAY WIRE  /  {len(items)} MORE DISPATCHES", "sans_k", 9.3, INK,
           anchor="lt", spacing=0.35, label="briefs-title")
    b.text(x + w, y, f"FILED THROUGH {S.CLOCK}", "sans_b", 9.2, "#3A4452",
           anchor="rt", label="wire-clock")
    rows = (len(items) + 1) // 2
    col_gap = 14.0
    colw = (w - col_gap) / 2
    lh = WIRE_LH
    top = 21.5
    for i, st in enumerate(items):
        c, r = divmod(i, rows)
        cx = x + c * (colw + col_gap)
        cy = y + top + r * lh
        col = region_color(st["region"])
        b.circle(cx + 6.2, cy, 6.2, col)
        b.text(cx + 6.2, cy + 0.3, str(st["id"]), "sans_k", 7.8, "#FFFFFF", anchor="mm",
               label=f"bd{st['id']}")
        # Open Lato at 11.0px keeps dollar figures ($55,106, $60,086) and numbers 100% crisp.
        runs = [
            (st["place"], "sans_b", 11.0, BRIEF_INK),
            (" " + st["brief"], "sans", 11.0, BRIEF_INK),
            ("  " + st["sources"], "sans_i", 10.0, MUTED),
        ]
        _, right = b.runs(cx + 15.6, cy + 0.2, runs, f"brief{st['id']}", anchor_v="m")
        limit = cx + colw
        if st["tag"]:
            limit = tag_pill(b, limit - 2, cy, st["tag"], 7.6, 11.8, st["id"])
        b.fit(f"brief{st['id']}", right, limit, 8.0)
        if r < rows - 1:
            b.hline(cx + 15.6, cx + colw, cy + lh / 2, "#E8E1D3", 0.5)

    wire_bot = y + top + (rows - 1) * lh + 7.5
    b.vline(x + colw + col_gap / 2, y + 15, wire_bot, RULE, 0.7)

    # Full-width match-desk strip below both wire columns: airy and OCR-proof.
    ft_y0 = wire_bot + 4.5
    ft_y1 = ft_y0 + 16.0
    ft_ym = (ft_y0 + ft_y1) / 2
    b.rect(x, ft_y0, x + w, ft_y1, fill=TILE_BG, outline=TILE_BORDER, width=0.65, r=2.0)
    slug = "PREMIER LEAGUE / FT"
    label_w = b.measure(slug, "sans_k", 8.8) + 12.0
    b.rect(x, ft_y0, x + label_w, ft_y1, fill=FOLIO_BG, r=2.0)
    b.text(x + label_w / 2, ft_ym + 0.2, slug, "sans_k", 8.8, FOLIO_GOLD,
           anchor="mm", label="ft-title")
    ft_runs = [
        ("   ·   ".join(S.FOOTBALL_FT), "sans_b", 10.4, INK),
        ("    Saturday full-time results", "sans_i", 9.8, MUTED),
    ]
    _, right = b.runs(x + label_w + 8.0, ft_ym + 0.2, ft_runs, "ft-scores", anchor_v="m")
    b.fit("ft-scores", right, x + w, 6.0)
    return ft_y1 + 1.0


def wrap_items(b, items, fkey, size, sep_w, maxw, spacing=0.0):
    """Greedy wrap that never splits a ledger item; each full line keeps room for its closing dot."""
    lines, cur, curw = [], [], 0.0
    for item in items:
        iw = b.measure(item, fkey, size, spacing)
        need = iw + (sep_w if cur else 0.0)
        if cur and curw + need + sep_w > maxw:
            lines.append(cur)
            cur, curw, need = [], 0.0, iw
        cur.append(item)
        curw += need
    lines.append(cur)
    return lines


def date_check(b, y0, y1):
    """Two ledgers with stacked left labels so body items stay large and airy."""
    b.rect(M, y0, W - M, y1, fill="#FFF8F5", outline=VERMILION, width=1.15, r=3)
    bw = 62.0
    b.rect(M, y0, M + bw, y1, fill=VERMILION, r=3)
    b.rect(M + bw - 4, y0, M + bw, y1, fill=VERMILION)
    ym = (y0 + y1) / 2
    for dy, word in ((-7.4, "DATE"), (7.8, "CHECK")):
        b.text(M + bw / 2, ym + dy, word, "sans_k", 12.6, "#FFFFFF", anchor="mm", spacing=0.9,
               label=f"dc-{word}")

    size, lh, entry_gap, spacing = 11.3, 14.3, 6.0, 0.12
    x = M + bw + 9.0
    ledgers = ((S.EXCLUDED_LABEL, [t for t, _ in S.EXCLUDED]),
               (S.PENDING_LABEL, [t for t, _ in S.PENDING]))
    label_w = max(max(b.measure(hi, "sans_k", 10.8), b.measure(lo, "sans_b", 9.5))
                  for (hi, lo), _ in ledgers)
    tx = x + label_w + 10.0
    maxw = W - M - 9.0 - tx
    gap_w = b.measure(" ", "sans_m", size) * 1.65
    dot_w = b.measure("·", "sans_k", size + 2)
    sep_w = 2 * gap_w + dot_w
    wrapped = [(lbl, wrap_items(b, items, "sans_m", size, sep_w, maxw, spacing))
               for lbl, items in ledgers]
    n_lines = sum(len(lines) for _, lines in wrapped)
    if n_lines > 4:
        raise SystemExit(f"LAYOUT: date check needs {n_lines} lines (max 4)")
    block = (n_lines - 1) * lh + entry_gap * (len(wrapped) - 1)
    yb = ym - block / 2 + size * 0.36
    for r, ((hi, lo), lines) in enumerate(wrapped):
        b.text(x, yb, hi, "sans_k", 10.8, VERMILION, anchor="ls", label=f"dc-hi{r}")
        b.text(x, yb + 12.8, lo, "sans_b", 9.5, "#7E2626", anchor="ls", label=f"dc-lo{r}")
        for i, items in enumerate(lines):
            cx, boxes = tx, []
            last_line = i == len(lines) - 1
            for j, item in enumerate(items):
                closing = "." if last_line and j == len(items) - 1 else ""
                boxes.append(b.text(cx, yb, item + closing, "sans_m", size, INK, anchor="ls",
                                    record=False, spacing=spacing))
                cx = boxes[-1][2]
                if not closing:
                    b.text(cx + gap_w, yb, "·", "sans_k", size + 2, VERMILION, anchor="ls",
                           record=False)
                    cx += sep_w if j < len(items) - 1 else gap_w + dot_w
            box = (tx, min(v[1] for v in boxes), boxes[-1][2], max(v[3] for v in boxes))
            b.texts.append(box + (f"dc{r}:{i}",))
            b.fit(f"dc{r}:{i}", cx, W - M, 8.0)
            yb += lh
        if r < len(wrapped) - 1:
            b.hline(x, W - M - 9, yb - lh + (lh + entry_gap) / 2 - 2.4, "#E6BDB5", 0.65)
        yb += entry_gap


def verification_bar(b, y0, y1):
    b.rect(M, y0, W - M, y1, fill="#EFE9DC", outline="#DDD4C2", width=0.6, r=2)
    cy = (y0 + y1) / 2 + 0.2
    head, hs, ps, ds = "HOW WE CHECKED:", 9.2, 8.0, 9.2
    items = [
        ("CONFIRMED", "independent accounts agree"),
        ("OFFICIAL", "named authority on record"),
        ("REPORTED", "attributed to one source"),
        ("CLAIM", "unverified party account"),
        ("UNCONFIRMED", "outcome not verified"),
    ]
    assert {tag for tag, _ in items} == set(TAG_STYLE)
    total_w = b.measure(head, "sans_k", hs) + 8.0
    for idx, (tag, desc) in enumerate(items):
        total_w += (10.0 if idx else 0.0) + b.measure(tag, "sans_k", ps) + 9.0 + 4.0 + b.measure(desc, "sans_m", ds)
    cx = M + (CW - total_w) / 2
    b.text(cx, cy, head, "sans_k", hs, INK, anchor="lm", label="vk-head")
    cx += b.measure(head, "sans_k", hs) + 8.0
    for idx, (tag, desc) in enumerate(items):
        if idx > 0:
            b.text(cx + 3.0, cy, "·", "sans_k", 9.0, MUTED, anchor="mm", record=False)
            cx += 10.0
        fg, bg = TAG_STYLE[tag]
        pw = b.measure(tag, "sans_k", ps) + 9.0
        b.rect(cx, cy - 6.0, cx + pw, cy + 6.0, fill=bg, outline=fg, width=0.7, r=6.0)
        b.text(cx + pw / 2, cy + 0.1, tag, "sans_k", ps, fg, anchor="mm", label=f"vk-p-{tag}")
        cx += pw + 4.0
        bx = b.text(cx, cy, desc, "sans_m", ds, BODY_INK, anchor="lm", label=f"vk-d-{tag}")
        cx = bx[2]
    b.fit("vk-bar", cx, W - M, 4.0)


def footer(b, y):
    left = (f"Strict Saturday UTC window, {S.WINDOW}; local time is named where it differs. "
            "Scores are full time only where stated.")
    right = "Dispatch Atlas  /  Original desk illustrations · Natural Earth coastlines"
    bl = b.text(M, y, left, "sans_i", 9.2, "#2F3946", anchor="lm", label="footer-l")
    br = b.text(W - M, y, right, "sans_b", 9.2, "#2F3946", anchor="rm", label="footer-r")
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


def write_lossless_rgb_png(img, path):
    """Write a deterministic, lossless 8-bit/color RGB PNG with filter=None for sharp typography."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    raw = rgb.tobytes()
    stride = w * 3
    buf = b"".join(b"\x00" + raw[y * stride:(y + 1) * stride] for y in range(h))
    comp = zlib.compressobj(9, zlib.DEFLATED, 15, 9, zlib.Z_DEFAULT_STRATEGY)
    idat = comp.compress(buf) + comp.flush()

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def build():
    S.validate()
    b = Board()
    tsize = masthead(b)
    utc_timeline(b, 102.8, 130.8)
    kpi_row(b, 133.8, 175.8)
    region_bar(b, 178.8, 192.8)

    # Lead cards 1-3: silkscreen art with vermilion ribbon, white sub-tag and caption bar.
    y = 197.0
    lw, gap = 320, (CW - 3 * 320) / 2
    ends = []
    for i, st in enumerate(S.STORIES[:3]):
        ends.append(card(b, st, M + i * (lw + gap), y, lw, LEAD_ART, True))
    y = max(ends) + 5.5
    b.hline(M, W - M, y, RULE, 0.85)
    y += 5.0

    # Secondary cards 4-13 (two rows of five, with slate ribbons).
    sw, sgap = 188, (CW - 5 * 188) / 4
    for row in range(2):
        ends = []
        for c in range(5):
            st = S.STORIES[3 + row * 5 + c]
            ends.append(card(b, st, M + c * (sw + sgap), y, sw, SEC_ART, False))
        y = max(ends) + 5.5
        b.hline(M, W - M, y, RULE, 0.85)
        y += 5.0

    bottom_top = y
    map_w = 334
    br_end = briefs(b, M + map_w + 18, bottom_top, CW - map_w - 18)
    # Match World Atlas box height precisely to the Saturday Wire + FT strip height.
    map_h = max(164.0, (br_end - bottom_top) - 14.5 - 9.5 - 13.5 - 6.5)
    map_end = world_map(b, M, bottom_top, map_w, map_h)
    b.vline(M + map_w + 9, bottom_top, max(map_end, br_end), RULE, 0.8)

    y = max(map_end, br_end) + 5.5
    dc_h = 69.0
    date_check(b, y, y + dc_h)
    vk_y0 = y + dc_h + 4.5
    vk_y1 = vk_y0 + 18.0
    verification_bar(b, vk_y0, vk_y1)
    fy = vk_y1 + 9.0
    if fy + 5 > H - 4:
        raise SystemExit(f"LAYOUT: page overflows (footer_y={fy:.1f})")
    footer(b, fy)

    bad = overlaps(b.texts)
    if bad:
        raise SystemExit(f"LAYOUT: overlapping text {bad[:8]}")
    for t in b.texts:
        if t[0] < M - 0.5 or t[2] > W - M + 0.5 or t[1] < 0 or t[3] > H:
            raise SystemExit(f"LAYOUT: text outside page margins {t}")

    # BICUBIC avoids LANCZOS ringing halos on flat paper typography while preserving sharp art.
    out = b.img.resize((W, H), Image.BICUBIC)
    brief_slacks = [f[4] for f in b.fits if f[0].startswith("brief")]
    report = dict(
        texts=b.texts,
        pins=b.pins, anchors=b.anchors,
        fits=b.fits,
        masthead_px=tsize,
        bottom_top=round(bottom_top, 2),
        map_h=round(map_h, 2),
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


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--out", default=os.path.join(root, "entry.png"))
    ap.add_argument("--report")
    ap.add_argument("--thumb")
    a = ap.parse_args()
    img, report = build()
    write_lossless_rgb_png(img, a.out)
    size = os.path.getsize(a.out)
    if size > 1024 * 1024:
        raise SystemExit(f"PNG exceeds 1 MiB: {size} bytes")
    if a.thumb:
        img.resize((300, 300), Image.LANCZOS).save(a.thumb, "PNG")
    report.update(format="PNG", size=size)
    if a.report:
        with open(a.report, "w") as fh:
            json.dump(report, fh, indent=2)
    print(
        f"wrote {a.out}: {size} bytes ({size / 1024:.1f} KiB), RGB PNG, "
        f"masthead={report['masthead_px']}px, min_brief_slack={report['min_brief_slack']}px, "
        f"bottom_top={report['bottom_top']}, map_h={report['map_h']}, "
        f"dc={report['date_check_y0']}..{report['date_check_y1']}, "
        f"vk={report['vk_y0']}..{report['vk_y1']}, footer={report['footer_y']}, "
        f"{len(report['texts'])} text boxes, {len(report['pins'])} pins"
    )


if __name__ == "__main__":
    main()
