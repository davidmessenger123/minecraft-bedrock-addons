"""
Content builders for the Bloomlands add-on.

Everything in the resource and behaviour packs is generated from this module:
pixel-art textures, Bedrock geometry, entity atlases, Blockbench project files
and the data used by the JSON writers in ``generate.py``.

The art is deliberately hand-built at Minecraft's native resolution.  Block
textures are 16x16 or 32x32; flowers, giant blooms and entity skins get larger
canvases where the extra room earns its keep.  No texture is a scaled-up copy
of a vanilla file: the palettes and shading follow vanilla's rules so the pack
sits naturally beside it.
"""

from __future__ import annotations

import base64
import colorsys
import io
import json
import math
import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter

NS = "bl"
VERSION = "2.2.3"
PACK_NAME = "Bloomlands"
BP_NAME = "Bloomlands Behaviour Pack"
RP_NAME = "Bloomlands Resource Pack"

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

RGBA = tuple[int, int, int, int]


def rgba(value: str | Sequence[int], alpha: int = 255) -> RGBA:
    """Turn ``#rrggbb`` or an RGB triple into an RGBA tuple."""
    if isinstance(value, str):
        value = value.lstrip("#")
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)
    if len(value) == 4:
        return tuple(value)  # type: ignore[return-value]
    return (int(value[0]), int(value[1]), int(value[2]), alpha)


def shade(color: str | Sequence[int], factor: float, alpha: int = 255) -> RGBA:
    r, g, b, _ = rgba(color, alpha)
    if factor >= 0:
        r = round(r + (255 - r) * factor)
        g = round(g + (255 - g) * factor)
        b = round(b + (255 - b) * factor)
    else:
        r = round(r * (1.0 + factor))
        g = round(g * (1.0 + factor))
        b = round(b * (1.0 + factor))
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), alpha)


def mix(a: str | Sequence[int], b: str | Sequence[int], t: float, alpha: int = 255) -> RGBA:
    ar, ag, ab, _ = rgba(a, alpha)
    br, bg, bb, _ = rgba(b, alpha)
    return (
        round(ar + (br - ar) * t),
        round(ag + (bg - ag) * t),
        round(ab + (bb - ab) * t),
        alpha,
    )


def hrand(x: int, y: int, seed: int = 0) -> int:
    """Stable small integer hash used for pixel noise."""
    n = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return n ^ (n >> 16)


def noise_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    colors: Sequence[str | Sequence[int]],
    seed: int = 1,
    alpha: int = 255,
) -> None:
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            color = colors[hrand(x, y, seed) % len(colors)]
            draw.point((x, y), fill=rgba(color, alpha))


def fill(img: Image.Image, color: str | Sequence[int], alpha: int = 255) -> None:
    img.paste(Image.new("RGBA", img.size, rgba(color, alpha)), (0, 0))


def new_tex(width: int = 16, height: int = 16) -> Image.Image:
    return Image.new("RGBA", (width, height), (0, 0, 0, 0))


def put(img: Image.Image, x: int, y: int, color: str | Sequence[int], alpha: int = 255) -> None:
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), rgba(color, alpha))


def rect(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, color: str | Sequence[int], alpha: int = 255) -> None:
    draw.rectangle((x0, y0, x1, y1), fill=rgba(color, alpha))


def line(draw: ImageDraw.ImageDraw, points: Sequence[tuple[int, int]], color: str | Sequence[int], width: int = 1, alpha: int = 255) -> None:
    draw.line(points, fill=rgba(color, alpha), width=width)


def ellipse(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: str | Sequence[int], alpha: int = 255) -> None:
    draw.ellipse(box, fill=rgba(color, alpha))


def polygon(draw: ImageDraw.ImageDraw, points: Sequence[tuple[int, int]], color: str | Sequence[int], alpha: int = 255) -> None:
    draw.polygon(points, fill=rgba(color, alpha))


def outline(
    draw: ImageDraw.ImageDraw,
    points: Sequence[tuple[int, int]],
    color: str | Sequence[int],
    width: int = 1,
    alpha: int = 255,
) -> None:
    draw.line(list(points) + [points[0]], fill=rgba(color, alpha), width=width)


def paste_tile(atlas: Image.Image, tile: Image.Image, x: int, y: int) -> None:
    atlas.alpha_composite(tile, (x, y))


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def data_uri(img: Image.Image) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes(img)).decode("ascii")


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

GRASS = ["#4f7d3a", "#5b8e43", "#689f4c", "#76b157", "#86c263", "#96d16f"]
DIRT = ["#5d3f2c", "#6b4a33", "#7a553b", "#876144", "#966d4c", "#a47a55"]
STONE = ["#55585e", "#60636a", "#6c7077", "#777b83", "#83878f", "#90949c"]
BARK = ["#4b3020", "#5d3c27", "#6d4a30", "#7d5838", "#8c6642", "#9c754d"]
MOSS = ["#4c7436", "#5b8840", "#6a9b4a", "#7aae55", "#8bc161"]
PLANK = ["#8a5c36", "#996b3d", "#aa7b46", "#b98a50", "#c89a5b", "#d8ab69"]
LEAF_DARK = ["#183d26", "#1e4a2d", "#245834", "#2b663b", "#327544", "#3b844d"]
LEAF_LIGHT = ["#3c8a4c", "#4a9b57", "#58ad62", "#68bd6f", "#7acc7b", "#8edb88"]
PETAL_PINK = ["#b73c6a", "#d94b7f", "#ee6493", "#ff7fa8", "#ff9fbe", "#ffc2d5"]
PETAL_GOLD = ["#a56a12", "#c98919", "#e5a925", "#f4c53b", "#ffdc62", "#fff0a0"]
PETAL_BLUE = ["#3d5e9c", "#4c78b8", "#5e93d0", "#72afe2", "#8ec9ef", "#b5e3fa"]
PETAL_PURPLE = ["#5f3f91", "#764fb0", "#8e63c9", "#a67ade", "#bf95ee", "#d9baf8"]
PETAL_WHITE = ["#8c9bb0", "#aebccd", "#cbd8e4", "#e4eef5", "#f4f9fd", "#ffffff"]
PETAL_ORANGE = ["#9e4215", "#c25a1d", "#df7628", "#f4923b", "#ffad57", "#ffcb82"]


# ---------------------------------------------------------------------------
# Ground, wood and foliage textures
# ---------------------------------------------------------------------------


def petal_grass_top() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, 15, 15), GRASS, 11)
    # A handful of darker blades keep the surface from looking like flat noise.
    for i in range(12):
        x = hrand(i, 1, 4) % 16
        y = hrand(i, 2, 5) % 16
        length = 2 + hrand(i, 3, 6) % 3
        for j in range(length):
            put(img, x + (j // 2), y - j, GRASS[1] if j % 2 else GRASS[0])
    # Light tips catch the sun.
    for i in range(18):
        x = hrand(i, 7, 9) % 16
        y = hrand(i, 8, 10) % 16
        put(img, x, y, GRASS[5] if i % 3 else GRASS[4])
    # Tiny meadow flowers: a 2x2 centre with a one-pixel halo.
    flowers = [
        (3, 4, PETAL_PINK[4]),
        (10, 9, PETAL_GOLD[4]),
        (13, 3, PETAL_WHITE[4]),
        (6, 13, PETAL_BLUE[3]),
    ]
    for x, y, color in flowers:
        put(img, x, y, shade(color, -0.35))
        put(img, x + 1, y, color)
        put(img, x, y + 1, shade(color, -0.15))
        put(img, x + 1, y + 1, shade(color, 0.15))
        if (x + y) % 3 == 0:
            put(img, x + 2, y, PETAL_WHITE[5])
    # Slight irregular darkening along one edge for a hand-painted feel.
    for y in range(16):
        if hrand(0, y, 13) % 4 == 0:
            put(img, 15, y, GRASS[1])
    return img


def petal_grass_side() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, 15, 15), DIRT, 21)
    # Grass overhang with a different depth in each column.
    for x in range(16):
        depth = 3 + hrand(x, 0, 22) % 3
        for y in range(depth):
            color = GRASS[hrand(x, y, 23) % len(GRASS)]
            put(img, x, y, color)
        put(img, x, depth, GRASS[0])
        if hrand(x, 1, 24) % 5 == 0:
            put(img, x, depth + 1, GRASS[1])
        if hrand(x, 2, 25) % 7 == 0:
            put(img, x, depth + 2, GRASS[2])
    # Roots and pebbles in the dirt.
    for i in range(8):
        x = hrand(i, 5, 26) % 16
        y = 7 + hrand(i, 6, 27) % 9
        put(img, x, y, DIRT[0])
        if i % 3 == 0:
            put(img, x + 1, y, DIRT[1])
    for i in range(5):
        x = hrand(i, 9, 28) % 14
        y = 7 + hrand(i, 10, 29) % 8
        put(img, x, y, "#b9a58f")
        put(img, x + 1, y, "#8d7862")
    # Two tiny flowers tucked into the grass.
    for x, y, color in [(3, 2, PETAL_PINK[4]), (11, 3, PETAL_GOLD[4])]:
        put(img, x, y, color)
        put(img, x + 1, y + 1, shade(color, -0.2))
    return img


def bloom_dirt() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, 15, 15), DIRT, 31)
    for i in range(11):
        x = hrand(i, 3, 32) % 16
        y = hrand(i, 4, 33) % 16
        if i % 3 == 0:
            put(img, x, y, "#b19a82")
        elif i % 3 == 1:
            put(img, x, y, "#4c3325")
        else:
            put(img, x, y, "#c07b91")
    # A few hairline roots.
    for x, y in [(2, 4), (3, 5), (3, 6), (12, 9), (11, 10), (11, 11), (6, 13), (6, 14)]:
        put(img, x, y, "#3f2a1e")
    return img


def bloom_stone() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, 15, 15), STONE, 41)
    # Cracks.
    for x, y, dx, dy, length in [(2, 2, 1, 1, 5), (11, 1, 0, 1, 4), (4, 12, 1, -1, 4), (14, 8, 0, 1, 5)]:
        for i in range(length):
            put(img, x + dx * i, y + dy * i, "#3d4046")
            if hrand(i, x, 42) % 2:
                put(img, x + dx * i + 1, y + dy * i, "#7d8189")
    # Crystal veins: each is a short, bright, branching seam.
    for base_x, base_y, color, length in [(3, 8, "#8ff0df", 7), (12, 5, "#f2a6d1", 6), (8, 11, "#b7a6ff", 5)]:
        x, y = base_x, base_y
        for i in range(length):
            put(img, x, y, color)
            put(img, x, y + 1, shade(color, -0.25))
            if i % 2 == 0:
                x += 1
            else:
                y += 1
            if x > 15 or y > 15:
                break
    # Sparkle pixels.
    for x, y in [(4, 9), (13, 6), (9, 12), (5, 3)]:
        put(img, x, y, "#ffffff")
    return img


def bloomwood_log_side() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, 15, 15), BARK, 51)
    # Vertical bark ridges.
    for x in range(1, 16, 4):
        for y in range(16):
            offset = (hrand(x, y, 52) % 3) - 1
            put(img, x + offset, y, BARK[1])
            put(img, x + offset + 1, y, BARK[0])
    for i in range(7):
        x = hrand(i, 0, 53) % 16
        y = hrand(i, 1, 54) % 10
        for j in range(2 + i % 3):
            put(img, x, y + j, BARK[5])
    # Moss creeping up from the base.
    for i in range(24):
        x = hrand(i, 3, 55) % 16
        y = 10 + hrand(i, 4, 56) % 6
        put(img, x, y, MOSS[hrand(i, 5, 57) % len(MOSS)])
    # A small blossom growing out of the bark.
    for x, y, color in [(11, 4, PETAL_PINK[3]), (12, 4, PETAL_PINK[4]), (11, 5, PETAL_PINK[2]), (12, 5, PETAL_PINK[5])]:
        put(img, x, y, color)
    put(img, 12, 3, PETAL_GOLD[4])
    return img


def bloomwood_log_top() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    fill(img, BARK[2])
    # Concentric growth rings.
    for i, color in enumerate([BARK[4], BARK[3], BARK[5], BARK[2], BARK[4], BARK[1]]):
        inset = i * 2
        if 15 - inset * 2 <= 0:
            break
        d.ellipse((inset, inset, 15 - inset, 15 - inset), fill=rgba(color))
    # Heartwood and cracks.
    d.ellipse((6, 6, 9, 9), fill=rgba("#d3a16c"))
    put(img, 7, 7, "#f0c48f")
    for x, y in [(1, 7), (2, 7), (3, 8), (12, 3), (13, 3), (13, 4), (5, 14), (5, 15)]:
        put(img, x, y, BARK[0])
    # Moss and a glow at the rim.
    for i in range(12):
        x = hrand(i, 6, 61) % 16
        y = hrand(i, 7, 62) % 3
        put(img, x, y, MOSS[hrand(i, 8, 63) % len(MOSS)])
    put(img, 3, 12, "#9ff2d9")
    put(img, 4, 12, "#d8fff2")
    return img


def bloomwood_planks() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    # Four horizontal boards.
    for row in range(4):
        y0 = row * 4
        base = PLANK[(row * 2) % len(PLANK)]
        for y in range(y0, y0 + 4):
            for x in range(16):
                color = PLANK[hrand(x, y, 71) % len(PLANK)]
                if y == y0 + 1 and hrand(x, y, 72) % 7 == 0:
                    color = PLANK[5]
                put(img, x, y, color)
        line(d, [(0, y0 + 3), (15, y0 + 3)], "#6b4529")
        line(d, [(0, y0), (15, y0)], PLANK[5])
        # Board ends and nails.
        for x in (3, 10):
            put(img, x, y0 + 2, "#4f3220")
        for x in (7, 14):
            put(img, x, y0 + 1, "#f0d09b")
    # Grain lines.
    for i in range(5):
        y = hrand(i, 2, 73) % 16
        for x in range(16):
            if hrand(x, y, 74) % 4 == 0:
                put(img, x, y, "#7c512f")
    # Moss and a petal inlay.
    for x, y in [(0, 12), (1, 12), (1, 13), (0, 13), (14, 5), (15, 5), (15, 6)]:
        put(img, x, y, MOSS[hrand(x, y, 75) % len(MOSS)])
    for x, y, color in [(6, 6, PETAL_PINK[4]), (7, 6, PETAL_PINK[5]), (6, 7, PETAL_PINK[3]), (7, 7, PETAL_PINK[4])]:
        put(img, x, y, color)
    return img


def petal_path() -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, 15, 15), ["#4b3327", "#563b2c", "#624532"], 81)
    # Sparse, softly coloured petals set into packed earth.  The earlier
    # twelve-petal scatter read as confetti rather than a path.
    petals = [
        (3, 4, PETAL_PINK[3]), (8, 3, PETAL_WHITE[3]),
        (12, 5, PETAL_GOLD[3]), (4, 9, PETAL_PURPLE[3]),
        (10, 10, PETAL_PINK[2]), (7, 13, PETAL_WHITE[3]),
        (13, 12, PETAL_PINK[3]), (1, 8, PETAL_BLUE[3]),
    ]
    for x, y, color in petals:
        put(img, x, y, color)
        put(img, x + 1, y, shade(color, -0.15))
        put(img, x, y + 1, shade(color, -0.3))
        put(img, x + 1, y + 1, shade(color, 0.1))
        if hrand(x, y, 82) % 3 == 0:
            put(img, x + 2, y, PETAL_WHITE[5])
    # Little stones and stems.
    for x, y in [(1, 1), (14, 14), (7, 5), (11, 11), (3, 9), (15, 1)]:
        put(img, x, y, "#9d8b76")
        put(img, x, y + 1, "#6d5a49")
    for x, y in [(5, 11), (5, 12), (12, 6), (12, 7), (1, 5)]:
        put(img, x, y, MOSS[(x + y) % len(MOSS)])
    return img


def _leaf_blob(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, colors: Sequence[str], seed: int) -> None:
    # Small angular leaves read better than perfect circles at 16x16.
    pts = [
        (cx - r, cy),
        (cx - r + 1, cy - r + 1),
        (cx, cy - r),
        (cx + r - 1, cy - r + 1),
        (cx + r, cy),
        (cx + r - 1, cy + r - 1),
        (cx, cy + r),
        (cx - r + 1, cy + r - 1),
    ]
    draw.polygon(pts, fill=rgba(colors[hrand(cx, cy, seed) % len(colors)]))
    # Darker lower edge and a bright top-left tip.
    draw.line([pts[0], pts[1], pts[2]], fill=rgba(colors[0]))
    draw.point((cx - max(1, r // 2), cy - max(1, r // 2)), fill=rgba(colors[-1]))
    if r >= 3:
        draw.point((cx + 1, cy), fill=rgba(colors[1]))
        draw.point((cx, cy + 1), fill=rgba(colors[2]))


def canopy_leaves(glow: bool = False) -> Image.Image:
    img = new_tex()
    d = ImageDraw.Draw(img)
    # Dense overlapping leaf clusters.  A few transparent gaps let light
    # through while three canopy layers still hide the sky.
    clusters = [
        (2, 2), (5, 1), (9, 2), (13, 3), (1, 6), (4, 5), (7, 6), (11, 5),
        (14, 7), (2, 10), (5, 9), (8, 10), (12, 9), (15, 11), (4, 13),
        (7, 14), (10, 13), (13, 14), (0, 3), (15, 4), (6, 11), (11, 12),
    ]
    colors = LEAF_DARK if glow else LEAF_LIGHT
    for i, (x, y) in enumerate(clusters):
        _leaf_blob(d, x, y, 2 + (i % 2), colors, 91 + i)
    # Overlapping highlights and dark seams.
    for i in range(23):
        x = hrand(i, 2, 92) % 16
        y = hrand(i, 3, 93) % 16
        if img.getpixel((x, y))[3] == 0:
            continue
        if i % 4 == 0:
            put(img, x, y, LEAF_DARK[5] if glow else LEAF_LIGHT[5])
        elif i % 4 == 1:
            put(img, x, y, LEAF_DARK[0] if glow else LEAF_LIGHT[0])
    # Tiny blossoms tucked into the foliage.
    blossoms = [(3, 4, PETAL_PINK[4]), (10, 8, PETAL_WHITE[5]), (6, 12, PETAL_GOLD[4]), (14, 1, PETAL_PINK[5])]
    for x, y, color in blossoms:
        put(img, x, y, color)
        put(img, x + 1, y, shade(color, -0.1))
        put(img, x, y + 1, shade(color, -0.25))
    if glow:
        for x, y in [(2, 12), (8, 2), (12, 14), (15, 6), (5, 7)]:
            put(img, x, y, "#8ffbe1")
            put(img, x, y - 1, "#e4fff8")
            put(img, x + 1, y, "#59d6bb")
    return img


# ---------------------------------------------------------------------------
# Flower textures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FlowerSpec:
    key: str
    label: str
    palette: tuple[str, ...]
    center: tuple[str, ...]
    accent: str = "#fff2b0"
    glow: bool = False
    map_color: str = "#ff8fbd"


SMALL_FLOWERS: list[FlowerSpec] = [
    FlowerSpec("sunpetal", "Sunpetal", PETAL_GOLD, ("#5b360e", "#8f5a16", "#c98a28", "#f4d36a", "#fff2b0"), "#fff8d0", map_color="#f6c23c"),
    FlowerSpec("rosequartz", "Rosequartz", PETAL_PINK, ("#6f2948", "#a43d62", "#d15b82", "#f39ab4", "#ffd6e2"), "#ffe6ef", map_color="#ef7fa7"),
    FlowerSpec("skybell", "Skybell", PETAL_BLUE, ("#263e70", "#3d5e9c", "#5e93d0", "#9ed2ef", "#dcf3ff"), "#f5fbff", map_color="#6faee6"),
    FlowerSpec("moondrop", "Moondrop", PETAL_WHITE, ("#5d6d80", "#8796a8", "#b3c1d0", "#dce8f1", "#ffffff"), "#e8f4ff", map_color="#dbe8f3"),
    FlowerSpec("emberbloom", "Emberbloom", PETAL_ORANGE, ("#5d250c", "#8d3b13", "#c25a1d", "#f4923b", "#ffd38d"), "#fff0b0", map_color="#ee8334"),
    FlowerSpec("amethyst_bell", "Amethyst Bell", PETAL_PURPLE, ("#3b245e", "#5f3f91", "#8e63c9", "#bf95ee", "#e8d2ff"), "#ffe6a8", map_color="#9f78dc"),
    FlowerSpec("lumen_bell", "Lumen Bell", ("#3b6f70", "#4f9996", "#6fc7be", "#9ff0df", "#e4fff9"), ("#8a6b1c", "#c49d2e", "#f4d86a", "#fff5c0", "#ffffff"), "#ffffff", glow=True, map_color="#a8f5df"),
]


def _draw_leaf_tile(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], palette: Sequence[str], seed: int) -> None:
    x0, y0, w, h = box
    pal = lambda i: palette[min(i, len(palette) - 1)]
    # A pointed leaf: wide at the base, narrow at the tip.
    pts = [
        (x0 + 1, y0 + h - 1),
        (x0 + 2, y0 + 2),
        (x0 + w // 2, y0),
        (x0 + w - 2, y0 + 2),
        (x0 + w - 1, y0 + h - 1),
        (x0 + w // 2, y0 + h - 2),
    ]
    draw.polygon(pts, fill=rgba(pal(2)))
    draw.line([(x0 + 2, y0 + 2), (x0 + w // 2, y0), (x0 + w - 2, y0 + 2)], fill=rgba(pal(4)))
    draw.line([(x0 + w // 2, y0 + 1), (x0 + w // 2, y0 + h - 3)], fill=rgba(pal(1)))
    for i in range(3):
        px = x0 + 2 + i * 2
        draw.line([(x0 + w // 2, y0 + 3 + i * 2), (px, y0 + 2 + i * 2)], fill=rgba(pal(3)))
    draw.point((x0 + 2, y0 + h - 2), fill=rgba(pal(0)))


def _draw_petal_tile(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], palette: Sequence[str], accent: str, seed: int, glow: bool = False) -> None:
    x0, y0, w, h = box
    pal = lambda i: palette[min(i, len(palette) - 1)]
    # Rounded, slightly asymmetric petal with a transparent margin.
    pts = [
        (x0 + w // 2, y0),
        (x0 + w - 2, y0 + 2),
        (x0 + w - 1, y0 + h // 2),
        (x0 + w - 2, y0 + h - 3),
        (x0 + w // 2, y0 + h - 1),
        (x0 + 2, y0 + h - 3),
        (x0 + 1, y0 + h // 2),
        (x0 + 2, y0 + 2),
    ]
    draw.polygon(pts, fill=rgba(pal(2)))
    # Gradient: darker rim, lighter toward the tip/centre.
    draw.line([(x0 + 2, y0 + 2), (x0 + 1, y0 + h // 2), (x0 + 2, y0 + h - 3)], fill=rgba(pal(1)))
    draw.line([(x0 + w - 2, y0 + 2), (x0 + w - 1, y0 + h // 2), (x0 + w - 2, y0 + h - 3)], fill=rgba(pal(0)))
    draw.line([(x0 + w // 2, y0 + 2), (x0 + w // 2, y0 + h - 3)], fill=rgba(pal(4)))
    for i in range(1, 4):
        yy = y0 + 2 + i * 2
        draw.line([(x0 + w // 2, yy), (x0 + 2 + i, yy - 1)], fill=rgba(pal(3)))
        draw.line([(x0 + w // 2, yy), (x0 + w - 2 - i, yy - 1)], fill=rgba(pal(1)))
    draw.line([(x0 + 3, y0 + 3), (x0 + 4, y0 + 3), (x0 + 4, y0 + 4)], fill=rgba(pal(5)))
    if glow:
        for x, y in [(x0 + 4, y0 + 5), (x0 + 8, y0 + 4), (x0 + 6, y0 + 8)]:
            draw.point((x, y), fill=rgba(accent))
    # A couple of dew pixels make the petal feel three-dimensional.
    draw.point((x0 + 3, y0 + h - 5), fill=rgba(accent))
    draw.point((x0 + 4, y0 + h - 5), fill=rgba("#ffffff", 200))


def _draw_center_tile(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], palette: Sequence[str], seed: int) -> None:
    x0, y0, w, h = box
    pal = lambda i: palette[min(i, len(palette) - 1)]
    cx, cy = x0 + w // 2, y0 + h // 2
    draw.ellipse((x0 + 1, y0 + 1, x0 + w - 2, y0 + h - 2), fill=rgba(pal(1)))
    draw.ellipse((x0 + 2, y0 + 2, x0 + w - 3, y0 + h - 3), fill=rgba(pal(2)))
    draw.ellipse((x0 + 3, y0 + 3, x0 + w - 4, y0 + h - 4), fill=rgba(pal(3)))
    # Seeds/pollen.
    for i in range(7):
        x = x0 + 3 + hrand(i, 0, 111) % max(1, w - 6)
        y = y0 + 3 + hrand(i, 1, 112) % max(1, h - 6)
        draw.point((x, y), fill=rgba(pal(0)))
        draw.point((x + 1, y), fill=rgba(pal(4)))
    draw.point((cx - 2, cy - 2), fill=rgba("#ffffff"))
    draw.point((cx - 1, cy - 2), fill=rgba(pal(4)))


def small_flower_texture(spec: FlowerSpec) -> Image.Image:
    img = new_tex(32, 32)
    d = ImageDraw.Draw(img)
    # Stem: a 2px column with a lighter left edge and tiny thorns.
    for y in range(20):
        base = "#3f6b35" if not spec.glow else "#3f7f78"
        light = "#6f9e4c" if not spec.glow else "#79d7ca"
        put(img, 1, y, base)
        put(img, 2, y, light if y % 4 else "#365e2e")
        if y in (5, 9, 14):
            put(img, 0, y, base)
            put(img, 3, y + 1, base)
    # Leaf tile.
    _draw_leaf_tile(d, (8, 0, 12, 7), ("#2d5229", "#3f6b35", "#5b8f3f", "#7ab654", "#a1d66d"), 1)
    # Petal and edge tiles.
    _draw_petal_tile(d, (0, 16, 12, 12), spec.palette, spec.accent, 2, spec.glow)
    for y in range(16, 28):
        for x in range(12, 16):
            _ = (x, y)
    # Edge tile: a thin strip of the darkest petal colour.
    for y in range(28, 32):
        for x in range(12, 16):
            put(img, x, y, spec.palette[0])
    # Centre tile.
    _draw_center_tile(d, (16, 16, 10, 10), spec.center, 3)
    # A few floating pollen pixels in the otherwise unused corner.
    for i in range(5):
        x = 24 + hrand(i, 2, 113) % 8
        y = 16 + hrand(i, 3, 114) % 10
        put(img, x, y, spec.accent if spec.glow else spec.palette[-1])
    return img


# Regions for the small-flower model.  Coordinates match the 32x32 texture.
SMALL_FLOWER_REGIONS = {
    "stem": (0, 0, 4, 20),
    "leaf": (8, 0, 12, 7),
    "petal": (0, 16, 12, 12),
    "edge": (12, 28, 4, 4),
    "center": (16, 16, 10, 10),
}


def portal_flower_texture() -> Image.Image:
    img = new_tex(64, 64)
    d = ImageDraw.Draw(img)
    # Stem.
    for y in range(30):
        put(img, 2, y, "#3f6b57")
        put(img, 3, y, "#5b9a7f")
        put(img, 4, y, "#79c7a6" if y % 5 else "#346b55")
        if y in (8, 15, 22):
            put(img, 1, y, "#2d5545")
            put(img, 5, y + 1, "#2d5545")
    # Large leaf.
    _draw_leaf_tile(d, (10, 0, 22, 14), ("#2d5229", "#3f6b35", "#5b9f5a", "#83cf7b", "#b6f0a8"), 4)
    # Petals: two layers, with a starry inner surface.
    _draw_petal_tile(d, (0, 32, 24, 18), ("#5c2a63", "#8f3f89", "#c85aa8", "#f27bc0", "#ffb7dc"), "#ffe6a8", 5, True)
    _draw_petal_tile(d, (0, 52, 28, 12), ("#2d5f75", "#3f8e9d", "#5fc3c0", "#94eddc", "#d4fff7"), "#ffffff", 6, True)
    # The heart of the portal flower: a luminous spiral.
    _draw_center_tile(d, (34, 32, 24, 24), ("#6b3b1c", "#a96a24", "#e6ad42", "#ffe37c", "#fffbd0"), 7)
    cx, cy = 46, 44
    for i in range(10):
        angle = i * 0.8
        rr = 2 + i * 0.75
        x = round(cx + math.cos(angle) * rr)
        y = round(cy + math.sin(angle) * rr)
        put(img, x, y, "#fff6c8")
    # Glow tile and sparkle specks.
    for y in range(20):
        for x in range(58, 64):
            if hrand(x, y, 115) % 4 == 0:
                put(img, x, y, "#fff0a0", 220)
    for x, y in [(58, 22), (60, 25), (62, 28), (59, 30)]:
        put(img, x, y, "#ffffff")
    # Tiny runes on the petals.
    for x, y in [(5, 38), (6, 39), (8, 41), (16, 36), (17, 37), (18, 38), (4, 56), (5, 57), (20, 55)]:
        put(img, x, y, "#fff0b8", 220)
    return img


PORTAL_FLOWER_REGIONS = {
    "stem": (0, 0, 8, 30),
    "leaf": (10, 0, 22, 14),
    "petal": (0, 32, 24, 18),
    "inner": (0, 52, 28, 12),
    "center": (34, 32, 24, 24),
    "glow": (58, 0, 6, 20),
}


def rainbow_portal_texture() -> Image.Image:
    """
    Recolour the vanilla Nether-portal frame sheet.

    The source is the 32x1024 sheet (32 frames of 32x32).  Hue is shifted by
    the pixel position and frame while the original brightness and alpha
    pattern are retained, so the surface keeps the familiar portal motion.
    """
    source = Path(__file__).with_name("nether_portal.png")
    base = Image.open(source).convert("RGBA")
    frame_size = base.width
    out = new_tex(base.width, base.height)
    for y in range(base.height):
        frame = y // frame_size
        for x in range(base.width):
            r, g, b, a = base.getpixel((x, y))
            if a <= 8:
                out.putpixel((x, y), (r, g, b, a))
                continue
            _, saturation, value = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hue = ((x / base.width) + (y % frame_size) / frame_size * 0.42
                   + frame * 0.13) % 1.0
            # Keep the sheet's smoky contrast rather than flattening it into
            # a pure rainbow.  The old portal purples become a full spectrum.
            saturation = max(0.62, min(1.0, saturation * 1.25))
            value = min(1.0, value * 1.18)
            rr, gg, bb = colorsys.hsv_to_rgb(hue, saturation, value)
            out.putpixel((x, y), (round(rr * 255), round(gg * 255), round(bb * 255), a))
    return out


def bloomheart_texture() -> Image.Image:
    """Four 64x64 frames stacked vertically for an animated portal heart."""
    img = new_tex(64, 256)
    d = ImageDraw.Draw(img)
    for frame in range(4):
        fy = frame * 64
        pulse = [0.55, 1.0, 0.75, 1.25][frame]
        # Heart sigil region 0..32.
        cx, cy = 16, 16
        # Outer ring of small petals.
        for i in range(10):
            angle = i * math.tau / 10
            x = round(cx + math.cos(angle) * 12)
            y = round(cy + math.sin(angle) * 12)
            color = PETAL_PINK[2] if frame < 2 else PETAL_PINK[3]
            d.ellipse((x - 2, y - 1, x + 2, y + 1), fill=rgba(color))
            d.point((x, y - 1), fill=rgba(PETAL_PINK[5]))
        # Heart shape made from two lobes and a point.
        heart = [
            (8, 13), (7, 9), (9, 7), (12, 8), (16, 11), (20, 8), (23, 7),
            (25, 9), (24, 13), (16, 24), (8, 13),
        ]
        d.polygon(heart, fill=rgba(PETAL_PINK[2] if frame % 2 else PETAL_PINK[3]))
        d.line(heart, fill=rgba(PETAL_PINK[0]), width=1)
        # Bright inner glow.
        d.ellipse((12, 10, 20, 17), fill=rgba(PETAL_PINK[4]))
        d.ellipse((14, 11, 18, 15), fill=rgba("#ffe6f0"))
        d.point((15, 12), fill=rgba("#ffffff"))
        # Rune ring.
        for i in range(12):
            angle = i * math.tau / 12
            x = round(cx + math.cos(angle) * 9)
            y = round(cy + math.sin(angle) * 9)
            c = "#ffe9a8" if (i + frame) % 3 else "#b7fff1"
            d.point((x, y), fill=rgba(c, min(255, round(150 * pulse))))
        # Petal tile at 32..48 x 0..16.
        for y in range(16):
            for x in range(16):
                dx, dy = x - 8, y - 8
                rr = math.hypot(dx, dy)
                if 2.5 <= rr <= 7.5 and not (abs(dx) < 1 and dy > 5):
                    color = PETAL_PINK[2] if rr > 5 else PETAL_PINK[3]
                    if (x + y + frame) % 5 == 0:
                        color = PETAL_PINK[4]
                    img.putpixel((32 + x, fy + y), rgba(color))
        d = ImageDraw.Draw(img)
        # Glow tile at 48..64 x 0..16.
        for y in range(16):
            for x in range(16):
                dx, dy = x - 8, y - 8
                rr = math.hypot(dx, dy)
                if rr < 7:
                    alpha = max(0, round((7 - rr) * 36 * pulse))
                    if alpha:
                        img.putpixel((48 + x, fy + y), (255, 243, 176, min(255, alpha)))
        # Base rune band at 32..64 x 16..32.
        for x in range(32, 64):
            for y in range(16, 32):
                xx, yy = x - 48, y - 24
                if abs(xx) + abs(yy) in (7, 8) or (abs(xx) <= 1 and abs(yy) <= 6):
                    img.putpixel((x, fy + y), rgba("#ffe9a8", 210))
                elif (xx * xx + yy * yy) < 20 and (x + y + frame) % 3 == 0:
                    img.putpixel((x, fy + y), rgba("#b7fff1", 130))
        d = ImageDraw.Draw(img)
    return img


# ---------------------------------------------------------------------------
# Giant bloom textures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GiantSpec:
    key: str
    label: str
    petal: tuple[str, ...]
    light: tuple[str, ...]
    center: tuple[str, ...]
    calyx: tuple[str, ...]
    glow: bool = False


GIANT_FLOWERS: list[GiantSpec] = [
    GiantSpec("giant_sunflower", "Giant Sunflower", PETAL_GOLD, ("#ffe58a", "#fff4bd", "#fffbe6"), ("#4a2a0b", "#7a4a13", "#b87822", "#e6b64a"), ("#3d5c2a", "#5c803a", "#7fa84e")),
    GiantSpec("giant_rosequartz", "Giant Rosequartz", PETAL_PINK, ("#ffd0e1", "#ffe8f0", "#fff7fa"), ("#6b2440", "#a83d62", "#e06b91", "#ffb2c8"), ("#3d5c2a", "#6a8e45", "#8fba5e")),
    GiantSpec("giant_skybell", "Giant Skybell", PETAL_BLUE, ("#c6f0ff", "#e5faff", "#ffffff"), ("#1f355e", "#35568e", "#5d86bd", "#a9d8f5"), ("#2e5a3a", "#4f8050", "#75a86b")),
    GiantSpec("giant_amethyst", "Giant Amethyst", PETAL_PURPLE, ("#e9d2ff", "#f6ebff", "#ffffff"), ("#3a245e", "#5d3f91", "#8e63c9", "#c9a6f2"), ("#3d5c2a", "#5f7d42", "#88a75e")),
    GiantSpec("giant_emberbloom", "Giant Emberbloom", PETAL_ORANGE, ("#ffd38d", "#ffe8b8", "#fff9e4"), ("#5a240b", "#8f3d14", "#c96720", "#f4a14a"), ("#4a4a1e", "#727a2e", "#9ca346")),
    GiantSpec("giant_lumen", "Giant Lumen Bloom", ("#6fc7be", "#9ff0df", "#d4fff7"), ("#e4fff9", "#f7fffd", "#ffffff"), ("#7a5a1c", "#b08a2b", "#e0c05a", "#fff0a0"), ("#2e5a4a", "#4f8066", "#75a88a"), glow=True),
]


def giant_bloom_texture(spec: GiantSpec) -> Image.Image:
    img = new_tex(64, 64)
    d = ImageDraw.Draw(img)
    # Large petal tile 0..24 x 0..24.
    _draw_petal_tile(d, (0, 0, 24, 24), spec.petal, spec.light[2], 201, spec.glow)
    # Light petal tile 24..48 x 0..24.
    _draw_petal_tile(d, (24, 0, 24, 24), spec.light, "#ffffff", 202, spec.glow)
    # Centre disc 0..28 x 28..56.
    _draw_center_tile(d, (0, 28, 28, 28), spec.center, 203)
    # Calyx 30..46 x 28..44.
    _draw_leaf_tile(d, (30, 28, 16, 16), spec.calyx, 204)
    # Pollen specks 48..56 x 0..8.
    for i in range(14):
        x = 48 + hrand(i, 0, 205) % 8
        y = hrand(i, 1, 206) % 8
        put(img, x, y, "#fff2a8" if i % 3 else "#ffffff", 230)
    # A spare leaf 48..64 x 10..26.
    _draw_leaf_tile(d, (48, 10, 16, 16), spec.calyx, 207)
    # Petal edge 48..56 x 28..36.
    for y in range(28, 36):
        for x in range(48, 56):
            put(img, x, y, spec.petal[1] if (x + y) % 3 else spec.petal[0])
    # Extra veins radiating through the main petals.
    for x0, y0 in [(12, 0), (0, 12)]:
        for i in range(8):
            put(img, x0 + (12 - x0) * i // 8, y0 + (12 - y0) * i // 8, spec.light[2], 180)
    return img


# ---------------------------------------------------------------------------
# Particle atlas and item icon
# ---------------------------------------------------------------------------


def particle_atlas() -> Image.Image:
    img = new_tex(64, 64)
    d = ImageDraw.Draw(img)
    # 0,0: petal.
    for y in range(16):
        for x in range(16):
            dx, dy = x - 8, y - 8
            if (dx * dx) / 30 + (dy * dy) / 55 <= 1:
                color = PETAL_PINK[3] if dx < 1 else PETAL_PINK[4]
                if abs(dx) < 1 and abs(dy) < 6:
                    color = PETAL_PINK[5]
                img.putpixel((x, y), rgba(color))
    # 16,0: sparkle.
    for x, y in [(24, 3), (23, 4), (24, 4), (25, 4), (24, 5), (24, 10), (23, 11), (24, 11), (25, 11), (24, 12)]:
        put(img, x, y, "#fff6c8")
    for x, y in [(22, 7), (26, 7), (20, 11), (28, 11)]:
        put(img, x, y, "#ffe58a", 180)
    # 32,0: firefly.
    d.ellipse((38, 4, 42, 8), fill=rgba("#fff8c4"))
    d.ellipse((40, 2, 44, 6), fill=rgba("#bfffa8", 170))
    put(img, 40, 6, "#ffffff")
    # 48,0: pollen.
    d.ellipse((54, 5, 57, 8), fill=rgba("#ffe58a"))
    put(img, 55, 6, "#ffffff")
    # 0,16: ripple.
    d.ellipse((1, 19, 14, 30), outline=rgba("#9ff0e4", 200), width=1)
    d.ellipse((4, 22, 11, 27), outline=rgba("#d4fff9", 150), width=1)
    # 16,16: aura ring.
    for i in range(16):
        angle = i * math.tau / 16
        x = round(24 + math.cos(angle) * 7)
        y = round(24 + math.sin(angle) * 7)
        put(img, x, y, "#ffb7dc" if i % 2 else "#ffe6f0")
    # 32,16: soft mote.
    d.ellipse((38, 20, 42, 24), fill=rgba("#ffffff", 180))
    d.ellipse((39, 21, 41, 23), fill=rgba("#fff8d0", 230))
    # 48,16: dew.
    d.ellipse((54, 19, 57, 23), fill=rgba("#a8f5ff", 190))
    put(img, 55, 20, "#ffffff")
    return img


def portal_item_icon() -> Image.Image:
    img = new_tex(32, 32)
    d = ImageDraw.Draw(img)
    # A ring of tiny flowers around a glowing heart.
    colors = [PETAL_PINK[4], PETAL_GOLD[4], PETAL_BLUE[4], PETAL_PURPLE[4], PETAL_PINK[5], PETAL_ORANGE[4], PETAL_WHITE[5], PETAL_PINK[4]]
    for i in range(8):
        angle = -math.pi / 2 + i * math.tau / 8
        cx = round(16 + math.cos(angle) * 9)
        cy = round(16 + math.sin(angle) * 9)
        color = colors[i]
        # Four petals and a centre.
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            put(img, cx + dx, cy + dy, color)
        put(img, cx + 1, cy + 1, shade(color, -0.25))
        put(img, cx, cy, PETAL_GOLD[5])
    # Vine ring.
    for i in range(40):
        angle = i * math.tau / 40
        x = round(16 + math.cos(angle) * 11)
        y = round(16 + math.sin(angle) * 11)
        if i % 3:
            put(img, x, y, MOSS[2] if i % 2 else MOSS[3])
    # A square rainbow portal set into the flower ring.  This reads as a
    # Bloomgate rather than the old heart-shaped activation sigil.
    rainbow = ["#ff5b6e", "#ff9b4a", "#ffe35a", "#8dde63",
               "#55dfd4", "#5b9cff", "#a873ff", "#ff70d4"]
    for y in range(10, 23):
        for x in range(10, 23):
            if x in (10, 22) or y in (10, 22):
                pixel = (32, 20, 45, 245)
            else:
                pixel = rgba(rainbow[(x + y) % len(rainbow)])
            img.putpixel((x, y), pixel)
    # A bright centre and two flower pixels at the cardinal points.
    d.rectangle((14, 14, 18, 18), fill=rgba("#fff8df", 235))
    for x, y in [(15, 16), (16, 15), (17, 16), (16, 17)]:
        put(img, x, y, "#ffffff")
    # Soft sparkles.
    for x, y in [(6, 5), (25, 7), (27, 24), (5, 26), (16, 2)]:
        put(img, x, y, "#fff6c8")
    return img


def pack_icon() -> Image.Image:
    """A square pack icon: the Bloomgate sigil over a soft twilight wash."""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    for y in range(256):
        t = y / 255.0
        top = mix("#24172f", "#7d315f", min(1.0, t * 1.4))
        bottom = mix("#7d315f", "#f0a7b8", max(0.0, (t - 0.55) / 0.45))
        color = top if t < 0.55 else bottom
        d.line([(0, y), (255, y)], fill=color)
    # Soft radial glow behind the sigil.
    glow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for radius, alpha in [(120, 20), (100, 28), (82, 38), (64, 48), (48, 58)]:
        gd.ellipse((128 - radius, 128 - radius, 128 + radius, 128 + radius),
                   fill=(255, 224, 188, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)
    icon = portal_item_icon().resize((224, 224), Image.Resampling.NEAREST)
    img.alpha_composite(icon, (16, 16))
    # Tiny stars in the corners.
    for x, y, c in [(36, 44, "#fff2b8"), (216, 52, "#ffd6e2"), (44, 212, "#c6f0ff"),
                    (210, 206, "#fff2b8"), (128, 18, "#ffffff")]:
        d.point((x, y), fill=rgba(c, 230))
        d.point((x - 1, y), fill=rgba(c, 120))
        d.point((x + 1, y), fill=rgba(c, 120))
    d.rectangle((4, 4, 251, 251), outline=rgba("#ffe6ef", 90), width=2)
    return img


def lily_bloom_texture() -> Image.Image:
    img = new_tex(32, 32)
    d = ImageDraw.Draw(img)
    # Lily pad tile 0..16 x 0..16.
    d.ellipse((0, 0, 15, 15), fill=rgba("#3f7d4e"))
    d.ellipse((1, 1, 14, 14), fill=rgba("#589c5d"))
    d.ellipse((2, 2, 13, 13), fill=rgba("#6fba6e"))
    # The characteristic notch.
    d.polygon([(8, 8), (15, 2), (15, 8)], fill=(0, 0, 0, 0))
    # Veins.
    for angle in range(0, 360, 45):
        x = round(8 + math.cos(math.radians(angle)) * 6)
        y = round(8 + math.sin(math.radians(angle)) * 6)
        line(d, [(8, 8), (x, y)], "#3d6e43")
    d.point((5, 4), fill=rgba("#a6e39a"))
    d.point((11, 10), fill=rgba("#2f5f39"))
    # Lotus flower tile 16..24 x 0..8.
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        cx = round(20 + math.cos(angle) * 3)
        cy = round(4 + math.sin(angle) * 2)
        d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=rgba(PETAL_PINK[3]))
        d.point((cx, cy - 1), fill=rgba(PETAL_PINK[5]))
    d.ellipse((19, 3, 21, 5), fill=rgba(PETAL_GOLD[4]))
    # Flower centre tile 24..32 x 0..8.
    d.ellipse((25, 1, 30, 6), fill=rgba(PETAL_GOLD[3]))
    d.ellipse((26, 2, 29, 5), fill=rgba(PETAL_GOLD[4]))
    d.point((27, 3), fill=rgba("#ffffff"))
    # Edge and dew tiles.
    for y in range(8, 16):
        for x in range(16, 24):
            put(img, x, y, "#2f5f39" if (x + y) % 2 else "#3f7d4e")
    for x, y in [(26, 10), (27, 10), (26, 11), (27, 11)]:
        put(img, x, y, "#b9fbff" if (x + y) % 2 else "#ffffff")
    return img


LILY_REGIONS = {
    "pad": (0, 0, 16, 16),
    "petal": (16, 0, 8, 8),
    "center": (24, 0, 8, 8),
    "edge": (16, 8, 8, 8),
    "dew": (24, 8, 8, 8),
}


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

FACES = ("north", "south", "east", "west", "up", "down")


def tile(x: int, y: int, w: int, h: int) -> tuple[int, int, int, int]:
    return (x, y, w, h)


def uv(tile_rect: Sequence[int]) -> dict[str, dict[str, list[int]]]:
    x, y, w, h = tile_rect
    return {face: {"uv": [x, y], "uv_size": [w, h]} for face in FACES}


def uv_faces(tile_rect: Sequence[int], **overrides: Sequence[int]) -> dict[str, dict[str, list[int]]]:
    base = uv(tile_rect)
    for face, rect in overrides.items():
        if face not in FACES:
            raise ValueError(f"unknown face {face}")
        x, y, w, h = rect
        base[face] = {"uv": [x, y], "uv_size": [w, h]}
    return base


def cube(
    origin: Sequence[float],
    size: Sequence[float],
    uv_map: dict[str, dict[str, list[int]]] | Sequence[int],
    rotation: Sequence[float] | None = None,
    pivot: Sequence[float] | None = None,
    inflate: float | None = None,
) -> dict:
    c: dict = {
        "origin": [round(float(v), 5) for v in origin],
        "size": [round(float(v), 5) for v in size],
        "uv": uv(uv_map) if isinstance(uv_map, (list, tuple)) else uv_map,
    }
    if rotation:
        c["rotation"] = [round(float(v), 5) for v in rotation]
    if pivot:
        c["pivot"] = [round(float(v), 5) for v in pivot]
    if inflate:
        c["inflate"] = round(float(inflate), 5)
    return c


def bone(name: str, pivot: Sequence[float], cubes: list[dict], parent: str | None = None, rotation: Sequence[float] | None = None) -> dict:
    b: dict = {"name": name, "pivot": [round(float(v), 5) for v in pivot], "cubes": cubes}
    if parent:
        b["parent"] = parent
    if rotation:
        b["rotation"] = [round(float(v), 5) for v in rotation]
    return b


def geometry(
    identifier: str,
    texture_width: int,
    texture_height: int,
    bones: list[dict],
    visible_bounds_width: float = 1.0,
    visible_bounds_height: float = 1.0,
    visible_bounds_offset: Sequence[float] = (0.0, 0.5, 0.0),
) -> dict:
    return {
        "format_version": "1.21.90",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": identifier,
                    "texture_width": texture_width,
                    "texture_height": texture_height,
                    "visible_bounds_width": visible_bounds_width,
                    "visible_bounds_height": visible_bounds_height,
                    "visible_bounds_offset": [round(float(v), 5) for v in visible_bounds_offset],
                },
                "bones": bones,
            }
        ],
    }


def entity_geometry(
    identifier: str,
    texture_width: int,
    texture_height: int,
    bones: list[dict],
    visible_bounds_width: float = 1.0,
    visible_bounds_height: float = 1.0,
    visible_bounds_offset: Sequence[float] = (0.0, 0.5, 0.0),
) -> dict:
    geo = geometry(identifier, texture_width, texture_height, bones, visible_bounds_width, visible_bounds_height, visible_bounds_offset)
    geo["format_version"] = "1.12.0"
    return geo


# ---------------------------------------------------------------------------
# Block geometry
# ---------------------------------------------------------------------------


def small_flower_geometry() -> dict:
    t = SMALL_FLOWER_REGIONS
    # Five broad outer petals and three shorter inner petals.  The older
    # six-plus-six arrangement read as a lumpy rosette at Minecraft scale;
    # this has a clear flower silhouette from above and from the side.
    petals = []
    for i in range(5):
        angle = i * 72
        petals.append(
            cube(
                [2, 18, -2.2],
                [5.2, 1, 4.4],
                uv_faces(t["petal"], up=t["petal"], down=t["petal"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]),
                rotation=[0, angle, 0],
                pivot=[0, 18, 0],
            )
        )
    inner = []
    for i in range(3):
        angle = 24 + i * 120
        inner.append(
            cube(
                [1.4, 19.3, -1.4],
                [3.8, 1, 2.8],
                uv_faces(t["petal"], up=t["petal"], down=t["petal"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]),
                rotation=[0, angle, 0],
                pivot=[0, 19.2, 0],
            )
        )
    stamens = []
    for i in range(3):
        angle = i * 120 + 30
        stamens.append(
            cube(
                [math.cos(math.radians(angle)) * 1.2 - 0.5, 21, math.sin(math.radians(angle)) * 1.2 - 0.5],
                [1, 1.8, 1],
                uv(t["center"]),
            )
        )
    cubes = [
        cube([-1, 0, -1], [2, 20, 2], uv_faces(t["stem"], up=t["stem"], down=t["stem"])),
        cube([0, 5, -1], [8, 1.2, 2], uv_faces(t["leaf"], up=t["leaf"], down=t["leaf"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]), rotation=[0, 22, 0], pivot=[0, 5.5, 0]),
        cube([-8, 10, -1], [8, 1.2, 2], uv_faces(t["leaf"], up=t["leaf"], down=t["leaf"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]), rotation=[0, -28, 0], pivot=[0, 10.6, 0]),
        cube([-2.5, 18, -2.5], [5, 4, 5], uv(t["center"])),
        *petals,
        *inner,
        *stamens,
    ]
    return geometry("geometry.bl.small_flower", 32, 32, [bone("flower", [0, 0, 0], cubes)], 1.6, 2.2, [0, 0.75, 0])


def portal_flower_geometry() -> dict:
    t = PORTAL_FLOWER_REGIONS
    petals = []
    for i in range(8):
        angle = i * 45
        petals.append(
            cube(
                [3, 20, -3],
                [8, 1.4, 6],
                uv_faces(t["petal"], up=t["petal"], down=t["petal"], north=t["inner"], south=t["inner"], east=t["glow"], west=t["glow"]),
                rotation=[0, angle, 0],
                pivot=[0, 20, 0],
            )
        )
    inner = []
    for i in range(8):
        angle = 22.5 + i * 45
        inner.append(
            cube(
                [2, 21.5, -2],
                [6, 1.1, 4],
                uv_faces(t["inner"], up=t["inner"], down=t["inner"], north=t["petal"], south=t["petal"], east=t["glow"], west=t["glow"]),
                rotation=[0, angle, 0],
                pivot=[0, 21.5, 0],
            )
        )
    glow = []
    for i in range(4):
        angle = i * 90 + 45
        glow.append(
            cube(
                [math.cos(math.radians(angle)) * 7 - 0.5, 26 + (i % 2), math.sin(math.radians(angle)) * 7 - 0.5],
                [1, 1, 1],
                uv(t["glow"]),
            )
        )
    cubes = [
        cube([-1.5, 0, -1.5], [3, 24, 3], uv_faces(t["stem"], up=t["stem"], down=t["stem"])),
        cube([0, 7, -1.5], [11, 1.5, 3], uv_faces(t["leaf"], up=t["leaf"], down=t["leaf"], north=t["stem"], south=t["stem"], east=t["stem"], west=t["stem"]), rotation=[0, 20, 0], pivot=[0, 7.75, 0]),
        cube([-11, 13, -1.5], [11, 1.5, 3], uv_faces(t["leaf"], up=t["leaf"], down=t["leaf"], north=t["stem"], south=t["stem"], east=t["stem"], west=t["stem"]), rotation=[0, -24, 0], pivot=[0, 13.75, 0]),
        cube([-4, 18, -4], [8, 2, 8], uv_faces(t["leaf"], up=t["leaf"], down=t["stem"], north=t["leaf"], south=t["leaf"], east=t["leaf"], west=t["leaf"])),
        cube([-4, 20, -4], [8, 6, 8], uv(t["center"])),
        *petals,
        *inner,
        *glow,
    ]
    return geometry("geometry.bl.portal_flower", 64, 64, [bone("flower", [0, 0, 0], cubes)], 2.2, 3.4, [0, 1.3, 0])


def rainbow_portal_geometry() -> dict:
    """A flat End-portal-like surface, slightly above the ground plane."""
    t = (0, 0, 32, 32)
    cube_data = cube(
        [-8, 0.01, -8],
        [16, 0.06, 16],
        uv_faces(t, up=t, down=t, north=t, south=t, east=t, west=t),
    )
    return geometry(
        "geometry.bl.rainbow_portal", 32, 1024,
        [bone("portal", [0, 0, 0], [cube_data])],
        1.0, 0.1, [0, 0.0, 0],
    )


def bloomheart_geometry() -> dict:
    t = {
        "heart": (0, 0, 32, 32),
        "petal": (32, 0, 16, 16),
        "glow": (48, 0, 16, 16),
        "rune": (32, 16, 32, 16),
    }
    petals = []
    for i in range(8):
        angle = i * 45
        petals.append(
            cube(
                [5, 2, -2],
                [6, 1.5, 4],
                uv_faces(t["petal"], up=t["petal"], down=t["petal"], north=t["glow"], south=t["glow"], east=t["glow"], west=t["glow"]),
                rotation=[0, angle, 0],
                pivot=[0, 3, 0],
            )
        )
    glow = []
    for i in range(4):
        angle = i * 90
        glow.append(cube([math.cos(math.radians(angle)) * 6 - 0.75, 13.5 + (i % 2) * 0.5, math.sin(math.radians(angle)) * 6 - 0.75], [1.5, 1.5, 1.5], uv(t["glow"])))
    cubes = [
        cube([-7, 0, -7], [14, 3, 14], uv_faces(t["rune"], up=t["rune"], down=t["rune"], north=t["petal"], south=t["petal"], east=t["petal"], west=t["petal"])),
        cube([-5, 3, -5], [10, 11, 10], uv(t["heart"])),
        *petals,
        *glow,
    ]
    return geometry("geometry.bl.bloomheart", 64, 64, [bone("heart", [0, 0, 0], cubes)], 1.6, 1.6, [0, 0.6, 0])


def giant_bloom_geometry() -> dict:
    t = {
        "petal": (0, 0, 24, 24),
        "light": (24, 0, 24, 24),
        "center": (0, 28, 28, 28),
        "calyx": (30, 28, 16, 16),
        "pollen": (48, 0, 8, 8),
        "leaf": (48, 10, 16, 16),
        "edge": (48, 28, 8, 8),
    }
    # Six broad outer petals, five shorter inner ones and five sepals create
    # a cleaner, more readable flower than the previous eight-plus-eight
    # stack while keeping the tree-sized scale.
    outer = []
    for i in range(6):
        outer.append(
            cube(
                [6, 10, -4],
                [9, 4, 8],
                uv_faces(t["petal"], up=t["petal"], down=t["light"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]),
                rotation=[0, i * 60, 0],
                pivot=[0, 12, 0],
            )
        )
    inner = []
    for i in range(5):
        inner.append(
            cube(
                [5, 13, -3],
                [8, 3, 6],
                uv_faces(t["light"], up=t["light"], down=t["petal"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]),
                rotation=[0, 24 + i * 72, 0],
                pivot=[0, 14.5, 0],
            )
        )
    sepals = []
    for i in range(5):
        sepals.append(
            cube(
                [6, 3, -1.5],
                [7, 2, 3],
                uv_faces(t["calyx"], up=t["calyx"], down=t["calyx"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"]),
                rotation=[0, 36 + i * 72, 0],
                pivot=[0, 4, 0],
            )
        )
    stamens = []
    for i in range(6):
        angle = i * 60
        stamens.append(
            cube(
                [math.cos(math.radians(angle)) * 4 - 0.5, 15, math.sin(math.radians(angle)) * 4 - 0.5],
                [1, 4 + (i % 2) * 2, 1],
                uv(t["center"]),
            )
        )
    pollen = []
    for i in range(5):
        angle = i * 72 + 15
        pollen.append(
            cube(
                [math.cos(math.radians(angle)) * (4 + i % 3) - 0.5, 20 + (i % 3) * 1.5, math.sin(math.radians(angle)) * (4 + i % 3) - 0.5],
                [1, 1, 1],
                uv(t["pollen"]),
            )
        )
    cubes = [
        cube([-3, 0, -3], [6, 11, 6], uv_faces(t["calyx"], up=t["calyx"], down=t["calyx"], north=t["leaf"], south=t["leaf"], east=t["leaf"], west=t["leaf"])),
        cube([-8, 10, -8], [16, 5, 16], uv(t["center"])),
        cube([-4, 15, -4], [8, 2, 8], uv(t["center"])),
        *sepals,
        *outer,
        *inner,
        *stamens,
        *pollen,
    ]
    return geometry("geometry.bl.giant_bloom", 64, 64, [bone("bloom", [0, 0, 0], cubes)], 3.2, 3.2, [0, 1.5, 0])


def dewgrass_geometry() -> dict:
    t = (0, 0, 32, 32)
    edge = (0, 0, 1, 1)
    cubes = [
        cube([-8, 0, 0], [16, 16, 0.25], uv_faces(t, north=t, south=t, up=edge, down=edge, east=edge, west=edge)),
        cube([0, 0, -8], [0.25, 16, 16], uv_faces(t, north=t, south=t, up=edge, down=edge, east=edge, west=edge)),
        cube([-6.4, 0, -6.4], [12.8, 13, 0.25], uv_faces(t, north=t, south=t, up=edge, down=edge, east=edge, west=edge), rotation=[0, 45, 0], pivot=[0, 0, 0]),
    ]
    return geometry("geometry.bl.dewgrass", 32, 32, [bone("grass", [0, 0, 0], cubes)], 1.6, 1.6, [0, 0.6, 0])


def lily_bloom_geometry() -> dict:
    t = LILY_REGIONS
    petals = []
    for i in range(5):
        petals.append(
            cube(
                [0, 0.6, -1.5],
                [6, 0.8, 3],
                uv_faces(t["petal"], up=t["petal"], down=t["petal"], north=t["center"], south=t["center"], east=t["center"], west=t["center"]),
                rotation=[0, i * 72, 0],
                pivot=[0, 1, 0],
            )
        )
    cubes = [
        cube([-8, 0, -8], [16, 0.5, 16], uv_faces(t["pad"], up=t["pad"], down=t["edge"], north=t["edge"], south=t["edge"], east=t["edge"], west=t["edge"])),
        cube([-2, 0.4, -2], [4, 1.5, 4], uv(t["center"])),
        *petals,
        cube([2, 0.7, 2], [1, 1, 1], uv(t["dew"])),
    ]
    return geometry("geometry.bl.lily_bloom", 32, 32, [bone("lily", [0, 0, 0], cubes)], 1.6, 1.2, [0, 0.3, 0])


# ---------------------------------------------------------------------------
# Block roster
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BlockSpec:
    key: str
    label: str
    kind: str
    geometry: str
    texture: str
    faces: dict[str, str]
    render_method: str = "opaque"
    light: int = 0
    dampening: int = 15
    hardness: float = 0.5
    collision: bool | dict = True
    selection: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None
    map_color: str = "#7fbf5f"
    sound: str = "grass"
    menu: str | None = "nature"
    flammable: bool = False
    placement: tuple[str, ...] = ()
    particle_count: int = 16
    item_visual: bool = True
    drop_item: bool = True


FULL = "minecraft:geometry.full_block"


def _flower_selection(height: float, width: float = 12.0) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    return ((-width / 2, 0, -width / 2), (width, height, width))


BLOCK_SPECS: list[BlockSpec] = [
    BlockSpec(
        "petal_grass", "Petal Grass", "full", FULL, "bl_petal_grass_side",
        {"*": "bl_petal_grass_side", "up": "bl_petal_grass_top", "down": "bl_bloom_dirt"},
        hardness=0.6, map_color="#6fbd52", sound="grass", menu="nature", flammable=True,
    ),
    BlockSpec(
        "bloom_dirt", "Bloom Dirt", "full", FULL, "bl_bloom_dirt", {"*": "bl_bloom_dirt"},
        hardness=0.5, map_color="#7a553b", sound="grass", menu="nature",
    ),
    BlockSpec(
        "bloom_stone", "Bloom Stone", "full", FULL, "bl_bloom_stone", {"*": "bl_bloom_stone"},
        hardness=1.5, map_color="#72767d", sound="stone", menu="construction",
    ),
    BlockSpec(
        "bloomwood_log", "Bloomwood Log", "full", FULL, "bl_bloomwood_log_side",
        {"*": "bl_bloomwood_log_side", "up": "bl_bloomwood_log_top", "down": "bl_bloomwood_log_top"},
        hardness=2.0, map_color="#6d4a30", sound="wood", menu="construction", flammable=True,
    ),
    BlockSpec(
        "bloomwood_planks", "Bloomwood Planks", "full", FULL, "bl_bloomwood_planks", {"*": "bl_bloomwood_planks"},
        hardness=2.0, map_color="#b98a50", sound="wood", menu="construction", flammable=True,
    ),
    BlockSpec(
        "petal_path", "Petal Path", "full", FULL, "bl_petal_path", {"*": "bl_petal_path"},
        hardness=0.4, map_color="#b56c85", sound="grass", menu="construction",
    ),
    BlockSpec(
        "canopy_leaves", "Canopy Leaves", "full", FULL, "bl_canopy_leaves", {"*": "bl_canopy_leaves"},
        render_method="alpha_test", dampening=4, hardness=0.2, map_color="#3b844d", sound="grass", menu="nature", flammable=True,
    ),
    BlockSpec(
        "glowbud_leaves", "Glowbud Leaves", "full", FULL, "bl_glowbud_leaves", {"*": "bl_glowbud_leaves"},
        render_method="alpha_test", light=3, dampening=3, hardness=0.2, map_color="#4a9b57", sound="grass", menu="nature", flammable=True,
    ),
    BlockSpec(
        "dewgrass", "Dewgrass", "custom", "geometry.bl.dewgrass", "bl_dewgrass", {"*": "bl_dewgrass"},
        render_method="alpha_test", dampening=0, hardness=0.05, collision=False,
        selection=_flower_selection(16, 16), map_color="#6fbd52", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:petal_path"),
    ),
    BlockSpec(
        "lily_bloom", "Lily Bloom", "custom", "geometry.bl.lily_bloom", "bl_lily_bloom", {"*": "bl_lily_bloom"},
        render_method="alpha_test", dampening=0, hardness=0.05, collision=False,
        selection=_flower_selection(3, 16), map_color="#589c5d", sound="grass",
        placement=("minecraft:water",),
    ),
    BlockSpec(
        "portal_flower", "Bloomgate Flower", "custom", "geometry.bl.portal_flower", "bl_portal_flower", {"*": "bl_portal_flower"},
        render_method="alpha_test", light=9, dampening=0, hardness=0.1, collision=False,
        selection=_flower_selection(16, 16), map_color="#e88ac0", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:petal_path"),
    ),
    BlockSpec(
        "rainbow_portal", "Rainbow Bloomgate", "custom", "geometry.bl.rainbow_portal", "bl_rainbow_portal", {"*": "bl_rainbow_portal"},
        render_method="blend", light=15, dampening=0, hardness=0.1, collision=False,
        selection=((-8, 0, -8), (16, 0.2, 16)), map_color="#ff70d4", sound="glass",
        menu=None, drop_item=False,
    ),
    BlockSpec(
        "bloomheart", "Bloomheart", "custom", "geometry.bl.bloomheart", "bl_bloomheart", {"*": "bl_bloomheart"},
        render_method="alpha_test", light=12, dampening=0, hardness=0.2, collision=True,
        selection=(( -8, 0, -8), (16, 16, 16)), map_color="#f07aa8", sound="glass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_planks", "bl:petal_path"),
        particle_count=24, menu=None, drop_item=False,
    ),
    BlockSpec(
        "giant_sunflower", "Giant Sunflower", "custom", "geometry.bl.giant_bloom", "bl_giant_sunflower", {"*": "bl_giant_sunflower"},
        render_method="alpha_test", dampening=0, hardness=0.3, collision=False,
        selection=((-8, 0, -8), (16, 16, 16)), map_color="#f4c53b", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_log", "bl:petal_path"),
    ),
    BlockSpec(
        "giant_rosequartz", "Giant Rosequartz", "custom", "geometry.bl.giant_bloom", "bl_giant_rosequartz", {"*": "bl_giant_rosequartz"},
        render_method="alpha_test", dampening=0, hardness=0.3, collision=False,
        selection=((-8, 0, -8), (16, 16, 16)), map_color="#ee6493", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_log", "bl:petal_path"),
    ),
    BlockSpec(
        "giant_skybell", "Giant Skybell", "custom", "geometry.bl.giant_bloom", "bl_giant_skybell", {"*": "bl_giant_skybell"},
        render_method="alpha_test", dampening=0, hardness=0.3, collision=False,
        selection=((-8, 0, -8), (16, 16, 16)), map_color="#72afe2", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_log", "bl:petal_path"),
    ),
    BlockSpec(
        "giant_amethyst", "Giant Amethyst", "custom", "geometry.bl.giant_bloom", "bl_giant_amethyst", {"*": "bl_giant_amethyst"},
        render_method="alpha_test", dampening=0, hardness=0.3, collision=False,
        selection=((-8, 0, -8), (16, 16, 16)), map_color="#a67ade", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_log", "bl:petal_path"),
    ),
    BlockSpec(
        "giant_emberbloom", "Giant Emberbloom", "custom", "geometry.bl.giant_bloom", "bl_giant_emberbloom", {"*": "bl_giant_emberbloom"},
        render_method="alpha_test", dampening=0, hardness=0.3, collision=False,
        selection=((-8, 0, -8), (16, 16, 16)), map_color="#f4923b", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_log", "bl:petal_path"),
    ),
    BlockSpec(
        "giant_lumen", "Giant Lumen Bloom", "custom", "geometry.bl.giant_bloom", "bl_giant_lumen", {"*": "bl_giant_lumen"},
        render_method="alpha_test", light=12, dampening=0, hardness=0.3, collision=False,
        selection=((-8, 0, -8), (16, 16, 16)), map_color="#9ff0df", sound="grass",
        placement=("minecraft:grass_block", "minecraft:dirt", "bl:petal_grass", "bl:bloom_dirt", "bl:bloom_stone", "bl:bloomwood_log", "bl:petal_path"),
    ),
]

# Small flowers share one model and are added as individual blocks.
for _spec in SMALL_FLOWERS:
    BLOCK_SPECS.append(
        BlockSpec(
            _spec.key, _spec.label, "custom", "geometry.bl.small_flower", f"bl_{_spec.key}", {"*": f"bl_{_spec.key}"},
            render_method="alpha_test", light=8 if _spec.glow else 0, dampening=0, hardness=0.05, collision=False,
            selection=_flower_selection(16, 12), map_color=_spec.map_color, sound="grass",
            placement=("minecraft:grass_block", "minecraft:dirt", "minecraft:podzol", "minecraft:mycelium", "bl:petal_grass", "bl:bloom_dirt", "bl:petal_path"),
            particle_count=12,
        )
    )


def block_material_instances(spec: BlockSpec) -> dict:
    result = {}
    for face, texture in spec.faces.items():
        result[face] = {
            "texture": texture,
            "render_method": spec.render_method,
            "face_dimming": False if spec.key in {"bloomheart", "rainbow_portal"} else True,
            "ambient_occlusion": spec.kind == "full",
        }
    return result


def block_geometry_files() -> dict[str, dict]:
    """Unique block geometry files keyed by identifier."""
    return {
        "small_flower": small_flower_geometry(),
        "portal_flower": portal_flower_geometry(),
        "rainbow_portal": rainbow_portal_geometry(),
        "bloomheart": bloomheart_geometry(),
        "giant_bloom": giant_bloom_geometry(),
        "dewgrass": dewgrass_geometry(),
        "lily_bloom": lily_bloom_geometry(),
    }


def block_textures() -> dict[str, Image.Image]:
    textures: dict[str, Image.Image] = {
        "bl_petal_grass_top": petal_grass_top(),
        "bl_petal_grass_side": petal_grass_side(),
        "bl_bloom_dirt": bloom_dirt(),
        "bl_bloom_stone": bloom_stone(),
        "bl_bloomwood_log_side": bloomwood_log_side(),
        "bl_bloomwood_log_top": bloomwood_log_top(),
        "bl_bloomwood_planks": bloomwood_planks(),
        "bl_petal_path": petal_path(),
        "bl_canopy_leaves": canopy_leaves(),
        "bl_glowbud_leaves": canopy_leaves(True),
        "bl_dewgrass": None,  # filled below
        "bl_lily_bloom": lily_bloom_texture(),
        "bl_portal_flower": portal_flower_texture(),
        "bl_rainbow_portal": rainbow_portal_texture(),
        "bl_bloomheart": bloomheart_texture(),
    }
    # Dewgrass uses the top part of a larger grass texture with dew drops.
    dew = new_tex(32, 32)
    dd = ImageDraw.Draw(dew)
    for blade in range(7):
        base_x = 2 + blade * 4 + (blade % 2)
        height = 12 + hrand(blade, 1, 301) % 19
        for y in range(height):
            x = base_x + round(math.sin(y * 0.35 + blade) * 1.4)
            color = GRASS[(blade + y) % len(GRASS)]
            if y > height - 4:
                color = GRASS[-1]
            put(dew, x, 31 - y, color)
            if y % 3 == 0:
                put(dew, x + 1, 31 - y, GRASS[max(0, (blade + y) % len(GRASS) - 1)])
        # Dew drop near the tip.
        if blade % 2 == 0:
            put(dew, base_x + 1, 31 - height + 3, "#b9fbff")
            put(dew, base_x + 1, 31 - height + 4, "#e8ffff")
    for x, y in [(7, 25), (18, 20), (26, 27), (13, 14)]:
        put(dew, x, y, PETAL_WHITE[5])
    textures["bl_dewgrass"] = dew
    for spec in SMALL_FLOWERS:
        textures["bl_" + spec.key] = small_flower_texture(spec)
    for spec in GIANT_FLOWERS:
        textures["bl_" + spec.key] = giant_bloom_texture(spec)
    return textures


def terrain_texture_keys() -> dict[str, str]:
    """Map terrain texture keys to their PNG paths."""
    keys = {}
    for spec in BLOCK_SPECS:
        for texture in spec.faces.values():
            keys[texture] = f"textures/blocks/{texture}"
    return keys


# ---------------------------------------------------------------------------
# Entity texture atlases
# ---------------------------------------------------------------------------


class Atlas:
    """A tiny padded shelf-packing atlas.

    Tiles are painted at their final size, then a one-pixel border is bled
    outwards so mipmapping and texture filtering cannot pull in a neighbouring
    tile.  The returned rectangle is the inner, UV-addressable area.
    """

    def __init__(self, width: int = 128, height: int = 128):
        self.width = width
        self.height = height
        self.image = new_tex(width, height)
        self.x = 1
        self.y = 1
        self.row_height = 0
        self.tiles: dict[str, tuple[int, int, int, int]] = {}

    def add(self, name: str, w: int, h: int, painter: Callable[[int, int], Image.Image]) -> tuple[int, int, int, int]:
        pad = 1
        if self.x + w + pad * 2 > self.width:
            self.x = 1
            self.y += self.row_height + pad * 2
            self.row_height = 0
        if self.y + h + pad * 2 > self.height:
            raise RuntimeError(f"atlas full while adding {name} ({w}x{h})")
        tile_img = painter(w, h)
        if tile_img.size != (w, h):
            raise ValueError(f"painter for {name} returned {tile_img.size}, expected {(w, h)}")
        x, y = self.x, self.y
        self.image.alpha_composite(tile_img, (x, y))
        # Bleed every edge into the padding.
        for i in range(h):
            self.image.putpixel((x - 1, y + i), tile_img.getpixel((0, i)))
            self.image.putpixel((x + w, y + i), tile_img.getpixel((w - 1, i)))
        for i in range(w):
            self.image.putpixel((x + i, y - 1), tile_img.getpixel((i, 0)))
            self.image.putpixel((x + i, y + h), tile_img.getpixel((i, h - 1)))
        for dx, dy, sx, sy in [(-1, -1, 0, 0), (w, -1, w - 1, 0), (-1, h, 0, h - 1), (w, h, w - 1, h - 1)]:
            self.image.putpixel((x + dx, y + dy), tile_img.getpixel((sx, sy)))
        self.tiles[name] = (x, y, w, h)
        self.x += w + pad * 2
        self.row_height = max(self.row_height, h)
        return self.tiles[name]


def paint_noise(w: int, h: int, palette: Sequence[str], seed: int, alpha: int = 255) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, w - 1, h - 1), palette, seed, alpha)
    return img


def petalwing_body_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    base = ["#d9a6c4", "#e6b7d1", "#f0c8de", "#f7d9e8", "#c98fb4", "#b57a9e"]
    noise_rect(d, (0, 0, w - 1, h - 1), base, 401)
    # Soft cream underside fading up from the bottom.
    for y in range(h):
        for x in range(w):
            if y > h * 0.62 and hrand(x, y, 402) % 3:
                d.point((x, y), fill=rgba("#ffe4ef", 180))
    # Dark abdominal bands.
    for y in (3, 7, 11, 15):
        for x in range(w):
            if hrand(x, y, 403) % 5:
                d.point((x, y), fill=rgba("#6b3b63"))
    # A lighter centre line and fuzzy flecks.
    for y in range(h):
        d.point((w // 2, y), fill=rgba("#f9d9e5", 190))
    for i in range(22):
        x, y = hrand(i, 1, 404) % w, hrand(i, 2, 405) % h
        d.point((x, y), fill=rgba("#8d5c86" if i % 3 else "#ffe8f1", 210))
    return img


def petalwing_head_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    base = ["#5e3f68", "#714b7a", "#855a8c", "#9a6d9f", "#b184b4"]
    noise_rect(d, (0, 0, w - 1, h - 1), base, 411)
    for y in range(h):
        for x in range(w):
            if y < 4 and hrand(x, y, 412) % 3:
                d.point((x, y), fill=rgba("#c39cc4"))
    for i in range(10):
        x, y = hrand(i, 3, 413) % w, hrand(i, 4, 414) % h
        d.point((x, y), fill=rgba("#3f294b" if i % 2 else "#d9b0d3"))
    return img


def petalwing_face_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = petalwing_head_tile(w, h)
    d = ImageDraw.Draw(img)
    # Fluffy cream muzzle and cheeks.
    d.ellipse((4, 9, 11, 15), fill=rgba("#f7dfe7"))
    d.ellipse((1, 10, 5, 14), fill=rgba("#f1c9db"))
    d.ellipse((10, 10, 14, 14), fill=rgba("#f1c9db"))
    # Compound eyes: two large almond shapes with a wet highlight.
    for x0, x1 in [(2, 6), (10, 14)]:
        d.ellipse((x0, 3, x1, 9), fill=rgba("#241b3b"))
        d.ellipse((x0 + 1, 4, x1 - 1, 8), fill=rgba("#3f5fa8"))
        d.ellipse((x0 + 1, 4, x0 + 3, 6), fill=rgba("#d4f4ff"))
        d.point((x0 + 1, 7), fill=rgba("#ffffff"))
        d.line([(x0, 3), (x1, 3)], fill=rgba("#160f27"))
    # Smile, nose, antenna bases.
    d.point((7, 12), fill=rgba("#7a3f60"))
    d.point((8, 12), fill=rgba("#7a3f60"))
    d.line([(6, 13), (7, 14), (9, 14), (10, 13)], fill=rgba("#7a3f60"))
    d.point((4, 11), fill=rgba("#ff9fc4"))
    d.point((11, 11), fill=rgba("#ff9fc4"))
    d.point((6, 1), fill=rgba("#e9c6a8"))
    d.point((9, 1), fill=rgba("#e9c6a8"))
    # Tiny moth freckles.
    for x, y in [(5, 10), (10, 10), (3, 13), (12, 13)]:
        d.point((x, y), fill=rgba("#d99bb3"))
    return img


def petalwing_wing_tile(w: int, h: int, mirrored: bool = False, lower: bool = False) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    # Root is at the right for the left wing and at the left for the right wing.
    if not mirrored:
        pts = [(w - 1, h // 2), (w - 5, 2), (w - 13, 1), (3, 3), (1, h // 2 - 1), (2, h - 3), (w // 2, h - 4), (w - 5, h - 2)]
        root_x = w - 1
    else:
        pts = [(0, h // 2), (4, 2), (12, 1), (w - 3, 3), (w - 2, h // 2 - 1), (w - 3, h - 3), (w // 2, h - 4), (5, h - 2)]
        root_x = 0
    # Rounded, scalloped wing silhouette.
    d.polygon(pts, fill=rgba("#d2649d"))
    # Gradient washes from the root to the tip.
    for y in range(h):
        for x in range(w):
            if img.getpixel((x, y))[3] == 0:
                continue
            dist = abs(x - root_x) / max(1, w - 1)
            if dist < 0.35:
                col = mix("#b44f8e", "#e98fbc", dist / 0.35)
            elif dist < 0.72:
                col = mix("#e98fbc", "#ffc6d8", (dist - 0.35) / 0.37)
            else:
                col = mix("#ffc6d8", "#fff0dc", (dist - 0.72) / 0.28)
            if lower:
                col = shade(col, -0.08)
            img.putpixel((x, y), col)
    # Leading edge highlight and dark trailing edge.
    d.line(pts[:4] + [pts[-1]], fill=rgba("#7c3c74"), width=1)
    d.line([(pts[4][0], pts[4][1]), (pts[5][0], pts[5][1]), (pts[6][0], pts[6][1])], fill=rgba("#5f2d5f"))
    # Veins radiating out from the root.
    for i in range(5):
        tx = 3 + i * (w - 6) // 4
        ty = 3 + (i % 2) * (h - 7)
        d.line([(root_x, h // 2), (tx, ty)], fill=rgba("#b24f87", 210))
        d.line([(root_x, h // 2 + 1), (tx, ty + 1)], fill=rgba("#f4b8cf", 160))
    # Eyespot near the outer third.
    ex = w // 3 if not mirrored else w - w // 3
    ey = h // 2
    d.ellipse((ex - 4, ey - 3, ex + 4, ey + 3), fill=rgba("#f9e6c8"))
    d.ellipse((ex - 3, ey - 2, ex + 3, ey + 2), fill=rgba("#423469"))
    d.ellipse((ex - 1, ey - 1, ex + 1, ey + 1), fill=rgba("#8fdcff"))
    d.point((ex - 2, ey - 1), fill=rgba("#ffffff"))
    # Gold dust and tiny pearls.
    for i in range(7):
        x = 4 + hrand(i, w, 421) % max(1, w - 8)
        y = 2 + hrand(i, h, 422) % max(1, h - 4)
        if img.getpixel((x, y))[3]:
            d.point((x, y), fill=rgba("#ffe08a" if i % 2 else "#fff5c8"))
    d.point((pts[2][0], pts[2][1] + 1), fill=rgba("#ffffff"))
    return img


def petalwing_antenna_tile(w: int = 8, h: int = 8) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    for y in range(h):
        x = w // 2 + (1 if y < 2 else 0)
        d.point((x, y), fill=rgba("#4a2f55"))
        d.point((x + 1, y), fill=rgba("#6e4a76" if y % 2 else "#3b2647"))
    d.ellipse((2, 0, 5, 2), fill=rgba("#ffe08a"))
    d.point((3, 0), fill=rgba("#ffffff"))
    d.point((4, 1), fill=rgba("#8ffbe1"))
    return img


def petalwing_leg_tile(w: int = 8, h: int = 8) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.point((3, y), fill=rgba("#3b2647"))
        d.point((4, y), fill=rgba("#68436e" if y % 2 else "#2d1e35"))
    d.point((2, h - 1), fill=rgba("#3b2647"))
    d.point((5, h - 1), fill=rgba("#3b2647"))
    d.point((3, h - 2), fill=rgba("#f2c8de"))
    return img


def petalwing_edge_tile(w: int = 8, h: int = 8) -> Image.Image:
    return paint_noise(w, h, ["#5f2d5f", "#7c3c74", "#a34f8a", "#c76a9f"], 431)


# ---------------------------------------------------------------------------
# Mossling textures
# ---------------------------------------------------------------------------


def _moss_base(d: ImageDraw.ImageDraw, w: int, h: int, seed: int, top_bias: bool = False) -> None:
    palette = ["#3f6b35", "#4f7f42", "#5f8f4a", "#70a357", "#82b565", "#96c77a"]
    noise_rect(d, (0, 0, w - 1, h - 1), palette, seed)
    for y in range(h):
        for x in range(w):
            if hrand(x, y, seed + 1) % 7 == 0:
                # Little mossy lobes.
                d.point((x, y), fill=rgba(palette[5] if y < h // 2 else palette[0]))
            if hrand(x, y, seed + 2) % 23 == 0:
                d.point((x, y), fill=rgba("#b8d98a"))
    # A few tiny mushrooms and flowers.
    for i in range(max(1, w * h // 180)):
        x = 2 + hrand(i, seed, 441) % max(1, w - 5)
        y = 2 + hrand(i, seed + 1, 442) % max(1, h - 5)
        if hrand(i, seed + 2, 443) % 2:
            d.rectangle((x, y, x + 1, y), fill=rgba("#c95c5c"))
            d.point((x, y + 1), fill=rgba("#f1e3c2"))
            d.point((x + 1, y + 1), fill=rgba("#d3c09b"))
        else:
            d.point((x, y), fill=rgba("#ff9fc4"))
            d.point((x + 1, y), fill=rgba("#ffd0e1"))
            d.point((x, y + 1), fill=rgba("#e58ab0"))
    if top_bias:
        for y in range(h // 3):
            for x in range(w):
                if hrand(x, y, seed + 3) % 4 == 0:
                    d.point((x, y), fill=rgba("#a8d283"))


def mossling_body_tile(w: int = 32, h: int = 32) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    _moss_base(d, w, h, 451, True)
    # Vine down the centre.
    for y in range(2, h - 2):
        x = w // 2 + round(math.sin(y * 0.5) * 2)
        d.point((x, y), fill=rgba("#2f5b2c"))
        if y % 4 == 0:
            d.point((x - 1, y), fill=rgba("#7db85f"))
            d.point((x + 1, y - 1), fill=rgba("#5d9448"))
    # Soft belly shadow.
    for y in range(h - 7, h):
        for x in range(3, w - 3):
            if hrand(x, y, 452) % 3:
                d.point((x, y), fill=rgba("#2f5229", 150))
    # A couple of pink blossoms.
    for x, y in [(6, 22), (23, 9), (9, 7)]:
        d.point((x, y), fill=rgba("#ff9fc4"))
        d.point((x + 1, y), fill=rgba("#ffd0e1"))
        d.point((x, y + 1), fill=rgba("#e58ab0"))
        d.point((x + 1, y + 1), fill=rgba("#c76a9f"))
    return img


def mossling_belly_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 0, w - 1, h - 1), ["#c8d9a4", "#d7e5b6", "#e6efc8", "#f1f5d8", "#b6c98f"], 461)
    for y in range(0, h, 3):
        for x in range(w):
            if hrand(x, y, 462) % 2:
                d.point((x, y), fill=rgba("#a8bd7f", 190))
    for i in range(4):
        x, y = hrand(i, 1, 463) % w, hrand(i, 2, 464) % h
        d.point((x, y), fill=rgba("#8ea86a"))
    return img


def mossling_head_tile(w: int = 32, h: int = 32) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    _moss_base(d, w, h, 471, True)
    # Larger leafy tufts around the crown.
    for i in range(7):
        x = 3 + hrand(i, 2, 472) % (w - 6)
        y = 1 + hrand(i, 3, 473) % 6
        d.ellipse((x - 2, y - 1, x + 2, y + 2), fill=rgba("#6aa34f"))
        d.point((x, y - 2), fill=rgba("#a8d283"))
        d.point((x - 1, y), fill=rgba("#4f7f42"))
    return img


def mossling_face_tile(w: int = 32, h: int = 32) -> Image.Image:
    img = mossling_head_tile(w, h)
    d = ImageDraw.Draw(img)
    # Cream muzzle and cheeks.
    d.ellipse((9, 19, 23, 29), fill=rgba("#e9e2bd"))
    d.ellipse((6, 21, 12, 27), fill=rgba("#f1ebca"))
    d.ellipse((20, 21, 26, 27), fill=rgba("#f1ebca"))
    # Big dark eyes with mossy upper lids.
    for x0, x1 in [(5, 12), (20, 27)]:
        d.ellipse((x0, 8, x1, 18), fill=rgba("#1f2b1a"))
        d.ellipse((x0 + 1, 9, x1 - 1, 17), fill=rgba("#3f5a2c"))
        d.ellipse((x0 + 2, 10, x0 + 5, 14), fill=rgba("#f4fff0"))
        d.point((x0 + 3, 11), fill=rgba("#ffffff"))
        d.point((x1 - 2, 15), fill=rgba("#89b86a"))
        d.line([(x0, 8), (x1, 8)], fill=rgba("#2f4b24"))
        # Leafy eyebrow.
        d.line([(x0 - 1, 6), (x0 + 2, 5), (x1, 6)], fill=rgba("#4f7f42"))
        d.point((x0 + 2, 5), fill=rgba("#96c77a"))
    # Nose and smile.
    d.ellipse((14, 20, 18, 23), fill=rgba("#6f4b36"))
    d.point((15, 20), fill=rgba("#a57a5a"))
    d.line([(13, 25), (15, 27), (17, 27), (19, 25)], fill=rgba("#6f4b36"))
    # Blush and freckles.
    d.ellipse((4, 23, 8, 26), fill=rgba("#e89aad", 180))
    d.ellipse((24, 23, 28, 26), fill=rgba("#e89aad", 180))
    for x, y in [(10, 24), (21, 24), (9, 27), (22, 27), (13, 21), (18, 21)]:
        d.point((x, y), fill=rgba("#c7a77f"))
    # Moss tufts on the cheeks.
    for x, y in [(2, 15), (3, 16), (28, 14), (29, 15), (1, 20), (30, 21)]:
        d.point((x, y), fill=rgba("#6aa34f"))
    return img


def mossling_ear_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    pts = [(2, 13), (3, 6), (6, 2), (9, 1), (13, 3), (14, 8), (12, 13), (8, 15)]
    d.polygon(pts, fill=rgba("#5f8f4a"))
    d.line(pts + [pts[0]], fill=rgba("#2f5b2c"))
    d.line([(3, 13), (7, 4), (12, 3)], fill=rgba("#96c77a"))
    for i in range(4):
        d.line([(7, 13), (5 + i * 2, 5)], fill=rgba("#3f6b35"))
    d.point((5, 4), fill=rgba("#c8e6a2"))
    d.point((9, 2), fill=rgba("#dff3bd"))
    return img


def mossling_arm_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    noise_rect(d, (2, 0, 13, 9), ["#4f7f42", "#5f8f4a", "#70a357", "#82b565"], 481)
    # Cream paw at the bottom.
    d.ellipse((3, 9, 12, 15), fill=rgba("#e9e2bd"))
    d.ellipse((4, 10, 7, 14), fill=rgba("#f7f2d8"))
    d.point((5, 12), fill=rgba("#bda77f"))
    d.point((9, 12), fill=rgba("#bda77f"))
    d.line([(4, 10), (7, 9), (11, 10)], fill=rgba("#96c77a"))
    # Tiny leaf on the shoulder.
    d.point((11, 2), fill=rgba("#a8d283"))
    d.point((12, 3), fill=rgba("#6aa34f"))
    return img


def mossling_leg_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    noise_rect(d, (3, 0, 12, 10), ["#4f7f42", "#5f8f4a", "#70a357", "#82b565"], 491)
    # Darker foot with three little toes.
    d.rectangle((3, 10, 12, 14), fill=rgba("#3f5a2c"))
    d.rectangle((4, 11, 11, 13), fill=rgba("#5a7a3e"))
    for x in (4, 7, 10):
        d.point((x, 14), fill=rgba("#2f4b24"))
        d.point((x, 13), fill=rgba("#8ea86a"))
    d.point((5, 2), fill=rgba("#a8d283"))
    return img


def mossling_flower_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    # Five petals in a ring.
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        cx = round(8 + math.cos(angle) * 4)
        cy = round(8 + math.sin(angle) * 4)
        d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=rgba(PETAL_PINK[3]))
        d.point((cx, cy - 1), fill=rgba(PETAL_PINK[5]))
        d.point((cx + 1, cy + 1), fill=rgba(PETAL_PINK[2]))
    d.ellipse((6, 6, 10, 10), fill=rgba(PETAL_GOLD[4]))
    d.ellipse((7, 7, 9, 9), fill=rgba(PETAL_GOLD[5]))
    d.point((7, 7), fill=rgba("#ffffff"))
    return img


def mossling_tail_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    pts = [(2, 1), (9, 2), (14, 6), (12, 12), (6, 15), (1, 11), (3, 6)]
    d.polygon(pts, fill=rgba("#6aa34f"))
    d.line(pts + [pts[0]], fill=rgba("#2f5b2c"))
    d.line([(3, 12), (8, 8), (13, 4)], fill=rgba("#a8d283"))
    for i in range(4):
        d.line([(3, 11), (9 - i, 5 + i)], fill=rgba("#3f6b35"))
    d.point((8, 7), fill=rgba("#dff3bd"))
    return img


def mossling_mushroom_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    # Stem.
    d.rectangle((6, 8, 9, 14), fill=rgba("#efe4c6"))
    d.point((6, 9), fill=rgba("#d4c5a3"))
    d.point((9, 14), fill=rgba("#c2b18d"))
    # Red cap with cream spots.
    d.ellipse((1, 2, 14, 10), fill=rgba("#c95c5c"))
    d.ellipse((2, 3, 13, 9), fill=rgba("#e07070"))
    for x, y in [(4, 5), (8, 4), (11, 6), (6, 7), (2, 7), (12, 8)]:
        d.ellipse((x, y, x + 1, y + 1), fill=rgba("#f7e8c8"))
    d.line([(2, 9), (13, 9)], fill=rgba("#8f3d3d"))
    d.point((4, 3), fill=rgba("#ffb0b0"))
    return img


# ---------------------------------------------------------------------------
# Dewdrop Snail textures
# ---------------------------------------------------------------------------


def snail_foot_tile(w: int = 32, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    noise_rect(d, (0, 1, w - 1, h - 2), ["#4f9a8f", "#5fae9f", "#6fc2b0", "#83d4c1", "#98e3d0"], 501)
    # Slime highlights and ripples.
    for x in range(w):
        if hrand(x, 0, 502) % 3:
            d.point((x, h - 1), fill=rgba("#3f7d78"))
            d.point((x, h - 2), fill=rgba("#c8f5e8"))
    for i in range(7):
        y = 3 + i
        for x in range(w):
            if hrand(x, y, 503) % 5 == 0:
                d.point((x, y), fill=rgba("#b9f0df", 190))
    for x, y in [(4, 5), (12, 9), (20, 5), (27, 10)]:
        d.point((x, y), fill=rgba("#effff8"))
    # A couple of pink petal flecks picked up from the meadow.
    for x, y in [(8, 7), (24, 4), (17, 12)]:
        d.point((x, y), fill=rgba(PETAL_PINK[4]))
    return img


def snail_body_tile(w: int = 16, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    noise_rect(d, (1, 0, 14, 15), ["#3f7d78", "#4f9a8f", "#5fae9f", "#6fc2b0", "#83d4c1"], 511)
    # Lighter belly and darker back.
    for y in range(h):
        for x in range(w):
            if y > 9 and hrand(x, y, 512) % 3:
                d.point((x, y), fill=rgba("#a8e6d4"))
            if y < 3 and hrand(x, y, 513) % 3:
                d.point((x, y), fill=rgba("#2f5f5a"))
    # Spots and speckles.
    for i in range(9):
        x, y = 2 + hrand(i, 1, 514) % (w - 4), 2 + hrand(i, 2, 515) % (h - 4)
        d.point((x, y), fill=rgba("#2f5f5a" if i % 2 else "#b9fbef"))
    d.point((7, 4), fill=rgba("#e4fff9"))
    return img


def snail_shell_tile(w: int = 32, h: int = 32) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    # Warm cream base with teal shadows.
    noise_rect(d, (0, 0, w - 1, h - 1), ["#c9b98f", "#d8c9a2", "#e7dbb8", "#f2e8cb", "#a89a76"], 521)
    # Spiral rings, shifting toward the upper-left.
    cx, cy = w // 2, h // 2
    for i, (radius, color) in enumerate([(13, "#3f7d78"), (11, "#5fae9f"), (9, "#83d4c1"), (7, "#b9f0df"), (5, "#e4fff9"), (3, "#5fae9f")]):
        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=rgba(color), width=2)
    # Spiral seam and radial ridges.
    for i in range(10):
        angle = math.radians(i * 36 + 10)
        x = round(cx + math.cos(angle) * 14)
        y = round(cy + math.sin(angle) * 14)
        d.line([(cx, cy), (x, y)], fill=rgba("#7a6a4d", 170))
    # Pink flower motif in the centre.
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        x = round(cx + math.cos(angle) * 4)
        y = round(cy + math.sin(angle) * 4)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=rgba(PETAL_PINK[3]))
        d.point((x, y - 1), fill=rgba(PETAL_PINK[5]))
    d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=rgba(PETAL_GOLD[4]))
    # Highlight and deep rim shadow.
    d.arc((2, 2, w - 3, h - 3), 200, 320, fill=rgba("#fff8dc", 220), width=2)
    d.arc((1, 1, w - 2, h - 2), 20, 160, fill=rgba("#5c513a", 190), width=2)
    for i in range(12):
        x, y = hrand(i, 3, 522) % w, hrand(i, 4, 523) % h
        d.point((x, y), fill=rgba("#fff3c8" if i % 2 else "#6fa89c", 200))
    return img


def snail_stalk_tile(w: int = 8, h: int = 16) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.point((3, y), fill=rgba("#3f7d78"))
        d.point((4, y), fill=rgba("#6fc2b0"))
        d.point((5, y), fill=rgba("#98e3d0" if y % 3 else "#4f9a8f"))
    for y in range(2, h, 4):
        d.point((3, y), fill=rgba("#2f5f5a"))
        d.point((5, y + 1), fill=rgba("#c8f5e8"))
    return img


def snail_eye_tile(w: int = 8, h: int = 8) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse((1, 1, 6, 6), fill=rgba("#f7e8c8"))
    d.ellipse((2, 2, 5, 5), fill=rgba("#2f3b2a"))
    d.ellipse((2, 2, 3, 3), fill=rgba("#ffffff"))
    d.point((4, 4), fill=rgba("#8ffbe1"))
    d.arc((0, 0, 7, 7), 180, 300, fill=rgba("#c9a84f"))
    return img


def snail_dew_tile(w: int = 8, h: int = 8) -> Image.Image:
    img = new_tex(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse((2, 1, 5, 6), fill=rgba("#8ffbe1"))
    d.ellipse((3, 2, 4, 4), fill=rgba("#e4fff9"))
    d.point((3, 2), fill=rgba("#ffffff"))
    d.point((2, 5), fill=rgba("#59d6bb"))
    return img


def snail_leaf_tile(w: int = 16, h: int = 16) -> Image.Image:
    return mossling_ear_tile(w, h)


def snail_edge_tile(w: int = 8, h: int = 8) -> Image.Image:
    return paint_noise(w, h, ["#3f7d78", "#4f9a8f", "#5fae9f", "#83d4c1"], 531)


# ---------------------------------------------------------------------------
# Entity models
# ---------------------------------------------------------------------------


def petalwing_model() -> tuple[dict, dict, dict]:
    atlas = Atlas()
    t: dict[str, tuple[int, int, int, int]] = {}
    t["wing_upper_left"] = atlas.add("wing_upper_left", 32, 16, lambda w, h: petalwing_wing_tile(w, h, False, False))
    t["wing_upper_right"] = atlas.add("wing_upper_right", 32, 16, lambda w, h: petalwing_wing_tile(w, h, True, False))
    t["wing_lower_left"] = atlas.add("wing_lower_left", 24, 16, lambda w, h: petalwing_wing_tile(w, h, False, True))
    t["wing_lower_right"] = atlas.add("wing_lower_right", 24, 16, lambda w, h: petalwing_wing_tile(w, h, True, True))
    t["body"] = atlas.add("body", 16, 16, petalwing_body_tile)
    t["head"] = atlas.add("head", 16, 16, petalwing_head_tile)
    t["face"] = atlas.add("face", 16, 16, petalwing_face_tile)
    t["antenna"] = atlas.add("antenna", 8, 8, petalwing_antenna_tile)
    t["leg"] = atlas.add("leg", 8, 8, petalwing_leg_tile)
    t["edge"] = atlas.add("edge", 8, 8, petalwing_edge_tile)

    b = t["body"]
    hd = t["head"]
    fc = t["face"]
    an = t["antenna"]
    lg = t["leg"]
    ed = t["edge"]
    wul, wur = t["wing_upper_left"], t["wing_upper_right"]
    wll, wlr = t["wing_lower_left"], t["wing_lower_right"]

    bones = [
        bone("root", [0, 0, 0], []),
        bone(
            "body", [0, 8, 0],
            [
                cube([-2, 6.5, -5], [4, 3.5, 9], uv(b)),
                # A soft collar.
                cube([-2.4, 8.6, -4.5], [4.8, 1.4, 3], uv(b)),
            ],
            parent="root",
        ),
        bone(
            "head", [0, 9, -5],
            [
                cube([-2.5, 8, -8], [5, 4, 4], uv_faces(hd, north=fc, south=hd, up=hd, down=hd, east=hd, west=hd)),
                cube([-1.8, 8.4, -8.4], [3.6, 2.4, 0.7], uv(fc)),
            ],
            parent="body",
        ),
        bone("antenna_left", [1.5, 11.5, -7.5], [cube([1.2, 11.5, -7.8], [0.8, 5, 0.8], uv(an), rotation=[-12, 0, 18], pivot=[1.2, 11.5, -7.8])], parent="head"),
        bone("antenna_right", [-1.5, 11.5, -7.5], [cube([-2, 11.5, -7.8], [0.8, 5, 0.8], uv(an), rotation=[-12, 0, -18], pivot=[-2, 11.5, -7.8])], parent="head"),
        bone(
            "wing_upper_left", [0, 9, -2],
            [cube([-13, 8.7, -5], [12, 0.8, 8], uv_faces(wul, up=wul, down=wul, north=ed, south=ed, east=ed, west=ed))],
            parent="body",
        ),
        bone(
            "wing_upper_right", [0, 9, -2],
            [cube([1, 8.7, -5], [12, 0.8, 8], uv_faces(wur, up=wur, down=wur, north=ed, south=ed, east=ed, west=ed))],
            parent="body",
        ),
        bone(
            "wing_lower_left", [0, 8, -1],
            [cube([-10, 7.4, 0], [9, 0.7, 6], uv_faces(wll, up=wll, down=wll, north=ed, south=ed, east=ed, west=ed))],
            parent="body",
        ),
        bone(
            "wing_lower_right", [0, 8, -1],
            [cube([1, 7.4, 0], [9, 0.7, 6], uv_faces(wlr, up=wlr, down=wlr, north=ed, south=ed, east=ed, west=ed))],
            parent="body",
        ),
    ]
    for i, (x, z) in enumerate([(-1.5, -3), (1.5, -3), (-1.5, 0.5), (1.5, 0.5), (-1.2, 3), (1.2, 3)]):
        bones.append(
            bone(
                f"leg_{i}", [x, 6.5, z],
                [cube([x - 0.4, 4.5, z - 0.4], [0.8, 2.2, 0.8], uv(lg), rotation=[-12 if i % 2 else 12, 0, 0], pivot=[x, 6.5, z])],
            )
        )
    geo = entity_geometry("geometry.bl.petalwing", 128, 128, bones, 3.2, 2.0, [0, 0.8, 0])
    return geo, atlas.image, t


def mossling_model() -> tuple[dict, dict, dict]:
    atlas = Atlas()
    t: dict[str, tuple[int, int, int, int]] = {}
    t["body"] = atlas.add("body", 32, 32, mossling_body_tile)
    t["head"] = atlas.add("head", 32, 32, mossling_head_tile)
    t["face"] = atlas.add("face", 32, 32, mossling_face_tile)
    t["belly"] = atlas.add("belly", 16, 16, mossling_belly_tile)
    t["ear"] = atlas.add("ear", 16, 16, mossling_ear_tile)
    t["arm"] = atlas.add("arm", 16, 16, mossling_arm_tile)
    t["leg"] = atlas.add("leg", 16, 16, mossling_leg_tile)
    t["flower"] = atlas.add("flower", 16, 16, mossling_flower_tile)
    t["tail"] = atlas.add("tail", 16, 16, mossling_tail_tile)
    t["mushroom"] = atlas.add("mushroom", 16, 16, mossling_mushroom_tile)
    t["edge"] = atlas.add("edge", 8, 8, lambda w, h: paint_noise(w, h, ["#2f5b2c", "#3f6b35", "#4f7f42"], 471))
    b, hd, fc = t["body"], t["head"], t["face"]
    be, ea, ar, lg = t["belly"], t["ear"], t["arm"], t["leg"]
    fl, ta, mu, ed = t["flower"], t["tail"], t["mushroom"], t["edge"]

    petals = []
    for i in range(5):
        petals.append(
            cube([1.8, 18, -1], [3, 0.7, 2], uv_faces(fl, up=fl, down=fl, north=fl, south=fl, east=fl, west=fl), rotation=[0, i * 72, 0], pivot=[0, 18.4, 0])
        )
    bones = [
        bone("root", [0, 0, 0], []),
        bone(
            "body", [0, 7, 0],
            [
                cube([-4.2, 3.2, -3.2], [8.4, 8, 6.4], uv(b)),
                cube([-3.4, 3.8, -3.45], [6.8, 5.4, 0.5], uv_faces(be, north=be, south=b, up=b, down=b, east=b, west=b)),
            ],
            parent="root",
        ),
        bone(
            "head", [0, 11, 0],
            [
                cube([-4, 10, -4], [8, 7, 7], uv_faces(hd, north=fc, south=hd, up=hd, down=hd, east=hd, west=hd)),
                cube([-3.4, 10.4, -4.32], [6.8, 3.2, 0.5], uv(fc)),
            ],
            parent="body",
        ),
        bone("ear_left", [-3, 16, 0], [cube([-6, 15.8, -2], [3, 0.9, 5], uv(ea), rotation=[0, 0, 18], pivot=[-3, 16.2, 0])], parent="head"),
        bone("ear_right", [3, 16, 0], [cube([3, 15.8, -2], [3, 0.9, 5], uv(ea), rotation=[0, 0, -18], pivot=[3, 16.2, 0])], parent="head"),
        bone(
            "flower", [0, 17, 0],
            [
                cube([-0.4, 17, -0.4], [0.8, 2.4, 0.8], uv(ed)),
                *petals,
                cube([-1.2, 18.2, -1.2], [2.4, 1.8, 2.4], uv(fl)),
            ],
            parent="head",
        ),
        bone("arm_left", [-4.5, 9.5, 0], [cube([-6.5, 4.8, -1.1], [2, 6, 2.2], uv(ar), rotation=[0, 0, 8], pivot=[-4.5, 9.5, 0])], parent="body"),
        bone("arm_right", [4.5, 9.5, 0], [cube([4.5, 4.8, -1.1], [2, 6, 2.2], uv(ar), rotation=[0, 0, -8], pivot=[4.5, 9.5, 0])], parent="body"),
        bone("leg_left", [-2.5, 4, 0], [cube([-4.5, 0, -2], [3, 4.2, 4], uv(lg))], parent="body"),
        bone("leg_right", [2.5, 4, 0], [cube([1.5, 0, -2], [3, 4.2, 4], uv(lg))], parent="body"),
        bone("tail", [0, 7, 3], [cube([-1.5, 6, 3], [3, 1, 5], uv(ta), rotation=[0, -18, 0], pivot=[0, 6.5, 3])], parent="body"),
        bone(
            "mushroom", [2, 10, 2],
            [
                cube([1.4, 10, 1.4], [1.4, 2.4, 1.4], uv(mu)),
                cube([0.2, 12.2, 0.2], [3.8, 1.4, 3.8], uv(mu)),
            ],
            parent="body",
        ),
    ]
    geo = entity_geometry("geometry.bl.mossling", 128, 128, bones, 1.8, 1.8, [0, 0.8, 0])
    return geo, atlas.image, t


def dewdrop_snail_model() -> tuple[dict, dict, dict]:
    atlas = Atlas()
    t: dict[str, tuple[int, int, int, int]] = {}
    t["foot"] = atlas.add("foot", 32, 16, snail_foot_tile)
    t["body"] = atlas.add("body", 16, 16, snail_body_tile)
    t["shell"] = atlas.add("shell", 32, 32, snail_shell_tile)
    t["stalk"] = atlas.add("stalk", 8, 16, snail_stalk_tile)
    t["eye"] = atlas.add("eye", 8, 8, snail_eye_tile)
    t["flower"] = atlas.add("flower", 16, 16, mossling_flower_tile)
    t["dew"] = atlas.add("dew", 8, 8, snail_dew_tile)
    t["leaf"] = atlas.add("leaf", 16, 16, snail_leaf_tile)
    t["edge"] = atlas.add("edge", 8, 8, snail_edge_tile)
    ft, bd, sh = t["foot"], t["body"], t["shell"]
    st, ey, fl = t["stalk"], t["eye"], t["flower"]
    dw, lf, ed = t["dew"], t["leaf"], t["edge"]

    shell_cubes = [
        cube([-5, 6, -4], [10, 3, 9], uv_faces(sh, up=sh, down=ed, north=sh, south=sh, east=sh, west=sh)),
        cube([-4, 8.5, -3], [8, 3, 7], uv_faces(sh, up=sh, down=sh, north=sh, south=sh, east=sh, west=sh), rotation=[0, 8, 0], pivot=[0, 10, 1]),
        cube([-3, 11, -2], [6, 3, 5], uv_faces(sh, up=sh, down=sh, north=sh, south=sh, east=sh, west=sh), rotation=[0, -12, 0], pivot=[0, 12.5, 1]),
        cube([-2, 13.5, -1], [4, 3, 3], uv_faces(sh, up=sh, down=sh, north=sh, south=sh, east=sh, west=sh), rotation=[0, 15, 0], pivot=[0, 15, 1]),
        cube([-1, 16, 0], [2, 2, 2], uv(sh)),
    ]
    petals = []
    for i in range(5):
        petals.append(
            cube([2.2, 19, -0.8], [2.8, 0.6, 1.8], uv_faces(fl, up=fl, down=fl, north=fl, south=fl, east=fl, west=fl), rotation=[0, i * 72, 0], pivot=[0, 19.3, 1])
        )
    bones = [
        bone("root", [0, 0, 0], []),
        bone(
            "foot", [0, 0, 0],
            [
                cube([-5, 0, -7], [10, 2.4, 14], uv_faces(ft, up=ft, down=ed, north=ft, south=ft, east=ft, west=ft)),
                cube([-4.5, 2.2, -6.4], [9, 1.2, 12], uv(ft)),
            ],
            parent="root",
        ),
        bone(
            "body", [0, 3, -5],
            [
                cube([-2, 2, -7], [4, 6, 4], uv(bd)),
                cube([-2.2, 2.4, -6.8], [4.4, 3, 0.5], uv(bd)),
            ],
            parent="root",
        ),
        bone(
            "head", [0, 8, -7],
            [
                cube([-2.5, 8, -9], [5, 4, 4], uv(bd)),
                cube([-2, 8.4, -9.25], [4, 2, 0.5], uv(bd)),
            ],
            parent="body",
        ),
        bone(
            "shell", [0, 8, 1],
            shell_cubes,
            parent="root",
        ),
        bone(
            "flower", [0, 18, 1],
            [
                cube([-0.4, 18, 0.6], [0.8, 2.2, 0.8], uv(lf)),
                *petals,
                cube([-1, 19.2, 0.2], [2, 1.6, 2], uv(fl)),
            ],
            parent="shell",
        ),
        bone("dew", [0, 8, 4], [cube([3, 8.2, 3.2], [1.2, 1.8, 1.2], uv(dw))], parent="shell"),
        bone("leaf", [0, 2, 5], [cube([-2, 1.2, 4.8], [4, 0.6, 6], uv(lf), rotation=[0, 28, 0], pivot=[0, 1.5, 5])], parent="root"),
    ]
    for side, sx in [("left", 1), ("right", -1)]:
        bones.append(
            bone(
                f"eye_stalk_{side}", [sx * 1.4, 12, -8],
                [
                    cube([sx * 1.2 - 0.4, 12, -8.4], [0.8, 6, 0.8], uv(st), rotation=[-8, 0, sx * 10], pivot=[sx * 1.2, 12, -8]),
                    cube([sx * 1.6 - 0.9, 17.6, -9], [1.8, 1.8, 1.8], uv(ey)),
                ],
                parent="head",
            )
        )
    geo = entity_geometry("geometry.bl.dewdrop_snail", 128, 128, bones, 1.8, 1.8, [0, 0.7, 0])
    return geo, atlas.image, t


# ---------------------------------------------------------------------------
# Entity roster and animations
# ---------------------------------------------------------------------------


@dataclass
class EntitySpec:
    key: str
    label: str
    identifier: str
    geometry_id: str
    geometry: dict
    texture: Image.Image
    atlas_tiles: dict[str, tuple[int, int, int, int]]
    animations: dict
    controller: str
    controller_json: dict
    animate: list[str]
    egg_base: str
    egg_overlay: str
    width: float
    height: float
    health: int
    movement: float
    family: str = "bloomling"
    flying: bool = False
    ambient_sound: str = ""
    spawn_weight: int = 10
    spawn_group_min: int = 1
    spawn_group_max: int = 2
    biomes: tuple[str, ...] = ("bl:bloomlands",)


def _animations_petalwing() -> tuple[dict, dict, list[str]]:
    anim = {
        "format_version": "1.10.0",
        "animations": {
            "animation.bl.petalwing.fly": {
                "loop": True,
                "animation_length": 0.5,
                "bones": {
                    "wing_upper_left": {"rotation": [0, 0, "math.sin(query.anim_time * 720) * 38 - 6"]},
                    "wing_upper_right": {"rotation": [0, 0, "math.sin(query.anim_time * 720 + 180) * 38 + 6"]},
                    "wing_lower_left": {"rotation": [0, 0, "math.sin(query.anim_time * 720 + 30) * 26 - 4"]},
                    "wing_lower_right": {"rotation": [0, 0, "math.sin(query.anim_time * 720 + 210) * 26 + 4"]},
                    "body": {"position": [0, "math.sin(query.anim_time * 720) * 0.35", 0], "rotation": [0, "math.sin(query.anim_time * 720) * 3", 0]},
                },
            },
            "animation.bl.petalwing.idle": {
                "loop": True,
                "animation_length": 3.0,
                "bones": {
                    "antenna_left": {"rotation": [0, "math.sin(query.anim_time * 60) * 8", "math.sin(query.anim_time * 45) * 5"]},
                    "antenna_right": {"rotation": [0, "math.sin(query.anim_time * 60 + 180) * 8", "math.sin(query.anim_time * 45 + 180) * 5"]},
                    "head": {"rotation": ["math.sin(query.anim_time * 35) * 2", "math.sin(query.anim_time * 25) * 6", 0]},
                },
            },
        },
    }
    return anim, {}, ["fly", "idle"]


def _animations_mossling() -> tuple[dict, dict, str]:
    anim = {
        "format_version": "1.10.0",
        "animations": {
            "animation.bl.mossling.walk": {
                "loop": True,
                "animation_length": 1.0,
                "bones": {
                    "leg_left": {"rotation": ["math.sin(query.anim_time * 360) * 32", 0, 0]},
                    "leg_right": {"rotation": ["math.sin(query.anim_time * 360 + 180) * 32", 0, 0]},
                    "arm_left": {"rotation": ["math.sin(query.anim_time * 360 + 180) * 26", 0, 0]},
                    "arm_right": {"rotation": ["math.sin(query.anim_time * 360) * 26", 0, 0]},
                    "body": {"position": [0, "math.abs(math.sin(query.anim_time * 360)) * 0.45", 0], "rotation": [0, "math.sin(query.anim_time * 360) * 3", 0]},
                    "head": {"rotation": ["math.sin(query.anim_time * 360) * 2", 0, "math.sin(query.anim_time * 360) * 2"]},
                    "tail": {"rotation": [0, "math.sin(query.anim_time * 360) * 12", 0]},
                    "flower": {"rotation": [0, 0, "math.sin(query.anim_time * 360) * 8"]},
                    "ear_left": {"rotation": [0, 0, "18 + math.sin(query.anim_time * 360) * 6"]},
                    "ear_right": {"rotation": [0, 0, "-18 - math.sin(query.anim_time * 360) * 6"]},
                },
            },
            "animation.bl.mossling.idle": {
                "loop": True,
                "animation_length": 4.0,
                "bones": {
                    "body": {"position": [0, "math.sin(query.anim_time * 70) * 0.18", 0]},
                    "head": {"rotation": ["math.sin(query.anim_time * 45) * 2", "math.sin(query.anim_time * 25) * 7", 0]},
                    "ear_left": {"rotation": [0, 0, "18 + math.sin(query.anim_time * 80) * 4"]},
                    "ear_right": {"rotation": [0, 0, "-18 - math.sin(query.anim_time * 80 + 80) * 4"]},
                    "flower": {"rotation": [0, "math.sin(query.anim_time * 60) * 10", "math.sin(query.anim_time * 55) * 5"]},
                    "tail": {"rotation": [0, "math.sin(query.anim_time * 50) * 8", 0]},
                },
            },
        },
    }
    controller = {
        "format_version": "1.10.0",
        "animation_controllers": {
            "controller.animation.bl.mossling": {
                "initial_state": "idle",
                "states": {
                    "idle": {"animations": ["idle"], "transitions": [{"walk": "query.modified_move_speed > 0.05"}], "blend_transition": 0.2},
                    "walk": {"animations": ["walk"], "transitions": [{"idle": "query.modified_move_speed <= 0.05"}], "blend_transition": 0.2},
                },
            }
        },
    }
    return anim, controller, "controller.animation.bl.mossling"


def _animations_snail() -> tuple[dict, dict, str]:
    anim = {
        "format_version": "1.10.0",
        "animations": {
            "animation.bl.dewdrop_snail.crawl": {
                "loop": True,
                "animation_length": 2.0,
                "bones": {
                    "foot": {"scale": [1, "1 + math.sin(query.anim_time * 180) * 0.04", 1], "position": [0, "math.sin(query.anim_time * 180) * 0.1", 0]},
                    "body": {"rotation": ["math.sin(query.anim_time * 180) * 3", 0, "math.sin(query.anim_time * 180 + 90) * 2"]},
                    "shell": {"position": [0, "math.sin(query.anim_time * 180 + 45) * 0.12", 0], "rotation": [0, "math.sin(query.anim_time * 180) * 1.5", 0]},
                    "eye_stalk_left": {"rotation": ["-8 + math.sin(query.anim_time * 90) * 6", 0, "10 + math.sin(query.anim_time * 70) * 5"]},
                    "eye_stalk_right": {"rotation": ["-8 + math.sin(query.anim_time * 90 + 60) * 6", 0, "-10 - math.sin(query.anim_time * 70 + 60) * 5"]},
                    "flower": {"rotation": [0, "math.sin(query.anim_time * 70) * 10", "math.sin(query.anim_time * 60) * 5"]},
                    "leaf": {"rotation": [0, "28 + math.sin(query.anim_time * 45) * 5", 0]},
                },
            },
            "animation.bl.dewdrop_snail.idle": {
                "loop": True,
                "animation_length": 4.0,
                "bones": {
                    "eye_stalk_left": {"rotation": ["-8 + math.sin(query.anim_time * 50) * 4", 0, "10 + math.sin(query.anim_time * 40) * 4"]},
                    "eye_stalk_right": {"rotation": ["-8 + math.sin(query.anim_time * 50 + 100) * 4", 0, "-10 - math.sin(query.anim_time * 40 + 100) * 4"]},
                    "flower": {"rotation": [0, "math.sin(query.anim_time * 45) * 8", "math.sin(query.anim_time * 35) * 4"]},
                    "shell": {"position": [0, "math.sin(query.anim_time * 60) * 0.08", 0]},
                },
            },
        },
    }
    controller = {
        "format_version": "1.10.0",
        "animation_controllers": {
            "controller.animation.bl.dewdrop_snail": {
                "initial_state": "idle",
                "states": {
                    "idle": {"animations": ["idle"], "transitions": [{"crawl": "query.modified_move_speed > 0.01"}], "blend_transition": 0.4},
                    "crawl": {"animations": ["crawl"], "transitions": [{"idle": "query.modified_move_speed <= 0.01"}], "blend_transition": 0.4},
                },
            }
        },
    }
    return anim, controller, "controller.animation.bl.dewdrop_snail"


def entity_specs() -> list[EntitySpec]:
    specs = []
    for key, label, model_fn, egg_base, egg_overlay, width, height, health, movement, flying, sound, weight, gmin, gmax, anim_fn in [
        ("petalwing", "Petalwing", petalwing_model, "#f7a8c8", "#7b4b9e", 0.6, 0.7, 10, 0.65, True, "mob.butterfly", 14, 1, 3, _animations_petalwing),
        ("mossling", "Mossling", mossling_model, "#6a9b4a", "#f7a8c8", 0.9, 1.1, 24, 0.32, False, "", 12, 1, 2, _animations_mossling),
        ("dewdrop_snail", "Dewdrop Snail", dewdrop_snail_model, "#5fb8b0", "#f5d98a", 0.9, 1.1, 16, 0.12, False, "", 10, 1, 2, _animations_snail),
    ]:
        geo, tex, tiles = model_fn()
        anim, controller_json, animate = anim_fn()
        if controller_json:
            controller_id = next(iter(controller_json["animation_controllers"]))
            animate = ["controller"]
        else:
            controller_id = ""
            animate = animate if isinstance(animate, list) else [animate]
        specs.append(
            EntitySpec(
                key=key,
                label=label,
                identifier=f"{NS}:{key}",
                geometry_id=geo["minecraft:geometry"][0]["description"]["identifier"],
                geometry=geo,
                texture=tex,
                atlas_tiles=tiles,
                animations=anim,
                controller=controller_id,
                controller_json=controller_json,
                animate=animate,
                egg_base=egg_base,
                egg_overlay=egg_overlay,
                width=width,
                height=height,
                health=health,
                movement=movement,
                flying=flying,
                ambient_sound=sound,
                spawn_weight=weight,
                spawn_group_min=gmin,
                spawn_group_max=gmax,
            )
        )
    return specs
