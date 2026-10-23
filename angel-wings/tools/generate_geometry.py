#!/usr/bin/env python3
"""Generate the layered Angel Wings Bedrock geometry.

Run from the project root:

    python3 tools/generate_geometry.py

The wings are authored in player-model space: the back of the player is +Z,
the shoulders are at y=24, and one model unit is 1/16 block.  The geometry is
deliberately built from flat, layered feather plates so the silhouette reads
well in-game without a huge cube count.
"""
import json
import math
import os


TEXTURE = 128
GOLD = (0, 64)
IVORY = (32, 64)
SHADE = (64, 64)
DARK_GOLD = (96, 64)


def face(uv, size=(32, 32)):
    return {"uv": list(uv), "uv_size": list(size)}


def feather_uv(cell_x, cell_y):
    """A cut-out feather on the large faces, gold trim on the thin edges."""
    return {
        "north": face((cell_x, cell_y)),
        "south": face((cell_x, cell_y)),
        "east": face(GOLD, (4, 4)),
        "west": face(GOLD, (4, 4)),
        "up": face(GOLD, (4, 4)),
        "down": face(GOLD, (4, 4)),
    }


def solid_uv(swatch, edge=None):
    edge = edge or swatch
    return {
        "north": face(swatch),
        "south": face(swatch),
        "east": face(edge, (8, 8)),
        "west": face(edge, (8, 8)),
        "up": face(edge, (8, 8)),
        "down": face(edge, (8, 8)),
    }


def cube(origin, size, uv, rotation=None, pivot=None):
    out = {
        "origin": [round(v, 3) for v in origin],
        "size": [round(v, 3) for v in size],
        "uv": uv,
    }
    if rotation is not None:
        out["rotation"] = [round(v, 3) for v in rotation]
    if pivot is not None:
        out["pivot"] = [round(v, 3) for v in pivot]
    return out


def feather(origin, size, pivot, rotation_z, cell_x, cell_y):
    return cube(origin, size, feather_uv(cell_x, cell_y),
                rotation=[0, 0, rotation_z], pivot=pivot)


def solid(origin, size, swatch, edge=None):
    return cube(origin, size, solid_uv(swatch, edge))


def wing(side):
    """Build one wing. side=+1 is the left wing (extends +X), -1 the right."""
    s = side
    cell_y = 0 if side > 0 else 32
    cells = [(0, cell_y), (32, cell_y), (64, cell_y), (96, cell_y)]

    def mx(x):
        # Mirror X around the centre line for the right wing.
        return x if side > 0 else -x

    def msize(w):
        return w

    def mirror_cube(origin, size, **kwargs):
        # For a mirrored cube, keep the same width but move the origin so the
        # cube occupies the mirrored interval.
        ox, oy, oz = origin
        w, h, d = size
        if side > 0:
            o = [ox, oy, oz]
        else:
            o = [-(ox + w), oy, oz]
        return cube(o, [w, h, d], **kwargs)

    def mirror_feather(origin, size, pivot, rz, cell_x, cell_y):
        ox, oy, oz = origin
        w, h, d = size
        if side > 0:
            o = [ox, oy, oz]
            p = [pivot[0], pivot[1], pivot[2]]
            r = rz
        else:
            o = [-(ox + w), oy, oz]
            p = [-pivot[0], pivot[1], pivot[2]]
            r = -rz
        return feather(o, [w, h, d], p, r, cell_x, cell_y)

    def mirror_solid(origin, size, swatch, edge=None):
        ox, oy, oz = origin
        w, h, d = size
        if side > 0:
            o = [ox, oy, oz]
        else:
            o = [-(ox + w), oy, oz]
        return solid(o, [w, h, d], swatch, edge)

    root = "left_wing" if side > 0 else "right_wing"
    mid = "left_wing_mid" if side > 0 else "right_wing_mid"
    tip = "left_wing_tip" if side > 0 else "right_wing_tip"

    root_bone = {
        "name": root,
        "parent": "body",
        "pivot": [s * 1.5, 25.0, 2.8],
        "rotation": [0, 0, s * 10],
        "cubes": [
            # Leading-edge arm.
            mirror_solid((1.5, 25.0, 2.5), (8.0, 1.2, 0.8), GOLD, DARK_GOLD),
            # Upper coverts, tucked behind the primaries.
            mirror_feather((2.0, 25.5, 2.8), (5.0, 2.5, 0.35), (2.0, 26.0, 2.8), 3, *cells[0]),
            mirror_feather((3.0, 23.5, 3.0), (6.0, 2.5, 0.35), (3.0, 24.0, 3.0), -3, *cells[0]),
            # Front primaries, fanning down and outward.
            mirror_feather((2.0, 24.5, 3.2), (7.0, 3.0, 0.35), (2.0, 25.0, 3.2), -5, *cells[1]),
            mirror_feather((3.0, 22.5, 3.5), (8.0, 3.0, 0.35), (3.0, 23.0, 3.5), -10, *cells[2]),
            mirror_feather((4.0, 20.5, 3.8), (7.0, 3.0, 0.35), (4.0, 21.0, 3.8), -16, *cells[3]),
        ],
    }

    mid_bone = {
        "name": mid,
        "parent": root,
        "pivot": [s * 9.0, 25.5, 3.0],
        "rotation": [0, 0, s * -8],
        "cubes": [
            mirror_solid((9.0, 25.2, 2.6), (7.0, 1.0, 0.7), GOLD, DARK_GOLD),
            mirror_feather((9.5, 25.8, 2.9), (5.0, 2.2, 0.35), (9.5, 26.3, 2.9), 2, *cells[0]),
            mirror_feather((9.0, 24.0, 3.3), (8.0, 3.0, 0.35), (9.0, 24.5, 3.3), -8, *cells[1]),
            mirror_feather((10.0, 22.0, 3.6), (8.0, 3.0, 0.35), (10.0, 22.5, 3.6), -14, *cells[2]),
            mirror_feather((11.0, 20.0, 3.9), (7.0, 3.0, 0.35), (11.0, 20.5, 3.9), -20, *cells[3]),
        ],
    }

    tip_bone = {
        "name": tip,
        "parent": mid,
        "pivot": [s * 16.0, 25.5, 3.0],
        "rotation": [0, 0, s * -14],
        "cubes": [
            mirror_solid((16.0, 25.0, 2.7), (5.0, 0.8, 0.6), GOLD, DARK_GOLD),
            mirror_feather((16.0, 24.5, 3.4), (6.0, 2.8, 0.35), (16.0, 25.0, 3.4), -10, *cells[2]),
            mirror_feather((17.0, 22.8, 3.7), (5.0, 2.8, 0.35), (17.0, 23.3, 3.7), -18, *cells[3]),
            mirror_feather((18.0, 21.3, 4.0), (4.0, 2.5, 0.35), (18.0, 21.8, 4.0), -26, *cells[3]),
            mirror_feather((20.0, 23.8, 3.5), (2.0, 2.0, 0.35), (20.0, 24.3, 3.5), -15, *cells[3]),
            mirror_feather((20.0, 21.8, 4.2), (3.0, 2.0, 0.3), (20.0, 22.3, 4.2), -30, *cells[3]),
        ],
    }

    return [root_bone, mid_bone, tip_bone]


def build():
    body = {
        "name": "body",
        "pivot": [0, 24, 0],
        "cubes": [
            # Compact back plate, sitting just behind the player's torso.
            solid((-1.8, 17.0, 2.0), (3.6, 6.0, 0.7), IVORY, GOLD),
            # Short central feather between the wing roots.
            solid((-1.2, 15.0, 2.6), (2.4, 8.0, 0.4), IVORY, GOLD),
            solid((-1.0, 15.0, 2.65), (2.0, 2.0, 0.45), GOLD, DARK_GOLD),
            # Gold shoulder clasps and a diamond gem at the centre.
            solid((-2.2, 21.5, 2.7), (1.2, 2.0, 0.5), GOLD, DARK_GOLD),
            solid((1.0, 21.5, 2.7), (1.2, 2.0, 0.5), GOLD, DARK_GOLD),
            cube([-1.0, 20.0, 2.75], [2.0, 2.0, 0.4], solid_uv(GOLD),
                 rotation=[0, 0, 45], pivot=[0, 21.0, 2.75]),
        ],
    }

    bones = [body]
    bones.extend(wing(+1))
    bones.extend(wing(-1))

    # Sit the whole wing assembly on the upper back rather than the neck.
    for bone in bones[1:]:
        bone["pivot"][1] -= 2.0
        for c in bone.get("cubes", []):
            c["origin"][1] -= 2.0
            if "pivot" in c:
                c["pivot"][1] -= 2.0

    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": "geometry.angel_wings",
                    "texture_width": TEXTURE,
                    "texture_height": TEXTURE,
                    "visible_bounds_width": 5.0,
                    "visible_bounds_height": 4.0,
                    "visible_bounds_offset": [0, 1.5, 0],
                },
                "bones": bones,
            }
        ],
    }


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "resource_pack", "models", "entity",
                       "angel_wings.geo.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(build(), fh, indent="\t")
        fh.write("\n")
    print("wrote", out)
