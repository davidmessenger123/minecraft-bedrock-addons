"""
Texture/UV coverage audit.

The reference validator checks that files exist and that animation bones
resolve. This checks the things it does not:

  * every cube's box-UV net lies fully inside its texture (no face
    sampling past the edge of the bitmap)
  * the texture is not blank / not a single flat colour
  * every species has a motion profile whose animation set exists
  * every species has a texture, geometry, client entity and spawn rule
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nzlib import face_rects, net_size
from roster import ROSTER
from textures_recipes import RECIPES, species_palette


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    build = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
    bp = os.path.join(build, "behavior_pack")
    rp = os.path.join(build, "resource_pack")

    from PIL import Image

    problems: list[str] = []
    rows = []

    geo_dir = os.path.join(rp, "models", "entity")
    tex_dir = os.path.join(rp, "textures", "entity")
    ent_dir = os.path.join(rp, "entity")
    spawn_dir = os.path.join(bp, "spawn_rules")
    anim_dir = os.path.join(rp, "animations")

    anim_sets = {}
    for f in sorted(os.listdir(anim_dir)):
        d = load(os.path.join(anim_dir, f))
        for name in d["animations"]:
            anim_sets[name] = d["animations"][name]

    species = sorted(f[:-len(".geo.json")] for f in os.listdir(geo_dir) if f.endswith(".geo.json"))

    # --- every marking colour must resolve in the palette that paints it ---
    for spec in ROSTER:
        sid = spec["id"]
        pal = species_palette(spec)
        for raw in RECIPES.get(sid, []):
            params = raw[3] if isinstance(raw, (tuple, list)) and len(raw) > 3 else {}
            for key in ("color", "iris"):
                ref = params.get(key)
                if isinstance(ref, str) and ref not in pal:
                    problems.append(
                        f"{sid}: marking colour '{ref}' is not in the species palette - "
                        f"it would be painted in the cube's own colour")

    for sp in species:
        geo = load(os.path.join(geo_dir, f"{sp}.geo.json"))
        g = geo["minecraft:geometry"][0]
        tex_path = os.path.join(tex_dir, sp, f"{sp}.png")

        if not os.path.exists(tex_path):
            problems.append(f"{sp}: no texture PNG")
            continue
        img = Image.open(tex_path).convert("RGB")
        tw, th = img.size

        # --- UV coverage ---
        cubes = []
        for bone in g["bones"]:
            for cube in bone.get("cubes", []):
                cubes.append(cube)
        if not cubes:
            problems.append(f"{sp}: geometry has no cubes")
            continue

        worst = 0
        for cube in cubes:
            w, h, d = cube["size"]
            nw, nh = net_size(w, h, d)
            ou, ov = cube["uv"]
            if ou < 0 or ov < 0:
                problems.append(f"{sp}: negative uv offset {cube['uv']}")
            if ou + nw > tw or ov + nh > th:
                problems.append(
                    f"{sp}: cube net {nw}x{nh} at uv {cube['uv']} exceeds texture {tw}x{th}")
            worst = max(worst, ou + nw, ov + nh)

        # --- texture is actually painted ---
        colours = img.getcolors(maxcolors=tw * th) or []
        distinct = len(colours)
        if distinct < 8:
            problems.append(f"{sp}: texture looks blank ({distinct} distinct colours)")

        # --- animations ---
        ce = load(os.path.join(ent_dir, f"{sp}.entity.json"))
        desc = ce["minecraft:client_entity"]["description"]
        anim_ids = [v for v in desc["animations"].values() if not v.startswith("controller.")]
        for a in anim_ids:
            if a not in anim_sets:
                problems.append(f"{sp}: animation {a} not found")
        if not anim_ids:
            problems.append(f"{sp}: client entity has no animations")

        # --- other required files ---
        for req, label in (
            (os.path.join(bp, "entities", f"{sp}.json"), "behaviour entity"),
            (os.path.join(spawn_dir, f"{sp}.json"), "spawn rule"),
            (os.path.join(bp, "loot_tables", "entities", f"{sp}.json"), "loot table"),
        ):
            if not os.path.exists(req):
                problems.append(f"{sp}: missing {label}")

        rows.append((sp, tw, th, len(cubes), len(anim_ids), distinct))

    print(f"{'species':22s} {'texture':>10s} {'cubes':>6s} {'anims':>6s} {'colours':>8s}")
    for sp, tw, th, nc, na, ncol in rows:
        print(f"{sp:22s} {str(tw) + 'x' + str(th):>10s} {nc:>6d} {na:>6d} {ncol:>8d}")

    print(f"\n{len(rows)} species audited")
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("Every species has a painted texture, fully UV-covered geometry and animations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
