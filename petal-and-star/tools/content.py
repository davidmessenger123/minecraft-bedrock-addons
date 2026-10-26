"""
Petal & Star - procedural texture content.

Every texture in the pack is painted here with Pillow.  The only borrowed
source art is the small set of vanilla entity atlases in tools/vanilla_entity;
they are recoloured, never shipped unmodified.  Keeping the generator
deterministic means the pack can be rebuilt byte-for-byte.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
VANILLA_ENTITY = Path(__file__).resolve().parent / "vanilla_entity"

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

INK = (67, 48, 82)
INK_SOFT = (104, 82, 119)
CREAM = (255, 248, 232)
CREAM_DARK = (244, 229, 208)
BLUSH = (255, 190, 204)
PINK = (255, 151, 177)
ROSE = (232, 111, 143)
CORAL = (247, 132, 126)
LAVENDER = (207, 184, 255)
PURPLE = (165, 135, 220)
PLUM = (120, 88, 145)
MINT = (176, 232, 194)
MINT_DARK = (119, 196, 152)
GREEN = (139, 211, 161)
SAGE = (157, 194, 156)
TEAL = (102, 181, 168)
SKY = (170, 222, 255)
BLUE = (125, 184, 239)
PERIWINKLE = (155, 164, 235)
BUTTER = (255, 229, 153)
GOLD = (244, 190, 96)
PEACH = (255, 203, 167)
COCOA = (143, 98, 80)
BROWN = (112, 76, 68)
WOOD = (206, 152, 107)
WOOD_LIGHT = (232, 182, 130)
WOOD_DARK = (164, 111, 81)
STONE = (205, 197, 220)
STONE_LIGHT = (229, 222, 239)
STONE_DARK = (163, 153, 184)
AQUA = (143, 222, 230)
AQUA_DARK = (96, 184, 198)

WHITE = (255, 255, 255)


def rgba(width: int = 16, height: int = 16, color=(0, 0, 0, 0)) -> Image.Image:
    return Image.new("RGBA", (width, height), color)


def mix(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] * (1.0 - t) + b[i] * t) for i in range(3))


def shade(color, factor: float):
    return tuple(max(0, min(255, round(c * factor))) for c in color[:3])


def rng(seed: int) -> random.Random:
    return random.Random(seed)


def _noise_tile(base, shades, count: int, seed: int) -> Image.Image:
    img = rgba(color=base + (255,))
    d = ImageDraw.Draw(img)
    r = rng(seed)
    for _ in range(count):
        x, y = r.randrange(16), r.randrange(16)
        d.point((x, y), fill=r.choice(shades) + (255,))
    return img


def _sparkle(d: ImageDraw.ImageDraw, x: int, y: int, color, size: int = 1):
    if size <= 1:
        d.point((x, y), fill=color + (255,))
        return
    d.line([(x - size, y), (x + size, y)], fill=color + (255,), width=1)
    d.line([(x, y - size), (x, y + size)], fill=color + (255,), width=1)
    d.point((x, y), fill=WHITE + (255,))


def _heart(d: ImageDraw.ImageDraw, x: int, y: int, color, size: int = 1):
    if size <= 1:
        d.point((x, y), fill=color + (255,))
        d.point((x - 1, y), fill=color + (255,))
        d.point((x + 1, y), fill=color + (255,))
        d.point((x, y + 1), fill=color + (255,))
        return
    # A compact 7x6 heart, good at item-icon scale.
    pts = [
        (x - 3, y - 2), (x - 2, y - 3), (x - 1, y - 2),
        (x, y - 1), (x + 1, y - 2), (x + 2, y - 3),
        (x + 3, y - 2), (x + 3, y), (x + 2, y + 2),
        (x, y + 3), (x - 2, y + 2), (x - 3, y),
    ]
    d.polygon(pts, fill=color + (255,))


def _daisy(d: ImageDraw.ImageDraw, x: int, y: int, petal, center, outline=INK):
    # 5x5 flower with a dark rim and a bright middle.
    for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        d.point((x + dx, y + dy), fill=outline + (255,))
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        d.point((x + dx, y + dy), fill=petal + (255,))
    d.point((x, y), fill=center + (255,))


def _star_points(cx: float, cy: float, outer: float, inner: float):
    pts = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = outer if i % 2 == 0 else inner
        pts.append((round(cx + math.cos(angle) * radius), round(cy + math.sin(angle) * radius)))
    return pts


def _leaf(d: ImageDraw.ImageDraw, x: int, y: int, color, outline=None, flip: bool = False):
    if flip:
        d.ellipse([x - 2, y - 1, x + 1, y + 1], fill=color + (255,))
        if outline:
            d.point((x - 2, y), fill=outline + (255,))
    else:
        d.ellipse([x - 1, y - 1, x + 2, y + 1], fill=color + (255,))
        if outline:
            d.point((x + 2, y), fill=outline + (255,))


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


def grass_top() -> Image.Image:
    img = _noise_tile(
        (174, 229, 184),
        [(151, 215, 165), (194, 241, 201), (137, 204, 155), (211, 247, 210)],
        150,
        seed=11,
    )
    d = ImageDraw.Draw(img)
    # Tufts and tiny clover.
    for x, y, c in [
        (2, 5, MINT_DARK), (4, 9, GREEN), (8, 3, MINT_DARK),
        (12, 7, GREEN), (14, 12, MINT_DARK), (6, 14, GREEN),
    ]:
        d.line([(x, y), (x, y - 2)], fill=c + (255,))
    for x, y, petal, center in [
        (3, 3, WHITE, GOLD), (11, 8, BLUSH, CREAM), (7, 12, BUTTER, CREAM),
    ]:
        _daisy(d, x, y, petal, center)
    _sparkle(d, 13, 3, WHITE)
    _sparkle(d, 5, 10, CREAM)
    return img


def dirt() -> Image.Image:
    img = _noise_tile(
        (135, 94, 78),
        [(116, 79, 68), (154, 111, 91), (172, 127, 105), (99, 68, 61)],
        180,
        seed=21,
    )
    d = ImageDraw.Draw(img)
    for x, y, c in [(3, 4, (181, 138, 113)), (10, 2, (102, 69, 61)), (6, 12, (172, 124, 101)), (13, 10, (109, 75, 66))]:
        d.ellipse([x - 1, y, x + 1, y + 1], fill=c + (255,))
    _heart(d, 8, 7, (199, 155, 132), size=1)
    _sparkle(d, 12, 13, (219, 183, 156))
    return img


def grass_side() -> Image.Image:
    img = dirt()
    d = ImageDraw.Draw(img)
    r = rng(31)
    for x in range(16):
        depth = 3 + (1 if (x * 7 + 3) % 5 < 2 else 0) + r.choice((0, 0, 1))
        for y in range(depth):
            t = y / max(1, depth - 1)
            color = mix((146, 211, 160), (185, 235, 193), 1.0 - t)
            d.point((x, y), fill=color + (255,))
        if depth < 6 and x % 3 == 0:
            d.line([(x, depth), (x, depth + 2)], fill=(122, 194, 144, 255))
    _daisy(d, 4, 2, WHITE, GOLD)
    _daisy(d, 12, 3, BLUSH, CREAM)
    return img


def stone() -> Image.Image:
    img = _noise_tile(
        STONE,
        [(184, 175, 204), (222, 214, 235), (194, 184, 216), (171, 160, 194)],
        160,
        seed=41,
    )
    d = ImageDraw.Draw(img)
    pebbles = [
        (2, 3, 5, 3, (214, 206, 232)), (9, 2, 5, 4, (188, 178, 210)),
        (4, 9, 6, 3, (226, 218, 241)), (11, 10, 4, 4, (181, 171, 204)),
        (1, 13, 4, 2, (198, 189, 220)),
    ]
    for x, y, w, h, c in pebbles:
        d.rounded_rectangle([x, y, x + w, y + h], radius=1, fill=c + (255,))
        d.line([(x + 1, y + 1), (x + w - 1, y + 1)], fill=(241, 236, 248, 255))
        d.line([(x + 1, y + h), (x + w - 1, y + h)], fill=(145, 134, 169, 255))
    _sparkle(d, 8, 7, WHITE)
    _sparkle(d, 14, 6, (255, 244, 200))
    return img


def cobblestone() -> Image.Image:
    img = rgba(color=CREAM_DARK + (255,))
    d = ImageDraw.Draw(img)
    r = rng(51)
    stones = [
        [(1, 2), (5, 1), (7, 3), (6, 6), (2, 6), (0, 4)],
        [(8, 1), (13, 1), (15, 4), (13, 6), (9, 6), (7, 3)],
        [(1, 8), (5, 7), (7, 10), (6, 14), (2, 15), (0, 12)],
        [(9, 8), (14, 7), (15, 10), (13, 14), (9, 15), (7, 12)],
        [(5, 8), (7, 8), (8, 10), (6, 11)],
    ]
    fills = [
        (196, 187, 218), (214, 205, 232), (180, 171, 205),
        (224, 215, 239), (203, 194, 224),
    ]
    for i, pts in enumerate(stones):
        c = fills[i % len(fills)]
        d.polygon([(x, y) for x, y in pts], fill=c + (255,))
        d.line(pts + [pts[0]], fill=(143, 132, 168, 255), width=1)
        d.line([pts[0], pts[1]], fill=(244, 238, 250, 255), width=1)
    for _ in range(20):
        x, y = r.randrange(16), r.randrange(16)
        d.point((x, y), fill=(239, 232, 247, 255))
    _sparkle(d, 11, 4, WHITE)
    return img


def sand() -> Image.Image:
    img = _noise_tile(
        (255, 232, 181),
        [(255, 240, 199), (244, 216, 160), (255, 246, 218), (238, 205, 152)],
        150,
        seed=61,
    )
    d = ImageDraw.Draw(img)
    # Tiny shells and a starfish.
    for x, y in [(3, 4), (11, 9), (6, 13)]:
        d.arc([x - 2, y - 1, x + 2, y + 2], 180, 360, fill=(234, 166, 147, 255), width=1)
        d.point((x, y + 2), fill=(255, 250, 231, 255))
    pts = _star_points(12, 3, 3, 1)
    d.polygon(pts, fill=(247, 166, 146, 255))
    _sparkle(d, 8, 7, WHITE)
    _sparkle(d, 2, 10, (255, 255, 255))
    return img


def log_side(bark, dark, light, knot, seed: int) -> Image.Image:
    img = rgba(color=bark + (255,))
    d = ImageDraw.Draw(img)
    r = rng(seed)
    for x in range(16):
        if x % 3 == 0:
            d.line([(x, 0), (x, 15)], fill=dark + (255,))
        elif x % 4 == 1:
            d.line([(x, 0), (x, 15)], fill=light + (255,))
        else:
            for y in range(16):
                if r.random() < 0.22:
                    d.point((x, y), fill=(mix(bark, light, r.random() * 0.5)) + (255,))
    for x, y in [(4, 5), (11, 11)]:
        _heart(d, x, y, knot, size=1)
        d.point((x, y + 2), fill=dark + (255,))
    return img


def log_top(wood, ring, center, bark) -> Image.Image:
    img = rgba(color=wood + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], outline=bark + (255,))
    for i, color in [(7, ring), (5, mix(ring, wood, 0.45)), (3, ring), (1, center)]:
        d.ellipse([8 - i, 8 - i, 7 + i, 7 + i], outline=color + (255,), width=1)
    _heart(d, 8, 8, center, size=1)
    _sparkle(d, 12, 3, CREAM)
    return img


def planks(wood, light, dark, nail, seed: int) -> Image.Image:
    img = rgba(color=wood + (255,))
    d = ImageDraw.Draw(img)
    r = rng(seed)
    for row in range(4):
        y = row * 4
        d.line([(0, y), (15, y)], fill=dark + (255,))
        d.line([(0, y + 1), (15, y + 1)], fill=light + (255,))
        for x in range(16):
            if r.random() < 0.20:
                d.point((x, y + 2 + r.randrange(2)), fill=(mix(wood, light, 0.45)) + (255,))
        # A tiny star nail at alternating ends.
        nx = 3 if row % 2 == 0 else 12
        _sparkle(d, nx, y + 2, nail)
    return img


def leaves(palette, blossom, opaque: bool, seed: int) -> Image.Image:
    bg = palette[0] if opaque else (0, 0, 0, 0)
    img = rgba(color=bg + (255,) if opaque else bg)
    d = ImageDraw.Draw(img)
    r = rng(seed)
    for _ in range(52):
        x, y = r.randrange(16), r.randrange(16)
        c = r.choice(palette)
        d.ellipse([x - 1, y - 1, x + 2, y + 1], fill=c + (255,))
        if r.random() < 0.45:
            d.point((x, y - 1), fill=mix(c, WHITE, 0.35) + (255,))
        if r.random() < 0.20:
            d.point((x + 2, y), fill=shade(c, 0.72) + (255,))
    for x, y in [(3, 4), (11, 7), (7, 13), (14, 2)]:
        if r.random() < 0.75:
            _daisy(d, x, y, blossom, BUTTER)
    return img


# ---------------------------------------------------------------------------
# Flowers and plants
# ---------------------------------------------------------------------------


def flower_sprite(petal, petal_dark, center, shape: str, seed: int) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    r = rng(seed)
    stem = (105, 173, 128)
    d.line([(7, 15), (7, 8)], fill=stem + (255,))
    d.line([(8, 15), (8, 9)], fill=(126, 193, 146, 255))
    _leaf(d, 5, 11, (128, 197, 150), outline=(91, 154, 113), flip=True)
    _leaf(d, 10, 9, (144, 209, 160), outline=(91, 154, 113))

    if shape == "daisy":
        for dx, dy in ((0, -3), (-3, 0), (3, 0), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
            d.ellipse([8 + dx - 1, 5 + dy - 1, 8 + dx + 1, 5 + dy + 1], fill=petal + (255,))
        d.ellipse([6, 3, 10, 7], fill=center + (255,))
    elif shape == "tulip":
        d.polygon([(4, 5), (6, 2), (8, 4), (10, 2), (12, 5), (11, 9), (8, 11), (5, 9)], fill=petal_dark + (255,))
        d.polygon([(5, 5), (7, 3), (8, 5), (9, 3), (11, 5), (10, 8), (8, 10), (6, 8)], fill=petal + (255,))
        d.line([(8, 5), (8, 9)], fill=petal_dark + (255,))
    elif shape == "ball":
        d.ellipse([4, 2, 12, 10], fill=petal_dark + (255,))
        d.ellipse([5, 3, 11, 9], fill=petal + (255,))
        for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            d.point((8 + dx, 6 + dy), fill=center + (255,))
    elif shape == "star":
        d.polygon(_star_points(8, 6, 5, 2), fill=petal_dark + (255,))
        d.polygon(_star_points(8, 6, 4, 1.5), fill=petal + (255,))
        d.ellipse([7, 5, 9, 7], fill=center + (255,))
    elif shape == "rose":
        d.ellipse([4, 2, 12, 10], fill=petal_dark + (255,))
        d.ellipse([5, 3, 11, 9], fill=petal + (255,))
        d.arc([6, 4, 10, 8], 30, 300, fill=petal_dark + (255,), width=1)
        d.arc([7, 5, 9, 7], 120, 360, fill=center + (255,), width=1)
        d.point((8, 6), fill=center + (255,))
    elif shape == "bell":
        d.line([(7, 15), (7, 6)], fill=stem + (255,))
        for x, y in [(6, 6), (9, 8), (7, 11)]:
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=petal + (255,))
            d.point((x, y + 1), fill=petal_dark + (255,))
    elif shape == "tiny":
        for x, y in [(6, 5), (10, 7), (8, 10)]:
            _daisy(d, x, y, petal, center)
    else:
        _daisy(d, 8, 6, petal, center)

    # A few dew sparkles.
    if r.random() < 0.8:
        _sparkle(d, r.randrange(3, 13), r.randrange(2, 12), WHITE)
    return img


def tallgrass() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    r = rng(91)
    for x, h, c in [
        (2, 6, (123, 195, 144)), (4, 10, (151, 216, 161)), (6, 8, (111, 184, 134)),
        (8, 12, (169, 228, 177)), (10, 9, (135, 204, 149)), (12, 7, (151, 216, 161)),
        (14, 5, (118, 190, 141)),
    ]:
        d.line([(x, 15), (x + r.choice((-1, 0, 1)), 15 - h)], fill=c + (255,))
        _leaf(d, x, 15 - h // 2, c, outline=(91, 154, 113), flip=x % 2 == 0)
    _daisy(d, 8, 3, WHITE, GOLD)
    _daisy(d, 3, 7, BLUSH, CREAM)
    return img


def sunflower_head(back: bool = False) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    center = COCOA if not back else (109, 77, 66)
    petals = BUTTER if not back else (239, 211, 126)
    dark = GOLD if not back else (208, 167, 93)
    # A big, simple sunflower head with two rings of petals.
    for i in range(12):
        angle = i * math.tau / 12
        px = 8 + math.cos(angle) * 5
        py = 8 + math.sin(angle) * 5
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=dark + (255,))
    for i in range(10):
        angle = i * math.tau / 10 + 0.2
        px = 8 + math.cos(angle) * 4
        py = 8 + math.sin(angle) * 4
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=petals + (255,))
    d.ellipse([4, 4, 11, 11], fill=center + (255,))
    d.ellipse([5, 5, 10, 10], fill=mix(center, WHITE, 0.18) + (255,))
    for x, y in [(6, 6), (9, 7), (7, 9), (10, 10)]:
        d.point((x, y), fill=shade(center, 0.75) + (255,))
    _sparkle(d, 4, 4, CREAM)
    return img


def sunflower_stem(top: bool) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.line([(7, 0), (7, 15)], fill=(103, 173, 128, 255))
    d.line([(8, 0), (8, 15)], fill=(130, 198, 148, 255))
    if top:
        _leaf(d, 5, 7, (128, 197, 150), outline=(91, 154, 113), flip=True)
        _leaf(d, 10, 4, (144, 209, 160), outline=(91, 154, 113))
    else:
        _leaf(d, 5, 11, (128, 197, 150), outline=(91, 154, 113), flip=True)
        _leaf(d, 10, 8, (144, 209, 160), outline=(91, 154, 113))
    _daisy(d, 8, 2 if top else 13, BLUSH, CREAM)
    return img


# ---------------------------------------------------------------------------
# Wool, glass, water, lights
# ---------------------------------------------------------------------------


WOOL_COLORS = {
    "white": CREAM,
    "orange": PEACH,
    "magenta": ROSE,
    "light_blue": SKY,
    "yellow": BUTTER,
    "lime": MINT,
    "pink": BLUSH,
    "gray": (186, 178, 198),
    "silver": (216, 207, 227),
    "cyan": AQUA,
    "purple": LAVENDER,
    "blue": PERIWINKLE,
    "brown": COCOA,
    "green": SAGE,
    "red": CORAL,
    "black": (91, 70, 104),
}


def wool(color) -> Image.Image:
    img = rgba(color=color + (255,))
    d = ImageDraw.Draw(img)
    light = mix(color, WHITE, 0.35)
    dark = shade(color, 0.80)
    for y in range(16):
        for x in range(16):
            if (x + y) % 4 == 0:
                d.point((x, y), fill=light + (255,))
            elif (x - y) % 5 == 0:
                d.point((x, y), fill=dark + (255,))
    _sparkle(d, 4, 4, CREAM)
    _heart(d, 11, 11, light, size=1)
    return img


def glass() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], outline=(209, 239, 255, 255))
    d.rectangle([1, 1, 14, 14], outline=(236, 250, 255, 150))
    d.line([(3, 12), (11, 4)], fill=(255, 255, 255, 120))
    _sparkle(d, 4, 4, WHITE, size=1)
    _sparkle(d, 12, 11, (255, 241, 174), size=1)
    return img


def glass_pane_top() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.line([(0, 7), (15, 7)], fill=(210, 239, 255, 255), width=2)
    d.line([(0, 8), (15, 8)], fill=(255, 255, 255, 150))
    _sparkle(d, 4, 4, WHITE)
    _sparkle(d, 12, 11, (255, 241, 174))
    return img


def water_still() -> Image.Image:
    frames = []
    for frame in range(32):
        img = rgba(color=AQUA + (255,))
        d = ImageDraw.Draw(img)
        phase = frame / 32 * math.tau
        for y in range(16):
            for x in range(16):
                wave = math.sin((x * 0.8 + y * 0.55) + phase)
                c = mix(AQUA_DARK, (187, 243, 244), (wave + 1) / 2 * 0.7)
                d.point((x, y), fill=c + (255,))
        for x, y in [(3, 4), (11, 7), (7, 12)]:
            if (frame + x + y) % 9 < 2:
                _sparkle(d, x, y, WHITE)
        frames.append(img)
    out = Image.new("RGBA", (16, 512))
    for i, im in enumerate(frames):
        out.alpha_composite(im, (0, i * 16))
    return out


def water_flow() -> Image.Image:
    frames = []
    for frame in range(32):
        img = rgba(color=AQUA + (255,))
        d = ImageDraw.Draw(img)
        phase = frame / 32 * math.tau
        for y in range(32):
            for x in range(32):
                wave = math.sin((x - y) * 0.55 + phase) + 0.5 * math.sin((x + y) * 0.28 - phase)
                c = mix(AQUA_DARK, (190, 247, 248), (wave + 1.5) / 3 * 0.85)
                d.point((x, y), fill=c + (255,))
        for x, y in [(5, 8), (19, 15), (11, 26)]:
            if (frame + x) % 11 < 2:
                _sparkle(d, x, y, WHITE)
        frames.append(img)
    out = Image.new("RGBA", (32, 1024))
    for i, im in enumerate(frames):
        out.alpha_composite(im, (0, i * 32))
    return out


def torch_on() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.rectangle([7, 7, 8, 15], fill=(132, 91, 75, 255))
    d.line([(7, 8), (7, 15)], fill=(185, 134, 105, 255))
    d.rectangle([6, 10, 9, 11], fill=(231, 172, 113, 255))
    d.ellipse([5, 3, 10, 8], fill=(255, 190, 105, 255))
    d.ellipse([6, 4, 9, 7], fill=(255, 240, 166, 255))
    _sparkle(d, 8, 2, WHITE)
    _sparkle(d, 11, 6, (255, 226, 150))
    return img


def lantern() -> Image.Image:
    frames = []
    for frame in range(3):
        img = rgba()
        d = ImageDraw.Draw(img)
        d.rectangle([5, 0, 10, 2], fill=(115, 82, 104, 255))
        d.rectangle([4, 2, 11, 5], fill=(255, 178, 116, 255))
        d.rectangle([3, 5, 12, 14], fill=(113, 85, 132, 255))
        d.rectangle([4, 6, 11, 13], fill=(255, 205, 118, 255))
        d.rectangle([5, 7, 10, 12], fill=(255, 244, 178, 255))
        d.rectangle([6, 8, 9, 11], fill=(255, 255, 238, 255))
        d.line([(3, 14), (12, 14)], fill=(91, 68, 109, 255), width=2)
        if frame == 0:
            _sparkle(d, 8, 6, WHITE)
        elif frame == 1:
            _sparkle(d, 6, 9, WHITE)
        else:
            _sparkle(d, 10, 8, (255, 246, 198))
        frames.append(img)
    out = Image.new("RGBA", (16, 48))
    for i, im in enumerate(frames):
        out.alpha_composite(im, (0, i * 16))
    return out


def glowstone() -> Image.Image:
    img = _noise_tile(
        (255, 222, 143),
        [(255, 241, 184), (242, 192, 102), (255, 250, 214), (231, 174, 96)],
        160,
        seed=101,
    )
    d = ImageDraw.Draw(img)
    for x, y in [(3, 3), (11, 5), (7, 11), (13, 12)]:
        _sparkle(d, x, y, WHITE, size=1)
    return img


def sea_lantern() -> Image.Image:
    img = _noise_tile(
        (168, 236, 235),
        [(202, 249, 246), (133, 213, 218), (235, 255, 250), (116, 195, 204)],
        130,
        seed=111,
    )
    d = ImageDraw.Draw(img)
    for x, y in [(4, 4), (11, 4), (4, 11), (11, 11)]:
        _sparkle(d, x, y, CREAM)
    _daisy(d, 8, 8, WHITE, GOLD)
    return img


# ---------------------------------------------------------------------------
# Wood sets
# ---------------------------------------------------------------------------


WOOD_SETS = {
    "oak": {
        "bark": (143, 99, 80), "dark": (105, 70, 64), "light": (184, 132, 101),
        "wood": (211, 157, 110), "wood_light": (235, 186, 136), "wood_dark": (166, 113, 82),
        "ring": (194, 137, 99), "center": (255, 190, 148),
        "leaf": [(123, 197, 145), (151, 216, 160), (102, 177, 130), (176, 231, 177)],
        "blossom": BLUSH,
        "paths": ("log_oak", "log_oak_top", "planks_oak", "leaves_oak"),
    },
    "birch": {
        "bark": (238, 221, 196), "dark": (193, 170, 154), "light": (255, 244, 222),
        "wood": (244, 215, 171), "wood_light": (255, 235, 197), "wood_dark": (208, 175, 139),
        "ring": (219, 184, 146), "center": (255, 225, 183),
        "leaf": [(184, 224, 150), (210, 239, 172), (156, 204, 133), (230, 248, 194)],
        "blossom": PINK,
        "paths": ("log_birch", "log_birch_top", "planks_birch", "leaves_birch"),
    },
    "spruce": {
        "bark": (105, 78, 86), "dark": (74, 54, 65), "light": (139, 105, 113),
        "wood": (165, 118, 105), "wood_light": (196, 147, 129), "wood_dark": (127, 86, 80),
        "ring": (149, 101, 95), "center": (215, 169, 144),
        "leaf": [(67, 128, 112), (91, 155, 135), (52, 108, 99), (112, 178, 151)],
        "blossom": LAVENDER,
        "paths": ("log_spruce", "log_spruce_top", "planks_spruce", "leaves_spruce"),
    },
    "jungle": {
        "bark": (128, 95, 73), "dark": (94, 66, 59), "light": (170, 127, 95),
        "wood": (190, 139, 103), "wood_light": (222, 171, 126), "wood_dark": (149, 102, 80),
        "ring": (175, 120, 94), "center": (242, 187, 143),
        "leaf": [(79, 171, 126), (111, 197, 144), (64, 143, 112), (143, 218, 158)],
        "blossom": BUTTER,
        "paths": ("log_jungle", "log_jungle_top", "planks_jungle", "leaves_jungle"),
    },
    "acacia": {
        "bark": (171, 107, 77), "dark": (128, 76, 65), "light": (212, 144, 98),
        "wood": (226, 154, 101), "wood_light": (246, 183, 125), "wood_dark": (183, 116, 80),
        "ring": (209, 137, 91), "center": (255, 204, 148),
        "leaf": [(156, 196, 115), (190, 220, 142), (128, 173, 100), (214, 236, 164)],
        "blossom": CORAL,
        "paths": ("log_acacia", "log_acacia_top", "planks_acacia", "leaves_acacia"),
    },
    "dark_oak": {
        "bark": (91, 64, 63), "dark": (64, 45, 50), "light": (126, 91, 82),
        "wood": (141, 95, 80), "wood_light": (177, 126, 101), "wood_dark": (108, 72, 66),
        "ring": (127, 84, 76), "center": (201, 149, 118),
        "leaf": [(82, 137, 111), (111, 166, 129), (64, 113, 97), (139, 189, 145)],
        "blossom": PINK,
        "paths": ("log_big_oak", "log_big_oak_top", "planks_big_oak", "leaves_big_oak"),
    },
    "cherry": {
        "bark": (143, 87, 97), "dark": (109, 63, 78), "light": (184, 119, 126),
        "wood": (224, 163, 157), "wood_light": (248, 195, 183), "wood_dark": (190, 127, 128),
        "ring": (209, 140, 139), "center": (255, 211, 196),
        "leaf": [(247, 175, 194), (255, 205, 215), (226, 139, 171), (255, 226, 226)],
        "blossom": WHITE,
        "paths": ("cherry_log_side", "cherry_log_top", "cherry_planks", "cherry_leaves"),
    },
    "mangrove": {
        "bark": (122, 81, 78), "dark": (91, 58, 62), "light": (157, 108, 96),
        "wood": (190, 125, 111), "wood_light": (220, 157, 135), "wood_dark": (154, 97, 90),
        "ring": (174, 109, 102), "center": (238, 173, 145),
        "leaf": [(112, 181, 135), (143, 207, 154), (88, 155, 120), (171, 224, 172)],
        "blossom": BUTTER,
        "paths": ("mangrove_log_side", "mangrove_log_top", "mangrove_planks", "mangrove_leaves"),
    },
}


def wood_textures() -> dict[str, Image.Image]:
    out: dict[str, Image.Image] = {}
    for i, (name, spec) in enumerate(WOOD_SETS.items()):
        side, top, planks_path, leaves_path = spec["paths"]
        out[f"blocks/{side}.png"] = log_side(
            spec["bark"], spec["dark"], spec["light"], spec["center"], seed=200 + i
        )
        out[f"blocks/{top}.png"] = log_top(
            spec["wood"], spec["ring"], spec["center"], spec["bark"]
        )
        out[f"blocks/{planks_path}.png"] = planks(
            spec["wood"], spec["wood_light"], spec["wood_dark"], CREAM, seed=300 + i
        )
        out[f"blocks/{leaves_path}.png"] = leaves(
            spec["leaf"], spec["blossom"], opaque=False, seed=400 + i
        )
        out[f"blocks/{leaves_path}_opaque.png"] = leaves(
            spec["leaf"], spec["blossom"], opaque=True, seed=400 + i
        )
    return out


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


def _outline_ellipse(d, box, fill, outline=INK):
    d.ellipse(box, fill=outline + (255,))
    d.ellipse([box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1], fill=fill + (255,))


def _outline_polygon(d, pts, fill, outline=INK):
    d.polygon(pts, fill=outline + (255,))
    # Inset by moving each point toward the centroid.
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    inner = []
    for x, y in pts:
        inner.append((round(x + (cx - x) * 0.12), round(y + (cy - y) * 0.12)))
    d.polygon(inner, fill=fill + (255,))


def item_apple(golden: bool = False) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    body = GOLD if golden else CORAL
    dark = (213, 157, 70) if golden else ROSE
    _outline_ellipse(d, [2, 4, 13, 14], body)
    d.ellipse([4, 6, 11, 12], fill=mix(body, WHITE, 0.12) + (255,))
    d.point((4, 7), fill=WHITE + (255,))
    d.line([(8, 5), (8, 2)], fill=(105, 79, 61, 255), width=1)
    _leaf(d, 10, 2, MINT_DARK, outline=(74, 124, 92))
    if golden:
        _sparkle(d, 6, 9, WHITE)
        _sparkle(d, 11, 11, CREAM)
    else:
        _heart(d, 9, 10, WHITE, size=1)
    return img


def item_bread() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [1, 4, 14, 13], (224, 157, 102))
    d.ellipse([3, 5, 12, 12], fill=(247, 190, 126, 255))
    for x, y in [(4, 7), (7, 6), (10, 8)]:
        d.line([(x, y), (x + 2, y + 2)], fill=(193, 126, 86, 255))
    _sparkle(d, 11, 6, CREAM)
    return img


def item_cookie() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [2, 2, 13, 13], (176, 117, 83))
    d.ellipse([3, 3, 12, 12], fill=(214, 151, 100, 255))
    for x, y, c in [(5, 5, PINK), (9, 6, CREAM), (6, 9, BLUSH), (10, 10, PINK)]:
        d.rectangle([x, y, x + 1, y + 1], fill=c + (255,))
    return img


def item_egg() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [4, 2, 11, 14], CREAM)
    d.ellipse([5, 3, 10, 13], fill=(255, 251, 238, 255))
    for x, y in [(6, 6), (9, 8), (7, 11)]:
        d.point((x, y), fill=PINK + (255,))
    _sparkle(d, 6, 4, WHITE)
    return img


def item_gem(colors, shape: str) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    light, mid, dark = colors
    if shape == "diamond":
        pts = [(8, 1), (14, 6), (8, 15), (2, 6)]
        _outline_polygon(d, pts, mid)
        d.polygon([(8, 3), (12, 6), (8, 13), (4, 6)], fill=light + (255,))
        d.polygon([(8, 3), (8, 13), (4, 6)], fill=mix(light, WHITE, 0.35) + (255,))
        d.line([(4, 6), (12, 6)], fill=dark + (255,))
    elif shape == "emerald":
        pts = [(8, 1), (13, 5), (11, 13), (5, 15), (2, 8)]
        _outline_polygon(d, pts, mid)
        d.polygon([(8, 3), (11, 6), (9, 12), (5, 13), (4, 8)], fill=light + (255,))
    else:  # amethyst shard
        pts = [(8, 1), (13, 5), (10, 14), (5, 13), (3, 6)]
        _outline_polygon(d, pts, mid)
        d.polygon([(8, 3), (11, 6), (8, 12), (5, 11)], fill=light + (255,))
        d.line([(8, 3), (8, 12)], fill=dark + (255,))
    _sparkle(d, 6, 5, WHITE)
    return img


def item_ingot(color, dark, light) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    pts = [(2, 9), (5, 5), (14, 5), (11, 12), (2, 12)]
    _outline_polygon(d, pts, color)
    d.polygon([(4, 8), (6, 6), (12, 6), (10, 10), (4, 10)], fill=light + (255,))
    d.line([(4, 11), (11, 11)], fill=dark + (255,))
    _sparkle(d, 10, 7, WHITE)
    return img


def item_bucket(fill_color, shine=True) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.arc([3, 2, 12, 10], 180, 360, fill=INK + (255,), width=1)
    pts = [(2, 6), (13, 6), (11, 14), (4, 14)]
    _outline_polygon(d, pts, (202, 207, 224))
    d.polygon([(3, 7), (12, 7), (10, 13), (5, 13)], fill=fill_color + (255,))
    d.line([(3, 7), (12, 7)], fill=(238, 241, 249, 255))
    if shine:
        _sparkle(d, 9, 9, WHITE)
    return img


def item_bottle() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.rectangle([7, 1, 8, 3], fill=INK + (255,))
    _outline_ellipse(d, [4, 3, 11, 14], (224, 198, 161))
    d.rectangle([5, 5, 10, 13], fill=(255, 190, 93, 255))
    d.rectangle([6, 7, 9, 11], fill=(255, 225, 148, 255))
    _heart(d, 8, 9, CREAM, size=1)
    _sparkle(d, 6, 6, WHITE)
    return img


def item_wheat() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.line([(8, 15), (8, 3)], fill=(166, 132, 79, 255))
    for y in range(3, 13, 2):
        d.line([(8, y), (5, y - 1)], fill=GOLD + (255,))
        d.line([(8, y), (11, y - 1)], fill=BUTTER + (255,))
    _sparkle(d, 9, 4, WHITE)
    return img


def item_carrot() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    pts = [(6, 4), (11, 4), (9, 14), (6, 14)]
    _outline_polygon(d, pts, (245, 146, 99))
    d.polygon([(7, 5), (10, 5), (8, 12), (7, 12)], fill=(255, 180, 118, 255))
    for y in (7, 10):
        d.line([(8, y), (10, y - 1)], fill=(216, 115, 83, 255))
    for x, y in [(7, 3), (9, 2), (11, 3)]:
        _leaf(d, x, y, MINT_DARK, outline=(74, 124, 92))
    return img


def item_potato() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [3, 4, 13, 13], (214, 169, 122))
    d.ellipse([5, 5, 11, 12], fill=(235, 192, 143, 255))
    for x, y in [(6, 7), (9, 9), (8, 6)]:
        d.point((x, y), fill=(176, 126, 95, 255))
    _heart(d, 10, 11, CREAM, size=1)
    return img


def item_beetroot() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [3, 6, 12, 14], (206, 92, 133))
    d.ellipse([5, 7, 10, 13], fill=(238, 127, 160, 255))
    d.line([(8, 6), (8, 2)], fill=(99, 159, 112, 255))
    _leaf(d, 6, 3, MINT_DARK, outline=(74, 124, 92), flip=True)
    _leaf(d, 10, 2, MINT_DARK, outline=(74, 124, 92))
    return img


def item_berries() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    for x, y in [(5, 6), (9, 5), (7, 9), (11, 9)]:
        _outline_ellipse(d, [x - 1, y - 1, x + 2, y + 2], (219, 83, 119))
        d.point((x, y - 1), fill=(255, 172, 181, 255))
    _leaf(d, 8, 3, MINT_DARK, outline=(74, 124, 92))
    return img


def item_book(writable: bool = False) -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    body = PINK if writable else LAVENDER
    dark = ROSE if writable else PURPLE
    _outline_polygon(d, [(3, 2), (13, 3), (13, 14), (3, 13)], body)
    d.rectangle([3, 2, 5, 14], fill=dark + (255,))
    d.line([(6, 4), (11, 4)], fill=CREAM + (255,))
    d.line([(6, 6), (11, 6)], fill=CREAM + (255,))
    _sparkle(d, 9, 9, WHITE)
    return img


def item_paper() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_polygon(d, [(3, 1), (12, 2), (13, 14), (2, 13)], CREAM)
    d.line([(4, 4), (11, 4)], fill=CREAM_DARK + (255,))
    d.line([(4, 6), (10, 6)], fill=CREAM_DARK + (255,))
    _heart(d, 8, 10, BLUSH, size=1)
    return img


def item_flower_pot() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_polygon(d, [(3, 7), (12, 7), (11, 14), (4, 14)], (203, 129, 104))
    d.rectangle([2, 6, 13, 8], fill=(228, 151, 119, 255))
    d.line([(7, 6), (7, 3)], fill=(105, 173, 128, 255))
    _daisy(d, 7, 3, BLUSH, GOLD)
    _leaf(d, 9, 5, MINT_DARK, outline=(74, 124, 92))
    return img


def item_stick() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    d.line([(4, 12), (11, 4)], fill=INK + (255,), width=3)
    d.line([(4, 12), (11, 4)], fill=(226, 180, 130, 255), width=1)
    for x, y in [(6, 10), (8, 8), (10, 6)]:
        d.point((x, y), fill=PINK + (255,))
    _sparkle(d, 11, 3, WHITE)
    return img


def item_snowball() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [3, 3, 13, 13], SKY)
    d.ellipse([4, 4, 11, 11], fill=(237, 252, 255, 255))
    _sparkle(d, 7, 6, WHITE)
    _sparkle(d, 10, 9, (255, 255, 255))
    return img


def item_cake() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_polygon(d, [(2, 7), (14, 7), (13, 14), (3, 14)], CREAM_DARK)
    d.rectangle([3, 8, 13, 13], fill=(255, 220, 190, 255))
    d.rectangle([3, 8, 13, 10], fill=BLUSH + (255,))
    d.line([(4, 11), (12, 11)], fill=ROSE + (255,))
    _heart(d, 8, 12, CREAM, size=1)
    _sparkle(d, 11, 5, WHITE)
    return img


def item_spawn_egg() -> Image.Image:
    img = rgba()
    d = ImageDraw.Draw(img)
    _outline_ellipse(d, [4, 2, 11, 14], CREAM)
    d.ellipse([5, 3, 10, 13], fill=(255, 247, 227, 255))
    for x, y in [(6, 5), (9, 7), (7, 10), (9, 12)]:
        d.point((x, y), fill=LAVENDER + (255,))
    _sparkle(d, 7, 4, WHITE)
    return img


def item_textures() -> dict[str, Image.Image]:
    return {
        "items/apple.png": item_apple(False),
        "items/apple_golden.png": item_apple(True),
        "items/bread.png": item_bread(),
        "items/cookie.png": item_cookie(),
        "items/egg.png": item_egg(),
        "items/diamond.png": item_gem([(190, 245, 255), (128, 210, 240), (79, 155, 201)], "diamond"),
        "items/emerald.png": item_gem([(177, 248, 203), (102, 212, 153), (55, 157, 119)], "emerald"),
        "items/amethyst_shard.png": item_gem([(235, 210, 255), (181, 140, 232), (125, 87, 181)], "shard"),
        "items/gold_ingot.png": item_ingot(GOLD, (192, 137, 62), (255, 232, 157)),
        "items/iron_ingot.png": item_ingot((205, 207, 224), (150, 151, 174), (240, 242, 252)),
        "items/bucket_milk.png": item_bucket(CREAM),
        "items/bucket_water.png": item_bucket(AQUA),
        "items/honey_bottle.png": item_bottle(),
        "items/wheat.png": item_wheat(),
        "items/carrot.png": item_carrot(),
        "items/potato.png": item_potato(),
        "items/beetroot.png": item_beetroot(),
        "items/sweet_berries.png": item_berries(),
        "items/book_normal.png": item_book(False),
        "items/book_writable.png": item_book(True),
        "items/paper.png": item_paper(),
        "items/flower_pot.png": item_flower_pot(),
        "items/stick.png": item_stick(),
        "items/snowball.png": item_snowball(),
        "items/cake.png": item_cake(),
        "items/spawn_egg.png": item_spawn_egg(),
    }


# ---------------------------------------------------------------------------
# Sky
# ---------------------------------------------------------------------------


def sun_texture() -> Image.Image:
    img = rgba(32, 32)
    d = ImageDraw.Draw(img)
    cx = cy = 16
    for i in range(12):
        angle = i * math.tau / 12
        x0 = cx + math.cos(angle) * 11
        y0 = cy + math.sin(angle) * 11
        x1 = cx + math.cos(angle) * 15
        y1 = cy + math.sin(angle) * 15
        d.line([(x0, y0), (x1, y1)], fill=(255, 226, 146, 255), width=2)
    d.ellipse([4, 4, 27, 27], fill=(255, 211, 116, 255))
    d.ellipse([5, 5, 26, 26], fill=(255, 238, 170, 255))
    d.ellipse([6, 6, 25, 25], fill=(255, 249, 210, 255))
    # Sleepy-happy face.
    d.arc([9, 12, 14, 17], 20, 160, fill=(196, 127, 91, 255), width=1)
    d.arc([17, 12, 22, 17], 20, 160, fill=(196, 127, 91, 255), width=1)
    d.arc([12, 17, 20, 23], 20, 160, fill=(214, 130, 126, 255), width=1)
    d.ellipse([8, 17, 11, 19], fill=(255, 174, 174, 180))
    d.ellipse([20, 17, 23, 19], fill=(255, 174, 174, 180))
    _sparkle(d, 6, 7, WHITE, size=1)
    return img


def moon_phases() -> Image.Image:
    out = rgba(128, 64)
    # Eight 32x32 phase cells, four columns by two rows.
    offsets = [None, 7, 11, 14, 16, 14, 11, 7]
    for i, offset in enumerate(offsets):
        cell = rgba(32, 32)
        d = ImageDraw.Draw(cell)
        # Stars in the transparent corners.
        for x, y in [(4, 5), (26, 7), (7, 25), (24, 24)]:
            _sparkle(d, x, y, (255, 244, 198), size=1)
        moon = rgba(32, 32)
        md = ImageDraw.Draw(moon)
        md.ellipse([5, 4, 26, 25], fill=(255, 242, 201, 255))
        md.ellipse([7, 6, 24, 23], fill=(255, 251, 226, 255))
        # Craters and sleepy face.
        for x, y, r in [(11, 10, 2), (20, 14, 2), (14, 20, 1), (22, 21, 1)]:
            md.ellipse([x - r, y - r, x + r, y + r], fill=(235, 218, 177, 255))
        md.arc([10, 12, 14, 16], 20, 160, fill=(177, 143, 112, 255), width=1)
        md.arc([18, 12, 22, 16], 20, 160, fill=(177, 143, 112, 255), width=1)
        md.arc([14, 17, 19, 21], 20, 160, fill=(196, 158, 126, 255), width=1)
        if offset is not None:
            # Erase a shifted circle to create the phase, leaving a faint rim.
            mask = Image.new("L", (32, 32), 255)
            ed = ImageDraw.Draw(mask)
            ed.ellipse([5 + offset, 4 - 1, 26 + offset, 25 - 1], fill=0)
            moon.putalpha(Image.composite(moon.getchannel("A"), Image.new("L", (32, 32), 0), mask))
            md = ImageDraw.Draw(moon)
            md.arc([5, 4, 26, 25], 0, 360, fill=(238, 211, 167, 255), width=1)
        cell.alpha_composite(moon)
        out.alpha_composite(cell, ((i % 4) * 32, (i // 4) * 32))
    return out


def clouds_texture() -> Image.Image:
    img = rgba(256, 256)
    d = ImageDraw.Draw(img)
    r = rng(701)
    colors = [(255, 231, 241), (255, 246, 229), (230, 220, 255)]
    for _ in range(18):
        cx, cy = r.randrange(256), r.randrange(256)
        color = r.choice(colors)
        w = r.randrange(26, 62)
        h = r.randrange(10, 22)
        for dx, dy, ww, hh in [
            (0, 0, w, h),
            (-w // 3, -h // 2, w // 2, h),
            (w // 3, -h // 3, w // 2, h),
            (0, h // 3, w // 2, h // 2),
        ]:
            for ox in (-256, 0, 256):
                for oy in (-256, 0, 256):
                    x0 = cx + dx + ox - ww // 2
                    y0 = cy + dy + oy - hh // 2
                    d.ellipse([x0, y0, x0 + ww, y0 + hh], fill=color + (255,))
    return img


# ---------------------------------------------------------------------------
# Entity recolours
# ---------------------------------------------------------------------------


def _recolour(src: Path, mapping, seed: int = 0) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    out = Image.new("RGBA", im.size)
    src_px = im.load()
    out_px = out.load()
    r = rng(seed)
    for y in range(im.height):
        for x in range(im.width):
            cr, cg, cb, ca = src_px[x, y]
            if ca == 0:
                continue
            best = None
            best_d = 1e9
            for s, t in mapping:
                dist = (cr - s[0]) ** 2 + (cg - s[1]) ** 2 + (cb - s[2]) ** 2
                if dist < best_d:
                    best_d = dist
                    best = (s, t)
            assert best is not None
            s, t = best
            lum_s = (s[0] * 0.299 + s[1] * 0.587 + s[2] * 0.114) / 255.0
            lum_c = (cr * 0.299 + cg * 0.587 + cb * 0.114) / 255.0
            ratio = max(0.70, min(1.28, (lum_c + 0.06) / (lum_s + 0.06)))
            nr = max(0, min(255, round(t[0] * ratio)))
            ng = max(0, min(255, round(t[1] * ratio)))
            nb = max(0, min(255, round(t[2] * ratio)))
            out_px[x, y] = (nr, ng, nb, ca)
    # A few tiny heart freckles, placed in safe corner areas of each atlas.
    d = ImageDraw.Draw(out)
    for _ in range(3):
        x = r.randrange(2, max(3, im.width - 4))
        y = r.randrange(2, max(3, im.height - 4))
        if out.getpixel((x, y))[3] > 0:
            _heart(d, x, y, CREAM, size=1)
    return out


ENTITY_RECIPES = {
    "entity/cow/cow.png": (
        "cow/cow.png",
        [
            ((245, 245, 245), CREAM), ((25, 25, 25), ROSE),
            ((120, 120, 120), LAVENDER), ((95, 65, 45), PEACH),
            ((215, 160, 160), BLUSH),
        ],
    ),
    "entity/cow/cow_v2.png": (
        "cow/cow_v2.png",
        [
            ((245, 245, 245), CREAM), ((25, 25, 25), ROSE),
            ((120, 120, 120), LAVENDER), ((95, 65, 45), PEACH),
            ((215, 160, 160), BLUSH),
        ],
    ),
    "entity/pig/pig.png": (
        "pig/pig.png",
        [
            ((242, 170, 170), BLUSH), ((190, 105, 105), ROSE),
            ((25, 25, 25), PLUM), ((245, 245, 245), CREAM),
        ],
    ),
    "entity/pig/pig_v3.png": (
        "pig/pig_v3.png",
        [
            ((242, 170, 170), BLUSH), ((190, 105, 105), ROSE),
            ((25, 25, 25), PLUM), ((245, 245, 245), CREAM),
        ],
    ),
    "entity/chicken/chicken.png": (
        "chicken/chicken.png",
        [
            ((245, 245, 245), CREAM), ((210, 45, 45), CORAL),
            ((235, 195, 55), BUTTER), ((120, 120, 120), LAVENDER),
            ((25, 25, 25), PLUM),
        ],
    ),
    "entity/bee/bee.png": (
        "bee/bee.png",
        [
            ((235, 195, 55), BUTTER), ((25, 25, 25), PLUM),
            ((245, 245, 245), CREAM), ((180, 190, 210), LAVENDER),
        ],
    ),
    "entity/bee/bee_nectar.png": (
        "bee/bee_nectar.png",
        [
            ((235, 195, 55), BUTTER), ((25, 25, 25), PLUM),
            ((245, 245, 245), CREAM), ((180, 190, 210), LAVENDER),
        ],
    ),
    "entity/sheep/sheep.tga": (
        "sheep/sheep.tga",
        [
            ((245, 245, 245), CREAM), ((220, 175, 175), BLUSH),
            ((95, 65, 45), COCOA), ((120, 120, 120), LAVENDER),
        ],
    ),
    "entity/rabbit/rabbit_white.png": (
        "rabbit/rabbit_white.png",
        [
            ((245, 245, 245), CREAM), ((220, 175, 175), BLUSH),
            ((95, 65, 45), COCOA),
        ],
    ),
    "entity/rabbit/rabbit_brown.png": (
        "rabbit/rabbit_brown.png",
        [
            ((120, 85, 60), PEACH), ((80, 55, 45), COCOA),
            ((245, 245, 245), CREAM), ((220, 175, 175), BLUSH),
        ],
    ),
}


def entity_textures() -> dict[str, Image.Image]:
    out = {}
    for i, (dest, (src, mapping)) in enumerate(ENTITY_RECIPES.items()):
        out[dest] = _recolour(VANILLA_ENTITY / src, mapping, seed=800 + i)
    return out


# ---------------------------------------------------------------------------
# Pack icon
# ---------------------------------------------------------------------------


def pack_icon() -> Image.Image:
    size = 256
    img = Image.new("RGBA", (size, size), (255, 244, 249, 255))
    d = ImageDraw.Draw(img)
    # Soft vertical sky gradient.
    for y in range(size):
        t = y / (size - 1)
        c = mix((208, 240, 255), (255, 224, 236), t)
        d.line([(0, y), (size, y)], fill=c + (255,))
    # A large smiling flower.
    cx, cy = 128, 134
    for i in range(8):
        angle = i * math.tau / 8
        px = cx + math.cos(angle) * 58
        py = cy + math.sin(angle) * 58
        d.ellipse([px - 34, py - 34, px + 34, py + 34], fill=(255, 176, 198, 255))
        d.ellipse([px - 28, py - 28, px + 28, py + 28], fill=(255, 211, 222, 255))
    d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], fill=(255, 228, 151, 255))
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=(255, 244, 196, 255))
    d.arc([cx - 22, cy - 12, cx - 4, cy + 8], 20, 160, fill=(178, 108, 86, 255), width=4)
    d.arc([cx + 4, cy - 12, cx + 22, cy + 8], 20, 160, fill=(178, 108, 86, 255), width=4)
    d.arc([cx - 16, cy + 4, cx + 16, cy + 30], 20, 160, fill=(214, 112, 126, 255), width=4)
    d.ellipse([cx - 32, cy + 6, cx - 18, cy + 18], fill=(255, 155, 171, 180))
    d.ellipse([cx + 18, cy + 6, cx + 32, cy + 18], fill=(255, 155, 171, 180))
    # Stars and a little rainbow arc.
    for x, y, r in [(38, 48, 12), (212, 62, 9), (198, 204, 7), (54, 208, 6)]:
        d.polygon(_star_points(x, y, r, r * 0.42), fill=(255, 248, 201, 255))
    d.arc([36, 186, 220, 330], 200, 340, fill=(255, 255, 255, 130), width=8)
    # Rounded frame.
    d.rounded_rectangle([5, 5, size - 6, size - 6], radius=30, outline=(255, 255, 255, 230), width=6)
    return img


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_textures() -> dict[str, Image.Image]:
    textures: dict[str, Image.Image] = {}

    # Ground and stone.
    textures["blocks/grass_top.png"] = grass_top()
    textures["blocks/grass_side.png"] = grass_side()
    textures["blocks/grass_side_carried.png"] = grass_side()
    textures["blocks/dirt.png"] = dirt()
    textures["blocks/stone.png"] = stone()
    textures["blocks/cobblestone.png"] = cobblestone()
    textures["blocks/sand.png"] = sand()

    # Wood, leaves and blossoms.
    textures.update(wood_textures())

    # Flowers and plants.
    textures["blocks/flower_dandelion.png"] = flower_sprite(BUTTER, GOLD, CREAM, "daisy", 1001)
    textures["blocks/flower_rose.png"] = flower_sprite(CORAL, ROSE, CREAM, "rose", 1002)
    textures["blocks/flower_allium.png"] = flower_sprite(LAVENDER, PURPLE, CREAM, "ball", 1003)
    textures["blocks/flower_blue_orchid.png"] = flower_sprite(SKY, BLUE, CREAM, "star", 1004)
    textures["blocks/flower_cornflower.png"] = flower_sprite(BLUE, PERIWINKLE, CREAM, "star", 1005)
    textures["blocks/flower_oxeye_daisy.png"] = flower_sprite(WHITE, CREAM_DARK, GOLD, "daisy", 1006)
    textures["blocks/flower_tulip_pink.png"] = flower_sprite(BLUSH, PINK, CREAM, "tulip", 1007)
    textures["blocks/flower_tulip_red.png"] = flower_sprite(CORAL, ROSE, CREAM, "tulip", 1008)
    textures["blocks/flower_tulip_orange.png"] = flower_sprite(PEACH, CORAL, CREAM, "tulip", 1009)
    textures["blocks/flower_tulip_white.png"] = flower_sprite(CREAM, CREAM_DARK, GOLD, "tulip", 1010)
    textures["blocks/flower_lily_of_the_valley.png"] = flower_sprite(CREAM, CREAM_DARK, GOLD, "bell", 1011)
    textures["blocks/flower_houstonia.png"] = flower_sprite(SKY, BLUE, CREAM, "tiny", 1012)
    textures["blocks/flower_paeonia.png"] = flower_sprite(BLUSH, PINK, CREAM, "ball", 1013)
    textures["blocks/flower_wither_rose.png"] = flower_sprite(PLUM, INK, LAVENDER, "rose", 1014)
    textures["blocks/flower_rose_blue.png"] = flower_sprite(BLUE, PERIWINKLE, CREAM, "star", 1015)
    textures["blocks/tallgrass.png"] = tallgrass()
    textures["blocks/double_plant_sunflower_front.png"] = sunflower_head(False)
    textures["blocks/double_plant_sunflower_back.png"] = sunflower_head(True)
    textures["blocks/double_plant_sunflower_top.png"] = sunflower_stem(True)
    textures["blocks/double_plant_sunflower_bottom.png"] = sunflower_stem(False)

    # Wool, glass, water and lights.
    for name, color in WOOL_COLORS.items():
        textures[f"blocks/wool_colored_{name}.png"] = wool(color)
    textures["blocks/glass.png"] = glass()
    textures["blocks/glass_pane_top.png"] = glass_pane_top()
    textures["blocks/water_still.png"] = water_still()
    textures["blocks/water_flow.png"] = water_flow()
    textures["blocks/torch_on.png"] = torch_on()
    textures["blocks/lantern.png"] = lantern()
    textures["blocks/glowstone.png"] = glowstone()
    textures["blocks/sea_lantern.png"] = sea_lantern()

    # Items.
    textures.update(item_textures())

    # Sky.
    textures["environment/sun.png"] = sun_texture()
    textures["environment/moon_phases.png"] = moon_phases()
    textures["environment/clouds.png"] = clouds_texture()

    # Friendly animal recolours.
    textures.update(entity_textures())

    return textures
