"""Render the Saturday 21 November 2026 front page.

    python3 tools/render.py [--out entry.png] [--report /tmp/report.json]

Draws at 2x (2048 px) and downsamples to 1024 x 1024, then writes a progressive
4:4:4 JPEG (the contest accepts JPEG bytes under the name entry.png). Layout
rules are enforced while drawing: text that would overflow its box, overlap
other text, or a map pin that would touch another pin stops the build.
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

K = 2  # drawing scale
W = H = 1024
M = 16
CW = W - 2 * M

PAPER = "#FAF8F3"
RULE = "#D8D2C5"
INK = "#14181F"
BRIEF_INK = "#11181F"
MUTED = "#5B6270"
RED = "#C8102E"
TAG_COL = {"CONFIRMED": "#2E7D4F", "OFFICIAL": "#2F5D9E", "REPORTED": "#A8650A"}

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
    k = (key, size)
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
        self.fits = []  # (label, right edge, container right, margin)

    # -- primitives in 1x coordinates
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0, r=0):
        box = [x0 * K, y0 * K, x1 * K, y1 * K]
        kw = dict(fill=fill, outline=outline, width=round(width * K) if outline else 0)
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
                       outline=outline, width=round(width * K) if outline else 0)

    def measure(self, s, fkey, size):
        return font(fkey, size).getlength(s) / K

    def text(self, x, y, s, fkey, size, fill=INK, anchor="la", label=None, record=True,
             spacing=0.0):
        f = font(fkey, size)
        if spacing:
            # letter-spaced caps: draw glyph by glyph
            total = sum(f.getlength(ch) / K for ch in s) + spacing * (len(s) - 1)
            if anchor[0] == "r":
                x -= total
            elif anchor[0] == "m":
                x -= total / 2
            cx = x
            for ch in s:
                self.d.text((cx * K, y * K), ch, font=f, fill=fill, anchor="l" + anchor[1])
                cx += f.getlength(ch) / K + spacing
            bb = self.d.textbbox((x * K, y * K), s.replace(" ", "x")[:1], font=f, anchor="l" + anchor[1])
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
        self.fits.append((label, right, limit, margin))
        if right > limit - margin + 1e-6:
            raise SystemExit(f"LAYOUT: '{label}' ends at {right:.1f}, limit {limit - margin:.1f}")


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
        box, right = board.runs(x, y + i * lh, ln, f"{label}:{i}")
        board.fit(f"{label}:{i}", right, x + maxw)
    return y + (len(lines) - 1) * lh


# ------------------------------------------------------------------ blocks
def masthead(b):
    counts = S.region_counts()
    beats = len({s["beat"] for s in S.STORIES})
    b.text(M, 13, "THE WORLD IN ONE DAY", "sans_k", 10.5, RED, anchor="lt", spacing=1.6)
    stats = (f"{len(S.STORIES)} STORIES · {len(counts)} REGIONS · {beats} BEATS · "
             f"EVERY STORY DATED {S.DAY_LABEL.upper()}")
    b.text(W - M, 13, stats, "sans_b", 9.5, INK, anchor="rt")
    b.hline(M, W - M, 29, INK, 1.2)
    b.text(W / 2, 57, S.DAY_LABEL, "serif_b", 46, INK, anchor="mm", label="title")
    b.text(W / 2, 90, S.DECK, "sans_m", 11.5, "#2A303A", anchor="mm", label="deck")
    b.fit("deck", b.measure(S.DECK, "sans_m", 11.5), CW)
    b.hline(M, W - M, 102, INK, 1.2)
    b.hline(M, W - M, 104.5, INK, 0.5)


def kpi_row(b, y0=108, y1=154):
    n = len(S.KPIS)
    cw = CW / n
    for i, k in enumerate(S.KPIS):
        x = M + i * cw
        st = S.story(k["story"])
        col = region_color(st["region"])
        if i:
            b.vline(x, y0 + 3, y1 - 3)
        b.text(x + 10, y0 + 1, k["figure"], "serif_b", 23, col, anchor="lt", label=f"kpi{i}")
        fw = b.measure(k["figure"], "serif_b", 23)
        b.text(x + 14 + fw, y0 + 9, f"#{st['id']}", "sans_k", 8, MUTED, anchor="lt", label=f"kpi{i}n")
        for j, cap in enumerate(k["caption"]):
            bx = b.text(x + 10, y0 + 29 + j * 10.5, cap, "sans", 9.5, INK, anchor="lt", label=f"kpi{i}c{j}")
            b.fit(f"kpi{i}c{j}", bx[2], x + cw, 4)
        b.fit(f"kpi{i}", x + 18 + fw + b.measure(f"#{st['id']}", "sans_k", 8), x + cw, 4)
    b.hline(M, W - M, y1 + 2, RULE, 0.8)


def timeline(b, y0=161, y1=191):
    b.rect(M, y0, W - M, y1, fill="#FFFFFF", outline="#E3DCCB", width=1.0, r=3)
    pw = 96
    b.rect(M + 6, y0 + 8, M + 6 + pw, y1 - 8, fill=RED, r=8)
    b.text(M + 6 + pw / 2, (y0 + y1) / 2, "THE DAY IN UTC", "sans_k", 8.5, "#FFFFFF", anchor="mm",
           label="tl-pill")
    x0 = M + pw + 18
    span = (W - M - 8) - x0
    n = len(S.TIMELINE)
    step = span / n
    ay = y0 + 17
    b.hline(x0 - 4, W - M - 10, ay, "#E9C9C9", 0.8)
    for i, (t, lab) in enumerate(S.TIMELINE):
        x = x0 + i * step
        b.circle(x + 3, ay, 2.2, RED)
        b.text(x + 8, y0 + 11.5, t, "sans_k", 10, RED, anchor="lm", label=f"tl{i}t")
        bx = b.text(x + 1, y1 - 7, lab, "sans_b", 8.6, INK, anchor="lm", label=f"tl{i}l")
        b.fit(f"tl{i}l", bx[2], x + step, 3)


def region_bar(b, y0=197, y1=210):
    counts = S.region_counts()
    total = sum(counts.values())
    assert total == len(S.STORIES) == 35
    b.text(M, (y0 + y1) / 2, "BY REGION", "sans_k", 8, MUTED, anchor="lm", spacing=0.6)
    x = M + 62
    span = W - M - x
    for key, label, col in S.REGIONS:
        seg = span * counts[key] / total
        b.rect(x + 0.5, y0, x + seg - 0.5, y1, fill=col)
        txt = f"{label}  {counts[key]}"
        bx = b.text(x + seg / 2, (y0 + y1) / 2 + 0.3, txt, "sans_k", 8.4, "#FFFFFF", anchor="mm",
                    label=f"rb-{key}")
        b.fit(f"rb-{key}", bx[2], x + seg, 3)
        x += seg


def ribbon(b, x, y, text, col, size, h):
    tw = b.measure(text, "sans_k", size) + size * 1.6
    b.rect(x, y, x + tw, y + h, fill=col)
    b.rect(x, y + h, x + tw, y + h + 1.2, fill=(0, 0, 0, 40))
    b.text(x + size * 0.8, y + h / 2 + 0.3, text, "sans_k", size, "#FFFFFF", anchor="lm",
           label=f"ribbon:{text}")
    return tw


def tag_pill(b, xr, cy, tag, size):
    col = TAG_COL[tag]
    tw = b.measure(tag, "sans_k", size)
    x0 = xr - tw - size * 1.4
    b.rect(x0, cy - size * 0.85, xr, cy + size * 0.85, fill="#FFFFFF", outline=col, width=0.8,
           r=size * 0.85)
    b.text((x0 + xr) / 2, cy + 0.2, tag, "sans_k", size, col, anchor="mm", label=f"tag:{tag}")
    return x0


def meta_line(b, x, y, w, st, size, badge_r):
    col = region_color(st["region"])
    b.circle(x + badge_r, y, badge_r, col)
    b.text(x + badge_r, y + 0.3, str(st["id"]), "sans_k", badge_r * 1.15, "#FFFFFF", anchor="mm",
           label=f"badge{st['id']}")
    px0 = tag_pill(b, x + w, y, st["tag"], size * 0.92)
    bx = b.text(x + badge_r * 2 + 5, y + 0.3, st["place"], "sans_k", size, col, anchor="lm",
                label=f"dateline{st['id']}")
    b.fit(f"dateline{st['id']}", bx[2], px0, 4)


def card(b, st, x, y, w, art_h, lead):
    col = region_color(st["region"])
    im = art.draw_scene(st["id"], w, art_h, out_scale=K)
    b.img.paste(im, (round(x * K), round(y * K)))
    b.rect(x, y, x + w, y + art_h, outline="#C9C1B0", width=0.6)
    if lead:
        ribbon(b, x, y, st["ribbon"], col, 9, 17)
    else:
        ribbon(b, x, y, st["ribbon"], col, 7.4, 13.5)
    my = y + art_h + (10 if lead else 9)
    meta_line(b, x, my, w, st, 9 if lead else 7.6, 8 if lead else 6.6)
    hy = my + (11 if lead else 10)
    hsize, hlh = (15.5, 18.5) if lead else (11.4, 13.4)
    hl = rich_wrap(b, tokens(st["headline"], "serif_b", hsize, INK), w)
    if len(hl) > 2:
        raise SystemExit(f"LAYOUT: headline {st['id']} needs {len(hl)} lines")
    for i, ln in enumerate(hl):
        bx, right = b.runs(x, hy + hsize * 0.98 + i * hlh, ln, f"h{st['id']}:{i}")
        b.fit(f"h{st['id']}:{i}", right, x + w)
    sy = hy + hsize * 0.98 + (len(hl) - 1) * hlh + (16 if lead else 13)
    ssize, slh = (10.6, 13.6) if lead else (9.1, 11.4)
    toks = tokens(st["summary"], "sans", ssize, "#2A303A")
    src = f"({st['sources']})".split()
    toks += [(t, "sans_i", ssize, MUTED) for t in src]
    sl = rich_wrap(b, toks, w)
    limit = 3 if lead else 2
    if len(sl) > limit:
        raise SystemExit(f"LAYOUT: summary {st['id']} needs {len(sl)} lines (max {limit})")
    end = draw_wrapped(b, x, sy, sl, slh, f"s{st['id']}", w)
    return end


def world_map(b, x, y, w, h):
    b.text(x, y, "WHERE IT HAPPENED · PINS 1–13", "sans_k", 9.5, INK, anchor="lt", spacing=0.5,
           label="map-title")
    my = y + 15
    box = (x, my, w, h)
    b.rect(x, my, x + w, my + h, fill="#E6EEF3", outline="#C9D3DA", width=0.6)
    for lat in (-30, 0, 30, 60):
        _, py = worldmap.project(0, lat, box)
        b.hline(x, x + w, py, "#D3DEE6", 0.5)
    for lon in (-120, -60, 0, 60, 120, 180):
        px, _ = worldmap.project(lon, 0, box)
        b.vline(px, my, my + h, "#D3DEE6", 0.5)
    # clip land drawing to the map box
    layer = Image.new("RGBA", b.img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for pts in worldmap.LAND.values():
        ld.polygon([tuple(v * K for v in worldmap.project(lo, la, box)) for lo, la in pts],
                   fill=(214, 205, 186, 255), outline=(176, 165, 142, 255))
    for pts in worldmap.WATER.values():
        ld.polygon([tuple(v * K for v in worldmap.project(lo, la, box)) for lo, la in pts],
                   fill=(230, 238, 243, 255), outline=(176, 165, 142, 255))
    mask = Image.new("L", b.img.size, 0)
    ImageDraw.Draw(mask).rectangle([x * K, my * K, (x + w) * K, (my + h) * K], fill=255)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", b.img.size, 0), mask)
    layer.putalpha(alpha)
    b.img.paste(layer, (0, 0), layer)
    b.d = ImageDraw.Draw(b.img, "RGBA")
    # pins, placed greedily with leader lines where the true spots crowd together
    R = 6.4
    gap = 2 * R + 1.6
    placed = []
    truths = []
    for st in S.STORIES[:13]:
        tx, ty = worldmap.project(st["lon"], st["lat"], box)
        truths.append((tx, ty))
    for idx, st in enumerate(S.STORIES[:13]):
        tx, ty = truths[idx]
        best = None
        for ring in range(0, 9):
            rr = ring * 7.5
            for k in range(16 if ring else 1):
                a = math.radians(-90 + k * 22.5 + (ring % 2) * 11.25)
                cx, cy = tx + math.cos(a) * rr, ty + math.sin(a) * rr
                if not (x + R + 1 <= cx <= x + w - R - 1 and my + R + 1 <= cy <= my + h - R - 1):
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
    for (cx, cy, st), (tx, ty) in zip(placed, truths):
        if math.hypot(cx - tx, cy - ty) > 0.5:
            b.d.line([(tx * K, ty * K), (cx * K, cy * K)], fill=(20, 24, 31, 170), width=round(0.8 * K))
        b.circle(tx, ty, 1.5, INK)
    for cx, cy, st in placed:
        b.circle(cx, cy, R, region_color(st["region"]), "#FFFFFF", 1.0)
        b.text(cx, cy + 0.3, str(st["id"]), "sans_k", 7.6, "#FFFFFF", anchor="mm", record=False)
        b.pins.append((cx, cy, R, st["id"]))
    # region key under the map
    ky = my + h + 9
    kx = x
    for key, label, col in S.REGIONS:
        need = 9 + b.measure(label, "sans_b", 7.4)
        if kx + need > x + w:
            kx, ky = x, ky + 11
        b.circle(kx + 3.5, ky, 3.5, col)
        bx = b.text(kx + 9, ky + 0.2, label, "sans_b", 7.4, MUTED, anchor="lm", label=f"key-{key}")
        b.fit(f"map-key-{key}", bx[2], x + w)
        kx = bx[2] + 7
    return ky + 6


def briefs(b, x, y, w):
    b.text(x, y, "ALSO ON SATURDAY 21 NOVEMBER · 22 MORE STORIES · 14–35", "sans_k", 9.5, INK,
           anchor="lt", spacing=0.5, label="briefs-title")
    rows = 11
    colw = (w - 16) / 2
    lh = 14.6
    items = S.STORIES[13:]
    assert len(items) == 22
    for i, st in enumerate(items):
        c, r = divmod(i, rows)
        cx = x + c * (colw + 16)
        cy = y + 22 + r * lh
        col = region_color(st["region"])
        b.circle(cx + 7, cy, 6.6, col)
        b.text(cx + 7, cy + 0.3, str(st["id"]), "sans_k", 7.2, "#FFFFFF", anchor="mm", label=f"bd{st['id']}")
        runs = [(st["place"], "nar_b", 11, BRIEF_INK), (" " + st["brief"], "nar", 11, BRIEF_INK),
                ("  " + st["sources"], "nar_i", 11, MUTED)]
        _, right = b.runs(cx + 17, cy + 0.2, runs, f"brief{st['id']}", anchor_v="m")
        b.fit(f"brief{st['id']}", right, cx + colw, 6)
        if r < rows - 1:
            b.hline(cx + 17, cx + colw, cy + lh / 2, "#ECE6DA", 0.5)
    b.vline(x + colw + 8, y + 15, y + 22 + (rows - 1) * lh + 7, RULE, 0.6)
    return y + 22 + (rows - 1) * lh + 7


def date_check(b, y0, y1):
    b.rect(M, y0, W - M, y1, fill="#FFF7F5", outline=RED, width=1.0, r=3)
    pw = 74
    b.rect(M + 6, y0 + 6, M + 6 + pw, y0 + 20, fill=RED, r=7)
    b.text(M + 6 + pw / 2, y0 + 13.3, "DATE CHECK", "sans_k", 8.4, "#FFFFFF", anchor="mm",
           label="dc-pill")
    x = M + pw + 14
    maxw = W - M - 8 - x
    t1 = [("Left out as Friday 20 Nov news:", "nar_b", 10, RED)] + \
        [(w, "nar", 10, INK) for w in " · ".join(S.EXCLUDED_FRIDAY).split(" ")]
    t2 = [("Not yet happened at press time:", "nar_b", 10, RED)] + \
        [(w, "nar", 10, INK) for w in " · ".join(S.NOT_YET).split(" ")]
    l1 = rich_wrap(b, [(t[0], t[1], t[2], t[3]) for t in _split_lead(t1)], maxw)
    l2 = rich_wrap(b, [(t[0], t[1], t[2], t[3]) for t in _split_lead(t2)], maxw)
    lines = l1 + l2
    if len(lines) > 3:
        raise SystemExit(f"LAYOUT: date check needs {len(lines)} lines")
    lh = (y1 - y0 - 6) / 3
    draw_wrapped(b, x, y0 + 4 + lh * 0.72, lines, lh, "datecheck", maxw)


def _split_lead(toks):
    out = []
    for s, f, z, c in toks:
        for w in s.split(" "):
            if w:
                out.append((w, f, z, c))
    return out


def footer(b, y):
    left = ("Every story here happened, or was first reported, on Saturday 21 November 2026 (UTC). "
            "Officials' counts and single-side claims are attributed.")
    right = "Sources named beside each story · Original vector drawings"
    bl = b.text(M, y, left, "sans_i", 8.6, "#3A404A", anchor="lm", label="footer-l")
    br = b.text(W - M, y, right, "sans_b", 8.6, "#3A404A", anchor="rm", label="footer-r")
    if bl[2] + 10 > br[0]:
        raise SystemExit("LAYOUT: footer halves collide")


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
    masthead(b)
    kpi_row(b)
    timeline(b)
    region_bar(b)
    # leads
    y = 217
    lw, gap = 320, (CW - 3 * 320) / 2
    ends = []
    for i, st in enumerate(S.STORIES[:3]):
        ends.append(card(b, st, M + i * (lw + gap), y, lw, 132, True))
    y = max(ends) + 10
    b.hline(M, W - M, y, RULE, 0.8)
    y += 8
    sw, sgap = 188, (CW - 5 * 188) / 4
    for row in range(2):
        ends = []
        for c in range(5):
            st = S.STORIES[3 + row * 5 + c]
            ends.append(card(b, st, M + c * (sw + sgap), y, sw, 72, False))
        y = max(ends) + 9
        b.hline(M, W - M, y, RULE, 0.8)
        y += 8
    bottom_top = y
    map_w = 330
    map_h = round(map_w * (74 + 50) / (180 + 132))
    map_end = world_map(b, M, bottom_top, map_w, map_h)
    b.vline(M + map_w + 8, bottom_top, max(map_end, bottom_top + 190), RULE, 0.8)
    br_end = briefs(b, M + map_w + 18, bottom_top, CW - map_w - 18)
    y = max(map_end, br_end) + 6
    dc_h = 35
    date_check(b, y, y + dc_h)
    fy = y + dc_h + 10
    if fy + 6 > H - 2:
        raise SystemExit(f"LAYOUT: page overflows ({fy:.1f})")
    footer(b, fy)
    bad = overlaps(b.texts)
    if bad:
        raise SystemExit(f"LAYOUT: overlapping text {bad[:6]}")
    for t in b.texts:
        if t[0] < M - 0.5 or t[2] > W - M + 0.5 or t[1] < 0 or t[3] > H:
            raise SystemExit(f"LAYOUT: text outside page margins {t}")
    out = b.img.resize((W, H), Image.LANCZOS)
    report = dict(texts=b.texts, pins=b.pins, fits=b.fits, bottom=fy)
    return out, report


def save_jpeg(img, path, quality=89):
    img.save(path, "JPEG", quality=quality, subsampling=0, progressive=True, optimize=True)
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--out", default=os.path.join(root, "entry.png"))
    ap.add_argument("--report")
    ap.add_argument("--quality", type=int, default=89)
    a = ap.parse_args()
    img, report = build()
    q = a.quality
    size = save_jpeg(img, a.out, q)
    while size > 450 * 1024 and q > 80:
        q -= 1
        size = save_jpeg(img, a.out, q)
    report.update(quality=q, size=size)
    if a.report:
        with open(a.report, "w") as fh:
            json.dump(report, fh)
    print(f"wrote {a.out}: {size} bytes, JPEG q{q}, {len(report['texts'])} text boxes, "
          f"{len(report['pins'])} pins")


if __name__ == "__main__":
    main()
