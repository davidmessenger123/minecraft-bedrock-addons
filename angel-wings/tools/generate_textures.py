#!/usr/bin/env python3
"""Generate the Angel Wings entity feather texture and inventory icon.

Pure-stdlib PNG writer (no Pillow needed) so the art can be regenerated on any
machine with Python 3.  Run from the project root:

    python3 tools/generate_textures.py
"""
import math
import os
import struct
import zlib


# --------------------------------------------------------------------------- #
# PNG output
# --------------------------------------------------------------------------- #
def write_png(path, width, height, pixels):
    """pixels: list of rows, each row a list of (r, g, b, a) tuples."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter type 0 (None)
        for r, g, b, a in row:
            raw.extend((r, g, b, a))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)


# --------------------------------------------------------------------------- #
# Small drawing helpers
# --------------------------------------------------------------------------- #
def clamp(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)


def mix(c1, c2, t):
    return tuple(clamp(c1[i] * (1 - t) + c2[i] * t) for i in range(4))


def put(px, width, height, x, y, color, alpha=1.0):
    if 0 <= int(x) < width and 0 <= int(y) < height:
        x, y = int(x), int(y)
        if alpha >= 1.0:
            px[y][x] = color
        else:
            px[y][x] = mix(px[y][x], color, alpha)


def line(px, w, h, x1, y1, x2, y2, color, alpha=1.0):
    x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        put(px, w, h, x1, y1, color, alpha)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def poly(px, w, h, points, fill, outline=None):
    """Scanline-fill an integer polygon, then stroke its outline."""
    ys = [p[1] for p in points]
    for y in range(max(0, int(min(ys))), min(h - 1, int(max(ys))) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if y1 == y2:
                continue
            if min(y1, y2) <= y < max(y1, y2):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(math.ceil(xs[i]))),
                           min(w - 1, int(math.floor(xs[i + 1]))) + 1):
                put(px, w, h, x, y, fill)
    if outline:
        for i in range(len(points)):
            line(px, w, h, *points[i], *points[(i + 1) % len(points)], outline)


# --------------------------------------------------------------------------- #
# Entity texture: a seamless-ish field of layered ivory feathers
# --------------------------------------------------------------------------- #
def generate_entity_texture(path):
    W = H = 64
    px = [[(0, 0, 0, 255) for _ in range(W)] for _ in range(H)]

    # Warm parchment background, slightly darker than the feathers so the
    # outlines and overlaps stay readable on small cubes.
    for y in range(H):
        t = y / (H - 1)
        r = 232 - 22 * t
        g = 214 - 26 * t
        b = 180 - 35 * t
        for x in range(W):
            wave = 1.5 * math.sin(x * 0.45 + y * 0.21)
            px[y][x] = (clamp(r + wave), clamp(g + wave), clamp(b + wave), 255)

    cream_hi = (255, 251, 240, 255)
    cream = (252, 244, 227, 255)
    cream_mid = (244, 232, 209, 255)
    shade = (216, 194, 160, 255)
    outline = (166, 129, 78, 255)
    shaft = (214, 190, 152, 255)
    gold_hi = (255, 240, 184, 255)
    gold = (230, 187, 92, 255)
    gold_dark = (166, 119, 42, 255)

    def feather(cx, top, bottom, halfw, base, tip, strength=1.0):
        h = bottom - top
        for y in range(top, bottom + 1):
            t = (y - top) / max(1, h)
            wid = halfw * max(0.06, 1.0 - t ** 1.35)
            x0 = int(round(cx - wid))
            x1 = int(round(cx + wid))
            for x in range(x0, x1 + 1):
                col = mix(base, tip, t * 0.5)
                if x == x0:
                    col = cream_hi
                elif x == x1:
                    col = shade
                put(px, W, H, x, y, col)
            put(px, W, H, x0 - 1, y, outline, 0.75)
            put(px, W, H, x1 + 1, y, outline, 0.75)
            if y == bottom:
                put(px, W, H, cx, y + 1, outline, 0.65)

        # Shaft: warm line with a lit left side.
        for y in range(top + 2, bottom - 1):
            sx = int(round(cx + math.sin(y * 0.5) * 0.25))
            put(px, W, H, sx, y, shaft)
            put(px, W, H, sx - 1, y, cream_hi)

        # Two soft barbs per side, slanted toward the tip.
        for i in range(2):
            yy = top + 5 + int(i * (h - 10) / 1)
            spread = halfw * (0.8 - 0.35 * i)
            for side in (-1, 1):
                line(px, W, H, cx + side * 1.5, yy,
                     cx + side * spread, yy + 3, outline, 0.18 * strength)
                line(px, W, H, cx + side * 1.5, yy - 1,
                     cx + side * spread, yy + 2, cream_hi, 0.25 * strength)

        # A warm glint near the tip.
        if int(cx) % 2 == 0:
            put(px, W, H, cx, max(top, bottom - 3), gold, 0.35)

    # Draw the lowest row first so the row above overlaps its base.  The rows
    # overlap by about a third, hiding the flat feather bases.
    for row, (top, bottom, halfw, base) in enumerate([
        (36, 62, 10.0, cream_mid),
        (19, 43, 9.6, cream),
        (3, 24, 9.2, cream_hi),
    ]):
        offset = 0 if row % 2 == 0 else 8
        for i in range(-1, 5):
            feather(offset + i * 16, top, bottom, halfw, base, cream_mid)

    # Gold leading-edge trim.  The arm cubes sample v=0..12, so this reads as
    # a clean metallic rim along the top of the wing.
    for x in range(W):
        put(px, W, H, x, 0, gold_hi)
        put(px, W, H, x, 1, gold)
        put(px, W, H, x, 2, gold_dark)

    # Sparse pinprick highlights for a hand-painted feel.
    for i in range(55):
        x = (i * 37 + 11) % W
        y = 6 + ((i * 23 + 7) % (H - 8))
        put(px, W, H, x, y, cream_hi, 0.22)

    # Keep the worn-wing sheet fully opaque; translucent pixels would put the
    # armor material into a sorted pass and can make the wings flicker.
    for y in range(H):
        for x in range(W):
            r, g, b, _ = px[y][x]
            px[y][x] = (r, g, b, 255)

    write_png(path, W, H, px)


# --------------------------------------------------------------------------- #
# Inventory icon: a clean symmetric wing pair on transparency
# --------------------------------------------------------------------------- #
def generate_item_icon(path):
    W = H = 64
    px = [[(0, 0, 0, 0) for _ in range(W)] for _ in range(H)]

    gold_hi = (255, 238, 176, 255)
    gold = (225, 184, 92, 255)
    gold_dark = (158, 116, 48, 255)
    white = (255, 255, 255, 255)
    cream = (250, 241, 222, 255)
    cream_hi = (255, 253, 246, 255)
    cream_mid = (238, 224, 198, 255)
    shadow = (207, 185, 149, 255)

    # One broad wing silhouette: smooth leading edge, five deep feather tips.
    left = [
        (30, 36), (24, 27), (17, 20), (10, 15), (4, 12), (2, 13),
        (4, 24), (8, 22), (10, 31), (14, 29), (16, 38), (20, 35),
        (22, 43), (26, 40), (28, 45), (30, 42),
    ]
    notches = [(8, 22), (14, 29), (20, 35), (26, 40)]
    tops = [(17, 19), (21, 23), (25, 27), (28, 31)]
    right = [(W - 1 - x, y) for x, y in left]
    right_notches = [(W - 1 - x, y) for x, y in notches]
    right_tops = [(W - 1 - x, y) for x, y in tops]

    def wing(points, notch_pts, top_pts):
        poly(px, W, H, points, cream, gold_dark)
        # Bright leading edge (the first six points trace the top arc).
        for i in range(5):
            line(px, W, H, *points[i], *points[i + 1], gold)
            line(px, W, H, points[i][0], points[i][1] + 1,
                 points[i + 1][0], points[i + 1][1] + 1, cream_hi)
        # Warm shadow along the scalloped trailing edge.
        for i in range(6, len(points) - 1):
            line(px, W, H, *points[i], *points[i + 1], shadow)
        # Internal feather divisions from each notch toward the leading edge.
        for (nx, ny), (tx, ty) in zip(notch_pts, top_pts):
            line(px, W, H, nx, ny, tx, ty, shadow)
            line(px, W, H, nx, ny - 1, tx, ty - 1, cream_hi)
            # A few short barbs on the lower side of each feather.
            mx = (nx + tx) // 2
            my = (ny + ty) // 2
            line(px, W, H, mx, my, mx + 3, my + 3, shadow, 0.55)
            line(px, W, H, mx, my + 1, mx + 3, my + 4, cream_hi, 0.55)
        # Sweeping main shaft.
        line(px, W, H, 29, 40, 3, 14, gold, 0.9)
        line(px, W, H, 29, 39, 3, 13, cream_hi, 0.9)
        # A highlight glint near the outer tip.
        line(px, W, H, 4, 16, 8, 19, white, 0.8)

    wing(left, notches, tops)
    wing(right, right_notches, right_tops)

    # Central clasp: a gold diamond cradling a sky-blue gem.
    poly(px, W, H, [(32, 30), (40, 39), (32, 50), (24, 39)], gold, gold_dark)
    poly(px, W, H, [(32, 33), (37, 39), (32, 47), (27, 39)],
         (104, 180, 240, 255), (48, 108, 176, 255))
    poly(px, W, H, [(32, 34), (36, 39), (32, 40), (28, 39)],
         (197, 234, 255, 255), None)
    put(px, W, H, 30, 37, white)
    put(px, W, H, 31, 36, white)
    put(px, W, H, 32, 38, white)
    put(px, W, H, 34, 41, (146, 207, 252, 255))
    line(px, W, H, 26, 43, 29, 43, gold_hi)

    # A small four-point sparkle above the clasp.
    line(px, W, H, 32, 6, 32, 16, gold_hi)
    line(px, W, H, 27, 11, 37, 11, gold_hi)
    line(px, W, H, 30, 9, 30, 13, gold)
    line(px, W, H, 34, 9, 34, 13, gold)
    put(px, W, H, 32, 11, white)
    put(px, W, H, 23, 18, gold_hi, 0.9)
    put(px, W, H, 41, 18, gold_hi, 0.9)

    write_png(path, W, H, px)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate_entity_texture(os.path.join(root, "resource_pack", "textures",
                                         "entity", "angel_wings.png"))
    generate_item_icon(os.path.join(root, "resource_pack", "textures",
                                    "items", "angel_wings.png"))
    print("wrote entity texture and item icon")
