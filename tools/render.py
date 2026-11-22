"""Render the v15c Hybrid Illustrated Poster Broadsheet (36 verified stories, 300px-legible top + 26-item wire).

    python3 -B tools/render.py [--out entry.png] [--report /tmp/report.json] [--thumb /tmp/thumb.png]

Top 66% is an unobstructed 300px-legible 2-Hero + 4x2 Illustrated Poster;
bottom 34% pairs a 10-pin World Atlas with counted 7-region key, 26 crisp Lato-Medium wire dispatches,
2-ledger Date Check, and 5-tier verification key.
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

K = 2
W = H = 1024
M = 16
CW = W - 2 * M  # 992

PAPER = "#F6F0E5"
CARD_BG = "#FFFDF8"
CARD_BORDER = "#D4C9B4"
RULE = "#D5CCB9"
SHADOW = (24, 34, 48, 22)
INK = "#111924"
SUB_INK = "#222C3A"
BRIEF_INK = "#131C26"
MUTED = "#4E5968"
FOLIO_BG = "#152538"
FOLIO_GOLD = "#F0C66E"
VERMILION = "#B22222"

MAP_OCEAN = "#18364A"
MAP_GRID = "#254A63"
MAP_LAND = (239, 231, 214, 255)
MAP_COAST = (184, 172, 150, 255)
MAP_WATER = (24, 54, 74, 255)

TAG_STYLE = {
    "CONFIRMED":   ("#156E5E", "#E6F5F1"),
    "OFFICIAL":    ("#1F4A6E", "#E8F0F7"),
    "REPORTED":    ("#9A5B0A", "#FDF3E3"),
    "CLAIM":       ("#6A3F7A", "#F4ECF8"),
    "UNCONFIRMED": ("#96382E", "#F9EBE6"),
}

FD = "/usr/share/fonts/truetype"
FONTS = {
    "serif_b": f"{FD}/noto/NotoSerif-Bold.ttf",
    "serif_i": f"{FD}/noto/NotoSerif-Italic.ttf",
    "sans":    f"{FD}/lato/Lato-Regular.ttf",
    "sans_m":  f"{FD}/lato/Lato-Medium.ttf",
    "sans_s":  f"{FD}/lato/Lato-Semibold.ttf",
    "sans_b":  f"{FD}/lato/Lato-Bold.ttf",
    "sans_k":  f"{FD}/lato/Lato-Black.ttf",
    "sans_i":  f"{FD}/lato/Lato-Italic.ttf",
    "nar_b":   f"{FD}/liberation/LiberationSansNarrow-Bold.ttf",
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
        self.texts = []
        self.pins = []
        self.fits = []

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

    def text(self, x, y, s, fkey, size, fill=INK, anchor="la", label=None, record=True, spacing=0.0):
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


def wrap_lines(b, text, fkey, size, maxw):
    lines, cur = [], ""
    for w in text.split():
        cand = f"{cur} {w}".strip()
        if cur and b.measure(cand, fkey, size) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def masthead(b):
    b.rect(M, 8, W - M, 29, fill=FOLIO_BG, r=2.0)
    bl = b.text(M + 10, 18.7, "WORLD NEWS  ·  FULL 24-HOUR EDITION", "sans_k", 10.6, FOLIO_GOLD,
                anchor="lm", spacing=0.7, label="kicker")
    badge_w = 96.0
    bx0 = W - M - badge_w
    b.rect(bx0, 8, W - M, 29, fill=FOLIO_GOLD, r=2.0)
    b.rect(bx0, 8, bx0 + 4, 29, fill=FOLIO_GOLD)
    b.text(bx0 + badge_w / 2, 18.7, S.CLOCK, "sans_k", 11.4, FOLIO_BG, anchor="mm", label="clock")
    stats = f"{len(S.STORIES)} SOURCED DISPATCHES  ·  7 REGIONS  ·  SATURDAY CLOSE"
    br = b.text(bx0 - 10, 18.7, stats, "sans_b", 10.2, "#F5F1E8", anchor="rm", spacing=0.3,
                label="folio-stats")
    if bl[2] + 12 > br[0]:
        raise SystemExit(f"LAYOUT: folio collision ({bl[2]:.1f} vs {br[0]:.1f})")

    tsize = 54.5
    while tsize > 46.0 and b.measure(S.DAY_LABEL, "serif_b", tsize) > CW - 14:
        tsize -= 0.5
    b.text(W / 2, 53.5, S.DAY_LABEL, "serif_b", tsize, INK, anchor="mm", label="title")

    b.hline(M, W - M, 88.5, VERMILION, 2.0)
    b.hline(M, W - M, 92.0, INK, 0.75)
    return tsize


def tag_pill(b, xr, cy, tag, size, h, sid):
    fg, bg = TAG_STYLE[tag]
    pad_x = 5.8 if size >= 9.0 else 4.5
    tw = b.measure(tag, "sans_k", size) + 2 * pad_x
    x0 = xr - tw
    b.rect(x0, cy - h / 2, xr, cy + h / 2, fill=bg, outline=fg, width=0.8, r=h / 2)
    b.text((x0 + xr) / 2, cy + 0.25, tag, "sans_k", size, fg, anchor="mm", label=f"tag:{sid}")
    return x0


def numbered_region_pill(b, x, y, sid, text, col, size, h):
    badge_w = h
    pad_x = 6.5 if size >= 10.5 else 5.2
    tw = badge_w + b.measure(text, "sans_k", size, spacing=0.3) + pad_x + 3.5
    b.rect(x + 1.0, y + 1.2, x + tw + 1.0, y + h + 1.2, fill=(0, 0, 0, 88), r=2.2)
    b.rect(x, y, x + tw, y + h, fill=col, outline="#FFFFFF", width=0.8, r=2.2)
    b.rect(x + 1.1, y + 1.1, x + badge_w - 1.1, y + h - 1.1, fill="#FFFFFF", r=1.4)
    b.text(x + badge_w / 2, y + h / 2 + 0.25, str(sid), "sans_k", size + 0.3, col, anchor="mm",
           label=f"num:{sid}")
    b.text(x + badge_w + 4.0, y + h / 2 + 0.25, text, "sans_k", size, "#FFFFFF", anchor="lm",
           spacing=0.3, label=f"rpill:{sid}")
    return tw


def hero_card(b, st, x, y, w, h):
    col = region_color(st["region"])
    b.rect(x + 1.5, y + 1.8, x + w + 1.5, y + h + 1.8, fill=SHADOW, r=3.5)
    b.rect(x, y, x + w, y + h, fill=CARD_BG, outline=CARD_BORDER, width=0.9, r=3.5)
    b.rect(x, y, x + w, y + 3.5, fill=col, r=1.6)

    art_y = y + 3.5
    art_h = 138.0
    im = art.draw_scene(st["scene"], w - 2.0, art_h, out_scale=K)
    b.img.paste(im, (round((x + 1.0) * K), round(art_y * K)))
    b.hline(x, x + w, art_y + art_h, CARD_BORDER, 0.8)

    numbered_region_pill(b, x + 8, art_y + 7, st["id"], st["region_pill"], col, 10.8, 20.0)

    pad = 12.0
    tx = x + pad
    tw = w - 2 * pad

    meta_y = art_y + art_h + 13.0
    px0 = tag_pill(b, x + w - pad, meta_y, st["tag"], 9.5, 16.0, st["id"])
    dl = b.text(tx, meta_y + 0.25, f"{st['place']}  ·  {st['meta']}", "sans_k", 10.6, col,
                anchor="lm", spacing=0.2, label=f"place:{st['id']}")
    b.fit(f"place:{st['id']}", dl[2], px0, 5.0)

    hsize = 28.0
    while hsize > 23.0 and b.measure(st["headline"], "serif_b", hsize) > tw:
        hsize -= 0.5
    hl_y = meta_y + 29.0
    hb = b.text(tx, hl_y, st["headline"], "serif_b", hsize, INK, anchor="ls", label=f"h{st['id']}")
    b.fit(f"h{st['id']}", hb[2], x + w - pad)

    sub_size = 14.0
    sub_lines = wrap_lines(b, st["subhead"], "sans_s", sub_size, tw)
    if len(sub_lines) > 2:
        raise SystemExit(f"LAYOUT: hero {st['id']} subhead needs {len(sub_lines)} lines")
    sy = hl_y + 18.5
    for i, ln in enumerate(sub_lines):
        sb = b.text(tx, sy + i * 16.0, ln, "sans_s", sub_size, SUB_INK, anchor="ls",
                    label=f"sub{st['id']}:{i}")
        b.fit(f"sub{st['id']}:{i}", sb[2], x + w - pad)


def grid_card(b, st, x, y, w, h):
    col = region_color(st["region"])
    b.rect(x + 1.3, y + 1.6, x + w + 1.3, y + h + 1.6, fill=SHADOW, r=3.0)
    b.rect(x, y, x + w, y + h, fill=CARD_BG, outline=CARD_BORDER, width=0.85, r=3.0)
    b.rect(x, y, x + w, y + 3.0, fill=col, r=1.4)

    art_y = y + 3.0
    art_h = 80.0
    im = art.draw_scene(st["scene"], w - 2.0, art_h, out_scale=K)
    b.img.paste(im, (round((x + 1.0) * K), round(art_y * K)))
    b.hline(x, x + w, art_y + art_h, CARD_BORDER, 0.75)

    numbered_region_pill(b, x + 6.0, art_y + 5.0, st["id"], st["region_pill"], col, 9.6, 17.5)

    pad = 9.0
    tx = x + pad
    tw = w - 2 * pad

    hsize = 18.8
    hl_lines = wrap_lines(b, st["headline"], "serif_b", hsize, tw)
    while len(hl_lines) > 1 and hsize > 16.5:
        hsize -= 0.4
        hl_lines = wrap_lines(b, st["headline"], "serif_b", hsize, tw)
    if len(hl_lines) > 2:
        raise SystemExit(f"LAYOUT: card {st['id']} headline needs {len(hl_lines)} lines")

    hl_lh = hsize * 1.12
    hy = art_y + art_h + 19.5
    for i, ln in enumerate(hl_lines):
        hb = b.text(tx, hy + i * hl_lh, ln, "serif_b", hsize, INK, anchor="ls",
                    label=f"h{st['id']}:{i}")
        b.fit(f"h{st['id']}:{i}", hb[2], x + w - pad)

    sub_size = 12.0
    sub_lines = wrap_lines(b, st["subhead"], "sans_s", sub_size, tw)
    if len(sub_lines) > 2:
        raise SystemExit(f"LAYOUT: card {st['id']} subhead needs {len(sub_lines)} lines")
    sy = hy + (len(hl_lines) - 1) * hl_lh + 15.2
    for i, ln in enumerate(sub_lines):
        sb = b.text(tx, sy + i * 14.0, ln, "sans_s", sub_size, SUB_INK, anchor="ls",
                    label=f"sub{st['id']}:{i}")
        b.fit(f"sub{st['id']}:{i}", sb[2], x + w - pad)

    fg, _ = TAG_STYLE[st["tag"]]
    my = y + h - 7.5
    b.circle(tx + 3.4, my - 3.3, 3.2, fg)
    mb = b.text(tx + 10.5, my, st["meta"], "sans_b", 10.2, MUTED, anchor="ls",
                label=f"meta:{st['id']}")
    b.fit(f"meta:{st['id']}", mb[2], x + w - pad)


def world_atlas(b, x, y, w, h):
    b.text(x, y, "WORLD ATLAS · CARDS 1–10", "sans_k", 9.4, INK, anchor="lt",
           spacing=0.35, label="map-title")
    my = y + 14.0
    mh = h - 54.0  # ~187px crisp natural ratio + spacious 2-row counted legend below
    box = (x, my, w, mh)
    b.rect(x, my, x + w, my + mh, fill=MAP_OCEAN, outline="#102535", width=0.85, r=2.5)

    for lat in (-30, 0, 30, 60):
        _, py = worldmap.project(0, lat, box)
        b.hline(x, x + w, py, MAP_GRID, 0.45)
    for lon in (-120, -60, 0, 60, 120):
        px, _ = worldmap.project(lon, 0, box)
        b.vline(px, my, my + mh, MAP_GRID, 0.45)

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
    ImageDraw.Draw(mask).rounded_rectangle([x * K, my * K, (x + w) * K, (my + mh) * K], radius=2.5 * K, fill=255)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", b.img.size, 0), mask)
    layer.putalpha(alpha)
    b.img.paste(layer, (0, 0), layer)
    b.d = ImageDraw.Draw(b.img, "RGBA")
    b.rect(x, my, x + w, my + mh, outline="#102535", width=0.85, r=2.5)

    geo_leads = S.STORIES[:S.LEADS]
    R = 7.2
    gap = 2 * R + 2.2
    placed = []
    truths = [worldmap.project(st["lon"], st["lat"], box) for st in geo_leads]
    for idx, st in enumerate(geo_leads):
        tx, ty = truths[idx]
        best = None
        bearing = {
            "cop": 10, "gulf": 30, "trade": -150, "baltic": -35,
            "mercury": 150, "caboverde": -135, "sinaloa": 120,
        }.get(st["scene"], -90)
        for ring in range(4):
            rr = ring * 13.5
            for k in range(16 if ring else 1):
                a = math.radians(bearing + (-1 if k % 2 else 1) * ((k + 1) // 2) * 22.5)
                cx, cy = tx + math.cos(a) * rr, ty + math.sin(a) * rr
                if not (x + R + 2 <= cx <= x + w - R - 2 and my + R + 2 <= cy <= my + mh - R - 2):
                    continue
                if any(math.hypot(cx - px, cy - py) < gap for px, py, _ in placed):
                    continue
                if any(j != idx and math.hypot(cx - px, cy - py) < R + 2.0
                       for j, (px, py) in enumerate(truths)):
                    continue
                best = (cx, cy)
                break
            if best:
                break
        if best is None:
            raise SystemExit(f"LAYOUT: no room for pin {st['id']}")
        placed.append((best[0], best[1], st))

    for (cx, cy, st), (tx, ty) in zip(placed, truths):
        if math.hypot(cx - tx, cy - ty) > 0.5:
            b.d.line([(tx * K, ty * K), (cx * K, cy * K)], fill="#FAF6EE", width=round(2.3 * K))
            b.d.line([(tx * K, ty * K), (cx * K, cy * K)], fill=FOLIO_BG, width=K)
            b.circle(tx, ty, 1.9, FOLIO_BG, "#FFFFFF", 0.7)
    for cx, cy, st in placed:
        b.circle(cx, cy, R, region_color(st["region"]), "#FFFFFF", 0.95)
        b.text(cx, cy + 0.25, str(st["id"]), "sans_k", 9.0, "#FFFFFF", anchor="mm", label=f"pin{st['id']}")
        b.pins.append((round(cx, 2), round(cy, 2), R, st["id"]))

    # Spacious 2-row counted regional breadth legend directly under the atlas.
    counts = S.region_counts()
    rows_reg = (S.REGIONS[:4], S.REGIONS[4:])
    b.rect(x, my + mh + 5.0, x + w, y + h, fill="#EFE9DC", outline="#DDD4C2", width=0.6, r=2.0)
    for ri, reg_row in enumerate(rows_reg):
        ky = my + mh + 14.5 + ri * 16.0
        kx = x + 7.0
        for key, label, col in reg_row:
            b.circle(kx + 3.2, ky, 3.2, col)
            txt = f"{label} {counts[key]}"
            bx = b.text(kx + 8.0, ky + 0.2, txt, "sans_b", 8.8, "#1F2937", anchor="lm",
                        label=f"key-{key}")
            b.fit(f"map-key-{key}", bx[2], x + w - 4.0)
            kx = bx[2] + 9.0


def global_wire(b, x, y, w, h):
    items = S.STORIES[S.LEADS:]
    b.text(x, y, f"GLOBAL WIRE · DISPATCHES {S.LEADS + 1}–{len(S.STORIES)}", "sans_k", 9.4, INK,
           anchor="lt", spacing=0.35, label="wire-title")
    b.text(x + w, y, f"00:00–{S.CLOCK}", "sans_b", 9.2, "#3A4452", anchor="rt", label="wire-clock")

    rows = (len(items) + 1) // 2  # 13 rows
    col_gap = 14.0
    colw = (w - col_gap) / 2
    top = 20.5
    lh = (h - top - 5.5) / (rows - 1)  # ~17.9px airy row spacing
    for i, st in enumerate(items):
        c, r = divmod(i, rows)
        cx = x + c * (colw + col_gap)
        cy = y + top + r * lh
        col = region_color(st["region"])
        b.circle(cx + 6.0, cy, 6.0, col)
        b.text(cx + 6.0, cy + 0.25, str(st["id"]), "sans_k", 7.6, "#FFFFFF", anchor="mm", label=f"bd{st['id']}")
        runs = [
            (st["place"], "sans_b", 11.1, BRIEF_INK),
            (" " + st["brief"], "sans_m", 11.1, BRIEF_INK),
            ("  " + st["sources"], "sans_i", 9.8, MUTED),
        ]
        _, right = b.runs(cx + 15.0, cy + 0.2, runs, f"brief{st['id']}", anchor_v="m")
        limit = cx + colw
        if st["tag"]:
            limit = tag_pill(b, limit - 2, cy, st["tag"], 7.4, 11.8, st["id"])
        b.fit(f"brief{st['id']}", right, limit, 4.0)
        if r < rows - 1:
            b.hline(cx + 15.0, cx + colw, cy + lh / 2, "#E6DFD0", 0.5)
    b.vline(x + colw + col_gap / 2, y + 14, y + h - 2, RULE, 0.7)


def wrap_items(b, items, fkey, size, sep_w, maxw, spacing=0.0):
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
    b.rect(M, y0, W - M, y1, fill="#FFF8F5", outline=VERMILION, width=1.1, r=3.0)
    bw = 60.0
    b.rect(M, y0, M + bw, y1, fill=VERMILION, r=3.0)
    b.rect(M + bw - 4, y0, M + bw, y1, fill=VERMILION)
    ym = (y0 + y1) / 2
    b.text(M + bw / 2, ym - 6.8, "DATE", "sans_k", 11.8, "#FFFFFF", anchor="mm", spacing=0.8, label="dc-0")
    b.text(M + bw / 2, ym + 7.2, "CHECK", "sans_k", 11.8, "#FFFFFF", anchor="mm", spacing=0.8, label="dc-1")

    x = M + bw + 9.0
    y_top = y0 + 14.5
    y_bot = y1 - 12.0
    b.hline(x, W - M - 8, ym, "#E6BDB5", 0.65)

    l1 = b.text(x, y_top, "EXCLUDED (Fri & prior):", "sans_k", 10.7, VERMILION, anchor="lm", label="dc-ex-l")
    ex_txt = " · ".join(t for t, _ in S.EXCLUDED) + "."
    t1 = b.text(l1[2] + 6.0, y_top, ex_txt, "sans_m", 11.1, INK, anchor="lm", label="dc-ex-t")
    b.fit("dc-ex-t", t1[2], W - M, 5.0)

    l2 = b.text(x, y_bot, "NOT YET (23:59 UTC):", "sans_k", 10.7, VERMILION, anchor="lm", label="dc-ny-l")
    ny_txt = " · ".join(t for t, _ in S.NOTYET) + "."
    t2 = b.text(l2[2] + 6.0, y_bot, ny_txt, "sans_m", 11.1, INK, anchor="lm", label="dc-ny-t")
    b.fit("dc-ny-t", t2[2], W - M, 5.0)


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
        bx = b.text(cx, cy, desc, "sans_m", ds, SUB_INK, anchor="lm", label=f"vk-d-{tag}")
        cx = bx[2]
    b.fit("vk-bar", cx, W - M, 4.0)


def footer(b, y):
    left = "Strict Saturday UTC window (00:00–23:59 UTC); local time named where it differs. Outcomes hedged where unconfirmed."
    right = "Dispatch Atlas  /  Original illustrations · Natural Earth coastlines"
    bl = b.text(M, y, left, "sans_i", 9.2, "#2F3946", anchor="lm", label="footer-l")
    br = b.text(W - M, y, right, "sans_b", 9.2, "#2F3946", anchor="rm", label="footer-r")
    if bl[2] + 10 > br[0]:
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
    rgb_img = img.convert("RGB")
    w, h = rgb_img.size
    raw = rgb_img.tobytes()
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


def utc_strip(b, y0, y1):
    """Crisp single-line Saturday UTC timeline directly below masthead (zero dense boxes)."""
    b.rect(M, y0, W - M, y1, fill="#F3ECE0", outline="#D6CBB7", width=0.7, r=2.0)
    bw = 78.0
    b.rect(M, y0, M + bw, y1, fill=FOLIO_BG, r=2.0)
    b.rect(M + bw - 3, y0, M + bw, y1, fill=FOLIO_BG)
    ym = (y0 + y1) / 2
    b.text(M + bw / 2, ym + 0.25, "DAY IN UTC", "sans_k", 9.6, FOLIO_GOLD, anchor="mm",
           spacing=0.45, label="utc-hdr")

    n = len(S.TIMELINE)
    x0 = M + bw + 4.0
    cell = (W - M - x0) / n
    for i, (sid, hhmm, label) in enumerate(S.TIMELINE):
        cx = x0 + i * cell
        if i > 0:
            b.vline(cx, y0 + 3.0, y1 - 3.0, "#D8CEBC", 0.6)
        tcol = VERMILION if i in (0, 1, 6) else FOLIO_BG
        bt = b.text(cx + 4.5, ym + 0.3, f"{hhmm}Z", "sans_b", 9.7, tcol, anchor="lm",
                    spacing=0.12, label=f"tl-t{i}")
        bl = b.text(bt[2] + 3.0, ym + 0.3, label, "sans_s", 9.5, INK, anchor="lm",
                    label=f"tl-l{i}")
        br = b.text(cx + cell - 4.0, ym + 0.3, f"#{sid}", "sans_b", 8.6, MUTED, anchor="rm",
                    label=f"tl-n{i}")
        b.fit(f"tl-l{i}", bl[2], br[0], 2.0)


def build():
    S.validate()
    b = Board()
    tsize = masthead(b)
    utc_strip(b, 94.5, 112.0)

    # Top Hero Row: 2 giant unobstructed illustrated panels (489 x 220).
    hy0, hh = 116.5, 220.0
    hgap = 14.0
    hw = (CW - hgap) / 2  # 489.0
    for i, st in enumerate(S.STORIES[:2]):
        hero_card(b, st, M + i * (hw + hgap), hy0, hw, hh)

    # Middle Illustrated Grid: 4 columns x 2 rows = 8 large unobstructed cards (240.5 x 161).
    gy0 = hy0 + hh + 8.0  # 344.5
    ggap = 8.5
    gw = (CW - 3 * ggap) / 4  # 241.625
    gh = 161.0
    for r in range(2):
        for c in range(4):
            st = S.STORIES[2 + r * 4 + c]
            grid_card(b, st, M + c * (gw + ggap), gy0 + r * (gh + ggap), gw, gh)

    # Bottom Global Dispatch Band (y=683..924, h=241): World Atlas + 26-item Airy Wire (13 rows x 2).
    by0 = gy0 + 2 * gh + ggap + 8.0  # 683.0
    bh = 241.0
    map_w = 318.0
    world_atlas(b, M, by0, map_w, bh)
    global_wire(b, M + map_w + 16.0, by0, CW - map_w - 16.0, bh)
    b.vline(M + map_w + 8.0, by0, by0 + bh, RULE, 0.8)

    dc_y0, dc_y1 = by0 + bh + 5.5, by0 + bh + 54.5  # 929.5..978.5 (49px)
    date_check(b, dc_y0, dc_y1)

    vk_y0, vk_y1 = dc_y1 + 4.5, dc_y1 + 22.0  # 983.0..1000.5
    verification_bar(b, vk_y0, vk_y1)

    fy = vk_y1 + 10.5  # 1011.0
    if fy + 6 > H:
        raise SystemExit(f"LAYOUT: page overflows (footer_y={fy:.1f})")
    footer(b, fy)

    bad = overlaps(b.texts)
    if bad:
        raise SystemExit(f"LAYOUT: overlapping text {bad[:8]}")
    for t in b.texts:
        if t[0] < M - 0.5 or t[2] > W - M + 0.5 or t[1] < 0 or t[3] > H:
            raise SystemExit(f"LAYOUT: text outside page margins {t}")

    out = b.img.resize((W, H), Image.BICUBIC)
    brief_slacks = [f[4] for f in b.fits if f[0].startswith("brief")]
    report = dict(
        texts=b.texts, pins=b.pins, fits=b.fits,
        masthead_px=tsize, footer_y=round(fy, 2),
        min_brief_slack=min(brief_slacks) if brief_slacks else None,
        story_count=len(S.STORIES),
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
        f"footer={report['footer_y']}, {len(report['texts'])} text boxes, "
        f"{len(report['pins'])} pins, {report['story_count']} stories"
    )


if __name__ == "__main__":
    main()
