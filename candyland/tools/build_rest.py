"""Render every remaining texture category into the resource pack.

Blocks and items are built by their own scripts.  This pass covers entities,
UI, GUI, trims, armour, paintings, maps, particles, environment effects and
the root atlases.  Nothing here is upscaled: entity UVs and UI pixel grids
must stay at their original resolution.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import colormaps  # noqa: E402
import environment  # noqa: E402
import pnglib  # noqa: E402
import restyle  # noqa: E402
from candy import Canvas, clamp, get_ramp, hex_rgb, make_ramp, mix  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "resource_pack")
TEX = os.path.join(PACK, "textures")
SRC = restyle.SRC

UI_NEUTRAL = make_ramp("#c9c2dc", shadow="#4f4862", light="#ffffff")

BANNER = ("entity/banner/", "entity/shield_patterns/")
TRIM_PALETTES = {
    "amethyst": ("amethyst_candy", 0.0),
    "copper_darker": ("copper_wrap", -0.16),
    "copper": ("copper_candy", 0.0),
    "diamond_darker": ("diamond_candy", -0.15),
    "diamond": ("diamond_candy", 0.0),
    "emerald": ("emerald_candy", 0.0),
    "gold_darker": ("gold_wrap", -0.15),
    "gold": ("gold_candy", 0.0),
    "iron_darker": ("silver_lilac", -0.12),
    "iron": ("iron_candy", 0.0),
    "lapis": ("lapis_candy", 0.0),
    "netherite_darker": ("netherite_dark", -0.10),
    "netherite": ("licorice", 0.0),
    "quartz": ("quartz_candy", 0.0),
    "redstone": ("redstone_candy", 0.0),
    "resin": ("resin_caramel", 0.0),
    "trim_palette": ("marshmallow", 0.0),
}
GREY_PARTICLES = ("particle/biome_tinted_leaves_atlas",
                  "particle/pale_oak_leaves_atlas")


def rel_path(base):
    return base.split("/", 1)[1] if "/" in base else base


def out_path(entry):
    return os.path.join(TEX, *entry["base"].split("/")) + "." + entry["src_ext"]


def write(entry, c):
    path = out_path(entry)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = entry["src_ext"]
    if ext == "tga":
        pnglib.tga_write(path, c.w, c.h, c.px)
    elif ext in ("jpg", "jpeg"):
        cache = "/tmp/opencode/jpgcache"
        os.makedirs(cache, exist_ok=True)
        tmp = os.path.join(cache, str(abs(hash(entry["base"]))) + ".png")
        pnglib.png_write(tmp, c.w, c.h, c.px)
        subprocess.run(["magick", tmp, "-background", "#2a1626",
                        "-alpha", "remove", "-alpha", "off", "-quality", "92",
                        path], check=True)
    else:
        pnglib.png_write(path, c.w, c.h, c.px)


def expected_dims(entry):
    return entry["w"], entry["h"]


def grey(entry, contrast=1.0):
    return restyle.restyle(entry, "marshmallow", scale=1, grey=True,
                           contrast=contrast)


def paint(entry, contrast=1.03, neutral=None, brightness=0.0):
    return restyle.candy_paint(entry, scale=1, contrast=contrast,
                               neutral=neutral, brightness=brightness)


def environment_canvas(name):
    if name == "clouds":
        return environment.clouds(256)
    if name == "sun":
        return environment.sun(False)
    if name == "sun_vv":
        return environment.sun(True)
    if name == "moon_phases":
        return environment.moon_phases()
    if name == "weather":
        return environment.weather()
    if name.startswith("destroy_stage_"):
        return environment.destroy_stage(int(name.rsplit("_", 1)[1]))
    if name == "end_portal_colors":
        return environment.end_portal_colors()
    if name == "end_sky":
        return environment.end_sky()
    if name == "end_flash":
        return environment.end_flash()
    raise KeyError("no environment recipe for " + name)


def candy_swirl(c, cx, cy, radius, shell, stripe, cream, turns=2.0):
    """Round peppermint candy used by the store art and sidebar badges."""
    c.disc(cx + radius * .12, cy + radius * .15, radius * 1.02,
           (32, 14, 30), 95)
    c.disc(cx, cy, radius, shell)
    c.disc(cx, cy, radius - max(3, radius // 13), cream)
    for y in range(int(cy - radius) - 1, int(cy + radius) + 2):
        for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
            dx, dy = x + .5 - cx, y + .5 - cy
            d = math.hypot(dx, dy)
            if d > radius - max(3, radius // 13):
                continue
            ang = math.atan2(dy, dx)
            phase = ((d / radius) * 3.2 + (ang / math.tau) * turns) % 1.0
            if phase < .47:
                c.set(x, y, stripe)
    # cream gloss
    rx, ry = radius * .38, radius * .24
    gx, gy = cx - radius * .34, cy - radius * .38
    for y in range(int(gy - ry), int(gy + ry) + 1):
        for x in range(int(gx - rx), int(gx + rx) + 1):
            if ((x + .5 - gx) / rx) ** 2 + ((y + .5 - gy) / ry) ** 2 <= 1:
                c.blend(x, y, (255, 255, 255), 42)


def promo_badge(entry):
    """Original candy badge for the Marketplace sidebar icon slots."""
    w, h = entry["w"], entry["h"]
    seed = abs(hash(entry["base"])) % 99999
    rnd = random.Random(seed)
    c = Canvas(w, h)
    palettes = [
        ((255, 143, 179), (239, 90, 116), (255, 243, 220)),
        ((143, 227, 192), (52, 168, 132), (255, 250, 230)),
        ((255, 226, 122), (239, 166, 56), (255, 246, 225)),
        ((143, 199, 255), (85, 131, 219), (242, 247, 255)),
        ((196, 150, 240), (128, 75, 185), (250, 240, 255)),
        ((255, 179, 107), (211, 101, 57), (255, 242, 224)),
    ]
    shell, stripe, cream = palettes[seed % len(palettes)]
    # backdrop
    for y in range(h):
        t = y / max(1, h - 1)
        base = mix((39, 20, 36), mix((77, 39, 81), shell, .12), t)
        for x in range(w):
            dx, dy = (x - w * .5) / w, (y - h * .48) / h
            glow = max(0.0, 1.0 - (dx * dx + dy * dy) * 3.8)
            col = mix(base, shell, glow * .13)
            if ((x + y) // max(8, w // 8)) & 1:
                col = tuple(clamp(v + 4) for v in col)
            c.set(x, y, col)
    # frame + confetti
    edge = max(2, w // 40)
    c.rect(edge, edge, w - edge, edge + 2, cream)
    c.rect(edge, h - edge - 2, w - edge, h - edge, cream)
    c.rect(edge, edge, edge + 2, h - edge, cream)
    c.rect(w - edge - 2, edge, w - edge, h - edge, cream)
    for _ in range(max(12, w // 14)):
        x0, y0 = rnd.uniform(10, w - 10), rnd.uniform(10, h - 10)
        if math.hypot(x0 - w * .5, y0 - h * .5) < min(w, h) * .34:
            continue
        ang = rnd.uniform(0, math.tau)
        ln = rnd.uniform(w * .025, w * .06)
        col = rnd.choice((cream, shell, (143, 227, 192), (255, 226, 122),
                          (143, 199, 255)))
        steps = max(4, int(ln))
        for i in range(steps):
            c.disc(x0 + math.cos(ang) * ln * i / steps,
                   y0 + math.sin(ang) * ln * i / steps,
                   max(1, w // 100), col)
    # candy
    candy_swirl(c, w * .5, h * .49, min(w, h) * .29, shell, stripe, cream,
                turns=1 + (seed % 3))
    for _ in range(6):
        a = rnd.uniform(0, math.tau)
        d = min(w, h) * rnd.uniform(.36, .44)
        sx, sy = w * .5 + math.cos(a) * d, h * .49 + math.sin(a) * d
        c.disc(sx, sy, max(2, w // 80), (255, 255, 255), 210)
    return c


def realms_art(entry):
    """A small original candy landscape for the Realms store banners."""
    w, h = entry["w"], entry["h"]
    c = Canvas(w, h)
    sky_top = (65, 36, 77)
    sky_bottom = (255, 185, 164)
    for y in range(h):
        t = y / max(1, h - 1)
        base = mix(sky_top, sky_bottom, t ** 1.3)
        for x in range(w):
            # warm glow around the sun
            dx, dy = (x - w * .72) / w, (y - h * .30) / h
            glow = max(0.0, 1.0 - (dx * dx + dy * dy) * 22.0)
            c.set(x, y, mix(base, (255, 238, 167), glow * .38))
    # sun
    c.disc(w * .72, h * .30, h * .105, (255, 230, 132))
    c.disc(w * .72, h * .30, h * .075, (255, 249, 206))
    # clouds
    rnd = random.Random(8102)
    for cx, cy, rr in ((w * .18, h * .19, h * .055),
                       (w * .33, h * .13, h * .042),
                       (w * .55, h * .22, h * .050),
                       (w * .86, h * .17, h * .036)):
        for k in range(5):
            c.disc(cx + (k - 2) * rr * .95, cy + (k % 2) * rr * .22,
                   rr * (0.75 + .18 * (k % 3)), (255, 243, 220), 220)
    # hills
    layers = (
        (h * .63, 28, (143, 227, 192), (98, 185, 156)),
        (h * .75, 24, (255, 143, 179), (216, 92, 129)),
        (h * .88, 20, (183, 121, 73), (128, 72, 49)),
    )
    for idx, (base_y, amp, light, dark) in enumerate(layers):
        for x in range(w):
            yy = base_y + math.sin(x * .013 + idx * 1.8) * amp + \
                math.sin(x * .037 + idx) * amp * .28
            for y in range(int(yy), h):
                t = (y - yy) / max(1.0, h - yy)
                c.set(x, y, mix(light, dark, min(1.0, t * 1.4)))
    # lollipop trees
    for cx, base, rr, shell, stripe in (
            (w * .20, h * .67, h * .095, (255, 143, 179), (239, 90, 116)),
            (w * .44, h * .72, h * .075, (143, 199, 255), (85, 131, 219)),
            (w * .80, h * .76, h * .085, (255, 226, 122), (239, 166, 56))):
        c.rect(int(cx - rr * .10), int(base), int(cx + rr * .10),
               int(h * .90), (255, 243, 220))
        candy_swirl(c, cx, base - rr * .65, rr, shell, stripe,
                    (255, 243, 220), turns=2)
    # foreground sprinkles
    for _ in range(34):
        x = rnd.uniform(0, w)
        y = rnd.uniform(h * .80, h * .98)
        ang = rnd.uniform(0, math.tau)
        col = rnd.choice(((255, 243, 220), (143, 227, 192),
                          (255, 226, 122)))
        ln = rnd.uniform(4, 10)
        for i in range(int(ln)):
            c.disc(x + math.cos(ang) * i, y + math.sin(ang) * i, 1, col)
    return c


def build(only=None):
    inv = json.load(open(os.path.join(ROOT, "build", "inventory.json")))
    entries = [t for t in inv["textures"]
               if t["category"] not in ("blocks", "items", "colormap")]
    if only:
        entries = [t for t in entries if t["category"] in only]
    t0 = time.time()
    problems = []
    done = 0
    for e in entries:
        cat, name = e["category"], e["name"]
        base = e["base"]
        try:
            if cat == "environment":
                c = environment_canvas(name)
            elif cat == "flame_atlas":
                c = environment.flame_atlas()
            elif cat == "forcefield_atlas":
                c = environment.forcefield_atlas()
            elif cat == "entity":
                c = grey(e) if base.startswith(BANNER) else paint(e, 1.02)
            elif cat == "models":
                if name == "elytra":
                    c = restyle.restyle(e, "silver_lilac", scale=1,
                                        contrast=1.04)
                else:
                    c = paint(e, 1.02)
            elif cat == "trims":
                if "/color_palettes/" in base:
                    ramp, bright = TRIM_PALETTES[name]
                    c = restyle.restyle(e, ramp, scale=1, contrast=1.02,
                                        brightness=bright)
                else:
                    c = grey(e)
            elif cat == "painting":
                c = grey(e) if e["tint_mask"] else paint(e, 1.0)
            elif cat == "particle":
                if base in GREY_PARTICLES:
                    c = grey(e)
                elif base == "particle/pixel":
                    c = Canvas(1, 1, fill=(255, 255, 255, 255))
                else:
                    c = paint(e, 1.02)
            elif cat == "particles":
                c = paint(e, 1.02)
            elif cat == "map":
                if name == "map_background":
                    c = restyle.restyle(e, "vanilla", scale=1, contrast=1.0)
                else:
                    c = paint(e, 1.0)
            elif cat == "misc":
                if name == "missing_texture":
                    c = environment.missing_texture()
                elif name.startswith("enchanted_"):
                    c = grey(e)
                else:
                    c = paint(e, 1.0)
            elif cat == "ui":
                if base.startswith("ui/sidebar_icons/"):
                    c = promo_badge(e)
                else:
                    c = paint(e, 1.02, neutral=UI_NEUTRAL)
            elif cat == "gui":
                if base.startswith("gui/newgui/mc_store_realms"):
                    c = realms_art(e)
                else:
                    c = paint(e, 1.03, neutral=UI_NEUTRAL)
            elif cat == "persona_thumbnails":
                c = paint(e, 1.02)
            else:
                raise KeyError("no recipe for category " + cat)
        except Exception as exc:
            problems.append((base, "EXC", repr(exc)))
            continue
        exp = expected_dims(e)
        if (c.w, c.h) != exp:
            problems.append((base, (c.w, c.h), exp))
            continue
        try:
            write(e, c)
        except Exception as exc:
            problems.append((base, "WRITE", repr(exc)))
            continue
        done += 1
        if done % 250 == 0:
            print("  %4d/%d  %5.1fs" % (done, len(entries), time.time() - t0))

    # biome colour maps
    if not only or "colormap" in only:
        names = colormaps.make_all(os.path.join(TEX, "colormap"))
        print("colormaps:", len(names))

    # root texture configs
    for fn in ("flipbook_textures.json", "texture_list.json"):
        src = os.path.join(SRC, fn)
        if os.path.exists(src):
            os.makedirs(TEX, exist_ok=True)
            shutil.copyfile(src, os.path.join(TEX, fn))

    print("categories: %d written in %.1fs" % (done, time.time() - t0))
    if problems:
        print("problems:", len(problems))
        for p in problems[:40]:
            print("  ", p)
    with open(os.path.join(ROOT, "build", "rest_problems.json"), "w") as fh:
        json.dump(problems, fh, indent=1)
    return problems


if __name__ == "__main__":
    only = sys.argv[1:] or None
    build(only)
