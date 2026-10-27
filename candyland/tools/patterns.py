"""Candyland surface patterns.  Everything here is drawn from scratch."""
import math
import random

from candy import (Canvas, ValueNoise, Ramp, get_ramp, mix, luma, at_luma,
                   q, sprinkle, star, heart)

# ------------------------------------------------------------------ helpers

def _noise_fill(c, ramp, seed, scale=4.0, octaves=4, gain=0.55,
                contrast=1.0, offset=0.0):
    n = ValueNoise(seed)
    period = max(1, int(round(scale)))
    for y in range(c.h):
        for x in range(c.w):
            v = n.fbm(x * scale / c.w, y * scale / c.h, octaves, gain, period)
            t = 0.5 + (v - 0.5) * contrast + offset
            c.set(x, y, ramp.at(t))


def bevel(c, ramp, depth=1, strength=0.35):
    """Very light top-left / bottom-right block edge, no hard outline."""
    for x in range(c.w):
        for y in range(depth):
            cc = c.get(x, y)
            if cc[3]:
                c.set(x, y, at_luma(ramp.at(0.72), luma(cc) + 22 * strength))
    for x in range(c.w):
        for y in range(c.h - depth, c.h):
            cc = c.get(x, y)
            if cc[3]:
                c.set(x, y, at_luma(ramp.at(0.28), luma(cc) - 18 * strength))
    for y in range(c.h):
        for x in range(depth):
            cc = c.get(x, y)
            if cc[3]:
                c.set(x, y, at_luma(ramp.at(0.68), luma(cc) + 14 * strength))
        for x in range(c.w - depth, c.w):
            cc = c.get(x, y)
            if cc[3]:
                c.set(x, y, at_luma(ramp.at(0.30), luma(cc) - 12 * strength))


def _clump(c, cx, cy, rx, ry, col, hi, shade, rnd, wrap=True):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            nx = (x + .5 - cx) / max(0.1, rx)
            ny = (y + .5 - cy) / max(0.1, ry)
            if nx * nx + ny * ny <= 1.0:
                if -nx * .7 - ny * .7 > .35:
                    cc = hi
                elif nx * .7 + ny * .7 > .35:
                    cc = shade
                else:
                    cc = col
                xx = x % c.w if wrap else x
                yy = y % c.h if wrap else y
                c.set(xx, yy, cc)


def _dome(dx, dy, r, expr=1.0):
    if r <= 0:
        return 0.0
    nx, ny = dx / r, dy / r
    d2 = nx * nx + ny * ny
    if d2 >= 1:
        return 0.0
    h = math.sqrt(1 - d2)
    return (-nx / max(.12, h) * -.707 + -ny / max(.12, h) * -.707) * expr


MASK_RAMP = Ramp([(92, 92, 92), (128, 128, 128), (160, 160, 160),
                  (192, 192, 192), (224, 224, 224), (252, 252, 252)])


# ------------------------------------------------------------------ rocks

def rock(c, seed, ramp, palette=None, accents=None, grain=.9, scale=5.0,
         sparkle=0.0, bevel_strength=.3, cool=False, cells=0.0,
         facet=.0, vein=.0):
    """Grainy fondant rock, or -- with ``cells`` -- faceted rock candy."""
    if cells:
        n = ValueNoise(seed)
        period = max(2, int(round(cells)))
        rnd = random.Random(seed * 19 + 7)
        for y in range(c.h):
            for x in range(c.w):
                dx, dy, d, edge, h = n.worley_cell(
                    x * cells / c.w, y * cells / c.h, period)
                t = .34 + h * .26
                if facet:
                    ang = math.atan2(dy, dx)
                    # three broad crystal faces per cell
                    f = math.cos(ang * 3.0 + h * 6.283)
                    t += f * facet * .22
                dome = _dome(dx, dy, .72, 1.0)
                t += dome * .07
                t += (n.fbm(x * .55, y * .55, 3, .55,
                            max(1, int(scale))) - .5) * grain * .18
                if edge < .055:
                    t += .22                       # sugar seam catches light
                elif edge < .12:
                    t += .05
                if vein:
                    v = math.sin((x * .55 + y * .28) + h * 5.0)
                    if v > .93:
                        t += vein * .18
                c.set(x, y, ramp.at(max(0, min(1, t))))
        if accents:
            for _ in range(max(2, c.w * c.h // 150)):
                x, y = rnd.randrange(c.w), rnd.randrange(c.h)
                r = rnd.choice([1, 1, 2])
                col = accents[rnd.randrange(len(accents))]
                hi = at_luma(col, min(255, luma(col) + 40))
                for yy in range(-r, r + 1):
                    for xx in range(-r, r + 1):
                        if xx * xx + yy * yy <= r * r:
                            c.set((x + xx) % c.w, (y + yy) % c.h,
                                  hi if xx <= 0 and yy <= 0 else col)
        if sparkle:
            for _ in range(int(c.w * c.h * sparkle)):
                c.set(rnd.randrange(c.w), rnd.randrange(c.h), (255, 255, 250))
        bevel(c, ramp, 1, bevel_strength * .6)
        return

    _noise_fill(c, ramp, seed, scale=scale, octaves=5, gain=.55,
                contrast=grain)
    rnd = random.Random(seed * 17 + 3)
    if accents:
        # pebbles / candy flecks
        for _ in range(max(2, c.w * c.h // 150)):
            x = rnd.randrange(c.w)
            y = rnd.randrange(c.h)
            r = rnd.choice([1, 1, 1, 2])
            col = accents[rnd.randrange(len(accents))]
            hi = at_luma(col, min(255, luma(col) + 40))
            for yy in range(-r, r + 1):
                for xx in range(-r, r + 1):
                    if xx * xx + yy * yy <= r * r:
                        c.set((x + xx) % c.w, (y + yy) % c.h,
                              hi if xx <= 0 and yy <= 0 else col)
    if sparkle:
        for _ in range(int(c.w * c.h * sparkle)):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, (255, 255, 250))
    bevel(c, ramp, 1, bevel_strength)


def crumb(c, seed, ramp, crumb_ramp=None, scale=5.0, holes=0.02,
          sprinkles=None):
    """Cake / soil surface: dense crumbs with tiny air pockets."""
    n = ValueNoise(seed)
    _noise_fill(c, ramp, seed, scale=scale, octaves=4, gain=.6, contrast=.75)
    rnd = random.Random(seed + 3)
    crumb_ramp = crumb_ramp or ramp
    for _ in range(int(c.w * c.h * .05)):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        r = rnd.choice([1, 1, 2])
        tone = rnd.choice([.45, .60, .75, .90])
        col = crumb_ramp.at(tone)
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r:
                    c.set((x + xx) % c.w, (y + yy) % c.h, col)
    for _ in range(int(c.w * c.h * holes)):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        c.set(x, y, ramp.at(.06))
        if rnd.random() < .4:
            c.set((x + 1) % c.w, y, ramp.at(.16))
    if sprinkles:
        sprinkle(c, 0, 0, sprinkles, seed + 9, density=.02, length=2, size=1)
    bevel(c, ramp, 1, .18)


def cobble(c, seed, ramp, palette, mortar, accent_cols=None, cells=5.0):
    n = ValueNoise(seed)
    period = max(2, int(round(cells)))
    for y in range(c.h):
        for x in range(c.w):
            dx, dy, d, edge, h = n.worley_cell(x * cells / c.w,
                                               y * cells / c.h, period)
            if edge < .055:
                c.set(x, y, mortar.at(.45))
                continue
            key = palette[int(h * len(palette)) % len(palette)]
            r = get_ramp(key)
            dome = _dome(dx, dy, .55, 1.15)
            t = .55 + dome * .32 + (h - .5) * .12
            col = r.at(t)
            c.set(x, y, col)
            if edge < .12:
                c.blend(x, y, (255, 255, 255), 28)
    if accent_cols:
        sprinkle(c, 0, 0, accent_cols, seed + 9, density=.012, length=2, size=1)
    bevel(c, ramp, 1, .25)


def gumdrop(c, seed, palette, icing, cells=5.0):
    n = ValueNoise(seed)
    period = max(2, int(round(cells)))
    for y in range(c.h):
        for x in range(c.w):
            dx, dy, d, edge, h = n.worley_cell(x * cells / c.w,
                                               y * cells / c.h, period)
            if edge < .08:
                c.set(x, y, icing.at(.72))
            else:
                r = get_ramp(palette[int(h * len(palette)) % len(palette)])
                dome = _dome(dx, dy, .55, 1.3)
                c.set(x, y, r.at(.52 + dome * .34 + (h - .5) * .1))


def bricks(c, seed, ramp, mortar, rows=3, cols=2, colors=None,
           crack=0.0, bevel_strength=.35):
    bh = c.h / rows
    bw = c.w / cols
    rnd = random.Random(seed)
    for y in range(c.h):
        ry = int(y // bh)
        offset = (bw * .5) if ry % 2 else 0
        for x in range(c.w):
            xx = (x + offset) % c.w
            cx = int(xx // bw)
            lx = xx % bw
            ly = y % bh
            edge = min(lx, bw - lx, ly, bh - ly)
            if edge < .9:
                c.set(x, y, mortar.at(.55))
                continue
            rr = ramp
            if colors:
                rr = get_ramp(colors[(cx + ry * 3) % len(colors)])
            tone = .58 + (rnd.random() - .5) * .04
            if ly < 2:
                tone += .12
            elif ly > bh - 2:
                tone -= .12
            if edge < 2:
                tone += .08 if lx < 2 or ly < 2 else -.08
            c.set(x, y, rr.at(tone))
    if crack:
        for _ in range(int(crack * 3)):
            x = rnd.randrange(c.w)
            y = rnd.randrange(c.h)
            for i in range(rnd.randrange(2, 5)):
                x = (x + rnd.choice([-1, 0, 1])) % c.w
                y = (y + 1) % c.h
                c.set(x, y, mortar.at(.15))
    bevel(c, ramp, 1, bevel_strength)


# ------------------------------------------------------------------ wood

def planks(c, seed, ramp, seam, boards=4, grain=.45, knot=True,
           polish=.0):
    bh = c.h / boards
    n = ValueNoise(seed)
    rnd = random.Random(seed + 4)
    for y in range(c.h):
        row = int(y // bh)
        ly = y % bh
        base_t = .56 + (n.at(row * 3.1, .5) - .5) * .16
        if ly < .9 or ly > bh - .9:
            c.set(0, y, seam.at(.35))
            for x in range(c.w):
                c.set(x, y, seam.at(.35))
            continue
        for x in range(c.w):
            st = n.fbm(x * .09, row * 5.1 + y * .25, 3, .55,
                       period=max(1, int(c.w * .09)))
            t = base_t + (st - .5) * grain
            if ly < 1.8:
                t += .11
            elif ly > bh - 2.2:
                t -= .10
            # icing stripe along one board seam
            c.set(x, y, ramp.at(t))
    if knot:
        kx = rnd.randrange(4, c.w - 4)
        ky = int((rnd.randrange(1, boards) - .5) * bh)
        for y in range(-2, 3):
            for x in range(-3, 4):
                if (x / 3.2) ** 2 + (y / 2.2) ** 2 <= 1:
                    c.set((kx + x) % c.w, (ky + y) % c.h,
                          seam.at(.48))
        for x in range(-1, 2):
            c.set((kx + x) % c.w, ky, ramp.at(.78))
    if polish:
        for y in range(c.h):
            for x in range(c.w):
                cc = c.get(x, y)
                if cc[3]:
                    c.set(x, y, mix(cc, (255, 250, 255), polish))
    bevel(c, ramp, 1, .22)


def log_side(c, seed, ramp, dark, light, striped=False, stripe_col=None,
             bark=True):
    n = ValueNoise(seed)
    if striped:
        # candy-cane poles: diagonal red/white bands
        for y in range(c.h):
            for x in range(c.w):
                band = int((((x + y * .55) % c.w) // (c.w / 5.0))) % 2
                col = stripe_col if band else (250, 247, 244)
                shade = n.at(x * .22, y * .11) - .5
                col = tuple(clamp(v * (1 + shade * .16)) for v in col)
                c.set(x, y, col)
        for _ in range(c.w):
            rnd = random.Random(seed + _)
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, mix(stripe_col, (255, 255, 255), .35))
        return
    for y in range(c.h):
        for x in range(c.w):
            g = n.fbm(x * .18, y * .07, 4, .55, max(1, int(c.w * .18)))
            wave = math.sin(x * 2 * math.pi * 2.3 / c.w + math.sin(y * .22) * .55)
            groove = 1.0 if wave > .35 else 0.0
            t = .55 + (g - .5) * .38 - groove * .10
            if wave < -.82:
                t += .10
            col = ramp.at(max(0, min(1, t)))
            if bark and wave > .93:
                col = mix(col, dark.at(.3), .55)
            c.set(x, y, col)
    # knots and bark flecks
    rnd = random.Random(seed + 7)
    for _ in range(2):
        kx, ky = rnd.randrange(c.w), rnd.randrange(c.h)
        for yy in range(-1, 2):
            for xx in range(-2, 3):
                if abs(xx) + abs(yy) <= 2:
                    c.set((kx + xx) % c.w, (ky + yy) % c.h,
                          dark.at(.5) if abs(xx) + abs(yy) == 2 else light.at(.8))
    bevel(c, ramp, 1, .18)

def log_end(c, seed, ramp, dark, light, peppermint=None):
    cx, cy = c.w / 2.0, c.h / 2.0
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x + .5 - cx, y + .5 - cy
            r = math.hypot(dx, dy) / (c.w * .5)
            ang = math.atan2(dy, dx)
            if peppermint:
                swirl = (ang / (2 * math.pi) + r * .9) % 1.0
                col = peppermint[0] if swirl < .5 else peppermint[1]
                if r > .93:
                    col = peppermint[2]
                c.set(x, y, col)
                continue
            ring = (r * 5.5 + n.at(ang * 2.2, r * 4) * .35) % 1.0
            t = .50 + (ring - .5) * .5 + (1 - r) * .12
            col = ramp.at(max(0, min(1, t)))
            if r < .11:
                col = dark.at(.32)
            elif r < .17:
                col = light.at(.8)
            c.set(x, y, col)
    if peppermint:
        # tiny dark centre
        c.disc(cx, cy, max(1, c.w * .045), peppermint[2])


# ------------------------------------------------------------------ leaves

def leaves(c, seed, ramp, opaque=False, colored=True, flowers=None,
           density=.86):
    """Layered gummy-leaf mass.  When ``colored`` is False the result is
    converted to a bright greyscale mask for biome tinting."""
    if not colored:
        ramp = MASK_RAMP
    rnd = random.Random(seed)
    n = ValueNoise(seed)
    if opaque:
        c.fill(ramp.at(.28), 255)
    else:
        c.fill(ramp.at(.48), 255)
    # undergrowth shadow blobs, then lit leaf lobes on top
    for layer in range(2):
        count = 30 if layer == 0 else 26
        for _ in range(count):
            cx = rnd.randrange(c.w)
            cy = rnd.randrange(c.h)
            rx = rnd.uniform(1.8, 4.1)
            ry = rx * rnd.uniform(.55, .95)
            tone = (rnd.uniform(.30, .52) if layer == 0
                    else rnd.uniform(.58, .92))
            col = ramp.at(tone)
            hi = ramp.at(min(1.0, tone + .16))
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                    nx = (x + .5 - cx) / rx
                    ny = (y + .5 - cy) / ry
                    if nx * nx + ny * ny > 1.0:
                        continue
                    xx, yy = x % c.w, y % c.h
                    cc = hi if (nx * .5 + ny * .5 < -.55) else col
                    c.set(xx, yy, cc, 255)
    # holes and deep gaps (opaque leaves just darken them)
    for y in range(c.h):
        for x in range(c.w):
            v = n.fbm(x * .38, y * .38, 2, .6, 4)
            if v < (1.0 - density) * 1.35:
                if opaque:
                    cc = c.get(x, y)
                    c.set(x, y, ramp.at(.20), cc[3])
                else:
                    c.px[(y * c.w + x) * 4 + 3] = 0
    if not opaque:
        for _ in range(6):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, c.get(x, y), 0)
    if flowers:
        for _ in range(max(3, c.w * c.h // 160)):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            if c.get(x, y)[3] or opaque:
                col = flowers[rnd.randrange(len(flowers))]
                c.set(x, y, col)
                c.set((x + 1) % c.w, y, mix(col, (255, 255, 255), .3))
                c.set(x, (y + 1) % c.h, at_luma(col, luma(col) * .8))
    return c


def n_alpha(seed, x, y):
    v = (x * 7349 + y * 9151 + seed * 3571) & 0xffff
    v = (v ^ (v >> 7)) * 2654435761 & 0xffffffff
    return ((v >> 8) & 0xffff) / 65535.0

def grass_top(c, seed, ramp, colored=True, flowers=None):
    if not colored:
        ramp = MASK_RAMP
    n = ValueNoise(seed)
    rnd = random.Random(seed + 2)
    for y in range(c.h):
        for x in range(c.w):
            v = n.fbm(x * 6.0 / c.w, y * 6.0 / c.h, 4, .55, 6)
            t = .58 + (v - .5) * .55
            c.set(x, y, ramp.at(max(0, min(1, t))))
    # blade tufts: lit strokes with a dark under-edge
    for _ in range(c.w * c.h // 18):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        hgt = rnd.randrange(2, 6)
        lean = rnd.choice([-1, 0, 0, 1])
        tone = rnd.uniform(.66, .98)
        for i in range(hgt):
            bx = (x + (lean if i > hgt // 2 else 0)) % c.w
            by = (y - i) % c.h
            c.set(bx, by, ramp.at(tone))
            if i == 0:
                c.set((bx + 1) % c.w, by, ramp.at(tone * .55))
        if rnd.random() < .25:
            c.set((x + lean) % c.w, (y - hgt) % c.h, ramp.at(1.0))
    if flowers:
        for _ in range(max(1, c.w * c.h // 420)):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            col = flowers[rnd.randrange(len(flowers))]
            c.set(x, y, col)
            c.set((x + 1) % c.w, y, mix(col, (255, 255, 255), .3))
            c.set(x, (y + 1) % c.h, at_luma(col, luma(col) * .78))
    bevel(c, ramp, 1, .18)


def grass_side_mask(c, seed, ramp, dirt_ramp=None):
    """Grey grass fringe over cake-crumb soil.

    RGB under alpha=0 is the soil; the client shows it through the alpha.
    The opaque fringe is neutral grey so biome tint can colour it.
    """
    dirt_ramp = dirt_ramp or get_ramp("chocolate")
    soil = Canvas(c.w, c.h)
    crumb(soil, seed + 4, dirt_ramp, scale=5.0, holes=.03,
          sprinkles=[(240, 190, 120), (120, 70, 45)])
    for y in range(c.h):
        for x in range(c.w):
            cc = soil.get(x, y)
            c.set(x, y, cc[:3], 0)

    n = ValueNoise(seed)
    heights = [8 + int(n.at(i * .8, 3.3) * 4 + n.fbm(i * .35, 1.2, 2) * 2)
               for i in range(c.w)]
    grey = MASK_RAMP
    for x in range(c.w):
        h = heights[x]
        for y in range(h):
            t = .42 + n.fbm(x * .8, y * .9, 3, .55, 4) * .38
            if y < 2:
                t += .22
            if y > h - 2:
                t -= .12
            c.set(x, y, grey.at(max(0, min(1, t))), 255)
        # icing drips over the soil
        if n.at(x * 1.7, 9.1) > .62:
            yy = h
            if yy < c.h:
                c.set(x, yy, grey.at(.55), 255)
            if n.at(x * 2.1, 4.2) > .7 and yy + 1 < c.h:
                c.set(x, yy + 1, grey.at(.40), 255)
        # a lit rim right at the edge
        c.set(x, max(0, h - 1), grey.at(1.0), 255)


# ------------------------------------------------------------------ soft materials

def wool(c, seed, ramp, accent=None):
    """Chunky basket weave in soft cotton-candy tones."""
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            bx, by = x // 4, y // 4
            lx, ly = x % 4, y % 4
            over = (bx + by) % 2 == 0
            if over:                     # horizontal thread
                t = .62 + .16 * math.sin((lx + .5) / 4 * math.pi)
                if ly == 0:
                    t += .12
                elif ly == 3:
                    t -= .12
            else:                        # vertical thread
                t = .62 + .16 * math.sin((ly + .5) / 4 * math.pi)
                if lx == 0:
                    t += .12
                elif lx == 3:
                    t -= .12
            t += (n.at(x * .45, y * .45) - .5) * .10
            c.set(x, y, ramp.at(max(0, min(1, t))))
    # loose fibres and nubs
    rnd = random.Random(seed + 11)
    for _ in range(c.w // 4):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        ln = rnd.randrange(2, 4)
        for i in range(ln):
            c.set((x + i) % c.w, y, ramp.at(.92))
    if accent:
        for _ in range(max(2, c.w * c.h // 500)):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, accent)
            c.set((x + 1) % c.w, y, accent)
    bevel(c, ramp, 1, .10)

def fondant(c, seed, ramp, swatch=None):
    _noise_fill(c, ramp, seed, scale=3.0, octaves=3, gain=.5, contrast=.35)
    if swatch:
        for _ in range(c.w * c.h // 220):
            x = random.Random(seed + _).randrange(c.w)
            y = random.Random(seed + _ + 5).randrange(c.h)
            c.set(x, y, swatch)
    bevel(c, ramp, 1, .12)


def fudge(c, seed, ramp):
    """Marbled fudge swirl."""
    n = ValueNoise(seed)
    cx, cy = c.w / 2.0, c.h / 2.0
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x + .5 - cx, y + .5 - cy
            ang = math.atan2(dy, dx)
            r = math.hypot(dx, dy) / (c.w * .5)
            swirl = math.sin(ang * 2.0 + r * 9.0
                            + n.fbm(x * .16, y * .16, 3) * 3.0)
            t = .52 + swirl * .17 + (n.fbm(x * .3, y * .3, 3) - .5) * .26
            c.set(x, y, ramp.at(max(0, min(1, t))))
    # glossy highlights along the swirl crests
    for _ in range(c.w * c.h // 90):
        x = random.Random(seed + _).randrange(c.w)
        y = random.Random(seed + _ + 2).randrange(c.h)
        cc = c.get(x, y)
        c.set(x, y, mix(cc, (255, 240, 220), .35))
    bevel(c, ramp, 1, .15)


def taffy(c, seed, ramp, ribbon=None):
    """Stretched taffy ribbons."""
    n = ValueNoise(seed)
    ribbon = ribbon or ramp.at(.86)
    for y in range(c.h):
        for x in range(c.w):
            v = math.sin((x * .28 + y * .12) * 2.4
                         + n.fbm(x * .14, y * .14, 3) * 5.0)
            t = .52 + v * .20 + (n.fbm(x * .35, y * .35, 3) - .5) * .18
            col = ramp.at(max(0, min(1, t)))
            if v > .86:
                col = mix(col, ribbon, .55)
            c.set(x, y, col)
    bevel(c, ramp, 1, .12)


def sugar(c, seed, ramp, sparkle=True, accent=None):
    _noise_fill(c, ramp, seed, scale=7.0, octaves=4, gain=.55, contrast=1.0)
    rnd = random.Random(seed + 6)
    if sparkle:
        for _ in range(c.w * c.h // 85):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, (255, 255, 250))
    if accent:
        for _ in range(c.w * c.h // 200):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, accent)
    bevel(c, ramp, 1, .12)


def gravel(c, seed, palette, mortar):
    n = ValueNoise(seed)
    period = 6
    for y in range(c.h):
        for x in range(c.w):
            dx, dy, d, edge, h = n.worley_cell(x * 6.0 / c.w, y * 6.0 / c.h, period)
            if edge < .06:
                c.set(x, y, mortar.at(.5))
            else:
                r = get_ramp(palette[int(h * len(palette)) % len(palette)])
                c.set(x, y, r.at(.5 + _dome(dx, dy, .55) * .35))


# ------------------------------------------------------------------ fluids / glass

def glass(c, seed, tint=(236, 250, 255), border=(255, 255, 255),
          shine=(255, 255, 255), stars=True):
    c.px = bytearray(c.w * c.h * 4)
    for y in range(c.h):
        for x in range(c.w):
            edge = min(x, y, c.w - 1 - x, c.h - 1 - y)
            if edge == 0:
                c.set(x, y, border, 190)
            elif edge == 1 and (x + y) % 5 != 0:
                c.set(x, y, mix(tint, border, .55), 26)
            elif edge < 4:
                c.set(x, y, mix(tint, border, .4), 8)
    # diagonal glints
    for d in (7, 16, 25):
        for i in range(c.w // 2):
            x = (i + d) % c.w
            y = c.h - 1 - i
            if 0 <= y < c.h:
                c.blend(x, y, shine, 70)
    if stars:
        rnd = random.Random(seed)
        for _ in range(3):
            star(c, rnd.randrange(3, c.w - 3), rnd.randrange(3, c.h - 3),
                 (255, 255, 255), 1)


def fluid_still(c, seed, ramp, foam, frame, frames):
    """One square fluid frame, tileable, used for flipbook strips."""
    n = ValueNoise(seed)
    ph = frame / max(1, frames)
    for y in range(c.h):
        for x in range(c.w):
            v = n.fbm(x * 3.0 / c.w + ph * 3.1,
                      y * 3.0 / c.h - ph * 2.3, 4, .55, 3)
            v2 = n.fbm(x * 7.0 / c.w - ph * 4, y * 7.0 / c.h, 3, .5, 7)
            t = .45 + (v * .75 + v2 * .25 - .5) * .65
            c.set(x, y, ramp.at(max(0, min(1, t))))
    # foam bubbles
    rnd = random.Random(seed + frame * 19)
    for _ in range(5):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        r = rnd.choice([1, 2])
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r:
                    c.set((x + xx) % c.w, (y + yy) % c.h, foam)


def fluid_flow(c, seed, ramp, foam, frame, frames, w=None, h=None):
    """One fluid frame, filling the whole canvas instead of a hard-coded 16x16 tile."""
    if w is None:
        w = c.w
    if h is None:
        h = c.h
    n = ValueNoise(seed)
    for y in range(h):
        for x in range(w):
            v = n.fbm(x * 2.5 / w, y * 5.0 / h + frame * .31, 4, .55, 4)
            t = .45 + (v - .5) * .8
            if (y + frame) % 7 < 2:
                t += .12
            c.set(x, y, ramp.at(max(0, min(1, t)), ))
    rnd = random.Random(seed + frame * 7)
    for _ in range(max(4, (w * h) // 64)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        c.set(x, y, foam)


# ------------------------------------------------------------------ ores, gems, metal

def ore(c, seed, body_ramp, gem_ramp, gems=4, deep=False):
    rock(c, seed, body_ramp, grain=.75, scale=5.5, bevel_strength=.22,
         cells=4.5)
    rnd = random.Random(seed + 12)
    w, h = c.w, c.h
    placed = []
    for _ in range(gems):
        for attempt in range(24):
            cx = rnd.randrange(3, w - 3)
            cy = rnd.randrange(3, h - 3)
            if all((cx - px) ** 2 + (cy - py) ** 2 > 7.0 ** 2
                   for px, py in placed):
                break
        placed.append((cx, cy))
        rx = rnd.choice([2.4, 2.8, 3.1])
        ry = rx * rnd.choice([.85, 1.0, 1.1])
        # dark sugar crust
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                nx = (x + .5 - cx) / (rx + 1.0)
                ny = (y + .5 - cy) / (ry + 1.0)
                if nx * nx + ny * ny <= 1.0:
                    c.set(x % w, y % h, gem_ramp.at(.06))
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                nx = (x + .5 - cx) / rx
                ny = (y + .5 - cy) / ry
                d2 = nx * nx + ny * ny
                if d2 > 1.0:
                    continue
                # faceted gummy: light from upper-left
                if nx + ny < -.75:
                    t = 1.0
                elif nx + ny < -.05:
                    t = .78 if nx < .1 else .60
                elif nx + ny < .72:
                    t = .45
                else:
                    t = .26
                if d2 > .80:
                    t *= .72
                c.set(x % w, y % h, gem_ramp.at(max(0, min(1, t))))
        # white glint
        c.set(int(cx - rx * .35) % w, int(cy - ry * .35) % h, (255, 255, 255))
        if rnd.random() < .5:
            c.set(int(cx - rx * .35 + 1) % w, int(cy - ry * .35) % h,
                  mix(gem_ramp.at(1), (255, 255, 255), .5))
    return c


def metal(c, seed, ramp, accent=None, pattern="foil"):
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            if pattern == "foil":
                band = math.sin((x + y * .45) * 2 * math.pi * 4 / c.w)
                t = .54 + band * .12 + (n.fbm(x * .2, y * .2, 3) - .5) * .18
            elif pattern == "brushed":
                t = .54 + (n.fbm(x * .08, y * .35, 4) - .5) * .28
            else:
                t = .54 + (n.fbm(x * .2, y * .2, 3) - .5) * .18
            c.set(x, y, ramp.at(max(0, min(1, t))))
    if accent:
        for _ in range(3):
            x = random.Random(seed + _).randrange(c.w)
            y = random.Random(seed + _ + 3).randrange(c.h)
            c.set(x, y, accent)
    bevel(c, ramp, 1, .4)


def gem_block(c, seed, ramp, facet_light=None, sparkle=True, style="crystal"):
    rnd = random.Random(seed)
    if style == "speckle":
        rock(c, seed, ramp, accents=[ramp.at(.9), ramp.at(.95)],
             grain=.75, scale=6, sparkle=.004, bevel_strength=.2)
        return c
    # pale sugar-rock bed so the block stays opaque
    n = ValueNoise(seed + 2)
    for y in range(c.h):
        for x in range(c.w):
            t = .78 + (n.fbm(x * .22, y * .22, 3) - .5) * .16
            c.set(x, y, mix(ramp.at(t), (255, 255, 255), .22))
    # packed rock-candy crystals: 2x2 large diamonds with four facets each
    cell = c.w / 2.0
    for gy in range(2):
        for gx in range(2):
            cx = (gx + .5) * cell
            cy = (gy + .5) * cell
            r = cell * .44
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for x in range(int(cx - r) - 1, int(cx + r) + 2):
                    dx, dy = x + .5 - cx, y + .5 - cy
                    if abs(dx) + abs(dy) > r + .8:
                        continue
                    xx, yy = x % c.w, y % c.h
                    if abs(dx) + abs(dy) > r - .7:
                        if dx + dy < 0:
                            c.set(xx, yy, mix(ramp.at(1), (255, 255, 255), .45))
                        else:
                            c.set(xx, yy, ramp.at(.16))
                        continue
                    facet = 0 if dx <= 0 and dy <= 0 else 1 if dx > 0 and dy <= 0 else 2 if dx <= 0 else 3
                    tones = [1.0, .70, .34, .52]
                    t = tones[facet] + (rnd.random() - .5) * .03
                    c.set(xx, yy, ramp.at(max(0, min(1, t))))
    if sparkle:
        for _ in range(4):
            star(c, rnd.randrange(2, c.w - 2), rnd.randrange(2, c.h - 2),
                 (255, 255, 255), 1)
    bevel(c, ramp, 1, .14)


# ------------------------------------------------------------------ food blocks

def cake_top(c, seed, ramp, frosting, sprinkle_cols, cherry):
    n = ValueNoise(seed)
    # soft frosting surface
    for y in range(c.h):
        for x in range(c.w):
            t = .72 + (n.fbm(x * .18, y * .18, 3) - .5) * .18
            c.set(x, y, frosting.at(max(0, min(1, t))))
    # piped frosting ring
    for y in range(c.h):
        for x in range(c.w):
            d = math.hypot(x + .5 - c.w / 2, y + .5 - c.h / 2)
            if c.w * .42 < d < c.w * .47:
                c.set(x, y, frosting.at(.92))
                if int(d * .8) % 3 == 0:
                    c.set(x, y, mix(frosting.at(1), (255, 255, 255), .4))
    # pink icing drizzle spiral
    pink = (244, 120, 158)
    for i in range(150):
        a = i * .21
        r = (i / 150.0) ** .72 * c.w * .34
        x = int(c.w / 2 + math.cos(a) * r)
        y = int(c.h / 2 + math.sin(a) * r)
        if 0 <= x < c.w and 0 <= y < c.h:
            c.set(x, y, pink if i % 7 else (255, 180, 200))
    sprinkle(c, 0, 0, sprinkle_cols, seed + 3, density=.035, length=2, size=1)
    # cherry with stem
    cx, cy = c.w * .5, c.h * .52
    c.disc(cx, cy, max(2.0, c.w * .085), cherry)
    c.set(int(cx) - 1, int(cy) - 1, (255, 220, 225))
    c.set(int(cx), int(cy) - 2, (120, 170, 90))
    c.set(int(cx) + 1, int(cy) - 3, (120, 170, 90))
    bevel(c, frosting, 1, .12)


def cake_side(c, seed, ramp, frosting, sprinkle_cols, cherry):
    # three sponge layers separated by cream
    layer = c.h / 3.0
    for y in range(c.h):
        ly = y % layer
        for x in range(c.w):
            if ly < 2:
                c.set(x, y, frosting.at(.62))
            elif ly < 4:
                c.set(x, y, frosting.at(.88))
            else:
                c.set(x, y, ramp.at(.48 + (ly / layer) * .12))
    # frosting drip from the top
    for x in range(c.w):
        h = 4 + int(ValueNoise(seed).at(x * .7, 1.5) * 5)
        for y in range(h):
            c.set(x, y, frosting.at(.65 + .2 * (1 - y / h)))
    sprinkle(c, 0, 0, sprinkle_cols, seed + 4, density=.012, length=1, size=1)
    c.disc(c.w * .5, c.h * .08, max(1.2, c.w * .055), cherry)


def cake_inner(c, seed, ramp):
    _noise_fill(c, ramp, seed, scale=5, octaves=3, contrast=.4)


def bookshelf(c, seed, ramp, seam, book_cols):
    planks(c, seed, ramp, seam, boards=5, knot=False)
    rnd = random.Random(seed + 3)
    # two shelves of candy-coloured books
    for shelf in (0, 1):
        y0 = 5 + shelf * (c.h // 2)
        x = 2
        while x < c.w - 3:
            w = rnd.randrange(2, 4)
            h = rnd.randrange(c.h // 4 - 2, c.h // 4 + 1)
            col = book_cols[rnd.randrange(len(book_cols))]
            for yy in range(y0, min(c.h - 2, y0 + h)):
                for xx in range(x, min(c.w - 2, x + w)):
                    cc = col
                    if xx == x:
                        cc = at_luma(col, luma(col) * .7)
                    elif xx == x + w - 1:
                        cc = mix(col, (255, 255, 255), .3)
                    c.set(xx, yy, cc)
            x += w + 1


def honeycomb(c, seed, ramp, wax):
    """Offset hex lattice: honey cells with wax walls."""
    s = 8.0
    for y in range(c.h):
        row = int(round(y / s))
        for x in range(c.w):
            best = 1e9
            second = 1e9
            best_h = 0
            for rr in (row - 1, row, row + 1):
                off = (s * .5) if rr % 2 else 0.0
                for k in (-1, 0, 1):
                    cxx = off + k * s
                    # keep centres in the 0..32 window
                    for rep in (-1, 0, 1):
                        cx = cxx + rep * c.w
                        cy = rr * s
                        d = math.hypot(x + .5 - cx, y + .5 - cy)
                        if d < best:
                            second = best
                            best = d
                            best_h = (int(cx) * 37 + int(cy) * 91) & 0xff
                        elif d < second:
                            second = d
            edge = (second - best) * .5
            if edge < .85:
                c.set(x, y, wax)
                if edge < .30:
                    c.set(x, y, mix(wax, (255, 240, 190), .35))
                continue
            t = .82 - (best / (s * .62)) * .42 + (best_h % 11) * .006
            c.set(x, y, ramp.at(max(0, min(1, t))))
    # tiny wax sheen
    bevel(c, ramp, 1, .10)


def sponge(c, seed, ramp, hole):
    _noise_fill(c, ramp, seed, scale=4, octaves=3, contrast=.5)
    rnd = random.Random(seed + 1)
    for _ in range(c.w * c.h // 28):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        r = rnd.choice([1, 1, 2])
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r:
                    c.set((x + xx) % c.w, (y + yy) % c.h, hole)


# ------------------------------------------------------------------ plants

def melon(c, seed, ramp, flesh, seed_col):
    _noise_fill(c, ramp, seed, scale=3, octaves=3, contrast=.4)
    for y in range(c.h):
        for x in range(c.w):
            # vertical watermelon stripes
            if int(x / (c.w / 7.0)) % 2 == 0:
                cc = c.get(x, y)
                c.set(x, y, mix(cc, ramp.at(.8), .35))
    rnd = random.Random(seed + 2)
    for _ in range(6):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        c.set(x, y, seed_col)


def pumpkin(c, seed, ramp, stem_col):
    _noise_fill(c, ramp, seed, scale=4, octaves=3, contrast=.5)
    for x in range(c.w):
        if int(x / (c.w / 9.0)) % 2 == 0:
            for y in range(c.h):
                cc = c.get(x, y)
                c.set(x, y, at_luma(cc, luma(cc) - 12))
    for y in range(c.h):
        if y < c.h * .08:
            for x in range(c.w):
                c.set(x, y, stem_col)


def cactus(c, seed, ramp, spine):
    _noise_fill(c, ramp, seed, scale=5, octaves=3, contrast=.35)
    for x in range(c.w):
        if x % 8 == 2:
            for y in range(c.h):
                c.set(x, y, at_luma(c.get(x, y), luma(c.get(x, y)) - 18))
    rnd = random.Random(seed)
    for _ in range(c.w):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        c.set(x, y, spine)
        c.set((x + 1) % c.w, y, spine)


# ------------------------------------------------------------------ masonry

def sandstone(c, seed, ramp, band, speckle=None, layers=3, wave=.6):
    """Soft layered sugar-sandstone."""
    n = ValueNoise(seed)
    bh = c.h / layers
    for y in range(c.h):
        ly = y % bh
        for x in range(c.w):
            v = n.fbm(x * .12, y * .35, 3, .55, 4)
            t = .62 + (v - .5) * .25
            if ly < 1.0:
                t -= .16
            elif ly > bh - 1.4:
                t += .10
            if n.at(x * .5, y * .8) > .82:
                t += .08
            c.set(x, y, ramp.at(max(0, min(1, t))))
    if speckle:
        rnd = random.Random(seed + 2)
        for _ in range(c.w * c.h // 90):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, mix(ramp.at(.8), speckle, .5))
    # top and bottom banding
    for x in range(c.w):
        if n.at(x * .4, 2.2) > .5:
            c.set(x, 0, band.at(.85))
            c.set(x, c.h - 1, band.at(.25))
    bevel(c, ramp, 1, .12)


def terracotta(c, seed, ramp, band=None):
    """Smooth pressed-sugar clay with faint horizontal strata."""
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            v = n.fbm(x * .07, y * .1, 3, .55, 4)
            t = .60 + (v - .5) * .20
            t += math.sin(y * .55) * .018
            if band and n.at(x * .2, y * .9) > .86:
                t += .06
            c.set(x, y, ramp.at(max(0, min(1, t))))
    bevel(c, ramp, 1, .08)


def concrete(c, seed, ramp):
    """Almost-flat poured fondant with a faint tooth."""
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            t = .62 + (n.at(x * .9, y * .9) - .5) * .07
            c.set(x, y, ramp.at(max(0, min(1, t))))
    bevel(c, ramp, 1, .05)


def glowstone(c, seed, ramp, spark=(255, 250, 210)):
    """Bubbly sugar crystal cluster that reads as a light source."""
    n = ValueNoise(seed)
    _noise_fill(c, ramp, seed, scale=4.0, octaves=3, gain=.55, contrast=.8)
    rnd = random.Random(seed + 2)
    for _ in range(c.w * c.h // 26):
        cx, cy = rnd.randrange(c.w), rnd.randrange(c.h)
        r = rnd.choice([1, 1, 2])
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r:
                    edge = abs(xx) + abs(yy) >= r
                    c.set((cx + xx) % c.w, (cy + yy) % c.h,
                          ramp.at(.32) if edge else ramp.at(.92))
        c.set(cx % c.w, cy % c.h, spark)
    bevel(c, ramp, 1, .18)


def snow(c, seed, ramp, sparkle=True):
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            t = .80 + (n.fbm(x * .16, y * .16, 3) - .5) * .12
            c.set(x, y, ramp.at(max(0, min(1, t))))
    if sparkle:
        rnd = random.Random(seed + 1)
        for _ in range(c.w * c.h // 90):
            c.set(rnd.randrange(c.w), rnd.randrange(c.h), (255, 255, 255))
    bevel(c, ramp, 1, .10)


def mushroom_skin(c, seed, ramp, spot, spots=5, freckle=True):
    """A soft candy cap with rounded cream spots.

    Spots wrap at the tile edge so the mushroom cap does not show seams.
    """
    rp = get_ramp(ramp)
    sp = get_ramp(spot)
    _noise_fill(c, rp, seed, scale=3.2, octaves=3, gain=.55, contrast=.9)
    rnd = random.Random(seed + 17)
    for _ in range(spots):
        cx = rnd.uniform(0, c.w)
        cy = rnd.uniform(0, c.h)
        rx = rnd.uniform(1.7, 3.5)
        ry = rx * rnd.uniform(.65, 1.0)
        for yy in range(-int(ry) - 1, int(ry) + 2):
            for xx in range(-int(rx) - 1, int(rx) + 2):
                d = (xx / rx) ** 2 + (yy / ry) ** 2
                if d <= 1.0:
                    edge = d > .60
                    c.set(int(cx + xx) % c.w, int(cy + yy) % c.h,
                          sp.at(.62 if edge else .94))
    if freckle:
        for _ in range(18):
            x, y = rnd.randrange(c.w), rnd.randrange(c.h)
            c.set(x, y, sp.at(.82) if rnd.random() < .5 else rp.at(.18))
    bevel(c, rp, 1, .10)


def mushroom_stem(c, seed, ramp):
    rp = get_ramp(ramp)
    _noise_fill(c, rp, seed, scale=4.5, octaves=3, gain=.5, contrast=.75)
    rnd = random.Random(seed + 3)
    for _ in range(9):
        x = rnd.randrange(c.w)
        length = rnd.randrange(8, 23)
        y0 = rnd.randrange(c.h)
        tone = .26 if rnd.random() < .55 else .86
        for i in range(length):
            y = (y0 + i) % c.h
            c.set(x, y, rp.at(tone))
            if c.w > 16 and rnd.random() < .25:
                c.set((x + 1) % c.w, y, rp.at(tone + .08))
    bevel(c, rp, 1, .08)


def mushroom_inside(c, seed, ramp):
    rp = get_ramp(ramp)
    _noise_fill(c, rp, seed, scale=3.0, octaves=3, gain=.55, contrast=.55)
    rnd = random.Random(seed + 5)
    for _ in range(c.w * c.h // 14):
        x, y = rnd.randrange(c.w), rnd.randrange(c.h)
        c.set(x, y, rp.at(.28 if rnd.random() < .55 else .88))
        if rnd.random() < .30:
            c.set((x + 1) % c.w, (y + 1) % c.h, rp.at(.36))
    bevel(c, rp, 1, .04)


def ice(c, seed, ramp, crack=(210, 245, 255)):
    n = ValueNoise(seed)
    for y in range(c.h):
        for x in range(c.w):
            t = .58 + (n.fbm(x * .13, y * .13, 4) - .5) * .30
            c.set(x, y, ramp.at(max(0, min(1, t))))
    for _ in range(4):
        x = random.Random(seed + _).randrange(c.w)
        y = random.Random(seed + _ + 1).randrange(c.h)
        dx, dy = random.Random(seed + _ + 2).choice([(1, 0), (0, 1), (1, 1), (1, -1)])
        for i in range(random.Random(seed + _ + 3).randrange(3, 8)):
            c.set((x + dx * i) % c.w, (y + dy * i) % c.h, crack)
    bevel(c, ramp, 1, .08)
