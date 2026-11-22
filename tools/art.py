"""Original silkscreen-editorial illustrations, keyed by subject rather than page position.

Each scene draws into an 8x supersampled Pen in 1x layout coordinates and
downsamples with LANCZOS for razor-sharp printmaking edges. The page lays a
ribbon over the upper left of every scene and a caption bar over everything
below ``Pen.base``, so focal elements are composed above that line and clear
of the ribbon. Everything is 100% deterministic (fixed-seed LCG only).
"""
import math

from PIL import Image, ImageChops, ImageDraw, ImageFont

FONT_DIR = "/usr/share/fonts/truetype"
F_SANS_BLACK = f"{FONT_DIR}/lato/Lato-Black.ttf"
F_SANS_BOLD = f"{FONT_DIR}/lato/Lato-Bold.ttf"


def rgb(hexstr, a=255):
    h = hexstr.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c0, c1, t):
    a, b = rgb(c0), rgb(c1)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


class Rand:
    """Tiny deterministic LCG so every build draws identical textures."""

    def __init__(self, seed):
        self.v = seed & 0xFFFFFFFF

    def next(self):
        self.v = (1664525 * self.v + 1013904223) & 0xFFFFFFFF
        return self.v / 4294967296.0

    def uniform(self, a, b):
        return a + (b - a) * self.next()


class Pen:
    def __init__(self, w, h, scale=8, base=None):
        self.w, self.h, self.s = w, h, scale
        self.base = h if base is None else base  # lowest row the caption bar leaves visible
        self.img = Image.new("RGB", (round(w * scale), round(h * scale)), (250, 246, 238))
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def _pts(self, pts):
        return [(x * self.s, y * self.s) for x, y in pts]

    def poly(self, pts, fill, outline=None, width=0):
        self.d.polygon(self._pts(pts), fill=_c(fill), outline=_c(outline) if outline else None,
                       width=max(1, round(width * self.s)) if outline else 0)

    def rect(self, x0, y0, x1, y1, fill, outline=None, width=0, r=0):
        box = [x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s]
        kw = dict(fill=_c(fill) if fill else None,
                  outline=_c(outline) if outline else None,
                  width=max(1, round(width * self.s)) if outline else 0)
        if r:
            self.d.rounded_rectangle(box, radius=r * self.s, **kw)
        else:
            self.d.rectangle(box, **kw)

    def ellipse(self, cx, cy, rx, ry, fill, outline=None, width=0):
        box = [(cx - rx) * self.s, (cy - ry) * self.s, (cx + rx) * self.s, (cy + ry) * self.s]
        self.d.ellipse(box, fill=_c(fill) if fill else None,
                       outline=_c(outline) if outline else None,
                       width=max(1, round(width * self.s)) if outline else 0)

    def circle(self, cx, cy, r, fill, outline=None, width=0):
        self.ellipse(cx, cy, r, r, fill, outline, width)

    def line(self, pts, fill, width=1.0):
        self.d.line(self._pts(pts), fill=_c(fill), width=max(1, round(width * self.s)),
                    joint="curve")
        r = width / 2
        for x, y in (pts[0], pts[-1]):
            self.ellipse(x, y, r, r, fill)

    def arc(self, cx, cy, r, a0, a1, fill, width=1.0):
        box = [(cx - r) * self.s, (cy - r) * self.s, (cx + r) * self.s, (cy + r) * self.s]
        self.d.arc(box, a0, a1, fill=_c(fill), width=max(1, round(width * self.s)))

    def vgrad(self, y0, y1, c0, c1, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        top, bot = round(y0 * self.s), round(y1 * self.s)
        for yy in range(top, bot):
            t = (yy - top) / max(1, bot - top - 1)
            self.d.line([(x0 * self.s, yy), (x1 * self.s, yy)], fill=mix(c0, c1, t))

    def glow(self, cx, cy, r, color, alpha=120, steps=18):
        base = rgb(color)
        for i in range(steps):
            t = i / steps
            rr = r * (1 - t)
            a = round(alpha * (t ** 1.6) / steps * 3)
            self.ellipse(cx, cy, rr, rr, base[:3] + (min(255, a),))

    def text(self, x, y, s, size, fill, font=F_SANS_BLACK, anchor="mm"):
        f = ImageFont.truetype(font, round(size * self.s))
        self.d.text((x * self.s, y * self.s), s, font=f, fill=_c(fill), anchor=anchor)

    def render(self, out_w, out_h):
        return self.img.resize((out_w, out_h), Image.LANCZOS)


def _c(c):
    if c is None:
        return None
    if isinstance(c, str):
        return rgb(c)
    return c


# ---------------------------------------------------------------- helpers
def ridge(p, base, amp, freq, phase, color, y_floor=None, steps=80):
    y_floor = p.h if y_floor is None else y_floor
    pts = [(0, y_floor)]
    for i in range(steps + 1):
        x = p.w * i / steps
        y = base - amp * (0.6 * math.sin(freq * x / p.w * 6.283 + phase)
                          + 0.4 * math.sin(freq * 2.3 * x / p.w * 6.283 + phase * 1.7))
        pts.append((x, y))
    pts.append((p.w, y_floor))
    p.poly(pts, color)


def waves(p, y0, y1, c_top, c_bot, crest="#FFFFFF", n=4, seed=3):
    p.vgrad(y0, y1, c_top, c_bot)
    rnd = Rand(seed)
    for row in range(n):
        y = y0 + (y1 - y0) * (row + 0.55) / n
        x = rnd.uniform(-8, 0)
        while x < p.w:
            L = rnd.uniform(6, 15) * (0.6 + row / n)
            p.line([(x, y), (x + L, y)], rgb(crest, 65 + row * 12), 0.65)
            x += L + rnd.uniform(6, 15)


def stars(p, n, seed, y1=None, color="#FFFFFF"):
    rnd = Rand(seed)
    y1 = p.h if y1 is None else y1
    for _ in range(n):
        x, y = rnd.uniform(0, p.w), rnd.uniform(0, y1)
        r = rnd.uniform(0.3, 0.85)
        p.circle(x, y, r, rgb(color, round(rnd.uniform(110, 255))))


def smoke(p, x, y, dx, dy, r0, r1, n, color, alpha=165, seed=9):
    rnd = Rand(seed)
    for i in range(n):
        t = i / max(1, n - 1)
        cx = x + dx * t + rnd.uniform(-1.5, 1.5)
        cy = y + dy * t + rnd.uniform(-1.0, 1.0)
        r = r0 + (r1 - r0) * t
        p.circle(cx, cy, r, rgb(color, round(alpha * (1 - 0.5 * t))))


def flames(p, cx, base, w, h, seed=5):
    rnd = Rand(seed)
    for layer, col in enumerate(("#A82824", "#EE6A1F", "#FFB23F", "#FFE999")):
        k = 1 - layer * 0.22
        pts = [(cx - w / 2 * k, base)]
        tongues = 5
        for i in range(tongues):
            x0 = cx - w / 2 * k + w * k * (i + 0.5) / tongues
            pts.append((x0 - w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
            pts.append((x0 + rnd.uniform(-0.7, 0.7), base - h * k * rnd.uniform(0.75, 1.0)))
            pts.append((x0 + w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
        pts.append((cx + w / 2 * k, base))
        p.poly(pts, col)


def seismo(p, x0, x1, y, amp, color, seed=7, width=1.1, burst=0.5):
    rnd = Rand(seed)
    pts = []
    n = 150
    for i in range(n + 1):
        t = i / n
        env = math.exp(-((t - burst) ** 2) / 0.007) + 0.06
        pts.append((x0 + (x1 - x0) * t, y + amp * env * rnd.uniform(-1, 1)))
    p.line(pts, color, width)


def starburst(p, cx, cy, r_out, r_in, col_out, col_in, rays=8):
    for scale, col in ((1.0, col_out), (0.56, col_in)):
        pts = []
        for k in range(rays * 2):
            a = math.radians(-90 + k * (180 / rays))
            r = (r_out if k % 2 == 0 else r_in) * scale
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        p.poly(pts, col)


# ------------------------------------------------------------------ scenes
def scene_cop31(p):
    """Antalya: oil derrick, turbines and a draft still awaiting adoption."""
    w, h, g = p.w, p.h, p.base
    water = g - 13
    base = water + 4.5
    p.vgrad(0, water, "#F2C794", "#FBF0DC")
    p.glow(w * 0.65, water * 0.80, h * 0.72, "#FFE3A6", 145)
    ridge(p, water - 11.5, h * 0.09, 1.5, 0.7, "#C8A488", y_floor=water + 2)
    ridge(p, water - 4.6, h * 0.06, 2.3, 1.9, "#A37F6A", y_floor=water + 2)
    waves(p, water, h, "#2D7899", "#174A66", n=5, seed=11)

    # Lower left: a compact oil derrick, kept below the ribbon and sub-tag.
    dx = w * 0.13
    p.poly([(dx - 9, base), (dx - 2, base - 29), (dx + 2, base - 29), (dx + 9, base)],
           None, "#322723", 1.3)
    for k in range(1, 4):
        yy = base - k * 7.2
        half = 9 - k * 1.7
        p.line([(dx - half, yy), (dx + half, yy)], "#322723", 0.9)
    p.rect(dx + 5, base - 19, dx + 24, base - 15.5, "#322723")
    p.poly([(dx + 22, base - 23), (dx + 29, base - 17.2), (dx + 22, base - 11.5)], "#322723")

    # Lower middle: the plenary pavilion and delegate flags.
    hx0, hx1 = w * 0.28, w * 0.60
    p.rect(hx0, base - 16, hx1, base, "#F2ECE0", "#7D6F61", 0.7)
    p.poly([(hx0 - 5, base - 16), ((hx0 + hx1) / 2, base - 27), (hx1 + 5, base - 16)],
           "#DED2BF", "#7D6F61", 0.7)
    for i in range(8):
        x = hx0 + 6 + i * (hx1 - hx0 - 12) / 7
        p.rect(x - 1.9, base - 12, x + 1.9, base, "#B4A592")
    flag_cols = ["#A82824", "#1F4A6E", "#266B47", "#E6B422", "#186F7A", "#C82828", "#2B7A4B", "#264E86"]
    for i, c in enumerate(flag_cols):
        x = hx0 + i * (hx1 - hx0) / (len(flag_cols) - 1)
        p.line([(x, base), (x, base - 24)], "#4B423A", 0.55)
        p.rect(x, base - 24, x + 5.6, base - 20, c)

    # Right: two white wind turbines in the open sky.
    for tx, th, ang in ((w * 0.885, 56, 14), (w * 0.962, 44, 48)):
        top = base - th
        p.poly([(tx - 1.5, base), (tx - 0.6, top), (tx + 0.6, top), (tx + 1.5, base)], "#FFFFFF", "#8C9CA6", 0.4)
        for k in range(3):
            a = math.radians(ang + k * 120)
            p.line([(tx, top), (tx + math.cos(a) * th * 0.38, top + math.sin(a) * th * 0.38)], "#FFFFFF", 1.7)
        p.circle(tx, top, 1.7, "#3B4A54")

    # An unsigned draft, not a gavel implying adoption.
    x, y = w * 0.625, 8
    for offset in (5, 2.5, 0):
        p.rect(x + offset, y + offset, x + 54 + offset, y + 50 + offset, "#FFF8E7", "#9F866D", 0.8)
    p.rect(x + 4, y + 5, x + 50, y + 21, "#204859")
    p.text(x + 27, y + 13.2, "DRAFT", 10.6, "#FFFFFF")
    for row, length in enumerate((38, 30, 42, 24)):
        yy = y + 27 + row * 4.2
        p.line([(x + 5, yy), (x + 5 + length, yy)], "#A2917C", 0.9)
    p.line([(x + 24, y + 46.5), (x + 46, y + 43.5)], "#AF392F", 1.5)


def scene_gulf_hero(p):
    """Persian Gulf diptych: Bahrain industrial plant fire on left, two Hormuz tankers + compass on right."""
    w, h, g = p.w, p.h, p.base
    sea = g * 0.56
    p.vgrad(0, sea, "#DFAA7B", "#FAF0DC")
    p.glow(w * 0.68, sea * 0.85, h * 0.54, "#FFE3A6", 110)

    # Layered Musandam / Khasab headlands behind the Strait of Hormuz.
    ridge(p, sea - 10.5, h * 0.11, 1.4, 0.4, "#BA8D66", y_floor=sea + 2)
    ridge(p, sea - 3.8, h * 0.07, 2.2, 1.6, "#8E6346", y_floor=sea + 2)
    waves(p, sea, h, "#2B7A96", "#15455C", n=5, seed=15)

    # Left shore: Bahrain industrial facility silhouette with fire & smoke plume (clear below sub-tag).
    bx_end = w * 0.345
    smoke(p, w * 0.255, g - 15, 22, -25, 2.8, 7.8, 12, "#2E303A", 165, seed=13)
    p.glow(w * 0.245, g - 11, 22, "#FFBD63", 175, steps=10)
    flames(p, w * 0.245, g - 6, 17, 19, seed=7)
    for sx, top in ((14, g - 26), (22, g - 22), (92, g - 25)):
        p.poly([(sx, h), (sx + 1, top), (sx + 3.5, top), (sx + 5, h)], "#2C2E3E")
        p.line([(sx + 1, top + 3.5), (sx + 3.5, top + 3.5)], "#E5C19F", 0.9)
    roof = [(0, h), (0, g - 8)]
    for x in range(0, int(bx_end), 18):
        roof.extend([(x + 13, g - 15), (x + 13, g - 8)])
    p.poly(roof + [(bx_end + 8, g - 5), (bx_end + 14, h)], "#182839")
    for x in range(6, int(bx_end) - 4, 9):
        p.rect(x, g - 5.2, x + 3.6, g - 2.6, "#F2CA85")

    # Right sea lane: distant outbound tanker off Khasab with alert beacon arcs.
    tx2, ty2 = w * 0.785, sea + (g - sea) * 0.34
    p.line([(tx2 - 30, ty2 + 3.0), (tx2 - 12, ty2 + 3.0)], rgb("#D8F1F8", 145), 0.7)
    p.poly([(tx2 - 20, ty2 - 2.4), (tx2 + 19, ty2 - 2.4), (tx2 + 24, ty2 - 5.2),
            (tx2 + 18, ty2 + 3.0), (tx2 - 19, ty2 + 3.0)], "#6F2829")
    p.rect(tx2 - 19, ty2 - 4.0, tx2 + 17, ty2 - 2.3, "#3B434E")
    p.rect(tx2 - 19, ty2 - 10.0, tx2 - 12, ty2 - 4.0, "#F6F2E9", "#7C756A", 0.35)
    p.rect(tx2 - 17, ty2 - 12.8, tx2 - 14.5, ty2 - 10.0, "#B0322E")
    for k in range(3):
        p.circle(tx2 - 7 + k * 7.8, ty2 - 4.8, 1.7, "#58626E")
    for rr, al in ((8.8, 195), (13.8, 130)):
        p.arc(tx2 + 3, ty2 - 4, rr, 200, 340, rgb("#D43D2C", al), 1.0)

    # Mid-foreground outbound tanker in the Strait of Hormuz.
    tx1, ty1 = w * 0.56, g - 10.2
    p.line([(tx1 - 46, ty1 + 4.4), (tx1 - 26, ty1 + 4.4)], rgb("#D8F1F8", 160), 0.85)
    p.poly([(tx1 - 31, ty1 - 3.5), (tx1 + 27, ty1 - 3.5), (tx1 + 33, ty1 - 7.5),
            (tx1 + 25, ty1 + 4.4), (tx1 - 29, ty1 + 4.4)], "#862B28")
    p.rect(tx1 - 29, ty1 - 5.6, tx1 + 24, ty1 - 3.5, "#38414C")
    p.rect(tx1 - 29, ty1 - 14.0, tx1 - 18, ty1 - 5.6, "#F7F3EA", "#6F685E", 0.4)
    p.rect(tx1 - 26.5, ty1 - 17.5, tx1 - 23, ty1 - 14.0, "#1F4A6E")
    for k in range(4):
        p.circle(tx1 - 12 + k * 9.0, ty1 - 6.7, 2.1, "#5B6572")
    for rr, al in ((10.0, 205), (15.5, 135)):
        p.arc(tx1 + 6, ty1 - 5.5, rr, 205, 335, rgb("#D43D2C", al), 1.1)

    # Archival nautical compass rose in the clear upper-right sky.
    cx, cy, cr = w * 0.895, 29.0, 18.0
    p.circle(cx, cy, cr, "#FAF2E1", "#6D5E4C", 0.95)
    p.circle(cx, cy, cr - 2.6, None, "#C8B89E", 0.5)
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        inner = cr - (4.2 if angle % 90 == 0 else 2.5)
        p.line([(cx + inner * math.sin(a), cy - inner * math.cos(a)),
                (cx + (cr - 0.8) * math.sin(a), cy - (cr - 0.8) * math.cos(a))], "#6B6156", 0.75)
    p.poly([(cx - 3.6, cy), (cx, cy - 12.2), (cx + 3.6, cy)], "#B22222")
    p.poly([(cx - 3.6, cy), (cx, cy + 12.2), (cx + 3.6, cy)], "#1F4A6E")
    p.circle(cx, cy, 2.2, "#F0C66E", "#4A3E30", 0.5)
    p.text(cx, cy - cr - 3.6, "N", 6.8, "#5A4634")


def scene_peru_hero(p):
    """Central Peru: Andean houses above an illustrative seismograph."""
    w, h, g = p.w, p.h, p.base
    sy0 = g - 29
    ground = sy0 + 1
    H = ground / 0.70
    p.vgrad(0, ground, "#9DC7E6", "#F4EFE5")
    # Snow-capped Junin Andes across the middle and right, clear of the ribbon.
    peaks = [(-8, 0.95), (w * 0.20, 0.56), (w * 0.38, 0.60), (w * 0.55, 0.22),
             (w * 0.68, 0.46), (w * 0.79, 0.12), (w * 0.90, 0.36), (w * 0.97, 0.20), (w + 8, 0.78)]
    pts = [(-8, h)] + [(x, H * y) for x, y in peaks] + [(w + 8, h)]
    p.poly(pts, "#79685A")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2 and x1 > w * 0.45:
            px, py = x1, H * y1
            p.poly([(px, py), (px - 14, py + 15), (px - 5, py + 11), (px, py + 18),
                    (px + 6, py + 11), (px + 14, py + 15)], "#FFFFFF")
    ridge(p, H * 0.68, H * 0.04, 1.8, 0.4, "#5E8046", y_floor=H * 0.76)

    # Adobe houses with tremor arcs.
    for hx, sc in ((w * 0.62, 0.95), (w * 0.74, 1.1), (w * 0.86, 0.9)):
        hy = ground
        p.poly([(hx - 8 * sc, hy), (hx + 8 * sc, hy - 1.5), (hx + 6.5 * sc, hy - 14 * sc),
                (hx - 9.5 * sc, hy - 12.5 * sc)], "#F7EBD5", "#5C4736", 0.75)
        p.poly([(hx - 11.5 * sc, hy - 12 * sc), (hx - 1.5 * sc, hy - 20 * sc),
                (hx + 9 * sc, hy - 14 * sc)], "#B8472F", "#5C4736", 0.7)
        p.rect(hx - 3 * sc, hy - 8 * sc, hx + 1.5 * sc, hy - 2 * sc, "#6E523F")
    p.arc(w * 0.74 - 1, ground - 11, 17, 195, 250, "#A82824", 1.1)
    p.arc(w * 0.74 - 1, ground - 11, 17, 295, 350, "#A82824", 1.1)

    # Full-width cream seismograph strip, entirely above the caption bar.
    p.rect(0, sy0, w, h, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#B8AE9A", 0.8)
    for k in range(1, 20):
        p.line([(w * k / 20, sy0), (w * k / 20, h)], "#ECE4D6", 0.45)
    seismo(p, 6, w - 6, sy0 + 15.5, 12.2, "#C82222", seed=12, width=1.45, burst=0.60)
    p.rect(w * 0.66, sy0 + 3.5, w * 0.66 + 56, sy0 + 19, "#A82824", r=2)
    p.text(w * 0.66 + 28, sy0 + 11.4, "M 6.7", 10.6, "#FFFFFF")


def scene_baltic(p):
    """Gulf of Finland: Sparta II burning at sea with a rescue lifeboat pulling clear."""
    w, h, g = p.w, p.h, p.base
    sea = g * 0.56
    p.vgrad(0, sea, "#46637B", "#C4D6DF")
    ridge(p, sea - 1.5, h * 0.08, 1.5, 0.5, "#324959", y_floor=sea + 2)
    waves(p, sea, h, "#21516B", "#112E42", crest="#D8ECF5", n=5, seed=23)

    # Smoke plume drifting cleanly into the open upper-right sky clear of the ribbon.
    sx, sy = w * 0.68, g - 9.5
    smoke(p, sx + 4, sy - 6, 30, -28, 3.0, 9.8, 16, "#2C3038", 185, seed=19)
    p.glow(sx + 2, sy - 4, 22, "#FFA84C", 170, steps=12)

    # Russian Ro-Ro cargo vessel Sparta II.
    p.poly([(sx - 32, sy - 2), (sx + 26, sy - 2), (sx + 32, sy - 6.5),
            (sx + 24, sy + 5), (sx - 30, sy + 5)], "#3F4B56", "#1D2630", 0.5)
    p.rect(sx - 30, sy + 2.2, sx + 25, sy + 4.8, "#8A342A")
    p.rect(sx - 28, sy - 10.5, sx - 17, sy - 2, "#E8E3D8", "#4D5864", 0.45)
    p.rect(sx - 25, sy - 13.5, sx - 20.5, sy - 10.5, "#6C7782")
    p.rect(sx - 12, sy - 6.5, sx + 13, sy - 2, "#5D6B77")
    flames(p, sx + 4, sy - 2.2, 16, 17, seed=31)

    # Bright orange lifeboat rowing clear in the foreground left.
    lx, ly = w * 0.21, g - 5.0
    p.poly([(lx - 11.5, ly - 1.6), (lx + 11.5, ly - 1.6), (lx + 8.5, ly + 2.8),
            (lx - 8.5, ly + 2.8)], "#E85D22", "#8C2C0C", 0.5)
    p.rect(lx - 6.0, ly - 4.4, lx + 5.0, ly - 1.6, "#FFF7EB")
    p.line([(lx + 12, ly + 2.4), (lx + 27, ly + 2.4)], rgb("#E6F4FA", 170), 0.75)


def scene_caboverde(p):
    """Praia, Cabo Verde: volcanic island horizon, ballot box and 63.96% tally board."""
    w, h, g = p.w, p.h, p.base
    sea = g * 0.65
    p.vgrad(0, sea, "#D89355", "#F9E7C2")
    ridge(p, sea - 3.5, h * 0.12, 1.3, 1.1, "#82614B", y_floor=sea + 2)
    ridge(p, sea + 0.5, h * 0.06, 2.0, 2.4, "#5D4537", y_floor=sea + 2)
    waves(p, sea, h, "#1E5686", "#113355", crest="#F6E2B3", n=4, seed=41)

    # Archival ballot box positioned cleanly below the upper-left ribbon.
    bx, by = w * 0.50, g - 1.5
    p.rect(bx - 19, by - 16.5, bx + 19, by, "#F7F1E3", "#182A40", 0.85, r=1.2)
    p.rect(bx - 18.2, by - 9.2, bx + 18.2, by - 6.0, "#1F4E8C")
    p.rect(bx - 18.2, by - 6.0, bx + 18.2, by - 4.5, "#FFFFFF")
    p.rect(bx - 18.2, by - 4.5, bx + 18.2, by - 2.8, "#C42B2B")
    p.rect(bx - 9, by - 15.0, bx + 9, by - 13.5, "#182A40")
    p.poly([(bx - 5.5, by - 14.5), (bx - 2.0, by - 25.0), (bx + 8.5, by - 23.0),
            (bx + 5.0, by - 14.5)], "#FFFFFF", "#182A40", 0.7)
    p.line([(bx - 0.5, by - 20.0), (bx + 1.5, by - 18.0), (bx + 5.0, by - 22.2)], "#1F7A4D", 1.3)

    # Dark-and-gold tally board in the clear upper-right.
    p.rect(w - 53, 4, w - 4, 24, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w - 28.5, 14.3, "63.96%", 10.2, "#FFD23F")


def scene_bandasea(p):
    """Banda Sea M6.8: Timor-Leste bathymetric chart, concentric tremor rings and seismograph."""
    w, h, g = p.w, p.h, p.base
    sy0 = g - 16.5
    p.vgrad(0, sy0, "#153A52", "#225B78")
    for k in range(1, 5):
        p.line([(w * k / 5, 0), (w * k / 5, sy0)], rgb("#397694", 95), 0.45)
    p.line([(0, sy0 * 0.55), (w, sy0 * 0.55)], rgb("#397694", 95), 0.45)

    # Stylized Timor-Leste below the ribbon and Banda Arc islands on the right.
    timor = [(w * 0.14, sy0 - 1.5), (w * 0.28, sy0 - 7.5), (w * 0.52, sy0 - 9.5),
             (w * 0.64, sy0 - 7.0), (w * 0.54, sy0 - 2.5), (w * 0.34, sy0 + 0.5)]
    p.poly(timor, "#DFCFAF", "#8A7A62", 0.7)
    for ix, iy, rx, ry in ((w * 0.72, sy0 - 10, 5.0, 1.8), (w * 0.92, sy0 - 8, 4.5, 1.8)):
        p.ellipse(ix, iy, rx, ry, "#DFCFAF", "#8A7A62", 0.55)

    # Concentric seismic epicenter rings clearly visible to the right of the ribbon.
    ex, ey = w * 0.875, 17.5
    for rr, al in ((13.0, 125), (8.8, 185), (5.0, 235)):
        p.circle(ex, ey, rr, None, rgb("#F0543E", al), 1.1)
    p.circle(ex, ey, 2.5, "#FFD24C", "#B22222", 0.7)

    # Clean cream seismograph strip above the caption bar.
    p.rect(0, sy0, w, h, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#B8AE9A", 0.75)
    for k in range(1, 14):
        p.line([(w * k / 14, sy0), (w * k / 14, h)], "#ECE4D6", 0.4)
    seismo(p, 4, w - 48, sy0 + 8.5, 6.6, "#C82222", seed=33, width=1.2, burst=0.52)
    p.rect(w - 44, sy0 + 2.0, w - 4, sy0 + 14.5, "#A82824", r=1.8)
    p.text(w - 24, sy0 + 8.5, "M 6.8", 9.2, "#FFFFFF")


def scene_bepicolombo(p):
    w, h, g = p.w, p.h, p.base
    p.vgrad(0, h, "#070D21", "#162447")
    stars(p, 64, 21, y1=g)
    # Warm solar rim glow from the lower left.
    p.glow(-8, g * 0.92, 50, "#FFE299", 140, steps=18)

    # Cratered Mercury on the right; the ribbon and caption bar crop it to a lit limb.
    mx, my, mr = w * 0.845, g * 0.74, g * 0.52
    p.circle(mx, my, mr, "#4A4642")
    sphere = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(sphere).ellipse([(mx - mr) * p.s, (my - mr) * p.s, (mx + mr) * p.s, (my + mr) * p.s],
                                   fill=255)
    lit = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(lit).ellipse([(mx - mr * 1.28) * p.s, (my - mr * 1.04) * p.s,
                                 (mx + mr * 0.35) * p.s, (my + mr * 1.04) * p.s], fill=255)
    p.img.paste(Image.new("RGB", p.img.size, (182, 173, 158)), (0, 0), ImageChops.multiply(sphere, lit))
    p.d = ImageDraw.Draw(p.img, "RGBA")
    rnd = Rand(44)
    for _ in range(40):
        a, rr = rnd.uniform(0, 6.283), mr * math.sqrt(rnd.next()) * 0.88
        cx, cy = mx + math.cos(a) * rr, my + math.sin(a) * rr
        if cy > h + 3 or cx > w + 3:
            continue
        cr = rnd.uniform(1.0, 3.6)
        is_lit = cx < mx - mr * 0.08
        p.ellipse(cx, cy, cr, cr * 0.85, rgb("#7B746A" if is_lit else "#3E3A36", 225))
        p.arc(cx, cy, cr, 200, 340, rgb("#DAD2C5" if is_lit else "#68625B", 215), 0.5)
    p.circle(mx, my, mr, None, rgb("#D8D0C2", 140), 0.9)

    # Show the approach, not a closed orbit that telemetry has not established.
    def path(v):
        return w * (.03 + .65 * v), g * (.99 - .50 * v * v)
    for i in range(22):
        p.line([path(i / 22), path((i + .58) / 22)], "#86B6CD", .9)

    # Stacked spacecraft riding the approach path: gold MPO, white Mio, blue solar wing.
    sx, sy = path(.56)
    p.glow(sx + 12, sy, 8.5, "#8BE0FF", 210, steps=10)
    p.line([(sx + 6, sy), (sx + 20, sy)], rgb("#A8E6FF", 210), 2.4)
    p.rect(sx - 44, sy - 3.6, sx - 9, sy + 3.6, "#285094", "#A4C2E8", 0.55)
    for k in range(1, 6):
        gx = sx - 44 + k * 35 / 6
        p.line([(gx, sy - 3.6), (gx, sy + 3.6)], rgb("#A4C2E8", 160), 0.4)
    p.line([(sx - 44, sy), (sx - 9, sy)], rgb("#A4C2E8", 160), 0.4)
    p.rect(sx - 9, sy - 0.8, sx - 6, sy + 0.8, "#C0C6CE")
    p.rect(sx - 6, sy - 6, sx + 6, sy + 6, "#E3AF44", "#8A641E", 0.6)
    p.line([(sx - 6, sy), (sx + 6, sy)], rgb("#8A641E", 170), 0.45)
    p.poly([(sx - 4.2, sy - 6), (sx + 4.2, sy - 6), (sx + 3.0, sy - 11.5), (sx - 3.0, sy - 11.5)],
           "#F2F4F7", "#8B95A2", 0.45)
    p.ellipse(sx, sy - 11.5, 3.0, 1.1, "#FFFFFF")


def scene_vegas_pole(p):
    """Las Vegas qualifying: night Strip circuit, a car on the grid and the P1 board."""
    w, h, g = p.w, p.h, p.base
    road = g * 0.50
    p.vgrad(0, road, "#142038", "#263A5C")
    p.rect(0, road, w, h, "#252C36")
    for lx, col in ((96, "#FF4D6D"), (114, "#4CC9F0"), (132, "#F7B801"), (150, "#7209B7")):
        p.rect(lx, road - 15, lx + 11, road, rgb(col, 68))
    fx = w * 0.80
    for r in range(7):
        for c in range(2):
            col = "#FFFFFF" if (r + c) % 2 == 0 else "#181C22"
            p.rect(fx + c * 5, road + r * 5.2, fx + (c + 1) * 5, road + (r + 1) * 5.2, col)

    cx, cy = w * 0.42, g - 12.5
    p.poly([(cx - 38, cy + 3), (cx - 32, cy - 8), (cx - 10, cy - 8), (cx + 2, cy - 10.5),
            (cx + 18, cy - 3.5), (cx + 42, cy + 1), (cx + 42, cy + 5), (cx - 38, cy + 5)],
           "#1A2B56", "#88A4D8", 0.6)
    p.rect(cx - 24, cy - 2.5, cx + 22, cy + 1.5, "#D9242E")
    p.poly([(cx + 30, cy - 1), (cx + 42, cy + 1), (cx + 42, cy + 4.5), (cx + 30, cy + 4)], "#F4C430")
    p.rect(cx - 42, cy - 11.5, cx - 34, cy - 2, "#131822")
    p.circle(cx - 2, cy - 9.5, 3.0, "#F4C430")
    for wx in (cx - 24, cx + 24):
        p.circle(wx, cy + 4, 5.8, "#12161C")
        p.circle(wx, cy + 4, 2.5, "#D9242E")

    p.rect(w - 38, 5, w - 5, 23, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w - 21.5, 14.2, "P1", 11.4, "#FFD23F")


def scene_rahul(p):
    w, h, g = p.w, p.h, p.base
    turf = g * 0.50
    p.vgrad(0, turf, "#8AC4E8", "#DCEFF9")
    ridge(p, turf - 1.4, h * 0.06, 1.4, 0.9, "#6A9472", y_floor=turf + 3)
    p.rect(0, turf, w, h, "#258C42")
    for k in range(1, 5):
        p.ellipse(w * 0.5, g * 0.94, w * 0.62 * (1 - k * 0.18), g * 0.60 * (1 - k * 0.18),
                  None, rgb("#38AC58", 130), 1.6)
    p.rect(w * 0.44, turf + 5, w * 0.54, h, "#E3CFA0")
    for dx in (-2.0, 0, 2.0):
        p.line([(w * 0.49 + dx, turf + 12), (w * 0.49 + dx, turf + 5)], "#FFFFFF", 0.8)

    p.poly([(w * 0.18, g - 2.5), (w * 0.29, turf + 4.5), (w * 0.36, turf + 6), (w * 0.25, g - 1)],
           "#E9C584", "#7B5B2A", 0.9)
    p.line([(w * 0.325, turf + 5), (w * 0.36, turf - 3)], "#1F4A6E", 2.5)
    p.circle(w * 0.63, turf + 4.5, 5.2, "#B81D24", "#FFFFFF", 0.6)
    p.arc(w * 0.63, turf + 4.5, 3.4, 110, 250, "#FFFFFF", 0.65)

    # Dark-and-gold scoreboard in the clear upper right.
    p.rect(w * 0.72, 5, w - 5, 29, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w * 0.85, 17.5, "136", 12.0, "#FFD23F")


def scene_trade(p):
    """EU-Indonesia CEPA: container vessel crossing open waters + 98.5% tariff-cut plaque."""
    w, h, g = p.w, p.h, p.base
    sea = g * 0.58
    p.vgrad(0, sea, "#9AC0DC", "#F5EFE3")
    ridge(p, sea - 1.5, h * 0.06, 1.3, 0.9, "#B6C4CC", y_floor=sea + 2)
    waves(p, sea, h, "#215B7E", "#123852", crest="#E3F2FA", n=4, seed=47)

    # Stylized deep-water container vessel carrying EU-navy, gold, crimson & ivory containers.
    sx, sy = w * 0.48, g - 8.5
    p.line([(sx - 66, sy + 4.8), (sx - 44, sy + 4.8)], rgb("#E6F4FA", 170), 0.85)
    p.poly([(sx - 44, sy - 2.0), (sx + 40, sy - 2.0), (sx + 48, sy - 7.0),
            (sx + 38, sy + 5.2), (sx - 41, sy + 5.2)], "#1D3248", "#0F1D2C", 0.55)
    p.rect(sx - 41, sy + 2.6, sx + 39, sy + 5.0, "#A9302A")
    # Stern bridge tower.
    p.rect(sx - 38, sy - 13.5, sx - 25, sy - 2.0, "#F8F4EC", "#394856", 0.5)
    p.rect(sx - 35.5, sy - 10.8, sx - 27.5, sy - 8.6, "#1F4E8C")
    p.rect(sx - 34, sy - 16.5, sx - 29.5, sy - 13.5, "#E0AF38")
    # Stacked containers cleanly below the upper-left ribbon.
    cols = (
        ("#1F4E8C", "#C42B2B", "#E0AF38"),
        ("#C42B2B", "#1F4E8C", "#F6F1E4"),
        ("#E0AF38", "#2B6B4F", "#1F4E8C"),
        ("#1F4E8C", "#C42B2B", "#F6F1E4"),
        ("#C42B2B", "#E0AF38", "#1F4E8C"),
    )
    for ci, stack in enumerate(cols):
        cx0 = sx - 21 + ci * 11.8
        for ri, col in enumerate(stack):
            cy1 = sy - 2.0 - ri * 4.4
            p.rect(cx0, cy1 - 3.9, cx0 + 10.6, cy1, col, "#142230", 0.35)

    # Dark-and-gold tariff-line cut plaque in the clear upper-right.
    p.rect(w - 50, 4, w - 4, 24, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w - 27, 14.3, "98.5%", 10.4, "#FFD23F")


def scene_flood(p):
    w, h, g = p.w, p.h, p.base
    p.vgrad(0, h, "#728B99", "#DDE6D4")
    ridge(p, g * .60, 4, 1.6, 1.2, "#688576")
    waves(p, g * .69, h, "#6698A1", "#356476", n=5)
    x = w * .86
    p.rect(x, 7, x + 11, h, "#E9DCAD", "#344855", 1)
    for i in range(12):
        yy = 11 + i * 4
        p.line([(x + 1, yy), (x + (7 if i % 2 else 4), yy)], "#8F4739", 1)
    for i in range(6):
        xx = 8 + i * 21
        p.line([(xx, g * .79), (xx + 7, g * .79)], "#CCDDD4", .9)


def scene_sinaloa(p):
    # Small Gulf of California locator, with Guasave on the mainland shore.
    w, h = p.w, p.h
    p.rect(0, 0, w, h, "#C2DADD")
    def xy(lon, lat):
        return (lon + 114) * w / 8, (29 - lat) * 70 / 6.5
    baja = [(-114, 29), (-112.9, 29), (-112.3, 27.9), (-111.7, 27.5), (-111.4, 26.4),
            (-111.0, 25.6), (-110.7, 24.8), (-109.9, 24.0), (-109.4, 23.5),
            (-109.9, 22.9), (-110.4, 23.7), (-111.8, 24.5), (-112.1, 25.9), (-114, 27.6)]
    coast = [(-112.3, 29), (-111.3, 28.4), (-110.6, 27.8), (-110.0, 27.0),
             (-109.45, 26.72), (-109.15, 25.65), (-108.45, 25.19),
             (-107.8, 24.77), (-107.4, 24.34), (-106.4, 23.19), (-106, 22.5), (-106, 29)]
    for land in (baja, coast):
        p.poly([xy(*ll) for ll in land], "#E8D7B4", "#947C5C", .8)
    x, y = xy(-108.47, 25.57)
    p.circle(x, y, 7, None, "#AF4437", 1.2)
    p.circle(x, y, 2.6, "#9C3228")
    p.line([(x + 7, y), (x + 14, y - 6), (x + 22, y - 6)], "#9C3228", .9)


def scene_football(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#BBCDD1", "#EFE4C5")
    p.poly([(0, 25), (w, 15), (w, 33), (0, 37)], "#52616A")
    for i in range(35):
        x = i * 5.8
        p.line([(x, 28 - x * .05), (x + 2, 28 - x * .05)], "#C8C6AE", 1)
    p.rect(0, 36, w, h, "#436F51")
    for i in range(4):
        p.poly([(i * 52, 36), (i * 52 + 23, 36), (i * 61 + 19, h), (i * 61 - 10, h)], "#51805C")
    p.ellipse(87, 46.5, 17, 5.6, None, "#C5D1AD", .9)
    p.line([(91, 36), (84, h)], "#DBE0BF", .9)
    p.rect(w - 62, 5, w - 5, 37, "#182735", "#DDBF78", 1)
    p.text(w - 33.5, 13.2, "NEW   ARS", 9.2, "#F2D696")
    p.text(w - 33.5, 26.6, "2 : 2", 13.6, "#FFFFFF")


SCENES = {
    "cop": scene_cop31, "gulf": scene_gulf_hero, "andes": scene_peru_hero,
    "trade": scene_trade, "baltic": scene_baltic, "caboverde": scene_caboverde,
    "sinaloa": scene_sinaloa, "flood": scene_flood, "bandasea": scene_bandasea,
    "mercury": scene_bepicolombo, "football": scene_football, "vegas": scene_vegas_pole,
    "cricket": scene_rahul,
}


def draw_scene(scene, w, h, out_scale=2, supersample=4, base=None):
    p = Pen(w, h, out_scale * supersample, base)
    SCENES[scene](p)
    return p.render(round(w * out_scale), round(h * out_scale))
