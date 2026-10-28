#!/usr/bin/env python3
"""Generate the Angel Wings entity feather atlas and inventory icon.

Pure-stdlib PNG writer (no Pillow needed) so the art can be regenerated on any
machine with Python 3.  Run from the project root:

    python3 tools/generate_textures.py

The entity atlas is 128x128.  The top two rows are eight 32x32 feather cells:
row 0 points right (left wing), row 1 points left (right wing).  Row 2 holds
four opaque material swatches used for leading edges and the back plate.
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
# Entity texture: eight cut-out feather cells plus opaque trim swatches
# --------------------------------------------------------------------------- #
CREAM_HI = (255, 252, 242, 255)
CREAM = (250, 240, 220, 255)
CREAM_MID = (238, 222, 192, 255)
SHADE = (205, 180, 140, 255)
OUTLINE = (148, 109, 58, 255)
SHAFT = (222, 196, 152, 255)
GOLD_HI = (255, 242, 184, 255)
GOLD = (226, 178, 76, 255)
GOLD_DARK = (158, 112, 38, 255)


def _feather_pixel(px, W, H, cell_x, cell_y, local_x, local_y, direction, color):
    x = cell_x + (local_x if direction > 0 else 31 - local_x)
    put(px, W, H, x, cell_y + local_y, color)


def draw_feather_cell(px, W, H, cell_x, cell_y, direction, tip_x, half_h, variant):
    """Draw one transparent feather cell pointing left or right.

    The vane is asymmetrical: a tighter leading edge, a fuller trailing edge
    and a tapered point.  Gold is painted onto the silhouette and shaft rather
    than around the 32x32 cell, so it does not become a rectangular frame.
    """
    base_x = 2
    span = max(1, tip_x - base_x)
    top_edge = []
    bottom_edge = []

    for lx in range(base_x, tip_x + 1):
        t = (lx - base_x) / span
        # Broad near the base, then a deliberate tapered point.
        width = half_h * (math.sin(math.pi * min(1.0, t * 1.04)) ** 0.64)
        if t > 0.78:
            width *= max(0.18, 1.0 - ((t - 0.78) / 0.22) * 0.72)
        if variant == 0:
            width *= 0.92
        if width < 0.45:
            width = 0.45
        top = 16 - width * (0.88 if variant < 2 else 0.74)
        bottom = 16 + width * (1.10 if variant < 2 else 1.18)
        top_edge.append((lx, top))
        bottom_edge.append((lx, bottom))
        for ly in range(int(round(top)), int(round(bottom)) + 1):
            if t < 0.58:
                color = mix(CREAM_HI, CREAM, t / 0.58)
            else:
                color = mix(CREAM, GOLD, (t - 0.58) / 0.42)
            # Warm rim and a cool-ish upper edge.
            if ly <= int(round(top)) + 1:
                color = mix(color, GOLD_HI, 0.55)
            elif ly >= int(round(bottom)) - 1:
                color = mix(color, SHADE, 0.55)
            _feather_pixel(px, W, H, cell_x, cell_y, lx, ly, direction, color)

    # Outline the silhouette, including the tapered tip.
    for lx, top in top_edge:
        _feather_pixel(px, W, H, cell_x, cell_y, lx, int(round(top)),
                       direction, OUTLINE)
    for lx, bottom in bottom_edge:
        _feather_pixel(px, W, H, cell_x, cell_y, lx, int(round(bottom)),
                       direction, OUTLINE)

    # Shaft and a lit upper edge.
    for lx in range(base_x, tip_x + 1):
        _feather_pixel(px, W, H, cell_x, cell_y, lx, 16, direction, SHAFT)
        _feather_pixel(px, W, H, cell_x, cell_y, lx, 15, direction, CREAM_HI)
        if lx % 3 == 0:
            _feather_pixel(px, W, H, cell_x, cell_y, lx, 17, direction,
                           GOLD_DARK)

    # Slanted barbs, stronger on the long primaries.
    barb_count = 3 + variant
    for i in range(barb_count):
        t = 0.18 + 0.15 * i
        lx = int(base_x + span * t)
        width = half_h * (math.sin(math.pi * min(1.0, t * 1.04)) ** 0.64)
        if t > 0.78:
            width *= max(0.18, 1.0 - ((t - 0.78) / 0.22) * 0.72)
        width = max(0.45, width)
        for side in (-1, 1):
            y0 = 16
            y1 = int(round(16 + side * width * 0.88))
            for step in range(1, 6):
                yy = int(round(y0 + (y1 - y0) * step / 5))
                xx = lx + int(round(step * 1.05))
                _feather_pixel(px, W, H, cell_x, cell_y, xx, yy,
                               direction, mix(SHADE, CREAM_MID, 0.35))
            _feather_pixel(px, W, H, cell_x, cell_y, lx, y1, direction,
                           OUTLINE)

    # Gold quill at the base.
    for ly in range(13, 20):
        for lx in range(0, 4):
            _feather_pixel(px, W, H, cell_x, cell_y, lx, ly, direction, GOLD)
    _feather_pixel(px, W, H, cell_x, cell_y, 1, 14, direction, GOLD_HI)
    _feather_pixel(px, W, H, cell_x, cell_y, 1, 19, direction, GOLD_DARK)


def draw_swatch(px, W, H, x0, y0, base, hi, lo, kind):
    for y in range(32):
        t = y / 31.0
        for x in range(32):
            color = mix(hi, base, t * 0.55)
            if kind == "gold" and ((x + y) % 11 < 2):
                color = mix(color, GOLD_HI, 0.45)
            if kind == "ivory" and (x % 9 == 0):
                color = mix(color, CREAM_HI, 0.4)
            put(px, W, H, x0 + x, y0 + y, color)
    # A darker border keeps the swatches from bleeding when stretched.
    for x in range(32):
        put(px, W, H, x0 + x, y0, lo)
        put(px, W, H, x0 + x, y0 + 31, lo)
    for y in range(32):
        put(px, W, H, x0, y0 + y, lo)
        put(px, W, H, x0 + 31, y0 + y, lo)
    # A little hand-painted wear.
    for i in range(10):
        xx = x0 + 3 + (i * 7) % 26
        yy = y0 + 5 + (i * 11) % 22
        put(px, W, H, xx, yy, hi)


def generate_entity_texture(path):
    W = H = 128
    px = [[(0, 0, 0, 0) for _ in range(W)] for _ in range(H)]

    # Row 0: left wing, pointing right.  Row 1: right wing, pointing left.
    left_specs = [(29, 14.0, 0), (30, 14.5, 1), (31, 13.0, 2), (31, 11.5, 3)]
    for i, (tip, half_h, variant) in enumerate(left_specs):
        draw_feather_cell(px, W, H, i * 32, 0, +1, tip, half_h, variant)
        draw_feather_cell(px, W, H, i * 32, 32, -1, tip, half_h, variant)

    # Row 2: opaque swatches used for the leading-edge arms and back plate.
    draw_swatch(px, W, H, 0, 64, GOLD, GOLD_HI, GOLD_DARK, "gold")
    draw_swatch(px, W, H, 32, 64, CREAM, CREAM_HI, OUTLINE, "ivory")
    draw_swatch(px, W, H, 64, 64, SHADE, CREAM_MID, OUTLINE, "shade")
    draw_swatch(px, W, H, 96, 64, GOLD_DARK, GOLD, OUTLINE, "gold")

    write_png(path, W, H, px)


# --------------------------------------------------------------------------- #
# Inventory icon: a clean symmetric wing pair on transparency
# --------------------------------------------------------------------------- #
def build_item_icon():
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

    return W, H, px


def generate_item_icon(path):
    W, H, px = build_item_icon()
    write_png(path, W, H, px)


# --------------------------------------------------------------------------- #
# Pack icon: the inventory icon over a dark night-sky field
# --------------------------------------------------------------------------- #
def generate_pack_icon(path):
    W = H = 128
    px = [[(0, 0, 0, 255) for _ in range(W)] for _ in range(H)]

    # Deep blue vignette with a warm halo behind the wings.
    for y in range(H):
        for x in range(W):
            dx = (x - 64) / 64.0
            dy = (y - 64) / 64.0
            distance = min(1.0, math.hypot(dx, dy))
            t = 1.0 - distance
            base = mix((10, 14, 28, 255), (34, 48, 82, 255), t * 0.9)
            halo = max(0.0, 1.0 - math.hypot(dx * 1.15, (dy - 0.05) * 1.6))
            px[y][x] = mix(base, (92, 132, 188, 255), halo * 0.22)

    # Gold frame.
    for i in range(3):
        for x in range(i, W - i):
            px[i][x] = (226, 178, 76, 255)
            px[H - 1 - i][x] = (158, 112, 38, 255)
        for y in range(i, H - i):
            px[y][i] = (226, 178, 76, 255)
            px[y][W - 1 - i] = (158, 112, 38, 255)

    # Scale the 64x64 item icon 2x and centre it.
    iw, ih, icon = build_item_icon()
    scale = 2
    ox = (W - iw * scale) // 2
    oy = (H - ih * scale) // 2
    for y in range(ih):
        for x in range(iw):
            r, g, b, a = icon[y][x]
            if a == 0:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    px[oy + y * scale + dy][ox + x * scale + dx] = (r, g, b, a)

    write_png(path, W, H, px)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate_entity_texture(os.path.join(root, "resource_pack", "textures",
                                         "entity", "angel_wings.png"))
    generate_item_icon(os.path.join(root, "resource_pack", "textures",
                                    "items", "angel_wings.png"))
    generate_pack_icon(os.path.join(root, "behavior_pack", "pack_icon.png"))
    generate_pack_icon(os.path.join(root, "resource_pack", "pack_icon.png"))
    print("wrote entity texture, item icon and pack icons")
