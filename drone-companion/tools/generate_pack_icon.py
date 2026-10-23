#!/usr/bin/env python3
"""Generate the 256x256 Drone Companion pack icon.

The icon is a stylised quadcopter on a dark tech panel.  It is written to both
pack roots so the behavior and resource packs show the same artwork.

    python3 tools/generate_pack_icon.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_textures import (  # noqa: E402
    write_png,
    put,
    rect,
    hline,
    vline,
    line,
    circle,
    ring,
    rounded_rect,
    mix,
)

W = H = 256

# A compact 3x5 font for the labels.
FONT = {
    "D": ["110", "101", "101", "101", "110"],
    "R": ["110", "101", "110", "101", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "N": ["101", "111", "111", "111", "101"],
    "E": ["111", "100", "111", "100", "111"],
    "C": ["111", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "P": ["110", "101", "110", "100", "100"],
    "A": ["010", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
}


def text(px, value, x, y, scale, color, shadow=None, spacing=1):
    if shadow:
        text(px, value, x + max(1, scale // 2), y + max(1, scale // 2), scale, shadow, None, spacing)
    cursor = x
    for char in value:
        glyph = FONT.get(char)
        if not glyph:
            cursor += (3 + spacing) * scale
            continue
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit != "1":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        put(px, W, H, cursor + gx * scale + sx, y + gy * scale + sy, color)
        cursor += (3 + spacing) * scale


def thick_line(px, x1, y1, x2, y2, width, color):
    steps = max(1, int(max(abs(x2 - x1), abs(y2 - y1))))
    for index in range(steps + 1):
        t = index / steps
        circle(px, W, H, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, width / 2, color)


def generate(path):
    px = [[(6, 16, 24, 255) for _ in range(W)] for _ in range(H)]

    # Dark tech-panel background with a soft centre glow and faint grid.
    for y in range(H):
        for x in range(W):
            t = y / (H - 1)
            r = int(8 + 8 * t)
            g = int(20 + 14 * t)
            b = int(30 + 20 * t)
            d = math.hypot(x - 128, y - 120)
            glow = max(0.0, 1.0 - d / 150.0) * 0.12
            r = int(r * (1 - glow) + 0 * glow)
            g = int(g * (1 - glow) + 184 * glow)
            b = int(b * (1 - glow) + 212 * glow)
            if (x + y) % 8 == 0:
                r = min(255, r + 3)
                g = min(255, g + 4)
                b = min(255, b + 5)
            px[y][x] = (r, g, b, 255)

    # Border.
    rounded_rect(px, W, H, 5, 5, 250, 250, 20, (4, 10, 15, 255))
    rounded_rect(px, W, H, 8, 8, 247, 247, 18, (10, 25, 36, 255))
    rounded_rect(px, W, H, 12, 12, 243, 243, 15, (8, 20, 30, 255))
    hline(px, W, H, 22, 233, 17, (0, 184, 212, 255))
    hline(px, W, H, 22, 233, 18, (0, 95, 107, 255))
    hline(px, W, H, 22, 233, 190, (0, 120, 143, 255))

    # Rotor arms.
    centres = [(64, 64), (192, 64), (64, 192), (192, 192)]
    for cx, cy in centres:
        thick_line(px, 128, 120, cx, cy, 16, (8, 15, 21, 255))
        thick_line(px, 128, 120, cx, cy, 12, (42, 50, 58, 255))
        thick_line(px, 128, 120, cx, cy, 4, (79, 91, 101, 255))

    # Rotors.
    for cx, cy in centres:
        circle(px, W, H, cx, cy, 34, (6, 12, 17, 255))
        ring(px, W, H, cx, cy, 32, 3, (40, 50, 59, 255))
        ring(px, W, H, cx, cy, 28, 1, (0, 120, 143, 255))
        for angle in (0, 90, 180, 270):
            radians = math.radians(angle)
            ex = cx + math.cos(radians) * 26
            ey = cy + math.sin(radians) * 26
            thick_line(px, cx, cy, ex, ey, 5, (17, 22, 27, 255))
            thick_line(px, cx, cy, ex, ey, 2, (94, 107, 117, 255))
        circle(px, W, H, cx, cy, 10, (26, 32, 38, 255))
        circle(px, W, H, cx, cy, 8, (95, 107, 117, 255))
        circle(px, W, H, cx, cy, 4, (0, 229, 255, 255))
        circle(px, W, H, cx, cy, 1.5, (230, 255, 255, 255))

    # Body shell.
    rounded_rect(px, W, H, 92, 90, 164, 156, 12, (8, 14, 19, 255))
    rounded_rect(px, W, H, 95, 93, 161, 153, 10, (58, 68, 78, 255))
    rounded_rect(px, W, H, 99, 97, 157, 149, 8, (48, 56, 65, 255))
    hline(px, W, H, 100, 156, 100, (88, 101, 112, 255))
    hline(px, W, H, 100, 156, 148, (26, 32, 38, 255))
    vline(px, W, H, 128, 100, 148, (35, 42, 49, 255))

    # Canopy and battery pack.
    rounded_rect(px, W, H, 106, 82, 150, 102, 6, (8, 14, 19, 255))
    rounded_rect(px, W, H, 108, 84, 148, 100, 5, (79, 91, 101, 255))
    rounded_rect(px, W, H, 110, 72, 146, 86, 5, (8, 14, 19, 255))
    rounded_rect(px, W, H, 112, 74, 144, 84, 4, (31, 38, 44, 255))
    hline(px, W, H, 114, 142, 77, (0, 184, 212, 255))
    hline(px, W, H, 114, 142, 81, (0, 95, 107, 255))

    # Belly and camera gimbal.
    rounded_rect(px, W, H, 102, 148, 154, 166, 6, (8, 14, 19, 255))
    rounded_rect(px, W, H, 104, 150, 152, 164, 5, (36, 42, 49, 255))
    rounded_rect(px, W, H, 113, 156, 143, 187, 9, (8, 14, 19, 255))
    rounded_rect(px, W, H, 115, 158, 141, 185, 8, (48, 54, 61, 255))
    circle(px, W, H, 128, 172, 14, (6, 14, 22, 255))
    circle(px, W, H, 128, 172, 12, (0, 120, 143, 255))
    circle(px, W, H, 128, 172, 9, (6, 52, 77, 255))
    circle(px, W, H, 128, 172, 6, (0, 229, 255, 255))
    circle(px, W, H, 128, 172, 3, (230, 255, 255, 255))
    circle(px, W, H, 124, 168, 2, (255, 255, 255, 255))

    # Front and side LEDs.
    hline(px, W, H, 106, 150, 145, (0, 229, 255, 255))
    hline(px, W, H, 106, 150, 146, (184, 255, 255, 255))
    vline(px, W, H, 94, 110, 138, (0, 229, 255, 255))
    vline(px, W, H, 162, 110, 138, (0, 229, 255, 255))
    vline(px, W, H, 95, 110, 138, (0, 95, 107, 255))
    vline(px, W, H, 161, 110, 138, (0, 95, 107, 255))

    # Antenna.
    thick_line(px, 148, 88, 174, 58, 7, (8, 14, 19, 255))
    thick_line(px, 148, 88, 174, 58, 4, (138, 151, 162, 255))
    thick_line(px, 148, 87, 174, 57, 1, (196, 207, 216, 255))
    circle(px, W, H, 177, 55, 9, (8, 14, 19, 255))
    circle(px, W, H, 177, 55, 7, (255, 90, 54, 255))
    circle(px, W, H, 177, 55, 4, (255, 208, 160, 255))
    circle(px, W, H, 176, 54, 1.5, (255, 255, 255, 255))

    # Soft glows around the brightest elements.
    for gx, gy, radius, colour in (
        (64, 64, 42, (0, 229, 255, 70)),
        (192, 64, 42, (0, 229, 255, 70)),
        (64, 192, 42, (0, 229, 255, 70)),
        (192, 192, 42, (0, 229, 255, 70)),
        (128, 172, 24, (0, 229, 255, 70)),
        (177, 55, 16, (255, 90, 54, 60)),
    ):
        for y in range(max(0, gy - radius), min(H, gy + radius + 1)):
            for x in range(max(0, gx - radius), min(W, gx + radius + 1)):
                d = math.hypot(x - gx, y - gy)
                if d <= radius:
                    put(px, W, H, x, y, colour, 0.10 * (1 - d / radius))

    # Labels.
    text(px, "DRONE", 64, 198, 7, (230, 255, 255, 255), (0, 95, 107, 255), spacing=1)
    text(px, "COMPANION", 76, 238, 2, (0, 229, 255, 255), (0, 60, 72, 255), spacing=1)

    write_png(path, W, H, px)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generate(os.path.join(root, "behavior_pack", "pack_icon.png"))
    generate(os.path.join(root, "resource_pack", "pack_icon.png"))
    print("Wrote pack icons.")
