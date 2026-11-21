"""Original silkscreen-editorial vector illustrations, one per illustrated story (ids 1-13).

Each scene draws into an 8x supersampled Pen in 1x layout coordinates and
downsamples with LANCZOS for razor-sharp printmaking edges. In v3 every art
panel sits unobstructed ABOVE its full-width banner ribbon, so all 13 scenes
use luminous, balanced full-frame compositions with high legibility at 300px.
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
        cx = x + dx * t + rnd.uniform(-1.6, 1.6)
        cy = y + dy * t + rnd.uniform(-1.1, 1.1)
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
    n = 130
    for i in range(n + 1):
        t = i / n
        env = math.exp(-((t - burst) ** 2) / 0.008) + 0.07
        pts.append((x0 + (x1 - x0) * t, y + amp * env * rnd.uniform(-1, 1)))
    p.line(pts, color, width)


def pine(p, x, base, h, color):
    for k in range(3):
        top = base - h + k * h * 0.22
        wid = h * (0.24 + k * 0.1)
        p.poly([(x, top), (x - wid, top + h * 0.42), (x + wid, top + h * 0.42)], color)
    p.rect(x - h * 0.04, base - h * 0.15, x + h * 0.04, base, color)


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
    """1. COP31 Antalya: Mediterranean sunrise, oil derrick vs wind turbines, plenary dome & overtime clock."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.74, "#F2C794", "#FBF0DC")
    p.glow(w * 0.50, h * 0.60, h * 0.75, "#FFE3A6", 140)
    ridge(p, h * 0.62, h * 0.11, 1.5, 0.7, "#C8A488", y_floor=h * 0.78)
    ridge(p, h * 0.70, h * 0.07, 2.3, 1.9, "#A37F6A", y_floor=h * 0.78)
    waves(p, h * 0.75, h, "#2D7899", "#174A66", n=3, seed=11)

    # Left: dark steel oil derrick + pumpjack (the fossil-fuel deadlock)
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

    # Right: three crisp white wind turbines (clean energy transition)
    for tx, th, ang in ((w * 0.78, 42, 72), (w * 0.86, 56, 14), (w * 0.94, 46, 48)):
        top = base - th
        p.poly([(tx - 1.5, base), (tx - 0.6, top), (tx + 0.6, top), (tx + 1.5, base)], "#FFFFFF", "#8C9CA6", 0.4)
        for k in range(3):
            a = math.radians(ang + k * 120)
            p.line([(tx, top), (tx + math.cos(a) * th * 0.40, top + math.sin(a) * th * 0.40)], "#FFFFFF", 1.7)
        p.circle(tx, top, 1.7, "#3B4A54")

    # Center: Antalya COP31 plenary pavilion + delegate flags
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

    # Center-top: crisp archival brass-rimmed overtime clock + "+1 DAY" seal
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


def scene_riyadh(p):
    """2. Riyadh Missiles: midnight slate-indigo sky, illuminated Riyadh skyline, 3 interception bursts."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#10213D", "#233F6B")
    stars(p, 85, 29, y1=h * 0.68)
    p.glow(w * 0.52, h * 0.84, 110, "#F0B954", 88)
    p.rect(0, h * 0.78, w, h, "#11203A")

    # Left & center-left Riyadh towers
    for x, bw, bh in [(10, 20, 26), (34, 18, 34), (56, 22, 24), (82, 18, 38), (104, 24, 30)]:
        p.rect(x, h - bh, x + bw, h, "#182B4A", "#375585", 0.6)
        for yy in range(int(h - bh + 4), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                if ((int(xx) * 7 + yy * 13) % 5) < 3:
                    p.rect(xx, yy, xx + 1.8, yy + 2.1, "#F7C960")

    # Centered iconic Kingdom Centre tower (parabolic cutout arch)
    kx, kh = w * 0.48, 60.0
    p.poly([(kx - 11, h), (kx - 9.5, h - kh), (kx + 9.5, h - kh), (kx + 11, h)], "#213860", "#7C9ED1", 0.8)
    p.poly([(kx - 5.5, h - kh + 1), (kx + 5.5, h - kh + 1), (kx + 3.8, h - kh + 16),
            (kx, h - kh + 20), (kx - 3.8, h - kh + 16)], "#1A325A")
    p.line([(kx - 7.5, h - kh + 2), (kx + 7.5, h - kh + 2)], "#FFE59E", 1.2)
    for yy in range(int(h - kh + 23), int(h - 4), 5):
        for xx in (kx - 6, kx - 2, kx + 2, kx + 5):
            p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F9D06B")

    # Al Faisaliah pyramid spire + golden orb
    fx, fh = w * 0.64, 50.0
    p.poly([(fx - 12, h), (fx, h - fh), (fx + 12, h)], "#1D3358", "#7C9ED1", 0.8)
    p.line([(fx, h - fh), (fx, h - fh - 7)], "#B0CBF0", 1.0)
    p.circle(fx, h - fh + 10, 4.0, "#F8C846", "#FFF2B2", 0.6)
    for k in range(5):
        yy = h - 7 - k * 7.5
        hw = 9 - k * 1.4
        p.line([(fx - hw, yy), (fx + hw, yy)], rgb("#F8D374", 190), 0.85)

    # KAFD right towers
    for x, bw, bh in [(w * 0.74, 18, 42), (w * 0.82, 20, 48), (w * 0.90, 22, 34)]:
        p.poly([(x, h), (x, h - bh), (x + bw, h - bh + 6), (x + bw, h)], "#1B3054", "#6486BA", 0.7)
        for yy in range(int(h - bh + 8), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F5C65D")

    # 3 incoming dotted arcs + rising defence interceptors + bright amber starbursts across full sky
    bursts = [
        ((w * 0.28, h * 0.26), (w * 0.02, h * 0.04), (w * 0.36, h * 0.72), 12.5),
        ((w * 0.56, h * 0.22), (w * 0.86, h * 0.02), (w * 0.52, h * 0.66), 13.5),
        ((w * 0.80, h * 0.30), (w * 0.99, h * 0.10), (w * 0.72, h * 0.70), 11.5),
    ]
    for (bx, by), (sx, sy), (ix, iy), br in bursts:
        steps = 14
        for k in range(steps):
            if k % 2 == 1:
                continue
            t0, t1 = k / steps, (k + 0.7) / steps
            x0 = sx + (bx - sx) * t0
            y0 = sy + (by - sy) * t0 - math.sin(t0 * math.pi) * 5
            x1 = sx + (bx - sx) * t1
            y1 = sy + (by - sy) * t1 - math.sin(t1 * math.pi) * 5
            p.line([(x0, y0), (x1, y1)], "#FF7849", 1.6)
        p.line([(ix, iy), (bx, by)], rgb("#80E2FF", 195), 1.35)
        p.line([(ix + (bx - ix) * 0.48, iy + (by - iy) * 0.48), (bx, by)], "#FFFFFF", 1.0)
        p.glow(bx, by, br * 2.0, "#FF9E2C", 180, steps=12)
        starburst(p, bx, by, br, br * 0.38, "#FFB338", "#FFF9D6", rays=10)


def scene_kryvyi(p):
    """3. Kryvyi Rih Strike: luminous slate-amber dusk, skyline, plume, drone & rescue ambulance."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#6E8AA6", "#E8C6A3")
    p.glow(w * 0.42, h * 0.54, 48, "#FF8138", 150)

    # Crisp Ukraine blue/gold edge band along left frame
    p.rect(0, 0, 4.5, h * 0.5, "#0057B7")
    p.rect(0, h * 0.5, 4.5, h, "#FFD700")

    # Apartment blocks across city skyline
    blocks = [
        (10, 34, 40), (48, 36, 48), (88, 38, 56), (130, 40, 52),
        (174, 36, 44), (214, 38, 48), (256, 36, 42), (296, 22, 36),
    ]
    rnd = Rand(17)
    for i, (x, bw, bh) in enumerate(blocks):
        top = h - bh
        col = "#4E5866" if i % 2 == 0 else "#5E6A79"
        p.rect(x, top, x + bw, h, col, "#353D47", 0.5)
        for yy in range(int(top + 5), int(h - 8), 6):
            for xx in range(int(x + 4), int(x + bw - 5), 6):
                lit = rnd.next() > 0.68
                p.rect(xx, yy, xx + 3.0, yy + 3.4, "#F8D57E" if lit else "#343B44")

    # Plume & fiery impact centered on block 3 (x=107, y=38)
    hx, hy = 107.0, h - 56.0
    smoke(p, hx, hy, 44, -38, 6.5, 19, 15, "#2F333B", 195, seed=31)
    flames(p, hx, hy + 7, 22, 16, seed=12)
    p.glow(hx, hy + 4, 24, "#FF7A2F", 160)

    # Diving double-tap delta drone in clear upper-right sky
    p.line([(w * 0.92, h * 0.08), (w * 0.78, h * 0.28)], rgb("#FFFFFF", 215), 1.4)
    delta_drone(p, w * 0.77, h * 0.29, 8.2, "#1A1E24", tilt=2.45)

    # Rescue ambulance in lower-center-right foreground (clear of tiny right chip)
    p.rect(4.5, h - 8, w, h, "#252B33")
    ax, ay = w * 0.62, h - 7
    p.glow(ax - 7, ay - 19, 11, "#3898FF", 180, steps=10)
    p.rect(ax - 26, ay - 18, ax + 13, ay - 2, "#FFFFFF", "#1C242E", 0.9, r=2)
    p.poly([(ax + 13, ay - 15), (ax + 22, ay - 15), (ax + 27, ay - 8.5), (ax + 27, ay - 2),
            (ax + 13, ay - 2)], "#FFFFFF", "#1C242E", 0.9)
    p.poly([(ax + 15, ay - 13.5), (ax + 21.5, ay - 13.5), (ax + 24.5, ay - 9), (ax + 15, ay - 9)], "#7FB8E0")
    p.rect(ax - 26, ay - 6.5, ax + 26, ay - 4.2, "#C82222")
    cx, cy = ax - 7, ay - 11.8
    p.rect(cx - 4.6, cy - 1.5, cx + 4.6, cy + 1.5, "#C82222")
    p.rect(cx - 1.5, cy - 4.6, cx + 1.5, cy + 4.6, "#C82222")
    p.rect(ax - 10, ay - 21, ax - 4, ay - 18, "#2B88FF")
    for wx in (ax - 16, ax + 18):
        p.circle(wx, ay - 1.5, 3.8, "#14181F")
        p.circle(wx, ay - 1.5, 1.5, "#C8D0D8")


def scene_finland(p):
    """4. Gulf of Finland (Sparta II): bright Nordic horizon, burning freighter + 2 diving drones."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.60, "#B4C8D8", "#ECF2F6")
    for k, x in enumerate(range(int(w * 0.72), int(w) + 6, 5)):
        pine(p, x, h * 0.61, 6.5 + (k * 37 % 4), "#324D43")
    p.rect(w * 0.70, h * 0.60, w, h * 0.62, "#324D43")
    waves(p, h * 0.60, h, "#3F6D88", "#1F4258", n=3, seed=8)

    bx, by = w * 0.40, h * 0.76
    p.poly([(bx - 50, by - 6), (bx + 44, by - 6), (bx + 52, by - 12), (bx + 38, by + 5),
            (bx - 46, by + 5)], "#232B34")
    p.rect(bx - 49, by - 6, bx + 44, by - 3.8, "#A82824")
    cols = ["#1F4A6E", "#C85A1C", "#2E7D4F", "#A82824", "#1F4A6E", "#D9A441"]
    for i, c in enumerate(cols):
        x = bx - 29 + i * 10.5
        p.rect(x, by - 13, x + 9.0, by - 6.5, c)
        if i % 2 == 0:
            p.rect(x, by - 19, x + 9.0, by - 13.5, cols[(i + 3) % 6])
    p.rect(bx - 47, by - 20, bx - 33, by - 6, "#F4F1EA")
    p.rect(bx - 45, by - 24, bx - 36, by - 20, "#F4F1EA")
    smoke(p, bx - 34, by - 22, 58, -22, 4.0, 12, 13, "#32363E", 180, seed=4)
    flames(p, bx - 35, by - 17, 16, 14, seed=6)
    p.glow(bx - 35, by - 14, 19, "#FF9A3C", 150)

    delta_drone(p, w * 0.80, h * 0.22, 7.0, "#18202A", tilt=2.55)
    delta_drone(p, w * 0.90, h * 0.36, 5.8, "#18202A", tilt=2.65)
    p.line([(w * 0.84, h * 0.16), (w * 0.96, h * 0.05)], rgb("#FFFFFF", 190), 0.9)


def scene_peru(p):
    """5. Peru M6.7 Quake: bright Andes cordillera + adobe house + crisp archival seismograph."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.65, "#B9D7EC", "#F5F1E7")
    peaks = [(-8, 0.95), (w * 0.16, 0.24), (w * 0.33, 0.56), (w * 0.54, 0.14),
             (w * 0.72, 0.48), (w * 0.87, 0.22), (w + 8, 0.82)]
    pts = [(-8, h)] + [(x, h * y) for x, y in peaks] + [(w + 8, h)]
    p.poly(pts, "#79685A")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2:
            px, py = x1, h * y1
            p.poly([(px, py), (px - 9, py + 10), (px - 3.5, py + 7.5), (px, py + 12),
                    (px + 4.5, py + 7.5), (px + 9, py + 10)], "#FFFFFF")
    ridge(p, h * 0.68, h * 0.04, 2.0, 0.5, "#5A7D43", y_floor=h * 0.76)

    hx, hy = w * 0.22, h * 0.66
    p.poly([(hx - 6.5, hy), (hx + 5.5, hy - 1.8), (hx + 4.2, hy - 10), (hx - 7.8, hy - 8.2)],
           "#F6E9D2", "#5A4535", 0.7)
    p.poly([(hx - 9.5, hy - 7.8), (hx - 2.0, hy - 14.5), (hx + 6.0, hy - 10)], "#B8472F", "#5A4535", 0.6)
    p.arc(hx - 2, hy - 8, 12, 190, 250, "#A82824", 0.9)
    p.arc(hx - 2, hy - 8, 12, 300, 350, "#A82824", 0.9)

    sy0, sy1 = h * 0.66, h
    p.rect(0, sy0, w, sy1, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#BFB5A3", 0.7)
    for k in range(1, 14):
        p.line([(w * k / 14, sy0), (w * k / 14, sy1)], "#ECE4D6", 0.45)
    seismo(p, 4, w - 4, (sy0 + sy1) / 2, (sy1 - sy0) * 0.44, "#C82222", seed=12, width=1.15, burst=0.45)


def scene_timor(p):
    """6. Timor-Leste M6.8 Quake: deep bathymetric sea-teal + Timor island + concentric seismic wave."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#2B7E96", "#17546A")
    for k in range(1, 5):
        p.line([(0, h * k / 5), (w, h * k / 5)], rgb("#FFFFFF", 38), 0.4)
        p.line([(w * k / 5, 0), (w * k / 5, h)], rgb("#FFFFFF", 38), 0.4)

    island = [(w * 0.05, h * 0.84), (w * 0.18, h * 0.60), (w * 0.36, h * 0.48), (w * 0.54, h * 0.44),
              (w * 0.62, h * 0.50), (w * 0.56, h * 0.62), (w * 0.40, h * 0.72), (w * 0.22, h * 0.86),
              (w * 0.10, h * 0.94)]
    p.poly(island, "#94C46D", "#5E8A3E", 0.8)
    p.poly([(w * 0.64, h * 1.04), (w * 0.78, h * 0.80), (w * 1.04, h * 0.74), (w * 1.04, h * 1.04)],
           "#E5CA8E", "#B59A5E", 0.7)

    ex, ey = w * 0.74, h * 0.40
    for k, (rr, col, wdt) in enumerate([(25, "#FF6458", 1.0), (18, "#FF3B30", 1.15),
                                        (12, "#FFFFFF", 1.2), (6.5, "#FF3B30", 1.2)]):
        p.circle(ex, ey, rr, rgb("#FF3B30", 24 + k * 14), col, wdt)
    star5(p, ex, ey, 5.2, "#FFD23F")
    p.circle(ex, ey, 1.7, "#A82824")


def scene_davao(p):
    """7. Davao Air Niugini 146 Safe: luminous tropical sky + runway + white 767 + alert & chute."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.68, "#82BEE8", "#EAF6FD")
    ridge(p, h * 0.63, h * 0.08, 1.4, 0.5, "#74A380", y_floor=h * 0.70)
    p.rect(0, h * 0.68, w, h, "#303944")
    p.line([(0, h * 0.68), (w, h * 0.68)], "#66717F", 0.8)
    for k in range(8):
        x0 = 6 + k * 24
        p.rect(x0, h * 0.82, x0 + 13, h * 0.86, "#EDF2F7")

    px, py = w * 0.46, h * 0.61
    # Tail fin (Air Niugini black/red/gold — cleanly centered in open sky!)
    p.poly([(px - 42, py - 2), (px - 53, py - 18), (px - 42, py - 18), (px - 31, py - 3)], "#181D24")
    p.poly([(px - 50, py - 16), (px - 43, py - 16), (px - 37.5, py - 8), (px - 44.5, py - 8)], "#D7262E")
    p.circle(px - 44, py - 12, 2.0, "#FFD23F")
    # Fuselage
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
    # Yellow-white evacuation chute
    p.poly([(px + 26, py + 3), (px + 33, py + 3), (px + 43, h * 0.85), (px + 34, h * 0.85)],
           "#FFF3C4", "#7D6F4B", 0.7)


def scene_fbi_ncic(p):
    """8. FBI NCIC Hack: architectural blueprint-blue terminal + server stack + gold-rimmed shield."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#22446B", "#173252")
    for k in range(1, 5):
        p.line([(0, h * k / 5), (w, h * k / 5)], rgb("#8CC4F5", 38), 0.45)
    for k in range(1, 9):
        p.line([(w * k / 9, 0), (w * k / 9, h)], rgb("#8CC4F5", 34), 0.45)

    # Clean NCIC database cylinder stack on left
    dx, dy, rw = w * 0.28, h * 0.54, 24.0
    for k in range(3):
        yy = dy + 11 - k * 10.5
        p.rect(dx - rw, yy - 5.5, dx + rw, yy + 3, "#3669A0", "#AED8FF", 0.7)
        p.ellipse(dx, yy + 3, rw, 4.0, "#295485", "#AED8FF", 0.7)
        p.ellipse(dx, yy - 5.5, rw, 4.0, "#4B83BE", "#CBE5FF", 0.7)
        p.circle(dx - rw + 7, yy - 1, 1.4, "#5CE6A0")
        p.circle(dx - rw + 12, yy - 1, 1.4, "#FF5252")

    # Crimson breach trace linking server stack to federal shield
    p.line([(dx + rw + 2, dy), (w * 0.50, dy), (w * 0.54, dy - 10),
            (w * 0.59, dy + 6), (w * 0.65, dy - 2)], "#FF5A4E", 1.7)

    # Federal navy/gold shield + crimson breach alert triangle on right
    sx, sy = w * 0.75, h * 0.48
    shield = [(sx, sy - 18), (sx + 17, sy - 12.5), (sx + 15, sy + 4), (sx, sy + 17),
              (sx - 15, sy + 4), (sx - 17, sy - 12.5)]
    p.poly(shield, "#183359", "#F0C35A", 1.4)
    p.glow(sx, sy, 18, "#FF4238", 130, steps=10)
    p.poly([(sx, sy - 11.5), (sx - 11.5, sy + 8), (sx + 11.5, sy + 8)], "#C82222", "#FFFFFF", 1.0)
    p.rect(sx - 1.2, sy - 5.8, sx + 1.2, sy + 1.8, "#FFFFFF")
    p.circle(sx, sy + 4.8, 1.3, "#FFFFFF")


def scene_sinaloa(p):
    """9. Sinaloa Capture: warm terracotta-violet desert twilight + helicopter beam + silver handcuffs."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.74, "#56386B", "#F09454")
    p.glow(w * 0.52, h * 0.70, 44, "#FFC86E", 145)
    ridge(p, h * 0.62, h * 0.12, 1.4, 1.0, "#7A4752", y_floor=h * 0.85)
    ridge(p, h * 0.76, h * 0.05, 2.2, 0.2, "#472932", y_floor=h)
    p.rect(0, h * 0.82, w, h, "#28181F")

    # Military helicopter in open upper-right sky sweeping pale-gold searchlight
    hx, hy = w * 0.72, h * 0.24
    p.d.polygon(p._pts([(hx - 6, hy + 4.5), (hx - 34, h * 0.88), (hx + 10, h * 0.88), (hx + 3, hy + 4.5)]),
                fill=rgb("#FFF3BE", 85))
    p.ellipse(hx, hy, 11.5, 4.8, "#181C22")
    p.poly([(hx + 7, hy - 1.8), (hx + 27, hy - 1.2), (hx + 27, hy + 0.5), (hx + 7, hy + 1.8)], "#181C22")
    p.poly([(hx + 25, hy - 5.5), (hx + 28, hy - 5.5), (hx + 27, hy + 1), (hx + 24, hy + 1)], "#181C22")
    p.ellipse(hx - 5.5, hy - 1, 3.8, 2.2, "#F9CC78")
    p.line([(hx - 19, hy - 6.8), (hx + 19, hy - 6.0)], "#181C22", 1.1)
    p.line([(hx, hy - 4.5), (hx, hy - 6.4)], "#181C22", 1.2)
    p.line([(hx - 6, hy + 5.8), (hx + 6, hy + 5.8)], "#181C22", 0.9)

    # Crisp silver interlocking handcuffs centered left
    cx1, cy1 = w * 0.20, h * 0.52
    cx2, cy2 = w * 0.40, h * 0.52
    p.circle(cx1, cy1, 12.2, None, "#F2F5F8", 2.9)
    p.circle(cx1, cy1, 12.2, None, "#2A3038", 0.6)
    p.circle(cx2, cy2, 12.2, None, "#F2F5F8", 2.9)
    p.circle(cx2, cy2, 12.2, None, "#2A3038", 0.6)
    p.line([(cx1 + 10.5, cy1 - 2.5), (cx2 - 10.5, cy2 - 2.5)], "#D6DCE2", 2.2)
    p.glow(w * 0.55, h * 0.80, 9, "#FF2D2D", 185, steps=8)
    p.glow(w * 0.62, h * 0.80, 9, "#2B7FFF", 185, steps=8)


def scene_eu_indonesia(p):
    """10. EU-Indonesia CEPA: archival EU blue/gold star circle + Indonesia red/white + brass seal."""
    w, h = p.w, p.h
    p.rect(0, 0, w * 0.5, h, "#0C3B8E")
    p.rect(w * 0.5, 0, w, h * 0.5, "#C81C2A")
    p.rect(w * 0.5, h * 0.5, w, h, "#FAF7F0")
    p.line([(w * 0.5, 0), (w * 0.5, h)], "#182A40", 0.8)

    ex, ey, er = w * 0.24, h * 0.50, 15.0
    for k in range(12):
        a = math.radians(-90 + k * 30)
        star5(p, ex + math.cos(a) * er, ey + math.sin(a) * er, 2.5, "#FFCC00")

    mx, my, mr = w * 0.50, h * 0.50, 16.0
    p.circle(mx + 1, my + 1.5, mr + 1, (0, 0, 0, 65))
    p.circle(mx, my, mr, "#F2C338", "#182A40", 1.3)
    p.circle(mx, my, mr - 2.4, None, "#FFF5C7", 0.7)
    p.line([(mx - 8.2, my - 3.6), (mx + 5.2, my - 3.6)], "#131B26", 2.1)
    p.poly([(mx + 9.4, my - 3.6), (mx + 4.0, my - 7.2), (mx + 4.0, my)], "#131B26")
    p.line([(mx + 8.2, my + 3.6), (mx - 5.2, my + 3.6)], "#131B26", 2.1)
    p.poly([(mx - 9.4, my + 3.6), (mx - 4.0, my), (mx - 4.0, my + 7.2)], "#131B26")


def scene_iran_launcher(p):
    """11. Iran Underground Launcher: crisp geological mountain-bunker cross-section + twin rails."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.48, "#DDE5EC", "#F3EDE2")
    # Sandstone mountain ridge over subterranean cavern
    ridge(p, h * 0.34, h * 0.14, 1.3, 0.6, "#C4A47C", y_floor=h)
    p.rect(0, h * 0.42, w, h, "#A98963")
    # Subterranean reinforced concrete vault cutaway
    p.ellipse(w * 0.52, h * 0.96, w * 0.44, h * 0.72, "#394454", "#6B788A", 1.3)
    p.ellipse(w * 0.52, h * 0.96, w * 0.38, h * 0.62, "#222B38")
    p.rect(0, h * 0.80, w, h, "#465161")

    # Mobile TEL truck + twin angled ballistic missiles centered cleanly in bunker arch
    tx, ty = w * 0.52, h * 0.82
    p.rect(tx - 28, ty - 9, tx + 26, ty - 1.5, "#4E5C4A", "#1C231A", 0.7, r=1.5)
    p.rect(tx + 17, ty - 13, tx + 28, ty - 1.5, "#5E6E58", "#1C231A", 0.7, r=1.5)
    p.rect(tx + 20, ty - 11.5, tx + 26, ty - 8, "#A6CDE6")
    for wx in (tx - 21, tx - 9, tx + 4, tx + 20):
        p.circle(wx, ty - 1, 3.6, "#14181F")
        p.circle(wx, ty - 1, 1.4, "#929DA8")

    ang = math.radians(-26)
    ca, sa = math.cos(ang), math.sin(ang)
    for off_x, off_y in ((0, -4.5), (3.5, 2.5)):
        bx0, by0 = tx - 20 + off_x, ty - 10 + off_y
        length = 44.0
        bx1, by1 = bx0 + ca * length, by0 + sa * length
        p.line([(bx0 - 2.5, by0 + 3.0), (bx1 - 4.5, by1 + 3.0)], "#7E8B9C", 1.5)
        p.line([(bx0, by0), (bx1, by1)], "#EEF2F6", 3.8)
        nx, ny = bx1 + ca * 6.5, by1 + sa * 6.5
        px, py = -sa * 2.1, ca * 2.1
        p.poly([(nx, ny), (bx1 + px, by1 + py), (bx1 - px, by1 - py)], "#C82822")

    # Subtle Iran flag accent stripe bottom-left
    fx0, fy0 = 6, h - 10
    p.rect(fx0, fy0, fx0 + 34, fy0 + 2.2, "#239F40")
    p.rect(fx0, fy0 + 2.2, fx0 + 34, fy0 + 4.4, "#FFFFFF")
    p.rect(fx0, fy0 + 4.4, fx0 + 34, fy0 + 6.6, "#DA0000")


def scene_geneva_ai(p):
    """12. Geneva UN 'Killer Robot' Talks: luminous UN blue + robot visor + deadlock slash + 2028."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#4584C4", "#245791")
    for k in range(5):
        x = 9 + k * 9
        p.rect(x, h * 0.28, x + 4.2, h, rgb("#FFFFFF", 36))
    p.poly([(6, h * 0.28), (54, h * 0.28), (30, h * 0.14)], rgb("#FFFFFF", 36))

    rx, ry = w * 0.44, h * 0.62
    p.rect(rx - 14, ry - 15, rx + 14, ry + 3, "#E4EBF2", "#58687A", 0.8, r=3.5)
    p.rect(rx - 10, ry - 10, rx + 10, ry - 4, "#151D28", r=1.8)
    p.rect(rx - 7.5, ry - 8.2, rx + 7.5, ry - 5.6, "#FF3B30", r=0.9)
    p.line([(rx, ry - 15), (rx, ry - 20.5)], "#C2D3E6", 1.1)
    p.circle(rx, ry - 21, 2.1, "#FF3B30")
    p.rect(rx - 20, ry + 5, rx + 20, h + 2, "#C3CFDC", "#58687A", 0.8, r=4)
    p.line([(rx - 18, ry - 14), (rx + 18, ry + 11)], "#FF3B30", 2.1)

    cx0, cy0 = w * 0.68, h * 0.08
    p.rect(cx0 + 1.5, cy0 + 1.5, cx0 + 46.5, cy0 + 34.5, (0, 0, 0, 70), r=2)
    p.rect(cx0, cy0, cx0 + 45, cy0 + 33, "#FFFFFF", r=2)
    p.rect(cx0, cy0, cx0 + 45, cy0 + 9.5, "#A82824", r=2)
    p.rect(cx0, cy0 + 5.5, cx0 + 45, cy0 + 9.5, "#A82824")
    p.text(cx0 + 22.5, cy0 + 4.8, "TARGET", 5.5, "#FFFFFF")
    p.text(cx0 + 22.5, cy0 + 21.8, "2028", 13.0, "#131B26")


def scene_mcg(p):
    """13. MCG Record 188 Chase: twilight stadium + emerald oval + cricket bat & ball + 188 board."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.44, "#1A3762", "#345C94")
    for x in (w * 0.08, w * 0.92):
        p.line([(x, h * 0.48), (x, h * 0.10)], "#B8C6D8", 1.2)
        p.rect(x - 5.5, h * 0.05, x + 5.5, h * 0.12, "#FFF7D2")
        p.glow(x, h * 0.09, 20, "#FFF2A8", 135, steps=10)

    p.ellipse(w * 0.5, h * 0.76, w * 0.62, h * 0.48, "#268F44")
    for k in range(1, 5):
        p.ellipse(w * 0.5, h * 0.76, w * 0.62 * (1 - k * 0.18), h * 0.48 * (1 - k * 0.18),
                  None, rgb("#3CB05A", 140), 1.8)
    p.rect(w * 0.45, h * 0.54, w * 0.53, h * 0.96, "#E3CFA0")
    for dx in (-2.0, 0, 2.0):
        p.line([(w * 0.49 + dx, h * 0.63), (w * 0.49 + dx, h * 0.55)], "#FFFFFF", 0.7)

    p.poly([(w * 0.16, h * 0.94), (w * 0.30, h * 0.52), (w * 0.36, h * 0.55), (w * 0.22, h * 0.97)],
           "#E9C584", "#7B5B2A", 0.9)
    p.line([(w * 0.33, h * 0.53), (w * 0.38, h * 0.40)], "#22262E", 2.4)
    for k in range(5):
        t = k / 4
        bx = w * (0.39 + 0.26 * t)
        by = h * (0.64 - 0.28 * t - 0.06 * math.sin(t * math.pi))
        p.circle(bx, by, 0.95 + t * 0.5, rgb("#FFFFFF", 95 + k * 25))
    p.circle(w * 0.67, h * 0.35, 5.2, "#C8102E", "#FFFFFF", 0.6)
    p.arc(w * 0.67, h * 0.35, 3.4, 110, 250, "#FFFFFF", 0.65)

    p.rect(w * 0.75, h * 0.10, w * 0.96, h * 0.44, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w * 0.855, h * 0.275, "188", 11.2, "#FFD23F")


SCENES = {
    1: scene_cop31,
    2: scene_riyadh,
    3: scene_kryvyi,
    4: scene_finland,
    5: scene_peru,
    6: scene_timor,
    7: scene_davao,
    8: scene_fbi_ncic,
    9: scene_sinaloa,
    10: scene_eu_indonesia,
    11: scene_iran_launcher,
    12: scene_geneva_ai,
    13: scene_mcg,
}


def draw_scene(sid, w, h, out_scale=2, supersample=4):
    p = Pen(w, h, out_scale * supersample)
    SCENES[sid](p)
    return p.render(round(w * out_scale), round(h * out_scale))
