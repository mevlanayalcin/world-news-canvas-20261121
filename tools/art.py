"""Original silkscreen-editorial illustrations, keyed by subject rather than page position.

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


# ------------------------------------------------------------------ scenes
def scene_cop31(p):
    """Antalya: oil derrick, turbines and a draft still awaiting adoption."""
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

    # An unsigned draft, not a gavel implying adoption.
    x, y = w * 0.64, 9
    for offset in (5, 2.5, 0):
        p.rect(x + offset, y + offset, x + 48 + offset, y + 48 + offset, "#FFF8E7", "#9F866D", 0.8)
    p.rect(x + 4, y + 5, x + 44, y + 19, "#204859")
    p.text(x + 24, y + 12.4, "DRAFT", 9.0, "#FFFAE8")
    for row, length in enumerate((33, 26, 37, 20)):
        yy = y + 24 + row * 4
        p.line([(x + 5, yy), (x + 5 + length, yy)], "#A2917C", 0.9)
    p.line([(x + 21, y + 44), (x + 41, y + 41)], "#AF392F", 1.5)


def scene_peru_hero(p):
    """Central Peru: Andean houses above an illustrative seismograph."""
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


def scene_tanker(p):
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

    # A nautical compass, not an illustration assigning blame for the hits.
    cx, cy = w * .84, h * .34
    p.circle(cx, cy, 14, "#F8F0DF", "#756855", .8)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        p.line([(cx + 11 * math.sin(a), cy + 11 * math.cos(a)),
                (cx + 13 * math.sin(a), cy + 13 * math.cos(a))], "#766F66", .8)
    p.poly([(cx - 3, cy + 1), (cx + 4, cy - 10), (cx + 3, cy + 1)], "#A33131")
    p.poly([(cx + 3, cy), (cx - 4, cy + 10), (cx - 3, cy)], "#244A5C")


def scene_bepicolombo(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#070D21", "#162447")
    stars(p, 90, 21)
    # Warm solar rim glow from bottom-left
    p.glow(-8, h * 0.85, 58, "#FFE299", 145, steps=18)

    # Sculpted cratered Mercury crescent on right half (100% clear of upper-left banner + white sub-tag!)
    mx, my, mr = w * 0.835, h * 0.51, h * 0.44
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
    for _ in range(66):
        a, rr = rnd.uniform(0, 6.283), mr * math.sqrt(rnd.next()) * 0.88
        cx, cy = mx + math.cos(a) * rr, my + math.sin(a) * rr
        if cy > h + 3 or cx > w + 3:
            continue
        cr = rnd.uniform(1.1, 4.2)
        is_lit = cx < mx - mr * 0.08
        p.ellipse(cx, cy, cr, cr * 0.85, rgb("#7B746A" if is_lit else "#3E3A36", 225))
        p.arc(cx, cy, cr, 200, 340, rgb("#DAD2C5" if is_lit else "#68625B", 215), 0.5)
    p.circle(mx, my, mr, None, rgb("#D8D0C2", 140), 0.9)

    # Show the approach, not a closed orbit that telemetry has not established.
    for i in range(24):
        t, u = i / 24, (i + .58) / 24
        p.line([(w * (.04 + .64 * v), h * (.91 - .46 * v * v)) for v in (t, u)],
               "#86B6CD", .9)

    # Stacked BepiColombo spacecraft (gold MPO + white Mio drum + blue solar wing + thruster glow)
    # Positioned cleanly in lower-center (x=28..108, y=46..64), 100% clear of banner + sub-tag!
    sx, sy = w * 0.49, h * 0.74
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


def scene_bahrain(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#292A41", "#CC7549")
    smoke(p, w * .69, h * .65, 24, -33, 3, 9, 18, "#32313A", 185)
    p.glow(w * .65, h * .63, 34, "#FFC87C", 190)
    flames(p, w * .65, h * .73, 22, 24)
    for x, top in ((21, 34), (29, 39), (158, 23)):
        p.poly([(x, h), (x + 1, top), (x + 4, top), (x + 6, h)], "#323242")
        p.line([(x + 1, top + 4), (x + 4, top + 4)], "#E2BE9E", 1)
    roof = [(0, h), (0, h * .70)]
    for x in range(0, int(w), 24):
        roof.extend([(x + 18, h * .59), (x + 18, h * .70)])
    p.poly(roof + [(w, h * .70), (w, h)], "#162839")
    for x in range(8, int(w), 10):
        p.rect(x, h * .77, x + 4, h * .81, "#EFC887")


def scene_ukraine(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#345470", "#D9C49E")
    for i, top in enumerate((33, 28, 38, 22, 14, 24)):
        x = i * 34 - 4
        p.rect(x, top, x + 32, h, "#394959", "#748791", .7)
        for row in range(top + 4, int(h - 9), 8):
            for col in range(4):
                p.rect(x + 4 + col * 7, row, x + 7 + col * 7, row + 4,
                       "#F6D190" if (row + i + col) % 3 else "#212B37")
    p.rect(0, h - 13, w, h, "#273143")
    x, y = w * .28, h - 17
    p.poly([(x - 20, y - 8), (x + 9, y - 8), (x + 17, y - 1), (x + 19, y + 7),
            (x - 20, y + 7)], "#F9F1DC", "#142D43", .9)
    p.rect(x - 18, y + 1, x + 16, y + 3, "#D38A35")
    p.rect(x + 5, y - 6, x + 10, y - 1, "#436474")
    p.rect(x - 7, y - 10, x + 1, y - 8, "#86E1F5")
    for dx in (-12, 11):
        p.circle(x + dx, y + 7, 3.8, "#17212B", "#85919B", .7)


def scene_kordofan(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#DDA263", "#FBE8B3")
    p.circle(w * .79, h * .34, 13, "#F8DA91")
    ridge(p, h * .62, 4, 1.4, .7, "#C29869")
    ridge(p, h * .72, 3, 1.8, .2, "#B07E4C")
    for x, y, scale in ((43, 46, .75), (63, 44, .8), (85, 47, 1), (108, 46, .78)):
        p.rect(x - 7 * scale, y, x + 7 * scale, y + 7 * scale, "#E8C189")
        p.poly([(x - 9 * scale, y), (x, y - 7 * scale), (x + 9 * scale, y)], "#795439")
        p.rect(x - 2 * scale, y + 2, x + scale, y + 7 * scale, "#5F4A39")
    x = w * .83
    p.poly([(x - 4, h), (x - 1, 39), (x - 10, 30), (x, 35), (x + 10, 23),
            (x + 4, 36), (x + 3, 48), (x + 5, h)], "#493F31")
    for dx, dy, rad in ((-12, 29, 13), (-2, 24, 16), (10, 22, 14), (19, 26, 9)):
        p.ellipse(x + dx, dy, rad, 4.2, "#514E34")


def scene_flood(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#728B99", "#DDE6D4")
    ridge(p, h * .48, 4, 1.6, 1.2, "#688576")
    waves(p, h * .55, h, "#6698A1", "#356476", n=4)
    x = w * .78
    p.rect(x, 9, x + 11, h, "#E9DCAD", "#344855", 1)
    for i in range(13):
        yy = 13 + i * 4
        p.line([(x + 1, yy), (x + (7 if i % 2 else 4), yy)], "#8F4739", 1)
    for i in range(6):
        xx = 8 + i * 21
        p.line([(xx, h * .62), (xx + 7, h * .62)], "#CCDDD4", .9)


def scene_sinaloa(p):
    # Small Gulf of California locator, with Guasave on the mainland shore.
    w, h = p.w, p.h
    p.rect(0, 0, w, h, "#C2DADD")
    def xy(lon, lat):
        return (lon + 114) * w / 8, (29 - lat) * h / 6.5
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


def scene_geneva(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#1F4656", "#142D41")
    cx, cy = w * .73, h * .52
    for i in range(7):
        yy = cy - 16 + i * 5
        for sign in (-1, 1):
            xx = cx + sign * 16
            ex = cx + sign * (29 + (i % 3) * 6)
            p.line([(xx, yy), (xx + sign * 6, yy), (ex, yy + (i - 3) * 2),
                    (ex + sign * 8, yy + (i - 3) * 2)], "#77B9B2", .8)
            p.circle(ex + sign * 8, yy + (i - 3) * 2, 1.4, "#D1B785")
    p.rect(cx - 18, cy - 17, cx + 18, cy + 18, "#D8CEAD", "#FAE3A9", 1.1, r=2)
    p.rect(cx - 14, cy - 13, cx + 14, cy + 14, "#243D4B")
    p.text(cx, cy, "AI", 14, "#F4D695")
    p.poly([(14, 40), (51, 32), (72, 37), (72, 57), (48, 54), (14, 61)], "#F4E9D1")
    p.line([(51, 33), (48, 53)], "#A89D85", 1)
    for i in range(3):
        p.line([(21, 43 + 4 * i), (43, 38 + 4 * i)], "#9C917D", .8)


def scene_football(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#BBCDD1", "#EFE4C5")
    p.poly([(0, 27), (w, 17), (w, 36), (0, 40)], "#52616A")
    for i in range(35):
        x = i * 5.8
        p.line([(x, 30 - x * .05), (x + 2, 30 - x * .05)], "#C8C6AE", 1)
    p.rect(0, 39, w, h, "#436F51")
    for i in range(4):
        p.poly([(i * 52, 39), (i * 52 + 23, 39), (i * 61 + 19, h), (i * 61 - 10, h)], "#51805C")
    p.ellipse(87, 53, 17, 6, None, "#C5D1AD", .9)
    p.line([(91, 39), (83, h)], "#DBE0BF", .9)
    p.rect(w - 64, 5, w - 5, 35, "#182735", "#DDBF78", 1)
    p.text(w - 34.5, 11.5, "NEW   ARS", 6.8, "#F2D696")
    p.text(w - 34.5, 24, "2 : 2", 13.2, "#FFFFFF")


SCENES = {
    "cop": scene_cop31, "mercury": scene_bepicolombo, "andes": scene_peru_hero,
    "bahrain": scene_bahrain, "ukraine": scene_ukraine, "kordofan": scene_kordofan,
    "tanker": scene_tanker, "flood": scene_flood, "sinaloa": scene_sinaloa,
    "geneva": scene_geneva, "football": scene_football, "vegas": scene_vegas_pole,
    "cricket": scene_rahul,
}


def draw_scene(scene, w, h, out_scale=2, supersample=4):
    p = Pen(w, h, out_scale * supersample)
    SCENES[scene](p)
    return p.render(round(w * out_scale), round(h * out_scale))
