"""Procedural editorial vector illustrations, one per illustrated story (ids 1-13).

Each scene draws into a high-contrast Pen whose coordinates are in 1x layout
pixels; the Pen supersamples at 8x so downsampling gives razor-sharp edges.
Focal elements are composed cleanly in the lower and right zones so top-left
crimson banners and bottom attribution chips never obscure key visual cues.
Everything is deterministic (fixed-seed LCG only).
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

    def glow(self, cx, cy, r, color, alpha=120, steps=20):
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
        cx = x + dx * t + rnd.uniform(-1.8, 1.8)
        cy = y + dy * t + rnd.uniform(-1.2, 1.2)
        r = r0 + (r1 - r0) * t
        p.circle(cx, cy, r, rgb(color, round(alpha * (1 - 0.5 * t))))


def flames(p, cx, base, w, h, seed=5):
    rnd = Rand(seed)
    for layer, col in enumerate(("#B52323", "#EE6A1F", "#FFB23F", "#FFE999")):
        k = 1 - layer * 0.22
        pts = [(cx - w / 2 * k, base)]
        tongues = 5
        for i in range(tongues):
            x0 = cx - w / 2 * k + w * k * (i + 0.5) / tongues
            pts.append((x0 - w * k / tongues * 0.3, base - h * k * rnd.uniform(0.35, 0.55)))
            pts.append((x0 + rnd.uniform(-0.8, 0.8), base - h * k * rnd.uniform(0.75, 1.0)))
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
    """1. COP31 Antalya: pale teal sky, Earth globe + red thermometer + overtime clock."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.78, "#CBE7F2", "#EDF6F9")
    ridge(p, h * 0.72, h * 0.08, 1.5, 0.8, "#9EC4D4", y_floor=h * 0.8)
    waves(p, h * 0.78, h, "#2C7DA0", "#174E6B", n=3, seed=11)

    # Lower-left Antalya plenary hall silhouette + subtle international flag row (below sub-chip)
    hx0, hx1, hy = w * 0.06, w * 0.44, h * 0.80
    p.rect(hx0, hy - 14, hx1, hy, "#F2EDE3", "#7F8E98", 0.7)
    p.poly([(hx0 - 5, hy - 14), ((hx0 + hx1) / 2, hy - 25), (hx1 + 5, hy - 14)],
           "#DFD5C3", "#7F8E98", 0.7)
    for i in range(7):
        x = hx0 + 6 + i * (hx1 - hx0 - 12) / 6
        p.rect(x - 2.0, hy - 10, x + 2.0, hy, "#9EA8B0")
    flag_cols = ["#C8102E", "#003399", "#009739", "#FFCD00", "#E30A17", "#00843D", "#002B7F", "#F7A600"]
    for i, c in enumerate(flag_cols):
        x = hx0 + 2 + i * (hx1 - hx0 - 6) / (len(flag_cols) - 1)
        p.line([(x, hy), (x, hy - 23)], "#4A5660", 0.6)
        p.rect(x, hy - 23, x + 5.5, hy - 19, c)

    # Stylized wind turbine silhouette far-mid
    tx, ty = w * 0.48, h * 0.80
    p.poly([(tx - 1.4, ty), (tx - 0.6, ty - 34), (tx + 0.6, ty - 34), (tx + 1.4, ty)], "#FFFFFF", "#8DA2AE", 0.4)
    for k in range(3):
        a = math.radians(18 + k * 120)
        p.line([(tx, ty - 34), (tx + math.cos(a) * 14, ty - 34 + math.sin(a) * 14)], "#FFFFFF", 1.7)
    p.circle(tx, ty - 34, 1.6, "#4A5A64")

    # Right focal cluster: Bold stylized Earth globe + crimson thermometer + white clock face
    gx, gy, gr = w * 0.64, h * 0.52, 34.0
    p.circle(gx + 1.5, gy + 2.0, gr, (20, 40, 60, 45))
    p.circle(gx, gy, gr, "#1868A8", "#123D66", 1.2)
    # Graticule arcs on globe
    for rx in (12, 24):
        p.ellipse(gx, gy, rx, gr - 1, None, rgb("#8CD0F5", 90), 0.7)
    for dy in (-14, 0, 14):
        half = math.sqrt(max(1.0, gr * gr - dy * dy)) - 1
        p.line([(gx - half, gy + dy), (gx + half, gy + dy)], rgb("#8CD0F5", 90), 0.7)
    # Bold stylized continents inside globe
    p.poly([(gx - 22, gy - 14), (gx - 9, gy - 20), (gx - 2, gy - 10), (gx - 8, gy + 2),
            (gx - 20, gy - 3)], "#4DA352")
    p.poly([(gx - 12, gy + 5), (gx - 3, gy + 8), (gx - 6, gy + 24), (gx - 15, gy + 18)], "#57B25C")
    p.poly([(gx + 4, gy - 18), (gx + 21, gy - 14), (gx + 26, gy - 2), (gx + 14, gy + 4),
            (gx + 5, gy - 6)], "#4DA352")
    p.poly([(gx + 7, gy + 6), (gx + 20, gy + 8), (gx + 16, gy + 22), (gx + 8, gy + 19)], "#63BA68")
    p.circle(gx, gy, gr, None, "#123D66", 1.3)

    # High-contrast crimson thermometer beside globe
    tx0, ty_top, ty_bot = w * 0.79, 14.0, h * 0.76
    p.rect(tx0 - 5.2, ty_top, tx0 + 5.2, ty_bot, "#FFFFFF", "#14181F", 1.1, r=5.0)
    p.circle(tx0, ty_bot + 5, 9.5, "#FFFFFF", "#14181F", 1.1)
    p.rect(tx0 - 2.6, ty_top + 11, tx0 + 2.6, ty_bot + 3, "#D7262E", r=2.0)
    p.circle(tx0, ty_bot + 5, 6.8, "#D7262E")
    p.circle(tx0 - 2.2, ty_bot + 3, 2.0, rgb("#FFFFFF", 180))
    for k in range(5):
        yy = ty_top + 13 + k * 11
        p.line([(tx0 + 6.5, yy), (tx0 + 10.5, yy)], "#14181F", 1.0)

    # Crisp white overtime clock upper-right + "+1 DAY" pill
    cx, cy, cr = w * 0.905, h * 0.37, 21.5
    p.circle(cx + 1, cy + 1.5, cr + 2.0, (20, 30, 45, 55))
    p.circle(cx, cy, cr + 2.0, "#14181F")
    p.circle(cx, cy, cr, "#FFFFFF")
    p.d.pieslice([(cx - cr) * p.s, (cy - cr) * p.s, (cx + cr) * p.s, (cy + cr) * p.s],
                 -90, 15, fill=rgb("#D7262E", 205))
    for k in range(12):
        a = math.radians(k * 30 - 90)
        r0 = cr * (0.74 if k % 3 == 0 else 0.84)
        p.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * cr * 0.95, cy + math.sin(a) * cr * 0.95)],
               "#14181F", 1.3 if k % 3 == 0 else 0.7)
    p.line([(cx, cy), (cx + math.cos(math.radians(-65)) * cr * 0.5,
                      cy + math.sin(math.radians(-65)) * cr * 0.5)], "#14181F", 2.2)
    p.line([(cx, cy), (cx + math.cos(math.radians(15)) * cr * 0.80,
                      cy + math.sin(math.radians(15)) * cr * 0.80)], "#14181F", 1.5)
    p.circle(cx, cy, 2.0, "#D7262E")
    p.rect(cx - 21, cy + cr + 6, cx + 21, cy + cr + 20, "#B52323", "#FFFFFF", 0.9, r=2)
    p.text(cx, cy + cr + 13.2, "+1 DAY", 9.0, "#FFFFFF")


def scene_riyadh(p):
    """2. Riyadh Missiles: deep midnight sky, gold-lit Riyadh skyline, 3 interception arcs & starbursts."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#0A152B", "#1A3058")
    stars(p, 95, 29, y1=h * 0.72)
    p.glow(w * 0.72, h * 0.82, 95, "#F2B652", 95)

    # Distant city haze band
    p.rect(0, h * 0.76, w, h, "#101E38")

    # Gold-lit Riyadh skyline along bottom (prominent in center-right & right)
    # Left low skyline
    left_towers = [(18, 18, 22), (40, 14, 18), (60, 22, 26), (86, 16, 20), (108, 20, 30),
                   (134, 18, 25), (156, 22, 36)]
    for x, bw, bh in left_towers:
        p.rect(x, h - bh, x + bw, h, "#14223B", "#263B63", 0.5)
        for yy in range(int(h - bh + 4), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                if ((xx * 7 + yy * 13) % 5) < 3:
                    p.rect(xx, yy, xx + 1.8, yy + 2.2, "#F5C65D")

    # Iconic Kingdom Centre tower (parabolic cutout arch) at x=w*0.60
    kx = w * 0.60
    kh = 68.0
    p.poly([(kx - 11, h), (kx - 9.5, h - kh), (kx + 9.5, h - kh), (kx + 11, h)], "#1D3156", "#6D8DC2", 0.8)
    # Inverted arch skybridge opening
    p.poly([(kx - 5.5, h - kh + 1), (kx + 5.5, h - kh + 1), (kx + 3.8, h - kh + 18),
            (kx, h - kh + 22), (kx - 3.8, h - kh + 18)], "#14274A")
    p.line([(kx - 7.5, h - kh + 2), (kx + 7.5, h - kh + 2)], "#FFE49C", 1.2)
    for yy in range(int(h - kh + 25), int(h - 4), 5):
        for xx in (kx - 6, kx - 2, kx + 2, kx + 5):
            p.rect(xx, yy, xx + 1.8, yy + 2.2, "#F9D06B")

    # Iconic Al Faisaliah pyramid spire + golden orb at x=w*0.74
    fx = w * 0.74
    fh = 56.0
    p.poly([(fx - 12, h), (fx, h - fh), (fx + 12, h)], "#1A2E52", "#6D8DC2", 0.8)
    p.line([(fx, h - fh), (fx, h - fh - 8)], "#A8C3EA", 1.0)
    p.circle(fx, h - fh + 11, 4.2, "#F8C846", "#FFF2B2", 0.6)
    for k in range(5):
        yy = h - 8 - k * 8
        hw = 9 - k * 1.4
        p.line([(fx - hw, yy), (fx + hw, yy)], rgb("#F8D374", 190), 0.9)

    # KAFD / PIF modern faceted towers on right
    right_towers = [(w * 0.82, 16, 46), (w * 0.88, 18, 54), (w * 0.95, 16, 38)]
    for x, bw, bh in right_towers:
        p.poly([(x, h), (x, h - bh), (x + bw, h - bh + 7), (x + bw, h)], "#182A4B", "#5675AB", 0.7)
        for yy in range(int(h - bh + 9), int(h - 4), 5):
            for xx in range(int(x + 3), int(x + bw - 3), 4):
                p.rect(xx, yy, xx + 1.8, yy + 2.0, "#F5C65D")

    # 3 incoming Houthi ballistic missile dotted arcs + interceptor streaks + bright amber starbursts
    bursts = [
        ((w * 0.64, h * 0.24), (w * 0.99, h * 0.05), (w * 0.56, h * 0.72), 14.0),
        ((w * 0.78, h * 0.18), (w * 1.01, h * 0.01), (w * 0.73, h * 0.66), 12.5),
        ((w * 0.89, h * 0.34), (w * 1.02, h * 0.16), (w * 0.84, h * 0.74), 11.5),
    ]
    for (bx, by), (sx, sy), (ix, iy), br in bursts:
        # Incoming dotted orange-red ballistic arc
        steps = 16
        for k in range(steps):
            if k % 2 == 1:
                continue
            t0, t1 = k / steps, (k + 0.7) / steps
            x0 = sx + (bx - sx) * t0
            y0 = sy + (by - sy) * t0 - math.sin(t0 * math.pi) * 6
            x1 = sx + (bx - sx) * t1
            y1 = sy + (by - sy) * t1 - math.sin(t1 * math.pi) * 6
            p.line([(x0, y0), (x1, y1)], "#FF7043", 1.7)
        # Rising interceptor streak from city air defence
        p.line([(ix, iy), (bx, by)], rgb("#7CE0FF", 190), 1.4)
        p.line([(ix + (bx - ix) * 0.45, iy + (by - iy) * 0.45), (bx, by)], "#FFFFFF", 1.1)
        # Burst glow & sharp amber-white starburst
        p.glow(bx, by, br * 2.1, "#FF9E2C", 185, steps=14)
        starburst(p, bx, by, br, br * 0.38, "#FFB338", "#FFF9D6", rays=10)


def scene_kryvyi(p):
    """3. Kryvyi Rih Strike: smoky dusk sky, Ukraine band, apartment blocks, plume & ambulance."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#516984", "#D8B392")
    p.glow(w * 0.65, h * 0.62, 56, "#FF8138", 160)

    # Subtle Ukraine national stripe accent along right edge
    p.rect(w - 5, 0, w, h * 0.5, "#0057B7")
    p.rect(w - 5, h * 0.5, w, h, "#FFD700")

    # Apartment blocks across city skyline (lower/mid clear of banners)
    blocks = [
        (8, 36, 42), (48, 34, 48), (86, 38, 44), (128, 36, 56),
        (168, 42, 62), (214, 38, 52), (256, 34, 46), (292, 22, 38),
    ]
    rnd = Rand(17)
    for i, (x, bw, bh) in enumerate(blocks):
        top = h - bh
        col = "#4E5763" if i % 2 == 0 else "#5E6875"
        p.rect(x, top, x + bw, h, col, "#353C45", 0.5)
        for yy in range(int(top + 5), int(h - 8), 7):
            for xx in range(int(x + 4), int(x + bw - 5), 6):
                lit = rnd.next() > 0.68
                p.rect(xx, yy, xx + 3.2, yy + 3.8, "#F8D57E" if lit else "#333A42")

    # Smoke plume & fiery impact on center-right block (x=189, y=54)
    hx, hy = 189.0, h - 62.0
    smoke(p, hx, hy, 38, -50, 7, 22, 16, "#2D3036", 205, seed=31)
    flames(p, hx, hy + 8, 24, 18, seed=12)
    p.glow(hx, hy + 4, 28, "#FF7A2F", 170)

    # Diving double-tap drone from upper-right
    p.line([(w * 0.96, h * 0.04), (w * 0.83, h * 0.22)], rgb("#FFFFFF", 205), 1.4)
    delta_drone(p, w * 0.82, h * 0.23, 8.5, "#1A1E24", tilt=2.45)

    # Lower-right emergency ambulance with vivid red cross & blue siren glow
    p.rect(0, h - 10, w - 5, h, "#252A30")
    ax, ay = w * 0.82, h - 9
    p.glow(ax - 8, ay - 20, 12, "#3898FF", 180, steps=10)
    p.rect(ax - 28, ay - 19, ax + 14, ay - 2, "#FFFFFF", "#1C242E", 0.9, r=2)
    p.poly([(ax + 14, ay - 16), (ax + 24, ay - 16), (ax + 29, ay - 9), (ax + 29, ay - 2),
            (ax + 14, ay - 2)], "#FFFFFF", "#1C242E", 0.9)
    p.poly([(ax + 16, ay - 14), (ax + 23, ay - 14), (ax + 26.5, ay - 9.5), (ax + 16, ay - 9.5)], "#7FB8E0")
    p.rect(ax - 28, ay - 7, ax + 28, ay - 4.5, "#D7262E")
    # Crisp red medical cross on ambulance side
    cx, cy = ax - 8, ay - 12.5
    p.rect(cx - 5.0, cy - 1.7, cx + 5.0, cy + 1.7, "#D7262E")
    p.rect(cx - 1.7, cy - 5.0, cx + 1.7, cy + 5.0, "#D7262E")
    # Flashing blue roof beacon
    p.rect(ax - 11, ay - 22, ax - 5, ay - 19, "#2B88FF")
    for wx in (ax - 17, ax + 19):
        p.circle(wx, ay - 1.5, 4.2, "#14181F")
        p.circle(wx, ay - 1.5, 1.7, "#C8D0D8")


def scene_finland(p):
    """4. Gulf of Finland (Sparta II): Nordic sea, burning freighter + smoke + 2 drones."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.60, "#8DA4B8", "#D8E2EA")
    for k, x in enumerate(range(int(w * 0.70), int(w) + 6, 5)):
        pine(p, x, h * 0.61, 7 + (k * 37 % 5), "#334A40")
    p.rect(w * 0.68, h * 0.60, w, h * 0.62, "#334A40")
    waves(p, h * 0.60, h, "#46708A", "#203D52", n=4, seed=8)

    # Freighter Sparta II in lower-left/mid
    bx, by = w * 0.38, h * 0.77
    p.poly([(bx - 52, by - 7), (bx + 46, by - 7), (bx + 54, by - 13), (bx + 40, by + 5),
            (bx - 48, by + 5)], "#232931")
    p.rect(bx - 51, by - 7, bx + 46, by - 4.5, "#B52323")
    cols = ["#2B6E9E", "#C85A1C", "#4E8A3A", "#A8323A", "#2B6E9E", "#D9A441"]
    for i, c in enumerate(cols):
        x = bx - 30 + i * 11
        p.rect(x, by - 15, x + 9.5, by - 7.5, c)
        if i % 2 == 0:
            p.rect(x, by - 22, x + 9.5, by - 15.5, cols[(i + 3) % 6])
    p.rect(bx - 49, by - 23, bx - 34, by - 7, "#F2EFE9")
    p.rect(bx - 47, by - 28, bx - 37, by - 23, "#F2EFE9")
    smoke(p, bx - 35, by - 26, 62, -26, 4.5, 14, 14, "#2B2D33", 185, seed=4)
    flames(p, bx - 36, by - 20, 18, 16, seed=6)
    p.glow(bx - 36, by - 16, 22, "#FF9A3C", 160)

    # Two delta drones diving in upper-right (clear of banner)
    delta_drone(p, w * 0.85, h * 0.24, 7.5, "#14181F", tilt=2.55)
    delta_drone(p, w * 0.93, h * 0.38, 6.0, "#14181F", tilt=2.65)
    p.line([(w * 0.89, h * 0.18), (w * 0.98, h * 0.06)], rgb("#FFFFFF", 180), 0.9)


def scene_peru(p):
    """5. Peru M6.7 Quake: Andes peaks + tilted house + bold crimson seismograph waveform."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.65, "#9BC5E6", "#EAF2F8")
    peaks = [(-8, 0.95), (w * 0.18, 0.36), (w * 0.34, 0.58), (w * 0.56, 0.20),
             (w * 0.72, 0.48), (w * 0.87, 0.22), (w + 8, 0.82)]
    pts = [(-8, h)] + [(x, h * y) for x, y in peaks] + [(w + 8, h)]
    p.poly(pts, "#6F5E51")
    for (x0, y0), (x1, y1), (x2, y2) in zip(peaks, peaks[1:], peaks[2:]):
        if y1 < y0 and y1 < y2:
            px, py = x1, h * y1
            p.poly([(px, py), (px - 10, py + 11), (px - 4, py + 8), (px, py + 13),
                    (px + 5, py + 8), (px + 10, py + 11)], "#FFFFFF")
    ridge(p, h * 0.72, h * 0.04, 2.0, 0.5, "#5A783C", y_floor=h * 0.82)

    # Tilted Andean house on lower-left with shake arcs
    hx, hy = w * 0.18, h * 0.68
    p.poly([(hx - 7, hy), (hx + 6, hy - 2), (hx + 4.5, hy - 11), (hx - 8.5, hy - 9)], "#F4E5CA", "#5A4535", 0.7)
    p.poly([(hx - 10.5, hy - 8.5), (hx - 2.5, hy - 16), (hx + 6.5, hy - 11)], "#C04832", "#5A4535", 0.6)
    p.arc(hx - 2, hy - 9, 13, 190, 250, "#B52323", 0.9)
    p.arc(hx - 2, hy - 9, 13, 300, 350, "#B52323", 0.9)

    # Crisp seismograph tape strip across lower band (above bottom-right chip)
    sy0, sy1 = h * 0.68, h * 0.92
    p.rect(0, sy0, w, sy1, "#FFFDF8")
    p.line([(0, sy0), (w, sy0)], "#B8AD9B", 0.7)
    p.line([(0, sy1), (w, sy1)], "#B8AD9B", 0.7)
    for k in range(1, 14):
        p.line([(w * k / 14, sy0), (w * k / 14, sy1)], "#EAE2D3", 0.45)
    seismo(p, 4, w - 4, (sy0 + sy1) / 2, (sy1 - sy0) * 0.46, "#D7262E", seed=12, width=1.2, burst=0.48)
    p.rect(0, sy1, w, h, "#2B313B")


def scene_timor(p):
    """6. Timor-Leste M6.8 Quake: deep teal Banda Sea + islands + concentric crimson rings."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#196B8A", "#0C3F56")
    for k in range(1, 6):
        p.line([(0, h * k / 6), (w, h * k / 6)], rgb("#FFFFFF", 35), 0.4)
        p.line([(w * k / 6, 0), (w * k / 6, h)], rgb("#FFFFFF", 35), 0.4)

    # Timor-Leste island lower-left
    island = [(w * 0.04, h * 0.88), (w * 0.18, h * 0.68), (w * 0.38, h * 0.58), (w * 0.56, h * 0.54),
              (w * 0.64, h * 0.58), (w * 0.58, h * 0.68), (w * 0.42, h * 0.76), (w * 0.24, h * 0.88),
              (w * 0.10, h * 0.96)]
    p.poly(island, "#8EC066", "#5D873E", 0.8)
    # Northern Australia (Darwin) lower-right
    p.poly([(w * 0.64, h * 1.04), (w * 0.79, h * 0.84), (w * 1.04, h * 0.78), (w * 1.04, h * 1.04)],
           "#E0C588", "#B3985B", 0.7)

    # Vivid red-and-white concentric seismic epicenter rings on right half
    ex, ey = w * 0.80, h * 0.44
    for k, (rr, col, wdt) in enumerate([(27, "#FF5252", 1.0), (20, "#FF3B30", 1.2),
                                        (13, "#FFFFFF", 1.2), (7.5, "#FF3B30", 1.3)]):
        p.circle(ex, ey, rr, rgb("#FF3B30", 24 + k * 14), col, wdt)
    star5(p, ex, ey, 5.6, "#FFD23F")
    p.circle(ex, ey, 1.8, "#B52323")


def scene_davao(p):
    """7. Davao Air Niugini 146 Safe: crisp sky + runway + bold white 767 + red engine glow & slide."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.72, "#6BB2E4", "#DCF0FB")
    # Distant Mindanao hills
    ridge(p, h * 0.68, h * 0.06, 1.4, 0.5, "#6E9A78", y_floor=h * 0.74)
    # Runway tarmac
    p.rect(0, h * 0.72, w, h, "#2C333D")
    p.line([(0, h * 0.72), (w, h * 0.72)], "#5B6470", 0.8)
    for k in range(8):
        x0 = 6 + k * 24
        p.rect(x0, h * 0.84, x0 + 13, h * 0.88, "#E6ECF2")

    # Bold white Boeing 767 silhouette touching down cleanly below banner
    px, py = w * 0.46, h * 0.66
    # Tail fin (Air Niugini black/red/gold accent — top at y=28, well clear of banner y=23)
    p.poly([(px - 42, py - 2), (px - 52, py - 16), (px - 42, py - 16), (px - 31, py - 3)], "#181C22")
    p.poly([(px - 49.5, py - 14.5), (px - 43, py - 14.5), (px - 37.5, py - 7), (px - 44, py - 7)], "#D7262E")
    p.circle(px - 43.5, py - 10.8, 1.8, "#FFD23F")
    # Fuselage
    p.poly([(px - 46, py - 2), (px + 42, py - 4.5), (px + 54, py - 1), (px + 52, py + 4),
            (px - 40, py + 4)], "#FFFFFF", "#3A4450", 0.7)
    p.rect(px + 38, py - 3.2, px + 47, py - 1.0, "#1C2A3A")  # cockpit
    for k in range(11):
        p.rect(px - 26 + k * 5.6, py - 2.0, px - 23.2 + k * 5.6, py - 0.3, "#2F4864")
    # Swept wing + red engine fire alert glow
    p.poly([(px - 10, py + 1), (px + 12, py + 1), (px - 4, py + 9.5), (px - 16, py + 9.5)], "#D8E2EC", "#3A4450", 0.5)
    p.rect(px - 2, py + 3, px + 9, py + 7.5, "#4A5462", r=1.5)
    p.glow(px + 2, py + 5.5, 10, "#FF4522", 210, steps=10)
    p.circle(px + 2, py + 5.5, 2.8, "#FF6A1A")
    p.circle(px + 2, py + 5.5, 1.3, "#FFE680")
    smoke(p, px - 2, py + 5, -24, -3.5, 1.6, 5.0, 8, "#FFFFFF", 165, seed=21)
    # Deployed white evacuation slide from forward door
    p.poly([(px + 26, py + 3), (px + 33, py + 3), (px + 43, h * 0.86), (px + 34, h * 0.86)],
           "#F5F8FB", "#6E7A88", 0.7)


def scene_fbi_ncic(p):
    """8. FBI NCIC Hack: dark navy terminal + database cylinders + crimson breach shield."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#0B1628", "#162A48")
    # Faint cyber grid & signal traces
    for k in range(1, 6):
        p.line([(0, h * k / 6), (w, h * k / 6)], rgb("#3A7BD5", 35), 0.45)
    for k in range(1, 9):
        p.line([(w * k / 9, 0), (w * k / 9, h)], rgb("#3A7BD5", 30), 0.45)

    # Lower-left database cylinder stack (NCIC server)
    dx, dy, rw = w * 0.28, h * 0.64, 24.0
    for k in range(3):
        yy = dy + 11 - k * 10.5
        p.rect(dx - rw, yy - 6, dx + rw, yy + 3, "#274C7D", "#72B4F5", 0.7)
        p.ellipse(dx, yy + 3, rw, 4.2, "#1E3E68", "#72B4F5", 0.7)
        p.ellipse(dx, yy - 6, rw, 4.2, "#3566A3", "#9CD0FF", 0.7)
        p.circle(dx - rw + 7, yy - 1, 1.4, "#5CE6A0")
        p.circle(dx - rw + 12, yy - 1, 1.4, "#FF5252")

    # Crimson intrusion signal trace connecting DB to shield
    p.line([(dx + rw + 2, dy - 4), (w * 0.52, dy - 4), (w * 0.56, dy - 12),
            (w * 0.61, dy + 2), (w * 0.67, dy - 6)], "#FF4D4D", 1.6)

    # Right federal shield + crimson breach warning triangle
    sx, sy = w * 0.77, h * 0.46
    shield = [(sx, sy - 20), (sx + 18, sy - 14), (sx + 16, sy + 4), (sx, sy + 18),
              (sx - 16, sy + 4), (sx - 18, sy - 14)]
    p.poly(shield, "#1E3A66", "#E6B84C", 1.3)
    # Breach warning triangle centered on shield
    p.glow(sx, sy - 1, 20, "#FF3B30", 140, steps=10)
    p.poly([(sx, sy - 13), (sx - 13, sy + 9), (sx + 13, sy + 9)], "#D7262E", "#FFFFFF", 1.0)
    p.rect(sx - 1.3, sy - 6.5, sx + 1.3, sy + 2.0, "#FFFFFF")
    p.circle(sx, sy + 5.2, 1.4, "#FFFFFF")


def scene_sinaloa(p):
    """9. Sinaloa Capture: desert twilight mountains, black helicopter + searchlight + handcuffs."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.74, "#3A2454", "#EC8244")
    p.glow(w * 0.58, h * 0.72, 48, "#FFC266", 140)
    ridge(p, h * 0.65, h * 0.11, 1.4, 1.0, "#6E3F4B", y_floor=h * 0.85)
    ridge(p, h * 0.78, h * 0.05, 2.2, 0.2, "#3F242D", y_floor=h)
    p.rect(0, h * 0.82, w, h, "#23151B")

    # Black military helicopter upper-right with sweeping searchlight cone (clear of banner)
    hx, hy = w * 0.81, h * 0.36
    p.d.polygon(p._pts([(hx - 6, hy + 4.5), (hx - 32, h * 0.88), (hx + 8, h * 0.88), (hx + 3, hy + 4.5)]),
                fill=rgb("#FFF2B8", 78))
    p.ellipse(hx, hy, 11.0, 4.6, "#15191E")
    p.poly([(hx + 7, hy - 1.8), (hx + 25, hy - 1.2), (hx + 25, hy + 0.5), (hx + 7, hy + 1.8)], "#15191E")
    p.poly([(hx + 23, hy - 5.5), (hx + 26, hy - 5.5), (hx + 25, hy + 1), (hx + 22, hy + 1)], "#15191E")
    p.ellipse(hx - 5.5, hy - 1, 3.8, 2.2, "#F9CC78")
    p.line([(hx - 17, hy - 6.8), (hx + 17, hy - 6.0)], "#15191E", 1.1)
    p.line([(hx, hy - 4.5), (hx, hy - 6.4)], "#15191E", 1.2)
    p.line([(hx - 6, hy + 5.8), (hx + 6, hy + 5.8)], "#15191E", 0.9)

    # Iconic bright silver interlocking handcuffs in lower-left clear zone
    cx1, cy1 = w * 0.19, h * 0.68
    cx2, cy2 = w * 0.39, h * 0.68
    p.circle(cx1, cy1, 11.8, None, "#EEF2F6", 2.8)
    p.circle(cx1, cy1, 11.8, None, "#2A3038", 0.6)
    p.circle(cx2, cy2, 11.8, None, "#EEF2F6", 2.8)
    p.circle(cx2, cy2, 11.8, None, "#2A3038", 0.6)
    p.line([(cx1 + 10.5, cy1 - 2.5), (cx2 - 10.5, cy2 - 2.5)], "#D0D7DF", 2.2)
    # Police red/blue flash accents on desert horizon
    p.glow(w * 0.56, h * 0.80, 10, "#FF2D2D", 190, steps=8)
    p.glow(w * 0.63, h * 0.80, 10, "#2B7FFF", 190, steps=8)


def scene_eu_indonesia(p):
    """10. EU-Indonesia CEPA: EU blue/gold star ring + Indonesia red/white + gold trade medallion."""
    w, h = p.w, p.h
    # Left half: EU royal blue
    p.rect(0, 0, w * 0.5, h, "#003399")
    # Right half: Indonesia red over white
    p.rect(w * 0.5, 0, w, h * 0.5, "#CE1126")
    p.rect(w * 0.5, h * 0.5, w, h, "#F8F8F6")
    p.line([(w * 0.5, 0), (w * 0.5, h)], "#14181F", 0.8)

    # 12 crisp EU gold stars cleanly in lower-left (below top-left banner)
    ex, ey, er = w * 0.24, h * 0.69, 13.5
    for k in range(12):
        a = math.radians(-90 + k * 30)
        star5(p, ex + math.cos(a) * er, ey + math.sin(a) * er, 2.4, "#FFCC00")

    # Indonesia divider
    p.rect(w * 0.5, h * 0.49, w, h * 0.51, "#B51022")

    # Central bold gold trade medallion clearly below banner (top ~28px vs banner bottom 23px)
    mx, my, mr = w * 0.52, h * 0.65, 14.5
    p.circle(mx + 1, my + 1.5, mr + 1, (0, 0, 0, 75))
    p.circle(mx, my, mr, "#F4C430", "#14181F", 1.2)
    p.circle(mx, my, mr - 2.3, None, "#FFF4C2", 0.7)
    # Right arrow (top)
    p.line([(mx - 7.5, my - 3.4), (mx + 5.0, my - 3.4)], "#14181F", 2.0)
    p.poly([(mx + 9.0, my - 3.4), (mx + 3.8, my - 6.8), (mx + 3.8, my)], "#14181F")
    # Left arrow (bottom)
    p.line([(mx + 7.5, my + 3.4), (mx - 5.0, my + 3.4)], "#14181F", 2.0)
    p.poly([(mx - 9.0, my + 3.4), (mx - 3.8, my), (mx - 3.8, my + 6.8)], "#14181F")


def scene_iran_launcher(p):
    """11. Iran Underground Dual-Missile Launcher: bunker arch + dual rails + Iran flag accent."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#161B22", "#28303B")
    # Reinforced concrete cavern tunnel arch
    for rx, ry, col in [(w * 0.62, h * 0.88, "#3B4452"),
                        (w * 0.54, h * 0.76, "#252C36"),
                        (w * 0.44, h * 0.64, "#1C222B")]:
        p.ellipse(w * 0.56, h * 0.96, rx, ry, col, "#556173", 1.0)
    # Warm bunker ceiling spotlights (right of banner)
    for lx in (w * 0.64, w * 0.84):
        p.glow(lx, h * 0.24, 15, "#FFB84D", 130, steps=10)
        p.circle(lx, h * 0.24, 2.0, "#FFE3A3")
    # Concrete floor
    p.rect(0, h * 0.80, w, h, "#303844")

    # Mobile TEL truck + twin angled ballistic missiles clearly emerging right of banner
    tx, ty = w * 0.62, h * 0.82
    p.rect(tx - 34, ty - 10, tx + 30, ty - 2, "#4B5648", "#1F261E", 0.8, r=1.5)
    p.rect(tx + 20, ty - 15, tx + 32, ty - 2, "#596655", "#1F261E", 0.8, r=1.5)
    p.rect(tx + 24, ty - 13, tx + 30, ty - 9, "#9CC3DC")
    for wx in (tx - 26, tx - 13, tx + 2, tx + 22):
        p.circle(wx, ty - 1, 4.0, "#14181F")
        p.circle(wx, ty - 1, 1.5, "#88929E")

    # Dual angled missiles on launch rails (clear of top-left banner x=4..122, y=4..23)
    ang = math.radians(-24)
    ca, sa = math.cos(ang), math.sin(ang)
    for off_x, off_y in ((0, -5), (4, 3)):
        bx0, by0 = tx - 22 + off_x, ty - 11 + off_y
        length = 50.0
        bx1, by1 = bx0 + ca * length, by0 + sa * length
        p.line([(bx0 - 3, by0 + 3.5), (bx1 - 5, by1 + 3.5)], "#6D7888", 1.7)
        p.line([(bx0, by0), (bx1, by1)], "#E2E6EA", 4.2)
        nx, ny = bx1 + ca * 7.5, by1 + sa * 7.5
        px, py = -sa * 2.3, ca * 2.3
        p.poly([(nx, ny), (bx1 + px, by1 + py), (bx1 - px, by1 - py)], "#C83228")
        p.poly([(bx0 - ca * 2 + px * 1.8, by0 - sa * 2 + py * 1.8),
                (bx0 - ca * 2 - px * 1.8, by0 - sa * 2 - py * 1.8),
                (bx0 + ca * 6, by0 + sa * 6)], "#5A6558")

    # Subtle Iran flag accent stripe bottom-left
    fx0, fy0 = 6, h - 11
    p.rect(fx0, fy0, fx0 + 36, fy0 + 2.4, "#239F40")
    p.rect(fx0, fy0 + 2.4, fx0 + 36, fy0 + 4.8, "#FFFFFF")
    p.rect(fx0, fy0 + 4.8, fx0 + 36, fy0 + 7.2, "#DA0000")


def scene_geneva_ai(p):
    """12. Geneva UN 'Killer Robot' Talks: UN blue, robot/drone visor + deadlock slash + 2028 target."""
    w, h = p.w, p.h
    p.vgrad(0, h, "#2D6BB0", "#163F73")
    # Faint Palais des Nations columns on left
    for k in range(5):
        x = 10 + k * 9
        p.rect(x, h * 0.44, x + 4, h, rgb("#FFFFFF", 28))

    # Sleek autonomous combat robot head + red optical visor cleanly below banner (antenna at y=28)
    rx, ry = w * 0.42, h * 0.72
    p.rect(rx - 14, ry - 14, rx + 14, ry + 3, "#DCE3EC", "#58687A", 0.8, r=3.5)
    p.rect(rx - 10, ry - 9.5, rx + 10, ry - 3.5, "#151D28", r=1.8)
    p.rect(rx - 7.5, ry - 7.8, rx + 7.5, ry - 5.2, "#FF3B30", r=0.9)
    p.line([(rx, ry - 14), (rx, ry - 19)], "#9DB0C4", 1.1)
    p.circle(rx, ry - 19.5, 2.0, "#FF3B30")
    p.rect(rx - 20, ry + 5, rx + 20, h + 2, "#B7C3D0", "#58687A", 0.8, r=4)

    # Diagonal crimson deadlock slash across robot
    p.line([(rx - 18, ry - 13), (rx + 18, ry + 11)], "#FF3B30", 2.1)

    # Crisp white calendar tag showing 2028 on right (clear of banner and bottom chip)
    cx0, cy0 = w * 0.71, h * 0.14
    p.rect(cx0 + 1.5, cy0 + 1.5, cx0 + 46.5, cy0 + 38.5, (0, 0, 0, 75), r=2)
    p.rect(cx0, cy0, cx0 + 45, cy0 + 37, "#FFFFFF", r=2)
    p.rect(cx0, cy0, cx0 + 45, cy0 + 10.5, "#B52323", r=2)
    p.rect(cx0, cy0 + 6.5, cx0 + 45, cy0 + 10.5, "#B52323")
    p.text(cx0 + 22.5, cy0 + 5.4, "TARGET", 5.8, "#FFFFFF")
    p.text(cx0 + 22.5, cy0 + 24.5, "2028", 13.8, "#14181F")


def scene_mcg(p):
    """13. MCG Record 188 Chase: emerald oval, cricket bat & crimson ball, scoreboard 188."""
    w, h = p.w, p.h
    p.vgrad(0, h * 0.44, "#0C1B36", "#213D6B")
    # Stadium floodlight towers
    for x in (w * 0.08, w * 0.92):
        p.line([(x, h * 0.48), (x, h * 0.10)], "#9EABBC", 1.3)
        p.rect(x - 6, h * 0.05, x + 6, h * 0.12, "#FFF7D2")
        p.glow(x, h * 0.09, 22, "#FFF2A8", 130, steps=10)

    # Emerald MCG cricket oval
    p.ellipse(w * 0.5, h * 0.76, w * 0.62, h * 0.48, "#228B3E")
    for k in range(1, 5):
        p.ellipse(w * 0.5, h * 0.76, w * 0.62 * (1 - k * 0.18), h * 0.48 * (1 - k * 0.18),
                  None, rgb("#36A852", 140), 1.8)
    # Cricket pitch & stumps
    p.rect(w * 0.46, h * 0.56, w * 0.54, h * 0.96, "#DEC999")
    for dx in (-2.0, 0, 2.0):
        p.line([(w * 0.50 + dx, h * 0.64), (w * 0.50 + dx, h * 0.57)], "#FFFFFF", 0.7)

    # Bold wooden cricket bat + struck crimson ball cleanly below banner
    p.poly([(w * 0.16, h * 0.94), (w * 0.31, h * 0.59), (w * 0.37, h * 0.62), (w * 0.22, h * 0.97)],
           "#E5BF7E", "#7B5B2A", 0.9)
    p.line([(w * 0.34, h * 0.60), (w * 0.40, h * 0.49)], "#22262E", 2.5)
    # Motion arc + crisp red cricket ball cleanly in open green/sky gap (y=36, clear of banner y=23)
    for k in range(5):
        t = k / 4
        bx = w * (0.41 + 0.28 * t)
        by = h * (0.69 - 0.15 * t - 0.06 * math.sin(t * math.pi))
        p.circle(bx, by, 1.0 + t * 0.55, rgb("#FFFFFF", 95 + k * 25))
    p.circle(w * 0.73, h * 0.54, 5.2, "#C8102E", "#FFFFFF", 0.6)
    p.arc(w * 0.73, h * 0.54, 3.5, 110, 250, "#FFFFFF", 0.65)

    # Crisp dark scoreboard "188" on upper-right
    p.rect(w * 0.74, h * 0.10, w * 0.97, h * 0.42, "#11161D", "#F0C842", 0.9, r=1.5)
    p.text(w * 0.855, h * 0.265, "188", 11.5, "#FFD23F")


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
