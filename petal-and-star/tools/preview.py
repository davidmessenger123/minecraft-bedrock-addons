"""
Offline previews for Petal & Star.

The block previews are small isometric renders built by sampling the same
16x16 textures that Minecraft loads.  They are colour/shape checks, not
in-game screenshots.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RP = ROOT / "resource_pack"
OUT = ROOT / "preview"

FACE_CORNERS = {
    "up": ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    "west": ((-1, 0, 0), [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)]),
    "north": ((0, 0, -1), [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
}
SHADE = {"up": 1.12, "west": 0.84, "north": 0.97}
_D = (-1.0, 1.0, -1.0)


def project(p, scale: float):
    x, y, z = p
    sx = (-x + z) * 0.70710678 * scale
    sy = -(x + 2.0 * y + z) * 0.40824829 * scale
    return sx, sy


def depth(p):
    x, y, z = p
    return -x + y - z


def visible(normal):
    return normal[0] * _D[0] + normal[1] * _D[1] + normal[2] * _D[2] > 0


def load_tex(path: str) -> Image.Image:
    img = Image.open(RP / "textures" / path).convert("RGBA")
    if img.size != (16, 16):
        img = img.crop((0, 0, 16, 16))
    return img


def _face_texture(block: dict, face: str) -> Image.Image:
    if face == "up":
        return load_tex(block.get("top", block["side"]))
    return load_tex(block.get("side", block["top"]))


def render_cubes(blocks: list[dict], size: tuple[int, int] = (900, 500), margin: float = 0.86) -> Image.Image:
    faces = []
    for block in blocks:
        ox, oy, oz = block.get("origin", (0, 0, 0))
        for face, (normal, corners) in FACE_CORNERS.items():
            if not visible(normal):
                continue
            tex = _face_texture(block, face)
            pts3 = []
            for cx, cy, cz in corners:
                pts3.append((ox + cx, oy + cy, oz + cz))
            # Sample every texture pixel as a tiny quad.
            for gy in range(16):
                for gx in range(16):
                    r, g, b, a = tex.getpixel((gx, gy))
                    if a < 24:
                        continue
                    alpha = a
                    if block.get("alpha") is not None:
                        alpha = int(alpha * block["alpha"])
                    s0, s1 = gx / 16, (gx + 1) / 16
                    t0, t1 = gy / 16, (gy + 1) / 16
                    cell = []
                    for s, t in ((s0, t0), (s1, t0), (s1, t1), (s0, t1)):
                        x = (1 - s) * (1 - t) * pts3[0][0] + s * (1 - t) * pts3[1][0] + s * t * pts3[2][0] + (1 - s) * t * pts3[3][0]
                        y = (1 - s) * (1 - t) * pts3[0][1] + s * (1 - t) * pts3[1][1] + s * t * pts3[2][1] + (1 - s) * t * pts3[3][1]
                        z = (1 - s) * (1 - t) * pts3[0][2] + s * (1 - t) * pts3[1][2] + s * t * pts3[2][2] + (1 - s) * t * pts3[3][2]
                        cell.append((x, y, z))
                    f = SHADE[face]
                    color = (
                        min(255, int(r * f)),
                        min(255, int(g * f)),
                        min(255, int(b * f)),
                        alpha,
                    )
                    faces.append((sum(depth(p) for p in cell) / 4, cell, color))

    if not faces:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    all_pts = [p for _d, pts, _c in faces for p in pts]
    proj = [project(p, 1.0) for p in all_pts]
    min_x, max_x = min(p[0] for p in proj), max(p[0] for p in proj)
    min_y, max_y = min(p[1] for p in proj), max(p[1] for p in proj)
    scale = min(
        size[0] * margin / max(1e-6, max_x - min_x),
        size[1] * margin / max(1e-6, max_y - min_y),
    )
    off_x = size[0] / 2 - (min_x + max_x) / 2 * scale
    off_y = size[1] / 2 - (min_y + max_y) / 2 * scale

    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    faces.sort(key=lambda item: item[0])
    for _d, pts, color in faces:
        sp = [project(p, scale) for p in pts]
        sp = [(x + off_x, y + off_y) for x, y in sp]
        d.polygon(sp, fill=color)
    return img


def block(top: str, side: str, origin=(0, 0, 0), bottom: str | None = None, alpha: float | None = None) -> dict:
    b = {"top": top, "side": side, "origin": origin}
    if bottom is not None:
        b["bottom"] = bottom
    if alpha is not None:
        b["alpha"] = alpha
    return b


def _card(size: tuple[int, int], color=(255, 255, 255, 255), radius: int = 22) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 4, size[0] - 3, size[1] - 3], radius=radius, fill=(201, 181, 210, 70))
    d.rounded_rectangle([0, 0, size[0] - 4, size[1] - 6], radius=radius, fill=color)
    return img


def _font(size: int, bold: bool = False):
    name = "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"
    for base in (Path("/usr/share/fonts/liberation"), Path("/usr/share/fonts/truetype/liberation")):
        path = base / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def _center_text(d: ImageDraw.ImageDraw, box, text: str, font, fill):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), text, font=font)
    d.text((x0 + (x1 - x0 - (bb[2] - bb[0])) / 2, y0 + (y1 - y0 - (bb[3] - bb[1])) / 2, ), text, font=font, fill=fill)


def _star(d: ImageDraw.ImageDraw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((round(cx + math.cos(a) * rr), round(cy + math.sin(a) * rr)))
    d.polygon(pts, fill=fill)


def block_card(top: str, side: str, label: str, size=164, alpha: float | None = None) -> Image.Image:
    card = _card((size, size + 34))
    cube = render_cubes([block(top, side, alpha=alpha)], (size - 16, size - 8), margin=0.82)
    # Soft shadow.
    d = ImageDraw.Draw(card)
    d.ellipse([size * 0.22, size * 0.73, size * 0.78, size * 0.88], fill=(119, 91, 139, 35))
    card.alpha_composite(cube, (8, 0))
    d = ImageDraw.Draw(card)
    _center_text(d, (0, size - 2, size, size + 30), label, _font(15, True), (78, 58, 92))
    return card


def sprite_card(path: str, label: str, size=142, scale: int = 6) -> Image.Image:
    card = _card((size, size + 32), (255, 255, 255, 255))
    tex = Image.open(RP / "textures" / path).convert("RGBA")
    if tex.size != (16, 16):
        tex = tex.crop((0, 0, 16, 16))
    tex = tex.resize((16 * scale, 16 * scale), Image.NEAREST)
    x = (size - tex.width) // 2
    y = (size - tex.height) // 2
    card.alpha_composite(tex, (x, y))
    d = ImageDraw.Draw(card)
    _center_text(d, (0, size - 1, size, size + 28), label, _font(14, True), (78, 58, 92))
    return card


def face_card(texture_path: str, uv: tuple[int, int, int, int], label: str, size=142, scale: int = 10) -> Image.Image:
    card = _card((size, size + 32), (255, 255, 255, 255))
    tex = Image.open(RP / "textures" / texture_path).convert("RGBA")
    face = tex.crop((uv[0], uv[1], uv[0] + uv[2], uv[1] + uv[3]))
    face = face.resize((uv[2] * scale, uv[3] * scale), Image.NEAREST)
    x = (size - face.width) // 2
    y = (size - face.height) // 2
    card.alpha_composite(face, (x, y))
    d = ImageDraw.Draw(card)
    _center_text(d, (0, size - 1, size, size + 28), label, _font(14, True), (78, 58, 92))
    return card


def image_card(path: str, label: str, size=116, crop=None, scale: int = 4, bg=(255, 255, 255, 255)) -> Image.Image:
    card = _card((size, size + 32), bg)
    tex = Image.open(RP / "textures" / path).convert("RGBA")
    if crop is not None:
        tex = tex.crop(crop)
    # Fit the source into the card without stretching it.
    fit = min((size - 16) / tex.width, (size - 16) / tex.height)
    nw, nh = max(1, round(tex.width * fit)), max(1, round(tex.height * fit))
    tex = tex.resize((nw, nh), Image.NEAREST)
    card.alpha_composite(tex, ((size - nw) // 2, (size - nh) // 2))
    d = ImageDraw.Draw(card)
    _center_text(d, (0, size - 1, size, size + 28), label, _font(14, True), (78, 58, 92))
    return card


def gradient_background(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        c = (
            round(255 * (1 - t) + 255 * t),
            round(238 * (1 - t) + 223 * t),
            round(249 * (1 - t) + 240 * t),
        )
        d.line([(0, y), (w, y)], fill=c + (255,))
    return img


def hero_scene() -> Image.Image:
    blocks = []
    for x in range(3):
        for z in range(2):
            if (x, z) == (0, 0):
                continue
            blocks.append(block("blocks/grass_top.png", "blocks/grass_side.png", (x, 0, z)))
    # A little tree.
    blocks.append(block("blocks/log_oak_top.png", "blocks/log_oak.png", (1, 1, 0)))
    for x, y, z in [
        (1, 2, 0), (0, 2, 0), (2, 2, 0), (1, 2, 1),
        (1, 3, 0), (0, 3, 0), (2, 3, 0), (1, 3, 1),
    ]:
        blocks.append(block("blocks/leaves_oak.png", "blocks/leaves_oak.png", (x, y, z)))
    # A cushion and a tiny pond.
    blocks.append(block("blocks/wool_colored_pink.png", "blocks/wool_colored_pink.png", (0, 1, 1)))
    blocks.append(block("blocks/water_still.png", "blocks/water_still.png", (0, 0, 0), alpha=0.82))
    return render_cubes(blocks, (1040, 430), margin=0.86)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()

    # Individual section previews.
    hero = hero_scene()
    hero.save(OUT / "hero.png")

    # Contact sheet.
    W = 1200
    H = 2250
    sheet = gradient_background((W, H))
    d = ImageDraw.Draw(sheet)

    # Header.
    d.text((70, 52), "Petal & Star", font=_font(72, True), fill=(92, 65, 104))
    d.text((73, 132), "A soft, whimsical texture pack for Minecraft Bedrock", font=_font(25), fill=(125, 92, 128))
    d.text((73, 166), "130 soft pastel textures  ·  flowers, stars, and friendly animals", font=_font(17), fill=(154, 119, 153))
    _star(d, 1030, 80, 22, (255, 215, 143, 255))
    _star(d, 1080, 125, 12, (255, 185, 204, 255))
    _star(d, 955, 145, 10, (207, 184, 255, 255))

    # Hero panel.
    panel = _card((1060, 440), (255, 255, 255, 235), radius=30)
    sheet.alpha_composite(panel, (70, 205))
    sheet.alpha_composite(hero, (80, 210))
    d = ImageDraw.Draw(sheet)
    d.text((96, 226), "A little garden at golden hour", font=_font(17, True), fill=(143, 105, 145))

    # Blocks.
    y = 690
    d.text((70, y), "Blocks", font=_font(34, True), fill=(92, 65, 104))
    d.line([(70, y + 45), (1130, y + 45)], fill=(226, 190, 213, 255), width=2)
    y += 64
    blocks = [
        ("blocks/grass_top.png", "blocks/grass_side.png", "Grass"),
        ("blocks/dirt.png", "blocks/dirt.png", "Dirt"),
        ("blocks/stone.png", "blocks/stone.png", "Stone"),
        ("blocks/cobblestone.png", "blocks/cobblestone.png", "Cobblestone"),
        ("blocks/sand.png", "blocks/sand.png", "Sand"),
        ("blocks/log_oak_top.png", "blocks/log_oak.png", "Oak log"),
        ("blocks/planks_oak.png", "blocks/planks_oak.png", "Oak planks"),
        ("blocks/leaves_oak.png", "blocks/leaves_oak.png", "Oak leaves"),
        ("blocks/log_birch_top.png", "blocks/log_birch.png", "Birch log"),
        ("blocks/cherry_leaves.png", "blocks/cherry_leaves.png", "Cherry leaves"),
        ("blocks/wool_colored_pink.png", "blocks/wool_colored_pink.png", "Pink wool"),
        ("blocks/wool_colored_light_blue.png", "blocks/wool_colored_light_blue.png", "Sky wool"),
        ("blocks/wool_colored_lime.png", "blocks/wool_colored_lime.png", "Mint wool"),
        ("blocks/glass.png", "blocks/glass.png", "Glass"),
        ("blocks/water_still.png", "blocks/water_still.png", "Water"),
        ("blocks/glowstone.png", "blocks/glowstone.png", "Glowstone"),
        ("blocks/sea_lantern.png", "blocks/sea_lantern.png", "Sea lantern"),
        ("blocks/cherry_planks.png", "blocks/cherry_planks.png", "Cherry planks"),
    ]
    for i, (top, side, label) in enumerate(blocks):
        x = 70 + (i % 6) * 174
        yy = y + (i // 6) * 206
        sheet.alpha_composite(block_card(top, side, label), (x, yy))

    # Flowers.
    y = 1405
    d = ImageDraw.Draw(sheet)
    d.text((70, y), "Flowers & plants", font=_font(34, True), fill=(92, 65, 104))
    d.line([(70, y + 45), (1130, y + 45)], fill=(226, 190, 213, 255), width=2)
    y += 64
    flowers = [
        ("blocks/flower_dandelion.png", "Dandelion"),
        ("blocks/flower_rose.png", "Poppy"),
        ("blocks/flower_allium.png", "Allium"),
        ("blocks/flower_blue_orchid.png", "Blue orchid"),
        ("blocks/flower_oxeye_daisy.png", "Daisy"),
        ("blocks/flower_tulip_pink.png", "Pink tulip"),
        ("blocks/tallgrass.png", "Tall grass"),
        ("blocks/double_plant_sunflower_front.png", "Sunflower"),
    ]
    for i, (path, label) in enumerate(flowers):
        x = 70 + (i % 8) * 132
        sheet.alpha_composite(sprite_card(path, label, size=116, scale=5), (x, y))

    # Items.
    y = 1660
    d = ImageDraw.Draw(sheet)
    d.text((70, y), "Little treasures", font=_font(34, True), fill=(92, 65, 104))
    d.line([(70, y + 45), (1130, y + 45)], fill=(226, 190, 213, 255), width=2)
    y += 64
    items = [
        ("items/apple.png", "Apple"),
        ("items/apple_golden.png", "Golden apple"),
        ("items/diamond.png", "Diamond"),
        ("items/emerald.png", "Emerald"),
        ("items/cookie.png", "Cookie"),
        ("items/honey_bottle.png", "Honey"),
        ("items/bucket_milk.png", "Milk"),
        ("items/cake.png", "Cake"),
    ]
    for i, (path, label) in enumerate(items):
        x = 70 + (i % 8) * 132
        sheet.alpha_composite(sprite_card(path, label, size=116, scale=5), (x, y))

    # Sky and friendly faces.
    y = 1915
    d = ImageDraw.Draw(sheet)
    d.text((70, y), "Sky & friends", font=_font(34, True), fill=(92, 65, 104))
    d.line([(70, y + 45), (1130, y + 45)], fill=(226, 190, 213, 255), width=2)
    y += 64
    sky_cards = [
        image_card("environment/sun.png", "Sun", size=116),
        image_card("environment/moon_phases.png", "Moon", size=116, crop=(0, 0, 32, 32)),
        image_card("environment/clouds.png", "Clouds", size=116, bg=(198, 232, 250, 255)),
    ]
    for i, card in enumerate(sky_cards):
        sheet.alpha_composite(card, (70 + i * 132, y))
    animal_cards = [
        face_card("entity/cow/cow.png", (6, 6, 8, 8), "Cow"),
        face_card("entity/pig/pig.png", (8, 8, 8, 8), "Pig"),
        face_card("entity/chicken/chicken.png", (3, 3, 4, 6), "Chicken"),
    ]
    for i, card in enumerate(animal_cards):
        sheet.alpha_composite(card, (70 + (i + 3) * 132, y))
    d.text(
        (70 + 6 * 132, y + 42),
        "also: sheep, rabbit & bee",
        font=_font(13, True),
        fill=(151, 117, 150),
    )

    # Footer.
    d = ImageDraw.Draw(sheet)
    d.text((70, H - 44), "Textures shown at 5–10×; Minecraft uses 16×16 pixels. No scripts, no experiments.", font=_font(14), fill=(151, 117, 150))

    sheet.convert("RGB").save(OUT / "_contact_sheet.png")
    # Handy standalone icon for the README.
    Image.open(RP / "pack_icon.png").save(OUT / "pack_icon.png")
    print(f"rendered previews -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
