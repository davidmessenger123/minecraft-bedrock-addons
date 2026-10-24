"""
Find coplanar, overlapping faces in the geometry.

Two boxes whose faces lie in the same plane and overlap in the other two axes
z-fight: the renderer has to choose which one to draw, and it alternates
between frames. The result is a texture that flickers.

Usage: python3 tools/check_zfight.py
"""
from __future__ import annotations

import glob
import json
import os
import sys

FACES = ("up", "down", "east", "west", "north", "south")
# (axis, sign): axis 0=x, 1=y, 2=z
NORMALS = {
    "up": (1, 1), "down": (1, -1),
    "east": (0, 1), "west": (0, -1),
    "north": (2, 1), "south": (2, -1),
}


def face_plane(cube, face):
    """Return (axis, sign, plane coordinate, the two other axes' ranges)."""
    axis, sign = NORMALS[face]
    o, s = cube["origin"], cube["size"]
    other = [i for i in range(3) if i != axis]
    if sign > 0:
        coord = o[axis] + s[axis]
    else:
        coord = o[axis]
    lo = [o[other[0]], o[other[1]]]
    hi = [o[other[0]] + s[other[0]], o[other[1]] + s[other[1]]]
    return axis, sign, coord, lo, hi


def overlap(a, b, tol=0.0):
    return (min(a[1], b[1]) - max(a[0], b[0]) > tol
            and min(b[1], b[1]) - max(a[0], b[0]) > tol)


def main() -> int:
    geo_dir = "build/resource_pack/models/entity"
    problems = []
    total = 0
    for f in sorted(glob.glob(os.path.join(geo_dir, "*.geo.json"))):
        sp = os.path.basename(f)[:-len(".geo.json")]
        d = json.load(open(f, encoding="utf-8"))
        cubes = []
        for bi, bone in enumerate(d["minecraft:geometry"][0]["bones"]):
            for ci, c in enumerate(bone.get("cubes", [])):
                cubes.append((f"{bone['name']}#{ci}", c))
        for i in range(len(cubes)):
            ni, ci = cubes[i]
            for j in range(i + 1, len(cubes)):
                nj, cj = cubes[j]
                for fi in FACES:
                    ai, si, coordi, loi, hii = face_plane(ci, fi)
                    for fj in FACES:
                        aj, sj, coordj, loj, hij = face_plane(cj, fj)
                        if ai != aj or coordi != coordj:
                            continue
                        # only two faces pointing the SAME way can z-fight;
                        # opposite faces are back-face culled
                        if si != sj:
                            continue
                        # same plane: do they overlap in the other two axes?
                        ov = True
                        for k in range(2):
                            if min(hii[k], hij[k]) - max(loi[k], loj[k]) <= 0:
                                ov = False
                                break
                        if ov:
                            total += 1
                            problems.append(
                                f"{sp}: {ni} face '{fi}' and {nj} face '{fj}' are "
                                f"coplanar at {coordi} on axis {ai}")
    print(f"{total} coplanar overlapping face pair(s)")
    if problems:
        by_species = {}
        for p in problems:
            by_species.setdefault(p.split(":")[0], []).append(p)
        print(f"in {len(by_species)} species")
        for sp in sorted(by_species)[:12]:
            print(f"  {sp}: {len(by_species[sp])}")
            for p in by_species[sp][:3]:
                print(f"      {p.split(': ', 1)[1]}")
        return 1
    print("no coplanar faces: no z-fighting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
