#!/usr/bin/env python3
"""Generate the Drone Companion entity atlas and the Drone Controller icon.

Pure-stdlib PNG writer (no Pillow) so the art can be regenerated anywhere with
Python 3.  Run from the project root:

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
    raw = bytearray()
    for row in pixels:
        raw.append(0)
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
# Drawing helpers
# --------------------------------------------------------------------------- #
def clamp(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)


def mix(c1, c2, t):
    return tuple(clamp(c1[i] * (1 - t) + c2[i] * t) for i in range(4))


def put(px, w, h, x, y, color, alpha=1.0):
    x, y = int(round(x)), int(round(y))
    if not (0 <= x < w and 0 <= y < h):
        return
    if alpha >= 1.0:
        px[y][x] = color
    else:
        px[y][x] = mix(px[y][x], color, alpha)


def rect(px, w, h, x0, y0, x1, y1, color, alpha=1.0):
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            put(px, w, h, x, y, color, alpha)


def hline(px, w, h, x0, x1, y, color, alpha=1.0):
    for x in range(int(x0), int(x1) + 1):
        put(px, w, h, x, y, color, alpha)


def vline(px, w, h, x, y0, y1, color, alpha=1.0):
    for y in range(int(y0), int(y1) + 1):
        put(px, w, h, x, y, color, alpha)


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


def circle(px, w, h, cx, cy, radius, color):
    r2 = radius * radius
    for y in range(int(cy - radius), int(cy + radius) + 1):
        for x in range(int(cx - radius), int(cx + radius) + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                put(px, w, h, x, y, color)


def ring(px, w, h, cx, cy, radius, thickness, color):
    inner = (radius - thickness) ** 2
    outer = radius * radius
    for y in range(int(cy - radius), int(cy + radius) + 1):
        for x in range(int(cx - radius), int(cx + radius) + 1):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if inner <= d <= outer:
                put(px, w, h, x, y, color)


def rounded_rect(px, w, h, x0, y0, x1, y1, radius, color):
    for y in range(int(y0), int(y1) + 1):
        inset = 0
        if y < y0 + radius:
            inset = int(round(radius - math.sqrt(max(0, radius ** 2 - (y0 + radius - y) ** 2))))
        elif y > y1 - radius:
            inset = int(round(radius - math.sqrt(max(0, radius ** 2 - (y - (y1 - radius)) ** 2))))
        hline(px, w, h, x0 + inset, x1 - inset, y, color)


# --------------------------------------------------------------------------- #
# Entity atlas: a 4 x 4 grid of 16 px material swatches
# --------------------------------------------------------------------------- #
ATLAS = {
    "body":    (0, 0),
    "canopy":  (16, 0),
    "belly":   (32, 0),
    "arm":     (48, 0),
    "rotor":   (0, 16),
    "motor":   (16, 16),
    "led":     (32, 16),
    "camera":  (48, 16),
    "lens":    (0, 32),
    "accent":  (16, 32),
    "metal":   (32, 32),
    "battery": (48, 32),
    "white":   (0, 48),
    "dark":    (16, 48),
    "hazard":  (32, 48),
    "grid":    (48, 48),
}


def region_px(px, name):
    """Yield (global_x, global_y, local_x, local_y) for one 16x16 region."""
    ox, oy = ATLAS[name]
    for ly in range(16):
        for lx in range(16):
            yield ox + lx, oy + ly, lx, ly


def generate_entity_texture(path):
    """Build a 4 x 4 atlas of 16 px material swatches.

    Each region is painted in local 0..15 coordinates so the swatches never
    bleed into one another.  The model maps whole faces to these regions.
    """
    W = H = 64
    px = [[(0, 0, 0, 255) for _ in range(W)] for _ in range(H)]
    grid = [
        ["body", "canopy", "belly", "arm"],
        ["rotor", "motor", "led", "camera"],
        ["lens", "accent", "metal", "battery"],
        ["white", "dark", "hazard", "grid"],
    ]

    for y in range(H):
        for x in range(W):
            name = grid[y // 16][x // 16]
            lx, ly = x % 16, y % 16
            r = g = b = 0

            if name == "body":
                t = 1.0 - ly / 15.0
                r, g, b = 48 + int(10 * t), 55 + int(10 * t), 63 + int(10 * t)
                if ly == 0:
                    r, g, b = 88, 101, 112
                elif ly in (4, 11):
                    r, g, b = 32, 38, 44
                elif ly in (5, 12):
                    r, g, b = 60, 69, 78
                if lx == 8:
                    r, g, b = 40, 47, 54
                if (lx, ly) in ((2, 2), (13, 2), (2, 13), (13, 13)):
                    r, g, b = 104, 116, 126
                if (lx, ly) == (12, 3):
                    r, g, b = 0, 229, 255
                elif (lx, ly) == (12, 2):
                    r, g, b = 145, 252, 255
                if lx - ly == -6 and 4 <= lx <= 8:
                    r, g, b = 74, 85, 95
                if ly == 15:
                    r, g, b = 25, 30, 35

            elif name == "canopy":
                t = 1.0 - ly / 15.0
                r, g, b = 74 + int(7 * t), 84 + int(7 * t), 94 + int(7 * t)
                if ly in (3, 5, 7, 9, 11, 13) and 2 <= lx <= 13:
                    r, g, b = 43, 50, 57
                elif ly in (2, 4, 6, 8, 10, 12) and 2 <= lx <= 13:
                    r, g, b = 92, 104, 114
                if lx == 8:
                    r, g, b = 60, 69, 78
                if ly == 0:
                    r, g, b = 113, 127, 138
                if ly == 15:
                    r, g, b = 42, 49, 56
                if ly == 1 and 5 <= lx <= 10:
                    r, g, b = 0, 184, 212
                if (lx, ly) in ((2, 2), (13, 2), (2, 13), (13, 13)):
                    r, g, b = 139, 153, 164

            elif name == "belly":
                r, g, b = 34, 39, 45
                if (lx + ly) % 4 == 0:
                    r, g, b = 52, 59, 66
                if (lx - ly) % 7 == 0:
                    r, g, b = 27, 31, 36
                if ly == 0:
                    r, g, b = 61, 69, 77
                if ly == 15:
                    r, g, b = 20, 24, 28
                if (lx, ly) in ((2, 2), (13, 2), (2, 13), (13, 13)):
                    r, g, b = 95, 107, 117

            elif name == "arm":
                r, g, b = 40, 46, 52
                if (lx + ly) % 4 == 0:
                    r, g, b = 59, 68, 76
                elif (lx - ly) % 7 == 0:
                    r, g, b = 28, 32, 37
                if ly == 1:
                    r, g, b = 83, 95, 105
                if ly == 2 and 4 <= lx <= 11:
                    r, g, b = 0, 184, 212
                if ly == 15:
                    r, g, b = 24, 28, 32

            elif name == "rotor":
                r, g, b = 17, 20, 23
                streak = {
                    3: (42, 48, 54),
                    5: (64, 73, 81),
                    7: (28, 32, 36),
                    9: (82, 92, 101),
                    11: (36, 42, 47),
                    13: (52, 60, 67),
                }
                if ly in streak:
                    r, g, b = streak[ly]
                if (lx * 5 + ly * 7) % 13 == 0:
                    r, g, b = 120, 134, 145
                if ly == 0:
                    r, g, b = 32, 37, 42
                if ly == 15:
                    r, g, b = 10, 12, 14

            elif name == "motor":
                d = math.hypot(lx - 7.5, ly - 7.5)
                if d > 6.5:
                    r, g, b = 38, 43, 49
                elif d > 5.5:
                    r, g, b = 79, 91, 101
                elif d > 4.5:
                    r, g, b = 103, 117, 128
                elif d > 3.5:
                    r, g, b = 51, 59, 67
                elif d > 2.2:
                    r, g, b = 112, 126, 137
                elif d > 1.2:
                    r, g, b = 26, 30, 34
                else:
                    r, g, b = 0, 229, 255
                if (lx, ly) in ((2, 2), (13, 2), (2, 13), (13, 13)):
                    r, g, b = 132, 146, 157

            elif name == "led":
                d = math.hypot(lx - 7.5, ly - 7.5)
                if d < 1.6:
                    r, g, b = 255, 255, 255
                elif d < 3.2:
                    r, g, b = 184, 255, 255
                elif d < 5.2:
                    r, g, b = 0, 229, 255
                elif d < 7.0:
                    r, g, b = 0, 168, 192
                else:
                    r, g, b = 0, 95, 107
                if (lx, ly) == (5, 5):
                    r, g, b = 255, 255, 255

            elif name == "camera":
                r, g, b = 48, 54, 61
                if ly == 8:
                    r, g, b = 30, 35, 40
                elif ly == 9:
                    r, g, b = 72, 82, 91
                if lx == 4:
                    r, g, b = 38, 44, 50
                if ly == 0:
                    r, g, b = 84, 96, 106
                if ly == 15:
                    r, g, b = 26, 31, 36
                if (lx, ly) in ((2, 2), (13, 2), (2, 13), (13, 13)):
                    r, g, b = 117, 131, 142
                if (lx, ly) == (12, 3):
                    r, g, b = 255, 75, 62
                elif (lx, ly) == (12, 2):
                    r, g, b = 255, 176, 160

            elif name == "lens":
                d = math.hypot(lx - 7.5, ly - 7.5)
                if d < 1.2:
                    r, g, b = 214, 255, 255
                elif d < 2.8:
                    r, g, b = 0, 229, 255
                elif d < 3.8:
                    r, g, b = 6, 52, 77
                elif d < 5.0:
                    r, g, b = 0, 184, 212
                elif d < 6.2:
                    r, g, b = 10, 43, 69
                elif d < 7.3:
                    r, g, b = 0, 120, 150
                else:
                    r, g, b = 6, 21, 34
                if (lx, ly) == (5, 5):
                    r, g, b = 255, 255, 255
                elif (lx, ly) == (6, 5):
                    r, g, b = 160, 255, 255
                if (lx, ly) in ((4, 4), (5, 5), (6, 6)):
                    r, g, b = 127, 239, 255

            elif name == "accent":
                d = math.hypot(lx - 7.5, ly - 7.5)
                if d < 2.0:
                    r, g, b = 255, 208, 160
                elif d < 4.0:
                    r, g, b = 255, 106, 61
                elif d < 6.0:
                    r, g, b = 214, 58, 37
                else:
                    r, g, b = 110, 22, 16
                if (lx, ly) == (6, 6):
                    r, g, b = 255, 255, 255

            elif name == "metal":
                r, g, b = 78, 86, 94
                if ly % 3 == 0:
                    r, g, b = 64, 71, 78
                elif ly % 3 == 1:
                    r, g, b = 94, 103, 112
                if (lx + ly) % 11 == 0:
                    r, g, b = 52, 58, 64
                if (lx - ly) % 9 == 0:
                    r, g, b = 112, 122, 132
                if ly == 0:
                    r, g, b = 124, 134, 144
                if ly == 15:
                    r, g, b = 44, 50, 56

            elif name == "battery":
                r, g, b = 30, 34, 39
                if (lx + ly) % 6 == 0:
                    r, g, b = 58, 66, 74
                if ly in (4, 5, 11, 12) and 2 <= lx <= 13:
                    r, g, b = (0, 184, 212) if ly in (4, 11) else (0, 95, 107)
                if ly == 0:
                    r, g, b = 73, 83, 92
                if ly == 15:
                    r, g, b = 18, 21, 24

            elif name == "white":
                d = math.hypot(lx - 7.5, ly - 7.5)
                if d < 3.0:
                    r, g, b = 255, 255, 255
                elif d < 5.0:
                    r, g, b = 214, 255, 255
                else:
                    r, g, b = 184, 255, 255

            elif name == "dark":
                r, g, b = 26, 30, 34
                if ly % 4 == 0:
                    r, g, b = 38, 43, 49

            elif name == "hazard":
                r, g, b = 43, 48, 54
                if (lx + ly) % 6 < 2:
                    r, g, b = 255, 177, 61
                elif (lx + ly) % 6 < 3:
                    r, g, b = 26, 30, 34

            elif name == "grid":
                r, g, b = 58, 65, 73
                if lx % 4 == 0 or ly % 4 == 0:
                    r, g, b = 42, 48, 54
                if lx % 4 == 2 and ly % 4 == 2:
                    r, g, b = 0, 184, 212

            px[y][x] = (clamp(r), clamp(g), clamp(b), 255)

    write_png(path, W, H, px)


# --------------------------------------------------------------------------- #
# Inventory icon: a compact drone controller on transparency
# --------------------------------------------------------------------------- #
def generate_item_icon(path):
    W = H = 64
    px = [[(0, 0, 0, 0) for _ in range(W)] for _ in range(H)]

    outline = (8, 10, 12, 255)
    shell = (47, 53, 60, 255)
    shell_hi = (75, 86, 96, 255)
    shell_lo = (30, 35, 40, 255)
    panel = (70, 81, 91, 255)
    panel_hi = (96, 110, 121, 255)
    screen_bg = (4, 18, 26, 255)
    cyan = (0, 229, 255, 255)
    cyan_dim = (0, 120, 143, 255)
    cyan_hi = (184, 255, 255, 255)
    white = (230, 255, 255, 255)
    red = (255, 75, 62, 255)
    green = (57, 217, 138, 255)
    orange = (255, 90, 54, 255)
    orange_hi = (255, 208, 160, 255)

    # Outer shell and inner bevel.
    rounded_rect(px, W, H, 12, 19, 52, 55, 5, outline)
    rounded_rect(px, W, H, 14, 21, 50, 53, 4, shell)
    rounded_rect(px, W, H, 15, 22, 49, 50, 3, shell_hi)
    rounded_rect(px, W, H, 17, 24, 47, 49, 2, shell)

    # Top panel.
    rounded_rect(px, W, H, 17, 23, 47, 41, 2, (34, 40, 46, 255))
    rounded_rect(px, W, H, 18, 24, 46, 40, 2, panel)
    hline(px, W, H, 19, 45, 25, panel_hi)
    hline(px, W, H, 19, 45, 39, (43, 50, 57, 255))

    # Screen with a tiny drone silhouette and a scan line.
    rounded_rect(px, W, H, 21, 26, 43, 37, 1, (2, 33, 43, 255))
    rect(px, W, H, 22, 27, 42, 36, screen_bg)
    for y in range(28, 35):
        t = (y - 28) / 6.0
        col = (0, int(80 + 90 * (1 - t)), int(110 + 90 * (1 - t)), 255)
        hline(px, W, H, 22, 42, y, col)
    # Drone icon: body, arms and rotor dots.
    rect(px, W, H, 29, 31, 35, 33, (0, 55, 67, 255))
    line(px, W, H, 29, 31, 26, 29, (0, 55, 67, 255))
    line(px, W, H, 35, 31, 38, 29, (0, 55, 67, 255))
    line(px, W, H, 29, 33, 26, 35, (0, 55, 67, 255))
    line(px, W, H, 35, 33, 38, 35, (0, 55, 67, 255))
    for cx, cy in ((26, 29), (38, 29), (26, 35), (38, 35)):
        circle(px, W, H, cx, cy, 1.2, (0, 55, 67, 255))
        put(px, W, H, cx, cy, cyan_hi)
    hline(px, W, H, 22, 42, 33, (127, 249, 255, 255))
    put(px, W, H, 42, 27, white)
    put(px, W, H, 41, 27, cyan_hi)

    # DRONE label in a tiny 3x5 font.
    font = {
        "D": ["111", "101", "101", "101", "111"],
        "R": ["111", "101", "111", "110", "101"],
        "O": ["111", "101", "101", "101", "111"],
        "N": ["101", "111", "111", "111", "101"],
        "E": ["111", "100", "111", "100", "111"],
    }
    label = "DRONE"
    x = 22
    for ch in label:
        glyph = font[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    put(px, W, H, x + gx, 40 + gy, cyan_hi)
        x += 4

    # Joysticks.
    for cx in (23, 41):
        circle(px, W, H, cx, 47, 5.5, outline)
        circle(px, W, H, cx, 47, 4.5, (23, 27, 31, 255))
        circle(px, W, H, cx, 47, 3.4, (58, 67, 75, 255))
        circle(px, W, H, cx, 47, 2.6, (138, 151, 162, 255))
        circle(px, W, H, cx - 0.7, 46.3, 1.2, (196, 207, 216, 255))
        put(px, W, H, cx - 1, 45, white)

    # Buttons.
    for cx, cy, col in ((29, 42, red), (35, 42, green), (46, 42, cyan)):
        circle(px, W, H, cx, cy, 1.6, outline)
        circle(px, W, H, cx, cy, 1.1, col)
        put(px, W, H, cx - 0.3, cy - 0.3, white)

    # Antenna with a glowing tip.
    line(px, W, H, 46, 23, 52, 11, outline)
    line(px, W, H, 46, 22, 52, 10, (138, 151, 162, 255))
    line(px, W, H, 45, 22, 51, 10, (196, 207, 216, 255))
    circle(px, W, H, 53, 9, 3.2, outline)
    circle(px, W, H, 53, 9, 2.4, orange)
    circle(px, W, H, 53, 9, 1.2, orange_hi)
    put(px, W, H, 52, 8, white)
    # A few translucent glow pixels around the tip.
    for gx, gy in ((49, 8), (50, 7), (51, 6), (55, 8), (56, 9), (54, 5)):
        put(px, W, H, gx, gy, (255, 90, 54, 150), 0.7)

    # Grip lines and a subtle cyan charge indicator on the lower shell.
    for gy in (51, 53):
        hline(px, W, H, 20, 44, gy, (20, 24, 28, 255))
    hline(px, W, H, 28, 36, 50, cyan_dim)
    hline(px, W, H, 28, 33, 50, cyan)
    put(px, W, H, 37, 50, (0, 95, 107, 255))

    # Top-left highlight and bottom shadow.
    line(px, W, H, 16, 24, 16, 46, (112, 126, 137, 255))
    line(px, W, H, 17, 24, 28, 24, (112, 126, 137, 255))
    hline(px, W, H, 18, 44, 54, (17, 20, 23, 255))

    write_png(path, W, H, px)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate_entity_texture(os.path.join(root, "resource_pack", "textures", "entity", "drone_companion.png"))
    generate_item_icon(os.path.join(root, "resource_pack", "textures", "items", "drone_controller.png"))
    print("Wrote entity atlas and controller icon.")
