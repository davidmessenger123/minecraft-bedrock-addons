"""
Detailed, proportion-accurate model builders for the NZ animals.

Everything is authored in REAL-WORLD CENTIMETRES so the proportions are
literally correct, then scaled to Minecraft units (1 unit = 1/16 block) by
`Model.scaled()`, which the roster drives from each species' target length.

The models are deliberately built from many overlapping boxes.  A single box
per body part is cheap, but it reads as a cardboard carton in game: no
shoulders, no tapered muzzle, no wing, no visible eye.  The builders below
give every archetype a proper silhouette:

* birds have a tapered torso, a neck, a skull with a brow and two mandibles,
  eyes on both sides, real wings (folded for flightless species), fanned tail
  feathers and jointed legs with toes;
* quadrupeds have a chest/rump/shoulder mass, a neck, a muzzle and jaw, four
  jointed legs and a tapering tail (seals use flippers instead);
* swimmers have a rostrum, melon, tapered trunk, countershaded belly,
  pectoral flippers, a dorsal fin and flukes;
* insects have three body segments, six jointed legs, mandibles and segmented
  antennae;
* the snail has a flat spiral coil shell instead of a stack of boxes.

Axes:  y up, x left/right, -z is the front (the animal faces north).
"""

from __future__ import annotations

from nzlib import Model


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _box(m: Model, bone: str, name: str, lo, hi, color, faces=None,
         details=None, markings=None):
    """Add a box, swapping any reversed axis so the geometry stays valid."""
    out_lo, out_hi = [], []
    for a, b in zip(lo, hi):
        if b < a:
            a, b = b, a
        out_lo.append(float(a))
        out_hi.append(float(b))
    m.cube(name, bone, tuple(out_lo), tuple(out_hi), color,
           faces or {}, details or [], markings or [])
    return m


def _mx(sx: int, a: float, b: float) -> tuple[float, float]:
    """Mirror a pair of x coordinates for the left (sx=-1) or right side."""
    x0, x1 = sx * a, sx * b
    return (min(x0, x1), max(x0, x1))


def _eye_details(size: float, iris=None) -> list[dict]:
    """Eyes on both side faces; a north-facing eye is invisible in profile."""
    d = {"type": "eye", "size": size}
    if iris is not None:
        d["iris"] = iris
    return [dict(d, face="east", u=0.52, v=0.44),
            dict(d, face="west", u=0.48, v=0.44)]


def _foot(m: Model, bone: str, prefix: str, cx: float, cz: float,
          leg_d: float, foot_len: float, color, y_top: float,
          toe_color=None):
    """A padded foot with three forward toes and one back toe."""
    toe = toe_color or color
    half = max(1.0, leg_d * 0.5)
    _box(m, bone, f"{prefix}_foot", (cx - half, 0, cz - half - foot_len * 0.15),
         (cx + half, y_top, cz + half + foot_len * 0.25), color)
    for i, off in enumerate((-0.5, 0.0, 0.5)):
        _box(m, bone, f"{prefix}_toe{i}",
             (cx + off * leg_d - leg_d * 0.16, 0,
              cz + half + foot_len * 0.15),
             (cx + off * leg_d + leg_d * 0.16, y_top * 0.78,
              cz + half + foot_len * 0.95), toe)
    _box(m, bone, f"{prefix}_back_toe",
         (cx - leg_d * 0.2, 0, cz - half - foot_len * 0.55),
         (cx + leg_d * 0.2, y_top * 0.7, cz - half - foot_len * 0.05), toe)


def _split(body_h: float, belly_frac: float = 0.34) -> tuple[float, float]:
    """Height of the lower (belly) mass and of the upper (back) mass."""
    low = body_h * belly_frac
    return low, body_h - low


# ---------------------------------------------------------------------------
# birds
# ---------------------------------------------------------------------------

def build_bird(p: dict, pal: dict) -> Model:
    """
    A perching/ground bird with a counter-shaded torso, a neck, a skull with
    a brow and two mandibles, eyes on both sides, wings, fanned tail feathers
    and jointed legs.

    The wing is built as a real airfoil: `wing_len` is the distance from the
    shoulder to the tip, and the front-to-back chord is derived from the body
    length.  The old builder ignored `wing_len` and made a 1 cm plate along
    the flank, which is why every bird looked wingless.
    """
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    belly = pal.get("belly", pal["body"])
    back = pal.get("back", pal["body"])
    wing = pal.get("wing", pal["body"])
    wing_top = pal.get("wing_top", wing)

    body_len, body_h, body_w = r["body_len"], r["body_h"], r["body_w"]
    head_len, head_h, head_w = r["head_len"], r["head_h"], r["head_w"]
    beak_len, beak_w, beak_h = r["beak_len"], r["beak_w"], r["beak_h"]
    leg_up, leg_low, foot_len, leg_d = (r["leg_upper"], r["leg_lower"],
                                        r["foot_len"], r["leg_d"])
    wing_len, wing_t = r["wing_len"], r["wing_t"]
    tail_len, tail_h, tail_w = r["tail_len"], r["tail_h"], r["tail_w"]
    crest_h = r.get("crest", 0)
    flying = p.get("kind") == "fly" or p.get("motion") == "bird_fly"

    hip = leg_up + leg_low
    body_top = hip + body_h
    body_front = -body_len / 2
    body_back = body_len / 2
    low_h, up_h = _split(body_h)

    # --- torso ------------------------------------------------------------
    # No single full-length cube: a stack of tapered masses gives the body a
    # chest, a back hump and a rump instead of a cardboard box silhouette.
    _box(m, "body", "belly",
         (-body_w * 0.44, hip, body_front + body_len * 0.05),
         (body_w * 0.44, hip + body_h * 0.32, body_back - body_len * 0.05),
         belly)
    _box(m, "body", "body",
         (-body_w * 0.46, hip + body_h * 0.18, body_front + body_len * 0.10),
         (body_w * 0.46, hip + body_h * 0.80, body_back - body_len * 0.10),
         pal["body"])
    _box(m, "body", "back",
         (-body_w * 0.40, hip + body_h * 0.62, body_front + body_len * 0.14),
         (body_w * 0.40, body_top, body_back - body_len * 0.14), back)
    _box(m, "body", "chest",
         (-body_w * 0.50, hip + body_h * 0.12, body_front),
         (body_w * 0.50, hip + body_h * 0.84, body_front + body_len * 0.28),
         pal["body"])
    _box(m, "body", "rump",
         (-body_w * 0.42, hip + body_h * 0.12, body_back - body_len * 0.28),
         (body_w * 0.42, hip + body_h * 0.74, body_back), back)
    _box(m, "body", "chest_top",
         (-body_w * 0.36, hip + body_h * 0.72, body_front + body_len * 0.02),
         (body_w * 0.36, hip + body_h * 0.92, body_front + body_len * 0.22),
         back)
    _box(m, "body", "rump_top",
         (-body_w * 0.32, hip + body_h * 0.62, body_back - body_len * 0.24),
         (body_w * 0.32, hip + body_h * 0.82, body_back - body_len * 0.04),
         back)

    # --- neck: two stepped boxes, hidden under the head -------------------
    neck_top = body_top + head_h * 0.26
    neck_cz = body_front + body_len * 0.03
    _box(m, "body", "neck_base",
         (-head_w * 0.32, body_top - body_h * 0.10, neck_cz - head_w * 0.20),
         (head_w * 0.32, body_top + head_h * 0.22, neck_cz + head_w * 0.55),
         pal.get("neck", pal["head"]))
    _box(m, "body", "neck_upper",
         (-head_w * 0.25, body_top + head_h * 0.04, neck_cz - head_w * 0.30),
         (head_w * 0.25, neck_top, neck_cz + head_w * 0.30),
         pal.get("neck", pal["head"]))

    # --- head -------------------------------------------------------------
    head_cz = body_front - head_len * 0.35
    head_cy = neck_top + head_h * 0.44
    _box(m, "head", "skull",
         (-head_w * 0.50, head_cy - head_h * 0.50, head_cz - head_len * 0.50),
         (head_w * 0.50, head_cy + head_h * 0.50, head_cz + head_len * 0.50),
         pal["head"], details=_eye_details(head_h * 0.24, pal.get("iris", "eye")))
    _box(m, "head", "brow",
         (-head_w * 0.44, head_cy + head_h * 0.16, head_cz - head_len * 0.48),
         (head_w * 0.44, head_cy + head_h * 0.44, head_cz + head_len * 0.14),
         pal.get("brow", pal["head"]))
    _box(m, "head", "cheek",
         (-head_w * 0.46, head_cy - head_h * 0.34, head_cz - head_len * 0.12),
         (head_w * 0.46, head_cy + head_h * 0.18, head_cz + head_len * 0.42),
         pal.get("neck", pal["head"]))
    if beak_len > 0:
        _box(m, "head", "beak",
             (-beak_w * 0.50, head_cy - beak_h * 0.12, head_cz - head_len * 0.50 - beak_len),
             (beak_w * 0.50, head_cy + beak_h * 0.46, head_cz - head_len * 0.30),
             pal["beak"])
        _box(m, "head", "beak_lower",
             (-beak_w * 0.42, head_cy - beak_h * 0.52, head_cz - head_len * 0.50 - beak_len * 0.88),
             (beak_w * 0.42, head_cy - beak_h * 0.04, head_cz - head_len * 0.30),
             pal.get("beak", pal["head"]))
    if crest_h > 0:
        _box(m, "head", "crest",
             (-head_w * 0.30, head_cy + head_h * 0.36, head_cz - head_len * 0.34),
             (head_w * 0.30, head_cy + head_h * 0.36 + crest_h, head_cz + head_len * 0.18),
             pal.get("crest", pal["head"]))
        _box(m, "head", "crest_tip",
             (-head_w * 0.20, head_cy + head_h * 0.34, head_cz + head_len * 0.02),
             (head_w * 0.20, head_cy + head_h * 0.34 + crest_h * 0.72, head_cz + head_len * 0.34),
             pal.get("crest", pal["head"]))

    # --- wings ------------------------------------------------------------
    shoulder_y = hip + body_h * 0.60
    wing_root_z = body_front + body_len * 0.18
    chord = body_len * (0.30 if flying else 0.26)
    span = max(body_w * (0.45 if flying else 0.30),
               wing_len * (1.05 if flying else 0.30))
    th = max(1.0, wing_t * 0.55)
    for side, sx in (("left", -1), ("right", 1)):
        bone = f"{side}_wing"
        if flying:
            # A swept, tapered planform.  The solid leading-edge segments
            # shorten toward the tip, and the feather vanes only fringe the
            # trailing edge instead of filling it in, so the wing narrows
            # from root to tip rather than reading as a rectangle.
            root_x = body_w * 0.45
            dihedral = span * 0.16

            x0, x1 = _mx(sx, root_x, root_x + span * 0.35)
            _box(m, bone, f"{side}_wing_upper",
                 (x0, shoulder_y - th * 0.50, wing_root_z),
                 (x1, shoulder_y + th * 0.50, wing_root_z + chord * 0.95),
                 wing, faces={"up": wing_top, "down": belly})
            x2, x3 = _mx(sx, root_x + span * 0.35, root_x + span * 0.66)
            _box(m, bone, f"{side}_wing_lower",
                 (x2, shoulder_y + dihedral * 0.35 - th * 0.40,
                  wing_root_z + chord * 0.12),
                 (x3, shoulder_y + dihedral * 0.35 + th * 0.40,
                  wing_root_z + chord * 0.72),
                 wing_top, faces={"up": wing_top, "down": wing})
            x4, x5 = _mx(sx, root_x + span * 0.66, root_x + span * 0.90)
            _box(m, bone, f"{side}_wing_tip",
                 (x4, shoulder_y + dihedral * 0.75 - th * 0.30,
                  wing_root_z + chord * 0.26),
                 (x5, shoulder_y + dihedral * 0.75 + th * 0.30,
                  wing_root_z + chord * 0.52), wing_top)
            x6, x7 = _mx(sx, root_x + span * 0.90, root_x + span)
            _box(m, bone, f"{side}_wing_end",
                 (x6, shoulder_y + dihedral - th * 0.22,
                  wing_root_z + chord * 0.36),
                 (x7, shoulder_y + dihedral + th * 0.22,
                  wing_root_z + chord * 0.54), wing_top)

            # Short secondary vanes along the inner trailing edge.
            for i in range(4):
                fx0, fx1 = _mx(sx, root_x + span * (0.12 + i * 0.10),
                               root_x + span * (0.185 + i * 0.10))
                _box(m, bone, f"{side}_secondary{i}",
                     (fx0, shoulder_y + dihedral * 0.10 - th * 0.28,
                      wing_root_z + chord * (0.93 - i * 0.015)),
                     (fx1, shoulder_y + dihedral * 0.10 + th * 0.14,
                      wing_root_z + chord * (1.04 - i * 0.025)), wing_top)
            # Primary vanes: longer, but still narrower than the root chord.
            for i in range(5):
                fx0, fx1 = _mx(sx, root_x + span * (0.62 + i * 0.07),
                               root_x + span * (0.675 + i * 0.07))
                _box(m, bone, f"{side}_primary{i}",
                     (fx0, shoulder_y + dihedral * 0.60 - th * 0.22,
                      wing_root_z + chord * (0.48 + i * 0.03)),
                     (fx1, shoulder_y + dihedral * 0.60 + th * 0.12,
                      wing_root_z + chord * (0.74 + i * 0.02)), wing_top)
            # A small covert at the shoulder hides the join with the body.
            _box(m, bone, f"{side}_wing_covert",
                 (x0, shoulder_y + th * 0.18, wing_root_z - chord * 0.02),
                 (x1, shoulder_y + th * 0.55, wing_root_z + chord * 0.34),
                 wing_top)
        else:
            # Folded wing: a tall, narrow oval lying against the flank.  A
            # kiwi's wing is only a few centimetres long; a kakapo's is much
            # larger, but both are tucked in.
            thick = max(body_w * 0.10, 1.0)
            x0, x1 = _mx(sx, body_w * 0.45, body_w * 0.45 + thick)
            _box(m, bone, f"{side}_wing_upper",
                 (x0, shoulder_y + body_h * 0.02, wing_root_z + body_len * 0.10),
                 (x1, shoulder_y + body_h * 0.24, wing_root_z + body_len * 0.78),
                 wing, faces={"up": wing_top, "down": belly})
            _box(m, bone, f"{side}_wing_lower",
                 (x0, shoulder_y - body_h * 0.15, wing_root_z + body_len * 0.16),
                 (x1, shoulder_y + body_h * 0.05, wing_root_z + body_len * 0.90),
                 wing_top, faces={"up": wing_top, "down": wing})
            _box(m, bone, f"{side}_wing_tip",
                 (x0, shoulder_y - body_h * 0.08, wing_root_z + body_len * 0.84),
                 (x1, shoulder_y + body_h * 0.09, wing_root_z + body_len * 0.96),
                 wing_top)

    # --- legs and feet ----------------------------------------------------
    leg_x = body_w * 0.26
    for side, sx in (("left", -1), ("right", 1)):
        cx = sx * leg_x
        bone = f"{side}_leg"
        _box(m, bone, f"{side}_thigh",
             (cx - leg_d * 0.45, hip - leg_up, -leg_d * 0.45),
             (cx + leg_d * 0.45, hip, leg_d * 0.45), pal["leg"])
        _box(m, bone, f"{side}_shank",
             (cx - leg_d * 0.32, hip - leg_up - leg_low, -leg_d * 0.32),
             (cx + leg_d * 0.32, hip - leg_up, leg_d * 0.32), pal["leg"])
        _foot(m, bone, side, cx, 0.0, leg_d, foot_len,
              pal.get("foot", pal["leg"]), max(1.2, leg_d * 0.55),
              pal.get("foot", pal["leg"]))

    # --- tail -------------------------------------------------------------
    tail_y = hip + low_h * 0.55
    _box(m, "tail", "tail",
         (-tail_w * 0.45, tail_y, body_back - body_len * 0.04),
         (tail_w * 0.45, tail_y + tail_h, body_back + tail_len * 0.15),
         pal.get("tail", pal["body"]))
    # Five broad feathers; the central pair is longest, giving a visible fan
    # from above instead of a single stick.
    for i in range(5):
        t = abs(i - 2) / 2.0
        fx0 = -tail_w * 0.85 + i * tail_w * 0.34
        fx1 = fx0 + tail_w * 0.32
        z1 = body_back + tail_len * (0.86 + 0.14 * (1.0 - t))
        y0 = tail_y + tail_h * (0.30 + 0.08 * (1.0 - t))
        _box(m, "tail", f"tail_fan_{i}",
             (fx0, y0, body_back + tail_len * 0.05),
             (fx1, y0 + tail_h * 0.55, z1),
             pal.get("tail", pal["body"]))

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, hip, 0), m.root)
    m.bone("head", (0, neck_top, head_cz + head_len * 0.20), "body")
    m.bone("tail", (0, tail_y, body_back), "body")
    for side, sx in (("left", -1), ("right", 1)):
        m.bone(f"{side}_wing", (sx * body_w * 0.45, shoulder_y,
                                wing_root_z + chord * 0.30), "body")
        m.bone(f"{side}_leg", (sx * leg_x, hip, 0), m.root)
    return m.ground()


# ---------------------------------------------------------------------------
# four-legged land animals
# ---------------------------------------------------------------------------

def build_quadruped(p: dict, pal: dict) -> Model:
    """
    Tuatara and seals.

    The tuatara gets a long, low torso, a neck, a skull with a brow and jaw,
    four jointed legs, a dorsal crest and a tapering tail.  Seals get the same
    torso/head treatment but flippers instead of legs, and the belly rests on
    the ground.
    """
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    belly = pal.get("belly", pal["body"])
    back = pal.get("back", pal["body"])

    body_len, body_h, body_w = r["body_len"], r["body_h"], r["body_w"]
    head_len, head_h, head_w = r["head_len"], r["head_h"], r["head_w"]
    snout_len = r.get("snout_len", head_len * 0.3)
    neck_len = r.get("neck_len", head_len * 0.55)
    leg_up, leg_low, foot_len, leg_d = (r["leg_upper"], r["leg_lower"],
                                        r["foot_len"], r["leg_d"])
    tail_len, tail_h, tail_w = r["tail_len"], r["tail_h"], r["tail_w"]
    crest_h = r.get("crest", 0)
    flipper = r.get("flipper", False)

    hip = 0.0 if flipper else leg_up + leg_low
    body_top = hip + body_h
    body_front = -body_len / 2
    body_back = body_len / 2
    low_h, up_h = _split(body_h, 0.30)

    # --- torso ------------------------------------------------------------
    # A smaller central barrel plus shoulder, hip and belly masses gives a
    # tapered body; the old full-length box read as a shipping container.
    _box(m, "body", "belly",
         (-body_w * 0.42, hip, body_front + body_len * 0.08),
         (body_w * 0.42, hip + body_h * 0.30, body_back - body_len * 0.08),
         belly)
    _box(m, "body", "body",
         (-body_w * 0.42, hip + body_h * 0.20, body_front + body_len * 0.14),
         (body_w * 0.42, hip + body_h * 0.72, body_back - body_len * 0.14),
         pal["body"])
    _box(m, "body", "back",
         (-body_w * 0.36, hip + body_h * 0.60, body_front + body_len * 0.18),
         (body_w * 0.36, body_top, body_back - body_len * 0.18), back)
    _box(m, "body", "chest",
         (-body_w * 0.48, hip + body_h * 0.12, body_front),
         (body_w * 0.48, hip + body_h * 0.62, body_front + body_len * 0.26),
         pal["body"])
    _box(m, "body", "rump",
         (-body_w * 0.38, hip + body_h * 0.12, body_back - body_len * 0.26),
         (body_w * 0.38, hip + body_h * 0.58, body_back), back)
    _box(m, "body", "shoulders",
         (-body_w * 0.44, hip + body_h * 0.55, body_front + body_len * 0.02),
         (body_w * 0.44, hip + body_h * 0.78,
          body_front + body_len * 0.22), pal["body"])
    _box(m, "body", "hips",
         (-body_w * 0.40, hip + body_h * 0.52, body_back - body_len * 0.24),
         (body_w * 0.40, hip + body_h * 0.72,
          body_back - body_len * 0.02), back)
    _box(m, "body", "chest_top",
         (-body_w * 0.34, hip + body_h * 0.62, body_front + body_len * 0.02),
         (body_w * 0.34, hip + body_h * 0.82, body_front + body_len * 0.22),
         back)
    _box(m, "body", "rump_top",
         (-body_w * 0.30, hip + body_h * 0.56, body_back - body_len * 0.24),
         (body_w * 0.30, hip + body_h * 0.76, body_back - body_len * 0.04),
         back)
    _box(m, "body", "belly_front",
         (-body_w * 0.34, hip + body_h * 0.04, body_front + body_len * 0.02),
         (body_w * 0.34, hip + body_h * 0.24, body_front + body_len * 0.14),
         belly)
    _box(m, "body", "belly_rear",
         (-body_w * 0.32, hip + body_h * 0.04, body_back - body_len * 0.14),
         (body_w * 0.32, hip + body_h * 0.22, body_back - body_len * 0.02),
         belly)

    # --- neck and head ----------------------------------------------------
    neck_w = head_w * (0.80 if flipper else 0.68)
    head_cz = body_front - head_len * 0.42
    head_cy = hip + body_h * 0.60 + neck_len
    _box(m, "body", "neck_lower",
         (-neck_w * 0.55, hip + body_h * 0.30, body_front - head_len * 0.08),
         (neck_w * 0.55, head_cy - head_h * 0.18,
          body_front + head_len * 0.10 + neck_w * 0.75),
         pal.get("neck", pal["head"]))
    _box(m, "body", "neck_upper",
         (-neck_w * 0.45, hip + body_h * 0.48, body_front - head_len * 0.28),
         (neck_w * 0.45, head_cy, body_front + head_len * 0.05),
         pal.get("neck", pal["head"]))

    _box(m, "head", "skull",
         (-head_w * 0.50, head_cy - head_h * 0.50, head_cz - head_len * 0.50),
         (head_w * 0.50, head_cy + head_h * 0.50, head_cz + head_len * 0.50),
         pal["head"], details=_eye_details(head_h * 0.24, pal.get("iris", "eye")))
    _box(m, "head", "brow",
         (-head_w * 0.46, head_cy + head_h * 0.14, head_cz - head_len * 0.46),
         (head_w * 0.46, head_cy + head_h * 0.44, head_cz + head_len * 0.16),
         pal.get("brow", pal["head"]))
    _box(m, "head", "muzzle",
         (-head_w * 0.32, head_cy - head_h * 0.34, head_cz - head_len * 0.50 - snout_len),
         (head_w * 0.32, head_cy + head_h * 0.16, head_cz - head_len * 0.20),
         pal.get("muzzle", pal["head"]))
    _box(m, "head", "jaw",
         (-head_w * 0.34, head_cy - head_h * 0.50, head_cz - head_len * 0.46 - snout_len * 0.82),
         (head_w * 0.34, head_cy - head_h * 0.16, head_cz - head_len * 0.18),
         pal.get("muzzle", pal["head"]))
    if flipper:
        for side, sx in (("left", -1), ("right", 1)):
            _box(m, "head", f"{side}_whisker_pad",
                 (sx * head_w * 0.30 - head_w * 0.10, head_cy - head_h * 0.30,
                  head_cz - head_len * 0.54 - snout_len * 0.35),
                 (sx * head_w * 0.30 + head_w * 0.10, head_cy - head_h * 0.04,
                  head_cz - head_len * 0.34),
                 pal.get("muzzle", pal["head"]))
            _box(m, "head", f"{side}_ear",
                 (sx * head_w * 0.44 - head_w * 0.08, head_cy + head_h * 0.10,
                  head_cz + head_len * 0.16),
                 (sx * head_w * 0.44 + head_w * 0.08, head_cy + head_h * 0.30,
                  head_cz + head_len * 0.34),
                 pal.get("head", pal["body"]))
        _box(m, "head", "nose",
             (-head_w * 0.13, head_cy - head_h * 0.12,
              head_cz - head_len * 0.50 - snout_len),
             (head_w * 0.13, head_cy + head_h * 0.04,
              head_cz - head_len * 0.44 - snout_len * 0.92),
             pal.get("beak", pal["head"]))

    # --- legs or flippers -------------------------------------------------
    if flipper:
        flip_span = max(body_w * 0.55, foot_len * 0.85)
        flip_th = max(1.0, leg_d * 0.32)
        for side, sx in (("left", -1), ("right", 1)):
            z0 = body_front + body_len * 0.24
            # Front flipper: a broad paddle that sweeps out and back, with a
            # slight downward droop at the tip.
            x0, x1 = _mx(sx, body_w * 0.42, body_w * 0.42 + flip_span * 0.50)
            _box(m, f"{side}_flipper", f"{side}_flipper",
                 (x0, hip + body_h * 0.30 - flip_th, z0),
                 (x1, hip + body_h * 0.30 + flip_th,
                  z0 + body_len * 0.16), pal.get("flipper", pal["leg"]))
            x2, x3 = _mx(sx, body_w * 0.42 + flip_span * 0.50,
                         body_w * 0.42 + flip_span * 0.82)
            _box(m, f"{side}_flipper", f"{side}_flipper_mid",
                 (x2, hip + body_h * 0.26 - flip_th * 0.85,
                  z0 + body_len * 0.07),
                 (x3, hip + body_h * 0.26 + flip_th * 0.85,
                  z0 + body_len * 0.25), pal.get("flipper", pal["leg"]))
            x4, x5 = _mx(sx, body_w * 0.42 + flip_span * 0.82,
                         body_w * 0.42 + flip_span)
            _box(m, f"{side}_flipper", f"{side}_flipper_tip",
                 (x4, hip + body_h * 0.20 - flip_th * 0.60,
                  z0 + body_len * 0.16),
                 (x5, hip + body_h * 0.20 + flip_th * 0.60,
                  z0 + body_len * 0.33), pal.get("flipper", pal["leg"]))

            hz0 = body_back - body_len * 0.18
            hx0, hx1 = _mx(sx, body_w * 0.18, body_w * 0.18 + flip_span * 0.35)
            _box(m, f"{side}_hind_flipper", f"{side}_hind_flipper",
                 (hx0, hip + body_h * 0.10 - flip_th * 0.8, hz0),
                 (hx1, hip + body_h * 0.10 + flip_th * 0.8,
                  hz0 + body_len * 0.20), pal.get("flipper", pal["leg"]))
            hx2, hx3 = _mx(sx, body_w * 0.18 + flip_span * 0.35,
                           body_w * 0.18 + flip_span * 0.68)
            _box(m, f"{side}_hind_flipper", f"{side}_hind_flipper_tip",
                 (hx2, hip + body_h * 0.08 - flip_th * 0.6,
                  hz0 + body_len * 0.10),
                 (hx3, hip + body_h * 0.08 + flip_th * 0.6,
                  hz0 + body_len * 0.32), pal.get("flipper", pal["leg"]))
    else:
        leg_x = body_w * 0.38
        leg_z = body_len * 0.32
        for side, sx in (("left", -1), ("right", 1)):
            for ftag, sz in (("front", -1), ("back", 1)):
                cx, cz = sx * leg_x, sz * leg_z
                bone = f"{side}_{ftag}_leg"
                _box(m, bone, f"{side}_{ftag}_upper",
                     (cx - leg_d * 0.46, hip - leg_up, cz - leg_d * 0.46),
                     (cx + leg_d * 0.46, hip, cz + leg_d * 0.46), pal["leg"])
                _box(m, bone, f"{side}_{ftag}_lower",
                     (cx - leg_d * 0.32, hip - leg_up - leg_low, cz - leg_d * 0.32),
                     (cx + leg_d * 0.32, hip - leg_up, cz + leg_d * 0.32), pal["leg"])
                _foot(m, bone, f"{side}_{ftag}", cx, cz, leg_d, foot_len,
                      pal.get("foot", pal["leg"]), max(1.2, leg_d * 0.5),
                      pal.get("foot", pal["leg"]))

    # --- dorsal crest -----------------------------------------------------
    if crest_h > 0:
        n = max(4, int(body_len * 0.55))
        for i in range(n):
            t = i / max(1, n - 1)
            h = crest_h * (1 - 0.55 * t)
            cz = body_front + body_len * 0.10 + i * (body_len * 0.76 / max(1, n - 1))
            _box(m, "body", f"crest{i}",
                 (-max(0.8, body_w * 0.06), body_top - 1.0, cz),
                 (max(0.8, body_w * 0.06), body_top - 1.0 + h,
                  cz + body_len * 0.76 / max(1, n) * 0.65),
                 pal.get("crest", pal["body"]))

    # --- tail -------------------------------------------------------------
    if flipper:
        _box(m, "tail", "tail",
             (-tail_w * 0.50, hip + body_h * 0.08, body_back - body_len * 0.04),
             (tail_w * 0.50, hip + body_h * 0.08 + tail_h, body_back + tail_len),
             pal.get("tail", pal["body"]))
    else:
        segs = 5
        for i in range(segs):
            t0, t1 = i / segs, (i + 1) / segs
            w = tail_w * (0.55 - 0.35 * t0)
            h = tail_h * (0.85 - 0.45 * t0)
            z0 = body_back - 1 + tail_len * t0 * 0.95
            z1 = body_back - 1 + tail_len * t1
            _box(m, "tail", f"tail_seg{i}",
                 (-w, hip + low_h * 0.45, z0),
                 (w, hip + low_h * 0.45 + h, z1),
                 pal.get("tail", pal["body"]))

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, hip, 0), m.root)
    m.bone("head", (0, head_cy - head_h * 0.25, head_cz + head_len * 0.20), "body")
    m.bone("tail", (0, hip + low_h * 0.45, body_back), "body")
    if flipper:
        for side, sx in (("left", -1), ("right", 1)):
            m.bone(f"{side}_flipper", (sx * body_w * 0.40,
                                       hip + body_h * 0.30,
                                       body_front + body_len * 0.30), "body")
            m.bone(f"{side}_hind_flipper", (sx * body_w * 0.20,
                                            hip + body_h * 0.10,
                                            body_back - body_len * 0.12), "body")
    else:
        for side, sx in (("left", -1), ("right", 1)):
            for ftag, sz in (("front", -1), ("back", 1)):
                m.bone(f"{side}_{ftag}_leg",
                       (sx * body_w * 0.38, hip, sz * body_len * 0.32), "body")
    return m.ground()


# ---------------------------------------------------------------------------
# ratites (moa)
# ---------------------------------------------------------------------------

def build_ratite(p: dict, pal: dict) -> Model:
    """The moa: a heavy flightless bird with a long neck and small head."""
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    belly = pal.get("belly", pal["body"])
    back = pal.get("back", pal["body"])

    body_len, body_h, body_w = r["body_len"], r["body_h"], r["body_w"]
    head_len, head_h, head_w = r["head_len"], r["head_h"], r["head_w"]
    neck_len, neck_w = r["neck_len"], r["neck_w"]
    beak_len, beak_w, beak_h = r["beak_len"], r["beak_w"], r["beak_h"]
    leg_up, leg_low, foot_len, leg_d = (r["leg_upper"], r["leg_lower"],
                                        r["foot_len"], r["leg_d"])
    tail_len, tail_h, tail_w = r["tail_len"], r["tail_h"], r["tail_w"]

    hip = leg_up + leg_low
    body_top = hip + body_h
    body_front = -body_len / 2
    body_back = body_len / 2
    low_h, up_h = _split(body_h, 0.30)

    # --- torso ------------------------------------------------------------
    _box(m, "body", "belly",
         (-body_w * 0.44, hip, body_front + body_len * 0.05),
         (body_w * 0.44, hip + body_h * 0.32, body_back - body_len * 0.05),
         belly)
    _box(m, "body", "body",
         (-body_w * 0.46, hip + body_h * 0.18, body_front + body_len * 0.10),
         (body_w * 0.46, hip + body_h * 0.80, body_back - body_len * 0.10),
         pal["body"])
    _box(m, "body", "back",
         (-body_w * 0.40, hip + body_h * 0.62, body_front + body_len * 0.14),
         (body_w * 0.40, body_top, body_back - body_len * 0.14), back)
    _box(m, "body", "breast",
         (-body_w * 0.50, hip + body_h * 0.10, body_front),
         (body_w * 0.50, body_top - body_h * 0.10,
          body_front + body_len * 0.28), pal["body"])
    _box(m, "body", "shoulders",
         (-body_w * 0.46, body_top - body_h * 0.16, body_front + body_len * 0.02),
         (body_w * 0.46, body_top + body_h * 0.04,
          body_front + body_len * 0.30), pal["body"])
    _box(m, "body", "rump",
         (-body_w * 0.42, hip + body_h * 0.12, body_back - body_len * 0.28),
         (body_w * 0.42, body_top - body_h * 0.06, body_back), back)
    _box(m, "body", "back_hump",
         (-body_w * 0.34, body_top - body_h * 0.10, body_front + body_len * 0.12),
         (body_w * 0.34, body_top + body_h * 0.02, body_back - body_len * 0.12),
         back)

    # --- neck: three stepped boxes, leaning forward ----------------------
    neck_base_z = body_front + body_w * 0.16
    neck_mid = body_top + neck_len * 0.42
    _box(m, "neck", "neck_base",
         (-neck_w * 0.58, body_top - body_h * 0.08, neck_base_z - neck_w * 0.30),
         (neck_w * 0.58, neck_mid, neck_base_z + neck_w * 0.55),
         pal.get("neck", pal["body"]))
    _box(m, "neck", "neck_mid",
         (-neck_w * 0.40, neck_mid - neck_len * 0.10, neck_base_z - neck_w * 0.55),
         (neck_w * 0.40, body_top + neck_len * 0.78, neck_base_z + neck_w * 0.10),
         pal.get("neck", pal["body"]))
    _box(m, "neck", "neck_upper",
         (-neck_w * 0.28, body_top + neck_len * 0.68, neck_base_z - neck_w * 0.72),
         (neck_w * 0.28, body_top + neck_len, neck_base_z - neck_w * 0.16),
         pal.get("neck", pal["body"]))

    # --- head -------------------------------------------------------------
    head_cy = body_top + neck_len + head_h * 0.28
    head_cz = neck_base_z - neck_w * 0.48
    _box(m, "head", "skull",
         (-head_w * 0.50, head_cy - head_h * 0.50, head_cz - head_len * 0.50),
         (head_w * 0.50, head_cy + head_h * 0.50, head_cz + head_len * 0.50),
         pal["head"], details=_eye_details(head_h * 0.24, pal.get("iris", "eye")))
    _box(m, "head", "brow",
         (-head_w * 0.44, head_cy + head_h * 0.14, head_cz - head_len * 0.46),
         (head_w * 0.44, head_cy + head_h * 0.40, head_cz + head_len * 0.12),
         pal.get("brow", pal["head"]))
    _box(m, "head", "beak",
         (-beak_w * 0.50, head_cy - beak_h * 0.55, head_cz - head_len * 0.50 - beak_len),
         (beak_w * 0.50, head_cy + beak_h * 0.30, head_cz - head_len * 0.30),
         pal["beak"])
    _box(m, "head", "beak_lower",
         (-beak_w * 0.42, head_cy - beak_h * 0.65, head_cz - head_len * 0.50 - beak_len * 0.85),
         (beak_w * 0.42, head_cy - beak_h * 0.10, head_cz - head_len * 0.30),
         pal["beak"])

    # --- legs and feet ----------------------------------------------------
    leg_x = body_w * 0.34
    for side, sx in (("left", -1), ("right", 1)):
        cx = sx * leg_x
        bone = f"{side}_leg"
        _box(m, bone, f"{side}_thigh",
             (cx - leg_d * 0.56, hip - leg_up, -leg_d * 0.56),
             (cx + leg_d * 0.56, hip, leg_d * 0.56), pal["leg"])
        _box(m, bone, f"{side}_shank",
             (cx - leg_d * 0.40, hip - leg_up - leg_low, -leg_d * 0.40),
             (cx + leg_d * 0.40, hip - leg_up, leg_d * 0.40), pal["leg"])
        _foot(m, bone, side, cx, 0.0, leg_d, foot_len,
              pal.get("foot", pal["leg"]), max(1.2, leg_d * 0.45),
              pal.get("foot", pal["leg"]))

    # --- tail -------------------------------------------------------------
    tail_y = hip + low_h * 0.45
    _box(m, "tail", "tail",
         (-tail_w * 0.42, tail_y, body_back - body_len * 0.04),
         (tail_w * 0.42, tail_y + tail_h, body_back + tail_len * 0.55),
         pal.get("tail", pal["body"]))
    for i in range(3):
        fx0 = -tail_w * 0.44 + i * tail_w * 0.28
        fx1 = fx0 + tail_w * 0.24
        _box(m, "tail", f"tail_fan_{i}",
             (fx0, tail_y + tail_h * 0.2, body_back + tail_len * 0.20),
             (fx1, tail_y + tail_h * 0.62, body_back + tail_len),
             pal.get("tail", pal["body"]))

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, hip, 0), m.root)
    m.bone("neck", (0, body_top, neck_base_z), "body")
    m.bone("head", (0, head_cy - head_h * 0.25, head_cz + head_len * 0.20), "neck")
    m.bone("tail", (0, tail_y, body_back), "body")
    for side, sx in (("left", -1), ("right", 1)):
        m.bone(f"{side}_leg", (sx * leg_x, hip, 0), m.root)
    return m.ground()


# ---------------------------------------------------------------------------
# aquatic animals
# ---------------------------------------------------------------------------

def build_swimmer(p: dict, pal: dict) -> Model:
    """
    Dolphins, whales and sharks.

    The body is a chain of tapered cross-sections rather than one long box,
    so the rostrum, melon, shoulders, tail stock and flukes read as separate
    masses.  The belly is a real lower body, visible from the side, not a
    panel hidden inside the torso.
    """
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    belly = pal.get("belly", pal["body"])
    back = pal.get("back", pal["body"])
    fin = pal.get("fin", pal["body"])
    tail_col = pal.get("tail", pal["body"])

    total = r["total_len"]
    body_h, body_w = r["body_h"], r["body_w"]
    rostrum = r.get("rostrum_len", total * 0.1)
    flip_len, flip_w = r["flipper_len"], r["flipper_w"]
    dorsal_h = r.get("dorsal_h", 0)
    fluke_len, fluke_w = r["fluke_len"], r["fluke_w"]
    shark = r.get("shark", False)
    sperm = p.get("id") == "sperm_whale"

    nose_z = -total / 2
    tail_z = total / 2
    low_h, up_h = _split(body_h, 0.34)
    # Where the head ends and the trunk can safely begin.  A sperm whale's
    # rostrum is a quarter of its body, so using rostrum + a fixed offset
    # would collapse the first chest segment to zero length.
    head_end = (nose_z + total * 0.30 if sperm
                else nose_z + rostrum + total * 0.18)

    # --- body: tapered upper (back) and lower (belly) cross-sections ------
    # Each pair is a segment of the trunk.  The pale lower box is slightly
    # narrower than the dark upper box but reaches higher up the flank, so
    # the white belly is visible in profile instead of being hidden inside
    # one long rectangular torso.
    _box(m, "body", "chest_body",
         (-body_w * 0.50, body_h * 0.04, head_end - total * 0.06),
         (body_w * 0.50, body_h * 0.50, nose_z + total * 0.36), pal["body"],
         faces={"up": back})
    _box(m, "body", "chest_belly",
         (-body_w * 0.53, -body_h * 0.50, head_end - total * 0.08),
         (body_w * 0.53, body_h * 0.16, nose_z + total * 0.36), belly)
    _box(m, "body", "mid_body",
         (-body_w * 0.44, body_h * 0.02, nose_z + total * 0.31),
         (body_w * 0.44, body_h * 0.45, nose_z + total * 0.54), pal["body"],
         faces={"up": back})
    _box(m, "body", "mid_belly",
         (-body_w * 0.47, -body_h * 0.45, nose_z + total * 0.31),
         (body_w * 0.47, body_h * 0.13, nose_z + total * 0.54), belly)
    _box(m, "body", "rear_body",
         (-body_w * 0.32, 0.0, nose_z + total * 0.50),
         (body_w * 0.32, body_h * 0.36, nose_z + total * 0.66), back)
    _box(m, "body", "rear_belly",
         (-body_w * 0.35, -body_h * 0.34, nose_z + total * 0.50),
         (body_w * 0.35, body_h * 0.10, nose_z + total * 0.66), belly)
    _box(m, "body", "tail_stock",
         (-body_w * 0.16, -body_h * 0.12, nose_z + total * 0.64),
         (body_w * 0.16, body_h * 0.18, nose_z + total * 0.86), tail_col)
    _box(m, "body", "peduncle",
         (-body_w * 0.09, -body_h * 0.06, nose_z + total * 0.84),
         (body_w * 0.09, body_h * 0.09, nose_z + total * 0.98), tail_col)

    # --- head -------------------------------------------------------------
    if sperm:
        # Sperm whales are all forehead: a huge square case and a narrow
        # lower jaw.
        _box(m, "head", "skull",
             (-body_w * 0.60, -body_h * 0.34, nose_z),
             (body_w * 0.60, body_h * 0.42, nose_z + total * 0.30),
             pal["head"], details=_eye_details(body_h * 0.10, pal.get("iris", "eye")))
        _box(m, "head", "jaw",
             (-body_w * 0.46, -body_h * 0.50, nose_z + total * 0.04),
             (body_w * 0.46, -body_h * 0.24, nose_z + total * 0.28),
             pal.get("head", pal["body"]))
    else:
        _box(m, "head", "skull",
             (-body_w * 0.38, -body_h * 0.38, nose_z + rostrum * 0.55),
             (body_w * 0.38, body_h * 0.38, nose_z + rostrum + total * 0.12),
             pal["head"], details=_eye_details(body_h * 0.14, pal.get("iris", "eye")))
        _box(m, "head", "rostrum",
             (-body_w * 0.16, -body_h * 0.22, nose_z),
             (body_w * 0.16, body_h * 0.12, nose_z + rostrum * 1.05),
             pal["head"])
        _box(m, "head", "melon",
             (-body_w * 0.40, -body_h * 0.15, nose_z + rostrum + total * 0.02),
             (body_w * 0.40, body_h * 0.42, nose_z + rostrum + total * 0.22),
             pal["head"])
        _box(m, "head", "jaw",
             (-body_w * 0.32, -body_h * 0.42, nose_z + rostrum * 0.70),
             (body_w * 0.32, -body_h * 0.08, nose_z + rostrum + total * 0.18),
             pal.get("belly", pal["body"]))
    if not shark:
        _box(m, "head", "blowhole",
             (-body_w * 0.05, body_h * 0.40, nose_z + rostrum + total * 0.10),
             (body_w * 0.05, body_h * 0.48, nose_z + rostrum + total * 0.16),
             pal.get("back", pal["body"]))

    # --- pectoral flippers ------------------------------------------------
    # Flippers sweep back and droop instead of sticking straight out like a
    # pair of wings.  Sharks keep a longer, narrower pectoral fin.
    fin_span = flip_len * (0.70 if shark else 0.36)
    fin_chord = flip_w * (0.85 if shark else 1.20)
    for side, sx in (("left", -1), ("right", 1)):
        z0 = nose_z + total * 0.24
        x0, x1 = _mx(sx, body_w * 0.44, body_w * 0.44 + fin_span * 0.30)
        _box(m, f"{side}_fin", f"{side}_fin",
             (x0, -body_h * 0.34, z0),
             (x1, -body_h * 0.08, z0 + fin_chord * 0.55), fin)
        x2, x3 = _mx(sx, body_w * 0.44 + fin_span * 0.30,
                     body_w * 0.44 + fin_span * 0.66)
        _box(m, f"{side}_fin", f"{side}_fin_mid",
             (x2, -body_h * 0.42, z0 + fin_chord * 0.18),
             (x3, -body_h * 0.18, z0 + fin_chord * 0.78), fin)
        x4, x5 = _mx(sx, body_w * 0.44 + fin_span * 0.66,
                     body_w * 0.44 + fin_span)
        _box(m, f"{side}_fin", f"{side}_fin_tip",
             (x4, -body_h * 0.52, z0 + fin_chord * 0.34),
             (x5, -body_h * 0.30, z0 + fin_chord), fin)

    # --- dorsal fin -------------------------------------------------------
    if dorsal_h > 0:
        dh = dorsal_h * (1.15 if not shark else 1.0)
        _box(m, "dorsal_fin", "dorsal_fin",
             (-body_w * 0.10, body_h * 0.42, total * 0.00),
             (body_w * 0.10, body_h * 0.42 + dh * 0.60, total * 0.14), fin)
        _box(m, "dorsal_fin", "dorsal_fin_mid",
             (-body_w * 0.07, body_h * 0.42 + dh * 0.42, total * 0.06),
             (body_w * 0.07, body_h * 0.42 + dh * 0.88, total * 0.20), fin)
        _box(m, "dorsal_fin", "dorsal_fin_tip",
             (-body_w * 0.04, body_h * 0.42 + dh * 0.76, total * 0.12),
             (body_w * 0.04, body_h * 0.42 + dh, total * 0.24), fin)

    # --- tail flukes ------------------------------------------------------
    if shark:
        _box(m, "tail", "tail_upper",
             (-body_w * 0.06, body_h * 0.08, tail_z * 0.86),
             (body_w * 0.06, body_h * 0.08 + fluke_len * 1.05,
              tail_z * 0.86 + fluke_len * 0.45), tail_col)
        _box(m, "tail", "tail_lower",
             (-body_w * 0.05, -body_h * 0.16, tail_z * 0.86),
             (body_w * 0.05, -body_h * 0.16 + fluke_len * 0.38,
              tail_z * 0.86 + fluke_len * 0.25), tail_col)
    else:
        for side, sx in (("left", -1), ("right", 1)):
            tag = "l" if sx < 0 else "r"
            fx0, fx1 = _mx(sx, body_w * 0.02, body_w * 0.02 + fluke_w * 0.42)
            _box(m, "tail", f"fluke_{tag}",
                 (fx0, -body_h * 0.05, tail_z * 0.88),
                 (fx1, body_h * 0.05, tail_z * 0.88 + fluke_len * 0.62),
                 tail_col)
            fx2, fx3 = _mx(sx, body_w * 0.02 + fluke_w * 0.42,
                           body_w * 0.02 + fluke_w * 0.80)
            _box(m, "tail", f"fluke_mid_{tag}",
                 (fx2, -body_h * 0.04, tail_z * 0.92),
                 (fx3, body_h * 0.04, tail_z * 0.92 + fluke_len * 0.82),
                 tail_col)
            fx4, fx5 = _mx(sx, body_w * 0.02 + fluke_w * 0.80,
                           body_w * 0.02 + fluke_w)
            _box(m, "tail", f"fluke_tip_{tag}",
                 (fx4, -body_h * 0.03, tail_z * 0.95),
                 (fx5, body_h * 0.03, tail_z * 0.95 + fluke_len), tail_col)

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, 0, 0), m.root)
    m.bone("head", (0, 0, nose_z + rostrum * 0.9), "body")
    m.bone("tail", (0, 0, tail_z * 0.88), "body")
    for side, sx in (("left", -1), ("right", 1)):
        m.bone(f"{side}_fin", (sx * body_w * 0.44, -body_h * 0.16,
                               nose_z + total * 0.30), "body")
    # Keep the bone even on the sperm whale, which has no dorsal fin: the
    # shared swim animation targets it and a missing bone invalidates the
    # whole animation.
    m.bone("dorsal_fin", (0, body_h * 0.44, total * 0.08), "body")
    return m.ground()


# ---------------------------------------------------------------------------
# insects
# ---------------------------------------------------------------------------

def build_insect(p: dict, pal: dict) -> Model:
    """
    Weta and huhu: three body segments, six jointed legs, mandibles and
    segmented antennae.  The old builder only made two pairs of legs and
    left the femurs floating below the body.
    """
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    # Make the body read at Minecraft scale: a weta is mostly legs, but a
    # body only a few pixels wide disappears behind them.
    segs = [(l, h * 1.30, w * 1.30) for (l, h, w) in r["segments"]]
    leg_u, leg_l = r["leg_upper"] * 0.85, r["leg_lower"] * 0.85
    leg_d = r["leg_d"]
    ant_len, ant_seg = r["antenna_len"] * 0.65, r.get("antenna_segments", 3)
    spine = r.get("spines", False)
    stand = r.get("stand", 0)
    beetle = p.get("id") == "huhu"

    total_len = sum(s[0] for s in segs)
    z0 = -total_len / 2
    centres = []
    for i, (length, height, width) in enumerate(segs):
        name = ("head", "thorax", "abdomen")[i] if i < 3 else f"seg{i}"
        _box(m, name, name,
             (-width / 2, stand, z0),
             (width / 2, stand + height, z0 + length),
             pal["body"] if i == 0 else pal.get("body2", pal["body"]),
             details=_eye_details(height * 0.24, "dark") if i == 0 else None)
        centres.append((name, z0, z0 + length, width, height))
        z0 += length

    head = centres[0]
    thorax = centres[1] if len(centres) > 1 else centres[0]
    abdomen = centres[2] if len(centres) > 2 else centres[-1]

    # --- plates and tail ------------------------------------------------
    # A weta's thorax is covered by a pronotum, and its abdomen ends in two
    # cerci.  These small boxes break up the three plain segments.
    _box(m, "thorax", "thorax_plate",
         (-thorax[3] * 0.56, stand + thorax[4] * 0.62,
          thorax[1] + (thorax[2] - thorax[1]) * 0.04),
         (thorax[3] * 0.56, stand + thorax[4] * 0.96,
          thorax[1] + (thorax[2] - thorax[1]) * 0.62),
         pal.get("back", pal["body"]))
    _box(m, "head", "head_plate",
         (-head[3] * 0.48, stand + head[4] * 0.70, head[1]),
         (head[3] * 0.48, stand + head[4] * 0.96,
          head[1] + (head[2] - head[1]) * 0.62),
         pal.get("back", pal["body"]))
    alen = abdomen[2] - abdomen[1]
    _box(m, "abdomen", "abdomen_tip",
         (-abdomen[3] * 0.38, stand + abdomen[4] * 0.08,
          abdomen[2] - alen * 0.18),
         (abdomen[3] * 0.38, stand + abdomen[4] * 0.74,
          abdomen[2] + alen * 0.16), pal.get("body2", pal["body"]))
    for sx, tag in ((-1, "left"), (1, "right")):
        _box(m, "abdomen", f"{tag}_cercus",
             (sx * abdomen[3] * 0.06, stand + abdomen[4] * 0.26,
              abdomen[2] + alen * 0.10),
             (sx * abdomen[3] * 0.22, stand + abdomen[4] * 0.40,
              abdomen[2] + alen * 0.16 + leg_l * 0.38),
             pal.get("leg", pal["body"]))

    # --- mandibles --------------------------------------------------------
    for sx, tag in ((-1, "left"), (1, "right")):
        _box(m, "head", f"{tag}_mandible",
             (sx * head[3] * 0.22 - head[3] * 0.08, stand + head[4] * 0.20,
              head[1] - head[3] * 0.30),
             (sx * head[3] * 0.22 + head[3] * 0.08, stand + head[4] * 0.38,
              head[1] + head[3] * 0.10), pal.get("dark", pal["body"]))

    # --- six legs: coxa, femur, knee, tibia, tarsus ----------------------
    # One box per segment is enough: the step from femur to tibia makes the
    # bend, and the knee block hides the join.  More boxes just turned the
    # legs into a pile of cubes.
    for sx, tag in ((-1, "left"), (1, "right")):
        for i, t in enumerate((0.18, 0.50, 0.82)):
            lz = thorax[1] + (thorax[2] - thorax[1]) * t
            edge = sx * thorax[3] * 0.5
            femur_len = leg_u * (0.85 if i == 1 else 0.75)
            knee_x = edge + sx * femur_len * 0.75
            knee_y = stand * 0.58
            foot_x = knee_x + sx * leg_l * (0.60 if i == 1 else 0.70)
            z_bias = (-0.18, 0.0, 0.18)[i] * leg_l
            knee_z = lz + z_bias * 0.40
            foot_z = lz + z_bias
            bone = f"{tag}_leg{i}"
            _box(m, bone, f"{tag}_leg{i}_coxa",
                 (min(edge, edge + sx * leg_d * 0.9), stand - leg_d * 0.2,
                  lz - leg_d * 0.45),
                 (max(edge, edge + sx * leg_d * 0.9), stand + leg_d * 0.55,
                  lz + leg_d * 0.45), pal["leg"])
            _box(m, bone, f"{tag}_leg{i}_femur",
                 (min(edge, knee_x), knee_y, lz - leg_d * 0.38),
                 (max(edge, knee_x), stand + leg_d * 0.40,
                  lz + leg_d * 0.38), pal["leg"])
            _box(m, bone, f"{tag}_leg{i}_knee",
                 (knee_x - leg_d * 0.45, knee_y - leg_d * 0.35,
                  knee_z - leg_d * 0.40),
                 (knee_x + leg_d * 0.45, knee_y + leg_d * 0.35,
                  knee_z + leg_d * 0.40), pal.get("dark", pal["leg"]))
            _box(m, bone, f"{tag}_leg{i}_tibia",
                 (min(knee_x, foot_x), 0.0,
                  min(knee_z, foot_z) - leg_d * 0.32),
                 (max(knee_x, foot_x), knee_y + leg_d * 0.40,
                  max(knee_z, foot_z) + leg_d * 0.32), pal["leg"])
            _box(m, bone, f"{tag}_leg{i}_tarsus",
                 (foot_x - leg_d * 0.42, 0.0, foot_z - leg_d * 0.34),
                 (foot_x + leg_d * 0.42, leg_d * 0.40,
                  foot_z + leg_d * 0.34), pal.get("dark", pal["leg"]))
            if spine:
                sx0 = knee_x + (foot_x - knee_x) * 0.55
                sz0 = knee_z + (foot_z - knee_z) * 0.55
                _box(m, bone, f"{tag}_leg{i}_spine",
                     (sx0 - leg_d * 0.12, knee_y * 0.60,
                      sz0 - leg_d * 0.10),
                     (sx0 + leg_d * 0.12, knee_y * 0.90 + leg_d * 0.40,
                      sz0 + leg_d * 0.10), pal.get("spine", pal["leg"]))

    # --- antennae ---------------------------------------------------------
    for sx, tag in ((-1, "left"), (1, "right")):
        for s in range(ant_seg):
            t0 = s / ant_seg
            t1 = (s + 1) / ant_seg
            az0 = head[1] - ant_len * t1
            az1 = head[1] - ant_len * t0
            w = max(0.4, head[3] * (0.10 - 0.015 * s))
            x = sx * head[3] * (0.26 + 0.20 * t0)
            _box(m, f"{tag}_antenna", f"{tag}_antenna{s}",
                 (x - w, stand + head[4] * 0.68, az0),
                 (x + w, stand + head[4] * 0.68 + w * 1.2, az1),
                 pal["antenna"])

    # --- beetle elytra ----------------------------------------------------
    if beetle:
        for sx, tag in ((-1, "left"), (1, "right")):
            _box(m, "abdomen", f"{tag}_elytron",
                 (sx * abdomen[3] * 0.02, stand + abdomen[4] * 0.70,
                  abdomen[1] + abdomen[3] * 0.10),
                 (sx * abdomen[3] * 0.48, stand + abdomen[4] * 0.95,
                  abdomen[2] - abdomen[3] * 0.05),
                 pal.get("back", pal["body"]))

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, stand, 0), m.root)
    for name, bz0, bz1, _w, _h in centres:
        m.bone(name, (0, stand, (bz0 + bz1) / 2), "body")
    for sx, tag in ((-1, "left"), (1, "right")):
        for i in range(3):
            lz = thorax[1] + (thorax[2] - thorax[1]) * (0.18, 0.50, 0.82)[i]
            m.bone(f"{tag}_leg{i}", (sx * thorax[3] * 0.5, stand, lz), "body")
        m.bone(f"{tag}_antenna", (sx * head[3] * 0.26,
                                  stand + head[4] * 0.70, head[1]), "head")
    return m.ground()


# ---------------------------------------------------------------------------
# snail
# ---------------------------------------------------------------------------

def build_snail(p: dict, pal: dict) -> Model:
    """Giant land snail: a stepped spiral shell, a broad foot and eye stalks."""
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    shell_w, shell_h, shell_d = r["shell_w"], r["shell_h"], r["shell_d"]
    foot_len, foot_h, foot_w = r["foot_len"], r["foot_h"], r["foot_w"]
    head_len = r.get("head_len", foot_w * 0.5)
    tent_len, tent_d = r["tentacle_len"], r["tentacle_d"]

    # --- foot: three tapered boxes ---------------------------------------
    _box(m, "body", "foot",
         (-foot_w * 0.50, 0, -foot_len * 0.50),
         (foot_w * 0.50, foot_h, foot_len * 0.50), pal["body"])
    _box(m, "body", "foot_front",
         (-foot_w * 0.40, 0, -foot_len * 0.58),
         (foot_w * 0.40, foot_h * 0.72, -foot_len * 0.40), pal["body"])
    _box(m, "body", "foot_back",
         (-foot_w * 0.42, 0, foot_len * 0.36),
         (foot_w * 0.42, foot_h * 0.75, foot_len * 0.58), pal["body"])

    # --- shell: a flat spiral disc ---------------------------------------
    # Powelliphanta is a flat-coiled snail: the shell is a low disc with a
    # painted square spiral on its top face.  Keeping the geometry flat
    # lets the spiral read from above instead of becoming a stepped pile.
    sh = pal["shell"]
    sh2 = pal.get("shell2", sh)
    sh3 = pal.get("shell_top", sh)
    dark = pal.get("dark", sh2)

    _box(m, "shell", "shell_base",
         (-shell_w * 0.50, foot_h, -shell_d * 0.50),
         (shell_w * 0.50, foot_h + shell_h * 0.45, shell_d * 0.50), sh2)
    _box(m, "shell", "shell_spire",
         (-shell_w * 0.10, foot_h + shell_h * 0.45, -shell_d * 0.10),
         (shell_w * 0.10, foot_h + shell_h * 0.65, shell_d * 0.10), sh3)
    # opening on the front-right, framed by a pale lip
    _box(m, "shell", "shell_lip",
         (shell_w * 0.08, foot_h, -shell_d * 0.54),
         (shell_w * 0.46, foot_h + shell_h * 0.45, -shell_d * 0.40), sh3)
    _box(m, "shell", "shell_aperture",
         (shell_w * 0.14, foot_h + shell_h * 0.04, -shell_d * 0.56),
         (shell_w * 0.40, foot_h + shell_h * 0.40, -shell_d * 0.52), dark)

    # --- head and eye stalks ---------------------------------------------
    hz = -foot_len * 0.50
    _box(m, "head", "head",
         (-head_len * 0.50, foot_h * 0.25, hz - head_len),
         (head_len * 0.50, foot_h * 0.25 + head_len * 1.15, hz),
         pal["body"], details=_eye_details(head_len * 0.20, "dark"))
    for sx, tag in ((-1, "left"), (1, "right")):
        x = sx * head_len * 0.32
        _box(m, f"{tag}_tentacle", f"{tag}_tentacle_base",
             (x - tent_d * 0.50, foot_h * 0.80, hz - head_len - tent_len * 0.55),
             (x + tent_d * 0.50, foot_h * 0.80 + tent_d, hz - head_len * 0.30),
             pal["body"])
        _box(m, f"{tag}_tentacle", f"{tag}_tentacle_tip",
             (x - tent_d * 0.36, foot_h * 1.00, hz - head_len - tent_len),
             (x + tent_d * 0.36, foot_h * 1.00 + tent_d * 0.82,
              hz - head_len - tent_len * 0.48), pal["body"])

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, 0, 0), m.root)
    m.bone("shell", (0, foot_h, 0), "body")
    m.bone("head", (0, foot_h * 0.6, hz), "body")
    for sx, tag in ((-1, "left"), (1, "right")):
        m.bone(f"{tag}_tentacle", (sx * head_len * 0.32, foot_h,
                                   hz - head_len), "head")
    return m.ground()


# ---------------------------------------------------------------------------
# penguins
# ---------------------------------------------------------------------------

def build_penguin(p: dict, pal: dict) -> Model:
    """
    Penguins: an upright torso, a white belly panel, a head with a real bill,
    eyes on the sides, tapered flippers, webbed feet and a short tail fan.
    """
    m = Model(p["name"])
    m.root = p["name"]
    r = p
    belly = pal.get("belly", pal["body"])
    back = pal.get("back", pal["body"])

    body_h, body_w, body_d = r["body_h"], r["body_w"], r["body_len"]
    head_len, head_h, head_w = r["head_len"], r["head_h"], r["head_w"]
    beak_len, beak_w, beak_h = r["beak_len"], r["beak_w"], r["beak_h"]
    foot_len, foot_w, foot_h = r["foot_len"], r["foot_w"], r["foot_h"]
    flip_len, flip_t = r["flipper_len"], r["flipper_w"]
    tail_len, tail_h, tail_w = r["tail_len"], r["tail_h"], r["tail_w"]
    crest_h = r.get("crest", 0)

    body_front = -body_d / 2
    body_back = body_d / 2
    body_top = foot_h + body_h

    # --- torso ------------------------------------------------------------
    _box(m, "body", "torso",
         (-body_w * 0.44, foot_h + body_h * 0.18, body_front + body_d * 0.05),
         (body_w * 0.44, foot_h + body_h * 0.82, body_back - body_d * 0.05),
         pal["body"], faces={"up": back})
    _box(m, "body", "belly",
         (-body_w * 0.42, foot_h + body_h * 0.04, body_front - body_d * 0.06),
         (body_w * 0.42, foot_h + body_h * 0.70, body_front + body_d * 0.42),
         belly)
    _box(m, "body", "chest",
         (-body_w * 0.50, foot_h + body_h * 0.12, body_front),
         (body_w * 0.50, foot_h + body_h * 0.84, body_front + body_d * 0.30),
         pal["body"])
    _box(m, "body", "rump",
         (-body_w * 0.42, foot_h + body_h * 0.12, body_back - body_d * 0.30),
         (body_w * 0.42, foot_h + body_h * 0.76, body_back), back)
    _box(m, "body", "back",
         (-body_w * 0.40, foot_h + body_h * 0.64, body_front + body_d * 0.08),
         (body_w * 0.40, body_top, body_back - body_d * 0.08), back)
    _box(m, "body", "shoulders",
         (-body_w * 0.47, body_top - body_h * 0.14, body_front - body_d * 0.04),
         (body_w * 0.47, body_top + body_h * 0.04, body_back), pal["body"])
    _box(m, "body", "neck",
         (-head_w * 0.36, body_top - body_h * 0.10, body_front + body_d * 0.02),
         (head_w * 0.36, body_top + head_h * 0.18, body_front + body_d * 0.34),
         pal["head"])

    # --- head -------------------------------------------------------------
    head_cy = body_top + head_h * 0.34
    head_cz = body_front - head_len * 0.30
    _box(m, "head", "skull",
         (-head_w * 0.50, head_cy - head_h * 0.50, head_cz - head_len * 0.50),
         (head_w * 0.50, head_cy + head_h * 0.50, head_cz + head_len * 0.50),
         pal["head"], details=_eye_details(head_h * 0.24, pal.get("iris", "eye")))
    _box(m, "head", "brow",
         (-head_w * 0.44, head_cy + head_h * 0.12, head_cz - head_len * 0.44),
         (head_w * 0.44, head_cy + head_h * 0.40, head_cz + head_len * 0.10),
         pal.get("brow", pal["head"]))
    if crest_h > 0:
        _box(m, "head", "crest",
             (-head_w * 0.22, head_cy + head_h * 0.34, head_cz - head_len * 0.28),
             (head_w * 0.22, head_cy + head_h * 0.34 + crest_h, head_cz + head_len * 0.26),
             pal.get("crest", pal["head"]))
        _box(m, "head", "crest_tip",
             (-head_w * 0.16, head_cy + head_h * 0.32, head_cz + head_len * 0.08),
             (head_w * 0.16, head_cy + head_h * 0.32 + crest_h * 0.72, head_cz + head_len * 0.40),
             pal.get("crest", pal["head"]))
    _box(m, "head", "beak",
         (-beak_w * 0.50, head_cy - beak_h * 0.55, head_cz - head_len * 0.50 - beak_len),
         (beak_w * 0.50, head_cy + beak_h * 0.36, head_cz - head_len * 0.22),
         pal["beak"])
    _box(m, "head", "beak_lower",
         (-beak_w * 0.42, head_cy - beak_h * 0.62, head_cz - head_len * 0.50 - beak_len * 0.88),
         (beak_w * 0.42, head_cy - beak_h * 0.12, head_cz - head_len * 0.22),
         pal["beak"])

    # --- flippers ---------------------------------------------------------
    flip_top = body_top - body_h * 0.08
    for side, sx in (("left", -1), ("right", 1)):
        x0, x1 = _mx(sx, body_w * 0.50, body_w * 0.50 + flip_t * 0.80)
        _box(m, f"{side}_flipper", f"{side}_flipper",
             (x0, flip_top - flip_len * 0.58, body_front + body_d * 0.14),
             (x1, flip_top, body_front + body_d * 0.30),
             pal.get("flipper", pal["body"]))
        x2, x3 = _mx(sx, body_w * 0.50 + flip_t * 0.70,
                     body_w * 0.50 + flip_t * 1.10)
        _box(m, f"{side}_flipper", f"{side}_flipper_mid",
             (x2, flip_top - flip_len * 0.84, body_front + body_d * 0.20),
             (x3, flip_top - flip_len * 0.26, body_front + body_d * 0.38),
             pal.get("flipper", pal["body"]))
        x4, x5 = _mx(sx, body_w * 0.50 + flip_t * 1.02,
                     body_w * 0.50 + flip_t * 1.34)
        _box(m, f"{side}_flipper", f"{side}_flipper_tip",
             (x4, flip_top - flip_len, body_front + body_d * 0.27),
             (x5, flip_top - flip_len * 0.48, body_front + body_d * 0.44),
             pal.get("flipper", pal["body"]))

    # --- feet and tail ----------------------------------------------------
    foot_x = body_w * 0.24
    for side, sx in (("left", -1), ("right", 1)):
        cx = sx * foot_x
        _foot(m, f"{side}_foot", side, cx, body_front + foot_len * 0.12,
              max(foot_w * 0.55, 1.5), foot_len, pal.get("foot", pal["leg"]),
              foot_h, pal.get("foot", pal["leg"]))

    tail_y = foot_h + body_h * 0.08
    _box(m, "tail", "tail",
         (-tail_w * 0.42, tail_y, body_back - body_d * 0.04),
         (tail_w * 0.42, tail_y + tail_h, body_back + tail_len * 0.55),
         pal.get("tail", pal["body"]))
    for i in range(3):
        fx0 = -tail_w * 0.44 + i * tail_w * 0.28
        fx1 = fx0 + tail_w * 0.24
        _box(m, "tail", f"tail_fan_{i}",
             (fx0, tail_y + tail_h * 0.2, body_back + tail_len * 0.20),
             (fx1, tail_y + tail_h * 0.62, body_back + tail_len),
             pal.get("tail", pal["body"]))

    # --- bones ------------------------------------------------------------
    m.bone(m.root, (0, 0, 0))
    m.bone("body", (0, foot_h, 0), m.root)
    m.bone("head", (0, head_cy - head_h * 0.25, head_cz + head_len * 0.20), "body")
    m.bone("tail", (0, tail_y, body_back), "body")
    for side, sx in (("left", -1), ("right", 1)):
        m.bone(f"{side}_flipper", (sx * body_w * 0.50, flip_top,
                                   body_front + body_d * 0.22), "body")
        m.bone(f"{side}_foot", (sx * foot_x, foot_h,
                                body_front + foot_len * 0.12), m.root)
    return m.ground()


BUILDERS = {
    "bird": build_bird,
    "quadruped": build_quadruped,
    "swimmer": build_swimmer,
    "insect": build_insect,
    "snail": build_snail,
    "ratite": build_ratite,
    "penguin": build_penguin,
}
