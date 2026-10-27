"""Candy biome colour maps.

Bedrock tints grass, foliage, waterlily and a few plants by sampling these
256x256 maps.  Replacing them is the clean way to retheme every tinted plant
without touching biome JSON.
"""
import math
import os

from pnglib import png_write
from candy import hex_rgb, mix, clamp, ValueNoise


def _bilinear(x, y, w, h, corners):
    """corners: tl, tr, bl, br."""
    u = x / (w - 1.0)
    v = y / (h - 1.0)
    top = mix(corners[0], corners[1], u)
    bot = mix(corners[2], corners[3], u)
    return mix(top, bot, v)


def gradient(name, corners, size=256, wobble=0.025, seed=1):
    n = ValueNoise(seed)
    px = bytearray(size * size * 4)
    tl, tr, bl, br = [hex_rgb(c) for c in corners]
    for y in range(size):
        for x in range(size):
            c = _bilinear(x, y, size, size, (tl, tr, bl, br))
            # very gentle organic wobble so bilinear sampling doesn't band
            w = (n.fbm(x * 5.0 / size, y * 5.0 / size, 3) - .5) * wobble
            c = tuple(clamp(int(v * (1 + w))) for v in c)
            i = (y * size + x) * 4
            px[i:i + 4] = bytes((c[0], c[1], c[2], 255))
    return name, px, size


def make_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    maps = [
        # grass: mint / pistachio / teal / lemon-lime.  Kept green so trees,
        # crops and flowers still read against it.
        gradient("grass", ("#8fe6c8", "#c8f0a6", "#79e0b5", "#d8f08a"),
                 wobble=.035, seed=2),
        # foliage gets the full candy treatment: mint -> cotton candy pink.
        gradient("foliage", ("#8fe6c8", "#c9b6f5", "#a8e6a0", "#f7a8c4"),
                 wobble=.045, seed=3),
        gradient("dry_foliage", ("#ffd6a5", "#f7a8c4", "#ffe9b0", "#f2c4a0"),
                 wobble=.04, seed=4),
        gradient("evergreen", ("#7fd7c0", "#9adcf7", "#5fc9a8", "#b7e6f7"),
                 wobble=.04, seed=5),
        gradient("birch", ("#d7f0a0", "#fff0a8", "#b8e69a", "#ffe18a"),
                 wobble=.04, seed=6),
        gradient("mangrove_swamp_foliage", ("#9fe6c8", "#c9b6f5", "#7fd7b8", "#e2a8e8"),
                 wobble=.04, seed=7),
        gradient("swamp_foliage", ("#7fd7b8", "#a8e6a0", "#79c9b5", "#c8e69a"),
                 wobble=.04, seed=8),
        gradient("swamp_grass", ("#8fe6c8", "#b8e69a", "#7fd7b8", "#d0e69a"),
                 wobble=.04, seed=9),
    ]
    for name, px, size in maps:
        png_write(os.path.join(outdir, name + ".png"), size, size, px)
    return [m[0] for m in maps]
