"""
Extract a candidate colour palette for each species from its reference photo.

Photographs are lit and noisy, so the result is only a starting point: the
script quantises the subject region, drops background extremes, and reports
the dominant hues. The palettes in tools/roster.py are the ones that actually
ship, corrected by eye against these references.

Usage: python3 tools/extract_palette.py [refs_dir]
"""

from __future__ import annotations

import colorsys
import os
import sys
from collections import Counter

from PIL import Image


def dominant(path: str, count: int = 5):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # centre crop: reference photos usually frame the subject in the middle
    im = im.crop((int(w * 0.18), int(h * 0.12), int(w * 0.82), int(h * 0.88)))
    im = im.resize((96, 96))
    px = list(im.getdata())

    # Remove the background: the border of the frame is almost always sky,
    # water, foliage or a studio sweep.
    border = []
    for x in range(96):
        border += [px[x], px[95 * 96 + x]]
    for y in range(96):
        border += [px[y * 96], px[y * 96 + 95]]
    def near_bg(c):
        return sum((c[i] - bg[i]) ** 2 for i in range(3)) < 55 ** 2
    bg = [sum(c[i] for c in border) // len(border) for i in range(3)]

    bins = Counter()
    for r, g, b in px:
        if near_bg((r, g, b)):
            continue
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if vv < 0.13 or vv > 0.97:
            continue
        # quantise
        qr = (r // 32) * 32 + 16
        qg = (g // 32) * 32 + 16
        qb = (b // 32) * 32 + 16
        bins[(qr, qg, qb)] += 1

    out = []
    for (r, g, b), n in bins.most_common(60):
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if ss < 0.12 and len(out) and all(
                colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)[1] < 0.15
                for c in out):
            continue
        # keep only reasonably saturated or neutral-dominant colours
        out.append((r, g, b))
        if len(out) >= count:
            break
    return out


def main() -> int:
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "refs")
    d = os.path.normpath(d)
    for f in sorted(os.listdir(d)):
        if not f.endswith(".jpg"):
            continue
        sid = f[:-4]
        cols = dominant(os.path.join(d, f))
        hexes = " ".join("#%02X%02X%02X" % c for c in cols)
        print(f"{sid:20s} {hexes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
