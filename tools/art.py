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


def scene_saudi(p):
    """Four interceptions in two coalition accounts: three over Riyadh, one bound for the west."""
    w, h, g = p.w, p.h, p.base
    p.vgrad(0, h, "#0A1730", "#27436F")
    stars(p, 84, 29, y1=g * 0.86)
    p.glow(w * 0.74, g + 8, 104, "#F0B954", 78)

    # The west is open country: a bare ridge, no skyline.
    hill = [(-4, h)]
    for i in range(41):
        x = w * 0.50 * i / 40
        hill.append((x, g - 7.5 - 5.5 * math.sin(i / 40 * 3.1416) - 2.4 * math.sin(i * 0.55 + 0.6)))
    p.poly(hill + [(w * 0.50, h)], "#0E1B33")
    p.rect(0, g - 2, w, h, "#0E1B33")

    # Riyadh's skyline fills the right-hand half.
    for x, bw, bh in ((0.505, 16, 15), (0.555, 13, 23), (0.60, 15, 18), (0.715, 15, 25),
                      (0.845, 15, 28), (0.895, 16, 20), (0.948, 15, 26)):
        x *= w
        p.rect(x, g - bh, x + bw, h, "#16294A", "#3A5A8C", 0.55)
        for row in range(int(bh // 6)):
            for col in range(int(bw // 5)):
                if (row * 3 + col * 5 + int(x)) % 4:
                    p.rect(x + 2.6 + col * 4.6, g - bh + 3.2 + row * 5.6,
                           x + 4.6 + col * 4.6, g - bh + 5.6 + row * 5.6, "#F4C35A")
    kx, kh = w * 0.672, 50.0  # Kingdom Centre and its open crown
    p.poly([(kx - 10.5, h), (kx - 9, g - kh), (kx + 9, g - kh), (kx + 10.5, h)], "#1F3761", "#7C9ED1", 0.8)
    p.poly([(kx - 5.4, g - kh + 1.2), (kx + 5.4, g - kh + 1.2), (kx + 3.6, g - kh + 14),
            (kx, g - kh + 18), (kx - 3.6, g - kh + 14)], "#132748")
    p.line([(kx - 7.2, g - kh + 2), (kx + 7.2, g - kh + 2)], "#FFE59E", 1.2)
    for row in range(5):
        for dxw in (-6, -2, 2, 5):
            p.rect(kx + dxw, g - kh + 22 + row * 5.4, kx + dxw + 1.8, g - kh + 24.2 + row * 5.4, "#F9D06B")
    fx, fh = w * 0.795, 43.0  # Al Faisaliah's spire and golden orb
    p.poly([(fx - 11, h), (fx, g - fh), (fx + 11, h)], "#1B3157", "#7C9ED1", 0.8)
    p.line([(fx, g - fh), (fx, g - fh - 6.5)], "#B0CBF0", 1.0)
    p.circle(fx, g - fh + 9.5, 3.7, "#F8C846", "#FFF2B2", 0.6)
    for k in range(4):
        yy = g - 5 - k * 7
        half = 8.2 - k * 1.6
        p.line([(fx - half, yy), (fx + half, yy)], rgb("#F8D374", 190), 0.85)

    # (burst, launch point, radius): three over the capital, one apart over the western ridge.
    shots = (
        ((w * 0.585, g * 0.345), (w * 0.535, g - 16), 10.0),
        ((w * 0.745, g * 0.205), (w * 0.700, g - 26), 11.0),
        ((w * 0.905, g * 0.335), (w * 0.870, g - 29), 10.0),
        ((w * 0.335, g * 0.735), (w * 0.215, g - 11), 9.0),
    )
    for (bx, by), (lx, ly), br in shots:
        sx, sy = bx + 25, by - 43  # each warhead falls steeply, so no two trails read as one
        for k in range(0, 7, 2):
            t0, t1 = k / 7, (k + 1.2) / 7
            p.line([(sx + (bx - sx) * t0, sy + (by - sy) * t0),
                    (sx + (bx - sx) * t1, sy + (by - sy) * t1)], "#FF8A4C", 1.35)
        p.line([(lx, ly), (bx, by)], rgb("#8EE3FF", 205), 1.15)
        p.glow(bx, by, br * 1.9, "#FF9E2C", 175, steps=12)
        starburst(p, bx, by, br, br * 0.40, "#FFB338", "#FFF9D6")


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


def scene_tanker(p):
    w, h, g = p.w, p.h, p.base
    sea = g * 0.52
    p.vgrad(0, sea, "#EBC092", "#F8E7CE")
    p.poly([(0, sea - 11), (w * 0.28, sea - 7), (w * 0.58, sea - 11), (w, sea - 7),
            (w, sea + 2), (0, sea + 2)], "#B88E68")
    waves(p, sea, h, "#30829C", "#184E66", n=5, seed=15)

    tx, ty = w * 0.30, g - 12
    p.poly([(tx - 32, ty - 4), (tx + 28, ty - 4), (tx + 34, ty - 8), (tx + 26, ty + 4),
            (tx - 30, ty + 4)], "#7E2E2A")
    p.rect(tx - 30, ty - 6, tx + 25, ty - 4, "#404852")
    p.rect(tx - 30, ty - 14, tx - 20, ty - 6, "#F4F1EA")
    for k in range(3):
        p.circle(tx - 12 + k * 10, ty - 7, 2.2, "#59626E")

    # A nautical compass, not an illustration assigning blame for the hits.
    cx, cy = w * .875, g * .44
    p.circle(cx, cy, 14, "#F8F0DF", "#756855", .8)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        p.line([(cx + 11 * math.sin(a), cy + 11 * math.cos(a)),
                (cx + 13 * math.sin(a), cy + 13 * math.cos(a))], "#766F66", .8)
    p.poly([(cx - 3, cy + 1), (cx + 4, cy - 10), (cx + 3, cy + 1)], "#A33131")
    p.poly([(cx + 3, cy), (cx - 4, cy + 10), (cx - 3, cy)], "#244A5C")


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


def scene_bahrain(p):
    w, h, g = p.w, p.h, p.base
    p.vgrad(0, h, "#292A41", "#CC7549")
    smoke(p, w * .69, g * .80, 24, -33, 3, 9, 18, "#32313A", 185)
    p.glow(w * .65, g * .78, 34, "#FFC87C", 190)
    flames(p, w * .65, g * .90, 22, 24)
    for x, top in ((21, 31), (29, 36), (158, 21)):
        p.poly([(x, h), (x + 1, top), (x + 4, top), (x + 6, h)], "#323242")
        p.line([(x + 1, top + 4), (x + 4, top + 4)], "#E2BE9E", 1)
    roof = [(0, h), (0, g * .88)]
    for x in range(0, int(w), 24):
        roof.extend([(x + 18, g * .74), (x + 18, g * .88)])
    p.poly(roof + [(w, g * .88), (w, h)], "#162839")
    for x in range(8, int(w), 10):
        p.rect(x, g - 5.2, x + 4, g - 2.4, "#EFC887")


def scene_ukraine(p):
    w, h, g = p.w, p.h, p.base
    p.vgrad(0, h, "#345470", "#D9C49E")
    for i, top in enumerate((33, 28, 38, 22, 14, 24)):
        x = i * 34 - 4
        p.rect(x, top, x + 32, h, "#394959", "#748791", .7)
        for row in range(top + 4, int(g - 12), 8):
            for col in range(4):
                p.rect(x + 4 + col * 7, row, x + 7 + col * 7, row + 4,
                       "#F6D190" if (row + i + col) % 3 else "#212B37")
    p.rect(0, g - 8, w, h, "#273143")
    x, y = w * .28, g - 12
    p.poly([(x - 20, y - 8), (x + 9, y - 8), (x + 17, y - 1), (x + 19, y + 7),
            (x - 20, y + 7)], "#F9F1DC", "#142D43", .9)
    p.rect(x - 18, y + 1, x + 16, y + 3, "#D38A35")
    p.rect(x + 5, y - 6, x + 10, y - 1, "#436474")
    p.rect(x - 7, y - 10, x + 1, y - 8, "#86E1F5")
    for dx in (-12, 11):
        p.circle(x + dx, y + 7, 3.8, "#17212B", "#85919B", .7)


def scene_kordofan(p):
    w, h, g = p.w, p.h, p.base
    p.vgrad(0, h, "#DDA263", "#FBE8B3")
    p.circle(w * .79, g * .44, 13, "#F8DA91")
    ridge(p, g * .76, 4, 1.4, .7, "#C29869")
    ridge(p, g * .88, 3, 1.8, .2, "#B07E4C")
    for x, y, scale in ((43, 43, .75), (63, 41, .8), (85, 44, 1), (108, 43, .78)):
        p.rect(x - 7 * scale, y, x + 7 * scale, y + 7 * scale, "#E8C189")
        p.poly([(x - 9 * scale, y), (x, y - 7 * scale), (x + 9 * scale, y)], "#795439")
        p.rect(x - 2 * scale, y + 2, x + scale, y + 7 * scale, "#5F4A39")
    x = w * .83
    p.poly([(x - 4, h), (x - 1, 39), (x - 10, 30), (x, 35), (x + 10, 23),
            (x + 4, 36), (x + 3, 48), (x + 5, h)], "#493F31")
    for dx, dy, rad in ((-12, 29, 13), (-2, 24, 16), (10, 22, 14), (19, 26, 9)):
        p.ellipse(x + dx, dy, rad, 4.2, "#514E34")


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
    "cop": scene_cop31, "saudi": scene_saudi, "andes": scene_peru_hero,
    "bahrain": scene_bahrain, "ukraine": scene_ukraine, "kordofan": scene_kordofan,
    "tanker": scene_tanker, "flood": scene_flood, "sinaloa": scene_sinaloa,
    "mercury": scene_bepicolombo, "football": scene_football, "vegas": scene_vegas_pole,
    "cricket": scene_rahul,
}


def draw_scene(scene, w, h, out_scale=2, supersample=4, base=None):
    p = Pen(w, h, out_scale * supersample, base)
    SCENES[scene](p)
    return p.render(round(w * out_scale), round(h * out_scale))
