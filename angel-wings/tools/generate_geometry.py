#!/usr/bin/env python3
"""Generate the layered Angel Wings Bedrock geometry.

Run from the project root:

    python3 tools/generate_geometry.py

The wings are authored in player-model space: the back of the player is +Z,
the shoulders are at y=24, and one model unit is 1/16 block.  The mesh is a
layered set of feather plates around a solid gold-and-ivory leading arm.  The
redesigned version adds a shoulder joint, scapulars, coverts, alula feathers,
long secondaries and staggered primaries, with transparent thin edges so the
old rectangular gold frames disappear in game.
"""
import json
import os


TEXTURE = 128
TRANSPARENT = (0, 96)
GOLD = (0, 64)
IVORY = (32, 64)
SHADE = (64, 64)
DARK_GOLD = (96, 64)


def face(uv, size=(32, 32)):
    return {"uv": list(uv), "uv_size": list(size)}


def feather_uv(cell_x, cell_y):
    """Cut-out vane on the broad faces; transparent thin edges.

    The old trim used solid gold on every edge, which drew a rectangular cage
    around each feather in game.  The vane silhouette already includes its own
    gold rim, so the side faces should be transparent.
    """
    return {
        "north": face((cell_x, cell_y)),
        "south": face((cell_x, cell_y)),
        "east": face(TRANSPARENT, (1, 1)),
        "west": face(TRANSPARENT, (1, 1)),
        "up": face(TRANSPARENT, (1, 1)),
        "down": face(TRANSPARENT, (1, 1)),
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


def solid(origin, size, swatch, edge=None, rotation=None, pivot=None):
    return cube(origin, size, solid_uv(swatch, edge), rotation=rotation,
                pivot=pivot)


def wing(side):
    """Build one four-layer wing. side=+1 extends +X, side=-1 extends -X."""
    s = side
    row = 0 if side > 0 else 32

    def cell(variant):
        return (variant * 32, row)

    def mirror_origin(origin, size):
        ox, oy, oz = origin
        w, h, d = size
        return [ox, oy, oz] if side > 0 else [-(ox + w), oy, oz]

    def mirror_pivot(pivot):
        return [pivot[0], pivot[1], pivot[2]] if side > 0 else [-pivot[0], pivot[1], pivot[2]]

    def mirror_rotation(rz):
        return rz if side > 0 else -rz

    def feather_cube(origin, size, pivot, rz, variant):
        return feather(mirror_origin(origin, size), size,
                       mirror_pivot(pivot), mirror_rotation(rz),
                       *cell(variant))

    def solid_cube(origin, size, swatch, edge=None):
        return solid(mirror_origin(origin, size), size, swatch, edge)

    root = "left_wing" if side > 0 else "right_wing"
    mid = "left_wing_mid" if side > 0 else "right_wing_mid"
    tip = "left_wing_tip" if side > 0 else "right_wing_tip"

    # ------------------------------------------------------------------ root
    root_cubes = [
        # Shoulder cap and first arm segment.
        solid_cube((0.8, 24.0, 2.5), (2.6, 2.4, 1.0), GOLD, DARK_GOLD),
        solid_cube((1.2, 25.15, 2.95), (8.5, 0.8, 0.7), IVORY, GOLD),
        solid_cube((1.3, 25.95, 3.0), (7.9, 0.25, 0.45), GOLD, DARK_GOLD),
        solid_cube((8.6, 24.6, 2.65), (1.7, 2.0, 1.2), GOLD, DARK_GOLD),

        # Scapular feathers tucked against the player's back.
        feather_cube((1.8, 23.7, 2.55), (5.6, 3.4, 0.32),
                     (1.8, 24.4, 2.55), -8, 0),
        feather_cube((3.4, 22.7, 2.65), (5.8, 3.3, 0.32),
                     (3.4, 23.3, 2.65), -16, 0),
        feather_cube((5.0, 21.8, 2.75), (5.4, 3.1, 0.32),
                     (5.0, 22.4, 2.75), -23, 0),

        # Overlapping upper coverts.
        feather_cube((2.2, 25.4, 3.25), (5.2, 2.7, 0.34),
                     (2.2, 25.9, 3.25), 4, 0),
        feather_cube((4.2, 25.1, 3.40), (5.8, 2.9, 0.34),
                     (4.2, 25.6, 3.40), -1, 0),
        feather_cube((6.2, 24.8, 3.55), (5.8, 3.0, 0.34),
                     (6.2, 25.3, 3.55), -6, 1),
        feather_cube((8.0, 24.4, 3.65), (4.8, 2.8, 0.34),
                     (8.0, 24.9, 3.65), -10, 1),

        # Darker underwing coverts sit behind the bright layers.
        feather_cube((2.0, 23.0, 2.18), (8.0, 4.8, 0.30),
                     (2.0, 23.8, 2.18), -12, 1),
        feather_cube((4.8, 21.8, 2.22), (8.5, 4.8, 0.30),
                     (4.8, 22.6, 2.22), -20, 2),
        feather_cube((7.8, 20.8, 2.26), (6.4, 4.2, 0.30),
                     (7.8, 21.5, 2.26), -27, 2),

        # Alula feathers at the wrist, pointing up and out.
        feather_cube((8.1, 25.5, 4.00), (3.0, 2.4, 0.30),
                     (8.1, 25.9, 4.00), 14, 0),
        feather_cube((8.6, 24.7, 4.12), (3.8, 2.2, 0.30),
                     (8.6, 25.1, 4.12), -5, 1),
    ]

    root_bone = {
        "name": root,
        "parent": "body",
        "pivot": [s * 1.5, 23.0, 2.8],
        "rotation": [0, 0, s * 10],
        "cubes": root_cubes,
    }

    # ------------------------------------------------------------------- mid
    mid_cubes = [
        # Second arm segment with a visible joint and a bright top ridge.
        solid_cube((8.8, 25.1, 3.0), (7.8, 0.7, 0.65), IVORY, GOLD),
        solid_cube((9.0, 25.85, 3.05), (7.1, 0.22, 0.4), GOLD, DARK_GOLD),
        solid_cube((15.5, 24.6, 2.65), (1.6, 1.7, 1.0), GOLD, DARK_GOLD),

        # Upper coverts bridge the shoulder and the long flight feathers.
        feather_cube((9.3, 24.9, 3.45), (6.0, 2.8, 0.34),
                     (9.3, 25.4, 3.45), -2, 0),
        feather_cube((11.7, 24.5, 3.60), (6.2, 3.0, 0.34),
                     (11.7, 25.0, 3.60), -7, 1),

        # Long secondaries fan down from the elbow.
        feather_cube((9.8, 23.6, 3.75), (7.8, 3.8, 0.34),
                     (9.8, 24.3, 3.75), -8, 1),
        feather_cube((11.2, 22.3, 3.85), (8.4, 4.0, 0.34),
                     (11.2, 23.0, 3.85), -14, 1),
        feather_cube((12.6, 21.0, 3.95), (8.2, 4.0, 0.34),
                     (12.6, 21.7, 3.95), -20, 2),
        feather_cube((14.0, 19.8, 4.05), (7.4, 3.8, 0.34),
                     (14.0, 20.4, 4.05), -26, 2),
        feather_cube((15.0, 18.7, 4.15), (6.2, 3.4, 0.34),
                     (15.0, 19.3, 4.15), -32, 2),

        # Underwing secondaries, deliberately darker and broader.
        feather_cube((10.4, 22.8, 2.45), (8.0, 4.2, 0.30),
                     (10.4, 23.5, 2.45), -11, 2),
        feather_cube((12.5, 21.0, 2.55), (8.2, 4.2, 0.30),
                     (12.5, 21.7, 2.55), -20, 3),
        feather_cube((14.4, 19.5, 2.65), (6.4, 3.8, 0.30),
                     (14.4, 20.1, 2.65), -28, 3),
    ]

    mid_bone = {
        "name": mid,
        "parent": root,
        "pivot": [s * 9.0, 23.5, 3.0],
        "rotation": [0, 0, s * -8],
        "cubes": mid_cubes,
    }

    # ------------------------------------------------------------------- tip
    tip_cubes = [
        # Wrist segment and final gold joint.
        solid_cube((15.8, 24.9, 3.0), (6.8, 0.65, 0.6), IVORY, GOLD),
        solid_cube((16.0, 25.6, 3.05), (6.2, 0.22, 0.4), GOLD, DARK_GOLD),
        solid_cube((21.6, 24.5, 2.65), (1.2, 1.3, 0.9), GOLD, DARK_GOLD),

        # Small upper coverts at the wrist.
        feather_cube((16.4, 25.4, 3.90), (4.2, 2.0, 0.32),
                     (16.4, 25.8, 3.90), 2, 0),
        feather_cube((18.6, 25.0, 4.00), (3.8, 1.9, 0.32),
                     (18.6, 25.4, 4.00), -4, 0),

        # Staggered primaries form the pointed outer silhouette.
        feather_cube((16.2, 24.4, 4.15), (7.2, 3.1, 0.34),
                     (16.2, 24.9, 4.15), -10, 2),
        feather_cube((17.1, 23.0, 4.20), (7.4, 3.1, 0.34),
                     (17.1, 23.5, 4.20), -16, 3),
        feather_cube((18.0, 21.7, 4.25), (6.8, 3.0, 0.34),
                     (18.0, 22.2, 4.25), -22, 3),
        feather_cube((19.0, 20.5, 4.30), (6.0, 2.8, 0.34),
                     (19.0, 21.0, 4.30), -28, 3),
        feather_cube((20.0, 19.4, 4.35), (5.2, 2.6, 0.34),
                     (20.0, 19.9, 4.35), -34, 3),
        feather_cube((21.0, 18.4, 4.40), (4.2, 2.4, 0.34),
                     (21.0, 18.9, 4.40), -40, 3),
        feather_cube((21.6, 17.6, 4.45), (3.2, 2.1, 0.34),
                     (21.6, 18.0, 4.45), -46, 3),

        # Darker flight feathers behind the primaries.
        feather_cube((17.8, 22.2, 2.55), (8.5, 4.6, 0.30),
                     (17.8, 22.8, 2.55), -16, 3),
        feather_cube((19.8, 20.0, 2.65), (7.2, 4.2, 0.30),
                     (19.8, 20.7, 2.65), -26, 3),
    ]

    tip_bone = {
        "name": tip,
        "parent": mid,
        "pivot": [s * 16.0, 23.5, 3.0],
        "rotation": [0, 0, s * -14],
        "cubes": tip_cubes,
    }

    return [root_bone, mid_bone, tip_bone]


def build():
    body = {
        "name": "body",
        "pivot": [0, 24, 0],
        "cubes": [
            # Layered back plate with a gold rim and a central spine feather.
            solid((-1.6, 17.0, 2.0), (3.2, 6.0, 0.7), IVORY, GOLD),
            solid((-2.0, 17.3, 2.05), (0.4, 5.4, 0.8), GOLD, DARK_GOLD),
            solid((1.6, 17.3, 2.05), (0.4, 5.4, 0.8), GOLD, DARK_GOLD),
            solid((-1.1, 15.1, 2.65), (2.2, 7.6, 0.4), IVORY, GOLD),
            solid((-0.9, 14.8, 2.70), (1.8, 2.0, 0.45), GOLD, DARK_GOLD),
            solid((-3.0, 22.4, 2.55), (6.0, 1.1, 0.7), GOLD, DARK_GOLD),
            solid((-2.2, 21.4, 2.7), (1.2, 2.0, 0.5), GOLD, DARK_GOLD),
            solid((1.0, 21.4, 2.7), (1.2, 2.0, 0.5), GOLD, DARK_GOLD),
            cube([-1.0, 20.0, 2.75], [2.0, 2.0, 0.4], solid_uv(GOLD),
                 rotation=[0, 0, 45], pivot=[0, 21.0, 2.75]),
        ],
    }

    bones = [body]
    bones.extend(wing(+1))
    bones.extend(wing(-1))

    # Sit the wing assembly on the upper back rather than the neck.
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
                    "visible_bounds_width": 5.5,
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
