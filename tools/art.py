"""Original museum-editorial silkscreen illustrations composed for the 10-panel front page (v14).

Each scene draws into a supersampled Pen in 1x layout coordinates and downsamples
with LANCZOS for razor-sharp printmaking edges. Top-left corner leaves light breathing
room for a compact region pill; every focal motif is bold and unmistakable even at 300px.
100% deterministic (fixed-seed LCG only).
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
    def __init__(self, w, h, scale=6):
        self.w, self.h, self.s = w, h, scale
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
def ridge(p, base, amp, freq, phase, color, y_floor=None, steps=90):
    y_floor = p.h if y_floor is None else y_floor
    pts = [(0, y_floor)]
    for i in range(steps + 1):
        x = p.w * i / steps
        y = base - amp * (0.6 * math.sin(freq * x / p.w * 6.283 + phase)
                          + 0.4 * math.sin(freq * 2.3 * x / p.w * 6.283 + phase * 1.7))
        pts.append((x, y))
    pts.append((p.w, y_floor))
    p.poly(pts, color)


def waves(p, y0, y1, c_top, c_bot, crest="#FFFFFF", n=5, seed=3):
    p.vgrad(y0, y1, c_top, c_bot)
    rnd = Rand(seed)
    for row in range(n):
        y = y0 + (y1 - y0) * (row + 0.55) / n
        x = rnd.uniform(-10, 0)
        while x < p.w:
            L = rnd.uniform(10, 24) * (0.65 + row / n)
            p.line([(x, y), (x + L, y)], rgb(crest, 72 + row * 12), 1.0)
            x += L + rnd.uniform(10, 22)


def stars(p, n, seed, y1=None, color="#FFFFFF"):
    rnd = Rand(seed)
    y1 = p.h if y1 is None else y1
    for _ in range(n):
        x, y = rnd.uniform(0, p.w), rnd.uniform(0, y1)
        r = rnd.uniform(0.4, 1.15)
        p.circle(x, y, r, rgb(color, round(rnd.uniform(120, 255))))


def smoke(p, x, y, dx, dy, r0, r1, n, color, alpha=170, seed=9):
    rnd = Rand(seed)
    for i in range(n):
        t = i / max(1, n - 1)
        cx = x + dx * t + rnd.uniform(-2.0, 2.0)
        cy = y + dy * t + rnd.uniform(-1.5, 1.5)
        r = r0 + (r1 - r0) * t
        p.circle(cx, cy, r, rgb(color, round(alpha * (1 - 0.48 * t))))


def flames(p, cx, base, w, h, seed=5):
    rnd = Rand(seed)
    for layer, col in enumerate(("#A82824", "#EE6A1F", "#FFB23F", "#FFE999")):
        k = 1 - layer * 0.22
        pts = [(cx - w / 2 * k, base)]
        tongues = 5
        for i in range(tongues):
            x0 = cx - w / 2 * k + w * k * (i + 0.5) / tongues
            pts.append((x0 - w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
            pts.append((x0 + rnd.uniform(-1.0, 1.0), base - h * k * rnd.uniform(0.75, 1.0)))
            pts.append((x0 + w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
        pts.append((cx + w / 2 * k, base))
        p.poly(pts, col)


def seismo(p, x0, x1, y, amp, color, seed=7, width=1.6, burst=0.5):
    rnd = Rand(seed)
    pts = []
    n = 160
    for i in range(n + 1):
        t = i / n
        env = math.exp(-((t - burst) ** 2) / 0.008) + 0.05
        pts.append((x0 + (x1 - x0) * t, y + amp * env * rnd.uniform(-1, 1)))
    p.line(pts, color, width)


# --------------------------------------------------------- Hero Posters (484 x 232)
def scene_cop31_poster(p):
    """Antalya COP31 overtime: oil derrick vs wind turbines, plenary pavilion, draft & midnight clock."""
    w, h = p.w, p.h
    water = h * 0.78
    base = water + 8
    p.vgrad(0, water, "#E6A971", "#FCF0D8")
    p.glow(w * 0.54, water * 0.80, h * 0.75, "#FFE3A6", 155)
    ridge(p, water - 26, h * 0.11, 1.4, 0.6, "#C59F82", y_floor=water + 4)
    ridge(p, water - 11, h * 0.07, 2.2, 1.8, "#9B7662", y_floor=water + 4)
    waves(p, water, h, "#297494", "#15445E", n=5, seed=11)

    # Left: dark fossil-fuel oil derrick & pumpjack contrasting against renewable side.
    dx = w * 0.13
    p.poly([(dx - 17, base), (dx - 3.5, base - 74), (dx + 3.5, base - 74), (dx + 17, base)],
           None, "#2E231F", 2.4)
    for k in range(1, 5):
        yy = base - k * 14.5
        half = 17 - k * 3.0
        p.line([(dx - half, yy), (dx + half, yy)], "#2E231F", 1.7)
    p.line([(dx - 13, base - 14.5), (dx + 10, base - 43.5)], "#2E231F", 1.2)
    p.line([(dx + 13, base - 14.5), (dx - 10, base - 43.5)], "#2E231F", 1.2)
    p.rect(dx + 11, base - 40, dx + 45, base - 33, "#2E231F")
    p.poly([(dx + 42, base - 48), (dx + 55, base - 36.5), (dx + 42, base - 25)], "#2E231F")

    # Center: Antalya plenary pavilion & delegate flags.
    hx0, hx1 = w * 0.29, w * 0.64
    p.rect(hx0, base - 34, hx1, base, "#F4EEE2", "#746658", 1.2)
    p.poly([(hx0 - 10, base - 34), ((hx0 + hx1) / 2, base - 58), (hx1 + 10, base - 34)],
           "#DFD2BD", "#746658", 1.2)
    for i in range(9):
        x = hx0 + 11 + i * (hx1 - hx0 - 22) / 8
        p.rect(x - 3.5, base - 25, x + 3.5, base, "#B2A38F")
    flag_cols = ["#A82824", "#1F4A6E", "#266B47", "#E6B422", "#186F7A", "#C82828", "#2B7A4B", "#264E86", "#B84E1D"]
    for i, c in enumerate(flag_cols):
        x = hx0 + i * (hx1 - hx0) / (len(flag_cols) - 1)
        p.line([(x, base), (x, base - 50)], "#463E36", 1.0)
        p.rect(x, base - 50, x + 10.5, base - 42, c)

    # Right: three crisp white wind turbines framed cleanly inside sunlit sky.
    for tx, th, ang in ((w * 0.785, h * 0.56, 18), (w * 0.875, h * 0.65, 48), (w * 0.948, h * 0.46, 82)):
        top = base - th
        p.poly([(tx - 2.8, base), (tx - 1.0, top), (tx + 1.0, top), (tx + 2.8, base)],
               "#FFFFFF", "#7E8E98", 0.7)
        for k in range(3):
            a = math.radians(ang + k * 120)
            p.line([(tx, top), (tx + math.cos(a) * th * 0.34, top + math.sin(a) * th * 0.34)],
                   "#FFFFFF", 2.8)
        p.circle(tx, top, 3.0, "#2F3E48")

    # Iconic unsigned DRAFT folio (upper center-left) + midnight OVERTIME clock (upper center-right).
    fx, fy = w * 0.365, 10
    for off in (6, 3.0, 0):
        p.rect(fx + off, fy + off, fx + 88 + off, fy + 66 + off, "#FFF9EB", "#8F7963", 1.3, r=2)
    p.rect(fx + 7, fy + 6, fx + 81, fy + 27, "#1D4456", r=1.5)
    p.text(fx + 44, fy + 16.8, "DRAFT", 15.5, "#FFFFFF")
    for row, length in enumerate((62, 48, 68, 36)):
        yy = fy + 35 + row * 6.4
        p.line([(fx + 9, yy), (fx + 9 + length, yy)], "#9D8B76", 1.6)
    p.line([(fx + 40, fy + 59), (fx + 74, fy + 55)], "#B83228", 2.4)

    # Stalled overtime clock past midnight (12:15) beside draft.
    cx, cy, cr = w * 0.652, 44, 26
    p.circle(cx + 2, cy + 2.5, cr, (0, 0, 0, 55))
    p.circle(cx, cy, cr, "#FFFBF2", "#B22222", 2.8)
    p.circle(cx, cy, cr - 4.5, None, "#D5C9B6", 0.9)
    for k in range(12):
        a = math.radians(k * 30)
        r0 = cr - (8.0 if k % 3 == 0 else 6.0)
        p.line([(cx + r0 * math.sin(a), cy - r0 * math.cos(a)),
                (cx + (cr - 3.4) * math.sin(a), cy - (cr - 3.4) * math.cos(a))], "#2B3440", 1.2)
    p.poly([(cx, cy), (cx, cy - 16), (cx + 12, cy - 11), (cx + 16, cy)], rgb("#B22222", 55))
    p.line([(cx, cy), (cx + 2, cy - 13.5)], "#131B26", 2.5)
    p.line([(cx, cy), (cx + 16, cy + 1)], "#B22222", 2.1)
    p.circle(cx, cy, 2.8, "#B22222")


def scene_gulf_poster(p):
    """Persian Gulf diptych: Bahrain industrial site ablaze left, two Hormuz tankers + brass compass right."""
    w, h = p.w, p.h
    sea = h * 0.56
    # Seamless two-stop twilight sky over the Persian Gulf.
    mid = sea * 0.52
    p.vgrad(0, mid, "#1C2E4E", "#C97A4F")
    p.vgrad(mid, sea, "#C97A4F", "#F9DFB2")
    stars(p, 45, 71, y1=mid * 0.85)
    p.glow(w * 0.62, sea * 0.88, h * 0.52, "#FFE3A6", 115)

    # Musandam headlands along right horizon.
    ridge(p, sea - 18, h * 0.11, 1.3, 0.5, "#B0825C", y_floor=sea + 4)
    ridge(p, sea - 6, h * 0.065, 2.1, 1.7, "#825A40", y_floor=sea + 4)
    waves(p, sea, h, "#25708C", "#113B52", n=6, seed=15)

    # Left coast: Bahrain industrial facility silhouette with vivid blaze & sweeping smoke.
    bx_end = w * 0.36
    smoke(p, w * 0.24, h * 0.72, 48, -68, 6.0, 18.0, 18, "#292B34", 180, seed=13)
    p.glow(w * 0.23, h * 0.76, 46, "#FFBC5C", 185, steps=12)
    flames(p, w * 0.23, h * 0.85, 38, 46, seed=7)
    for sx, top in ((22, h * 0.54), (38, h * 0.60), (144, h * 0.55)):
        p.poly([(sx, h), (sx + 2, top), (sx + 7, top), (sx + 10, h)], "#242838")
        p.line([(sx + 2, top + 7), (sx + 7, top + 7)], "#E5C19F", 1.6)
    roof = [(0, h), (0, h * 0.82)]
    for x in range(0, int(bx_end), 28):
        roof.extend([(x + 21, h * 0.71), (x + 21, h * 0.82)])
    p.poly(roof + [(bx_end + 14, h * 0.87), (bx_end + 24, h)], "#152333")
    for x in range(10, int(bx_end) - 6, 15):
        p.rect(x, h * 0.89, x + 6.5, h * 0.94, "#F4CD84")

    # Distant outbound tanker off Khasab with crimson alert arcs.
    tx2, ty2 = w * 0.785, sea + (h - sea) * 0.30
    p.line([(tx2 - 58, ty2 + 5.5), (tx2 - 22, ty2 + 5.5)], rgb("#D8F1F8", 155), 1.3)
    p.poly([(tx2 - 36, ty2 - 4.5), (tx2 + 34, ty2 - 4.5), (tx2 + 43, ty2 - 10.0),
            (tx2 + 32, ty2 + 5.5), (tx2 - 34, ty2 + 5.5)], "#722728")
    p.rect(tx2 - 34, ty2 - 7.5, tx2 + 31, ty2 - 4.2, "#38414C")
    p.rect(tx2 - 34, ty2 - 19.0, tx2 - 21, ty2 - 7.5, "#F6F2E9", "#7C756A", 0.6)
    p.rect(tx2 - 30, ty2 - 24.5, tx2 - 25.5, ty2 - 19.0, "#B0322E")
    for k in range(3):
        p.circle(tx2 - 12 + k * 14, ty2 - 9.0, 3.0, "#58626E")
    for rr, al in ((16.0, 210), (25.0, 145)):
        p.arc(tx2 + 6, ty2 - 7, rr, 200, 340, rgb("#E04231", al), 2.0)

    # Foreground outbound tanker in the Strait of Hormuz.
    tx1, ty1 = w * 0.565, h - 26
    p.line([(tx1 - 84, ty1 + 8.0), (tx1 - 48, ty1 + 8.0)], rgb("#D8F1F8", 165), 1.6)
    p.poly([(tx1 - 56, ty1 - 6.5), (tx1 + 48, ty1 - 6.5), (tx1 + 59, ty1 - 14.0),
            (tx1 + 45, ty1 + 8.0), (tx1 - 52, ty1 + 8.0)], "#8D2B27")
    p.rect(tx1 - 52, ty1 - 10.5, tx1 + 44, ty1 - 6.5, "#36404B")
    p.rect(tx1 - 52, ty1 - 26.0, tx1 - 32, ty1 - 10.5, "#F8F4EC", "#6B645A", 0.7)
    p.rect(tx1 - 47, ty1 - 33.0, tx1 - 41, ty1 - 26.0, "#1F4A6E")
    for k in range(4):
        p.circle(tx1 - 21 + k * 16.5, ty1 - 12.2, 3.6, "#5B6572")
    for rr, al in ((19.0, 220), (30.0, 150)):
        p.arc(tx1 + 12, ty1 - 10, rr, 205, 335, rgb("#E04231", al), 2.2)

    # Large archival brass nautical compass rose in the clear upper-right sky.
    cx, cy, cr = w * 0.875, 55, 25
    p.circle(cx + 1.5, cy + 2.0, cr, (0, 0, 0, 55))
    p.circle(cx, cy, cr, "#FAF2E1", "#6D5E4C", 1.8)
    p.circle(cx, cy, cr - 4.0, None, "#C8B89E", 0.9)
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        inner = cr - (6.2 if angle % 90 == 0 else 3.6)
        p.line([(cx + inner * math.sin(a), cy - inner * math.cos(a)),
                (cx + (cr - 1.5) * math.sin(a), cy - (cr - 1.5) * math.cos(a))], "#6B6156", 1.2)
    p.poly([(cx - 5.2, cy), (cx, cy - 17.5), (cx + 5.2, cy)], "#B22222")
    p.poly([(cx - 5.2, cy), (cx, cy + 17.5), (cx + 5.2, cy)], "#1F4A6E")
    p.circle(cx, cy, 3.1, "#F0C66E", "#4A3E30", 0.9)
    p.text(cx, cy - cr - 6.0, "N", 10.5, "#FFF5DF")


# --------------------------------------------------------- Grid Posters (238.5 x 80)
def scene_peru_poster(p):
    """Junin Andes, trembling adobe village and bold M6.7 seismograph strip."""
    w, h = p.w, p.h
    sy0 = h - 29
    ground = sy0 + 1
    p.vgrad(0, ground, "#84B8E0", "#F3EDE2")

    peaks = [(-6, 0.92), (w * 0.16, 0.44), (w * 0.34, 0.56), (w * 0.52, 0.18),
             (w * 0.68, 0.46), (w * 0.82, 0.12), (w * 0.95, 0.36), (w + 6, 0.72)]
    pts = [(-6, ground)] + [(x, ground * y) for x, y in peaks] + [(w + 6, ground)]
    p.poly(pts, "#796759")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2:
            px, py = x1, ground * y1
            p.poly([(px, py), (px - 16, py + 17), (px - 5, py + 13), (px, py + 20),
                    (px + 6, py + 13), (px + 16, py + 17)], "#FFFFFF")
    ridge(p, ground * 0.84, 6, 1.8, 0.4, "#5A7D44", y_floor=ground)

    # Adobe village houses with vivid tremor arcs.
    for hx, sc in ((w * 0.30, 0.88), (w * 0.52, 1.05), (w * 0.74, 0.88)):
        hy = ground
        p.poly([(hx - 10 * sc, hy), (hx + 10 * sc, hy - 1.5), (hx + 8 * sc, hy - 16 * sc),
                (hx - 12 * sc, hy - 14 * sc)], "#F7EBD5", "#5C4736", 0.9)
        p.poly([(hx - 14 * sc, hy - 14 * sc), (hx - 2 * sc, hy - 23 * sc),
                (hx + 11 * sc, hy - 16 * sc)], "#B8472F", "#5C4736", 0.85)
        p.rect(hx - 3.5 * sc, hy - 9 * sc, hx + 2 * sc, hy - 2 * sc, "#6E523F")
    p.arc(w * 0.52 - 1, ground - 13, 21, 195, 252, "#B22222", 1.7)
    p.arc(w * 0.52 - 1, ground - 13, 21, 290, 348, "#B22222", 1.7)

    # Crisp cream seismograph strip.
    p.rect(0, sy0, w, h, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#B8AE9A", 1.0)
    for k in range(1, 16):
        p.line([(w * k / 16, sy0), (w * k / 16, h)], "#ECE4D6", 0.55)
    seismo(p, 6, w - 64, sy0 + 14.5, 11.2, "#C82222", seed=12, width=1.6, burst=0.55)
    p.rect(w - 58, sy0 + 4.5, w - 5, sy0 + 24.5, "#A82824", r=2.2)
    p.text(w - 31.5, sy0 + 14.8, "M 6.7", 12.4, "#FFFFFF")


def scene_trade_poster(p):
    """EU-Indonesia CEPA: deep-water container vessel & 98.5% tariff-cut plaque."""
    w, h = p.w, p.h
    sea = h * 0.58
    p.vgrad(0, sea, "#8FBAD9", "#F7F1E5")
    ridge(p, sea - 3, h * 0.07, 1.3, 0.9, "#B4C4CD", y_floor=sea + 3)
    waves(p, sea, h, "#1E587D", "#10334C", crest="#E3F2FA", n=5, seed=47)

    # Bold cargo container vessel carrying EU-navy, gold, crimson & ivory containers.
    sx, sy = w * 0.50, h - 22
    p.line([(sx - 92, sy + 9), (sx - 60, sy + 9)], rgb("#E6F4FA", 175), 1.4)
    p.poly([(sx - 64, sy - 4), (sx + 58, sy - 4), (sx + 70, sy - 12),
            (sx + 55, sy + 9), (sx - 60, sy + 9)], "#1B3046", "#0D1B2A", 0.9)
    p.rect(sx - 60, sy + 4.5, sx + 56, sy + 8.8, "#B22D28")
    p.rect(sx - 56, sy - 24, sx - 36, sy - 4, "#F8F4EC", "#394856", 0.8)
    p.rect(sx - 52, sy - 19, sx - 40, sy - 15, "#1F4E8C")
    p.rect(sx - 49, sy - 29.5, sx - 42.5, sy - 24, "#E6B422")
    cols = (
        ("#1F4E8C", "#C42B2B", "#E6B422", "#1F4E8C"),
        ("#C42B2B", "#1F4E8C", "#F6F1E4", "#C42B2B"),
        ("#E6B422", "#266B47", "#1F4E8C", "#E6B422"),
        ("#1F4E8C", "#C42B2B", "#F6F1E4", "#1F4E8C"),
        ("#C42B2B", "#E6B422", "#1F4E8C", "#C42B2B"),
    )
    for ci, stack in enumerate(cols):
        cx0 = sx - 31 + ci * 17.5
        for ri, col in enumerate(stack):
            cy1 = sy - 4 - ri * 6.8
            p.rect(cx0, cy1 - 6.0, cx0 + 15.8, cy1, col, "#142230", 0.55)

    # Dark-and-gold 98.5% tariff badge in clear upper right.
    p.rect(w - 64, 6, w - 6, 30, "#11161D", "#F0C842", 1.2, r=2.2)
    p.text(w - 35, 18.4, "98.5%", 13.0, "#FFD23F")


def scene_baltic_poster(p):
    """Gulf of Finland: Sparta II ablaze with smoke plume & bright orange rescue lifeboat."""
    w, h = p.w, p.h
    sea = h * 0.56
    p.vgrad(0, sea, "#3E5B74", "#C4D7E0")
    ridge(p, sea - 3, h * 0.08, 1.5, 0.5, "#2C4252", y_floor=sea + 3)
    waves(p, sea, h, "#1E4D67", "#0F2B3F", crest="#D8ECF5", n=5, seed=23)

    sx, sy = w * 0.64, h - 28
    smoke(p, sx + 6, sy - 14, 48, -52, 5.5, 16.5, 18, "#292D36", 185, seed=19)
    p.glow(sx + 4, sy - 10, 36, "#FFA84C", 175, steps=12)

    p.poly([(sx - 50, sy - 4), (sx + 42, sy - 4), (sx + 51, sy - 11.5),
            (sx + 39, sy + 8.5), (sx - 47, sy + 8.5)], "#3D4954", "#1B242E", 0.85)
    p.rect(sx - 47, sy + 4.0, sx + 40, sy + 8.3, "#8D342A")
    p.rect(sx - 44, sy - 19, sx - 26, sy - 4, "#EAE4D8", "#4B5662", 0.7)
    p.rect(sx - 39, sy - 24.5, sx - 32, sy - 19, "#6B7682")
    p.rect(sx - 19, sy - 12, sx + 22, sy - 4, "#5B6975")
    flames(p, sx + 6, sy - 4, 28, 32, seed=31)

    # Bright orange lifeboat pulling safely clear in foreground left.
    lx, ly = w * 0.22, h - 14
    p.poly([(lx - 18, ly - 2.8), (lx + 18, ly - 2.8), (lx + 13.5, ly + 4.8),
            (lx - 13.5, ly + 4.8)], "#EB6022", "#8C2C0C", 0.8)
    p.rect(lx - 9.5, ly - 7.5, lx + 8.0, ly - 2.8, "#FFF8EC")
    p.line([(lx + 19, ly + 4.2), (lx + 42, ly + 4.2)], rgb("#E6F4FA", 175), 1.3)


def scene_caboverde_poster(p):
    """Praia, Cabo Verde: Atlantic sunset, Santiago ridge, ballot box & 63.96% tally board."""
    w, h = p.w, p.h
    sea = h * 0.62
    p.vgrad(0, sea, "#D88E4E", "#FAE8C2")
    ridge(p, sea - 6, h * 0.14, 1.3, 1.0, "#7E5D47", y_floor=sea + 3)
    ridge(p, sea + 1, h * 0.07, 2.0, 2.4, "#5A4234", y_floor=sea + 3)
    waves(p, sea, h, "#1C5382", "#103152", crest="#F6E2B3", n=4, seed=41)

    # Bold ballot box with Cabo Verde sash and green-checked ballot paper.
    bx, by = w * 0.48, h - 6
    p.rect(bx - 30, by - 36, bx + 30, by, "#F8F2E4", "#182A40", 1.3, r=2.0)
    p.rect(bx - 28.8, by - 19.5, bx + 28.8, by - 12.5, "#1F4E8C")
    p.rect(bx - 28.8, by - 12.5, bx + 28.8, by - 9.2, "#FFFFFF")
    p.rect(bx - 28.8, by - 9.2, bx + 28.8, by - 5.5, "#C42B2B")
    p.rect(bx - 15, by - 33, bx + 15, by - 30, "#182A40")
    p.poly([(bx - 9.5, by - 31.5), (bx - 3.5, by - 52), (bx + 15, by - 48),
            (bx + 9, by - 31.5)], "#FFFFFF", "#182A40", 1.1)
    p.line([(bx - 1.5, by - 42.5), (bx + 2.5, by - 38.2), (bx + 9.2, by - 46.2)], "#1E7D4E", 2.4)

    # Bold dark-and-gold 63.96% tally board in upper right.
    p.rect(w - 70, 6, w - 6, 30, "#11161D", "#F0C842", 1.2, r=2.2)
    p.text(w - 38, 18.4, "63.96%", 12.6, "#FFD23F")


def scene_odisha_poster(p):
    """Odisha flood watch: storm clouds, rain bands, swollen river & crimson flood gauge staff."""
    w, h = p.w, p.h
    sea = h * 0.62
    p.vgrad(0, sea, "#527082", "#D5E2D8")
    # Stylized cyclone cloud swirl band on upper-center-left.
    cx, cy = w * 0.44, h * 0.36
    for rr, a0, a1, al in ((24, 15, 220, 155), (16, 65, 290, 185), (9, 130, 350, 210)):
        p.arc(cx, cy, rr, a0, a1, rgb("#F7FAF8", al), 2.8)
    p.circle(cx, cy, 3.5, rgb("#3A5769", 180))
    # Subtle monsoon rain streaks.
    rnd = Rand(63)
    for _ in range(28):
        rx, ry = rnd.uniform(14, w - 40), rnd.uniform(22, sea - 8)
        p.line([(rx, ry), (rx - 4.5, ry + 10.5)], rgb("#E8F2F5", 130), 0.9)

    ridge(p, sea - 2, h * 0.07, 1.6, 1.2, "#5D7D6E", y_floor=sea + 3)
    waves(p, sea, h, "#528996", "#275366", crest="#D6ECEB", n=5, seed=27)

    # Tall iconic river flood gauge staff on right.
    gx = w * 0.80
    p.rect(gx, 12, gx + 19, h, "#EFE2B6", "#273A47", 1.4)
    p.rect(gx + 1.2, 13.2, gx + 17.8, 34, "#B82924")
    for i in range(14):
        yy = 38 + i * 6.5
        if yy > h - 3:
            break
        p.line([(gx + 1.5, yy), (gx + (13 if i % 2 == 0 else 8), yy)], "#8F382B", 1.5)


def scene_sinaloa_poster(p):
    """Gulf of California cartographic locator highlighting Guasave, Sinaloa."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#B5D5DC", "#C9E2E7")
    # Fine maritime graticule.
    for k in range(1, 5):
        p.line([(w * k / 5, 0), (w * k / 5, h)], rgb("#8EB7C2", 120), 0.7)
    for k in range(1, 4):
        p.line([(0, h * k / 4), (w, h * k / 4)], rgb("#8EB7C2", 120), 0.7)

    def xy(lon, lat):
        return (lon + 114.2) * w / 8.4, (29.2 - lat) * h / 6.8

    baja = [(-114.2, 29.2), (-112.9, 29.2), (-112.3, 27.9), (-111.7, 27.5), (-111.4, 26.4),
            (-111.0, 25.6), (-110.7, 24.8), (-109.9, 24.0), (-109.4, 23.5),
            (-109.9, 22.9), (-110.4, 23.7), (-111.8, 24.5), (-112.1, 25.9), (-114.2, 27.6)]
    coast = [(-112.3, 29.2), (-111.3, 28.4), (-110.6, 27.8), (-110.0, 27.0),
             (-109.45, 26.72), (-109.15, 25.65), (-108.45, 25.19),
             (-107.8, 24.77), (-107.4, 24.34), (-106.4, 23.19), (-105.8, 22.4), (-105.8, 29.2)]
    for land in (baja, coast):
        p.poly([xy(*ll) for ll in land], "#ECDAB8", "#8F7758", 1.2)

    gx, gy = xy(-108.47, 25.57)
    for rr, al in ((19, 130), (12, 200)):
        p.circle(gx, gy, rr, None, rgb("#B22222", al), 1.8)
    p.circle(gx, gy, 4.8, "#B22222", "#FFFFFF", 1.0)
    # Crisp GUASAVE map tag.
    p.rect(gx - 68, gy + 10, gx - 6, gy + 30, "#152538", "#FFFFFF", 0.9, r=2.0)
    p.text(gx - 37, gy + 20.2, "GUASAVE", 10.2, "#F0C66E")
    p.line([(gx - 6, gy + 15), (gx - 4, gy + 4)], "#152538", 1.2)


def scene_mercury_poster(p):
    """Deep-space Mercury limb & BepiColombo spacecraft on dashed insertion trajectory."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#060C20", "#16254A")
    stars(p, 75, 21, y1=h)
    p.glow(-10, h * 0.92, 72, "#FFE299", 150, steps=18)

    # Large cratered Mercury limb on right.
    mx, my, mr = w * 0.86, h * 0.58, h * 0.56
    p.circle(mx, my, mr, "#4A4642")
    sphere = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(sphere).ellipse([(mx - mr) * p.s, (my - mr) * p.s, (mx + mr) * p.s, (my + mr) * p.s],
                                   fill=255)
    lit = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(lit).ellipse([(mx - mr * 1.28) * p.s, (my - mr * 1.04) * p.s,
                                 (mx + mr * 0.35) * p.s, (my + mr * 1.04) * p.s], fill=255)
    p.img.paste(Image.new("RGB", p.img.size, (186, 177, 162)), (0, 0), ImageChops.multiply(sphere, lit))
    p.d = ImageDraw.Draw(p.img, "RGBA")
    rnd = Rand(44)
    for _ in range(44):
        a, rr = rnd.uniform(0, 6.283), mr * math.sqrt(rnd.next()) * 0.88
        cx, cy = mx + math.cos(a) * rr, my + math.sin(a) * rr
        if cy > h + 4 or cx > w + 4:
            continue
        cr = rnd.uniform(1.8, 5.8)
        is_lit = cx < mx - mr * 0.08
        p.ellipse(cx, cy, cr, cr * 0.85, rgb("#7B746A" if is_lit else "#3E3A36", 225))
        p.arc(cx, cy, cr, 200, 340, rgb("#DDD5C8" if is_lit else "#68625B", 215), 0.75)
    p.circle(mx, my, mr, None, rgb("#D8D0C2", 145), 1.3)

    # Dashed orbital approach curve (not a closed confirmed orbit).
    def path(v):
        return w * (.05 + .62 * v), h * (.94 - .44 * v * v)
    for i in range(20):
        p.line([path(i / 20), path((i + .56) / 20)], "#8CC4DD", 1.5)

    # Stacked BepiColombo spacecraft: blue solar wing, gold MPO, white Mio, cyan thruster glow.
    sx, sy = path(.56)
    p.glow(sx + 18, sy, 14, "#8BE0FF", 220, steps=10)
    p.line([(sx + 9, sy), (sx + 30, sy)], rgb("#A8E6FF", 220), 3.8)
    p.rect(sx - 64, sy - 6.0, sx - 13, sy + 6.0, "#285094", "#A4C2E8", 0.9)
    for k in range(1, 6):
        gx = sx - 64 + k * 51 / 6
        p.line([(gx, sy - 6.0), (gx, sy + 6.0)], rgb("#A4C2E8", 165), 0.65)
    p.line([(sx - 64, sy), (sx - 13, sy)], rgb("#A4C2E8", 165), 0.65)
    p.rect(sx - 13, sy - 1.4, sx - 9, sy + 1.4, "#C0C6CE")
    p.rect(sx - 9, sy - 9.5, sx + 9, sy + 9.5, "#E3AF44", "#8A641E", 1.0)
    p.line([(sx - 9, sy), (sx + 9, sy)], rgb("#8A641E", 170), 0.7)
    p.poly([(sx - 6.5, sy - 9.5), (sx + 6.5, sy - 9.5), (sx + 4.8, sy - 18.0), (sx - 4.8, sy - 18.0)],
           "#F2F4F7", "#8B95A2", 0.75)
    p.ellipse(sx, sy - 18.0, 4.8, 1.8, "#FFFFFF")


def scene_cricket_poster(p):
    """Basin Reserve, Wellington: striped oval turf, stumps, bat & ball + 486/4 DAY 3 scoreboard."""
    w, h = p.w, p.h
    turf = h * 0.44
    p.vgrad(0, turf, "#7ABCE6", "#DCF0FA")
    ridge(p, turf - 2, h * 0.08, 1.4, 0.9, "#5E8B67", y_floor=turf + 4)
    p.rect(0, turf, w, h, "#22883F")
    for k in range(1, 5):
        p.ellipse(w * 0.5, h * 0.96, w * 0.66 * (1 - k * 0.18), h * 0.62 * (1 - k * 0.18),
                  None, rgb("#36AC57", 135), 2.6)
    p.rect(w * 0.42, turf + 8, w * 0.58, h, "#E6D1A2")
    # Crisp white wickets & bails.
    for dx in (-4.2, 0, 4.2):
        p.line([(w * 0.50 + dx, turf + 24), (w * 0.50 + dx, turf + 6)], "#FFFFFF", 1.6)
    p.line([(w * 0.50 - 5.0, turf + 6), (w * 0.50 + 5.0, turf + 6)], "#F0C842", 1.4)

    # Bold willow cricket bat & stitched crimson leather ball.
    p.poly([(w * 0.16, h - 6), (w * 0.30, turf + 10), (w * 0.39, turf + 13), (w * 0.25, h - 2)],
           "#EBC784", "#765626", 1.4)
    p.line([(w * 0.345, turf + 11.5), (w * 0.395, turf - 5)], "#1F4A6E", 4.0)
    p.circle(w * 0.68, turf + 18, 9.5, "#B81D24", "#FFFFFF", 0.9)
    p.arc(w * 0.68, turf + 18, 6.2, 110, 250, "#FFFFFF", 1.1)

    # Bold stadium scoreboard in clear upper right.
    p.rect(w - 74, 5, w - 5, 39, "#11161D", "#F0C842", 1.2, r=2.2)
    p.text(w - 39.5, 16.5, "486/4", 13.0, "#FFFFFF")
    p.text(w - 39.5, 31.0, "DAY 3", 10.0, "#FFD23F")


SCENES = {
    "cop": scene_cop31_poster,
    "gulf": scene_gulf_poster,
    "andes": scene_peru_poster,
    "trade": scene_trade_poster,
    "baltic": scene_baltic_poster,
    "caboverde": scene_caboverde_poster,
    "flood": scene_odisha_poster,
    "sinaloa": scene_sinaloa_poster,
    "mercury": scene_mercury_poster,
    "cricket": scene_cricket_poster,
}


def draw_scene(scene, w, h, out_scale=2, supersample=3):
    p = Pen(w, h, out_scale * supersample)
    SCENES[scene](p)
    return p.render(round(w * out_scale), round(h * out_scale))
