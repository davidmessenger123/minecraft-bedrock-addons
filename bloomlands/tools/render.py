"""Preview images and Blockbench sources for Bloomlands.

The build script calls :func:`build_all` after the packs have been written.
Everything here is intentionally dependency-light: Pillow is the only
third-party module, and the model preview is a small painter's-algorithm
renderer rather than a full 3D engine.

Generated files
---------------
previews/block_textures.png   Contact sheet of every block texture
previews/entity_textures.png  Contact sheet of the three mob atlases
previews/models.png           Isometric previews of the custom block and mob models
previews/portal_layout.png    Top-down diagram of the Bloomgate
previews/region_map.png       Illustrated map of the island's five regions
blockbench/blocks/*.bbmodel   Editable block models with embedded textures
blockbench/entities/*.bbmodel Editable mob models with embedded textures
"""

from __future__ import annotations

import base64
import json
import math
import uuid
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont, ImageOps

import content

BG = (24, 19, 31)
CARD = (38, 30, 48)
INK = (244, 236, 250)
MUTED = (189, 174, 204)
ACCENT = (255, 184, 213)
GOLD = (255, 221, 138)
TEAL = (151, 238, 218)

FACE_ORDER = ("north", "south", "east", "west", "up", "down")
FACE_LIGHT = {
    "north": 0.82,
    "south": 0.72,
    "east": 0.70,
    "west": 0.86,
    "up": 1.04,
    "down": 0.58,
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/usr/share/fonts/liberation/LiberationSans-%s.ttf" % ("Bold" if bold else "Regular"),
        "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf" % ("Bold" if bold else "Regular"),
        "/usr/share/fonts/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
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


def checker(width: int, height: int, cell: int = 10) -> Image.Image:
    image = Image.new("RGBA", (width, height), (28, 23, 36, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(42, 35, 52, 255))
    return image


def fit_image(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    return ImageOps.contain(image.convert("RGBA"), box, Image.Resampling.NEAREST)


def texture_sheet(
    textures: Sequence[tuple[str, Image.Image]],
    path: Path,
    title: str,
    *,
    columns: int = 6,
    cell_w: int = 150,
    cell_h: int = 168,
) -> None:
    rows = max(1, math.ceil(len(textures) / columns))
    width = columns * cell_w + 32
    height = rows * cell_h + 86
    image = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.text((20, 18), title, font=font(26, True), fill=INK)
    draw.text((20, 52), "Pixel art generated for the Bloomlands resource pack.", font=font(13), fill=MUTED)

    for index, (name, texture) in enumerate(textures):
        col = index % columns
        row = index // columns
        x = 16 + col * cell_w
        y = 76 + row * cell_h
        tile = checker(cell_w - 18, cell_h - 38, 9)
        art = fit_image(texture, (cell_w - 34, cell_h - 54))
        tile.alpha_composite(art, ((tile.width - art.width) // 2, (tile.height - art.height) // 2))
        image.alpha_composite(tile, (x, y))
        draw = ImageDraw.Draw(image)
        draw.rectangle((x, y, x + tile.width - 1, y + tile.height - 1), outline=(92, 79, 108, 255))
        label = name.removeprefix("bl_").replace("_", " ")
        draw.text((x + 2, y + tile.height + 5), label, font=font(12, True), fill=INK)
        size = f"{texture.width} x {texture.height}"
        draw.text((x + 2, y + tile.height + 22), size, font=font(10), fill=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "PNG")


def average_texture_color(texture: Image.Image, rect: Sequence[int]) -> tuple[int, int, int, int]:
    x, y, w, h = (int(v) for v in rect)
    if w <= 0 or h <= 0:
        return (0, 0, 0, 0)
    x0 = max(0, min(texture.width - 1, x))
    y0 = max(0, min(texture.height - 1, y))
    x1 = max(x0 + 1, min(texture.width, x + w))
    y1 = max(y0 + 1, min(texture.height, y + h))
    crop = texture.convert("RGBA").crop((x0, y0, x1, y1))
    pixels = []
    for r, g, b, a in crop.getdata():
        if a > 24:
            pixels.append((r, g, b, a))
    if not pixels:
        return (0, 0, 0, 0)
    # Median-ish average: use the mean of the opaque pixels, weighted by alpha.
    total = sum(p[3] for p in pixels)
    if total <= 0:
        return (0, 0, 0, 0)
    r = sum(p[0] * p[3] for p in pixels) / total
    g = sum(p[1] * p[3] for p in pixels) / total
    b = sum(p[2] * p[3] for p in pixels) / total
    a = sum(p[3] for p in pixels) / len(pixels)
    return (round(r), round(g), round(b), round(a))


def rotate_point(point: Sequence[float], pivot: Sequence[float], rotation: Sequence[float]) -> tuple[float, float, float]:
    x, y, z = (float(point[i]) - float(pivot[i]) for i in range(3))
    rx, ry, rz = (math.radians(float(v)) for v in rotation)
    if rx:
        c, s = math.cos(rx), math.sin(rx)
        y, z = y * c - z * s, y * s + z * c
    if ry:
        c, s = math.cos(ry), math.sin(ry)
        x, z = x * c + z * s, -x * s + z * c
    if rz:
        c, s = math.cos(rz), math.sin(rz)
        x, y = x * c - y * s, x * s + y * c
    return (x + pivot[0], y + pivot[1], z + pivot[2])


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


def project(point: Sequence[float], size: int, bounds: tuple[float, float, float, float],
            scale: float, yaw: float, pitch: float) -> tuple[float, float, float]:
    x, y, z = point
    x1 = x * math.cos(yaw) - z * math.sin(yaw)
    z1 = x * math.sin(yaw) + z * math.cos(yaw)
    y2 = y * math.cos(pitch) - z1 * math.sin(pitch)
    z2 = y * math.sin(pitch) + z1 * math.cos(pitch)
    return ((x1 - bounds[0]) * scale + 14, size - 14 - (y2 - bounds[1]) * scale, z2)


def model_image(geometry: dict, texture: Image.Image, label: str, caption: str, size: int = 210) -> Image.Image:
    entry = geometry["minecraft:geometry"][0]
    cubes = []
    for bone in entry.get("bones", []):
        for index, cube in enumerate(bone.get("cubes", [])):
            cubes.append((bone.get("name", ""), index, cube))

    yaw = math.radians(38)
    pitch = math.radians(24)
    transformed: list[tuple[dict, dict[str, list[tuple[float, float, float]]]]] = []
    all_points: list[tuple[float, float, float]] = []
    for bone_name, index, cube in cubes:
        origin = cube["origin"]
        faces = cube_faces(origin, cube["size"])
        if cube.get("rotation"):
            pivot = cube.get("pivot", [0, 0, 0])
            faces = {
                name: [rotate_point(point, pivot, cube["rotation"]) for point in points]
                for name, points in faces.items()
            }
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
    scale = (size - 32) / span
    bounds = (min_x, min_y, max_x, max_y)

    canvas = checker(size, size, 12)
    draw = ImageDraw.Draw(canvas)
    faces_to_draw = []
    for cube, faces in transformed:
        uv = cube.get("uv", {})
        for face_name in FACE_ORDER:
            points = faces[face_name]
            face_uv = uv.get(face_name)
            if not face_uv:
                continue
            color = average_texture_color(texture, [face_uv["uv"][0], face_uv["uv"][1],
                                                    face_uv["uv_size"][0], face_uv["uv_size"][1]])
            if color[3] < 22:
                continue
            projected_points = [project(p, size, bounds, scale, yaw, pitch) for p in points]
            coords = [(p[0], p[1]) for p in projected_points]
            depth = sum(p[2] for p in projected_points) / 4.0
            faces_to_draw.append((depth, face_name, coords, color))
    faces_to_draw.sort(key=lambda item: item[0])
    for _, face_name, coords, color in faces_to_draw:
        light = FACE_LIGHT.get(face_name, 0.8)
        r = min(255, round(color[0] * light))
        g = min(255, round(color[1] * light))
        b = min(255, round(color[2] * light))
        alpha = min(255, max(70, color[3]))
        draw.polygon(coords, fill=(r, g, b, alpha), outline=(25, 19, 31, 160))
    canvas.alpha_composite(Image.new("RGBA", (size, size), (0, 0, 0, 0)))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 7), label, font=font(13, True), fill=INK)
    draw.text((8, size - 19), caption, font=font(10), fill=MUTED)
    draw.rectangle((0, 0, size - 1, size - 1), outline=(92, 79, 108, 255))
    return canvas


def model_sheet(tiles: Sequence[tuple[str, str, Image.Image]], path: Path, title: str) -> None:
    columns = 4
    cell_w, cell_h = 230, 254
    rows = max(1, math.ceil(len(tiles) / columns))
    image = Image.new("RGBA", (columns * cell_w + 28, rows * cell_h + 92), BG)
    draw = ImageDraw.Draw(image)
    draw.text((18, 18), title, font=font(26, True), fill=INK)
    draw.text((18, 52), "Isometric previews rendered from the Bedrock geometry files.", font=font(13), fill=MUTED)
    for index, (label, caption, tile) in enumerate(tiles):
        col, row = index % columns, index // columns
        x = 14 + col * cell_w
        y = 78 + row * cell_h
        image.alpha_composite(tile, (x, y))
        draw = ImageDraw.Draw(image)
        draw.text((x + 4, y + tile.height + 7), label, font=font(12, True), fill=INK)
        draw.text((x + 4, y + tile.height + 23), caption, font=font(10), fill=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "PNG")


def draw_flower(draw: ImageDraw.ImageDraw, center: tuple[float, float], radius: float,
                petal: str, heart: str) -> None:
    x, y = center
    for index in range(6):
        angle = math.tau * index / 6
        px = x + math.cos(angle) * radius * 0.62
        py = y + math.sin(angle) * radius * 0.62
        draw.ellipse((px - radius * 0.45, py - radius * 0.35,
                      px + radius * 0.45, py + radius * 0.35), fill=petal)
    draw.ellipse((x - radius * 0.34, y - radius * 0.34,
                  x + radius * 0.34, y + radius * 0.34), fill=heart)


def portal_diagram(path: Path) -> None:
    width, height = 820, 820
    image = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.text((28, 22), "Bloomgate construction", font=font(30, True), fill=INK)
    draw.text((28, 60), "A 7 x 7 petal-path plaza, eight Bloomgate flowers, and one Bloomheart.", font=font(14), fill=MUTED)

    cell = 64
    origin_x, origin_y = 70, 128
    ring = {(0, -3), (-2, -2), (-3, 0), (-2, 2), (0, 3), (2, 2), (3, 0), (2, -2)}
    for dz in range(-3, 4):
        for dx in range(-3, 4):
            x = origin_x + (dx + 3) * cell
            y = origin_y + (dz + 3) * cell
            draw.rectangle((x, y, x + cell - 2, y + cell - 2), fill=(181, 108, 133, 255),
                           outline=(226, 164, 186, 255), width=2)
            if (dx, dz) in ring:
                draw_flower(draw, (x + cell / 2, y + cell / 2), cell * 0.34, "#f27bc0", "#ffe6a8")
    center_x = origin_x + 3 * cell + cell / 2
    center_y = origin_y + 3 * cell + cell / 2
    draw.ellipse((center_x - 21, center_y - 21, center_x + 21, center_y + 21),
                 fill=(240, 122, 168, 255), outline="#fff0a8", width=3)
    draw.ellipse((center_x - 9, center_y - 9, center_x + 9, center_y + 9), fill="#fff7d6")
    draw.text((center_x + 22, center_y - 7), "Bloomheart", font=font(13, True), fill=INK)

    # Legend.
    legend_x, legend_y = 580, 142
    draw.text((legend_x, legend_y), "Legend", font=font(20, True), fill=INK)
    draw.rectangle((legend_x, legend_y + 38, legend_x + 28, legend_y + 66), fill=(181, 108, 133, 255))
    draw.text((legend_x + 38, legend_y + 41), "Petal path floor", font=font(13), fill=MUTED)
    draw_flower(draw, (legend_x + 14, legend_y + 96), 10, "#f27bc0", "#ffe6a8")
    draw.text((legend_x + 38, legend_y + 87), "Bloomgate flower (8)", font=font(13), fill=MUTED)
    draw.ellipse((legend_x + 2, legend_y + 122, legend_x + 26, legend_y + 146), fill="#fff7d6")
    draw.text((legend_x + 38, legend_y + 123), "Bloomheart", font=font(13), fill=MUTED)

    # Arrival walkway and arrow.
    spawn_x = center_x
    plaza_bottom = origin_y + 7 * cell
    spawn_y = plaza_bottom + 48
    draw.rectangle((spawn_x - 10, plaza_bottom - 4, spawn_x + 10, spawn_y - 30), fill=(181, 108, 133, 255))
    draw.line((spawn_x, spawn_y - 28, spawn_x, spawn_y - 4), fill=ACCENT, width=4)
    draw.polygon([(spawn_x, spawn_y), (spawn_x - 8, spawn_y - 16), (spawn_x + 8, spawn_y - 16)], fill=ACCENT)
    draw.text((spawn_x + 18, spawn_y - 30), "Arrival platform", font=font(13, True), fill=ACCENT)

    # Side note.
    draw.rounded_rectangle((52, 672, 760, 780), radius=16, fill=CARD, outline=(92, 79, 108, 255), width=2)
    draw.text((74, 690), "Build it with the Bloomgate item", font=font(18, True), fill=INK)
    draw.text((74, 718), "Use the item on the top face of a ground block. The 7 x 7 area must be clear", font=font(13), fill=MUTED)
    draw.text((74, 738), "of solid blocks. Stand on the Bloomheart to travel between worlds.", font=font(13), fill=MUTED)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "PNG")


def region_map(path: Path) -> None:
    width = 780
    image = Image.new("RGBA", (width, width), BG)
    overlay = Image.new("RGBA", (width, width), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx = cy = width // 2
    radius = 292
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(38, 48, 40, 255))

    def wedge(start: float, end: float, color: tuple[int, int, int, int], r: int = radius) -> None:
        draw.pieslice((cx - r, cy - r, cx + r, cy + r), start, end, fill=color)

    # Broad region shapes.  They are illustrative rather than exact boundaries.
    wedge(205, 335, (31, 62, 43, 230))          # Whispering Canopy (north)
    wedge(-35, 62, (238, 100, 147, 92))         # Giant's Garden (east)
    wedge(155, 218, (92, 147, 208, 128))        # Petal Hills (west)
    wedge(125, 170, (68, 179, 171, 118))        # Mirror Pool (south-west)
    wedge(18, 162, (111, 189, 82, 100), radius - 23)  # Sunpetal Meadow (south)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                 outline=(185, 166, 218, 255), width=34)
    draw.ellipse((cx - radius + 22, cy - radius + 22, cx + radius - 22, cy + radius - 22),
                 outline=(120, 102, 145, 255), width=2)
    image.alpha_composite(overlay)
    draw = ImageDraw.Draw(image)

    # Decorative flowers.
    for index in range(28):
        angle = index * 2.399
        rr = 80 + (index * 37) % 170
        x = cx + math.cos(angle) * rr
        y = cy + math.sin(angle) * rr
        draw_flower(draw, (x, y), 7, "#d85b92", "#ffe6a8")

    # Paths.
    draw.line((cx, cy + 14, cx, cy + 160), fill=(230, 177, 190, 230), width=7)
    draw.line((cx, cy + 14, cx + 150, cy + 80), fill=(230, 177, 190, 230), width=7)
    draw.line((cx, cy + 14, cx - 150, cy + 80), fill=(230, 177, 190, 230), width=7)
    draw.line((cx, cy + 14, cx - 120, cy - 130), fill=(230, 177, 190, 230), width=7)

    # Portal and spawn.
    draw.ellipse((cx - 13, cy + 1, cx + 13, cy + 27), fill=(240, 122, 168, 255), outline="#fff0a8", width=3)
    draw.text((cx + 20, cy + 3), "Bloomgate", font=font(14, True), fill=INK)
    draw.ellipse((cx - 7, cy + 32, cx + 7, cy + 46), fill=TEAL)
    draw.text((cx + 20, cy + 30), "Arrival", font=font(13, True), fill=TEAL)

    def label(x: int, y: int, text: str, sub: str, color: str = INK) -> None:
        box = draw.textbbox((0, 0), text, font=font(20, True))
        w = box[2] - box[0]
        draw.rounded_rectangle((x - 12, y - 9, x + w + 12, y + 35), radius=9,
                               fill=(24, 19, 31, 220), outline=color, width=2)
        draw.text((x, y), text, font=font(20, True), fill=color)
        draw.text((x, y + 23), sub, font=font(10), fill=MUTED)

    label(cx - 375, cy + 170, "Sunpetal Meadow", "flowers, paths, and the arrival garden")
    label(cx - 370, cy - 265, "Whispering Canopy", "dense flower trees under a closed sky")
    label(cx + 90, cy - 35, "Giant's Garden", "tree-sized blooms and glowing trunks")
    label(cx - 355, cy - 95, "Petal Hills", "six walkable flower terraces")
    label(cx - 355, cy + 30, "Mirror Pool", "a quiet lake, lilies, and a skybell island")
    label(cx - 65, cy - 320, "Bloomlands Edge", "the stone rim above the void", TEAL)

    draw.text((28, 24), "The Bloomlands", font=font(32, True), fill=INK)
    draw.text((30, 64), "A floating garden island, roughly 120 blocks across.", font=font(13), fill=MUTED)
    draw.text((width - 190, 30), "N", font=font(24, True), fill=ACCENT)
    draw.line((width - 165, 36, width - 165, 80), fill=ACCENT, width=4)
    draw.polygon([(width - 165, 26), (width - 176, 44), (width - 154, 44)], fill=ACCENT)
    image.convert("RGB").save(path, "PNG")


def data_uri(image: Image.Image) -> str:
    import io

    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def uid(*parts: object) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "bloomlands/" + "/".join(str(p) for p in parts)))


def bbmodel(
    name: str,
    model_identifier: str,
    geometry: dict,
    texture: Image.Image,
    texture_name: str,
) -> dict:
    entry = geometry["minecraft:geometry"][0]
    elements = []
    bone_groups: dict[str, dict] = {}
    bone_cubes: dict[str, list[str]] = {}
    bone_parents: dict[str, str | None] = {}
    bone_order: list[str] = []

    for bone in entry.get("bones", []):
        bone_name = bone.get("name", "bone")
        bone_order.append(bone_name)
        bone_parents[bone_name] = bone.get("parent")
        group_uuid = uid("group", name, bone_name)
        bone_groups[bone_name] = {
            "name": bone_name,
            "uuid": group_uuid,
            "export": True,
            "locked": False,
            "scope": 0,
            "selected": False,
            "visibility": True,
            "_static": {"properties": {}, "temp_data": {}},
            "origin": [round(float(v), 5) for v in bone.get("pivot", [0, 0, 0])],
            "rotation": [round(float(v), 5) for v in bone.get("rotation", [0, 0, 0])],
            "bedrock_binding": "",
            "color": 0,
            "children": [],
            "reset": False,
            "shade": True,
            "mirror_uv": False,
            "autouv": 0,
            "isOpen": False,
            "primary_selected": False,
        }
        bone_cubes[bone_name] = []
        for index, cube in enumerate(bone.get("cubes", [])):
            element_uuid = uid("element", name, bone_name, index)
            bone_cubes[bone_name].append(element_uuid)
            origin = [float(v) for v in cube["origin"]]
            size = [float(v) for v in cube["size"]]
            faces = {}
            for face in FACE_ORDER:
                face_data = cube.get("uv", {}).get(face)
                if not face_data:
                    continue
                u, v = face_data["uv"]
                uw, uh = face_data["uv_size"]
                faces[face] = {"uv": [u, v, u + uw, v + uh], "texture": 0}
            element = {
                "name": f"{bone_name}_{index}",
                "box_uv": False,
                "render_order": "default",
                "locked": False,
                "export": True,
                "scope": 0,
                "allow_mirror_modeling": True,
                "from": [round(v, 5) for v in origin],
                "to": [round(origin[i] + size[i], 5) for i in range(3)],
                "autouv": 0,
                "color": 0,
                "origin": [round(float(v), 5) for v in cube.get("pivot", [0, 0, 0])],
                "faces": faces,
                "type": "cube",
                "uuid": element_uuid,
            }
            if cube.get("rotation"):
                element["rotation"] = [round(float(v), 5) for v in cube["rotation"]]
            elements.append(element)

    # Build the outliner tree.
    def group_node(bone_name: str) -> dict:
        children: list[object] = list(bone_cubes.get(bone_name, []))
        for child_name in bone_order:
            if bone_parents.get(child_name) == bone_name:
                children.append(group_node(child_name))
        return {"uuid": bone_groups[bone_name]["uuid"], "isOpen": False, "children": children}

    roots = [group_node(bone) for bone in bone_order if bone_parents.get(bone) not in bone_groups]
    if not roots and bone_order:
        roots = [group_node(bone_order[0])]

    return {
        "meta": {"format_version": "5.0", "model_format": "bedrock", "box_uv": False},
        "name": name,
        "model_identifier": model_identifier,
        "visible_box": [1, 1, 0],
        "variable_placeholders": "",
        "multi_file_ruleset": "",
        "variable_placeholder_buttons": [],
        "bedrock_animation_mode": "entity",
        "timeline_setups": [],
        "unhandled_root_fields": {},
        "ai_used": False,
        "ai_agents": "",
        "resolution": {"width": texture.width, "height": texture.height},
        "elements": elements,
        "groups": list(bone_groups.values()),
        "outliner": roots,
        "textures": [
            {
                "name": texture_name,
                "path": "",
                "folder": "",
                "namespace": "",
                "id": "0",
                "group": "",
                "scope": 0,
                "width": texture.width,
                "height": texture.height,
                "uv_width": texture.width,
                "uv_height": texture.height,
                "particle": False,
                "use_as_default": False,
                "layers_enabled": False,
                "sync_to_project": "",
                "file_format": "png",
                "render_mode": "default",
                "render_sides": "auto",
                "wrap_mode": "limited",
                "pbr_channel": "color",
                "fps": 7,
                "force_translucent": False,
                "frame_time": 1,
                "frame_order_type": "loop",
                "frame_order": "",
                "frame_interpolate": False,
                "visible": True,
                "internal": True,
                "saved": True,
                "uuid": uid("texture", name, texture_name),
                "source": data_uri(texture),
            }
        ],
        "animations": [],
    }


def write_bbmodels(
    blockbench: Path,
    block_geometries: dict[str, dict],
    block_textures: dict[str, Image.Image],
    giant_specs: Iterable,
    small_specs: Iterable,
    entities: Iterable,
) -> None:
    blocks_dir = blockbench / "blocks"
    entities_dir = blockbench / "entities"
    blocks_dir.mkdir(parents=True, exist_ok=True)
    entities_dir.mkdir(parents=True, exist_ok=True)
    for old in list(blocks_dir.glob("*.bbmodel")) + list(entities_dir.glob("*.bbmodel")):
        old.unlink()

    def save(path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    for spec in small_specs:
        geometry = block_geometries["small_flower"]
        texture = block_textures[f"bl_{spec.key}"]
        save(
            blocks_dir / f"{spec.key}.bbmodel",
            bbmodel(spec.label, geometry["minecraft:geometry"][0]["description"]["identifier"],
                    geometry, texture, f"bl_{spec.key}"),
        )

    for spec in giant_specs:
        geometry = block_geometries["giant_bloom"]
        texture = block_textures[f"bl_{spec.key}"]
        save(
            blocks_dir / f"{spec.key}.bbmodel",
            bbmodel(spec.label, geometry["minecraft:geometry"][0]["description"]["identifier"],
                    geometry, texture, f"bl_{spec.key}"),
        )

    extras = [
        ("portal_flower", "Bloomgate Flower", "portal_flower", "bl_portal_flower"),
        ("bloomheart", "Bloomheart", "bloomheart", "bl_bloomheart"),
        ("dewgrass", "Dewgrass", "dewgrass", "bl_dewgrass"),
        ("lily_bloom", "Lily Bloom", "lily_bloom", "bl_lily_bloom"),
    ]
    for key, label, geometry_key, texture_key in extras:
        geometry = block_geometries[geometry_key]
        texture = block_textures[texture_key]
        save(
            blocks_dir / f"{key}.bbmodel",
            bbmodel(label, geometry["minecraft:geometry"][0]["description"]["identifier"],
                    geometry, texture, texture_key),
        )

    for spec in entities:
        save(
            entities_dir / f"{spec.key}.bbmodel",
            bbmodel(spec.label, spec.geometry_id, spec.geometry, spec.texture, f"{spec.key}_atlas"),
        )


def build_all(
    *,
    root: Path,
    previews: Path,
    blockbench: Path,
    block_textures: dict[str, Image.Image],
    block_geometries: dict[str, dict],
    entities: Iterable,
    block_specs: Iterable,
    giant_specs: Iterable,
    small_specs: Iterable,
) -> None:
    previews.mkdir(parents=True, exist_ok=True)
    blockbench.mkdir(parents=True, exist_ok=True)
    # Remove the scratch previews left by model-design iterations.
    for old in previews.glob("_test_*.png"):
        old.unlink()

    ordered = sorted(block_textures.items())
    texture_sheet(ordered, previews / "block_textures.png", "Block textures", columns=6)
    entity_sheet = [(spec.key, spec.texture) for spec in entities]
    texture_sheet(entity_sheet, previews / "entity_textures.png", "Mob atlases", columns=3, cell_w=200, cell_h=230)

    tiles: list[tuple[str, str, Image.Image]] = []
    small_preview = next((s for s in small_specs if s.key == "sunpetal"), None)
    if small_preview is not None:
        tiles.append((
            "Small flower",
            "geometry.bl.small_flower - sunpetal",
            model_image(block_geometries["small_flower"], block_textures["bl_sunpetal"], "Small flower", "six petals + two leaves"),
        ))
    tiles.append((
        "Bloomgate flower",
        "geometry.bl.portal_flower",
        model_image(block_geometries["portal_flower"], block_textures["bl_portal_flower"], "Bloomgate flower", "eight glowing petals"),
    ))
    tiles.append((
        "Bloomheart",
        "geometry.bl.bloomheart - animated",
        model_image(block_geometries["bloomheart"], block_textures["bl_bloomheart"], "Bloomheart", "four-frame flipbook"),
    ))
    for spec in giant_specs:
        tiles.append((
            spec.label,
            "geometry.bl.giant_bloom",
            model_image(block_geometries["giant_bloom"], block_textures[f"bl_{spec.key}"], spec.label, "tree-sized bloom"),
        ))
    tiles.append((
        "Dewgrass",
        "geometry.bl.dewgrass",
        model_image(block_geometries["dewgrass"], block_textures["bl_dewgrass"], "Dewgrass", "crossed blades with dew"),
    ))
    tiles.append((
        "Lily Bloom",
        "geometry.bl.lily_bloom",
        model_image(block_geometries["lily_bloom"], block_textures["bl_lily_bloom"], "Lily Bloom", "floating lotus pad"),
    ))
    for spec in entities:
        tiles.append((
            spec.label,
            "geometry.bl." + spec.key,
            model_image(spec.geometry, spec.texture, spec.label, spec.identifier),
        ))

    model_sheet(tiles, previews / "models.png", "Custom models")
    portal_diagram(previews / "portal_layout.png")
    region_map(previews / "region_map.png")
    write_bbmodels(blockbench, block_geometries, block_textures, giant_specs, small_specs, entities)
