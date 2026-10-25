"""
Offline isometric previews for Rainbow Garden.

Renders the custom block models and the butterfly using the same box-UV
geometry that Bedrock loads, then writes one PNG per asset plus a contact
sheet.  The renderer samples the average visible colour of each face, so it is
a shape/colour check rather than a full in-game screenshot.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RP = ROOT / "resource_pack"
OUT = ROOT / "preview"

FACE_CORNERS = {
    "up": ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    "down": ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    "east": ((1, 0, 0), [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]),
    "west": ((-1, 0, 0), [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)]),
    "north": ((0, 0, -1), [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
    "south": ((0, 0, 1), [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]),
}
SHADE = {"up": 1.16, "down": 0.66, "east": 0.86, "west": 0.80, "north": 1.0, "south": 0.92}
_D = (-1.0, 1.0, -1.0)


def project(p, scale):
    x, y, z = p
    sx = (-x + z) * 0.70710678 * scale
    sy = -(x + 2.0 * y + z) * 0.40824829 * scale
    return sx, sy


def depth(p):
    x, y, z = p
    return (-x + y - z)


def visible(normal):
    return normal[0] * _D[0] + normal[1] * _D[1] + normal[2] * _D[2] > 0


def rotate_point(point, pivot, rotation):
    x, y, z = (point[i] - pivot[i] for i in range(3))
    rx, ry, rz = (math.radians(v) for v in rotation)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    # Bedrock applies cube rotations as X, then Y, then Z.
    y, z = y * cx - z * sx, y * sx + z * cx
    x, z = x * cy + z * sy, -x * sy + z * cy
    x, y = x * cz - y * sz, x * sz + y * cz
    return x + pivot[0], y + pivot[1], z + pivot[2]


def sample_pixel(tex: Image.Image, u: float, v: float):
    x = max(0, min(tex.width - 1, int(u)))
    y = max(0, min(tex.height - 1, int(v)))
    r, g, b, a = tex.getpixel((x, y))
    if a < 24:
        return None
    return r, g, b


def render_geometry(geo_path: Path, tex_path: Path, size: int = 240) -> Image.Image:
    geo = json.loads(geo_path.read_text(encoding="utf-8"))
    desc = geo["minecraft:geometry"][0]["description"]
    tex = Image.open(tex_path).convert("RGBA")
    cubes = []
    for bone in geo["minecraft:geometry"][0]["bones"]:
        cubes.extend(bone.get("cubes", []))
    if not cubes:
        return Image.new("RGB", (size, size), (245, 247, 252))

    # Transform every cube corner once so both the fit and the faces use the
    # same rotated geometry.
    transformed = []
    all_corners = []
    for cube in cubes:
        ox, oy, oz = cube["origin"]
        w, h, d = cube["size"]
        rotation = cube.get("rotation")
        pivot = cube.get("pivot", [ox + w / 2, oy + h / 2, oz + d / 2])
        corners = []
        for cx, cy, cz in FACE_CORNERS["up"][1] + FACE_CORNERS["down"][1]:
            p = (ox + cx * w, oy + cy * h, oz + cz * d)
            if rotation:
                p = rotate_point(p, pivot, rotation)
            corners.append(p)
        all_corners.extend(corners)
        transformed.append((cube, corners))
    lo = [min(p[i] for p in all_corners) for i in range(3)]
    hi = [max(p[i] for p in all_corners) for i in range(3)]
    centre = [(lo[i] + hi[i]) / 2 for i in range(3)]

    faces = []
    for cube, _corners in transformed:
        ox, oy, oz = cube["origin"]
        w, h, d = cube["size"]
        rotation = cube.get("rotation")
        pivot = cube.get("pivot", [ox + w / 2, oy + h / 2, oz + d / 2])
        uv = cube.get("uv", [0, 0])
        for face, (normal, corners) in FACE_CORNERS.items():
            if not visible(normal):
                continue
            pts = []
            for cx, cy, cz in corners:
                p = (ox + cx * w, oy + cy * h, oz + cz * d)
                if rotation:
                    p = rotate_point(p, pivot, rotation)
                pts.append((p[0] - centre[0], p[1] - centre[1], p[2] - centre[2]))
            if isinstance(uv, dict):
                fuv = uv.get(face)
                if not fuv:
                    continue
                u, v = fuv["uv"]
                uw, uh = fuv["uv_size"]
            else:
                u, v = uv
                if face in ("north", "south"):
                    uw, uh = w, h
                elif face in ("east", "west"):
                    uw, uh = d, h
                else:
                    uw, uh = w, d
            # Textured quad: sample the face as a small grid so alpha-cutout
            # textures (the butterfly wings) show their real silhouette.
            gw = max(1, int(round(uw)))
            gh = max(1, int(round(uh)))
            for gy in range(gh):
                for gx in range(gw):
                    s0, s1 = gx / gw, (gx + 1) / gw
                    t0, t1 = gy / gh, (gy + 1) / gh
                    col = sample_pixel(tex, u + (s0 + s1) * 0.5 * uw,
                                       v + (t0 + t1) * 0.5 * uh)
                    if col is None:
                        continue
                    cell = []
                    for s, t in [(s0, t0), (s1, t0), (s1, t1), (s0, t1)]:
                        cell.append((
                            (1 - s) * (1 - t) * pts[0][0] + s * (1 - t) * pts[1][0] + s * t * pts[2][0] + (1 - s) * t * pts[3][0],
                            (1 - s) * (1 - t) * pts[0][1] + s * (1 - t) * pts[1][1] + s * t * pts[2][1] + (1 - s) * t * pts[3][1],
                            (1 - s) * (1 - t) * pts[0][2] + s * (1 - t) * pts[1][2] + s * t * pts[2][2] + (1 - s) * t * pts[3][2],
                        ))
                    f = SHADE[face]
                    color = tuple(min(255, int(c * f)) for c in col)
                    faces.append((sum(depth(p) for p in cell) / 4, cell, color))

    if not faces:
        return Image.new("RGB", (size, size), (245, 247, 252))
    faces.sort(key=lambda item: item[0])
    all_pts = [p for _d, pts, _c in faces for p in pts]
    proj = [project(p, 1.0) for p in all_pts]
    min_x = min(p[0] for p in proj)
    max_x = max(p[0] for p in proj)
    min_y = min(p[1] for p in proj)
    max_y = max(p[1] for p in proj)
    scale = min(size * 0.82 / max(1e-6, max_x - min_x), size * 0.82 / max(1e-6, max_y - min_y))
    off_x = size / 2 - (min_x + max_x) / 2 * scale
    off_y = size / 2 - (min_y + max_y) / 2 * scale

    img = Image.new("RGB", (size, size), (245, 247, 252))
    d = ImageDraw.Draw(img)
    for _d, pts, color in faces:
        sp = [project(p, scale) for p in pts]
        sp = [(x + off_x, y + off_y) for x, y in sp]
        d.polygon(sp, fill=color)
    return img


def render_full_block(tex_path: Path, size: int = 240) -> Image.Image:
    tex = Image.open(tex_path).convert("RGBA")
    # A synthetic 16x16x16 cube with the whole texture on every face.
    geo = {
        "minecraft:geometry": [
            {
                "description": {"identifier": "preview.full_block"},
                "bones": [
                    {
                        "name": "block",
                        "pivot": [0, 0, 0],
                        "cubes": [
                            {
                                "origin": [-8, 0, -8],
                                "size": [16, 16, 16],
                                "uv": {
                                    face: {"uv": [0, 0], "uv_size": [16, 16]}
                                    for face in FACE_CORNERS
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }
    tmp = ROOT / "preview" / "_tmp_block.geo.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(geo), encoding="utf-8")
    try:
        return render_geometry(tmp, tex_path, size)
    finally:
        tmp.unlink(missing_ok=True)


def label(img: Image.Image, text: str) -> Image.Image:
    out = Image.new("RGB", (img.width, img.height + 26), (245, 247, 252))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), text, font=font)
    d.text(((out.width - (box[2] - box[0])) / 2, img.height + 4), text, fill=(42, 36, 58), font=font)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()

    bp = RP
    flower_geo = bp / "models" / "blocks" / "rainbow_flower.geo.json"
    tree_geo = bp / "models" / "blocks" / "rainbow_tree.geo.json"
    mushroom_geo = bp / "models" / "blocks" / "rainbow_mushroom.geo.json"
    butterfly_geo = bp / "models" / "entity" / "rainbow_butterfly.geo.json"

    assets = []
    for key, name in [
        ("red", "Red flower"),
        ("orange", "Orange flower"),
        ("yellow", "Yellow flower"),
        ("green", "Green flower"),
        ("blue", "Blue flower"),
        ("purple", "Purple flower"),
    ]:
        assets.append((
            f"rainbow_flower_{key}",
            name,
            lambda key=key: render_geometry(
                flower_geo,
                bp / "textures" / "blocks" / f"rainbow_flower_{key}.png",
            ),
        ))
    assets += [
        ("rainbow_tree", "Rainbow tree", lambda: render_geometry(tree_geo, bp / "textures" / "blocks" / "rainbow_tree.png")),
        ("rainbow_mushroom", "Rainbow mushroom", lambda: render_geometry(mushroom_geo, bp / "textures" / "blocks" / "rainbow_mushroom.png")),
        ("rainbow_lantern", "Rainbow lantern", lambda: render_full_block(bp / "textures" / "blocks" / "rainbow_lantern.png")),
        ("rainbow_butterfly", "Rainbow butterfly", lambda: render_geometry(butterfly_geo, bp / "textures" / "entity" / "rainbow_butterfly.png")),
    ]

    cell = 240
    cols = 5
    rows = (len(assets) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 26)), (245, 247, 252))
    for i, (key, name, make) in enumerate(assets):
        img = label(make(), name)
        img.save(OUT / f"{key}.png")
        sheet.paste(img, ((i % cols) * cell, (i // cols) * (cell + 26)))
    sheet.save(OUT / "_contact_sheet.png")
    print(f"rendered {len(assets)} previews -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
