"""
Box-UV geometry + texture engine for Bedrock .geo.json models.

The UV layout reproduced here is the one Blockbench generates for a Bedrock
Entity (box_uv) cube, verified against an exported model:

    net width  = 2 * (d + w)
    net height = h + d

    +---------------------------+  <- top band, d tall
    |   up   |  down  |         |
    +---+---+---+---+---+---+---+  <- side band, h tall
    |east|north|west|south|     |
    +---+---+---+---+---+---+---+

where up/down are w wide and east/west are d wide, north/south are w wide.
Because 1 model unit == 1 texture pixel in Bedrock, net units are pixels.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

RGB = tuple[int, int, int]

# Face order used by the box-UV net.
FACES = ("up", "down", "east", "north", "west", "south")


# --------------------------------------------------------------------------
# box UV math
# --------------------------------------------------------------------------

def face_rects(w: int, h: int, d: int) -> dict[str, tuple[int, int, int, int]]:
    """Face rectangles in net-local pixel coordinates (u1, v1, u2, v2)."""
    return {
        "up":    (d, 0, d + w, d),
        "down":  (d + w, 0, d + 2 * w, d),
        "east":  (0, d, d, d + h),
        "north": (d, d, d + w, d + h),
        "west":  (d + w, d, 2 * d + w, d + h),
        "south": (2 * d + w, d, 2 * d + 2 * w, d + h),
    }


def net_size(w: int, h: int, d: int) -> tuple[int, int]:
    return 2 * (d + w), h + d


# --------------------------------------------------------------------------
# model primitives
# --------------------------------------------------------------------------

@dataclass
class Cube:
    """One box-UV cube of a model."""
    name: str
    bone: str
    lo: tuple[int, int, int]
    hi: tuple[int, int, int]
    color: RGB
    faces: dict[str, RGB] = field(default_factory=dict)
    details: list[dict] = field(default_factory=list)
    markings: list[dict] = field(default_factory=list)

    @property
    def size(self) -> tuple[int, int, int]:
        # Texture nets are measured in whole pixels even when the exported
        # geometry keeps fractional model-space dimensions.
        return tuple(max(1, int(round(self.hi[i] - self.lo[i]))) for i in range(3))

    def face_color(self, face: str) -> RGB:
        return self.faces.get(face, self.color)


@dataclass
class Bone:
    name: str
    pivot: tuple[int, int, int]
    parent: str | None = None


@dataclass
class Model:
    name: str
    bones: list[Bone] = field(default_factory=list)
    cubes: list[Cube] = field(default_factory=list)
    root: str = "root"

    def bone(self, name: str, pivot: tuple[int, int, int], parent: str | None = None) -> None:
        self.bones.append(Bone(name, pivot, parent))

    def cube(self, *args, **kwargs) -> None:
        self.cubes.append(Cube(*args, **kwargs))

    def attach_markings(self, marks: list[dict]) -> "Model":
        """
        Attach texture markings to the cubes they belong to.

        A marking names a cube; it matches that cube exactly, or any cube
        whose name ends with it (so "wing_upper" hits both "left_wing_upper"
        and "right_wing_upper").

        ``face="sides"`` paints the same marking on both east and west, which
        is what an eye on a bird or a dolphin needs: an eye painted only on
        the north (front) face is invisible in profile.
        """
        for c in self.cubes:
            for raw in marks:
                if isinstance(raw, (tuple, list)):
                    # (cube, face, kind, params)
                    cube, face, kind, params = (list(raw) + [None, None, None, {}])[:4]
                    m = dict(params or {}, cube=cube, face=face, type=kind)
                else:
                    m = dict(raw)
                want = m.get("cube")
                if not (want and (c.name == want or c.name.endswith("_" + want))):
                    continue
                face = m.get("face", "north")
                if face == "outer":
                    # the visible flank of a limb: right side -> east, left -> west
                    face = "east" if "right" in c.name else "west"
                faces = ("east", "west") if face == "sides" else (face,)
                for f in faces:
                    c.markings.append(dict(m, face=f))
        return self

    def scaled(self, factor: float) -> "Model":
        """
        Convert a model authored in real-world centimetres into Minecraft
        units (1 unit = 1/16 block).

        Box-UV still needs integer cube sizes, but keeping fractional
        *origins* preserves the spacing and silhouette of small feathers,
        toes and scales.  The generator also authors small species at the
        24-unit detail floor, so this rounding is no longer destructive.
        A tiny physical floor keeps degenerate boxes valid.
        """
        def conv(v: float) -> float:
            return round(v * factor, 4)

        for c in self.cubes:
            lo = [conv(v) for v in c.lo]
            hi = [conv(v) for v in c.hi]
            for i in range(3):
                if hi[i] - lo[i] < 0.02 and abs(c.hi[i] - c.lo[i]) > 1e-6:
                    hi[i] = round(lo[i] + 0.02, 4)
                if hi[i] < lo[i]:
                    lo[i], hi[i] = hi[i], lo[i]
            c.lo = tuple(lo)
            c.hi = tuple(hi)
            # painted details (eyes, stripes) are authored in the same
            # centimetres as the geometry, so they must scale with it
            for d in c.details:
                if "size" in d:
                    d["size"] = max(1, int(round(d["size"] * factor)))
        for b in self.bones:
            b.pivot = tuple(conv(v) for v in b.pivot)
        return self

    def ground(self) -> "Model":
        """
        Put the lowest cube on y = 0.

        Ground animals are already authored that way, but a swimmer is built
        around its body centreline, so its belly sits below the entity origin
        and the mob renders half-buried in the water/floor.  The root bone
        stays at the origin; every cube and child pivot moves up together.
        """
        if not self.cubes:
            return self
        lo_y = min(c.lo[1] for c in self.cubes)
        if abs(lo_y) < 1e-6:
            return self
        for c in self.cubes:
            c.lo = (c.lo[0], c.lo[1] - lo_y, c.lo[2])
            c.hi = (c.hi[0], c.hi[1] - lo_y, c.hi[2])
        for b in self.bones:
            if b.name != self.root:
                b.pivot = (b.pivot[0], b.pivot[1] - lo_y, b.pivot[2])
        return self

    # ------------------------------------------------------------------
    # de-coplanar
    # ------------------------------------------------------------------
    # Two boxes whose faces lie in the same plane, point the same way and
    # overlap are drawn at exactly the same depth. The renderer has to pick
    # one, and it alternates between frames: the texture flickers.
    #
    # The cause here is rounding. The torso is authored with a chest and a
    # rump that are slightly narrower than the body, but after scaling to
    # Minecraft units those widths often round to the *same* integer, so
    # the flanks end up flush.
    #
    # The fix is to inset the offending box by half a unit on each side of
    # the axis, which separates the faces and keeps the silhouette intact:
    # half a unit is 1/32 of a block.

    _FACE_AXIS = {
        "up": (1, 1), "down": (1, -1),
        "east": (0, 1), "west": (0, -1),
        "north": (2, 1), "south": (2, -1),
    }

    def deconflict(self, step: float = 0.0005) -> int:
        """
        Break coplanar box faces.

        Two boxes that overlap and are flush on an axis z-fight: both faces
        sit at exactly the same depth, so the renderer alternates between
        them and the texture flickers.

        Every box is given its own tiny offset, the same offset on all three
        axes so the model keeps its shape, and centred on zero so it does not
        drift off the entity's origin.  The offset spread must stay well
        below 0.1 unit: a literal-scale 7-unit bird cannot absorb the old
        0.7-unit spread without visibly tearing its tail and feet apart.
        Overlaps are irrelevant here - z-fighting needs coplanarity *and*
        overlap - so a sub-pixel separation is enough.
        """
        n = len(self.cubes)
        if n < 2:
            return 0
        # keep the whole spread below 0.08 unit even for the most detailed
        # weta/snail/parrot models
        span = (n - 1) * step
        if span > 0.08:
            step = 0.08 / (n - 1)
        mid = (n - 1) / 2.0
        for i, c in enumerate(self.cubes):
            d = (i - mid) * step
            c.lo = tuple(c.lo[a] + d for a in range(3))
            c.hi = tuple(c.hi[a] + d for a in range(3))
        return n

    def _coplanar_pairs(self):
        """(i, j, axis, sign) for every pair of same-facing coplanar faces."""
        out = []
        cubes = self.cubes
        for i in range(len(cubes)):
            ci = cubes[i]
            for j in range(i + 1, len(cubes)):
                cj = cubes[j]
                for fi, (ai, si) in self._FACE_AXIS.items():
                    for fj, (aj, sj) in self._FACE_AXIS.items():
                        if ai != aj or si != sj:
                            continue
                        if self._plane(ci, ai, si) != self._plane(cj, ai, si):
                            continue
                        if not self._overlap(ci, cj, ai):
                            continue
                        out.append((i, j, ai, si))
        return out

    @staticmethod
    def _plane(cube, axis, sign):
        return cube.hi[axis] if sign > 0 else cube.lo[axis]

    @staticmethod
    def _overlap(ci, cj, axis):
        others = [i for i in range(3) if i != axis]
        for k in others:
            if (min(ci.hi[k], cj.hi[k]) - max(ci.lo[k], cj.lo[k])) <= 0:
                return False
        return True


# --------------------------------------------------------------------------
# texture packing + painting
# --------------------------------------------------------------------------

def _shelf_pack(nets: list[tuple[int, int]], max_width: int = 256) -> list[tuple[int, int]]:
    """Shelf-pack (w, h) rectangles into a list of (x, y) offsets."""
    placements: list[tuple[int, int]] = []
    x = y = shelf_h = 0
    for w, h in nets:
        if x + w > max_width and x > 0:
            x = 0
            y += shelf_h
            shelf_h = 0
        placements.append((x, y))
        x += w
        shelf_h = max(shelf_h, h)
    return placements


def _noise(seed: str, x: int, y: int) -> float:
    """Deterministic 0..1 value for a pixel."""
    h = hashlib.sha256(f"{seed}:{x}:{y}".encode()).digest()
    return h[0] / 255.0


def _shade(c: RGB, f: float) -> RGB:
    return (
        max(0, min(255, int(c[0] * f))),
        max(0, min(255, int(c[1] * f))),
        max(0, min(255, int(c[2] * f))),
    )


def _rect(px, x0: int, y0: int, x1: int, y1: int, color: RGB) -> None:
    for y in range(max(0, y0), min(len(px), y1)):
        for x in range(max(0, x0), len(px[0])):
            if x0 <= x < x1 and y0 <= y < y1:
                px[y][x] = color


def _mottle(px, x0: int, y0: int, x1: int, y1: int, color: RGB, seed: str, strength: float = 0.12) -> None:
    for y in range(max(0, y0), min(len(px), y1)):
        for x in range(max(0, x0), min(len(px[0]), x1)):
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            n = _noise(seed, x, y)
            if n < strength:
                px[y][x] = _shade(color, 0.86)
            elif n < strength * 2:
                px[y][x] = _shade(color, 1.12)


def _eye(px, x0, y0, x1, y1, seed, iris=(40, 30, 20), size=None):
    """Blocky eye: sclera, coloured iris, black pupil, white highlight."""
    w = x1 - x0
    h = y1 - y0
    if w < 2 or h < 2:
        return
    s = size or max(1, min(w, h) // 3)
    s = max(1, min(s, w - 1, h - 1))
    ex0 = x0 + (w - s) // 2
    ey0 = y0 + (h - s) // 2
    _rect(px, ex0, ey0, ex0 + s, ey0 + s, (242, 242, 238))
    p = max(1, s // 2)
    _rect(px, ex0 + (s - p) // 2, ey0 + (s - p) // 2,
          ex0 + (s + p) // 2, ey0 + (s + p) // 2, (16, 16, 18))
    if s >= 4:
        _rect(px, ex0 + 1, ey0 + 1, ex0 + 2, ey0 + 2, (250, 250, 250))


def _ellipse(px, cx, cy, rx, ry, color):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if (x + 0.5 - cx) ** 2 / max(0.5, rx) ** 2 + (y + 0.5 - cy) ** 2 / max(0.5, ry) ** 2 <= 1.0:
                px[y][x] = color


def _soft_ellipse(px, cx, cy, rx, ry, color, core=0.55):
    """Ellipse with a feathered edge, for markings like a throat patch."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        if not (0 <= y < len(px)):
            continue
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not (0 <= x < len(px[0])):
                continue
            d = ((x + 0.5 - cx) ** 2 / max(0.5, rx) ** 2
                 + (y + 0.5 - cy) ** 2 / max(0.5, ry) ** 2) ** 0.5
            if d <= 1.0:
                f = 1.0 if d <= core else (1.0 - (d - core) / (1.0 - core))
            elif d <= 1.3:
                f = (1.3 - d) / 0.3 * 0.4
            else:
                continue
            base = px[y][x]
            px[y][x] = (int(base[0] + (color[0] - base[0]) * f),
                        int(base[1] + (color[1] - base[1]) * f),
                        int(base[2] + (color[2] - base[2]) * f))


def _spots(px, x0, y0, x1, y1, color, count, radius, seed):
    import random as _r
    rng = _r.Random(seed)
    for _ in range(count):
        cx = rng.randint(x0, max(x0, x1 - 1))
        cy = rng.randint(y0, max(y0, y1 - 1))
        r = max(1, radius)
        for y in range(max(0, cy - r), min(len(px), cy + r + 1)):
            for x in range(max(0, cx - r), min(len(px[0]), cx + r + 1)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    px[y][x] = color


def _scales(px, x0, y0, x1, y1, color, step):
    """Overlapping arcs, for reptilian and fish skin."""
    step = max(2, step)
    for row, y in enumerate(range(y0, y1, max(1, step // 2))):
        off = (row % 2) * (step // 2)
        for x in range(x0 - off, x1, step):
            for yy in range(y, min(y1, y + step // 2 + 1)):
                for xx in range(x, min(x1, x + step)):
                    if (xx - x) ** 2 + (yy - y) ** 2 <= (step / 2.0) ** 2:
                        px[yy][xx] = color


def _resolve(col, base):
    """Resolve a colour reference: a tuple, a palette key, or a shade factor."""
    if col is None:
        return base
    if isinstance(col, (tuple, list)):
        return tuple(col)
    if isinstance(col, (int, float)):
        return _shade(base, float(col))
    return base


def _palette_color(ref, base, palette):
    """
    Resolve a marking colour.

    A palette entry may be an absolute colour (a tuple) or a shade factor
    (a number, meaning "this much lighter/darker than the cube it sits on"),
    so palette values go through the same resolver as literal ones.
    """
    if isinstance(ref, str):
        ref = palette.get(ref, base)
    return _resolve(ref, base)


def _draw_marking(px, rect, kind, spec, base_color, palette):
    """Draw one marking into a face rectangle (u1, v1, u2, v2)."""
    u1, v1, u2, v2 = rect
    w, h = u2 - u1, v2 - v1
    if w <= 0 or h <= 0:
        return
    raw = spec.get("color")
    color = _palette_color(raw, base_color, palette)

    if kind == "eye":
        s = spec.get("size")
        s = max(1, int(s * min(w, h))) if s else max(1, min(w, h) // 3)
        cx = u1 + int(w * spec.get("u", 0.5))
        cy = v1 + int(h * spec.get("v", 0.5))
        iris = _resolve(
            palette.get(spec["iris"], (40, 30, 20))
            if isinstance(spec.get("iris"), str) else spec.get("iris"),
            (40, 30, 20))
        _eye(px, cx - s, cy - s, cx + s, cy + s, spec.get("seed", "e"), iris, s)
    elif kind == "oval":
        cx = u1 + w * spec.get("u", 0.5)
        cy = v1 + h * spec.get("v", 0.5)
        rx = max(0.6, w * spec.get("w", 0.4) / 2)
        ry = max(0.6, h * spec.get("h", 0.4) / 2)
        if spec.get("soft", True):
            _soft_ellipse(px, cx, cy, rx, ry, color, spec.get("core", 0.55))
        else:
            _ellipse(px, cx, cy, rx, ry, color)
    elif kind == "rect":
        _rect(px, u1 + int(w * spec.get("u", 0)), v1 + int(h * spec.get("v", 0)),
              u1 + int(w * spec.get("u2", 1)), v1 + int(h * spec.get("v2", 1)), color)
    elif kind == "band":
        _rect(px, u1, v1 + int(h * spec.get("v", 0)), u2, v1 + int(h * spec.get("v2", 1)), color)
    elif kind == "vband":
        _rect(px, u1 + int(w * spec.get("u", 0)), v1, u1 + int(w * spec.get("u2", 1)), v2, color)
    elif kind == "spots":
        _spots(px, u1, v1, u2, v2, color, spec.get("count", 6), spec.get("r", 1),
               spec.get("seed", "s"))
    elif kind == "speckle":
        _spots(px, u1, v1, u2, v2, color, spec.get("count", 14), 1, spec.get("seed", "k"))
    elif kind == "scales":
        _scales(px, u1, v1, u2, v2, color, spec.get("step", 3))
    elif kind == "streak":
        import random as _r
        rng = _r.Random(spec.get("seed", "f"))
        for x in range(u1, u2):
            if rng.random() < spec.get("density", 0.4):
                y0 = v1 + rng.randint(0, max(0, h - 2))
                ln = rng.randint(1, max(1, h // 2))
                _rect(px, x, y0, x + 1, min(v2, y0 + ln),
                      _shade(color, rng.uniform(0.86, 1.14)))
    elif kind == "spiral":
        # A square spiral with a one-pixel groove, for a flat-coiled snail
        # shell.  The path is authored on an 8x8 grid and scaled to the face;
        # at the shell's texture resolution a one-pixel line with a one-pixel
        # gap is the only spiral that reads.
        path = [
            (4, 4), (5, 4), (6, 4), (6, 5), (6, 6), (5, 6), (4, 6),
            (3, 6), (2, 6), (1, 6), (1, 5), (1, 4), (1, 3), (1, 2),
            (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (6, 2),
            (6, 3), (6, 4), (6, 5), (5, 5), (4, 5), (3, 5), (3, 4),
            (3, 3), (4, 3),
        ]
        for gx, gy in path:
            x = u1 + int(gx * w / 8.0)
            y = v1 + int(gy * h / 8.0)
            x = max(u1, min(u2 - 1, x))
            y = max(v1, min(v2 - 1, y))
            _rect(px, x, y, x + 1, y + 1, color)


def render_texture(model: Model, palette: dict | None = None) -> tuple[list[list[RGB]], int, int, dict[str, tuple[int, int]]]:
    """
    Render the model's texture.

    Returns (pixels, width, height, cube_uv_offsets) where pixels is
    row-major (row 0 == v 0) and cube_uv_offsets maps cube name -> (u, v).
    """
    nets = []
    rects = {}
    for c in model.cubes:
        w, h, d = c.size
        if w <= 0 or h <= 0 or d <= 0:
            raise ValueError(f"cube {c.name} has non-positive size {c.size}")
        rects[c.name] = face_rects(w, h, d)
        nets.append(net_size(w, h, d))

    placements = _shelf_pack(nets)

    # Texture size: each axis rounded up to a power of two (Bedrock prefers POT).
    used_w = max((p[0] + n[0]) for p, n in zip(placements, nets))
    used_h = max((p[1] + n[1]) for p, n in zip(placements, nets))

    def pot(v: int) -> int:
        s = 16
        while s < v:
            s *= 2
        return s

    width, height = pot(used_w), pot(used_h)

    pixels = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
    palette = palette or {}

    offsets: dict[str, tuple[int, int]] = {}
    for cube, (nw, nh), (ox, oy) in zip(model.cubes, nets, placements):
        offsets[cube.name] = (ox, oy)
        for face in FACES:
            u1, v1, u2, v2 = rects[cube.name][face]
            gx1, gy1 = ox + u1, oy + v1
            gx2, gy2 = ox + u2, oy + v2
            color = cube.face_color(face)
            # Per-face shading gives the models readable form under flat light.
            factor = {
                "up": 1.14, "down": 0.74, "east": 0.88,
                "north": 1.0, "west": 0.82, "south": 0.92,
            }[face]
            base = _shade(color, factor)
            _rect(pixels, gx1, gy1, gx2, gy2, base)
            _mottle(pixels, gx1, gy1, gx2, gy2, base, cube.name + face)
            # A subtle one-pixel bevel/outline around each face makes the
            # small, low-resolution boxes read as separate body parts instead
            # of one flat silhouette.
            if gx2 - gx1 > 1 and gy2 - gy1 > 1:
                hi = _shade(base, 1.10)
                lo = _shade(base, 0.76)
                for x in range(gx1, gx2):
                    pixels[gy1][x] = hi
                    pixels[gy2 - 1][x] = lo
                for y in range(gy1, gy2):
                    pixels[y][gx1] = hi
                    pixels[y][gx2 - 1] = lo

        # markings and legacy details share one drawing pass
        for det in list(cube.details) + list(cube.markings):
            face = det.get("face", "north")
            u1, v1, u2, v2 = rects[cube.name][face]
            gx1, gy1 = ox + u1, oy + v1
            gx2, gy2 = ox + u2, oy + v2
            kind = det.get("type", det.get("kind", "rect"))
            if kind == "eye":
                fw, fh = gx2 - gx1, gy2 - gy1
                cx = gx1 + int(fw * det.get("u", 0.5))
                cy = gy1 + int(fh * det.get("v", 0.35))
                s = det.get("size", max(2, min(fw, fh) // 3))
                if isinstance(s, float) and s < 1.0:
                    s = max(1, int(s * min(fw, fh)))
                iris = _resolve(
                    palette.get(det.get("iris"), (40, 30, 20))
                    if isinstance(det.get("iris"), str) else det.get("iris"),
                    (40, 30, 20))
                _eye(pixels, cx - s // 2, cy - s // 2, cx + s // 2 + 1, cy + s // 2 + 1,
                     cube.name, iris, s)
            else:
                _draw_marking(pixels, (gx1, gy1, gx2, gy2), kind, det,
                              cube.face_color(face), palette)

    return pixels, width, height, offsets


def write_png(path: str, pixels: list[list[RGB]], width: int, height: int) -> None:
    from PIL import Image
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGBA", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[y][x]
            px[x, y] = (r, g, b, 255)
    img.save(path)


# --------------------------------------------------------------------------
# geometry export
# --------------------------------------------------------------------------

def to_geo_json(model: Model, offsets: dict[str, tuple[int, int]], identifier: str,
                texture_size: tuple[int, int] = (64, 64)) -> dict:
    """Build a Bedrock .geo.json document from a model."""
    bones = []
    bone_index: dict[str, int] = {}
    for b in model.bones:
        entry: dict = {"name": b.name, "pivot": list(b.pivot)}
        if b.parent:
            entry["parent"] = b.parent
        bone_index[b.name] = len(bones)
        bones.append(entry)

    # Group cubes under their owning bone.
    by_bone: dict[str, list[dict]] = {}
    for c in model.cubes:
        # Box-UV maps a cube by its integer size.  Keep the fractional
        # origins (they preserve the silhouette) but round the cube size so
        # the texture face rectangles and geometry agree.
        by_bone.setdefault(c.bone, []).append({
            "origin": [round(v, 4) for v in c.lo],
            "size": list(c.size),
            "uv": list(offsets[c.name]),
        })

    for bone_name, cubes in by_bone.items():
        bones[bone_index[bone_name]]["cubes"] = cubes

    # Bounds -> visible box (in blocks, 16 units per block).
    #
    # visible_bounds_offset is the CENTRE of the box, not its bottom edge.
    # The old code used lo[1], which put the box below the model: tall wings,
    # dorsal fins and raised necks fell outside it and were culled at the
    # edge of the screen.  Use the real centre and a little padding.
    lo = [min(c.lo[i] for c in model.cubes) for i in range(3)]
    hi = [max(c.hi[i] for c in model.cubes) for i in range(3)]
    centre = [(lo[i] + hi[i]) / 2.0 / 16.0 for i in range(3)]
    width = max((hi[0] - lo[0]) / 16.0, (hi[2] - lo[2]) / 16.0)
    height = (hi[1] - lo[1]) / 16.0
    # 15% padding keeps a wingtip or tail fluke inside the culling box even
    # while the bone is mid-animation.
    width = max(0.5, round(width * 1.15, 2))
    height = max(0.5, round(height * 1.15, 2))

    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": identifier,
                "texture_width": texture_size[0],
                "texture_height": texture_size[1],
                "visible_bounds_width": width,
                "visible_bounds_height": height,
                "visible_bounds_offset": [round(centre[0], 2), round(centre[1], 2),
                                          round(centre[2], 2)],
            },
            "bones": bones,
        }],
    }
