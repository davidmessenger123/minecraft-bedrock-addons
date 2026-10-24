"""
Offline isometric preview renderer for the generated NZ animal models.

Loads each .geo.json + its texture, projects the boxes with an isometric
camera and shades every face using the colour sampled from the texture at
that face's UV rectangle. Produces one PNG per species plus a contact sheet.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

from nzlib import face_rects

# Cube face -> (normal, four corners in local unit-cube coordinates)
FACE_CORNERS = {
    "up":    ((0, 1, 0),  [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    "down":  ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    "east":  ((1, 0, 0),  [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]),
    "west":  ((-1, 0, 0), [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)]),
    "north": ((0, 0, -1), [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
    "south": ((0, 0, 1),  [(1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)]),
}

SHADE = {"up": 1.16, "down": 0.66, "east": 0.86, "west": 0.80, "north": 1.0, "south": 0.92}


# Orthographic camera looking from the front-left-above, so the entity's
# north face (where the eyes are) is visible.
#   view dir (object -> camera) d = (-1, 1, -1)
#   screen right r = (-1, 0, 1) / sqrt(2)
#   screen up    u = ( 1, 2, 1) / sqrt(6)
_D = (-1.0, 1.0, -1.0)


def project(p, scale):
    x, y, z = p
    sx = (-x + z) * 0.70710678 * scale
    # Screen Y grows downward in PIL, so negate the up-positive axis.
    sy = -(x + 2.0 * y + z) * 0.40824829 * scale
    return sx, sy


def depth(p):
    x, y, z = p
    return (-x + y - z)


def visible(normal):
    return (normal[0] * _D[0] + normal[1] * _D[1] + normal[2] * _D[2]) > 0


STRUCT_PALETTE = [
    (226, 92, 84), (246, 168, 66), (232, 214, 84), (140, 200, 96),
    (86, 190, 190), (92, 140, 220), (150, 116, 214), (222, 110, 180),
    (170, 150, 130), (120, 130, 140),
]


def render_species(geo_path: str, tex_path: str, size: int = 220, structure: bool = False):
    with open(geo_path, encoding="utf-8") as fh:
        geo = json.load(fh)
    desc = geo["minecraft:geometry"][0]["description"]
    tex = Image.open(tex_path).convert("RGB")
    tpx = tex.load()

    cubes = []
    for bone in geo["minecraft:geometry"][0]["bones"]:
        for cube in bone.get("cubes", []):
            cubes.append(cube)

    if not cubes:
        return Image.new("RGB", (size, size), (32, 32, 38))

    lo = [min(c["origin"][i] for c in cubes) for i in range(3)]
    hi = [max(c["origin"][i] + c["size"][i] for c in cubes) for i in range(3)]
    centre = [(lo[i] + hi[i]) / 2 for i in range(3)]

    faces = []
    for ci, cube in enumerate(cubes):
        ox, oy, oz = cube["origin"]
        w, h, d = cube["size"]
        u0, v0 = cube["uv"]
        rects = face_rects(w, h, d)
        for face, (normal, corners) in FACE_CORNERS.items():
            if not visible(normal):
                continue
            pts = []
            for cx, cy, cz in corners:
                pts.append((ox + cx * w - centre[0], oy + cy * h - centre[1], oz + cz * d - centre[2]))
            u1, v1, u2, v2 = rects[face]
            # average the face region so markings and texture detail show up
            sx0 = max(0, min(tex.width - 1, int(u0 + u1)))
            sy0 = max(0, min(tex.height - 1, int(v0 + v1)))
            sx1 = max(sx0 + 1, min(tex.width, int(u0 + u2)))
            sy1 = max(sy0 + 1, min(tex.height, int(v0 + v2)))
            rs = gs = bs = n = 0
            for yy in range(sy0, sy1):
                for xx in range(sx0, sx1):
                    pr, pg, pb = tpx[xx, yy]
                    rs += pr; gs += pg; bs += pb; n += 1
            r, g, b = rs // n, gs // n, bs // n
            f = SHADE[face]
            if structure:
                r, g, b = STRUCT_PALETTE[ci % len(STRUCT_PALETTE)]
                f = 1.0
            col = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))
            faces.append((sum(depth(p) for p in pts) / 4, pts, col))

    # Painter's algorithm: farthest faces first, nearer ones drawn over them.
    faces.sort(key=lambda f: f[0])

    # Fit the projected bounding box into the image.
    all_pts = [p for _d, pts, _c in faces for p in pts]
    proj = [project(p, 1.0) for p in all_pts]
    min_x = min(p[0] for p in proj); max_x = max(p[0] for p in proj)
    min_y = min(p[1] for p in proj); max_y = max(p[1] for p in proj)
    scale = min(size * 0.88 / max(1e-6, max_x - min_x), size * 0.88 / max(1e-6, max_y - min_y))
    off_x = size / 2 - (min_x + max_x) / 2 * scale
    off_y = size / 2 - (min_y + max_y) / 2 * scale

    img = Image.new("RGB", (size, size), (32, 32, 38))
    dr = ImageDraw.Draw(img)
    for _depth, pts, col in faces:
        sp = [project(p, scale) for p in pts]
        sp = [(x + off_x, y + off_y) for x, y in sp]
        dr.polygon(sp, fill=col, outline=(18, 18, 20))
    return img


def make_icon(geo_path: str, tex_path: str, size: int = 128) -> Image.Image:
    """Pack icon: the model on a deep-green rounded tile."""
    from PIL import ImageDraw
    bg = Image.new("RGB", (size, size), (22, 44, 28))
    dr = ImageDraw.Draw(bg)
    for i in range(size // 6, size):
        t = (i - size // 6) / (size - size // 6)
        dr.ellipse(
            [size * 0.5 - i * 0.75, size * 0.5 - i * 0.75, size * 0.5 + i * 0.75, size * 0.5 + i * 0.75],
            fill=(int(22 + 26 * t), int(44 + 34 * t), int(28 + 22 * t)),
        )
    model = render_species(geo_path, tex_path, size)
    model = model.resize((size, size))
    px = model.load()
    for y in range(size):
        for x in range(size):
            r, g, b = px[x, y]
            if not (r == 24 and g == 24 and b == 28):
                bg.paste((r, g, b), (x, y, x + 1, y + 1))
    return bg


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    structure = "--structure" in sys.argv
    build = args[0] if args else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
    out = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "preview"))
    # clear stale renders (species can be renamed between runs)
    if os.path.isdir(out):
        for f in os.listdir(out):
            if f.endswith(".png"):
                os.remove(os.path.join(out, f))
    os.makedirs(out, exist_ok=True)

    geo_dir = os.path.join(build, "resource_pack", "models", "entity")
    tex_dir = os.path.join(build, "resource_pack", "textures", "entity")
    species = sorted(f[:-len(".geo.json")] for f in os.listdir(geo_dir) if f.endswith(".geo.json"))

    cols = 6
    cell = 220
    rows = (len(species) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (18, 18, 22))
    for i, sp in enumerate(species):
        img = render_species(
            os.path.join(geo_dir, f"{sp}.geo.json"),
            os.path.join(tex_dir, sp, f"{sp}.png"),
            cell, structure,
        )
        img.save(os.path.join(out, f"{sp}_struct.png" if structure else f"{sp}.png"))
        sheet.paste(img, ((i % cols) * cell, (i // cols) * cell))
    sheet.save(os.path.join(out, "_contact_sheet.png"))
    print(f"rendered {len(species)} species -> {os.path.normpath(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
