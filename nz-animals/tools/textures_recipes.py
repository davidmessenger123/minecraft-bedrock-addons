"""
Per-species texture recipes.

Each entry lists the markings painted onto the model's cubes, in the order
they are drawn. Marking kinds are implemented in tools/nzlib.py:

  eye     {u, v, size, iris}       sclera + coloured iris + pupil + highlight
  oval    {u, v, w, h, color, soft} a patch (throat, eye patch, saddle)
  rect    {u, v, u2, v2, color}    a rectangular patch
  band    {v, v2, color}           a horizontal band across the face
  vband   {u, u2, color}           a vertical band
  spots   {count, r, color, seed}   scattered spots
  speckle {count, color, seed}      fine mottling
  scales  {step, color}            overlapping arcs (reptile / fish skin)
  streak  {density, color, seed}    fine directional strokes (fur / feathers)
  spiral  {legs, color}             a square spiral line (flat snail shell)

`cube` names a cube in the model; it matches exactly, or as a suffix, so
"wing_upper" hits both "left_wing_upper" and "right_wing_upper".

The colour of a marking may be a palette key (resolved against the species
palette) or an RGB tuple. Palette keys used here:
  throat, belly, back, eye, iris, wattle, band, pale, dark, cream, rump
"""

# Reusable marking groups.
def eye(u=0.5, v=0.35, size=0.3, iris="eye"):
    return ("skull", "sides", "eye", dict(u=u, v=v, size=size, iris=iris))


RECIPES = {
    # ---------------- birds ----------------
    "kiwi": [
        ("body", "sides", "streak", dict(density=0.5, color="pale", seed="k1")),
        ("belly", "north", "streak", dict(density=0.45, color="pale", seed="k2")),
        ("body", "up", "streak", dict(density=0.4, color="pale", seed="k3")),
    ],
    "kakapo": [
        ("skull", "sides", "oval", dict(u=0.5, v=0.62, w=0.7, h=0.34, color="pale")),
        ("body", "sides", "speckle", dict(count=22, color="pale", seed="kp1")),
        ("body", "up", "speckle", dict(count=26, color="pale", seed="kp2")),
        ("wing_upper", "up", "speckle", dict(count=12, color="pale", seed="kp3")),
    ],
    "kea": [
        # a bright yellow iris, as on the real bird
        ("skull", "up", "oval", dict(u=0.5, v=0.4, w=0.8, h=0.7, color="pale")),
        # the upper mandible is black, the lower one orange
        ("beak", "north", "rect", dict(u=0.0, v=0.0, u2=1.0, v2=0.5, color="mandible")),
        ("beak", "up", "rect", dict(u=0.0, v=0.0, u2=1.0, v2=1.0, color="mandible")),
        # crimson undertail coverts and a red underwing
        ("rump", "down", "rect", dict(u=0.0, v=0.0, u2=1.0, v2=1.0, color="wattle")),
        ("tail", "down", "rect", dict(u=0.0, v=0.0, u2=1.0, v2=0.85, color="wattle")),
        ("wing_lower", "outer", "band", dict(v=0.15, v2=0.85, color="wattle")),
        ("body", "up", "streak", dict(density=0.35, color="pale", seed="ke1")),
    ],
    "kaka": [
        ("wing_lower", "outer", "band", dict(v=0.15, v2=0.85, color="wattle")),
        ("body", "up", "streak", dict(density=0.35, color="pale", seed="ka1")),
    ],
    "tui": [
        ("skull", "sides", "oval", dict(u=0.5, v=0.9, w=0.8, h=0.45, color="throat")),
        ("wing_lower", "outer", "band", dict(v=0.55, v2=0.95, color="throat")),
        ("body", "up", "speckle", dict(count=18, color="band", seed="tu1")),
    ],
    "hihi": [
        ("wing_lower", "outer", "band", dict(v=0.45, v2=0.95, color="throat")),
        ("tail", "sides", "band", dict(v=0.6, v2=1.0, color="throat")),
    ],
    "kereru": [
        ("skull", "up", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.8, color="throat")),
        ("body", "sides", "oval", dict(u=0.5, v=0.55, w=0.6, h=0.5, color="throat")),
        ("body", "up", "speckle", dict(count=12, color="pale", seed="ke2")),
    ],
    "pukeko": [
        ("skull", "sides", "oval", dict(u=0.5, v=0.92, w=0.62, h=0.4, color="wattle")),
        ("body", "up", "speckle", dict(count=14, color="band", seed="pu1")),
    ],
    "morepork": [
        ("skull", "sides", "oval", dict(u=0.5, v=0.5, w=0.86, h=0.8, color="pale")),
        ("body", "sides", "speckle", dict(count=20, color="dark", seed="mo1")),
        ("body", "up", "speckle", dict(count=24, color="dark", seed="mo2")),
    ],
    "kotare": [
        ("skull", "sides", "oval", dict(u=0.5, v=0.92, w=0.7, h=0.4, color="throat")),
        ("body", "sides", "oval", dict(u=0.5, v=0.55, w=0.8, h=0.55, color="belly")),
    ],
    "tieke": [
        # the chestnut throat patch below the bill
        ("skull", "sides", "oval", dict(u=0.5, v=0.92, w=0.7, h=0.4, color="wattle")),
        # the chestnut "saddle" over the shoulders
        ("wing_upper", "outer", "band", dict(v=0.1, v2=0.6, color="wattle")),
        ("body", "up", "streak", dict(density=0.3, color="pale", seed="ti1")),
    ],
    "whio": [
        ("body", "sides", "oval", dict(u=0.5, v=0.5, w=0.75, h=0.6, color="belly")),
        ("body", "up", "streak", dict(density=0.3, color="pale", seed="wh1")),
    ],
    "huia": [
        ("tail", "sides", "band", dict(v=0.45, v2=0.95, color="throat")),
        # the white thigh tufts
        ("thigh", "outer", "oval", dict(u=0.5, v=0.35, w=0.85, h=0.6, color="throat")),
        ("body", "up", "streak", dict(density=0.3, color="pale", seed="hu1")),
    ],
    "haasts_eagle": [
        ("skull", "up", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.8, color="pale")),
        ("body", "sides", "streak", dict(density=0.5, color="pale", seed="he1")),
        ("body", "up", "streak", dict(density=0.35, color="pale", seed="he2")),
    ],

    # ---------------- penguins ----------------
    "little_penguin": [
        ("skull", "up", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.8, color="pale")),
        ("belly", "north", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.8, color="throat")),
    ],
    "yellow_eyed_penguin": [
        ("skull", "up", "oval", dict(u=0.5, v=0.45, w=0.85, h=0.7, color="pale")),
        ("belly", "north", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.85, color="throat")),
    ],
    "rockhopper_penguin": [
        # a red iris, as on the real bird
        # yellow feathering around the eye, dark crown between the crest plumes
        ("skull", "sides", "oval", dict(u=0.45, v=0.62, w=0.75, h=0.50, color="crest")),
        ("belly", "north", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.85, color="throat")),
    ],

    # ---------------- land vertebrates & invertebrates ----------------
    "tuatara": [
        ("body", "up", "speckle", dict(count=26, color="pale", seed="tu1")),
        ("body", "sides", "speckle", dict(count=16, color="pale", seed="tu2")),
        ("skull", "up", "speckle", dict(count=10, color="pale", seed="tu3")),
    ],
    "powelliphanta": [
        # The flat top carries the square spiral; the sides get growth bands
        # and mottling so the shell does not read as a plain box.
        ("shell_base", "up", "rect", dict(u=0.0, v=0.0, u2=1.0, v2=1.0, color="dark")),
        ("shell_base", "up", "spiral", dict(legs=7, color="shell_top")),
        ("shell_base", "sides", "band", dict(v=0.10, v2=0.32, color="band")),
        ("shell_base", "sides", "speckle", dict(count=10, color="dark", seed="pws")),
        ("shell_spire", "up", "oval", dict(u=0.5, v=0.5, w=0.9, h=0.9, color="shell_top")),
        ("shell_lip", "sides", "band", dict(v=0.20, v2=0.70, color="pale")),
    ],
    "weta": [
        ("abdomen", "up", "band", dict(v=0.3, v2=0.45, color="dark")),
        ("abdomen", "up", "band", dict(v=0.6, v2=0.72, color="dark")),
        ("thorax", "up", "band", dict(v=0.35, v2=0.5, color="dark")),
    ],
    "huhu": [
        ("abdomen", "up", "speckle", dict(count=14, color="dark", seed="hh1")),
        ("abdomen", "up", "vband", dict(u=0.45, u2=0.55, color="band")),
    ],

    # ---------------- marine ----------------
    "nz_sea_lion": [
        ("body", "up", "speckle", dict(count=24, color="pale", seed="sl1")),
        ("body", "sides", "speckle", dict(count=16, color="pale", seed="sl2")),
        ("skull", "sides", "speckle", dict(count=8, color="pale", seed="sl3")),
    ],
    "nz_fur_seal": [
        ("body", "up", "speckle", dict(count=26, color="pale", seed="fs1")),
        ("body", "sides", "speckle", dict(count=14, color="pale", seed="fs2")),
        ("skull", "sides", "speckle", dict(count=8, color="pale", seed="fs3")),
    ],
    "hectors_dolphin": [
        ("chest_body", "sides", "vband", dict(u=0.08, u2=0.2, color="dark")),
        ("body", "up", "speckle", dict(count=12, color="pale", seed="hd1")),
    ],
    "dusky_dolphin": [
        ("chest_body", "sides", "vband", dict(u=0.06, u2=0.18, color="dark")),
        ("body", "up", "speckle", dict(count=10, color="pale", seed="dd1")),
    ],
    "orca": [
        # White post-ocular patch on both cheeks, the diagnostic orca mark.
        ("skull", "sides", "oval", dict(u=0.68, v=0.40, w=0.42, h=0.26,
                                       color="throat", soft=False)),
        ("skull", "up", "oval", dict(u=0.5, v=0.5, w=0.95, h=0.9, color="throat")),
        # Grey saddle behind the dorsal fin, on the mid-trunk only.
        ("mid_body", "up", "oval", dict(u=0.58, v=0.5, w=0.30, h=0.32, color="pale")),
    ],
    "sperm_whale": [
        ("skull", "up", "oval", dict(u=0.5, v=0.5, w=0.8, h=0.8, color="pale")),
        ("body", "up", "speckle", dict(count=16, color="pale", seed="sw1")),
    ],
    "blue_shark": [
        ("body", "up", "scales", dict(step=4, color="pale")),
        # Three gill slits just behind the head on each flank.
        ("chest_body", "sides", "vband", dict(u=0.03, u2=0.05, color="dark")),
        ("chest_body", "sides", "vband", dict(u=0.07, u2=0.09, color="dark")),
        ("chest_body", "sides", "vband", dict(u=0.11, u2=0.13, color="dark")),
    ],

    # ---------------- extinct ----------------
    "moa": [
        ("body", "up", "streak", dict(density=0.55, color="pale", seed="mo1")),
        ("body", "sides", "streak", dict(density=0.4, color="pale", seed="mo2")),
        ("neck_upper", "up", "streak", dict(density=0.4, color="pale", seed="mo3")),
    ],
}


# ---------------------------------------------------------------------------
# Extra palette keys used by the recipes.
# A float value is a shade factor applied to the cube's base colour, so the
# same key can be a light/dark variant of whatever that animal happens to be.
# ---------------------------------------------------------------------------

PALETTE_EXTRAS = {
    "tui": dict(throat=(238, 238, 242), band=(74, 86, 118), eye=(26, 22, 20)),
    "hihi": dict(throat=(240, 240, 240), eye=(24, 20, 18)),
    "whio": dict(throat=(236, 238, 240), eye=(30, 24, 20)),
    "kereru": dict(throat=(122, 168, 138), eye=(30, 24, 20)),
    "kotare": dict(throat=(238, 240, 238), eye=(26, 22, 20)),
    "huia": dict(throat=(238, 238, 240), eye=(26, 22, 20)),
    "morepork": dict(pale=(168, 156, 134), dark=0.66, eye=(36, 26, 18)),
    "kakapo": dict(pale=(168, 190, 128), eye=(28, 22, 18)),
    "kea": dict(pale=(150, 134, 108), wattle=(196, 74, 52), eye=(30, 24, 20),
                iris=(232, 196, 40), mandible=(32, 28, 26)),
    "kaka": dict(pale=(134, 112, 86), wattle=(168, 62, 46), eye=(30, 24, 20)),
    "pukeko": dict(wattle=(198, 64, 44), band=(62, 76, 112), eye=(30, 24, 20)),
    "tieke": dict(wattle=(176, 96, 44), pale=(88, 88, 94), eye=(28, 24, 22)),
    "kiwi": dict(pale=(146, 116, 84), dark=(52, 38, 24), eye=(22, 18, 14)),
    "haasts_eagle": dict(pale=(188, 156, 96), eye=(34, 26, 16)),
    "yellow_eyed_penguin": dict(throat=(238, 238, 232), pale=(226, 220, 168),
                                wattle=(226, 198, 84), iris=(226, 198, 84)),
    "rockhopper_penguin": dict(throat=(238, 238, 234), pale=(222, 200, 140),
                                wattle=(196, 74, 44), iris=(196, 74, 44)),
    "little_penguin": dict(throat=(240, 240, 238), pale=(176, 190, 206)),
    "tuatara": dict(pale=(158, 164, 126), eye=(28, 24, 18)),
    "powelliphanta": dict(band=(92, 60, 32), dark=(78, 50, 26)),
    "weta": dict(dark=(46, 34, 22)),
    "huhu": dict(band=(122, 84, 52), dark=(26, 20, 14)),
    "orca": dict(throat=(238, 238, 238), pale=(122, 126, 132)),
    "sperm_whale": dict(pale=(104, 104, 110)),
    "blue_shark": dict(pale=(226, 232, 238)),
    "hectors_dolphin": dict(dark=(78, 84, 92), pale=(196, 200, 206)),
    "dusky_dolphin": dict(dark=(66, 72, 80), pale=(180, 188, 196)),
    "nz_sea_lion": dict(pale=(160, 148, 134)),
    "nz_fur_seal": dict(pale=(126, 102, 78)),
    "moa": dict(pale=(166, 146, 112)),
}


def species_palette(spec) -> dict:
    """
    The full colour palette for one species: the roster colours plus the
    recipe extras plus the fallbacks the marking recipes rely on.

    generate.py and audit_textures.py both use this, so a marking colour can
    never be silently missing from the palette that paints the texture.
    """
    palette = dict(spec["pal"])
    palette.update(PALETTE_EXTRAS.get(spec["id"], {}))
    palette.setdefault("pale", 1.35)
    palette.setdefault("dark", 0.6)
    palette.setdefault("throat", palette.get("belly", palette["body"]))
    palette.setdefault("wattle", palette.get("beak", palette["body"]))
    palette.setdefault("band", palette.get("back", palette["body"]))
    palette.setdefault("eye", (28, 22, 18))
    return palette
