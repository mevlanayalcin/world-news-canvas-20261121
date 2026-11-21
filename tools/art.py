"""Original silkscreen-editorial vector illustrations, one per illustrated story (ids 1-13, v5).

Each scene draws into an 8x supersampled Pen in 1x layout coordinates and
downsamples with LANCZOS for razor-sharp printmaking edges. Every focal element
is composed cleanly in the open lower and right zones so bold upper-left
vermilion editorial ribbons and white sub-tags never cover key storytelling art.
Everything is 100% deterministic (fixed-seed LCG only).
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
    """1. COP31 Antalya (320x114): warm sunrise, oil derrick vs turbines, plenary & right-side overtime clock."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.78, "#F2C794", "#FBF0DC")
    p.glow(w * 0.65, h * 0.62, h * 0.72, "#FFE3A6", 145)
    ridge(p, h * 0.68, h * 0.09, 1.5, 0.7, "#C8A488", y_floor=h * 0.80)
    ridge(p, h * 0.74, h * 0.06, 2.3, 1.9, "#A37F6A", y_floor=h * 0.80)
    waves(p, h * 0.78, h, "#2D7899", "#174A66", n=3, seed=11)

    # Lower-left: compact oil derrick sitting cleanly below banner + sub-chip (top at y=58)
    dx, base = w * 0.13, h * 0.82
    p.poly([(dx - 11, base), (dx - 2.5, base - 36), (dx + 2.5, base - 36), (dx + 11, base)],
           None, "#322723", 1.4)
    for k in range(1, 4):
        yy = base - k * 9
        half = 11 - k * 2.1
        p.line([(dx - half, yy), (dx + half, yy)], "#322723", 1.0)
    p.rect(dx + 6, base - 23, dx + 28, base - 19, "#322723")
    p.poly([(dx + 26, base - 28), (dx + 34, base - 21), (dx + 26, base - 14)], "#322723")

    # Lower-mid: Antalya plenary pavilion + delegate flags (below sub-chip)
    hx0, hx1, hy = w * 0.28, w * 0.64, h * 0.82
    p.rect(hx0, hy - 16, hx1, hy, "#F2ECE0", "#7D6F61", 0.7)
    p.poly([(hx0 - 5, hy - 16), ((hx0 + hx1) / 2, hy - 27), (hx1 + 5, hy - 16)],
           "#DED2BF", "#7D6F61", 0.7)
    for i in range(8):
        x = hx0 + 6 + i * (hx1 - hx0 - 12) / 7
        p.rect(x - 1.9, hy - 12, x + 1.9, hy, "#B4A592")
    flag_cols = ["#A82824", "#1F4A6E", "#266B47", "#E6B422", "#186F7A", "#C82828", "#2B7A4B", "#264E86"]
    for i, c in enumerate(flag_cols):
        x = hx0 + i * (hx1 - hx0) / (len(flag_cols) - 1)
        p.line([(x, hy), (x, hy - 24)], "#4B423A", 0.55)
        p.rect(x, hy - 24, x + 5.6, hy - 20, c)

    # Right: three crisp white wind turbines in clear open right zone
    for tx, th, ang in ((w * 0.72, 40, 72), (w * 0.89, 54, 14), (w * 0.96, 44, 48)):
        top = base - th
        p.poly([(tx - 1.5, base), (tx - 0.6, top), (tx + 0.6, top), (tx + 1.5, base)], "#FFFFFF", "#8C9CA6", 0.4)
        for k in range(3):
            a = math.radians(ang + k * 120)
            p.line([(tx, top), (tx + math.cos(a) * th * 0.38, top + math.sin(a) * th * 0.38)], "#FFFFFF", 1.7)
        p.circle(tx, top, 1.7, "#3B4A54")

    # Upper-right: crisp archival brass-rimmed overtime clock + "+1 DAY" pill (100% clear of top-left banner!)
    cx, cy, cr = w * 0.77, h * 0.30, 21.5
    p.circle(cx + 1.0, cy + 1.5, cr + 2.2, (50, 35, 20, 55))
    p.circle(cx, cy, cr + 2.2, "#182A40")
    p.circle(cx, cy, cr, "#FFFDF8")
    p.d.pieslice([(cx - cr) * p.s, (cy - cr) * p.s, (cx + cr) * p.s, (cy + cr) * p.s],
                 -90, 12, fill=rgb("#A82824", 205))
    for k in range(12):
        a = math.radians(k * 30 - 90)
        r0 = cr * (0.74 if k % 3 == 0 else 0.85)
        p.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * cr * 0.95, cy + math.sin(a) * cr * 0.95)],
               "#131B26", 1.3 if k % 3 == 0 else 0.65)
    p.line([(cx, cy), (cx + math.cos(math.radians(-68)) * cr * 0.5,
                      cy + math.sin(math.radians(-68)) * cr * 0.5)], "#131B26", 2.1)
    p.line([(cx, cy), (cx + math.cos(math.radians(12)) * cr * 0.80,
                      cy + math.sin(math.radians(12)) * cr * 0.80)], "#131B26", 1.4)
    p.circle(cx, cy, 1.9, "#A82824")
    p.rect(cx - 21, cy + cr + 4, cx + 21, cy + cr + 18, "#A82824", "#FFFDF8", 0.85, r=2)
    p.text(cx, cy + cr + 11.2, "+1 DAY", 8.8, "#FFFFFF")


def scene_saudi_missiles(p):
    """2. Saudi 5 Missiles (320x114): midnight sky, Riyadh skyline right/bottom + 5 starbursts in right sky."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#0F203B", "#223D68")
    stars(p, 95, 29, y1=h * 0.68)
    p.glow(w * 0.72, h * 0.84, 110, "#F0B954", 90)
    p.rect(0, h * 0.80, w, h, "#101E36")

    # Left low skyline cleanly beneath banner + sub-chip
    for x, bw, bh in [(10, 20, 22), (34, 18, 26), (56, 22, 20), (82, 18, 30), (104, 24, 24), (132, 20, 32)]:
        p.rect(x, h - bh, x + bw, h, "#172A48", "#355382", 0.55)
        for yy in range(int(h - bh + 4), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                if ((int(xx) * 7 + yy * 13) % 5) < 3:
                    p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F7C960")

    # Iconic Kingdom Centre tower in clear right-center
    kx, kh = w * 0.57, 64.0
    p.poly([(kx - 11, h), (kx - 9.5, h - kh), (kx + 9.5, h - kh), (kx + 11, h)], "#213860", "#7C9ED1", 0.8)
    p.poly([(kx - 5.5, h - kh + 1), (kx + 5.5, h - kh + 1), (kx + 3.8, h - kh + 16),
            (kx, h - kh + 20), (kx - 3.8, h - kh + 16)], "#1A325A")
    p.line([(kx - 7.5, h - kh + 2), (kx + 7.5, h - kh + 2)], "#FFE59E", 1.2)
    for yy in range(int(h - kh + 23), int(h - 4), 5):
        for xx in (kx - 6, kx - 2, kx + 2, kx + 5):
            p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F9D06B")

    # Al Faisaliah pyramid spire + golden orb
    fx, fh = w * 0.72, 54.0
    p.poly([(fx - 12, h), (fx, h - fh), (fx + 12, h)], "#1D3358", "#7C9ED1", 0.8)
    p.line([(fx, h - fh), (fx, h - fh - 7)], "#B0CBF0", 1.0)
    p.circle(fx, h - fh + 10, 4.0, "#F8C846", "#FFF2B2", 0.6)
    for k in range(5):
        yy = h - 7 - k * 7.5
        hw = 9 - k * 1.4
        p.line([(fx - hw, yy), (fx + hw, yy)], rgb("#F8D374", 190), 0.85)

    # KAFD right towers
    for x, bw, bh in [(w * 0.80, 17, 44), (w * 0.87, 19, 50), (w * 0.94, 18, 34)]:
        p.poly([(x, h), (x, h - bh), (x + bw, h - bh + 6), (x + bw, h)], "#1B3054", "#6486BA", 0.7)
        for yy in range(int(h - bh + 8), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F5C65D")

    # 5 bright intercepted Houthi missiles soaring cleanly across right & mid-right sky!
    bursts = [
        ((w * 0.55, h * 0.34), (w * 0.72, h * 0.02), (w * 0.48, h * 0.78), 9.5),
        ((w * 0.65, h * 0.18), (w * 0.84, h * 0.01), (w * 0.60, h * 0.72), 11.5),
        ((w * 0.76, h * 0.28), (w * 0.96, h * 0.04), (w * 0.72, h * 0.72), 11.5),
        ((w * 0.86, h * 0.16), (w * 1.01, h * 0.01), (w * 0.82, h * 0.68), 10.5),
        ((w * 0.93, h * 0.34), (w * 1.02, h * 0.18), (w * 0.89, h * 0.74), 9.0),
    ]
    for (bx, by), (sx, sy), (ix, iy), br in bursts:
        steps = 11
        for k in range(steps):
            if k % 2 == 1:
                continue
            t0, t1 = k / steps, (k + 0.68) / steps
            x0 = sx + (bx - sx) * t0
            y0 = sy + (by - sy) * t0 - math.sin(t0 * math.pi) * 3.5
            x1 = sx + (bx - sx) * t1
            y1 = sy + (by - sy) * t1 - math.sin(t1 * math.pi) * 3.5
            p.line([(x0, y0), (x1, y1)], "#FF7849", 1.45)
        p.line([(ix, iy), (bx, by)], rgb("#80E2FF", 190), 1.2)
        p.glow(bx, by, br * 1.85, "#FF9E2C", 180, steps=12)
        starburst(p, bx, by, br, br * 0.38, "#FFB338", "#FFF9D6", rays=10)


def scene_peru_hero(p):
    """3. Peru M6.7 Quake (320x114): right-side snowcaps, Lima houses + bold full-width seismograph."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.70, "#9DC7E6", "#F4EFE5")
    # Dramatic snow-capped Junin Andes rising across right & mid-right (clear of top-left banner!)
    peaks = [(-8, 0.95), (w * 0.20, 0.56), (w * 0.38, 0.60), (w * 0.55, 0.22),
             (w * 0.68, 0.46), (w * 0.79, 0.12), (w * 0.90, 0.36), (w * 0.97, 0.20), (w + 8, 0.78)]
    pts = [(-8, h)] + [(x, h * y) for x, y in peaks] + [(w + 8, h)]
    p.poly(pts, "#79685A")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2 and x1 > w * 0.45:
            px, py = x1, h * y1
            p.poly([(px, py), (px - 14, py + 15), (px - 5, py + 11), (px, py + 18),
                    (px + 6, py + 11), (px + 14, py + 15)], "#FFFFFF")
    ridge(p, h * 0.68, h * 0.04, 1.8, 0.4, "#5E8046", y_floor=h * 0.76)

    # Adobe houses in lower-center & lower-right with tremor shake arcs
    for hx, sc in ((w * 0.62, 0.95), (w * 0.74, 1.1), (w * 0.86, 0.9)):
        hy = h * 0.70
        p.poly([(hx - 8 * sc, hy), (hx + 8 * sc, hy - 1.5), (hx + 6.5 * sc, hy - 14 * sc),
                (hx - 9.5 * sc, hy - 12.5 * sc)], "#F7EBD5", "#5C4736", 0.75)
        p.poly([(hx - 11.5 * sc, hy - 12 * sc), (hx - 1.5 * sc, hy - 20 * sc),
                (hx + 9 * sc, hy - 14 * sc)], "#B8472F", "#5C4736", 0.7)
        p.rect(hx - 3 * sc, hy - 8 * sc, hx + 1.5 * sc, hy - 2 * sc, "#6E523F")
    p.arc(w * 0.74 - 1, h * 0.59, 17, 195, 250, "#A82824", 1.1)
    p.arc(w * 0.74 - 1, h * 0.59, 17, 295, 350, "#A82824", 1.1)

    # Full-width archival cream seismograph strip (y=72..98) clearly above bottom-left chip!
    sy0, sy1 = h * 0.69, h * 0.96
    p.rect(0, sy0, w, h, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#B8AE9A", 0.8)
    for k in range(1, 20):
        p.line([(w * k / 20, sy0), (w * k / 20, h)], "#ECE4D6", 0.45)
    seismo(p, 6, w - 6, (sy0 + sy1) / 2, (sy1 - sy0) * 0.46, "#C82222", seed=12, width=1.45, burst=0.60)
    p.rect(w * 0.65, sy0 + 4, w * 0.65 + 48, sy0 + 18, "#A82824", r=2)
    p.text(w * 0.65 + 24, sy0 + 11.2, "M 6.7", 8.8, "#FFFFFF")


def scene_kyiv_warning(p):
    """4. Kyiv Warning (188x70): Ukrainian blue/gold sky, Kerch bridge span below banner + vermilion X."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.58, "#3B7AC4", "#7DB0E4")
    p.vgrad(h * 0.58, h * 0.74, "#F2CF68", "#F8E39A")
    waves(p, h * 0.73, h, "#25537A", "#153652", n=3, seed=19)

    by = h * 0.69
    p.rect(0, by, w, by + 3.5, "#2F3A48")
    for px in (w * 0.14, w * 0.30, w * 0.70, w * 0.86):
        p.rect(px - 2.2, by + 3.5, px + 2.2, h * 0.82, "#3C4858")
    pts = []
    for k in range(25):
        t = k / 24
        x = w * 0.28 + t * w * 0.44
        y = by - math.sin(t * math.pi) * 17.5
        pts.append((x, y))
    p.line(pts, "#F2F5F8", 2.5)
    for k in range(1, 8):
        t = k / 8
        x = w * 0.28 + t * w * 0.44
        y = by - math.sin(t * math.pi) * 17.5
        p.line([(x, by), (x, y)], "#DCE4EC", 0.8)

    cx, cy = w * 0.50, h * 0.57
    p.line([(cx - 17, cy - 10.5), (cx + 17, cy + 10.5)], "#C82222", 2.6)
    p.line([(cx + 17, cy - 10.5), (cx - 17, cy + 10.5)], "#C82222", 2.6)


def scene_hormuz_drone(p):
    """5. Hormuz Drone (188x70): strait cliffs, turquoise water, tanker lower-left + struck drone right."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.50, "#EBC092", "#F8E7CE")
    p.poly([(0, h * 0.34), (w * 0.28, h * 0.40), (w * 0.58, h * 0.34), (w, h * 0.40),
            (w, h * 0.54), (0, h * 0.54)], "#B88E68")
    waves(p, h * 0.52, h, "#30829C", "#184E66", n=3, seed=15)

    tx, ty = w * 0.30, h * 0.76
    p.poly([(tx - 32, ty - 4), (tx + 28, ty - 4), (tx + 34, ty - 8), (tx + 26, ty + 4),
            (tx - 30, ty + 4)], "#7E2E2A")
    p.rect(tx - 30, ty - 6, tx + 25, ty - 4, "#404852")
    p.rect(tx - 30, ty - 14, tx - 20, ty - 6, "#F4F1EA")
    for k in range(3):
        p.circle(tx - 12 + k * 10, ty - 7, 2.2, "#59626E")

    # Two claimed recon drones (burning drone + second distant drone) in open right sky
    smoke(p, w * 0.84, h * 0.22, -22, 22, 1.5, 4.0, 10, "#464A52", 160, seed=25)
    delta_drone(p, w * 0.77, h * 0.38, 8.2, "#1E242C", tilt=2.2)
    flames(p, w * 0.77, h * 0.41, 9, 8, seed=40)
    p.glow(w * 0.77, h * 0.38, 12, "#FFB23F", 150)
    delta_drone(p, w * 0.90, h * 0.17, 5.4, "#1E242C", tilt=2.5)
    p.glow(w * 0.90, h * 0.17, 6.5, "#FFB23F", 130, steps=8)


def scene_iran_uranium(p):
    """6. Iran Uranium (188x70): cream archival frame + tricolor bars + padlock & atomic U cleanly below banner."""
    w, h = p.w, p.h
    p.rect(0, 0, w, h, "#F6F2E8")
    p.rect(0, 0, w, 4.5, "#239F40")
    p.rect(0, h - 4.5, w, h, "#C82222")

    # Padlock lower-left + atomic U rings centered cleanly at y=45 (below banner bottom y=25!)
    lx, ly = w * 0.17, h * 0.66
    p.arc(lx, ly - 5, 6.2, 180, 360, "#4A5666", 1.8)
    p.rect(lx - 7.5, ly - 5, lx + 7.5, ly + 8, "#1F4A6E", "#131B26", 0.8, r=2)
    p.circle(lx, ly + 1, 2.0, "#F0C66E")

    cx, cy = w * 0.61, h * 0.65
    p.ellipse(cx, cy, 34, 11.5, None, "#1F4A6E", 1.3)
    p.ellipse(cx, cy, 11.5, 16.5, None, "#186F7A", 1.3)
    p.circle(cx, cy, 7.8, "#182A40", "#E8B944", 1.4)
    p.text(cx, cy + 0.3, "U", 8.8, "#FFD25A")
    for ex, ey in ((cx + 33, cy), (cx - 33, cy), (cx, cy - 16.0)):
        p.circle(ex, ey, 2.4, "#A82824", "#FFFFFF", 0.6)


def scene_trump_ai_tax(p):
    """7. Trump AI Tax (188x70): blueprint slate-blue, overseas AI racks & vermilion % cleanly below banner."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#1E3C60", "#132944")
    for k in range(1, 6):
        p.line([(0, h * k / 6), (w, h * k / 6)], rgb("#8CC4F5", 34), 0.45)
    for k in range(1, 9):
        p.line([(w * k / 9, 0), (w * k / 9, h)], rgb("#8CC4F5", 30), 0.45)

    # Lower-left & right overseas AI server racks (clear of top-left banner!)
    for rx, y_top in ((w * 0.21, 30), (w * 0.81, 14)):
        p.rect(rx - 17, y_top, rx + 17, h - 13, "#2A507C", "#99C9F5", 0.8, r=2)
        rows = 3 if y_top > 20 else 4
        for row in range(rows):
            yy = y_top + 4.5 + row * 8.2
            p.rect(rx - 13, yy, rx + 13, yy + 5.0, "#193352")
            p.circle(rx - 9, yy + 2.5, 1.3, "#5CE6A0")
            p.circle(rx - 4, yy + 2.5, 1.3, "#FFD24D")
    p.text(w * 0.81, h * 0.44, "AI", 10.5, rgb("#E6F2FF", 215))

    # Bold vermilion & gold "%" tariff stamp in lower-center (top at y=30, clear of banner y=25!)
    cx, cy = w * 0.51, h * 0.64
    p.circle(cx, cy, 15.5, "#A82824", "#F4C858", 1.4)
    p.text(cx, cy + 0.5, "%", 16.5, "#FFFFFF")


def scene_china_japan(p):
    """8. China-Japan (188x70): crimson China left + white Japan right, stars & emblem cleanly below banner."""
    w, h = p.w, p.h
    p.rect(0, 0, w * 0.50, h, "#C82222")
    # Stars nestled neatly below the upper-left banner
    star5(p, w * 0.14, h * 0.62, 7.2, "#FFDE00")
    for sx, sy in ((w * 0.25, h * 0.48), (w * 0.29, h * 0.58), (w * 0.29, h * 0.72), (w * 0.24, h * 0.82)):
        star5(p, sx, sy, 2.5, "#FFDE00")

    p.rect(w * 0.50, 0, w, h, "#FAF8F4")
    p.circle(w * 0.77, h * 0.48, 14.0, "#BC002D")

    p.line([(w * 0.50, 0), (w * 0.50, h)], "#182A40", 1.2)
    p.circle(w * 0.50, h * 0.62, 12.0, "#182A40", "#F0C66E", 1.2)
    p.line([(w * 0.44, h * 0.62), (w * 0.56, h * 0.62)], "#FFFFFF", 1.8)
    p.poly([(w * 0.43, h * 0.62), (w * 0.47, h * 0.55), (w * 0.47, h * 0.69)], "#F0C66E")
    p.poly([(w * 0.57, h * 0.62), (w * 0.53, h * 0.55), (w * 0.53, h * 0.69)], "#F0C66E")


def scene_davao(p):
    """9. Davao Air Niugini 146 Safe (188x70): tropical sky + runway + white 767 cleanly below banner."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.72, "#82BEE8", "#EAF6FD")
    ridge(p, h * 0.68, h * 0.06, 1.4, 0.5, "#74A380", y_floor=h * 0.74)
    p.rect(0, h * 0.72, w, h, "#303944")
    p.line([(0, h * 0.72), (w, h * 0.72)], "#66717F", 0.8)
    for k in range(8):
        x0 = 6 + k * 24
        p.rect(x0, h * 0.84, x0 + 13, h * 0.88, "#EDF2F7")

    px, py = w * 0.46, h * 0.66
    # Air Niugini tail (top at y=30, well below banner bottom y=25!)
    p.poly([(px - 42, py - 2), (px - 52, py - 16), (px - 42, py - 16), (px - 31, py - 3)], "#181D24")
    p.poly([(px - 49.5, py - 14.5), (px - 43, py - 14.5), (px - 37.5, py - 7.5), (px - 44, py - 7.5)], "#D7262E")
    p.circle(px - 43.5, py - 11.0, 1.8, "#FFD23F")
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
    p.poly([(px + 26, py + 3), (px + 33, py + 3), (px + 43, h * 0.87), (px + 34, h * 0.87)],
           "#FFF3C4", "#7D6F4B", 0.7)


def scene_bepicolombo(p):
    """10. BepiColombo Mercury Orbit (188x70): deep-space Mercury crescent + dual-orbiter silkscreen."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#070D21", "#162447")
    stars(p, 90, 21)
    # Warm solar rim glow from bottom-left
    p.glow(-8, h * 0.85, 58, "#FFE299", 145, steps=18)

    # Sculpted cratered Mercury crescent on right half (100% clear of upper-left banner + white sub-tag!)
    mx, my, mr = w * 0.85, h * 0.55, 29.0
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
    for _ in range(26):
        a, rr = rnd.uniform(0, 6.283), mr * math.sqrt(rnd.next()) * 0.90
        cx, cy = mx + math.cos(a) * rr, my + math.sin(a) * rr
        if cy > h + 3 or cx > w + 3:
            continue
        cr = rnd.uniform(1.1, 4.2)
        is_lit = cx < mx - mr * 0.08
        p.ellipse(cx, cy, cr, cr * 0.85, rgb("#7B746A" if is_lit else "#3E3A36", 225))
        p.arc(cx, cy, cr, 200, 340, rgb("#DAD2C5" if is_lit else "#68625B", 215), 0.5)
    p.circle(mx, my, mr, None, rgb("#D8D0C2", 140), 0.9)

    # Dashed luminous cyan capture-orbit ellipse looping around Mercury
    for k in range(36):
        if k % 2:
            continue
        a0, a1 = k / 36 * 6.283, (k + 0.85) / 36 * 6.283
        pts = [(mx + math.cos(a) * mr * 1.52, my - 2 + math.sin(a) * mr * 0.55)
               for a in (a0, (a0 + a1) / 2, a1)]
        if all(math.hypot(x - mx, y - my) > mr * 0.96 or y < my - mr * 0.25 for x, y in pts):
            p.line(pts, rgb("#7FD6FF", 210), 0.9)

    # Stacked BepiColombo spacecraft (gold MPO + white Mio drum + blue solar wing + thruster glow)
    # Positioned cleanly in lower-center (x=28..108, y=46..64), 100% clear of banner + sub-tag!
    sx, sy = w * 0.44, h * 0.77
    p.glow(sx + 12, sy, 8.5, "#8BE0FF", 210, steps=10)
    p.line([(sx + 6, sy), (sx + 20, sy)], rgb("#A8E6FF", 210), 2.4)
    # Solar wing extending left
    p.rect(sx - 44, sy - 3.6, sx - 9, sy + 3.6, "#285094", "#A4C2E8", 0.55)
    for k in range(1, 6):
        gx = sx - 44 + k * 35 / 6
        p.line([(gx, sy - 3.6), (gx, sy + 3.6)], rgb("#A4C2E8", 160), 0.4)
    p.line([(sx - 44, sy), (sx - 9, sy)], rgb("#A4C2E8", 160), 0.4)
    p.rect(sx - 9, sy - 0.8, sx - 6, sy + 0.8, "#C0C6CE")
    # Gold MPO spacecraft body
    p.rect(sx - 6, sy - 6, sx + 6, sy + 6, "#E3AF44", "#8A641E", 0.6)
    p.line([(sx - 6, sy), (sx + 6, sy)], rgb("#8A641E", 170), 0.45)
    # White octagonal JAXA Mio orbiter stacked atop MPO
    p.poly([(sx - 4.2, sy - 6), (sx + 4.2, sy - 6), (sx + 3.0, sy - 11.5), (sx - 3.0, sy - 11.5)],
           "#F2F4F7", "#8B95A2", 0.45)
    p.ellipse(sx, sy - 11.5, 3.0, 1.1, "#FFFFFF")


def scene_bitcoin(p):
    """11. Bitcoin $58,983 (188x70): crisp dark-slate ticker, amber coin lower-left & red dip below $59k."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#162436", "#101B29")
    for k in range(1, 6):
        p.line([(0, h * k / 6), (w, h * k / 6)], rgb("#FFFFFF", 22), 0.45)

    # Dashed $59k line + downward intraday chart in lower-mid/right
    y59 = h * 0.56
    for x0 in range(44, int(w - 6), 8):
        p.line([(x0, y59), (x0 + 4, y59)], rgb("#F0C66E", 160), 0.7)

    pts = [
        (46, h * 0.36), (62, h * 0.40), (78, h * 0.34), (94, h * 0.44),
        (110, h * 0.42), (124, h * 0.56), (138, h * 0.66), (154, h * 0.72), (168, h * 0.66),
    ]
    area = [(pts[0][0], h)] + pts + [(pts[-1][0], h)]
    p.poly(area, rgb("#D9382E", 55))
    p.line(pts, "#FF5247", 2.0)
    p.circle(pts[-2][0], pts[-2][1], 3.0, "#FFD23F", "#C82222", 0.8)

    # Bold amber Bitcoin medallion lower-left (top at y=34, completely clear of banner y=25!)
    p.circle(23, h * 0.68, 13.5, "#E5941A", "#FFE099", 1.2)
    p.text(23, h * 0.685, "B", 13.5, "#FFFFFF")
    p.line([(20.8, h * 0.68 - 9), (20.8, h * 0.68 + 9)], "#FFFFFF", 1.2)
    p.line([(24.8, h * 0.68 - 9), (24.8, h * 0.68 + 9)], "#FFFFFF", 1.2)

    p.text(w - 7, 13, "-3.9%", 9.2, "#FF6B61", anchor="rm")
    p.text(w - 7, 25, "ETH $1,625", 6.5, "#B8C7D8", F_SANS_BOLD, anchor="rm")


def scene_vegas_pole(p):
    """12. Las Vegas GP Pole (188x70): night Strip circuit, Verstappen Red Bull F1 car + checkered P1."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.46, "#142038", "#263A5C")
    p.rect(0, h * 0.46, w, h, "#252C36")
    # Neon Strip glow bars on right half
    for lx, col in ((96, "#FF4D6D"), (114, "#4CC9F0"), (132, "#F7B801"), (150, "#7209B7")):
        p.rect(lx, h * 0.22, lx + 11, h * 0.46, rgb(col, 68))
    # Checkered start/finish line on right
    fx = w * 0.80
    for r in range(6):
        for c in range(2):
            col = "#FFFFFF" if (r + c) % 2 == 0 else "#181C22"
            p.rect(fx + c * 5, h * 0.46 + r * 5.2, fx + (c + 1) * 5, h * 0.46 + (r + 1) * 5.2, col)

    # Sleek Red Bull midnight-navy/crimson/gold F1 car speeding right cleanly along bottom half (y=46..64)
    cx, cy = w * 0.44, h * 0.77
    p.poly([(cx - 38, cy + 3), (cx - 32, cy - 8), (cx - 10, cy - 8), (cx + 2, cy - 10.5),
            (cx + 18, cy - 3.5), (cx + 42, cy + 1), (cx + 42, cy + 5), (cx - 38, cy + 5)],
           "#1A2B56", "#88A4D8", 0.6)
    p.rect(cx - 24, cy - 2.5, cx + 22, cy + 1.5, "#D9242E")   # crimson bull livery accent
    p.poly([(cx + 30, cy - 1), (cx + 42, cy + 1), (cx + 42, cy + 4.5), (cx + 30, cy + 4)], "#F4C430")  # gold nose
    p.rect(cx - 42, cy - 11.5, cx - 34, cy - 2, "#131822")   # rear wing
    p.circle(cx - 2, cy - 9.5, 3.0, "#F4C430")               # helmet
    for wx in (cx - 24, cx + 24):
        p.circle(wx, cy + 4, 5.8, "#12161C")
        p.circle(wx, cy + 4, 2.5, "#D9242E")

    # Crisp gold P1 badge in upper-right clear zone
    p.rect(w - 36, 5, w - 5, 22, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w - 20.5, 13.8, "P1", 10.5, "#FFD23F")


def scene_rahul(p):
    """13. KL Rahul 124* Wellington (188x70): kiwi sky, emerald oval, willow bat lower-left + 124* right."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.46, "#8AC4E8", "#DCEFF9")
    ridge(p, h * 0.44, h * 0.06, 1.4, 0.9, "#6A9472", y_floor=h * 0.50)
    p.rect(0, h * 0.46, w, h, "#258C42")
    for k in range(1, 5):
        p.ellipse(w * 0.5, h * 0.80, w * 0.62 * (1 - k * 0.18), h * 0.46 * (1 - k * 0.18),
                  None, rgb("#38AC58", 130), 1.6)
    p.rect(w * 0.44, h * 0.54, w * 0.54, h * 0.98, "#E3CFA0")
    for dx in (-2.0, 0, 2.0):
        p.line([(w * 0.49 + dx, h * 0.64), (w * 0.49 + dx, h * 0.54)], "#FFFFFF", 0.8)

    # Willow bat & crimson Test ball cleanly in lower half (below banner y=25!)
    p.poly([(w * 0.18, h * 0.94), (w * 0.29, h * 0.52), (w * 0.36, h * 0.54), (w * 0.25, h * 0.96)],
           "#E9C584", "#7B5B2A", 0.9)
    p.line([(w * 0.325, h * 0.53), (w * 0.36, h * 0.40)], "#1F4A6E", 2.5)
    p.circle(w * 0.63, h * 0.47, 5.2, "#B81D24", "#FFFFFF", 0.6)
    p.arc(w * 0.63, h * 0.47, 3.4, 110, 250, "#FFFFFF", 0.65)

    # Crisp dark-and-gold Wellington Test scoreboard "136" in upper-right clear zone
    p.rect(w * 0.72, 5, w - 5, 29, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w * 0.85, 17.5, "136", 11.4, "#FFD23F")


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
    10: scene_bepicolombo,
    11: scene_bitcoin,
    12: scene_vegas_pole,
    13: scene_rahul,
}


def draw_scene(sid, w, h, out_scale=2, supersample=4):
    p = Pen(w, h, out_scale * supersample)
    SCENES[sid](p)
    return p.render(round(w * out_scale), round(h * out_scale))
