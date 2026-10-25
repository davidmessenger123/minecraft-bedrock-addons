"""
Content and asset builders for the Rainbow Garden add-on.

The add-on is deliberately data-only: custom blocks, items, recipes and one
ambient butterfly entity.  Keeping it script-free means it installs on a
normal Bedrock world without experiments, and a four-year-old can play with
it in Creative mode without any UI or reading.
"""

from __future__ import annotations

import math
import random
from PIL import Image, ImageChops, ImageDraw

NS = "rg"
VERSION = "1.0.1"
PACK_NAME = "Rainbow Garden"
BP_NAME = "Rainbow Garden Behaviour Pack"
RP_NAME = "Rainbow Garden Resource Pack"

# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

FLOWERS = [
    {
        "key": "red",
        "label": "Red",
        "dye": "minecraft:red_dye",
        "petal": (255, 82, 126),
        "dark": (188, 35, 78),
        "light": (255, 172, 198),
        "map": "#ff5a8a",
    },
    {
        "key": "orange",
        "label": "Orange",
        "dye": "minecraft:orange_dye",
        "petal": (255, 148, 48),
        "dark": (192, 82, 12),
        "light": (255, 204, 112),
        "map": "#ff9838",
    },
    {
        "key": "yellow",
        "label": "Yellow",
        "dye": "minecraft:yellow_dye",
        "petal": (255, 220, 64),
        "dark": (196, 154, 18),
        "light": (255, 247, 154),
        "map": "#ffe04a",
    },
    {
        "key": "green",
        "label": "Green",
        "dye": "minecraft:lime_dye",
        "petal": (84, 220, 120),
        "dark": (22, 142, 64),
        "light": (174, 255, 190),
        "map": "#54dc78",
    },
    {
        "key": "blue",
        "label": "Blue",
        "dye": "minecraft:light_blue_dye",
        "petal": (72, 154, 255),
        "dark": (24, 78, 190),
        "light": (164, 214, 255),
        "map": "#489aff",
    },
    {
        "key": "purple",
        "label": "Purple",
        "dye": "minecraft:purple_dye",
        "petal": (188, 106, 255),
        "dark": (112, 42, 184),
        "light": (232, 182, 255),
        "map": "#bc6aff",
    },
]

# UV regions inside the 64x64 flower texture.  Each region has a little
# transparent padding so texture filtering cannot bleed between parts.
FLOWER_UV = {
    "stem": (0, 0),
    "leaf": (8, 0),
    "petal": (24, 0),
    "center": (44, 0),
    "sparkle": (0, 32),
}

TREE_UV = {"trunk": (0, 0), "leaves": (16, 0), "fruit": (48, 0)}
MUSHROOM_UV = {"stem": (0, 0), "cap": (16, 0), "underside": (44, 0)}
BUTTERFLY_UV = {
    "body": (0, 0),
    "head": (8, 0),
    "wing_upper_right": (0, 20),
    "wing_upper_left": (12, 20),
    "wing_lower_right": (0, 30),
    "wing_lower_left": (10, 30),
}


# ---------------------------------------------------------------------------
# Texture painting
# ---------------------------------------------------------------------------

def _rgba(size: tuple[int, int] = (64, 64)) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _gradient_rect(draw: ImageDraw.ImageDraw, box, top, bottom):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0 - 1)
    for y in range(y0, y1):
        t = (y - y0) / h
        c = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(x0, y), (x1 - 1, y)], fill=c + (255,))


def _rainbow(t: float):
    stops = [
        (255, 82, 126),
        (255, 148, 48),
        (255, 224, 72),
        (84, 220, 120),
        (72, 154, 255),
        (188, 106, 255),
        (255, 82, 126),
    ]
    t = max(0.0, min(0.999999, t)) * (len(stops) - 1)
    i = int(t)
    f = t - i
    a, b = stops[i], stops[i + 1]
    return tuple(round(a[j] + (b[j] - a[j]) * f) for j in range(3))


def _draw_leaf(draw: ImageDraw.ImageDraw, x: int, y: int):
    draw.rectangle([x, y, x + 11, y + 7], fill=(52, 150, 76, 255))
    draw.ellipse([x + 1, y + 1, x + 10, y + 6], fill=(104, 206, 112, 255))
    draw.line([(x + 1, y + 4), (x + 10, y + 4)], fill=(28, 104, 54, 255), width=1)
    draw.line([(x + 5, y + 1), (x + 5, y + 6)], fill=(28, 104, 54, 255), width=1)


def _draw_petal(draw: ImageDraw.ImageDraw, x: int, y: int, flower: dict):
    # The whole region is opaque.  The cube geometry supplies the petal shape;
    # the texture adds a soft highlight and a darker edge.
    _gradient_rect(draw, (x, y, x + 16, y + 16), flower["light"], flower["petal"])
    draw.ellipse([x + 1, y + 1, x + 14, y + 14], fill=flower["petal"] + (255,))
    draw.ellipse([x + 4, y + 3, x + 12, y + 11], fill=flower["light"] + (255,))
    draw.arc([x + 2, y + 2, x + 13, y + 13], 200, 340, fill=flower["dark"] + (255,), width=1)


def _draw_center(draw: ImageDraw.ImageDraw, x: int, y: int):
    draw.rectangle([x, y, x + 11, y + 11], fill=(255, 196, 40, 255))
    draw.ellipse([x + 1, y + 1, x + 10, y + 10], fill=(255, 226, 86, 255))
    draw.ellipse([x + 3, y + 3, x + 8, y + 8], fill=(226, 138, 20, 255))
    for px, py in [(x + 4, y + 2), (x + 8, y + 5), (x + 5, y + 9)]:
        draw.point((px, py), fill=(255, 255, 200, 255))


def _draw_sparkle(draw: ImageDraw.ImageDraw, x: int, y: int):
    draw.polygon(
        [(x + 8, y), (x + 10, y + 6), (x + 16, y + 8), (x + 10, y + 10),
         (x + 8, y + 16), (x + 6, y + 10), (x, y + 8), (x + 6, y + 6)],
        fill=(255, 255, 255, 255),
    )
    draw.ellipse([x + 6, y + 6, x + 10, y + 10], fill=(255, 246, 170, 255))


def flower_texture(flower: dict) -> Image.Image:
    img = _rgba()
    d = ImageDraw.Draw(img)
    x, y = FLOWER_UV["stem"]
    _gradient_rect(d, (x, y, x + 4, y + 24), (90, 194, 92), (32, 116, 54))
    for yy in range(2, 23, 4):
        d.line([(x + 1, y + yy), (x + 2, y + yy)], fill=(24, 96, 44, 255), width=1)

    _draw_leaf(d, *FLOWER_UV["leaf"])
    _draw_petal(d, *FLOWER_UV["petal"], flower)
    _draw_center(d, *FLOWER_UV["center"])
    _draw_sparkle(d, *FLOWER_UV["sparkle"])
    return img


def tree_texture() -> Image.Image:
    img = _rgba()
    d = ImageDraw.Draw(img)
    x, y = TREE_UV["trunk"]
    _gradient_rect(d, (x, y, x + 8, y + 20), (142, 96, 54), (88, 56, 30))
    for yy in range(2, 19, 3):
        d.line([(x + 1, y + yy), (x + 6, y + yy)], fill=(72, 44, 22, 255), width=1)

    lx, ly = TREE_UV["leaves"]
    _gradient_rect(d, (lx, ly, lx + 28, ly + 28), (86, 214, 116), (32, 142, 76))
    rng = random.Random(11)
    for _ in range(34):
        cx = lx + rng.randrange(1, 26)
        cy = ly + rng.randrange(1, 26)
        r = rng.choice([1, 1, 2, 2, 3])
        color = rng.choice([
            (255, 232, 92), (255, 150, 90), (255, 112, 170),
            (140, 220, 255), (198, 142, 255), (188, 255, 144),
        ])
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,))
    for _ in range(10):
        cx = lx + rng.randrange(0, 28)
        cy = ly + rng.randrange(0, 28)
        d.point((cx, cy), fill=(24, 104, 52, 255))

    fx, fy = TREE_UV["fruit"]
    _gradient_rect(d, (fx, fy, fx + 8, fy + 8), (255, 154, 210), (226, 70, 150))
    d.ellipse([fx + 1, fy + 1, fx + 6, fy + 6], fill=(255, 210, 238, 255))
    d.point((fx + 2, fy + 2), fill=(255, 255, 255, 255))
    return img


def mushroom_texture() -> Image.Image:
    img = _rgba()
    d = ImageDraw.Draw(img)
    x, y = MUSHROOM_UV["stem"]
    _gradient_rect(d, (x, y, x + 8, y + 16), (255, 240, 206), (208, 174, 126))
    for yy in range(3, 15, 3):
        d.line([(x + 1, y + yy), (x + 6, y + yy)], fill=(184, 146, 100, 255), width=1)

    cx, cy = MUSHROOM_UV["cap"]
    _gradient_rect(d, (cx, cy, cx + 24, cy + 16), (255, 112, 154), (204, 58, 118))
    for sx, sy, r in [(4, 3, 3), (14, 2, 2), (20, 8, 3), (9, 10, 2), (17, 13, 2)]:
        d.ellipse([cx + sx - r, cy + sy - r, cx + sx + r, cy + sy + r], fill=(255, 244, 226, 255))
    d.arc([cx + 1, cy + 1, cx + 22, cy + 14], 200, 340, fill=(255, 190, 214, 255), width=1)

    ux, uy = MUSHROOM_UV["underside"]
    _gradient_rect(d, (ux, uy, ux + 16, uy + 16), (226, 190, 142), (168, 126, 82))
    for xx in range(1, 16, 3):
        d.line([(ux + xx, uy + 1), (ux + xx, uy + 14)], fill=(142, 100, 64, 255), width=1)
    return img


def lantern_texture() -> Image.Image:
    img = Image.new("RGBA", (16, 16), (34, 26, 54, 255))
    d = ImageDraw.Draw(img)
    # Dark frame
    d.rectangle([0, 0, 15, 1], fill=(52, 38, 76, 255))
    d.rectangle([0, 14, 15, 15], fill=(52, 38, 76, 255))
    d.rectangle([0, 0, 1, 15], fill=(52, 38, 76, 255))
    d.rectangle([14, 0, 15, 15], fill=(52, 38, 76, 255))
    # Four glowing rainbow panes
    colors = [(255, 98, 142), (255, 202, 72), (96, 218, 128), (98, 168, 255)]
    for i, color in enumerate(colors):
        x = 3 + (i % 2) * 6
        y = 3 + (i // 2) * 6
        d.rectangle([x, y, x + 4, y + 4], fill=color + (255,))
        d.rectangle([x, y, x + 4, y], fill=(255, 255, 255, 150))
    d.rectangle([7, 2, 8, 13], fill=(255, 244, 186, 220))
    return img


def _wing_masks() -> tuple[Image.Image, Image.Image]:
    # These masks are drawn for the right wing, with the narrow body edge at
    # x=0 and the rounded outer tip at x=width-1.  The left wing is the
    # horizontal mirror of this texture.
    upper = Image.new("L", (11, 7), 0)
    du = ImageDraw.Draw(upper)
    du.polygon([
        (0, 2), (2, 0), (6, 0), (9, 1), (10, 3),
        (9, 5), (6, 6), (3, 6), (1, 5), (0, 4),
    ], fill=255)

    lower = Image.new("L", (9, 5), 0)
    dl = ImageDraw.Draw(lower)
    dl.polygon([
        (0, 2), (2, 0), (5, 0), (8, 2),
        (8, 3), (6, 4), (3, 4), (1, 3),
    ], fill=255)
    return upper, lower


def _paint_wing(width: int, height: int, mask: Image.Image) -> Image.Image:
    wing = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    px = wing.load()
    for yy in range(height):
        for xx in range(width):
            if mask.getpixel((xx, yy)) < 128:
                continue
            t = (xx / max(1, width - 1)) * 0.8 + (yy / max(1, height - 1)) * 0.2
            px[xx, yy] = _rainbow(t) + (255,)

    # A dark one-pixel edge makes the silhouette readable against the sky.
    outlined = wing.copy()
    op = outlined.load()
    for yy in range(height):
        for xx in range(width):
            if mask.getpixel((xx, yy)) < 128:
                continue
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = xx + dx, yy + dy
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    edge = True
                elif mask.getpixel((nx, ny)) < 128:
                    edge = True
            if edge:
                op[xx, yy] = (38, 24, 72, 255)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.line([(0, 3), (width - 2, 1)], fill=(48, 30, 86, 210), width=1)
    od.line([(0, 3), (width - 2, 3)], fill=(48, 30, 86, 210), width=1)
    od.line([(0, 3), (width - 3, height - 2)], fill=(48, 30, 86, 210), width=1)
    for sx, sy in ((width // 3, 2), (width // 2 + 1, height // 2)):
        od.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255, 230))
    overlay.putalpha(ImageChops.multiply(overlay.getchannel("A"), mask))
    outlined.alpha_composite(overlay)
    return outlined


def butterfly_texture() -> Image.Image:
    img = _rgba()
    d = ImageDraw.Draw(img)

    # Body and head.
    bx, by = BUTTERFLY_UV["body"]
    _gradient_rect(d, (bx, by, bx + 8, by + 20), (82, 56, 142), (38, 24, 78))
    for yy in range(2, 20, 3):
        d.line([(bx + 1, by + yy), (bx + 6, by + yy)], fill=(154, 112, 222, 255), width=1)
    hx, hy = BUTTERFLY_UV["head"]
    d.rectangle([hx, hy, hx + 7, hy + 7], fill=(44, 28, 84, 255))
    d.ellipse([hx + 1, hy + 2, hx + 3, hy + 4], fill=(180, 246, 255, 255))
    d.ellipse([hx + 4, hy + 2, hx + 6, hy + 4], fill=(180, 246, 255, 255))

    upper_mask, lower_mask = _wing_masks()
    upper_right = _paint_wing(11, 7, upper_mask)
    lower_right = _paint_wing(9, 5, lower_mask)
    upper_left = upper_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    lower_left = lower_right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    for key, wing in (
        ("wing_upper_right", upper_right),
        ("wing_upper_left", upper_left),
        ("wing_lower_right", lower_right),
        ("wing_lower_left", lower_left),
    ):
        x, y = BUTTERFLY_UV[key]
        img.alpha_composite(wing, (x, y))
    return img


def seed_icon(flower: dict) -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, 29, 29], radius=7, fill=(255, 249, 224, 235), outline=(150, 118, 82, 255), width=1)
    # Seed
    d.ellipse([10, 19, 21, 27], fill=(150, 102, 56, 255), outline=(104, 68, 34, 255))
    d.arc([11, 20, 20, 26], 200, 340, fill=(210, 168, 108, 255), width=1)
    # Stem
    d.line([(16, 20), (16, 12)], fill=(54, 142, 70, 255), width=2)
    # Five petals
    cx, cy = 16, 10
    for dx, dy in [(-5, 0), (5, 0), (0, -5), (-3, -3), (3, -3)]:
        d.ellipse([cx + dx - 3, cy + dy - 3, cx + dx + 3, cy + dy + 3], fill=flower["petal"] + (255,))
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(255, 218, 76, 255))
    return img


def tree_seed_icon() -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, 29, 29], radius=7, fill=(236, 255, 232, 235), outline=(74, 132, 82, 255), width=1)
    d.rectangle([14, 17, 17, 27], fill=(126, 82, 44, 255))
    for cx, cy, r, color in [(16, 13, 7, (84, 214, 112)), (10, 16, 5, (255, 208, 80)), (22, 16, 5, (255, 130, 170)), (16, 7, 5, (112, 178, 255))]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,))
    d.point((13, 10), fill=(255, 255, 255, 255))
    d.point((20, 13), fill=(255, 255, 255, 255))
    return img


def mushroom_seed_icon() -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, 29, 29], radius=7, fill=(255, 238, 246, 235), outline=(152, 88, 120, 255), width=1)
    d.rectangle([14, 17, 17, 27], fill=(246, 224, 190, 255))
    d.ellipse([6, 9, 26, 21], fill=(236, 82, 140, 255))
    d.rectangle([6, 15, 25, 20], fill=(236, 82, 140, 255))
    for cx, cy, r in [(10, 12, 2), (18, 11, 2), (22, 16, 2), (13, 17, 1)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 246, 230, 255))
    d.arc([7, 9, 25, 20], 200, 340, fill=(255, 176, 206, 255), width=1)
    return img


def pack_icon() -> Image.Image:
    img = Image.new("RGB", (128, 128), (28, 34, 70))
    d = ImageDraw.Draw(img)
    # Sky gradient
    for y in range(128):
        t = y / 127
        c = (round(42 + 70 * t), round(54 + 96 * t), round(110 + 90 * t))
        d.line([(0, y), (127, y)], fill=c)
    # Sun
    d.ellipse([94, 10, 118, 34], fill=(255, 236, 132))
    # Rainbow
    for i, color in enumerate([(255, 88, 132), (255, 156, 58), (255, 228, 76), (92, 218, 124), (82, 160, 255), (190, 112, 255)]):
        r = 54 - i * 6
        d.arc([64 - r, 44 - r, 64 + r, 44 + r], 180, 360, fill=color, width=5)
    # Hill
    d.ellipse([-34, 82, 162, 174], fill=(52, 146, 82))
    d.ellipse([-10, 90, 138, 164], fill=(74, 182, 102))
    # Flower
    for dx, dy in [(-12, -8), (12, -8), (0, -18), (-10, 4), (10, 4)]:
        d.ellipse([52 + dx - 9, 84 + dy - 9, 52 + dx + 9, 84 + dy + 9], fill=(255, 118, 166))
    d.ellipse([44, 76, 60, 92], fill=(255, 224, 84))
    d.rectangle([51, 92, 54, 112], fill=(38, 128, 64))
    # Butterfly
    d.ellipse([80, 60, 98, 78], fill=(255, 190, 82))
    d.ellipse([94, 64, 110, 80], fill=(255, 118, 166))
    d.rectangle([92, 66, 95, 84], fill=(58, 34, 90))
    d.ellipse([89, 55, 99, 65], fill=(255, 244, 154))
    return img


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _face_uv(region: tuple[int, int], w: int, h: int, d: int):
    u, v = region
    return {
        "north": {"uv": [u, v], "uv_size": [w, h]},
        "south": {"uv": [u, v], "uv_size": [w, h]},
        "east": {"uv": [u, v], "uv_size": [d, h]},
        "west": {"uv": [u, v], "uv_size": [d, h]},
        "up": {"uv": [u, v], "uv_size": [w, d]},
        "down": {"uv": [u, v], "uv_size": [w, d]},
    }


def cube(origin, size, region, rotation=None, pivot=None):
    c = {
        "origin": list(origin),
        "size": list(size),
        "uv": _face_uv(region, *size),
    }
    if rotation is not None:
        c["rotation"] = list(rotation)
    if pivot is not None:
        c["pivot"] = list(pivot)
    return c


def bone(name: str, cubes: list, pivot=(0, 0, 0), parent: str | None = None):
    b = {"name": name, "pivot": list(pivot), "cubes": cubes}
    if parent is not None:
        b["parent"] = parent
    return b


def block_geometry(identifier: str, bones: list):
    return {
        "format_version": "1.21.90",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": identifier,
                    "texture_width": 64,
                    "texture_height": 64,
                },
                "bones": bones,
            }
        ],
    }


def entity_geometry(identifier: str, bones: list):
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": identifier,
                    "texture_width": 64,
                    "texture_height": 64,
                    "visible_bounds_width": 2.0,
                    "visible_bounds_height": 2.0,
                    "visible_bounds_offset": [0.0, 0.8, 0.0],
                },
                "bones": bones,
            }
        ],
    }


def flower_geometry():
    return block_geometry(
        "geometry.rg.rainbow_flower",
        [
            bone(
                "flower",
                [
                    cube([-1, 0, -1], [2, 18, 2], FLOWER_UV["stem"]),
                    cube([-9, 5, -0.5], [8, 3, 1], FLOWER_UV["leaf"]),
                    cube([1, 8, -0.5], [8, 3, 1], FLOWER_UV["leaf"]),
                    # Lower ring of petals
                    cube([-3, 18, -7], [6, 1, 5], FLOWER_UV["petal"]),
                    cube([-3, 18, 2], [6, 1, 5], FLOWER_UV["petal"]),
                    cube([2, 18, -3], [5, 1, 6], FLOWER_UV["petal"]),
                    cube([-7, 18, -3], [5, 1, 6], FLOWER_UV["petal"]),
                    # Upper, smaller petals
                    cube([-2, 21, -6], [4, 1, 4], FLOWER_UV["petal"]),
                    cube([-2, 21, 2], [4, 1, 4], FLOWER_UV["petal"]),
                    cube([2, 21, -2], [4, 1, 4], FLOWER_UV["petal"]),
                    cube([-6, 21, -2], [4, 1, 4], FLOWER_UV["petal"]),
                    cube([-3, 19, -3], [6, 2, 6], FLOWER_UV["center"]),
                ],
            )
        ],
    )


def tree_geometry():
    return block_geometry(
        "geometry.rg.rainbow_tree",
        [
            bone(
                "tree",
                [
                    cube([-2, 0, -2], [4, 18, 4], TREE_UV["trunk"]),
                    cube([-9, 16, -9], [18, 8, 18], TREE_UV["leaves"]),
                    cube([-6, 24, -6], [12, 6, 12], TREE_UV["leaves"]),
                    cube([-12, 18, -5], [4, 6, 10], TREE_UV["leaves"]),
                    cube([8, 18, -5], [4, 6, 10], TREE_UV["leaves"]),
                    cube([-5, 18, -12], [10, 6, 4], TREE_UV["leaves"]),
                    cube([-5, 18, 8], [10, 6, 4], TREE_UV["leaves"]),
                    cube([-12, 22, -1], [2, 2, 2], TREE_UV["fruit"]),
                    cube([10, 22, -1], [2, 2, 2], TREE_UV["fruit"]),
                    cube([-1, 22, -12], [2, 2, 2], TREE_UV["fruit"]),
                    cube([-1, 22, 10], [2, 2, 2], TREE_UV["fruit"]),
                ],
            )
        ],
    )


def mushroom_geometry():
    return block_geometry(
        "geometry.rg.rainbow_mushroom",
        [
            bone(
                "mushroom",
                [
                    cube([-2, 0, -2], [4, 12, 4], MUSHROOM_UV["stem"]),
                    cube([-8, 10, -8], [16, 6, 16], MUSHROOM_UV["cap"]),
                    cube([-5, 16, -5], [10, 4, 10], MUSHROOM_UV["cap"]),
                    cube([-6, 10, -6], [12, 1, 12], MUSHROOM_UV["underside"]),
                ],
            )
        ],
    )


def butterfly_geometry():
    return entity_geometry(
        "geometry.rg.rainbow_butterfly",
        [
            bone("root", [], pivot=[0, 0, 0]),
            bone(
                "body",
                [
                    cube([-1, 4, -4], [2, 2, 8], BUTTERFLY_UV["body"]),
                    cube([-1.5, 4, -7], [3, 3, 3], BUTTERFLY_UV["head"]),
                    cube([-1.5, 7, -6], [1, 4, 1], BUTTERFLY_UV["body"],
                         rotation=[0, 0, 20], pivot=[-1.5, 7, -5]),
                    cube([0.5, 7, -6], [1, 4, 1], BUTTERFLY_UV["body"],
                         rotation=[0, 0, -20], pivot=[0.5, 7, -5]),
                ],
                pivot=[0, 4, 0],
                parent="root",
            ),
            bone(
                "left_wing",
                [
                    cube([-12, 6, -5], [11, 1, 7], BUTTERFLY_UV["wing_upper_left"],
                         rotation=[0, 0, -18], pivot=[0, 6, 0]),
                    cube([-10, 5, 0], [9, 1, 5], BUTTERFLY_UV["wing_lower_left"],
                         rotation=[0, 0, -8], pivot=[0, 5, 0]),
                ],
                pivot=[0, 6, 0],
                parent="body",
            ),
            bone(
                "right_wing",
                [
                    cube([1, 6, -5], [11, 1, 7], BUTTERFLY_UV["wing_upper_right"],
                         rotation=[0, 0, 18], pivot=[0, 6, 0]),
                    cube([1, 5, 0], [9, 1, 5], BUTTERFLY_UV["wing_lower_right"],
                         rotation=[0, 0, 8], pivot=[0, 5, 0]),
                ],
                pivot=[0, 6, 0],
                parent="body",
            ),
        ],
    )
