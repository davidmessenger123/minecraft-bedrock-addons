"""Assemble the distributable Candyland resource pack.

Generates the pack icon and manifest, then packages the finished resource_pack
tree as an .mcpack (and a plain .zip for manual installs).

Run from the project root:

    python3 tools/build_pack.py
"""
import json
import math
import os
import random
import shutil
import sys
import uuid
import zipfile

from candy import Canvas, mix, clamp
import pnglib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "resource_pack")
DIST = os.path.join(ROOT, "dist")
VERSION = [1, 0, 2]
VERSION_STR = ".".join(map(str, VERSION))
PACK_NAME = "Candyland"


# ------------------------------------------------------------------ colour
DEEP_PLUM = (42, 22, 38)
GRAPE = (86, 44, 92)
BUBBLEGUM = (255, 143, 179)
CHERRY = (239, 90, 116)
CREAM = (255, 243, 220)
CARAMEL = (176, 102, 57)
MINT = (143, 227, 192)
LEMON = (255, 226, 122)
BLUEBERRY = (143, 199, 255)
ORANGE = (255, 179, 107)
SPRINKLES = (BUBBLEGUM, MINT, LEMON, BLUEBERRY, ORANGE, CREAM)


# ------------------------------------------------------------------ drawing
def caps(c, x0, y0, x1, y1, r, col, a=255):
    """Rounded capsule from (x0,y0) to (x1,y1)."""
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 1.4))
    for i in range(n + 1):
        t = i / n
        c.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, col, a)


def sparkle(c, cx, cy, r, col):
    """Four-point sugar sparkle."""
    for d in range(-r, r + 1):
        w = int((1.0 - abs(d) / (r + 1.0)) * r * 0.13) + 1
        c.rect(cx - w, cy + d, cx + w + 1, cy + d + 1, col)
        c.rect(cx + d, cy - w, cx + d + 1, cy + w + 1, col)


def blend_ellipse(c, cx, cy, rx, ry, col, a):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0:
                c.blend(x, y, col, a)


def icon_canvas():
    """1024x1024 master, box-downsampled to 256x256."""
    S = 1024
    c = Canvas(S, S)
    cx, cy, R = 512.0, 432.0, 286.0

    # Deep plum-to-grape backdrop with a warm candy glow behind the pop.
    for y in range(S):
        t = y / (S - 1.0)
        base = mix(DEEP_PLUM, GRAPE, t ** 0.82)
        for x in range(S):
            dx = (x - cx) / S
            dy = (y - cy) / S
            glow = max(0.0, 1.0 - (dx * dx + dy * dy) * 3.3)
            col = mix(base, BUBBLEGUM, glow * .16)
            stripe = ((x + y) // 128) & 1
            if stripe:
                col = tuple(clamp(v + 5) for v in col)
            c.set(x, y, col)

    # Soft vignette.
    for y in range(S):
        for x in range(S):
            edge = min(x, y, S - 1 - x, S - 1 - y) / 110.0
            if edge < 1.0:
                c.blend(x, y, (18, 8, 20), int((1.0 - edge) * 105))

    # Background sprinkles, kept clear of the pop itself.
    rnd = random.Random(7317)
    for _ in range(42):
        x0 = rnd.uniform(40, S - 40)
        y0 = rnd.uniform(40, S - 40)
        if math.hypot(x0 - cx, y0 - cy) < R + 90:
            continue
        if abs(x0 - cx) < 105 and y0 > cy:
            continue
        ang = rnd.uniform(0, math.tau)
        ln = rnd.uniform(38, 70)
        x1, y1 = x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln
        col = rnd.choice(SPRINKLES)
        caps(c, x0, y0, x1, y1, rnd.choice((7, 8, 9)), col)
        # tiny highlight along the top of the sprinkle
        caps(c, x0 - 2, y0 - 3, x1 - 2, y1 - 3, 2, CREAM, 70)

    for x, y, r in ((146, 150, 36), (872, 214, 27), (812, 808, 34),
                    (196, 832, 24)):
        sparkle(c, x, y, r, CREAM)
        sparkle(c, x, y, max(4, r // 3), LEMON)

    # Lollipop shadow.
    blend_ellipse(c, cx + 26, cy + 34, R + 12, R + 12, (20, 8, 22), 110)

    # Stick: caramel outline, candy-striped cream core.
    stick_top, stick_bottom = 604, 952
    caps(c, cx, stick_top, cx, stick_bottom, 48, CARAMEL)
    caps(c, cx, stick_top + 8, cx, stick_bottom - 8, 38, CREAM)
    bottom_cap = stick_bottom - 46
    for y in range(stick_top + 8, stick_bottom - 8):
        if y > bottom_cap:
            half = math.sqrt(max(0.0, 38.0 ** 2 - (y - bottom_cap) ** 2))
        else:
            half = 38.0
        for x in range(int(cx - half), int(cx + half) + 1):
            if int(y + (x - cx) * 3) // 38 & 1:
                col = BUBBLEGUM
            else:
                col = CREAM
            if x > cx + 18:
                col = tuple(clamp(v - 16) for v in col)
            c.set(x, y, col)

    # Outer candy rim.
    c.disc(cx, cy, R + 12, CHERRY)
    c.disc(cx, cy, R + 4, BUBBLEGUM)
    c.disc(cx, cy, R - 4, CREAM)

    # Peppermint spiral, drawn from scratch.
    for y in range(int(cy - R) - 1, int(cy + R) + 2):
        for x in range(int(cx - R) - 1, int(cx + R) + 2):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            if d > R - 4:
                continue
            ang = math.atan2(dy, dx)
            phase = (d * 0.0185 + (ang / math.tau) * 2.0) % 1.0
            if phase < 0.465:
                col = CHERRY
            else:
                col = CREAM
            # subtle shaded rim inside the disc
            if d > R - 22:
                col = mix(col, CARAMEL, .12)
            c.set(x, y, col)

    # Glossy highlight on the upper-left of the candy.
    blend_ellipse(c, cx - 92, cy - 92, 118, 72, (255, 255, 255), 42)
    blend_ellipse(c, cx - 120, cy - 116, 38, 22, (255, 255, 255), 95)

    # A few sugar crystals on the cream bands.
    rnd = random.Random(88)
    for _ in range(16):
        ang = rnd.uniform(0, math.tau)
        rr = rnd.uniform(30, R - 45)
        x = int(cx + math.cos(ang) * rr)
        y = int(cy + math.sin(ang) * rr)
        if c.get(x, y)[:3] == CREAM:
            c.disc(x, y, rnd.choice((2, 3)), (255, 255, 255), 180)

    return c


def downsample(c, factor):
    out = Canvas(c.w // factor, c.h // factor)
    area = factor * factor
    src = c.px
    for oy in range(out.h):
        for ox in range(out.w):
            r = g = b = a = 0
            for sy in range(oy * factor, (oy + 1) * factor):
                base = (sy * c.w + ox * factor) * 4
                for sx in range(factor):
                    i = base + sx * 4
                    r += src[i]
                    g += src[i + 1]
                    b += src[i + 2]
                    a += src[i + 3]
            j = (oy * out.w + ox) * 4
            out.px[j] = r // area
            out.px[j + 1] = g // area
            out.px[j + 2] = b // area
            out.px[j + 3] = a // area
    return out


def build_icon():
    master = icon_canvas()
    icon = downsample(master, 4)
    path = os.path.join(PACK, "pack_icon.png")
    pnglib.png_write(path, icon.w, icon.h, icon.px)
    print("pack icon ->", path, (icon.w, icon.h))
    return path


def camera_icon():
    """Small candy camera icon for the legacy 'camera' atlas entry."""
    c = Canvas(32, 32)
    outline = (61, 33, 58)
    body = (255, 143, 179)
    body_dark = (222, 98, 132)
    lens = (91, 52, 102)
    lens_light = (143, 199, 255)
    cream = (255, 243, 220)
    # body + viewfinder hump
    c.rect(3, 9, 29, 25, outline)
    c.rect(4, 10, 28, 24, body)
    c.rect(9, 6, 19, 11, outline)
    c.rect(10, 7, 18, 10, (143, 227, 192))
    c.rect(4, 21, 28, 24, body_dark)
    # flash and shutter
    c.rect(5, 11, 10, 14, cream)
    c.rect(6, 12, 9, 13, LEMON)
    c.rect(23, 6, 27, 9, outline)
    c.rect(24, 7, 26, 8, CHERRY)
    # lens
    c.disc(17, 17, 7, outline)
    c.disc(17, 17, 6, cream)
    c.disc(17, 17, 5, lens)
    c.disc(17, 17, 3, (71, 143, 214))
    c.disc(15, 15, 2, lens_light)
    c.set(15, 15, (255, 255, 255))
    # little highlight on the body corner
    c.rect(5, 11, 7, 12, (255, 214, 228))
    return c


def build_extras():
    """Cover texture references that the vanilla samples leave dangling."""
    extra = []
    cake_side = os.path.join(PACK, "textures", "blocks", "cake_side.png")
    cake = os.path.join(PACK, "textures", "blocks", "cake.png")
    if os.path.isfile(cake_side):
        shutil.copyfile(cake_side, cake)
        extra.append(cake)
    cam = os.path.join(PACK, "textures", "items", "camera.png")
    os.makedirs(os.path.dirname(cam), exist_ok=True)
    c = camera_icon()
    pnglib.png_write(cam, c.w, c.h, c.px)
    extra.append(cam)

    # The 1.26.60 terrain atlas still contains two legacy hanging_pale_moss
    # aliases, while the shipped colour files use pale_hanging_moss.  Keep the
    # default atlas byte-for-byte and provide the two alias files beside the
    # real textures.
    blocks_dir = os.path.join(PACK, "textures", "blocks")
    for real, alias in (
        ("pale_hanging_moss_middle.png", "hanging_pale_moss_middle.png"),
        ("pale_hanging_moss_tip.png", "hanging_pale_moss_tip.png"),
    ):
        source = os.path.join(blocks_dir, real)
        target = os.path.join(blocks_dir, alias)
        if os.path.isfile(source):
            shutil.copyfile(source, target)
            extra.append(target)
    for path in extra:
        print("extra ->", path)
    return extra


# ------------------------------------------------------------------ manifest
def build_manifest():
    ns = uuid.NAMESPACE_URL
    header_id = str(uuid.uuid5(ns, "https://candyland.invalid/resourcepack/header/v1"))
    module_id = str(uuid.uuid5(ns, "https://candyland.invalid/resourcepack/resources/v1"))
    manifest = {
        "format_version": 2,
        "header": {
            "name": PACK_NAME,
            "description": "Every vanilla colour texture, reimagined as candy: blocks, items, mobs, skies and menus.",
            "uuid": header_id,
            "version": VERSION,
            "min_engine_version": [1, 26, 60],
        },
        "modules": [
            {
                "description": "Candyland resource pack",
                "type": "resources",
                "uuid": module_id,
                "version": VERSION,
            }
        ],
        "metadata": {
            "authors": ["Candyland"],
            "license": "Fan project. Not affiliated with Mojang or Microsoft.",
        },
    }
    path = os.path.join(PACK, "manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    print("manifest ->", path)
    return manifest


def write_lang():
    texts = os.path.join(PACK, "texts")
    os.makedirs(texts, exist_ok=True)
    path = os.path.join(texts, "en_US.lang")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("pack.name=Candyland\n")
        fh.write("pack.description=Every vanilla texture, reimagined as candy.\n")
    return path


# ------------------------------------------------------------------ package
def iter_pack_files():
    for root, dirs, files in os.walk(PACK):
        dirs.sort()
        for fn in sorted(files):
            if fn in (".DS_Store",) or fn.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, PACK).replace(os.sep, "/")
            yield full, rel


def package():
    os.makedirs(DIST, exist_ok=True)
    base = f"Candyland-v{VERSION_STR}"
    mcpack = os.path.join(DIST, base + ".mcpack")
    plain_zip = os.path.join(DIST, base + ".zip")
    for path in (mcpack, plain_zip):
        if os.path.exists(path):
            os.remove(path)
    with zipfile.ZipFile(mcpack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for full, rel in iter_pack_files():
            z.write(full, rel)
    shutil.copyfile(mcpack, plain_zip)
    print("packaged ->", mcpack, os.path.getsize(mcpack) // 1024, "KiB")
    print("packaged ->", plain_zip)
    return mcpack, plain_zip


def main():
    if "--icon-only" in sys.argv:
        build_icon()
        return
    build_icon()
    build_manifest()
    write_lang()
    build_extras()
    package()
    print("done")


if __name__ == "__main__":
    main()
