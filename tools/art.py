"""Original silkscreen-editorial vector illustrations, one per illustrated story (ids 1-13, v4).

Each scene draws into an 8x supersampled Pen in 1x layout coordinates and
downsamples with LANCZOS for razor-sharp printmaking edges. Every art panel
sits unobstructed ABOVE its full-width banner ribbon, giving crisp full-frame
visual storytelling legible at both 1024px and 300px thumbnail sizes.
Everything is 100% deterministic (fixed-seed LCG only).
"""
import math

from PIL import Image, ImageDraw, ImageFont

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
    def __init__(self, w, h, scale=8):
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


def delta_drone(p, cx, cy, s, color, tilt=0.0):
    ca, sa = math.cos(tilt), math.sin(tilt)

    def r(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    p.poly([r(s, 0), r(-s * 0.65, -s * 0.78), r(-s * 0.3, 0), r(-s * 0.65, s * 0.78)], color)


def starburst(p, cx, cy, r_out, r_in, col_out, col_in, rays=10):
    pts = []
    for k in range(rays * 2):
        a = math.radians(-90 + k * (180 / rays))
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    p.poly(pts, col_out)
    pts2 = []
    for k in range(rays * 2):
        a = math.radians(-90 + k * (180 / rays))
        r = (r_out * 0.56) if k % 2 == 0 else (r_in * 0.56)
        pts2.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    p.poly(pts2, col_in)


def star5(p, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    p.poly(pts, fill)


# ------------------------------------------------------------------ scenes
def scene_cop31(p):
    """1. COP31 Antalya: Mediterranean sunrise, oil derrick vs wind turbines, plenary hall & overtime clock."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.74, "#F2C794", "#FBF0DC")
    p.glow(w * 0.50, h * 0.60, h * 0.75, "#FFE3A6", 140)
    ridge(p, h * 0.62, h * 0.11, 1.5, 0.7, "#C8A488", y_floor=h * 0.78)
    ridge(p, h * 0.70, h * 0.07, 2.3, 1.9, "#A37F6A", y_floor=h * 0.78)
    waves(p, h * 0.75, h, "#2D7899", "#174A66", n=3, seed=11)

    dx, base = w * 0.14, h * 0.79
    p.poly([(dx - 13, base), (dx - 3, base - 52), (dx + 3, base - 52), (dx + 13, base)],
           None, "#322723", 1.5)
    for k in range(1, 5):
        yy = base - k * 11
        half = 13 - k * 2.4
        p.line([(dx - half, yy), (dx + half, yy)], "#322723", 1.1)
        p.line([(dx - half - 2.4, yy + 11), (dx + half, yy)], "#322723", 0.75)
    p.rect(dx + 7, base - 30, dx + 34, base - 25.5, "#322723")
    p.poly([(dx + 32, base - 36), (dx + 41, base - 28), (dx + 32, base - 20)], "#322723")
    p.rect(dx - 26, base - 9, dx - 14, base, "#261E1A", r=1.2)
    p.rect(dx - 26, base - 6.5, dx - 14, base - 5.0, "#DFAD3B")

    for tx, th, ang in ((w * 0.78, 42, 72), (w * 0.86, 56, 14), (w * 0.94, 46, 48)):
        top = base - th
        p.poly([(tx - 1.5, base), (tx - 0.6, top), (tx + 0.6, top), (tx + 1.5, base)], "#FFFFFF", "#8C9CA6", 0.4)
        for k in range(3):
            a = math.radians(ang + k * 120)
            p.line([(tx, top), (tx + math.cos(a) * th * 0.40, top + math.sin(a) * th * 0.40)], "#FFFFFF", 1.7)
        p.circle(tx, top, 1.7, "#3B4A54")

    hx0, hx1, hy = w * 0.30, w * 0.68, h * 0.80
    p.rect(hx0, hy - 18, hx1, hy, "#F2ECE0", "#7D6F61", 0.7)
    p.poly([(hx0 - 6, hy - 18), ((hx0 + hx1) / 2, hy - 31), (hx1 + 6, hy - 18)],
           "#DED2BF", "#7D6F61", 0.7)
    for i in range(9):
        x = hx0 + 6 + i * (hx1 - hx0 - 12) / 8
        p.rect(x - 2.1, hy - 13, x + 2.1, hy, "#B4A592")
    flag_cols = ["#A82824", "#1F4A6E", "#266B47", "#E6B422", "#186F7A", "#C82828", "#2B7A4B", "#264E86", "#D98A1A"]
    for i, c in enumerate(flag_cols):
        x = hx0 - 2 + i * (hx1 - hx0 + 4) / (len(flag_cols) - 1)
        p.line([(x, hy), (x, hy - 28)], "#4B423A", 0.6)
        p.rect(x, hy - 28, x + 6.2, hy - 23.5, c)

    cx, cy, cr = w * 0.49, h * 0.28, 20.0
    p.circle(cx + 1.0, cy + 1.5, cr + 2.2, (50, 35, 20, 55))
    p.circle(cx, cy, cr + 2.2, "#182A40")
    p.circle(cx, cy, cr, "#FFFDF8")
    p.d.pieslice([(cx - cr) * p.s, (cy - cr) * p.s, (cx + cr) * p.s, (cy + cr) * p.s],
                 -90, 10, fill=rgb("#A82824", 205))
    for k in range(12):
        a = math.radians(k * 30 - 90)
        r0 = cr * (0.74 if k % 3 == 0 else 0.85)
        p.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * cr * 0.95, cy + math.sin(a) * cr * 0.95)],
               "#131B26", 1.3 if k % 3 == 0 else 0.65)
    p.line([(cx, cy), (cx + math.cos(math.radians(-68)) * cr * 0.5,
                      cy + math.sin(math.radians(-68)) * cr * 0.5)], "#131B26", 2.1)
    p.line([(cx, cy), (cx + math.cos(math.radians(10)) * cr * 0.80,
                      cy + math.sin(math.radians(10)) * cr * 0.80)], "#131B26", 1.4)
    p.circle(cx, cy, 1.9, "#A82824")
    p.rect(cx + cr + 6, cy - 8, cx + cr + 48, cy + 8, "#A82824", "#FFFDF8", 0.8, r=2)
    p.text(cx + cr + 27, cy + 0.2, "+1 DAY", 9.0, "#FFFFFF")


def scene_saudi_missiles(p):
    """2. Saudi 5 Missiles: midnight slate-indigo sky, Riyadh skyline + 5 interception bursts."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#10213D", "#233F6B")
    stars(p, 85, 29, y1=h * 0.68)
    p.glow(w * 0.50, h * 0.84, 115, "#F0B954", 88)
    p.rect(0, h * 0.78, w, h, "#11203A")

    for x, bw, bh in [(10, 20, 26), (34, 18, 34), (56, 22, 24), (82, 18, 38), (104, 24, 30)]:
        p.rect(x, h - bh, x + bw, h, "#182B4A", "#375585", 0.6)
        for yy in range(int(h - bh + 4), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                if ((int(xx) * 7 + yy * 13) % 5) < 3:
                    p.rect(xx, yy, xx + 1.8, yy + 2.1, "#F7C960")

    kx, kh = w * 0.48, 58.0
    p.poly([(kx - 11, h), (kx - 9.5, h - kh), (kx + 9.5, h - kh), (kx + 11, h)], "#213860", "#7C9ED1", 0.8)
    p.poly([(kx - 5.5, h - kh + 1), (kx + 5.5, h - kh + 1), (kx + 3.8, h - kh + 15),
            (kx, h - kh + 19), (kx - 3.8, h - kh + 15)], "#1A325A")
    p.line([(kx - 7.5, h - kh + 2), (kx + 7.5, h - kh + 2)], "#FFE59E", 1.2)
    for yy in range(int(h - kh + 22), int(h - 4), 5):
        for xx in (kx - 6, kx - 2, kx + 2, kx + 5):
            p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F9D06B")

    fx, fh = w * 0.64, 48.0
    p.poly([(fx - 12, h), (fx, h - fh), (fx + 12, h)], "#1D3358", "#7C9ED1", 0.8)
    p.line([(fx, h - fh), (fx, h - fh - 7)], "#B0CBF0", 1.0)
    p.circle(fx, h - fh + 10, 3.8, "#F8C846", "#FFF2B2", 0.6)
    for k in range(5):
        yy = h - 7 - k * 7.2
        hw = 9 - k * 1.4
        p.line([(fx - hw, yy), (fx + hw, yy)], rgb("#F8D374", 190), 0.85)

    for x, bw, bh in [(w * 0.74, 18, 40), (w * 0.82, 20, 46), (w * 0.90, 22, 32)]:
        p.poly([(x, h), (x, h - bh), (x + bw, h - bh + 6), (x + bw, h)], "#1B3054", "#6486BA", 0.7)
        for yy in range(int(h - bh + 8), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F5C65D")

    # 5 intercepted Houthi missiles (3 over Riyadh left-center + 2 over Jizan right)
    bursts = [
        ((w * 0.18, h * 0.30), (w * 0.01, h * 0.08), (w * 0.24, h * 0.72), 9.5),
        ((w * 0.36, h * 0.20), (w * 0.14, h * 0.01), (w * 0.40, h * 0.68), 11.5),
        ((w * 0.56, h * 0.24), (w * 0.76, h * 0.02), (w * 0.52, h * 0.66), 12.0),
        ((w * 0.74, h * 0.22), (w * 0.92, h * 0.02), (w * 0.70, h * 0.68), 10.5),
        ((w * 0.88, h * 0.34), (w * 1.00, h * 0.14), (w * 0.82, h * 0.72), 9.5),
    ]
    for (bx, by), (sx, sy), (ix, iy), br in bursts:
        steps = 12
        for k in range(steps):
            if k % 2 == 1:
                continue
            t0, t1 = k / steps, (k + 0.68) / steps
            x0 = sx + (bx - sx) * t0
            y0 = sy + (by - sy) * t0 - math.sin(t0 * math.pi) * 4
            x1 = sx + (bx - sx) * t1
            y1 = sy + (by - sy) * t1 - math.sin(t1 * math.pi) * 4
            p.line([(x0, y0), (x1, y1)], "#FF7849", 1.4)
        p.line([(ix, iy), (bx, by)], rgb("#80E2FF", 190), 1.2)
        p.glow(bx, by, br * 1.9, "#FF9E2C", 175, steps=12)
        starburst(p, bx, by, br, br * 0.38, "#FFB338", "#FFF9D6", rays=10)


def scene_peru_hero(p):
    """3. Peru M6.7 Quake (Hero 320x94): Andean snowcaps, Lima houses + bold cream seismograph."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.66, "#9DC7E6", "#F4EFE5")
    peaks = [(-8, 0.95), (w * 0.11, 0.24), (w * 0.22, 0.54), (w * 0.36, 0.12),
             (w * 0.50, 0.44), (w * 0.64, 0.16), (w * 0.78, 0.48), (w * 0.90, 0.22), (w + 8, 0.80)]
    pts = [(-8, h)] + [(x, h * y) for x, y in peaks] + [(w + 8, h)]
    p.poly(pts, "#79685A")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2:
            px, py = x1, h * y1
            p.poly([(px, py), (px - 14, py + 15), (px - 5, py + 11), (px, py + 18),
                    (px + 6, py + 11), (px + 14, py + 15)], "#FFFFFF")
    ridge(p, h * 0.66, h * 0.05, 1.8, 0.4, "#5E8046", y_floor=h * 0.76)

    # Stylized Andean & Lima adobe houses with subtle tremor shake arcs
    for hx, sc in ((w * 0.14, 1.0), (w * 0.23, 0.85), (w * 0.79, 1.05)):
        hy = h * 0.66
        p.poly([(hx - 8 * sc, hy), (hx + 8 * sc, hy - 1.5), (hx + 6.5 * sc, hy - 14 * sc),
                (hx - 9.5 * sc, hy - 12.5 * sc)], "#F7EBD5", "#5C4736", 0.75)
        p.poly([(hx - 11.5 * sc, hy - 12 * sc), (hx - 1.5 * sc, hy - 20 * sc),
                (hx + 9 * sc, hy - 14 * sc)], "#B8472F", "#5C4736", 0.7)
        p.rect(hx - 3 * sc, hy - 8 * sc, hx + 1.5 * sc, hy - 2 * sc, "#6E523F")
    p.arc(w * 0.79 - 1, h * 0.56, 17, 195, 250, "#A82824", 1.1)
    p.arc(w * 0.79 - 1, h * 0.56, 17, 295, 350, "#A82824", 1.1)

    # Clean archival cream seismograph tape across bottom 34% with bold crimson M6.7 spike
    sy0, sy1 = h * 0.66, h
    p.rect(0, sy0, w, sy1, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#B8AE9A", 0.8)
    for k in range(1, 20):
        p.line([(w * k / 20, sy0), (w * k / 20, sy1)], "#ECE4D6", 0.45)
    seismo(p, 6, w - 6, (sy0 + sy1) / 2, (sy1 - sy0) * 0.44, "#C82222", seed=12, width=1.35, burst=0.46)
    p.rect(w * 0.46 + 14, sy0 + 4, w * 0.46 + 64, sy0 + 17, "#A82824", r=2)
    p.text(w * 0.46 + 39, sy0 + 10.6, "M 6.7", 8.5, "#FFFFFF")


def scene_kyiv_warning(p):
    """4. Kyiv Warning: Ukrainian blue/gold sky, Kerch bridge span with bold vermilion warning mark."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.58, "#3B7AC4", "#7DB0E4")
    p.vgrad(h * 0.58, h * 0.72, "#F2CF68", "#F8E39A")
    waves(p, h * 0.70, h, "#25537A", "#153652", n=3, seed=19)

    # Bridge roadway & iconic white steel arch span across strait
    by = h * 0.62
    p.rect(0, by, w, by + 3.5, "#2F3A48")
    for px in (w * 0.14, w * 0.30, w * 0.70, w * 0.86):
        p.rect(px - 2.2, by + 3.5, px + 2.2, h * 0.76, "#3C4858")
    # Central steel arch
    pts = []
    for k in range(25):
        t = k / 24
        x = w * 0.28 + t * w * 0.44
        y = by - math.sin(t * math.pi) * 20.0
        pts.append((x, y))
    p.line(pts, "#F2F5F8", 2.6)
    for k in range(1, 8):
        t = k / 8
        x = w * 0.28 + t * w * 0.44
        y = by - math.sin(t * math.pi) * 20.0
        p.line([(x, by), (x, y)], "#DCE4EC", 0.8)

    # Bold vermilion cross-out warning slash over bridge arch
    cx, cy = w * 0.50, h * 0.46
    p.line([(cx - 18, cy - 13), (cx + 18, cy + 13)], "#C82222", 2.6)
    p.line([(cx + 18, cy - 13), (cx - 18, cy + 13)], "#C82222", 2.6)


def scene_hormuz_drone(p):
    """5. Hormuz Drone: sandstone strait cliffs, turquoise water, tanker + struck recon drone."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.46, "#EBC092", "#F8E7CE")
    p.poly([(0, h * 0.22), (w * 0.28, h * 0.30), (w * 0.58, h * 0.24), (w, h * 0.32),
            (w, h * 0.48), (0, h * 0.48)], "#B88E68")
    waves(p, h * 0.46, h, "#30829C", "#184E66", n=3, seed=15)

    # Oil tanker on left
    tx, ty = w * 0.30, h * 0.74
    p.poly([(tx - 32, ty - 4), (tx + 28, ty - 4), (tx + 34, ty - 8), (tx + 26, ty + 4),
            (tx - 30, ty + 4)], "#7E2E2A")
    p.rect(tx - 30, ty - 6, tx + 25, ty - 4, "#404852")
    p.rect(tx - 30, ty - 14, tx - 20, ty - 6, "#F4F1EA")
    for k in range(3):
        p.circle(tx - 12 + k * 10, ty - 7, 2.2, "#59626E")

    # Recon drone + burst plume upper-right
    smoke(p, w * 0.72, h * 0.20, -24, 22, 1.4, 3.8, 10, "#464A52", 155, seed=25)
    delta_drone(p, w * 0.64, h * 0.36, 8.0, "#1E242C", tilt=2.2)
    flames(p, w * 0.64, h * 0.39, 9, 8, seed=40)
    p.glow(w * 0.64, h * 0.36, 12, "#FFB23F", 150)


def scene_iran_uranium(p):
    """6. Iran Uranium: clean archival cream-and-tricolor frame, centrifuge & atomic rings in dome."""
    w, h = p.w, p.h
    p.rect(0, 0, w, h, "#F6F2E8")
    # Crisp thin Iran flag top & bottom accent bands
    p.rect(0, 0, w, 5.5, "#239F40")
    p.rect(0, h - 5.5, w, h, "#C82222")

    # Stylized atomic orbit + slate-indigo protective vault dome in center
    cx, cy = w * 0.48, h * 0.50
    p.ellipse(cx, cy, 38, 14, None, "#1F4A6E", 1.3)
    p.ellipse(cx, cy, 14, 22, None, "#186F7A", 1.3)
    p.circle(cx, cy, 8.5, "#182A40", "#E8B944", 1.4)
    p.text(cx, cy + 0.3, "U", 9.5, "#FFD25A")
    # Orbiting electrons
    for ex, ey in ((cx + 36, cy), (cx - 36, cy), (cx, cy - 21)):
        p.circle(ex, ey, 2.8, "#A82824", "#FFFFFF", 0.6)
    # Protective vault padlock badge on left
    lx, ly = w * 0.16, h * 0.52
    p.arc(lx, ly - 5, 6.5, 180, 360, "#4A5666", 1.8)
    p.rect(lx - 8, ly - 5, lx + 8, ly + 8, "#1F4A6E", "#131B26", 0.8, r=2)
    p.circle(lx, ly + 1, 2.0, "#F0C66E")


def scene_trump_ai_tax(p):
    """7. Trump AI Tax: architectural blueprint slate-blue, overseas AI data servers + vermilion % seal."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#1E3C60", "#132944")
    for k in range(1, 5):
        p.line([(0, h * k / 5), (w, h * k / 5)], rgb("#8CC4F5", 34), 0.45)
    for k in range(1, 9):
        p.line([(w * k / 9, 0), (w * k / 9, h)], rgb("#8CC4F5", 30), 0.45)

    # Overseas AI data-centre server racks left & right
    for rx in (w * 0.20, w * 0.78):
        p.rect(rx - 18, 11, rx + 18, h - 10, "#2A507C", "#99C9F5", 0.8, r=2)
        for row in range(4):
            yy = 16 + row * 8.5
            p.rect(rx - 14, yy, rx + 14, yy + 5.2, "#193352")
            p.circle(rx - 10, yy + 2.6, 1.3, "#5CE6A0")
            p.circle(rx - 5, yy + 2.6, 1.3, "#FFD24D")
    p.text(w * 0.78, h * 0.50, "AI", 10.5, rgb("#E6F2FF", 210))

    # Central bold vermilion & gold "%" tariff stamp
    cx, cy = w * 0.49, h * 0.49
    p.circle(cx, cy, 17.5, "#A82824", "#F4C858", 1.5)
    p.text(cx, cy + 0.5, "%", 18.0, "#FFFFFF")


def scene_china_japan(p):
    """8. China-Japan: diplomatic crimson & white flag panels divided by bold slate tension bolt."""
    w, h = p.w, p.h
    # Left half: China crimson with gold stars
    p.rect(0, 0, w * 0.50, h, "#C82222")
    star5(p, w * 0.16, h * 0.36, 7.5, "#FFDE00")
    for sx, sy in ((w * 0.27, h * 0.20), (w * 0.31, h * 0.32), (w * 0.31, h * 0.48), (w * 0.26, h * 0.60)):
        star5(p, sx, sy, 2.7, "#FFDE00")

    # Right half: Japan crisp white with sun disc
    p.rect(w * 0.50, 0, w, h, "#FAF8F4")
    p.circle(w * 0.76, h * 0.48, 13.5, "#BC002D")

    # Center diplomatic friction divider + Taiwan island emblem
    p.line([(w * 0.50, 0), (w * 0.50, h)], "#182A40", 1.2)
    p.circle(w * 0.50, h * 0.48, 12.5, "#182A40", "#F0C66E", 1.2)
    p.line([(w * 0.44, h * 0.48), (w * 0.56, h * 0.48)], "#FFFFFF", 1.8)
    p.poly([(w * 0.43, h * 0.48), (w * 0.47, h * 0.41), (w * 0.47, h * 0.55)], "#F0C66E")
    p.poly([(w * 0.57, h * 0.48), (w * 0.53, h * 0.41), (w * 0.53, h * 0.55)], "#F0C66E")


def scene_davao(p):
    """9. Davao Air Niugini 146 Safe: luminous tropical sky + runway + white 767 + alert & chute."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.68, "#82BEE8", "#EAF6FD")
    ridge(p, h * 0.63, h * 0.08, 1.4, 0.5, "#74A380", y_floor=h * 0.70)
    p.rect(0, h * 0.68, w, h, "#303944")
    p.line([(0, h * 0.68), (w, h * 0.68)], "#66717F", 0.8)
    for k in range(8):
        x0 = 6 + k * 24
        p.rect(x0, h * 0.82, x0 + 13, h * 0.86, "#EDF2F7")

    px, py = w * 0.46, h * 0.61
    p.poly([(px - 42, py - 2), (px - 53, py - 18), (px - 42, py - 18), (px - 31, py - 3)], "#181D24")
    p.poly([(px - 50, py - 16), (px - 43, py - 16), (px - 37.5, py - 8), (px - 44.5, py - 8)], "#D7262E")
    p.circle(px - 44, py - 12, 2.0, "#FFD23F")
    p.poly([(px - 46, py - 2), (px + 42, py - 4.5), (px + 54, py - 1), (px + 52, py + 4),
            (px - 40, py + 4)], "#FFFFFF", "#3A4450", 0.7)
    p.rect(px + 38, py - 3.2, px + 47, py - 1.0, "#1C2A3A")
    for k in range(11):
        p.rect(px - 26 + k * 5.6, py - 2.0, px - 23.2 + k * 5.6, py - 0.3, "#2F4864")
    p.poly([(px - 10, py + 1), (px + 12, py + 1), (px - 4, py + 9), (px - 16, py + 9)], "#D8E2EC", "#3A4450", 0.5)
    p.rect(px - 2, py + 3, px + 9, py + 7.2, "#4A5462", r=1.4)
    p.glow(px + 2, py + 5.2, 9.5, "#FF4522", 210, steps=10)
    p.circle(px + 2, py + 5.2, 2.6, "#FF6A1A")
    p.circle(px + 2, py + 5.2, 1.2, "#FFE680")
    smoke(p, px - 2, py + 4.8, -24, -3.5, 1.6, 4.8, 8, "#FFFFFF", 165, seed=21)
    p.poly([(px + 26, py + 3), (px + 33, py + 3), (px + 43, h * 0.85), (px + 34, h * 0.85)],
           "#FFF3C4", "#7D6F4B", 0.7)


def scene_canberra_ai(p):
    """10. Canberra AI Talks: sunlit ivory-teal sky, Parliament spire + Beijing roof + central AI dialogue node."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#D7EBF0", "#F6F2E8")
    p.rect(0, h * 0.76, w, h, "#5E8B63")

    # Left: Canberra Parliament House spire silhouette
    px = w * 0.18
    p.rect(px - 22, h * 0.62, px + 22, h * 0.76, "#FFFFFF", "#7B8A96", 0.7)
    p.line([(px - 12, h * 0.62), (px, h * 0.24), (px + 12, h * 0.62)], "#687886", 1.3)
    p.line([(px, h * 0.24), (px, h * 0.12)], "#687886", 1.1)
    p.rect(px, h * 0.12, px + 9, h * 0.18, "#1F4A6E")

    # Right: Beijing ceremonial pavilion roofline
    bx = w * 0.82
    p.rect(bx - 18, h * 0.56, bx + 18, h * 0.76, "#D8CFC0", "#7D6E5D", 0.7)
    p.poly([(bx - 24, h * 0.56), (bx, h * 0.38), (bx + 24, h * 0.56)], "#B8332A", "#6E201A", 0.7)
    for k in range(5):
        cx = bx - 13 + k * 6.5
        p.line([(cx, h * 0.56), (cx, h * 0.76)], "#8F2A24", 1.1)

    # Dialogue arcs + glowing central AI node
    p.line([(px + 14, h * 0.44), (w * 0.50, h * 0.38), (bx - 16, h * 0.44)], "#186F7A", 1.4)
    p.circle(w * 0.50, h * 0.38, 14.5, "#186F7A", "#FFFFFF", 1.2)
    p.text(w * 0.50, h * 0.385, "AI", 11.5, "#FFFFFF")


def scene_bitcoin(p):
    """11. Bitcoin $58,983: crisp dark-slate market ticker, amber coin emblem & vermilion dip below $59k."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#162436", "#101B29")
    for k in range(1, 5):
        p.line([(0, h * k / 5), (w, h * k / 5)], rgb("#FFFFFF", 24), 0.45)

    # Dashed $59k threshold line
    y59 = h * 0.54
    for x0 in range(44, int(w - 6), 8):
        p.line([(x0, y59), (x0 + 4, y59)], rgb("#F0C66E", 160), 0.7)

    # Price curve dipping below $59k
    pts = [
        (46, h * 0.24), (62, h * 0.28), (78, h * 0.22), (94, h * 0.36),
        (110, h * 0.34), (124, h * 0.50), (138, h * 0.62), (154, h * 0.70), (168, h * 0.64),
    ]
    area = [(pts[0][0], h)] + pts + [(pts[-1][0], h)]
    p.poly(area, rgb("#D9382E", 55))
    p.line(pts, "#FF5247", 2.0)
    p.circle(pts[-2][0], pts[-2][1], 3.0, "#FFD23F", "#C82222", 0.8)

    # Bold amber Bitcoin medallion on left
    p.circle(23, h * 0.48, 15.0, "#E5941A", "#FFE099", 1.2)
    p.text(23, h * 0.485, "B", 15.0, "#FFFFFF")
    p.line([(20.5, h * 0.48 - 10), (20.5, h * 0.48 + 10)], "#FFFFFF", 1.3)
    p.line([(25.0, h * 0.48 - 10), (25.0, h * 0.48 + 10)], "#FFFFFF", 1.3)

    # Crisp right stats
    p.text(w - 8, 11, "-3.9%", 9.2, "#FF6B61", anchor="rm")
    p.text(w - 8, 22, "ETH $1,625", 6.4, "#B8C7D8", F_SANS_BOLD, anchor="rm")


def scene_russell_p1(p):
    """12. Russell P1 Las Vegas: damp night strip circuit, sleek silver-teal F1 car & 1:34.041 timing."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.40, "#142038", "#263A5C")
    p.rect(0, h * 0.40, w, h, "#252C36")
    # Neon Strip reflections & damp rain streaks
    for lx, col in ((22, "#FF4D6D"), (52, "#4CC9F0"), (84, "#F7B801"), (114, "#7209B7")):
        p.rect(lx, h * 0.14, lx + 14, h * 0.40, rgb(col, 65))
    # Checkered start/finish band on right
    fx = w * 0.78
    for r in range(6):
        for c in range(2):
            col = "#FFFFFF" if (r + c) % 2 == 0 else "#181C22"
            p.rect(fx + c * 5, h * 0.40 + r * 5.4, fx + (c + 1) * 5, h * 0.40 + (r + 1) * 5.4, col)

    # Sleek silver & Petronas-teal F1 car silhouette speeding right
    cx, cy = w * 0.42, h * 0.70
    p.poly([(cx - 38, cy + 3), (cx - 32, cy - 8), (cx - 10, cy - 8), (cx + 2, cy - 11),
            (cx + 18, cy - 4), (cx + 42, cy + 1), (cx + 42, cy + 5), (cx - 38, cy + 5)], "#D6DDE6", "#18202A", 0.6)
    p.rect(cx - 26, cy - 2, cx + 26, cy + 1.5, "#00A19C")  # teal stripe
    p.rect(cx - 42, cy - 12, cx - 34, cy - 2, "#18202A")   # rear wing
    p.rect(cx + 38, cy + 1, cx + 46, cy + 5, "#00A19C")    # front wing
    p.circle(cx - 2, cy - 10, 3.2, "#1A222C")              # helmet/halo
    for wx in (cx - 24, cx + 24):
        p.circle(wx, cy + 4, 6.2, "#12161C")
        p.circle(wx, cy + 4, 2.8, "#7D8896")

    # Crisp gold-trimmed timing badge upper-right
    p.rect(w - 58, 5, w - 5, 19, "#11161D", "#F0C842", 0.8, r=1.5)
    p.text(w - 31.5, 12.2, "1:34.041", 8.0, "#FFD23F")


def scene_rahul(p):
    """13. KL Rahul 124* Wellington: kiwi sky, emerald Basin Reserve oval, willow bat & 124* board."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.42, "#8AC4E8", "#DCEFF9")
    ridge(p, h * 0.40, h * 0.08, 1.4, 0.9, "#6A9472", y_floor=h * 0.46)
    p.rect(0, h * 0.42, w, h, "#258C42")
    for k in range(1, 5):
        p.ellipse(w * 0.5, h * 0.78, w * 0.62 * (1 - k * 0.18), h * 0.46 * (1 - k * 0.18),
                  None, rgb("#38AC58", 130), 1.6)
    p.rect(w * 0.44, h * 0.50, w * 0.54, h * 0.98, "#E3CFA0")
    for dx in (-2.0, 0, 2.0):
        p.line([(w * 0.49 + dx, h * 0.60), (w * 0.49 + dx, h * 0.50)], "#FFFFFF", 0.8)

    # Raised willow cricket bat + crimson Test leather ball
    p.poly([(w * 0.18, h * 0.92), (w * 0.30, h * 0.44), (w * 0.37, h * 0.46), (w * 0.25, h * 0.94)],
           "#E9C584", "#7B5B2A", 0.9)
    p.line([(w * 0.335, h * 0.45), (w * 0.37, h * 0.31)], "#1F4A6E", 2.6)
    p.circle(w * 0.61, h * 0.34, 5.2, "#B81D24", "#FFFFFF", 0.6)
    p.arc(w * 0.61, h * 0.34, 3.4, 110, 250, "#FFFFFF", 0.65)

    # Crisp dark-and-gold Wellington Test scoreboard "124*"
    p.rect(w * 0.71, h * 0.10, w * 0.96, h * 0.46, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w * 0.835, h * 0.285, "124*", 10.8, "#FFD23F")


SCENES = {
    1: scene_cop31,
    2: scene_saudi_missiles,
    3: scene_peru_hero,
    4: scene_kyiv_warning,
    5: scene_hormuz_drone,
    6: scene_iran_uranium,
    7: scene_trump_ai_tax,
    8: scene_china_japan,
    9: scene_davao,
    10: scene_canberra_ai,
    11: scene_bitcoin,
    12: scene_russell_p1,
    13: scene_rahul,
}


def draw_scene(sid, w, h, out_scale=2, supersample=4):
    p = Pen(w, h, out_scale * supersample)
    SCENES[sid](p)
    return p.render(round(w * out_scale), round(h * out_scale))
