"""Isometric previews of the Cogworks block models.

This is deliberately a small painter's-algorithm renderer: it reads the same
Bedrock geometry and atlas that the add-on ships, so a texture or geometry
mistake shows up in the repository preview as well as in game.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

import content

BG = (21, 25, 31)
INK = (240, 235, 222)
MUTED = (175, 184, 193)
GRID = (34, 40, 48)
CARD = (30, 36, 44)
FACE_ORDER = ("north", "south", "east", "west", "up", "down")
FACE_LIGHT = {
    "north": 0.80,
    "south": 0.69,
    "east": 0.72,
    "west": 0.87,
    "up": 1.05,
    "down": 0.56,
}

CAPTIONS = {
    "generator": ("Coal Generator", "fuel + 2,000 E buffer"),
    "cable": ("Copper Cable", "links the power network"),
    "battery": ("Battery Bank", "5,000 E storage"),
    "conveyor": ("Conveyor Belt", "virtual stack transport"),
    "assembler": ("Crafting Assembler", "recipes + energy"),
    "storage_core": ("Storage Core", "8 slots, expandable"),
    "storage_extension": ("Storage Extension", "+8 slots"),
    "quarry": ("Quarry Controller", "surveyor-defined excavation"),
}


def font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/liberation/LiberationSans-%s.ttf" % ("Bold" if bold else "Regular"),
        "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf" % ("Bold" if bold else "Regular"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def checker(size: int, cell: int = 12) -> Image.Image:
    image = Image.new("RGBA", (size, size), GRID)
    draw = ImageDraw.Draw(image)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(38, 45, 54, 255))
    return image


def average_texture_color(texture: Image.Image, rect: Sequence[int]) -> tuple[int, int, int, int]:
    x, y, w, h = (int(v) for v in rect)
    x = max(0, min(texture.width - 1, x))
    y = max(0, min(texture.height - 1, y))
    w = max(1, min(texture.width - x, w))
    h = max(1, min(texture.height - y, h))
    crop = texture.crop((x, y, x + w, y + h)).convert("RGBA")
    pixels = list(crop.getdata())
    opaque = [p for p in pixels if p[3] >= 20]
    if not opaque:
        return (0, 0, 0, 0)
    n = len(opaque)
    return (
        sum(p[0] for p in opaque) // n,
        sum(p[1] for p in opaque) // n,
        sum(p[2] for p in opaque) // n,
        sum(p[3] for p in opaque) // n,
    )


def cube_faces(origin: Sequence[float], size: Sequence[float]) -> dict[str, list[tuple[float, float, float]]]:
    x0, y0, z0 = (float(v) for v in origin)
    x1, y1, z1 = x0 + float(size[0]), y0 + float(size[1]), z0 + float(size[2])
    return {
        "north": [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
        "south": [(x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1)],
        "east": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
        "west": [(x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)],
        "up": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "down": [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
    }


def project(point: Sequence[float], size: int, bounds, scale: float,
            yaw: float, pitch: float) -> tuple[float, float, float]:
    x, y, z = point
    x1 = x * math.cos(yaw) - z * math.sin(yaw)
    z1 = x * math.sin(yaw) + z * math.cos(yaw)
    y2 = y * math.cos(pitch) - z1 * math.sin(pitch)
    z2 = y * math.sin(pitch) + z1 * math.cos(pitch)
    return ((x1 - bounds[0]) * scale + 12, size - 16 - (y2 - bounds[1]) * scale, z2)


def model_image(geometry: dict, texture: Image.Image, label: str, caption: str,
                size: int = 230) -> Image.Image:
    entry = geometry["minecraft:geometry"][0]
    cubes = []
    for bone in entry.get("bones", []):
        for index, cube in enumerate(bone.get("cubes", [])):
            cubes.append(cube)

    yaw = math.radians(38)
    pitch = math.radians(24)
    transformed = []
    all_points = []
    for cube in cubes:
        faces = cube_faces(cube["origin"], cube["size"])
        for points in faces.values():
            all_points.extend(points)
        transformed.append((cube, faces))

    if not all_points:
        return Image.new("RGBA", (size, size), BG)

    projected = []
    for point in all_points:
        x, y, z = point
        x1 = x * math.cos(yaw) - z * math.sin(yaw)
        z1 = x * math.sin(yaw) + z * math.cos(yaw)
        y2 = y * math.cos(pitch) - z1 * math.sin(pitch)
        z2 = y * math.sin(pitch) + z1 * math.cos(pitch)
        projected.append((x1, y2, z2))
    min_x = min(p[0] for p in projected)
    max_x = max(p[0] for p in projected)
    min_y = min(p[1] for p in projected)
    max_y = max(p[1] for p in projected)
    span = max(max_x - min_x, max_y - min_y, 1.0)
    scale = (size - 46) / span
    bounds = (min_x, min_y, max_x, max_y)

    canvas = checker(size)
    draw = ImageDraw.Draw(canvas)
    faces_to_draw = []
    for cube, faces in transformed:
        for face_name in FACE_ORDER:
            points = faces[face_name]
            face_uv = cube.get("uv", {}).get(face_name)
            if not face_uv:
                continue
            color = average_texture_color(
                texture,
                [face_uv["uv"][0], face_uv["uv"][1], face_uv["uv_size"][0], face_uv["uv_size"][1]],
            )
            if color[3] < 22:
                continue
            coords = [project(p, size, bounds, scale, yaw, pitch) for p in points]
            depth = sum(p[2] for p in coords) / 4.0
            faces_to_draw.append((depth, face_name, [(p[0], p[1]) for p in coords], color))
    faces_to_draw.sort(key=lambda item: item[0])
    for _, face_name, coords, color in faces_to_draw:
        light = FACE_LIGHT.get(face_name, 0.8)
        draw.polygon(
            coords,
            fill=(
                min(255, round(color[0] * light)),
                min(255, round(color[1] * light)),
                min(255, round(color[2] * light)),
                min(255, max(80, color[3])),
            ),
            outline=(17, 20, 25, 170),
        )

    draw.text((10, 8), label, font=font(14, True), fill=INK)
    draw.text((10, size - 23), caption, font=font(10), fill=MUTED)
    draw.rectangle((0, 0, size - 1, size - 1), outline=(68, 79, 91, 255))
    return canvas


def build_model_sheet(path: Path) -> None:
    atlas = content.block_atlas()
    tiles = []
    for key, geo in content.block_geometries().items():
        label, caption = CAPTIONS.get(key, (key.replace("_", " ").title(), ""))
        tiles.append((label, caption, model_image(geo, atlas, label, caption)))

    columns = 4
    cell_w, cell_h = 252, 292
    rows = math.ceil(len(tiles) / columns)
    image = Image.new("RGB", (columns * cell_w + 28, rows * cell_h + 108), BG)
    draw = ImageDraw.Draw(image)
    draw.text((20, 18), "Cogworks block models", font=font(28, True), fill=INK)
    draw.text((20, 56), "Rendered from the shipped Bedrock geometry and shared industrial atlas.",
              font=font(13), fill=MUTED)
    draw.text((20, 76), "Place conveyors and machines next to a powered cable network; connect storage extensions for capacity.",
              font=font(12), fill=MUTED)
    for index, (label, caption, tile) in enumerate(tiles):
        col, row = index % columns, index // columns
        x = 14 + col * cell_w
        y = 104 + row * cell_h
        image.paste(tile, (x, y), tile)
        draw.text((x + 4, y + tile.height + 7), label, font=font(12, True), fill=INK)
        draw.text((x + 4, y + tile.height + 23), caption, font=font(10), fill=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


if __name__ == "__main__":
    build_model_sheet(Path(__file__).resolve().parent.parent / "previews" / "models.png")
