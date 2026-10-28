"""Candyland design system: palettes, ramps, tileable noise, small canvas."""
import math
import random


def stable_seed(text):
    """Stable 31-bit seed for reproducible texture variation.

    Python's built-in hash() is salted per process, so using it for texture
    seeds made two builds of the same pack produce different block and UI art.
    FNV-1a keeps rebuilds byte-for-byte deterministic.
    """
    value = 2166136261
    for byte in str(text).encode("utf-8"):
        value ^= byte
        value = (value * 16777619) & 0xFFFFFFFF
    return value & 0x7FFFFFFF


# ------------------------------------------------------------------ colour

def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else v


def hex_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return "#%02x%02x%02x" % tuple(clamp(int(v)) for v in c[:3])


def mix(a, b, t):
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def at_luma(c, target):
    base = luma(c)
    if base <= 0.01:
        return (target, target, target)
    r = target / base
    return tuple(clamp(int(v * r)) for v in c)


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6.0
    elif mx == g:
        h = (b - r) / d + 2.0
    else:
        h = (r - g) / d + 4.0
    h /= 6.0
    s = 0.0 if mx == 0 else d / mx
    return h, s, mx


def hsv_to_rgb(h, s, v):
    h = h % 1.0
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6
    r, g, b = [(v, t, p), (q, v, p), (p, v, t),
               (p, q, v), (t, p, v), (v, p, q)][i]
    return (int(r * 255 + .5), int(g * 255 + .5), int(b * 255 + .5))


# ------------------------------------------------------------------ ramps

class Ramp:
    """Six discrete candy tones, shadow -> highlight."""

    __slots__ = ("tones",)

    def __init__(self, tones):
        self.tones = tones

    def at(self, t):
        if t <= 0.0:
            return self.tones[0]
        if t >= 1.0:
            return self.tones[-1]
        return self.tones[int(t * (len(self.tones) - 1) + 0.5)]

    def __getitem__(self, i):
        return self.tones[i]


# Dark/light anchors used to build every ramp.  They are deliberately not
# pure black / white: candy shadows are plum or chocolate, highlights are
# cream.  That single rule is what makes 600 generated tiles feel like one
# material family.
DARK_ANCHOR = hex_rgb("#2a1626")
WARM_LIGHT = hex_rgb("#fff6e6")
COOL_LIGHT = hex_rgb("#fff3fb")


def make_ramp(base, spread=0.45, shadow=None, light=None, cool=False):
    b = base if isinstance(base, tuple) else hex_rgb(base)
    h0, s0, v0 = rgb_to_hsv(*b)
    b = hsv_to_rgb(h0, min(1.0, s0 * 1.18), v0)
    if shadow is not None and isinstance(shadow, str):
        shadow = hex_rgb(shadow)
    if light is not None and isinstance(light, str):
        light = hex_rgb(light)
    L = luma(b)
    lo = max(4, L - 82 * spread)
    hi = min(255, L + 72 * spread)
    targets = [lo + (hi - lo) * f for f in
               (0.0, 0.12, 0.24, 0.38, 0.52, 0.66, 0.82, 1.0)]
    dark = shadow or DARK_ANCHOR
    lite = light or (COOL_LIGHT if cool else WARM_LIGHT)
    hues = [mix(dark, b, 0.16), mix(dark, b, 0.34), mix(dark, b, 0.52),
            mix(dark, b, 0.72), b, mix(b, lite, 0.28),
            mix(b, lite, 0.52), mix(b, lite, 0.76)]
    tones = [at_luma(h, t) for h, t in zip(hues, targets)]
    # enforce strictly increasing luma after integer truncation
    for i in range(1, 6):
        prev = luma(tones[i - 1])
        if luma(tones[i]) <= prev:
            tones[i] = at_luma(tones[i], min(255, prev + 2))
    return Ramp(tones)


# ------------------------------------------------------------------ palettes

# 16 dye names -> candy colour, in Bedrock order.
DYE_COLORS = {
    "white":       ("marshmallow",   "#fff7f8"),
    "orange":      ("orange_sherbet", "#ffb36b"),
    "magenta":     ("bubblegum",     "#f27ac0"),
    "light_blue":  ("cotton_blue",   "#9adcf7"),
    "yellow":      ("lemon_drop",    "#ffe18a"),
    "lime":        ("sour_apple",    "#c4e97a"),
    "pink":        ("cotton_candy",  "#f7a8c4"),
    "gray":        ("silver_lilac",  "#b9b2c9"),
    "silver":      ("silver_sugar",  "#dcd5e4"),
    "cyan":        ("blue_raspberry", "#86d9f7"),
    "purple":      ("grape_taffy",   "#b58be8"),
    "blue":        ("blueberry",     "#7d9bf0"),
    "brown":       ("milk_chocolate", "#8b5a44"),
    "green":       ("mint",          "#8fe3bf"),
    "red":         ("cherry",        "#ef5d76"),
    "black":       ("licorice",      "#3a2c3e"),
}
# Bedrock sometimes calls light gray "silver" and dark gray "gray".
DYE_ALIASES = {"light_gray": "silver", "dark_gray": "gray"}

# Named materials.  `base` is the midtone; `shadow` / `light` bias the ramp.
MATERIALS = {
    "rock_candy":       dict(base="#f0d9e7", shadow="#6c3e59", light="#fff8fd"),
    "rock_candy_pink":  dict(base="#f3bcd5", shadow="#8a3158", light="#fff4fa"),
    "rock_candy_mint":  dict(base="#bfeedd", shadow="#2f6e62", light="#f4fffb"),
    "rock_candy_blue":  dict(base="#c4e9f7", shadow="#326b83", light="#f4fdff"),
    "rock_candy_lilac": dict(base="#d9c9f2", shadow="#5f4387", light="#fbf7ff"),
    "white_chocolate":  dict(base="#f1e0c9", shadow="#7c5a39", light="#fffaf0"),
    "vanilla":          dict(base="#f8ecd0", shadow="#8a6c45", light="#fffdf4"),
    "meringue":         dict(base="#fbf1de", shadow="#a4825c", light="#ffffff"),
    "sugar":            dict(base="#f2e4bd", shadow="#8f7440", light="#fffcef"),
    "sugar_pink":       dict(base="#f6d2c6", shadow="#955b4f", light="#fff7f2"),
    "chocolate":        dict(base="#7a4a34", shadow="#2a1712", light="#c9936f"),
    "milk_chocolate":   dict(base="#9a6448", shadow="#3a2118", light="#d8a47e"),
    "dark_chocolate":   dict(base="#4a2d24", shadow="#160d0b", light="#8e6250"),
    "chocolate_chip":   dict(base="#2f1d1a", shadow="#0f0908", light="#5e4036"),
    "caramel":          dict(base="#d99a4e", shadow="#6a3a16", light="#ffd79a"),
    "honey":            dict(base="#f0b64e", shadow="#7a4a11", light="#ffe9a8"),
    "wafer":            dict(base="#e8c28a", shadow="#7d542c", light="#fff0cc"),
    "cookie":           dict(base="#c9915c", shadow="#5c351b", light="#f3cfa2"),
    "strawberry":       dict(base="#f26d7d", shadow="#7e1e36", light="#ffc1c8"),
    "cherry":           dict(base="#e84763", shadow="#6b1028", light="#ffb3c0"),
    "raspberry":        dict(base="#d63d6a", shadow="#5c0f2e", light="#ffadc4"),
    "cotton_candy":     dict(base="#f7a8c4", shadow="#8e3457", light="#ffe4ef"),
    "bubblegum":        dict(base="#f27ac0", shadow="#77155b", light="#ffc7ee"),
    "mint":             dict(base="#8fe3bf", shadow="#21705c", light="#e0fff4"),
    "sour_apple":       dict(base="#c4e97a", shadow="#4d721c", light="#f4ffd2"),
    "lemon_drop":       dict(base="#ffe18a", shadow="#8f6b15", light="#fffbd9"),
    "orange_sherbet":   dict(base="#ffb36b", shadow="#8a4517", light="#ffe0bd"),
    "blue_raspberry":   dict(base="#86d9f7", shadow="#1f617e", light="#dcf8ff"),
    "blueberry":        dict(base="#7d9bf0", shadow="#263a83", light="#dbe4ff"),
    "grape_taffy":      dict(base="#b58be8", shadow="#4a2478", light="#eadbff"),
    "lavender":         dict(base="#cdb8f2", shadow="#554082", light="#f6efff"),
    "marshmallow":      dict(base="#fff7f8", shadow="#b39aa4", light="#ffffff"),
    "licorice":         dict(base="#3a2c3e", shadow="#0c0810", light="#6d5a72"),
    "silver_sugar":     dict(base="#dcd5e4", shadow="#5f5873", light="#ffffff"),
    "silver_lilac":     dict(base="#b9b2c9", shadow="#4f4862", light="#f4f0fa"),
    "cotton_blue":      dict(base="#9adcf7", shadow="#2c6480", light="#eafaff"),
    "gold_wrap":        dict(base="#f5c84c", shadow="#7b5109", light="#fff1a8"),
    "copper_wrap":      dict(base="#e08a5a", shadow="#6e2f19", light="#ffcfb0"),
    "pistachio":        dict(base="#b7d98a", shadow="#4a6b2c", light="#edffd2"),
    "red_velvet":       dict(base="#a83a4a", shadow="#3d0d18", light="#e88992"),
    "grape_jelly":      dict(base="#6a3e8e", shadow="#241031", light="#b596d4"),
    "blackberry_jelly": dict(base="#3b2a52", shadow="#0b0714", light="#7a62a0"),
    "peanut_brittle":   dict(base="#c9955c", shadow="#57331b", light="#f7d7a9"),
    "cookies_cream":    dict(base="#d8cfc7", shadow="#4c3f3a", light="#ffffff"),
    "pudding":          dict(base="#8b5a3c", shadow="#2e1a10", light="#d3a079"),
    "fudge":            dict(base="#6b4230", shadow="#20110c", light="#b98763"),
    "honeycomb":        dict(base="#e9b44c", shadow="#6a3f0a", light="#ffe6a1"),
    "sponge_cake":      dict(base="#f4d47c", shadow="#8a5d18", light="#fff6c9"),
    "melon_taffy":      dict(base="#f27c8d", shadow="#6e1b2d", light="#ffd0d7"),
    "gummy_green":      dict(base="#77d48d", shadow="#1e5e33", light="#d9ffdf"),
    "gummy_blue":       dict(base="#6fcbe3", shadow="#174e60", light="#d7fbff"),
    "gummy_pink":       dict(base="#f28fb4", shadow="#7a2048", light="#ffdce9"),
    "gummy_purple":     dict(base="#b483e0", shadow="#432266", light="#eeddff"),
    "gummy_orange":     dict(base="#f7a45e", shadow="#7d3a12", light="#ffe1c2"),
    "gummy_yellow":     dict(base="#f7d96b", shadow="#7d5d0b", light="#fff4b8"),
    "sea_glass":        dict(base="#a7e3d8", shadow="#2f6f68", light="#ecfffb"),
    "sugar_glass":      dict(base="#d8f1ff", shadow="#5c87a0", light="#ffffff"),
    "ice_blue":         dict(base="#b8e2f7", shadow="#3d6f8c", light="#f0fbff"),
    "snow_fluff":       dict(base="#f7fbff", shadow="#a4b6c8", light="#ffffff"),
    "soul_fudge":       dict(base="#b9a58a", shadow="#4c3d2c", light="#f1e4c9"),
    "magma_jam":        dict(base="#e2633f", shadow="#631505", light="#ffb36e"),
    "lemon_meringue":   dict(base="#f5e6a8", shadow="#8d7932", light="#fffce0"),
    "purpur_taffy":     dict(base="#c59acb", shadow="#5a3364", light="#f3dbf7"),
    "prismarine_jelly": dict(base="#8fdfc5", shadow="#246b5a", light="#e3fff8"),
    "sculk_jam":        dict(base="#3a5a86", shadow="#0c1729", light="#75a6d6"),
    "mud_pudding":      dict(base="#7a5a44", shadow="#2a1c13", light="#c79c7a"),
    "clay_lavender":    dict(base="#b8b7d6", shadow="#4c4b6e", light="#eae9ff"),
    "sulfur_sherbet":   dict(base="#f2dc6a", shadow="#827016", light="#fff9c2"),
    "resin_caramel":    dict(base="#d98f3a", shadow="#6b390b", light="#ffd193"),
    "cactus_gummy":     dict(base="#79c86a", shadow="#255f1e", light="#d7ffcf"),
    "mushroom_cream":   dict(base="#f2e6d5", shadow="#8c6f59", light="#fffaf2"),
    "bone_white":       dict(base="#efe6cf", shadow="#82745c", light="#fffdf5"),
    "obsidian_jelly":   dict(base="#2c2340", shadow="#07040d", light="#6b5791"),
    "ancient_chocolate": dict(base="#4a332e", shadow="#160c0a", light="#9c735c"),
    "netherite_dark":   dict(base="#3d3238", shadow="#0d090c", light="#7d6b72"),
    "emerald_candy":    dict(base="#57d68b", shadow="#12683b", light="#c6ffe1"),
    "diamond_candy":    dict(base="#7de8e1", shadow="#1e7476", light="#d7fffd"),
    "lapis_candy":      dict(base="#5b7de0", shadow="#1d2d7a", light="#c5d3ff"),
    "redstone_candy":   dict(base="#e04444", shadow="#650e12", light="#ffa3a3"),
    "quartz_candy":     dict(base="#f4eee4", shadow="#9a8a76", light="#ffffff"),
    "gold_candy":       dict(base="#f7d45a", shadow="#7d5b0a", light="#fff5b0"),
    "iron_candy":       dict(base="#d9d7e5", shadow="#666077", light="#ffffff"),
    "copper_candy":     dict(base="#e8915b", shadow="#71300f", light="#ffd2b4"),
    "amethyst_candy":   dict(base="#b083e8", shadow="#431e72", light="#ecd7ff"),
    "coal_candy":       dict(base="#332b38", shadow="#09060b", light="#6d5d73"),
    "raw_candy":        dict(base="#d8a37c", shadow="#6b3e25", light="#ffe1c7"),
    "bark_wafer":       dict(base="#cfa06a", shadow="#5e351b", light="#f5d5a8"),
    "bark_chocolate":   dict(base="#6a4431", shadow="#1f110b", light="#b98463"),
    "bark_white":       dict(base="#f4e8d7", shadow="#9b8068", light="#ffffff"),
    "bark_cherry":      dict(base="#f2a2b8", shadow="#8c2f4d", light="#ffe1ea"),
    "bark_red":         dict(base="#b84a54", shadow="#3e0d14", light="#f08d92"),
    "bark_blue":        dict(base="#5c8f9e", shadow="#183a43", light="#b9e4ea"),
    "bark_green":       dict(base="#8fa55c", shadow="#3d4a1e", light="#e0edb8"),
}


def get_ramp(key, spread=0.72):
    if isinstance(key, Ramp):
        return key
    if key.startswith("#"):
        return make_ramp(key, spread)
    p = MATERIALS[key]
    return make_ramp(p["base"], spread, p.get("shadow"), p.get("light"))


def dye_ramp(dye):
    dye = DYE_ALIASES.get(dye, dye)
    key = DYE_COLORS[dye][0]
    return get_ramp(key)


# ------------------------------------------------------------------ noise

class ValueNoise:
    """Deterministic value noise.  All lattices wrap, so tiles are seamless."""

    def __init__(self, seed=1):
        self.seed = seed & 0xffffffff

    def _h(self, x, y):
        n = (x * 374761393 + y * 668265263 + self.seed * 2246822519) & 0xffffffff
        n = (n ^ (n >> 13)) * 1274126177 & 0xffffffff
        return ((n ^ (n >> 16)) & 0xffffffff) / 4294967295.0

    def at(self, x, y):
        xi, yi = int(math.floor(x)), int(math.floor(y))
        xf, yf = x - xi, y - yi
        u = xf * xf * (3 - 2 * xf)
        v = yf * yf * (3 - 2 * yf)
        a = self._h(xi, yi)
        b = self._h(xi + 1, yi)
        c = self._h(xi, yi + 1)
        d = self._h(xi + 1, yi + 1)
        return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v

    def fbm(self, x, y, octaves=4, gain=0.5, period=0):
        total = 0.0
        amp = 1.0
        norm = 0.0
        freq = 1
        for _ in range(octaves):
            if period:
                xx = (x * freq) % (period * freq)
                yy = (y * freq) % (period * freq)
            else:
                xx, yy = x * freq, y * freq
            total += self.at(xx, yy) * amp
            norm += amp
            amp *= gain
            freq *= 2
        return total / norm

    def worley_full(self, x, y, period=8):
        xi, yi = int(math.floor(x)), int(math.floor(y))
        best = 1e9
        best_dx = best_dy = 0.0
        second = 1e9
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                cx = xi + ox
                cy = yi + oy
                # wrap cell hash coordinates
                hx = cx % period
                hy = cy % period
                px = cx + self._h(hx, hy)
                py = cy + self._h(hx + 91, hy + 57)
                d = (px - x) ** 2 + (py - y) ** 2
                if d < best:
                    second = best
                    best = d
                    best_dx = px - x
                    best_dy = py - y
                elif d < second:
                    second = d
        d = math.sqrt(best)
        edge = math.sqrt(second) - d
        return best_dx, best_dy, d, max(0.0, min(1.0, edge))


# ------------------------------------------------------------------ canvas

class Canvas:
    __slots__ = ("w", "h", "px")

    def __init__(self, w, h=None, fill=(0, 0, 0, 0)):
        self.w, self.h = w, h if h is not None else w
        self.px = bytearray(bytes(fill) * (self.w * self.h))

    def set(self, x, y, c, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 4
            self.px[i] = int(clamp(c[0])); self.px[i + 1] = int(clamp(c[1]))
            self.px[i + 2] = int(clamp(c[2])); self.px[i + 3] = int(clamp(a))

    def get(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return (0, 0, 0, 0)
        i = (y * self.w + x) * 4
        return tuple(self.px[i:i + 4])

    def blend(self, x, y, c, a):
        if not (0 <= x < self.w and 0 <= y < self.h) or a <= 0:
            return
        i = (y * self.w + x) * 4
        da = self.px[i + 3] / 255.0
        sa = (a / 255.0)
        oa = sa + da * (1 - sa)
        if oa <= 0:
            return
        for k in range(3):
            self.px[i + k] = clamp(int((c[k] * sa + self.px[i + k] * da * (1 - sa)) / oa))
        self.px[i + 3] = clamp(int(oa * 255))

    def fill(self, c, a=255):
        for y in range(self.h):
            for x in range(self.w):
                self.set(x, y, c, a)

    def rect(self, x0, y0, x1, y1, c, a=255):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, c, a)

    def disc(self, cx, cy, r, c, a=255):
        r2 = r * r
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r2:
                    self.set(x, y, c, a)

    def blaze(self, x, y, dx, dy, length, c, a=255):
        for i in range(length):
            self.set(x + dx * i, y + dy * i, c, a)

    def outline_alpha(self, c, threshold=0):
        out = Canvas(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                if self.get(x, y)[3] > threshold:
                    out.set(x, y, c, 255)
        return out


def q(t, n=6):
    if t <= 0:
        return 0
    if t >= 1:
        return n - 1
    return int(t * (n - 1) + 0.5)


def tile_value_noise(w, h, seed, scale=4.0, octaves=4, gain=0.55):
    n = ValueNoise(seed)
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            out[y][x] = n.fbm(x * scale / w, y * scale / h, octaves, gain,
                              period=int(scale))
    return out


def sprinkle(c, x, y, colors, seed, density=0.035, length=2, size=2):
    """Draw tiny candy sprinkles, wrapping at the tile edge."""
    rnd = random.Random(seed)
    for _ in range(int(c.w * c.h * density / max(1, length))):
        xx = rnd.randrange(c.w)
        yy = rnd.randrange(c.h)
        col = colors[rnd.randrange(len(colors))]
        horiz = rnd.random() < 0.5
        for k in range(length):
            for j in range(size):
                px = (xx + (k if horiz else 0)) % c.w
                py = (yy + (0 if horiz else k)) % c.h
                if size == 2:
                    for jj in range(2):
                        c.set((px + (0 if horiz else jj)) % c.w,
                              (py + (jj if horiz else 0)) % c.h, col)


def heart(c, x, y, col, shade=None, hi=None):
    mask = [
        ".XX.XX.",
        "XXXXXXX",
        "XXXXXXX",
        ".XXXXX.",
        "..XXX..",
        "...X...",
    ]
    for yy, row in enumerate(mask):
        for xx, ch in enumerate(row):
            if ch == "X":
                cc = col
                if shade and yy >= 4 and xx >= 3:
                    cc = shade
                if hi and yy <= 1 and xx <= 2:
                    cc = hi
                c.set(x + xx, y + yy, cc)


def star(c, cx, cy, col, size=2):
    for i in range(-size, size + 1):
        c.set(cx + i, cy, col)
        c.set(cx, cy + i, col)
    if size >= 2:
        c.set(cx - 1, cy - 1, col)
        c.set(cx + 1, cy - 1, col)
        c.set(cx - 1, cy + 1, col)
        c.set(cx + 1, cy + 1, col)


def worley_cell(self, x, y, period=8):
    """Worley with the winning cell hash, for per-pebble colours."""
    xi, yi = int(math.floor(x)), int(math.floor(y))
    best = 1e9
    second = 1e9
    bdx = bdy = 0.0
    bhash = 0.0
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = xi + ox, yi + oy
            hx, hy = cx % period, cy % period
            px = cx + self._h(hx, hy)
            py = cy + self._h(hx + 91, hy + 57)
            d = (px - x) ** 2 + (py - y) ** 2
            if d < best:
                second = best
                best = d
                bdx, bdy = px - x, py - y
                bhash = self._h(hx * 7 + 13, hy * 11 + 29)
            elif d < second:
                second = d
    d = math.sqrt(best)
    edge = math.sqrt(second) - d
    return bdx, bdy, d, max(0.0, min(1.0, edge)), bhash

ValueNoise.worley_cell = worley_cell
