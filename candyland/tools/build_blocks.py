"""Render every block texture into the resource pack."""
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import blocks  # noqa: E402
import pnglib  # noqa: E402
import restyle  # noqa: E402
from candy import Canvas  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "resource_pack")
OUT = os.path.join(PACK, "textures", "blocks")


def strip(c, frames):
    out = Canvas(c.w, c.h * frames)
    for f in range(frames):
        for y in range(c.h):
            for x in range(c.w):
                cc = c.get(x, y)
                out.set(x, f * c.h + y, cc, cc[3])
    return out


def build(limit=None):
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    inv = json.load(open(os.path.join(ROOT, "build", "inventory.json")))
    entries = [t for t in inv["textures"] if t["category"] == "blocks"]
    if limit:
        entries = entries[:limit]
    t0 = time.time()
    written = 0
    problems = []
    for i, e in enumerate(entries):
        c = blocks.block_canvas(e["name"], e)
        scale = restyle.scale_for(e)
        base_h = e["h"] // e["frames"]
        exp_w = e["w"] * scale
        exp_h = base_h * scale * e["frames"]
        if e["frames"] > 1 and c.w == exp_w and c.h == 32 and exp_h > 32:
            c = strip(c, e["frames"])
        if (c.w, c.h) != (exp_w, exp_h):
            problems.append((e["name"], (c.w, c.h), (exp_w, exp_h)))
        rel = e["base"].split("/", 1)[1] if "/" in e["base"] else e["base"]
        path = os.path.join(OUT, *rel.split("/")) + "." + e["src_ext"]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if e["src_ext"] == "tga":
            pnglib.tga_write(path, c.w, c.h, c.px)
        else:
            pnglib.png_write(path, c.w, c.h, c.px)
        written += 1
        if i % 200 == 0:
            print("  %4d/%d  %5.1fs" % (i, len(entries), time.time() - t0))
    # atlas config is copied verbatim: names and layout are unchanged
    tex = os.path.join(PACK, "textures")
    os.makedirs(tex, exist_ok=True)
    src_cfg = os.path.join(restyle.SRC, "terrain_texture.json")
    dst_cfg = os.path.join(tex, "terrain_texture.json")
    shutil.copyfile(src_cfg, dst_cfg)
    # The sample config has two stale aliases for pale hanging moss.  Point
    # them at the textures that actually exist so no atlas lookup can fail.
    with open(dst_cfg, encoding="utf-8") as fh:
        cfg = fh.read()
    cfg = cfg.replace("textures/blocks/hanging_pale_moss_",
                      "textures/blocks/pale_hanging_moss_")
    with open(dst_cfg, "w", encoding="utf-8") as fh:
        fh.write(cfg)
    print("blocks: %d written in %.1fs" % (written, time.time() - t0))
    if problems:
        print("size problems:", len(problems))
        for p in problems[:20]:
            print("  ", p)
    with open(os.path.join(ROOT, "build", "block_problems.json"), "w") as fh:
        json.dump(problems, fh, indent=1)


if __name__ == "__main__":
    build(int(sys.argv[1]) if len(sys.argv) > 1 else None)
