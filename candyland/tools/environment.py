"""Hand-authored sky, weather, damage-overlay and atlas art.

Everything here is drawn from scratch with the candy palette.  Dimensions and
sprite-sheet layouts match the vanilla files exactly so the engine's UV maths
are untouched.
"""
import math
import random

from candy import (Canvas, ValueNoise, clamp, get_ramp, hex_rgb, luma, mix,
                   rgb_to_hsv)


# ------------------------------------------------------------------ helpers

def glow(c, cx, cy, r, colour, alpha=90, power=2.0):
    """Soft radial halo, clipped to the canvas."""
    for y in range(max(0, int(cy - r) - 1), min(c.h, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(c.w, int(cx + r) + 2)):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            if d >= r:
                continue
            a = int(alpha * (1.0 - d / r) ** power)
            if a:
                c.blend(x, y, colour, a)


def primitive_disc(c, cx, cy, r, colour, alpha=255):
    for y in range(max(0, int(cy - r) - 1), min(c.h, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(c.w, int(cx + r) + 2)):
            if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r:
                c.set(x, y, colour, alpha)


def _craters():
    return [(-2.3, -1.5, 1.5), (2.2, 1.9, 1.3), (-0.8, 2.8, 1.0),
            (3.1, -2.2, .9), (-3.4, 1.7, .8), (0.9, -3.0, .7),
            (1.4, 0.4, .6)]


# ------------------------------------------------------------------ sun

def sun(vivid=False, size=32):
    c = Canvas(size, size)
    cx = cy = size / 2.0
    lemon = hex_rgb("#ffe18a")
    cream = hex_rgb("#fffbe8")
    orange = hex_rgb("#ffb36b")
    caramel = hex_rgb("#d99a4e")
    pink = hex_rgb("#f7a8c4")
    r_disc = 8.4 if not vivid else 9.0

    glow(c, cx, cy, 15.7, pink, 42, 2.4)
    glow(c, cx, cy, 13.5, lemon, 100, 2.0)

    # eight soft rays behind the disc
    rays = 8
    for k in range(rays):
        a = k * math.pi * 2 / rays + (0.2 if vivid else 0.0)
        for d in range(8, 14):
            if d > 12 and not vivid:
                continue
            rx = cx + math.cos(a) * d
            ry = cy + math.sin(a) * d
            w = 1 if d < 10 else 1
            alpha = int(150 * (1 - (d - 8) / 7.0))
            for ox in range(-w, w + 1):
                for oy in range(-w, w + 1):
                    if ox * ox + oy * oy <= w * w:
                        c.blend(int(rx) + ox, int(ry) + oy,
                                caramel if d > 9 else orange, max(0, alpha))

    for y in range(size):
        for x in range(size):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            scallop = r_disc + (0.8 if not vivid else 1.2) * math.cos(rays * ang)
            if d <= scallop:
                if d > scallop - 2.0:
                    col = orange
                elif d > 5.1:
                    col = lemon
                elif d > 3.4:
                    col = cream
                else:
                    col = (255, 255, 248)
                c.set(x, y, col, 255)
    # sugar glints
    for sx, sy in ((12, 12), (19, 13), (14, 20), (21, 19)):
        if c.get(sx, sy)[3]:
            c.set(sx, sy, cream)
    return c


# ------------------------------------------------------------------ moon

def moon_phases():
    c = Canvas(128, 64)
    phases = [(1.0, -1), (.75, -1), (.5, -1), (.25, -1),
              (0.0, -1), (.25, 1), (.5, 1), (.75, 1)]
    cream = hex_rgb("#fff8e8")
    crumb = hex_rgb("#e7d6c4")
    crater = hex_rgb("#cbb7d8")
    crater_dk = hex_rgb("#a88cb9")
    dark = hex_rgb("#2b1a33")
    sparkle = hex_rgb("#fff3fb")
    for idx, (frac, side) in enumerate(phases):
        ox = (idx % 4) * 32
        oy = (idx // 4) * 32
        cx, cy = ox + 16.0, oy + 16.0
        # halo
        for y in range(oy, oy + 32):
            for x in range(ox, ox + 32):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if 7.5 < d < 15.5:
                    a = int(58 * (1 - (d - 7.5) / 8.0) ** 2.2)
                    c.blend(x, y, hex_rgb("#cfc4ff"), a)
        r = 7.4
        for y in range(oy + 8, oy + 25):
            for x in range(ox + 8, ox + 25):
                dx, dy = x + .5 - cx, y + .5 - cy
                if dx * dx + dy * dy > r * r:
                    continue
                nx, ny = dx / r, dy / r
                semi = math.sqrt(max(0.0, 1 - ny * ny))
                k = 1.0 - 2.0 * frac
                lit = (side * nx) >= k * semi
                if not lit:
                    c.set(x, y, dark, 178)
                    continue
                # cookie surface: cream with crumb mottling and craters
                n = ValueNoise(70 + idx)
                m = n.fbm(x * .55, y * .55, 2, .5)
                col = mix(cream, crumb, .18 + .22 * m)
                for ccx, ccy, cr in _craters():
                    dd = math.hypot(dx - ccx, dy - ccy)
                    if dd <= cr:
                        col = crater_dk if dd > cr - .7 else crater
                c.set(x, y, col, 255)
        # a single sugar highlight, only on visible phases
        if frac > 0:
            hx = int(cx + (-2.4 if side < 0 else 2.4) * 1.0)
            hy = int(cy - 3.2)
            if c.get(hx, hy)[3] and c.get(hx, hy)[0] > 180:
                c.set(hx, hy, sparkle)
    return c


# ------------------------------------------------------------------ clouds

def clouds(size=256):
    """Puffy cotton-candy clouds built from overlapping discs.

    Drawing blobs (rather than thresholding noise) keeps the silhouettes
    readable as clouds while the per-pixel fringe noise keeps them organic.
    All positions wrap, so the sky texture tiles seamlessly.
    """
    n = ValueNoise(31)
    rnd = random.Random(77)
    solid = [[False] * size for _ in range(size)]

    def puff(cx, cy, r):
        rr = int(r) + 3
        for y in range(int(cy) - rr, int(cy) + rr + 1):
            for x in range(int(cx) - rr, int(cx) + rr + 1):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                # ragged rim: noise can eat or add a couple of pixels
                edge = .40 + 1.15 * n.fbm(x * .21, y * .21, 3, .55)
                if d <= r - edge:
                    solid[y % size][x % size] = True

    for _ in range(32):
        cx, cy = rnd.uniform(0, size), rnd.uniform(0, size)
        base = rnd.uniform(10.0, 15.0)
        # one solid core with lobes crowded around it: readable cumulus
        puff(cx, cy, base * .88)
        for _ in range(rnd.randint(6, 9)):
            puff(cx + rnd.gauss(0, base * .68),
                 cy + rnd.gauss(0, base * .42),
                 rnd.uniform(4.2, 8.0))
    # a handful of tiny stray puffs, like the vanilla sky
    for _ in range(10):
        puff(rnd.uniform(0, size), rnd.uniform(0, size),
             rnd.uniform(2.0, 4.2))

    # smooth the rim without destroying small puffs
    for _ in range(2):
        nxt = [row[:] for row in solid]
        for y in range(size):
            for x in range(size):
                near = sum(solid[(y + dy) % size][(x + dx) % size]
                           for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                           if dx or dy)
                if solid[y][x] and near <= 2:
                    nxt[y][x] = False
                elif not solid[y][x] and near >= 7:
                    nxt[y][x] = True
        solid = nxt

    c = Canvas(size, size)
    white = hex_rgb("#fffdf9")
    fluff = hex_rgb("#fbeef5")
    pink = hex_rgb("#f7d2e2")
    deep_pink = hex_rgb("#eebbd2")
    for y in range(size):
        for x in range(size):
            if not solid[y][x]:
                continue
            above = solid[(y - 1) % size][x]
            below = solid[(y + 1) % size][x]
            left = solid[y][(x - 1) % size]
            right = solid[y][(x + 1) % size]
            n2 = n.fbm(x * .035, y * .035, 3, .55, period=9)
            if not above:
                col = white
            elif not below:
                col = deep_pink if n2 > .5 else pink
            elif not left or not right:
                col = fluff if n2 > .45 else pink
            else:
                col = mix(fluff, pink, .10 + .28 * (y / size) + .18 * n2)
            c.set(x, y, col, 255)
    return c


# ------------------------------------------------------------------ weather

def weather():
    c = Canvas(32, 32)
    rnd = random.Random(88)
    # snow specks, first three rows
    snow = [hex_rgb("#fffdf8"), hex_rgb("#dff8ff"), hex_rgb("#e7fff4")]
    for y in range(0, 3):
        for x in range(32):
            if rnd.random() < .17:
                c.set(x, y, snow[rnd.randrange(len(snow))], rnd.choice((170, 210, 255)))
    # rain streaks, rows 5..19
    blue_hi = hex_rgb("#d7f5ff")
    blue_mid = hex_rgb("#86d9f7")
    blue_lo = hex_rgb("#5b7de0")
    for i in range(16):
        x = rnd.randrange(32)
        top = 5 + rnd.randrange(0, 5)
        length = 6 + rnd.randrange(0, 9)
        width = 1 if rnd.random() < .82 else 2
        for k in range(length):
            y = top + k
            if y > 19:
                break
            t = k / max(1, length - 1)
            col = mix(blue_hi, blue_lo, t)
            a = int(150 + 95 * math.sin(math.pi * min(1.0, t * 1.15)))
            for w in range(width):
                c.set((x + w) % 32, y, blue_mid if t < .5 else col, a)
        # bright splash at the tip
        if top + length <= 19:
            c.set(x, top + length, blue_hi, 220)
    # the four engine swatches at the bottom, same footprints as vanilla
    for x0, y0, col in ((0, 20, hex_rgb("#ef5d76")),
                        (0, 24, hex_rgb("#263a83")),
                        (0, 28, hex_rgb("#2a1626")),
                        (4, 28, hex_rgb("#b9b2c9"))):
        c.rect(x0, y0, x0 + 3, y0 + 3, col)
    return c


# ------------------------------------------------------------------ destroy

def destroy_stage(stage, size=16):
    """One frame of a cumulative chocolate-crack overlay."""
    rnd = random.Random(417)
    r = 6.8
    pixels = {}

    def add(x, y, rev):
        if 0 <= x < size and 0 <= y < size:
            if (x, y) not in pixels or rev < pixels[(x, y)]:
                pixels[(x, y)] = rev

    # five main cracks walking outward; each step has a reveal stage
    for k in range(6):
        ang = k * math.pi * 2 / 6 + rnd.uniform(-.25, .25)
        x, y = 7.5 + rnd.uniform(-.7, .7), 7.5 + rnd.uniform(-.7, .7)
        for step in range(13):
            ang += rnd.uniform(-.28, .28)
            x += math.cos(ang)
            y += math.sin(ang)
            px, py = int(round(x)), int(round(y))
            rev = min(9, int(step * .82))
            add(px, py, rev)
            if rnd.random() < .35:
                add(px + rnd.choice((-1, 0, 1)), py + rnd.choice((-1, 0, 1)),
                    min(9, rev + 1))
            if step in (3, 6, 9) and rnd.random() < .7:
                # side branch
                ba = ang + rnd.choice((-1, 1)) * rnd.uniform(.5, 1.1)
                bx, by = x, y
                for j in range(3 + rnd.randrange(0, 3)):
                    ba += rnd.uniform(-.3, .3)
                    bx += math.cos(ba)
                    by += math.sin(ba)
                    add(int(round(bx)), int(round(by)),
                        min(9, rev + 1 + j // 2))
    # crumbs near the centre at late stages
    for _ in range(30):
        x, y = rnd.randrange(size), rnd.randrange(size)
        d = math.hypot(x - 7.5, y - 7.5)
        if d < 7.0:
            add(x, y, min(9, 5 + int(d * .55)))

    c = Canvas(size, size)
    dark = hex_rgb("#2a1626")
    mid = hex_rgb("#5a3550")
    for (x, y), rev in pixels.items():
        if rev <= stage:
            # late cracks get a faint mauve lip so they read on dark blocks
            c.set(x, y, mid if rev >= 7 and (x + y) % 5 == 0 else dark, 236)
    return c


# ------------------------------------------------------------------ flame atlas

def flame_atlas(frames=32, size=16):
    c = Canvas(size, size * frames)
    cherry = hex_rgb("#ef5d76")
    orange = hex_rgb("#ffb36b")
    lemon = hex_rgb("#ffe18a")
    cream = hex_rgb("#fff8e6")
    ember = hex_rgb("#ffd0a0")
    for f in range(frames):
        t = f / float(frames)
        tone = Canvas(size, size)
        flick = .88 + .12 * math.sin(t * math.pi * 2 * 3 + .7)
        height = 14.6 * flick
        sway = 1.25 * math.sin(t * math.pi * 2)
        for y in range(size):
            depth = (size - 1 - y) / height
            if depth < 0 or depth > 1:
                continue
            h = depth
            half = 4.5 * (1 - h) ** .58 * (0.86 + .14 * math.sin(
                t * math.pi * 2 * 2 + h * 4.0))
            if half < .35:
                continue
            cx = 7.5 + sway * (h ** 1.5) + .45 * math.sin(t * 9 + h * 5)
            for x in range(size):
                dx = abs(x + .5 - cx)
                if dx > half:
                    continue
                e = dx / half
                # wavy notch so the silhouette is not a clean cone
                if e > .72 and math.sin(x * 2.1 + y * 1.7 + f * 1.3) > .55:
                    continue
                if e > .62:
                    col = mix(orange, cherry, e)
                elif e > .34:
                    col = mix(lemon, orange, (e - .34) / .28)
                else:
                    col = mix(cream, lemon, (e / .34) ** 1.4)
                if e < .30 and h > .25 and h < .78:
                    col = cream
                a = 255 if e < .88 else 225
                tone.set(x, y, col, a)
        # rising sugar sparks
        rr = random.Random(900 + f)
        if f % 2 == 0:
            sx = rr.randrange(4, 12)
            sy = rr.randrange(0, 3)
            tone.set(sx, sy, ember, 190)
        for y in range(size):
            for x in range(size):
                cc = tone.get(x, y)
                if cc[3]:
                    c.set(x, f * size + y, cc, cc[3])
    return c


# ------------------------------------------------------------------ end

def end_portal_colors():
    c = Canvas(4, 4)
    cols = ["#2a1235", "#4a1f55", "#7a2f6e", "#b565a0",
            "#263a83", "#4a2478", "#b58be8", "#f7a8c4",
            "#21705c", "#2c6480", "#86d9f7", "#ffe18a",
            "#1d1026", "#3a2c3e", "#77155b", "#fff7f8"]
    for i, hx in enumerate(cols):
        c.set(i % 4, i // 4, hex_rgb(hx))
    return c


def end_sky(size=128):
    c = Canvas(size, size)
    top = hex_rgb("#190e23")
    bottom = hex_rgb("#4a2350")
    for y in range(size):
        col = mix(top, bottom, (y / (size - 1.0)) ** .85)
        for x in range(size):
            c.set(x, y, col)
    n = ValueNoise(6)
    pink = hex_rgb("#c46aa8")
    lilac = hex_rgb("#8e5bb0")
    mint = hex_rgb("#6fbfb7")
    for y in range(size):
        for x in range(size):
            u, v = x / size * 5.0, y / size * 5.0
            a = n.fbm(u, v, 5, .55, period=5)
            b = n.fbm(u * 2.7 + 11, v * 2.7 + 4, 4, .5, period=13)
            if a > .54:
                c.blend(x, y, pink, int((a - .54) * 120))
            if b > .60:
                c.blend(x, y, lilac, int((b - .60) * 130))
            if a * b > .30:
                c.blend(x, y, mint, 16)
    rnd = random.Random(2026)
    cream = hex_rgb("#fff5df")
    star_pink = hex_rgb("#ffd3e6")
    star_mint = hex_rgb("#d8fff2")
    for _ in range(120):
        x, y = rnd.randrange(size), rnd.randrange(size)
        col = rnd.choice((cream, cream, star_pink, star_mint))
        c.set(x, y, col, 255)
        if rnd.random() < .10:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < size and 0 <= y + dy < size:
                    c.set(x + dx, y + dy, col, 130)
    for _ in range(4):
        x, y = rnd.randrange(8, size - 8), rnd.randrange(8, size - 8)
        glow(c, x, y, 5.5, star_pink, 55, 2.0)
        c.set(x, y, cream, 255)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0),
                       (0, 2), (0, -2)):
            c.set(x + dx, y + dy, star_pink, 190)
    return c


def end_flash(size=64):
    c = Canvas(size, size, fill=(4, 2, 7, 255))
    cx = cy = size / 2.0
    dark = hex_rgb("#1d1026")
    plum = hex_rgb("#5a2a6e")
    pink = hex_rgb("#f28fb4")
    cream = hex_rgb("#fff8e6")
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + .5 - cx, y + .5 - cy)
            t = clamp(1.0 - d / (size * .46), 0.0, 1.0)
            if t <= 0:
                col = dark
            elif t < .55:
                col = mix(dark, plum, (t / .55) ** .7)
            elif t < .83:
                col = mix(plum, pink, (t - .55) / .28)
            else:
                col = mix(pink, cream, (t - .83) / .17)
            # soft eight-point star rays
            ang = math.atan2(y + .5 - cy, x + .5 - cx)
            ray = (math.cos(ang * 8) + 1) * .5
            if t > .05:
                col = mix(col, cream, ray * t * t * .18)
            c.set(x, y, col, 255)
    return c


def forcefield_atlas(size=16):
    c = Canvas(size, size)
    n = ValueNoise(19)
    deep = hex_rgb("#4c3a62")
    lilac = hex_rgb("#b9a6d8")
    mint = hex_rgb("#bfe9df")
    for y in range(size):
        for x in range(size):
            v = n.fbm(x * .55, y * .55, 3, .55)
            col = mix(deep, lilac, .25 + v * .55)
            if (x + y) % 5 == 0:
                col = mix(col, mint, .22)
            if (x * 7 + y * 11) % 23 == 0:
                col = mix(col, hex_rgb("#fff7f8"), .65)
            c.set(x, y, col, 255)
    return c


# ------------------------------------------------------------------ misc

def missing_texture(size=16):
    c = Canvas(size, size)
    pink = hex_rgb("#f7a8c4")
    plum = hex_rgb("#3a2c3e")
    for y in range(size):
        for x in range(size):
            c.set(x, y, pink if ((x // 4) + (y // 4)) % 2 == 0 else plum)
    # cream question mark
    cream = hex_rgb("#fff6e6")
    pattern = ["011100", "100010", "000010", "000100", "001000",
               "001000", "000000", "001000"]
    ox, oy = 5, 4
    for yy, row in enumerate(pattern):
        for xx, ch in enumerate(row):
            if ch == "1":
                c.set(ox + xx, oy + yy, cream)
    return c
