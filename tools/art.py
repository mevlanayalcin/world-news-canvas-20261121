"""Procedural vector illustrations, one per illustrated story (ids 1-13).

Each scene draws into a Pen whose coordinates are in 1x layout pixels; the Pen
renders at a high scale so that downsampling gives smooth anti-aliased edges.
Everything is deterministic: the only randomness is a fixed-seed LCG.
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
    """Tiny deterministic LCG so every build draws the same stars and crowds."""

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
        self.img = Image.new("RGB", (round(w * scale), round(h * scale)), (255, 255, 255))
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

    def glow(self, cx, cy, r, color, alpha=120, steps=24):
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


def waves(p, y0, y1, c_top, c_bot, crest="#FFFFFF", n=5, seed=3):
    p.vgrad(y0, y1, c_top, c_bot)
    rnd = Rand(seed)
    for row in range(n):
        y = y0 + (y1 - y0) * (row + 0.6) / n
        x = rnd.uniform(-10, 0)
        while x < p.w:
            L = rnd.uniform(6, 14) * (0.6 + row / n)
            p.line([(x, y), (x + L, y)], rgb(crest, 70 + row * 10), 0.6)
            x += L + rnd.uniform(6, 16)


def stars(p, n, seed, y1=None, color="#FFFFFF"):
    rnd = Rand(seed)
    y1 = p.h if y1 is None else y1
    for _ in range(n):
        x, y = rnd.uniform(0, p.w), rnd.uniform(0, y1)
        r = rnd.uniform(0.25, 0.8)
        p.circle(x, y, r, rgb(color, round(rnd.uniform(110, 255))))


def smoke(p, x, y, dx, dy, r0, r1, n, color, alpha=150, seed=9):
    rnd = Rand(seed)
    for i in range(n):
        t = i / max(1, n - 1)
        cx = x + dx * t + rnd.uniform(-2, 2)
        cy = y + dy * t + rnd.uniform(-1.5, 1.5)
        r = r0 + (r1 - r0) * t
        p.circle(cx, cy, r, rgb(color, round(alpha * (1 - 0.55 * t))))


def flames(p, cx, base, w, h, seed=5):
    rnd = Rand(seed)
    for layer, col in enumerate(("#C0261B", "#EE6A1F", "#FFB23F", "#FFE38A")):
        k = 1 - layer * 0.22
        pts = [(cx - w / 2 * k, base)]
        tongues = 5
        for i in range(tongues):
            x0 = cx - w / 2 * k + w * k * (i + 0.5) / tongues
            pts.append((x0 - w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
            pts.append((x0 + rnd.uniform(-1, 1), base - h * k * rnd.uniform(0.75, 1.0)))
            pts.append((x0 + w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
        pts.append((cx + w / 2 * k, base))
        p.poly(pts, col)


def seismo(p, x0, x1, y, amp, color, seed=7, width=0.9, burst=0.45):
    rnd = Rand(seed)
    pts = []
    n = 140
    for i in range(n + 1):
        t = i / n
        env = math.exp(-((t - burst) ** 2) / 0.006) + 0.06
        pts.append((x0 + (x1 - x0) * t, y + amp * env * rnd.uniform(-1, 1)))
    p.line(pts, color, width)


def pine(p, x, base, h, color):
    for k in range(3):
        top = base - h + k * h * 0.22
        wid = h * (0.22 + k * 0.1)
        p.poly([(x, top), (x - wid, top + h * 0.42), (x + wid, top + h * 0.42)], color)
    p.rect(x - h * 0.04, base - h * 0.15, x + h * 0.04, base, color)


def palm(p, x, base, h, color):
    p.line([(x, base), (x + h * 0.08, base - h * 0.5), (x + h * 0.05, base - h)], color, h * 0.06)
    tx, ty = x + h * 0.05, base - h
    for ang in (-160, -130, -100, -70, -40, -15):
        a = math.radians(ang)
        ex, ey = tx + math.cos(a) * h * 0.45, ty - math.sin(a) * h * 0.05 + h * 0.18
        mx, my = tx + math.cos(a) * h * 0.25, ty - abs(math.sin(a)) * h * 0.12
        p.line([(tx, ty), (mx, my), (ex, ey)], color, h * 0.05)


def person(p, x, base, h, color, bundle=False):
    p.circle(x, base - h * 0.88, h * 0.11, color)
    p.poly([(x - h * 0.14, base - h * 0.74), (x + h * 0.14, base - h * 0.74),
            (x + h * 0.1, base - h * 0.35), (x - h * 0.1, base - h * 0.35)], color)
    p.line([(x - h * 0.05, base - h * 0.36), (x - h * 0.1, base)], color, h * 0.09)
    p.line([(x + h * 0.05, base - h * 0.36), (x + h * 0.11, base)], color, h * 0.09)
    if bundle:
        p.ellipse(x, base - h * 1.08, h * 0.2, h * 0.1, color)


def quadcopter(p, cx, cy, s, color):
    p.line([(cx - s, cy - s * 0.5), (cx + s, cy + s * 0.5)], color, s * 0.22)
    p.line([(cx - s, cy + s * 0.5), (cx + s, cy - s * 0.5)], color, s * 0.22)
    for dx, dy in ((-s, -s * 0.5), (s, s * 0.5), (-s, s * 0.5), (s, -s * 0.5)):
        p.ellipse(cx + dx, cy + dy, s * 0.55, s * 0.16, color)
    p.ellipse(cx, cy, s * 0.35, s * 0.25, color)


def delta_drone(p, cx, cy, s, color, tilt=0.0):
    ca, sa = math.cos(tilt), math.sin(tilt)

    def r(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    p.poly([r(s, 0), r(-s * 0.6, -s * 0.75), r(-s * 0.3, 0), r(-s * 0.6, s * 0.75)], color)


# ------------------------------------------------------------------ scenes
def scene_cop31(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.72, "#F6C58F", "#FBEBD3")
    p.glow(w * 0.5, h * 0.62, h * 0.7, "#FFE2A8", 150)
    ridge(p, h * 0.58, h * 0.1, 1.6, 0.7, "#C9A58A", y_floor=h * 0.75)
    ridge(p, h * 0.66, h * 0.07, 2.4, 2.0, "#A7836E", y_floor=h * 0.75)
    waves(p, h * 0.72, h, "#4E8FB8", "#24577E", n=4)
    # oil derrick (left) and wind turbines (right): the two sides of the fight
    dx, base = w * 0.12, h * 0.78
    p.poly([(dx - 15, base), (dx - 3, base - 62), (dx + 3, base - 62), (dx + 15, base)],
           None, "#3B2F2A", 1.6)
    for k in range(1, 5):
        y = base - k * 13
        half = 15 - k * 2.9
        p.line([(dx - half, y), (dx + half, y)], "#3B2F2A", 1.2)
        p.line([(dx - half - 2.9, y + 13), (dx + half, y)], "#3B2F2A", 0.8)
    p.rect(dx + 8, base - 34, dx + 38, base - 29, "#3B2F2A")
    p.poly([(dx + 36, base - 40), (dx + 46, base - 31), (dx + 36, base - 22)], "#3B2F2A")
    p.rect(dx - 30, base - 10, dx - 16, base, "#2C2420", r=1.5)
    p.rect(dx - 30, base - 7, dx - 16, base - 5.5, "#E0B040")
    for tx, th, ang in ((w * 0.86, 68, 12), (w * 0.95, 50, 47), (w * 0.77, 44, 80)):
        top = base - th
        p.poly([(tx - 1.6, base), (tx - 0.7, top), (tx + 0.7, top), (tx + 1.6, base)], "#F4F4F2")
        for k in range(3):
            a = math.radians(ang + k * 120)
            p.poly([(tx, top), (tx + math.cos(a) * th * 0.48 - math.sin(a) * 2.2,
                                top + math.sin(a) * th * 0.48 + math.cos(a) * 2.2),
                    (tx + math.cos(a) * th * 0.5, top + math.sin(a) * th * 0.5)], "#FFFFFF",
                   "#B9C2C8", 0.4)
        p.circle(tx, top, 1.8, "#D8DDE0")
    # plenary hall with a row of flags
    hx0, hx1, hy = w * 0.31, w * 0.69, h * 0.78
    p.rect(hx0, hy - 20, hx1, hy, "#EDE6DA", "#8C7B6B", 0.6)
    p.poly([(hx0 - 6, hy - 20), (w * 0.5, hy - 34), (hx1 + 6, hy - 20)], "#D9CDBB", "#8C7B6B", 0.6)
    for i in range(9):
        x = hx0 + 6 + i * (hx1 - hx0 - 12) / 8
        p.rect(x - 2.4, hy - 15, x + 2.4, hy, "#B9AA98")
    flag_cols = ["#C8102E", "#003399", "#009739", "#FFCD00", "#0033A0", "#E30A17", "#00843D",
                 "#002B7F", "#F7A600", "#D52B1E", "#008751"]
    for i, c in enumerate(flag_cols):
        x = hx0 - 4 + i * (hx1 - hx0 + 8) / (len(flag_cols) - 1)
        p.line([(x, hy), (x, hy - 31)], "#5A4D42", 0.6)
        p.rect(x, hy - 31, x + 7, hy - 26.5, c)
    # overtime clock
    cx, cy, r = w * 0.5, h * 0.3, h * 0.22
    p.circle(cx + 1.2, cy + 1.6, r + 2, (60, 40, 20, 60))
    p.circle(cx, cy, r + 2.4, "#14181F")
    p.circle(cx, cy, r, "#FFFDF8")
    p.d.pieslice([(cx - r) * p.s, (cy - r) * p.s, (cx + r) * p.s, (cy + r) * p.s], -90, -10,
                 fill=rgb("#D7262E", 190))
    for k in range(12):
        a = math.radians(k * 30 - 90)
        r0 = r * (0.78 if k % 3 == 0 else 0.86)
        p.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95)], "#14181F",
               1.4 if k % 3 == 0 else 0.7)
    a_min, a_hr = math.radians(-10), math.radians(-90 + 8)
    p.line([(cx, cy), (cx + math.cos(a_hr) * r * 0.5, cy + math.sin(a_hr) * r * 0.5)], "#14181F", 2.2)
    p.line([(cx, cy), (cx + math.cos(a_min) * r * 0.82, cy + math.sin(a_min) * r * 0.82)],
           "#14181F", 1.4)
    p.circle(cx, cy, 1.8, "#D7262E")
    p.text(cx + r + 14, cy - r * 0.35, "+1", 15, "#D7262E", anchor="lm")
    p.text(cx + r + 14, cy + r * 0.25, "DAY", 8, "#D7262E", anchor="lm")


def scene_bepi(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#05081A", "#121A3A")
    stars(p, 140, 21)
    p.glow(-h * 0.1, h * 0.3, h * 1.1, "#FFE9B0", 240, 40)
    p.circle(-h * 0.25, h * 0.3, h * 0.42, "#FFF6DA")
    # Mercury
    mx, my, mr = w * 0.76, h * 0.7, h * 0.62
    # night side first, then the sunlit part = sphere ∩ an ellipse shifted toward the Sun
    p.circle(mx, my, mr, "#4F4A45")
    sphere = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(sphere).ellipse([(mx - mr) * p.s, (my - mr) * p.s, (mx + mr) * p.s, (my + mr) * p.s],
                                   fill=255)
    lit = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(lit).ellipse([(mx - mr * 1.25) * p.s, (my - mr * 1.05) * p.s,
                                 (mx + mr * 0.45) * p.s, (my + mr * 1.05) * p.s], fill=255)
    from PIL import ImageChops
    p.img.paste(Image.new("RGB", p.img.size, (160, 153, 143)), (0, 0), ImageChops.multiply(sphere, lit))
    p.d = ImageDraw.Draw(p.img, "RGBA")
    rnd = Rand(44)
    for _ in range(36):
        a, rr = rnd.uniform(0, 6.283), mr * math.sqrt(rnd.next()) * 0.92
        x, y = mx + math.cos(a) * rr, my + math.sin(a) * rr
        if y > h + 4:
            continue
        cr = rnd.uniform(1.2, 6.5)
        lit = x < mx - mr * 0.05
        p.ellipse(x, y, cr, cr * 0.85, rgb("#6E6860" if lit else "#45413C", 230))
        p.arc(x, y, cr, 200, 340, rgb("#C7C0B5" if lit else "#6A645D", 220), 0.5)
    p.circle(mx, my, mr, None, rgb("#C9C2B6", 120), 0.8)
    # orbit ellipse (dashed)
    for k in range(48):
        if k % 2:
            continue
        a0, a1 = k / 48 * 6.283, (k + 1) / 48 * 6.283
        pts = [(mx + math.cos(a) * mr * 1.35, my - mr * 0.25 + math.sin(a) * mr * 0.5)
               for a in (a0, (a0 + a1) / 2, a1)]
        if all(math.hypot(x - mx, y - my) > mr * 0.98 or y < my - mr * 0.3 for x, y in pts):
            p.line(pts, rgb("#7FD1FF", 200), 0.8)
    # spacecraft stack: gold MPO body, white Mio drum, long blue solar wing
    sx, sy = w * 0.34, h * 0.38
    p.line([(sx + 10, sy), (sx + 30, sy - 1)], rgb("#9ED8FF", 160), 3.2)
    p.glow(sx + 16, sy, 9, "#9ED8FF", 200)
    p.rect(sx - 88, sy - 5.5, sx - 14, sy + 5.5, "#24407A", "#9FB4D8", 0.5)
    for k in range(1, 8):
        x = sx - 88 + k * 74 / 8
        p.line([(x, sy - 5.5), (x, sy + 5.5)], rgb("#9FB4D8", 160), 0.4)
    p.line([(sx - 88, sy), (sx - 14, sy)], rgb("#9FB4D8", 160), 0.4)
    p.rect(sx - 14, sy - 1, sx - 9, sy + 1, "#B0B0B0")
    p.rect(sx - 9, sy - 9, sx + 9, sy + 9, "#D9A441", "#8A6420", 0.6)
    p.line([(sx - 9, sy - 3), (sx + 9, sy - 3)], rgb("#8A6420", 180), 0.4)
    p.line([(sx - 9, sy + 3), (sx + 9, sy + 3)], rgb("#8A6420", 180), 0.4)
    p.poly([(sx - 6, sy - 9), (sx + 6, sy - 9), (sx + 4, sy - 17), (sx - 4, sy - 17)], "#EDEDED",
           "#9A9A9A", 0.4)
    p.ellipse(sx, sy - 17, 4, 1.4, "#FFFFFF")
    p.line([(sx + 9, sy - 6), (sx + 15, sy - 12)], "#CFCFCF", 0.6)
    p.ellipse(sx + 16, sy - 13, 3.4, 1.4, "#E8E8E8")


def scene_mexico(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.75, "#3B2C5C", "#F08A4B")
    p.glow(w * 0.6, h * 0.78, h * 0.6, "#FFC46B", 170)
    ridge(p, h * 0.66, h * 0.12, 1.3, 1.1, "#7A4A4F")
    ridge(p, h * 0.78, h * 0.06, 2.1, 0.3, "#4A2E35")
    p.rect(0, h * 0.84, w, h, "#2C1C22")
    for cx, ch in ((w * 0.93, 30), (w * 0.86, 18)):
        b = h * 0.86
        p.line([(cx, b), (cx, b - ch)], "#1E1418", 4.2)
        p.line([(cx - 7, b - ch * 0.45), (cx - 7, b - ch * 0.72)], "#1E1418", 3)
        p.line([(cx - 7, b - ch * 0.45), (cx, b - ch * 0.45)], "#1E1418", 3)
        p.line([(cx + 7, b - ch * 0.55), (cx + 7, b - ch * 0.85)], "#1E1418", 3)
        p.line([(cx + 7, b - ch * 0.55), (cx, b - ch * 0.55)], "#1E1418", 3)
    # army truck
    tx, ty = w * 0.62, h * 0.86
    p.rect(tx - 34, ty - 20, tx + 6, ty - 4, "#3E4A2F", r=1.5)
    p.rect(tx + 6, ty - 16, tx + 20, ty - 4, "#4A5838", r=2)
    p.rect(tx + 9, ty - 14, tx + 17, ty - 9, "#F3C27A")
    for wx in (tx - 24, tx - 8, tx + 13):
        p.circle(wx, ty - 3, 4.4, "#141012")
        p.circle(wx, ty - 3, 1.6, "#6B6B6B")
    for k, sx in enumerate((tx - 46, tx - 54, tx + 30)):
        person(p, sx, ty, 15 + (k % 2), "#1E1418")
        p.line([(sx + 2, ty - 10), (sx + 8, ty - 13)], "#1E1418", 1.0)
    # helicopter
    hx, hy = w * 0.73, h * 0.26
    p.ellipse(hx, hy, 18, 7.5, "#1F2420")
    p.poly([(hx + 12, hy - 3), (hx + 46, hy - 2), (hx + 46, hy + 0.5), (hx + 12, hy + 3)], "#1F2420")
    p.poly([(hx + 44, hy - 8), (hx + 48, hy - 8), (hx + 47, hy + 1), (hx + 43, hy + 1)], "#1F2420")
    p.ellipse(hx - 9, hy - 1.5, 6, 3.6, rgb("#F7C987", 230))
    p.line([(hx - 34, hy - 10.5), (hx + 30, hy - 9)], "#1F2420", 1.0)
    p.line([(hx, hy - 7), (hx, hy - 10)], "#1F2420", 1.4)
    p.line([(hx - 10, hy + 8.5), (hx + 10, hy + 8.5)], "#1F2420", 1.0)
    p.d.polygon(p._pts([(hx - 12, hy + 8), (hx - 50, h * 0.86), (hx + 10, h * 0.86), (hx + 2, hy + 8)]),
                fill=rgb("#FFF2C9", 55))
    # wanted poster with CAPTURED band
    px0, py0, px1, py1 = w * 0.08, h * 0.16, w * 0.3, h * 0.86
    p.rect(px0 + 1.5, py0 + 2, px1 + 1.5, py1 + 2, (0, 0, 0, 70))
    p.rect(px0, py0, px1, py1, "#F3E7CC", "#8C7650", 0.6)
    p.text((px0 + px1) / 2, py0 + 10, "WANTED", 10.5, "#3A2A1A")
    p.text((px0 + px1) / 2, py0 + 21, "FBI TOP TEN", 5.6, "#3A2A1A", F_SANS_BOLD)
    cx = (px0 + px1) / 2
    p.circle(cx, py0 + 44, 11, "#5A4A3A")
    p.ellipse(cx, py0 + 74, 24, 18, "#5A4A3A")
    p.rect(px0, py0 + 82, px1, py1, "#F3E7CC")
    p.text(cx, py0 + 90, "REWARD", 6, "#3A2A1A", F_SANS_BOLD)
    band = [(px0 - 6, py0 + 62), (px1 + 6, py0 + 44), (px1 + 6, py0 + 58), (px0 - 6, py0 + 76)]
    p.poly(band, rgb("#C8102E", 235))
    ang = math.degrees(math.atan2(18, px1 - px0 + 12))  # band rises to the right: rotate CCW
    f = ImageFont.truetype(F_SANS_BLACK, round(9.5 * p.s))
    tmp = Image.new("RGBA", (round(90 * p.s), round(16 * p.s)), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((tmp.width / 2, tmp.height / 2), "CAPTURED", font=f, fill=(255, 255, 255, 255),
                             anchor="mm")
    tmp = tmp.rotate(ang, resample=Image.BICUBIC, expand=True)
    p.img.paste(tmp, (round(cx * p.s - tmp.width / 2), round((py0 + 60) * p.s - tmp.height / 2)), tmp)


def scene_finland(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.62, "#8E9BA8", "#D5DBE0")
    for k, x in enumerate(range(int(w * 0.66), int(w) + 8, 5)):
        pine(p, x, h * 0.63, 7 + (k * 37 % 5), "#3E5246")
    p.rect(w * 0.64, h * 0.62, w, h * 0.64, "#3E5246")
    waves(p, h * 0.63, h, "#5F7E92", "#2D485C", n=4, seed=8)
    # cargo ship
    bx, by = w * 0.34, h * 0.8
    p.poly([(bx - 50, by - 9), (bx + 46, by - 9), (bx + 54, by - 15), (bx + 40, by + 4), (bx - 46, by + 4)],
           "#2B2F36")
    p.rect(bx - 50, by - 9, bx + 46, by - 6.5, "#8E2B25")
    cols = ["#2F6E9E", "#C2571A", "#5B8C3A", "#A8323A", "#2F6E9E", "#D9A441"]
    for i, c in enumerate(cols):
        x = bx - 30 + i * 11
        p.rect(x, by - 18, x + 10, by - 9.5, c)
        if i % 2 == 0:
            p.rect(x, by - 26, x + 10, by - 18.5, cols[(i + 3) % 6])
    p.rect(bx - 48, by - 26, bx - 33, by - 9, "#EEECE6")
    p.rect(bx - 46, by - 31, bx - 36, by - 26, "#EEECE6")
    for k in range(3):
        p.rect(bx - 46 + k * 4, by - 23, bx - 44 + k * 4, by - 21, "#2B2F36")
    smoke(p, bx - 40, by - 32, 70, -40, 4, 16, 16, "#3A3A3E", 170, seed=4)
    flames(p, bx - 40, by - 24, 18, 18, seed=6)
    p.glow(bx - 40, by - 20, 26, "#FF9A3C", 150)
    # two delta drones diving in
    delta_drone(p, w * 0.82, h * 0.18, 7, "#1B1F25", tilt=2.6)
    delta_drone(p, w * 0.68, h * 0.12, 6, "#1B1F25", tilt=2.7)
    p.line([(w * 0.86, h * 0.13), (w * 0.95, h * 0.05)], rgb("#FFFFFF", 150), 0.6)
    p.line([(w * 0.715, h * 0.08), (w * 0.79, h * 0.02)], rgb("#FFFFFF", 150), 0.6)


def scene_kryvyi(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#BFD3E6", "#F2E3C9")
    rnd = Rand(17)
    x = -4
    blocks = []
    while x < w:
        bw = rnd.uniform(14, 24)
        bh = rnd.uniform(h * 0.28, h * 0.6)
        blocks.append((x, bw, bh))
        x += bw + rnd.uniform(1, 4)
    for i, (x, bw, bh) in enumerate(blocks):
        top = h - bh
        col = "#6F7782" if i % 2 else "#7E8691"
        p.rect(x, top, x + bw, h, col)
        for yy in range(int(top + 3), int(h - 2), 4):
            for xx in range(int(x + 2), int(x + bw - 2), 4):
                lit = rnd.next() > 0.7
                p.rect(xx, yy, xx + 2, yy + 2, "#F6D78B" if lit else "#4F5660")
    hit = blocks[len(blocks) // 2]
    hx, hy = hit[0] + hit[1] / 2, h - hit[2]
    smoke(p, hx, hy, -30, -hy + 2, 6, 20, 16, "#3B3D42", 190, seed=31)
    flames(p, hx, hy + 6, 16, 12, seed=2)
    p.glow(hx, hy + 4, 24, "#FF8A3C", 160)
    p.line([(w * 0.96, h * 0.02), (w * 0.82, h * 0.25)], rgb("#FFFFFF", 210), 1.6)
    p.poly([(w * 0.82, h * 0.25), (w * 0.835, h * 0.205), (w * 0.81, h * 0.215)], "#C0261B")


def scene_robots(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#3E7CC0", "#1C4E86")
    for k in range(7):
        x = w * 0.08 + k * 11
        p.rect(x, h * 0.4, x + 5, h, rgb("#FFFFFF", 30))
    p.poly([(w * 0.04, h * 0.4), (w * 0.47, h * 0.4), (w * 0.255, h * 0.22)], rgb("#FFFFFF", 30))
    # robot bust
    rx, ry = w * 0.5, h * 0.55
    p.rect(rx - 16, ry - 22, rx + 16, ry + 2, "#D5DCE4", "#6C7A89", 0.6, r=4)
    p.rect(rx - 12, ry - 15, rx + 12, ry - 8, "#1B2330", r=2)
    p.rect(rx - 9, ry - 13, rx + 9, ry - 10, "#FF4D3D", r=1)
    p.line([(rx, ry - 22), (rx, ry - 29)], "#6C7A89", 1)
    p.circle(rx, ry - 30, 2, "#FF4D3D")
    p.rect(rx - 26, ry + 4, rx + 26, h + 2, "#AEB8C4", "#6C7A89", 0.6, r=5)
    p.rect(rx - 6, ry + 1, rx + 6, ry + 5, "#6C7A89")
    quadcopter(p, w * 0.2, h * 0.3, 6, "#E8EEF4")
    # calendar page showing 2028
    cx0, cy0 = w * 0.72, h * 0.18
    p.rect(cx0 + 1.5, cy0 + 2, cx0 + 41.5, cy0 + 48, (0, 0, 0, 60))
    p.rect(cx0, cy0, cx0 + 40, cy0 + 46, "#FFFFFF", r=2)
    p.rect(cx0, cy0, cx0 + 40, cy0 + 12, "#D7262E", r=2)
    p.rect(cx0, cy0 + 8, cx0 + 40, cy0 + 12, "#D7262E")
    p.text(cx0 + 20, cy0 + 6.2, "TARGET", 5.2, "#FFFFFF")
    p.text(cx0 + 20, cy0 + 29, "2028", 12.5, "#14181F")
    for k in (8, 32):
        p.circle(cx0 + k, cy0, 1.6, "#55606C")


def scene_peru(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.7, "#9CC4E4", "#E9F1F6")
    peaks = [(-10, 0.95), (w * 0.18, 0.18), (w * 0.33, 0.55), (w * 0.5, 0.1), (w * 0.68, 0.5),
             (w * 0.84, 0.22), (w + 10, 0.8)]
    pts = [(-10, h)] + [(x, h * y) for x, y in peaks] + [(w + 10, h)]
    p.poly(pts, "#7A6A5C")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2:
            px, py = x1, h * y1
            p.poly([(px, py), (px - 10, py + 12), (px - 4, py + 9), (px, py + 14), (px + 5, py + 9),
                    (px + 11, py + 12)], "#FFFFFF")
    ridge(p, h * 0.82, h * 0.05, 2.0, 0.4, "#5E7A3A")
    for k, x in enumerate((w * 0.2, w * 0.27, w * 0.74)):
        b = h * 0.86
        p.rect(x, b - 7, x + 9, b, "#E9D9BF")
        p.poly([(x - 1.5, b - 7), (x + 4.5, b - 12), (x + 10.5, b - 7)], "#B5523B")
    p.rect(0, h * 0.86, w, h, "#FFFDF8")
    p.line([(0, h * 0.86), (w, h * 0.86)], "#C9BFAE", 0.5)
    for k in range(1, 12):
        p.line([(w * k / 12, h * 0.87), (w * k / 12, h)], "#EFE7DA", 0.4)
    seismo(p, 4, w - 4, h * 0.93, h * 0.08, "#D7262E", seed=12, width=0.9, burst=0.5)


def scene_timor(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#5FA8D3", "#2F79A8")
    for k in range(1, 6):
        p.line([(0, h * k / 6), (w, h * k / 6)], rgb("#FFFFFF", 40), 0.4)
        p.line([(w * k / 6, 0), (w * k / 6, h)], rgb("#FFFFFF", 40), 0.4)
    island = [(w * 0.05, h * 0.86), (w * 0.2, h * 0.68), (w * 0.4, h * 0.6), (w * 0.58, h * 0.55),
              (w * 0.7, h * 0.56), (w * 0.66, h * 0.66), (w * 0.5, h * 0.72), (w * 0.3, h * 0.85),
              (w * 0.12, h * 0.95)]
    p.poly(island, "#8FB36A", "#6D8F4D", 0.6)
    p.poly([(w * 0.24, h * 0.75), (w * 0.38, h * 0.66), (w * 0.5, h * 0.64), (w * 0.45, h * 0.7)],
           "#77985A")
    p.poly([(w * 0.62, h * 1.05), (w * 0.8, h * 0.88), (w * 1.05, h * 0.84), (w * 1.05, h * 1.05)],
           "#D7C08A", "#B79E66", 0.6)
    ex, ey = w * 0.82, h * 0.3
    for k, rr in enumerate((40, 30, 21, 13)):
        p.circle(ex, ey, rr, rgb("#FFFFFF", 25 + k * 12), rgb("#FFFFFF", 150), 0.6)
    star = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = 6 if k % 2 == 0 else 2.6
        star.append((ex + math.cos(a) * r, ey + math.sin(a) * r))
    p.poly(star, "#D7262E", "#FFFFFF", 0.5)
    p.circle(w * 0.67, h * 0.58, 1.6, "#14181F")
    p.line([(w * 0.67, h * 0.58), (ex - 5, ey + 4)], rgb("#14181F", 150), 0.5)


def scene_basra(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.8, "#2B2340", "#B4553A")
    smoke(p, w * 0.42, h * 0.45, 40, -h * 0.5, 8, 26, 18, "#1A1618", 210, seed=13)
    p.rect(w * 0.22, h * 0.48, w * 0.62, h * 0.84, "#4A4048")
    for k in range(6):
        x = w * 0.25 + k * w * 0.06
        p.rect(x, h * 0.56, x + w * 0.03, h * 0.62, "#F5B65A")
    for k, x in enumerate((w * 0.3, w * 0.38, w * 0.54)):
        top = h * (0.12 + 0.06 * k)
        p.poly([(x - 3, h * 0.48), (x - 2, top), (x + 2, top), (x + 3, h * 0.48)], "#5A5058")
        p.rect(x - 2.4, top + 4, x + 2.4, top + 6, "#C0392B")
    flames(p, w * 0.46, h * 0.5, 30, 28, seed=19)
    p.glow(w * 0.46, h * 0.44, 36, "#FF8A3C", 170)
    tx = w * 0.78
    p.line([(tx - 9, h * 0.84), (tx, h * 0.2), (tx + 9, h * 0.84)], "#2B2328", 1.0)
    p.line([(tx - 12, h * 0.32), (tx + 12, h * 0.32)], "#2B2328", 1.0)
    p.line([(tx - 9, h * 0.45), (tx + 9, h * 0.45)], "#2B2328", 0.8)
    p.line([(tx - 6, h * 0.6), (tx + 6, h * 0.45)], "#2B2328", 0.6)
    p.line([(tx + 12, h * 0.32), (w + 2, h * 0.38)], "#2B2328", 0.4)
    p.rect(0, h * 0.84, w, h, "#1E1A1E")
    palm(p, w * 0.08, h * 0.86, 30, "#1A1517")
    palm(p, w * 0.15, h * 0.88, 22, "#1A1517")
    palm(p, w * 0.92, h * 0.88, 26, "#1A1517")


def scene_manipur(p):
    w, h = p.w, p.h
    p.vgrad(0, h, "#DCEBE3", "#F7F4EC")
    ridge(p, h * 0.5, h * 0.12, 1.2, 0.2, "#9DBFA5", y_floor=h * 0.7)
    ridge(p, h * 0.6, h * 0.08, 1.9, 1.4, "#7FA588", y_floor=h * 0.72)
    p.rect(0, h * 0.7, w, h, "#EAE4D6")
    # hospital
    hx0, hx1 = w * 0.52, w * 0.95
    p.rect(hx0, h * 0.28, hx1, h * 0.78, "#FFFFFF", "#9AA3A8", 0.6)
    for r in range(3):
        for c in range(5):
            x = hx0 + 6 + c * (hx1 - hx0 - 10) / 5
            y = h * 0.4 + r * 9
            p.rect(x, y, x + 6, y + 5, "#9CC3DA")
    p.rect(hx0 + 26, h * 0.12, hx0 + 52, h * 0.3, "#FFFFFF", "#9AA3A8", 0.6)
    cx, cy = hx0 + 39, h * 0.21
    p.rect(cx - 7, cy - 2.4, cx + 7, cy + 2.4, "#D7262E")
    p.rect(cx - 2.4, cy - 7, cx + 2.4, cy + 7, "#D7262E")
    # spurious-liquor bottles with a warning sign
    for k, (bx, tint) in enumerate(((w * 0.1, "#B48A3C"), (w * 0.18, "#8C6B2E"), (w * 0.26, "#A07A35"))):
        base = h * 0.92
        p.rect(bx - 5.5, base - 24, bx + 5.5, base, tint, r=2)
        p.rect(bx - 2, base - 33, bx + 2, base - 23, tint)
        p.rect(bx - 2.4, base - 35, bx + 2.4, base - 32, "#3A2A1A")
        p.rect(bx - 4.5, base - 17, bx + 4.5, base - 9, "#F4EBD6")
    tx, ty = w * 0.4, h * 0.6
    p.poly([(tx, ty - 14), (tx - 14, ty + 10), (tx + 14, ty + 10)], "#FFD23F", "#14181F", 1.0)
    p.rect(tx - 1.2, ty - 6, tx + 1.2, ty + 3, "#14181F")
    p.circle(tx, ty + 6.2, 1.3, "#14181F")


def scene_ethiopia(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.7, "#F3D9A8", "#F8EEDC")
    ridge(p, h * 0.48, h * 0.1, 1.1, 2.2, "#B9A27E", y_floor=h * 0.7)
    p.rect(0, h * 0.62, w, h, "#D9BE8F")
    ax, ay = w * 0.84, h * 0.6
    p.line([(ax, ay + 10), (ax + 1, ay - 12)], "#4A3A2A", 1.8)
    p.ellipse(ax, ay - 16, 20, 5, "#5D7A3A")
    p.ellipse(ax + 6, ay - 20, 12, 3.4, "#6E8C46")
    for r, y in enumerate((h * 0.66, h * 0.8)):
        for k in range(7):
            x = w * 0.05 + k * w * 0.1 + (6 if r else 0)
            s = 7 + r * 2.5
            p.poly([(x - s, y + s * 0.4), (x, y - s * 0.75), (x + s, y + s * 0.4)], "#F7F7F4", "#9C9584", 0.4)
            p.poly([(x - 1.6, y + s * 0.4), (x, y - s * 0.1), (x + 1.6, y + s * 0.4)], "#6B6455")
    for k, x in enumerate((w * 0.55, w * 0.62, w * 0.68, w * 0.75)):
        person(p, x, h * 0.98, 14 - (k % 2) * 2, "#3F3328", bundle=(k % 2 == 0))


def scene_mcg(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.5, "#0C1B33", "#26406A")
    for x in (w * 0.07, w * 0.93):
        p.line([(x, h * 0.55), (x, h * 0.1)], "#9AA5B4", 1.2)
        p.rect(x - 6, h * 0.05, x + 6, h * 0.12, "#FFF8D8")
        p.glow(x, h * 0.09, 30, "#FFF2B0", 140)
    p.ellipse(w * 0.5, h * 0.62, w * 0.62, h * 0.46, "#3B3F4C")
    rnd = Rand(77)
    for _ in range(420):
        a = rnd.uniform(3.2, 6.25)
        rr = rnd.uniform(0.8, 1.0)
        x = w * 0.5 + math.cos(a) * w * 0.6 * rr
        y = h * 0.62 + math.sin(a) * h * 0.44 * rr
        p.circle(x, y, 0.55, rgb(["#E0C341", "#FFFFFF", "#1B3A8C", "#D7262E", "#8FA0B8"][int(rnd.next() * 5)], 200))
    p.ellipse(w * 0.5, h * 0.7, w * 0.46, h * 0.3, "#2F8F3E")
    for k in range(6):
        p.ellipse(w * 0.5, h * 0.7, w * 0.46 * (1 - k * 0.15), h * 0.3 * (1 - k * 0.15), None,
                  rgb("#3CA34C", 120), 1.6)
    p.rect(w * 0.5 - 4, h * 0.58, w * 0.5 + 4, h * 0.84, "#D9C79A")
    for y in (h * 0.6, h * 0.82):
        for dx in (-1.6, 0, 1.6):
            p.line([(w * 0.5 + dx, y), (w * 0.5 + dx, y - 5)], "#FFFFFF", 0.5)
    p.circle(w * 0.72, h * 0.38, 3.2, "#C8102E")
    p.arc(w * 0.72, h * 0.38, 2.2, 100, 260, "#FFFFFF", 0.4)
    for k in range(5):
        p.circle(w * 0.6 - k * 4.5, h * 0.52 + k * 2.6, 1.2 - k * 0.18, rgb("#FFFFFF", 150 - k * 25))
    p.rect(w * 0.79, h * 0.12, w * 0.97, h * 0.3, "#111111", "#E0C341", 0.5)
    p.text(w * 0.88, h * 0.21, "188", 7.5, "#FFD23F")


def scene_hormuz(p):
    w, h = p.w, p.h
    p.vgrad(0, h * 0.45, "#E9B98A", "#F6E2C6")
    p.poly([(0, h * 0.2), (w * 0.3, h * 0.28), (w * 0.6, h * 0.22), (w, h * 0.3), (w, h * 0.45), (0, h * 0.45)],
           "#B08967")
    waves(p, h * 0.45, h, "#3D8BA6", "#1E5670", n=4, seed=15)
    p.poly([(w * 0.55, h), (w * 0.62, h * 0.8), (w * 0.72, h * 0.74), (w * 0.82, h * 0.82), (w, h * 0.78),
            (w, h)], "#A07E5E")
    tx, ty = w * 0.3, h * 0.72
    p.poly([(tx - 32, ty - 5), (tx + 30, ty - 5), (tx + 36, ty - 9), (tx + 28, ty + 4), (tx - 30, ty + 4)],
           "#7A2E2A")
    p.rect(tx - 30, ty - 6.5, tx + 26, ty - 5, "#4A4F58")
    p.rect(tx - 30, ty - 15, tx - 20, ty - 6.5, "#EEECE6")
    for k in range(4):
        p.circle(tx - 12 + k * 9, ty - 7.5, 2.2, "#5A606A")
    smoke(p, w * 0.73, h * 0.18, -28, 30, 1.2, 3.2, 10, "#4A4A4E", 150, seed=25)
    delta_drone(p, w * 0.62, h * 0.4, 7, "#22262C", tilt=2.2)
    flames(p, w * 0.62, h * 0.43, 8, 7, seed=40)
    p.glow(w * 0.62, h * 0.4, 12, "#FFB23F", 140)
    delta_drone(p, w * 0.86, h * 0.14, 5, "#22262C", tilt=0.25)


SCENES = {1: scene_cop31, 2: scene_bepi, 3: scene_mexico, 4: scene_finland, 5: scene_kryvyi,
          6: scene_robots, 7: scene_peru, 8: scene_timor, 9: scene_basra, 10: scene_manipur,
          11: scene_ethiopia, 12: scene_mcg, 13: scene_hormuz}


def draw_scene(sid, w, h, out_scale=2, supersample=4):
    p = Pen(w, h, out_scale * supersample)
    SCENES[sid](p)
    return p.render(round(w * out_scale), round(h * out_scale))
