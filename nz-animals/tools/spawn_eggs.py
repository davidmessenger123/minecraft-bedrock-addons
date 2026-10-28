"""
Modern-style Bedrock spawn egg icons for the NZ Animals roster.

Bedrock's 1.21.80+ vanilla eggs are 32x32 pixel-art eggs with a dark
outline and a mob-readable face/pattern.  The old fallback
`base_color`/`overlay_color` fields still produce the pre-1.21 two-tone
egg, so these icons are written into the item atlas and referenced from
each client entity's spawn_egg definition.
"""

from __future__ import annotations

import json
import math
import os
import random

from PIL import Image

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

ICON_SIZE = 32


def _shade(c: RGB, factor: float) -> RGB:
    return tuple(max(0, min(255, int(v * factor))) for v in c)


def _resolve(palette: dict, key: str, fallback: RGB) -> RGB:
    value = palette.get(key, fallback)
    if isinstance(value, str):
        value = palette.get(value, fallback)
    if isinstance(value, (int, float)):
        return _shade(fallback, float(value))
    if isinstance(value, (tuple, list)) and len(value) >= 3:
        return tuple(int(v) for v in value[:3])
    return fallback


def _egg_mask(size_class: str) -> set[tuple[int, int]]:
    top, bottom, half_width = {
        "small": (7, 29, 7),
        "medium": (4, 30, 10),
        "large": (2, 31, 13),
    }[size_class]
    mask: set[tuple[int, int]] = set()
    for y in range(top, bottom + 1):
        t = (y - top) / max(1, bottom - top)
        if t < 0.30:
            f = 0.30 + 0.70 * (t / 0.30)
        elif t < 0.70:
            f = 1.0
        else:
            f = 1.0 - 0.47 * ((t - 0.70) / 0.30)
        rx = max(1, int(round(half_width * f)))
        for x in range(16 - rx, 16 + rx + 1):
            mask.add((x, y))
    return mask


class EggIcon:
    def __init__(self, mask: set[tuple[int, int]], outline: RGB):
        self.image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        self.px = self.image.load()
        self.mask = set(mask)
        self.outline = (*outline, 255)
        self.bbox = (
            min(x for x, _ in mask),
            min(y for _, y in mask),
            max(x for x, _ in mask),
            max(y for _, y in mask),
        )

    def put(self, x: int, y: int, color: RGB | RGBA, *, clip: bool = True) -> None:
        if not (0 <= x < ICON_SIZE and 0 <= y < ICON_SIZE):
            return
        if clip and (x, y) not in self.mask:
            return
        self.px[x, y] = (*color, 255) if len(color) == 3 else color

    def get(self, x: int, y: int) -> RGBA:
        if not (0 <= x < ICON_SIZE and 0 <= y < ICON_SIZE):
            return (0, 0, 0, 0)
        return self.px[x, y]

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: RGB) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, color)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, color: RGB) -> None:
        for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
            for x in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
                if ((x + 0.5 - cx) / max(0.5, rx)) ** 2 + (
                    (y + 0.5 - cy) / max(0.5, ry)
                ) ** 2 <= 1.0:
                    self.put(x, y, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: RGB, width: int = 1) -> None:
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            r = width // 2
            if width <= 1:
                self.put(x, y, color, clip=False)
            else:
                for yy in range(y - r, y - r + width):
                    for xx in range(x - r, x - r + width):
                        self.put(xx, yy, color, clip=False)

    def _fill_polygon(self, points: list[tuple[float, float]], color: RGB) -> None:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        for y in range(max(0, math.floor(min(ys))), min(ICON_SIZE, math.ceil(max(ys)) + 1)):
            for x in range(max(0, math.floor(min(xs))), min(ICON_SIZE, math.ceil(max(xs)) + 1)):
                inside = False
                j = len(points) - 1
                for i in range(len(points)):
                    xi, yi = points[i]
                    xj, yj = points[j]
                    if ((yi > y + 0.5) != (yj > y + 0.5)) and (
                        x + 0.5 < (xj - xi) * (y + 0.5 - yi) / ((yj - yi) or 1e-9) + xi
                    ):
                        inside = not inside
                    j = i
                if inside:
                    self.put(x, y, color, clip=False)

    def shape(self, points: list[tuple[float, float]], color: RGB, outline: bool = True) -> None:
        self._fill_polygon(points, self.outline[:3] if outline else color)
        if outline:
            inner = []
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            for x, y in points:
                inner.append((x + (cx - x) * 0.12, y + (cy - y) * 0.12))
            self._fill_polygon(inner, color)

    def outline_mask(self) -> None:
        for x, y in list(self.mask):
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in self.mask:
                    edge = True
                    break
            if edge:
                self.px[x, y] = self.outline


def _base_icon(spec: dict, palette: dict, size_class: str) -> EggIcon:
    sid = spec["id"]
    body = _resolve(palette, "body", (110, 100, 80))
    back = _resolve(palette, "back", body)
    belly = _resolve(palette, "belly", body)
    dark = _resolve(palette, "dark", _shade(body, 0.45))
    icon = EggIcon(_egg_mask(size_class), _shade(dark, 0.72))
    x0, y0, x1, y1 = icon.bbox
    w, h = x1 - x0 + 1, y1 - y0 + 1

    # Egg body: warm body colour, cooler back band and a softly shaded lower
    # edge.  The small amount of vertical banding reads at 32 pixels without
    # turning into a noisy texture.
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, h - 1)
        band = back if t < 0.42 else body
        if t > 0.70:
            band = _shade(body, 0.90)
        for x in range(x0, x1 + 1):
            if (x, y) not in icon.mask:
                continue
            left = x < 16
            if t < 0.14 and left:
                band = _shade(band, 1.08)
            icon.px[x, y] = (*band, 255)

    # Body / belly field.  Penguins, seals, whales and sharks need much more
    # white than a songbird.
    if spec["arch"] in {"penguin", "seal", "swimmer", "quadruped"}:
        belly_ry = h * (0.30 if spec["arch"] != "penguin" else 0.38)
        icon.ellipse(16, y0 + h * 0.72, w * 0.36, belly_ry, belly)
    elif spec["arch"] == "bird":
        icon.ellipse(16, y0 + h * 0.72, w * 0.27, h * 0.24, belly)

    # A light face disc for birds and mammals, then a darker crown.
    if spec["arch"] != "insect" and spec["arch"] != "snail":
        head = _resolve(palette, "head", body)
        icon.ellipse(16, y0 + h * 0.34, w * 0.34, h * 0.25, head)

    # A few deterministic spots/scales on the sides.  They are clipped to the
    # egg silhouette and skip the face so the eyes stay readable.
    rng = random.Random(f"spawn-egg-{sid}")
    for _ in range(5 if size_class != "small" else 3):
        sx = rng.randint(x0 + 2, x1 - 2)
        sy = rng.randint(y0 + int(h * 0.55), y1 - 2)
        if abs(sx - 16) < w * 0.20 and sy < y0 + h * 0.55:
            continue
        icon.put(sx, sy, _shade(back, 0.78), clip=True)
        if rng.random() < 0.6:
            icon.put(sx + 1, sy, _shade(back, 0.86), clip=True)

    icon.outline_mask()

    # Head crown / crest and little side masses.
    crest = _resolve(palette, "crest", _shade(body, 1.1))
    if "crest" in palette:
        top = y0
        spikes = 3 if size_class != "small" else 2
        for i in range(spikes):
            sx = 16 + (i - (spikes - 1) / 2) * 4
            icon.shape([(sx - 2, top + 1), (sx + 1, top - 3), (sx + 4, top + 1)], crest)

    # Bird wings / penguin flippers.  They sit on the edge of the silhouette
    # and use the exact same palette as the entity model.
    wing = _resolve(palette, "wing", _shade(body, 0.82))
    wing_top = _resolve(palette, "wing_top", wing)
    if spec["arch"] == "bird" and sid not in {"kiwi", "kakapo"}:
        for side in (-1, 1):
            ex = x0 + 1 if side < 0 else x1 - 1
            icon.shape(
                [(ex, y0 + h * 0.53), (ex - side * 3, y0 + h * 0.68),
                 (ex - side * 1, y0 + h * 0.86), (ex + side * 1, y0 + h * 0.94)],
                wing,
            )
            icon.put(ex, y0 + int(h * 0.68), wing_top, clip=False)
        if sid == "kea":
            for side in (-1, 1):
                ex = x0 + 2 if side < 0 else x1 - 2
                icon.rect(ex - 1, y0 + int(h * 0.70), ex + 1, y0 + int(h * 0.78), _resolve(palette, "wing_top", wing))
    elif spec["arch"] == "penguin":
        for side in (-1, 1):
            ex = x0 + 1 if side < 0 else x1 - 1
            icon.shape(
                [(ex, y0 + h * 0.45), (ex - side * 3, y0 + h * 0.70),
                 (ex - side * 1, y0 + h * 0.91)],
                wing,
            )
        # White face mask for every penguin; crested species get their brow.
        icon.ellipse(16, y0 + h * 0.34, w * 0.25, h * 0.18, belly)
        if "crest" in palette:
            icon.rect(9, y0 + 2, 13, y0 + 5, crest)
            icon.rect(19, y0 + 2, 23, y0 + 5, crest)

    # Seal flippers and muzzle.
    if spec["arch"] == "seal":
        for side in (-1, 1):
            ex = x0 + 1 if side < 0 else x1 - 1
            icon.shape(
                [(ex, y1 - 6), (ex - side * 5, y1 - 1),
                 (ex - side * 2, y1 + 2)],
                _resolve(palette, "flipper", _shade(body, 0.75)),
            )
        icon.ellipse(16, y0 + h * 0.42, w * 0.25, h * 0.13, _shade(belly, 0.95))

    # Swimmer dorsal fins, flukes and rostrum.
    if spec["arch"] == "swimmer":
        fin = _resolve(palette, "fin", _shade(body, 0.8))
        top = y0 + int(h * 0.22)
        icon.shape([(13, top), (17, top - (7 if size_class == "large" else 5)), (21, top)], fin)
        for side in (-1, 1):
            ex = x0 + 2 if side < 0 else x1 - 2
            icon.shape([(ex, y0 + h * 0.58), (ex - side * 4, y0 + h * 0.73),
                        (ex - side * 1, y0 + h * 0.82)], fin)
        if sid != "blue_shark":
            icon.ellipse(16, y0 + h * 0.47, w * 0.16, h * 0.08, _shade(belly, 1.03))
        if sid == "orca":
            icon.ellipse(20, y0 + h * 0.32, 4, 2, belly)
            icon.rect(8, y0 + int(h * 0.63), 24, y0 + int(h * 0.78), belly)
        if sid == "sperm_whale":
            icon.rect(x0 + 2, y0 + 2, x1 - 1, y0 + int(h * 0.39), _shade(body, 0.94))

    # Quadruped ears / brow, plus the tuatara crest.
    if spec["arch"] == "quadruped" and sid != "tuatara":
        head = _resolve(palette, "head", body)
        for side in (-1, 1):
            ex = 16 + side * 8
            icon.shape([(ex - 2, y0 + 4), (ex, y0 + 1), (ex + 2, y0 + 4)], _shade(head, 0.88))
    if sid == "tuatara":
        crest = _resolve(palette, "crest", (206, 198, 152))
        for i in range(5):
            yy = y0 + 3 + i * 3
            xx = 12 + i
            icon.shape([(xx, yy + 2), (xx + 1, yy - 2), (xx + 3, yy + 2)], crest)
        for side in (-1, 1):
            ex = x0 + 3 if side < 0 else x1 - 3
            icon.line(ex, y1 - 7, ex - side * 4, y1 - 1, _resolve(palette, "leg", body), 2)

    # Insect antennae and legs, or the snail's eye stalks.
    if spec["arch"] == "insect":
        leg = _resolve(palette, "leg", _shade(body, 0.7))
        for side in (-1, 1):
            sx = 16 + side * 3
            icon.line(sx, y0 + 4, sx + side * 5, y0 - 3, leg)
            for row in (0.55, 0.72, 0.88):
                y = y0 + int(h * row)
                icon.line(16 + side * int(w * 0.30), y,
                          16 + side * int(w * 0.52), y + 4, leg)
        if sid == "huhu":
            icon.rect(12, y0 + int(h * 0.52), 20, y1 - 4, _shade(back, 0.55))
            icon.line(16, y0 + int(h * 0.52), 16, y1 - 4, _shade(body, 0.75))
    elif spec["arch"] == "snail":
        shell = _resolve(palette, "shell2", _shade(body, 0.85))
        shell_top = _resolve(palette, "shell_top", _shade(shell, 1.12))
        icon.ellipse(16, y0 + h * 0.52, w * 0.42, h * 0.34, shell)
        icon.ellipse(16, y0 + h * 0.47, w * 0.32, h * 0.24, shell_top)
        # Square spiral, one pixel wide, matching the shell marking.
        path = [(16, 10), (20, 10), (20, 14), (14, 14), (14, 8),
                (22, 8), (22, 17), (10, 17), (10, 7), (24, 7)]
        for i in range(len(path) - 1):
            icon.line(*path[i], *path[i + 1], _resolve(palette, "dark", shell), 1)
        icon.ellipse(16, y1 - 3, w * 0.34, h * 0.12, belly)
        for side in (-1, 1):
            ex = 16 + side * 3
            icon.line(ex, y0 + 7, ex + side * 2, y0 - 1, belly, 1)
            icon.put(ex + side * 2, y0 - 2, dark, clip=False)

    # Moa: a long neck and legs make the egg immediately readable.
    if sid == "moa":
        neck = _resolve(palette, "head", body)
        icon.rect(14, y0, 18, y0 + 8, neck)
        icon.ellipse(16, y0 + 3, 4, 3, neck)
        icon.shape([(16, y0 + 3), (22, y0 + 5), (16, y0 + 7)], _resolve(palette, "beak", dark))
        for side in (-1, 1):
            xx = 16 + side * 4
            icon.line(xx, y1 - 6, xx + side * 2, y1, _resolve(palette, "leg", body), 2)

    # Kiwi's long probing bill is a stronger identifier than a generic beak.
    if sid == "kiwi":
        icon.line(16, y0 + h * 0.44, 16, y0 + h * 0.78, _resolve(palette, "beak", belly), 2)
        icon.put(15, y0 + int(h * 0.78), dark, clip=False)

    # Pukeko's red frontal shield and long legs.
    if sid == "pukeko":
        icon.rect(13, y0 + 3, 19, y0 + 8, _resolve(palette, "beak", (198, 52, 40)))
        for side in (-1, 1):
            xx = 16 + side * 3
            icon.line(xx, y1 - 6, xx + side * 3, y1 + 2,
                      _resolve(palette, "leg", body), 2)

    # Tui's white throat tuft, hihi's wingbar, kereru's chest and huia's band.
    if sid == "tui":
        icon.ellipse(16, y0 + h * 0.57, 3, 3, _resolve(palette, "belly", (214, 216, 226)))
        for side in (-1, 1):
            icon.rect(16 + side * 6, y0 + int(h * 0.69), 16 + side * 8,
                      y0 + int(h * 0.77), _resolve(palette, "wing_top", body))
    if sid == "hihi":
        icon.rect(8, y0 + int(h * 0.68), 24, y0 + int(h * 0.74),
                  _resolve(palette, "belly", (232, 232, 234)))
    if sid == "kereru":
        icon.ellipse(16, y0 + h * 0.66, 5, 6, _resolve(palette, "belly", (140, 148, 158)))
    if sid == "huia":
        icon.rect(10, y1 - 5, 23, y1 - 1, _resolve(palette, "belly", (48, 48, 52)))

    # Eyes.  Owls get a larger facial disc; kiwi a tiny eye.
    iris = _resolve(palette, "iris", (220, 190, 90))
    eye = _resolve(palette, "eye", (30, 24, 20))
    eye_y = y0 + int(h * 0.29)
    eye_dx = 4 if size_class != "small" else 3
    if sid == "morepork":
        eye_dx, eye_y = 5, y0 + int(h * 0.30)
        for side in (-1, 1):
            icon.ellipse(16 + side * eye_dx, eye_y, 3, 3, (238, 220, 120))
            icon.rect(16 + side * eye_dx - 1, eye_y - 1,
                      16 + side * eye_dx + 1, eye_y + 1, eye)
    else:
        for side in (-1, 1):
            ex = 16 + side * eye_dx
            icon.rect(ex - 1, eye_y - 1, ex + 1, eye_y + 1, (242, 242, 238))
            icon.put(ex, eye_y, eye if sid != "kea" else iris)

    # Beak or muzzle.  Long-billed birds are deliberately easy to identify.
    beak = _resolve(palette, "beak", _shade(body, 0.6))
    if spec["arch"] == "bird":
        if sid in {"kiwi", "kotare", "huia", "moa"}:
            icon.line(16, eye_y + 2, 16, eye_y + (11 if sid in {"kiwi", "kotare"} else 8), beak, 2)
        elif sid == "morepork":
            icon.shape([(14, eye_y + 3), (18, eye_y + 3), (16, eye_y + 6)], beak)
        else:
            icon.shape([(14, eye_y + 3), (18, eye_y + 3), (16, eye_y + 7)], beak)
        if sid in {"pukeko", "tieke", "huia"}:
            icon.rect(15, eye_y + 6, 17, eye_y + 9, _resolve(palette, "wattle", _resolve(palette, "beak", (198, 52, 40))))
    elif spec["arch"] in {"quadruped", "seal"}:
        icon.ellipse(16, eye_y + 5, 3, 2, beak)
        if spec["arch"] == "seal":
            for side in (-1, 1):
                icon.line(16 + side * 4, eye_y + 5, 16 + side * 9, eye_y + 4, (220, 214, 200))
                icon.line(16 + side * 4, eye_y + 6, 16 + side * 9, eye_y + 7, (220, 214, 200))
    elif spec["arch"] == "swimmer":
        icon.rect(14, eye_y + 4, 18, eye_y + 6, _shade(beak, 0.75))
    elif spec["arch"] == "snail":
        pass

    # A tiny dark foot/base shadow gives the icon a grounded look like the
    # vanilla eggs without making the silhouette muddy.
    for x, y in list(icon.mask):
        if y == y1 and (x + y) % 3 != 0:
            icon.px[x, y] = _shade(body, 0.62)

    return icon


def _size_class(spec: dict, real_units: float) -> str:
    if spec["arch"] == "insect" or real_units < 9:
        return "small"
    if real_units >= 34:
        return "large"
    return "medium"


def write_icon(path: str, spec: dict, palette: dict, real_units: float) -> str:
    icon = _base_icon(spec, palette, _size_class(spec, real_units))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    icon.image.save(path)
    return path


def item_texture_data(ids: list[str]) -> dict:
    return {
        "resource_pack_name": "nz_animals",
        "texture_name": "atlas.items",
        "texture_data": {
            f"nza:spawn_egg_{sid}": {
                "textures": f"textures/items/spawn_eggs/spawn_egg_{sid}"
            }
            for sid in ids
        },
    }


def write_item_texture(path: str, ids: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(item_texture_data(ids), fh, indent=2)
        fh.write("\n")
