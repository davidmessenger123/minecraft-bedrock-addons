"""Style-transfer helpers: turn any vanilla texture into candy art.

The silhouette and shading are kept; every colour is replaced by a tone from
a candy ramp.  No original pixels survive, so the result is a genuine
replacement rather than a recolour of the source.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from candy import Canvas, clamp, get_ramp, mix, luma, Ramp  # noqa: E402
import pnglib  # noqa: E402

SRC_ROOT = os.environ.get(
    "BEDROCK_SAMPLES", "/tmp/opencode/bedrock-samples/resource_pack")
SRC = os.path.join(SRC_ROOT, "textures")


CACHE = "/tmp/opencode/imgcache"


def src_path(entry):
    return os.path.join(SRC, entry["base"] + "." + entry["src_ext"])


def load_source(entry):
    """Decode a vanilla texture, normalising exotic PNGs with ImageMagick."""
    path = src_path(entry)
    try:
        return pnglib.read_image(path)
    except Exception:
        os.makedirs(CACHE, exist_ok=True)
        name = entry["base"].replace("/", "_") + ".png"
        out = os.path.join(CACHE, name)
        if not os.path.exists(out):
            import subprocess
            subprocess.run(["magick", path, "-depth", "8",
                            "-define", "png:color-type=6", out], check=True)
        return pnglib.read_png(out)


def scale_for(entry, target=32):
    """Integer upscale that brings a 16px tile to the pack resolution."""
    w, h = entry["w"], entry["h"]
    if entry["frames"] > 1:
        return max(1, target // w)
    short = min(w, h)
    if short >= target:
        return 1
    return max(1, target // short)


def _range(px):
    """2nd..98th percentile luma, so low-contrast art still reads."""
    vals = []
    for i in range(0, len(px), 4 * 7):
        if px[i + 3]:
            vals.append(0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2])
    if not vals:
        return 0.0, 1.0
    vals.sort()
    lo = vals[int(len(vals) * .02)] / 255.0
    hi = vals[min(len(vals) - 1, int(len(vals) * .98))] / 255.0
    if hi - lo < .10:
        mid = (hi + lo) / 2
        lo, hi = mid - .05, mid + .05
    return lo, hi


def restyle(entry, ramp, scale=None, keep_hue=0.0, contrast=1.0,
            brightness=0.0, grey=False, saturation=1.0, flip=False):
    w, h, px = load_source(entry)
    ramp = get_ramp(ramp) if isinstance(ramp, str) else ramp
    lo, hi = _range(px)
    if scale is None:
        scale = scale_for(entry)
    out = Canvas(w * scale, h * scale)
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            r, g, b, a = px[i], px[i + 1], px[i + 2], px[i + 3]
            if not a:
                continue
            l = ((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 - lo) / (hi - lo)
            l = (l - .5) * contrast + .5 + brightness
            col = ramp.at(clamp(l, 0.0, 1.0))
            if keep_hue:
                col = mix(col, (r, g, b), keep_hue)
            if grey:
                gg = int(90 + clamp(l, 0.0, 1.0) * 162)
                col = (gg, gg, gg)
            for sy in range(scale):
                for sx in range(scale):
                    out.set(x * scale + sx, y * scale + sy, col, a)
    return out


def has_transparency(entry):
    w, h, px = load_source(entry)
    return any(px[i] < 255 for i in range(3, len(px), 4))


def tint(c, colour, strength=1.0):
    """Multiply a canvas toward a colour (dye variants)."""
    for y in range(c.h):
        for x in range(c.w):
            cc = c.get(x, y)
            if cc[3]:
                col = tuple(cc[k] * (1 - strength) + cc[k] * colour[k] / 255.0
                            * strength for k in range(3))
                c.set(x, y, col, cc[3])
    return c


def glow(c, colour, strength=0.35, mask_luma=0.55):
    """Add a warm emissive bloom to bright pixels."""
    for y in range(c.h):
        for x in range(c.w):
            cc = c.get(x, y)
            if cc[3] and luma(cc) / 255.0 > mask_luma:
                c.set(x, y, mix(cc, colour, strength), cc[3])
    return c


GREY_RAMP = Ramp([(64, 64, 64), (104, 104, 104), (144, 144, 144),
                  (184, 184, 184), (220, 220, 220), (252, 252, 252)])

# Pastel neutral used by UI art: white masks stay white, panels pick up a
# faint lilac candy tint.
UI_NEUTRAL = get_ramp("silver_lilac")


def candy_paint(entry, scale=None, sat_boost=1.0, contrast=1.05,
                brightness=0.0, outline=None, grey=False, neutral=None):
    """Map every pixel to the candy ramp of its hue family.

    Keeps multi-colour art (flowers, items, skins) readable while replacing
    the palette wholesale.  `neutral` overrides the ramp used for greys, so
    UI panels and white tint masks can pick up a pastel candy tint.
    """
    w, h, px = load_source(entry)
    lo, hi = _range(px)
    if scale is None:
        scale = scale_for(entry)
    if neutral is not None and not isinstance(neutral, Ramp):
        neutral = get_ramp(neutral)
    out = Canvas(w * scale, h * scale)
    cache = {}
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            r, g, b, a = px[i], px[i + 1], px[i + 2], px[i + 3]
            if not a:
                continue
            l = ((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 - lo) / (hi - lo)
            l = (l - .5) * contrast + .5 + brightness
            if grey:
                col = GREY_RAMP.at(clamp(l, 0.0, 1.0))
            else:
                key = (r >> 4, g >> 4, b >> 4)
                col = cache.get(key)
                if col is None:
                    col = _paint_pixel(r, g, b, l, neutral)
                    cache[key] = col
            for sy in range(scale):
                for sx in range(scale):
                    out.set(x * scale + sx, y * scale + sy, col, a)
    if outline is not None:
        silhouette_outline(out, outline)
    return out


def _paint_pixel(r, g, b, l, neutral=None):
    from candy import rgb_to_hsv
    h, s, v = rgb_to_hsv(r, g, b)
    if s < .10:
        if neutral is not None:
            return neutral.at(clamp(l, 0.0, 1.0))
        key = "marshmallow" if l > .55 else ("silver_sugar" if l > .3
                                             else "licorice")
        return get_ramp(key).at(clamp(l, 0.0, 1.0))
    deg = h * 360.0
    if deg < 18 or deg >= 345:
        key = "cherry"
    elif deg < 42:
        key = "orange_sherbet" if l > .42 else "milk_chocolate"
    elif deg < 66:
        key = "lemon_drop" if l > .42 else "caramel"
    elif deg < 105:
        key = "sour_apple"
    elif deg < 160:
        key = "mint"
    elif deg < 195:
        key = "blue_raspberry"
    elif deg < 250:
        key = "blueberry"
    elif deg < 288:
        key = "grape_taffy"
    elif deg < 320:
        key = "bubblegum"
    else:
        key = "cotton_candy"
    return get_ramp(key).at(clamp(l, 0.0, 1.0))


def silhouette_outline(c, colour, thickness=1):
    """Dark candy outline around alpha (makes sprites pop on any background)."""
    src = c.px[:]
    w, h = c.w, c.h
    for y in range(h):
        for x in range(w):
            if src[(y * w + x) * 4 + 3]:
                continue
            near = False
            for dy in range(-thickness, thickness + 1):
                for dx in range(-thickness, thickness + 1):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h:
                        if src[(yy * w + xx) * 4 + 3]:
                            near = True
            if near:
                c.set(x, y, colour)
    return c
