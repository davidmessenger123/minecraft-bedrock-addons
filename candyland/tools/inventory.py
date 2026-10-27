#!/usr/bin/env python3
"""Build a source-of-truth inventory of every vanilla Bedrock colour texture.

The Mojang bedrock-samples repository is used only as a file/name/dimension
reference.  No vanilla pixels are shipped unchanged: every colour texture is
either regenerated from scratch (blocks) or run through the candy style
transfer (entities, items, UI, effects).
"""
import json
import os
import re
import struct
import subprocess
import sys

SRC = os.environ.get("BEDROCK_SAMPLES",
                     "/tmp/opencode/bedrock-samples/resource_pack")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "build", "inventory.json")

# PBR companion maps are not colour textures.  A few legitimate colour
# textures also end in "_normal" (sandstone_normal, book_normal, ...), so only
# the TGA normal maps (the actual PBR companions in the vanilla samples) are
# excluded by that suffix.
PBR_SUFFIXES = ("_mers", "_mer", "_heightmap", "_height")

# Textures the engine tints at runtime.  We keep these luminance masks
# grayscale and retheme the colormap instead.
TINT_MASKS = [
    r"^grass_top$", r"^grass_side$", r"^grass_side_snowed$",
    r"^grass_carried$", r"^grass_carried_top$", r"^grass_side_carried$",
    r"^leaves_", r"leaves_.*_opaque$",
    r"^mangrove_leaves", r"^pale_oak_leaves",
    r"^tallgrass", r"^fern", r"^double_plant_grass", r"^double_plant_fern",
    r"^reeds$", r"^vine$", r"^waterlily$", r"^lily_pad$",
    r"^short_dry_grass$", r"^tall_dry_grass$", r"^bush$", r"^firefly_bush$",
    r"^hanging_roots$", r"^pale_hanging_moss", r"^pale_moss",
    r"^cave_vines", r"^redstone_dust_",
    r"^water_still_grey$", r"^water_flow_grey$",
]

def is_tint_mask(name):
    # Azalea and cherry leaves use fixed colours in vanilla rather than a
    # biome tint; the other leaves remain luminance masks.
    if name.startswith(("azalea_leaves", "cherry_leaves")):
        return False
    return any(re.search(p, name) for p in TINT_MASKS)

def load_json_relaxed(path):
    s = open(path, encoding="utf-8-sig").read()
    s = re.sub(r"^\s*//.*$", "", s, flags=re.M)
    return json.loads(s)

def dims_tsv(root):
    files = []
    for dirpath, _dirs, names in os.walk(root):
        for fn in names:
            if fn.lower().endswith((".png", ".tga", ".jpg", ".jpeg")):
                files.append(os.path.join(dirpath, fn))
    # identify in chunks; output is comma separated
    rows = {}
    for i in range(0, len(files), 300):
        chunk = files[i:i + 300]
        try:
            out = subprocess.check_output(
                ["magick", "identify", "-format", "%w,%h,%m,%i\n"] + chunk,
                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # fall back to one-by-one so one bad file cannot kill the run
            out = b""
            for f in chunk:
                try:
                    out += subprocess.check_output(
                        ["magick", "identify", "-format", "%w,%h,%m,%i\n", f],
                        stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    pass
        for line in out.decode("utf-8", "replace").splitlines():
            parts = line.rsplit(",", 3)
            if len(parts) != 4:
                continue
            try:
                w, h = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            rows[parts[3]] = (w, h, parts[2])
    return rows

def main():
    root = os.path.join(SRC, "textures")
    dims = dims_tsv(root)
    print("identified", len(dims), "images")

    # runtime colour textures = everything except PBR companions
    by_base = {}
    for path, (w, h, fmt) in dims.items():
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        base, ext = os.path.splitext(rel)
        ext = ext.lower()[1:]
        name = base.split("/")[-1]
        if name.endswith(PBR_SUFFIXES):
            continue
        if name.endswith("_normal") and ext == "tga":
            continue
        # The one mislabelled JPEG in the samples is still a runtime texture.
        rec = by_base.setdefault(base, {"base": base, "ws": [], "h": h,
                                        "exts": [], "src_ext": None,
                                        "size": 0, "fmt": fmt})
        rec["ws"].append(w)
        rec["h"] = h
        rec["exts"].append(ext)
        rec["fmt"] = fmt
        try:
            rec["size"] += os.path.getsize(path)
        except OSError:
            pass
        if ext == "png" or rec["src_ext"] is None:
            rec["src_ext"] = ext
    # Add the two root atlases that identify() may not have listed due to
    # extension filtering.
    for extra in ("flame_atlas.png", "forcefield_atlas.png"):
        p = os.path.join(root, extra)
        if os.path.isfile(p):
            base = extra[:-4]
            if base not in by_base:
                out = subprocess.check_output(
                    ["magick", "identify", "-format", "%w %h", p])
                w, h = map(int, out.split())
                by_base[base] = {"base": base, "ws": [w], "h": h,
                                 "exts": ["png"], "src_ext": "png",
                                 "size": os.path.getsize(p), "fmt": "PNG"}

    # animated flipbooks
    flip = load_json_relaxed(os.path.join(SRC, "textures",
                                          "flipbook_textures.json"))
    animated = {}
    for e in flip:
        p = e.get("flipbook_texture", "")
        if p.startswith("textures/"):
            p = p[len("textures/"):]
        animated[p] = e

    terrain = load_json_relaxed(os.path.join(SRC, "textures",
                                             "terrain_texture.json"))
    items = load_json_relaxed(os.path.join(SRC, "textures",
                                          "item_texture.json"))
    used = set()
    for d in (terrain, items):
        for v in d.get("texture_data", {}).values():
            stack = [v.get("textures", v)]
            while stack:
                x = stack.pop()
                if isinstance(x, str):
                    if x.startswith("textures/"):
                        used.add(x[len("textures/"):])
                elif isinstance(x, list):
                    stack.extend(x)
                elif isinstance(x, dict):
                    if "path" in x:
                        stack.append(x["path"])
                    if "textures" in x:
                        stack.append(x["textures"])
    # include direct references discovered in texture_set files
    # (sound/no-op for colour coverage; useful for the report)

    out = []
    for base in sorted(by_base):
        rec = by_base[base]
        name = base.split("/")[-1]
        w = min(rec["ws"]) if rec["ws"] else 0
        h = rec["h"]
        cat = base.split("/")[0]
        frames = h // w if w and h > w and h % w == 0 else 1
        out.append({
            "base": base,
            "name": name,
            "category": cat,
            "w": w,
            "h": h,
            "frames": frames,
            "exts": sorted(set(rec["exts"])),
            "src_ext": rec["src_ext"],
            "fmt": rec["fmt"],
            "size": rec["size"],
            "animated": base in animated,
            "flipbook": animated.get(base),
            "tint_mask": (is_tint_mask(name)
                          and cat in ("blocks", "environment", "particle", "particles")),
            "used": base in used,
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({
            "source": SRC,
            "colormaps": sorted(os.listdir(os.path.join(root, "colormap")))
            if os.path.isdir(os.path.join(root, "colormap")) else [],
            "textures": out,
        }, fh, indent=1)
    from collections import Counter
    c = Counter(t["category"] for t in out)
    print("colour textures:", len(out))
    for k, v in c.most_common():
        print(f"  {k:12s} {v}")
    print("tint masks:", sum(t["tint_mask"] for t in out))
    print("animated:", sum(t["animated"] for t in out))
    print("tga-only:", sum(t["exts"] == ["tga"] for t in out))
    print("wrote", OUT)

if __name__ == "__main__":
    main()
