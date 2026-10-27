"""Block-texture recipes: every name in textures/blocks resolves to a canvas."""
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from candy import (Canvas, Ramp, clamp, get_ramp, make_ramp, mix, luma,
                   at_luma, hex_rgb, DYE_COLORS, DYE_ALIASES)  # noqa: E402
import patterns as P  # noqa: E402
import restyle  # noqa: E402

DYES = set(DYE_COLORS)


def dye_of(name):
    for d in sorted(DYES, key=len, reverse=True):
        if name.endswith("_" + d):
            return d
    return None


def dye_ramp(name):
    d = dye_of(name)
    key = DYE_COLORS[DYE_ALIASES.get(d, d)][0]
    return get_ramp(key)


def dye_col(name):
    d = dye_of(name)
    return hex_rgb(DYE_COLORS[DYE_ALIASES.get(d, d)][1])


def G(size=32):
    return Canvas(size)


# wood key -> (planks ramp, bark ramp, core ramp, leaf ramp, leaf style)
WOODS = {
    "oak":       ("wafer", "bark_wafer", "caramel", "mint", "round"),
    "spruce":    ("caramel", "bark_chocolate", "peanut_brittle", "mint", "round"),
    "birch":     ("meringue", "bark_white", "vanilla", "sour_apple", "round"),
    "jungle":    ("orange_sherbet", "bark_red", "caramel", "pistachio", "round"),
    "acacia":    ("orange_sherbet", "bark_red", "caramel", "mint", "round"),
    "dark_oak":  ("milk_chocolate", "bark_chocolate", "fudge", "mint", "round"),
    "big_oak":   ("milk_chocolate", "bark_chocolate", "fudge", "mint", "round"),
    "mangrove":  ("red_velvet", "bark_red", "red_velvet", "mint", "round"),
    "cherry":    ("cotton_candy", "bark_cherry", "cotton_candy", "cotton_candy", "blossom"),
    "pale_oak":  ("marshmallow", "bark_white", "meringue", "mint", "round"),
    "poplar":    ("lemon_meringue", "bark_green", "sugar", "lemon_drop", "poplar"),
    "bamboo":    ("pistachio", "bark_green", "sour_apple", "sour_apple", "bamboo"),
    "crimson":   ("raspberry", "bark_red", "strawberry", "mint", "round"),
    "warped":    ("blue_raspberry", "bark_blue", "sea_glass", "mint", "round"),
}


def wood_of(name):
    for w in sorted(WOODS, key=len, reverse=True):
        if re.search(r"(^|_)" + w + r"($|_)", name):
            return w
    if "big_oak" in name:
        return "big_oak"
    return None


def frames_canvas(frames, fn):
    """Render fn(frame, canvas) into a vertical flipbook strip."""
    out = Canvas(32, 32 * frames)
    for f in range(frames):
        c = Canvas(32)
        fn(f, c)
        for y in range(32):
            for x in range(32):
                out.set(x, f * 32 + y, c.get(x, y), c.get(x, y)[3])
    return out


# ---------------------------------------------------------------- recipes

def ores(name):
    gem = None
    for g in ("coal", "iron", "copper", "gold", "redstone", "lapis",
              "diamond", "emerald", "quartz"):
        if ("_" + g + "_ore") in ("_" + name):
            gem = g
            break
    if not gem:
        return None
    deep = name.startswith("deepslate_") or name.startswith("cobbled_deepslate")
    body = "obsidian_jelly" if deep else "rock_candy_pink"
    gem_ramp = {
        "coal": "coal_candy", "iron": "raw_candy", "copper": "copper_candy",
        "gold": "gold_candy", "redstone": "redstone_candy",
        "lapis": "lapis_candy", "diamond": "diamond_candy",
        "emerald": "emerald_candy", "quartz": "quartz_candy"}[gem]
    return _ore_canvas(body, gem_ramp, name, deep)


def _ore_canvas(body, gem, name, deep):
    c = Canvas(32)
    P.ore(c, abs(hash(name)) % 9999, get_ramp(body), get_ramp(gem),
          gems=3 if deep else 4, deep=deep)
    return c


def leaf_canvas(name, e):
    wood = wood_of(name)
    flowers = None
    ramp = "mint"
    colored = False
    if "cherry" in name:
        ramp, colored = "cotton_candy", True
        flowers = [(255, 210, 228), (255, 240, 248), (244, 128, 170)]
    elif "azalea" in name:
        ramp, colored = "pistachio", True
        flowers = [(246, 140, 190), (255, 200, 225)] if "flower" in name else None
    elif "orange_poplar" in name:
        ramp, colored = "orange_sherbet", True
    elif "red_poplar" in name:
        ramp, colored = "cherry", True
    elif "yellow_poplar" in name:
        ramp, colored = "lemon_drop", True
    elif "pale_oak" in name:
        ramp = "mint"
    elif wood:
        ramp = WOODS[wood][3]
    c = Canvas(32)
    P.leaves(c, abs(hash(name)) % 9999, get_ramp(ramp),
             opaque=("opaque" in name), colored=colored, flowers=flowers,
             density=.90)
    return c


def planks_canvas(name, e, boards=5):
    wood = wood_of(name) or "oak"
    pr, bark, core, leaf, style = WOODS[wood]
    c = Canvas(32)
    P.planks(c, abs(hash(name)) % 9999, get_ramp(pr), get_ramp(core),
             boards=boards, grain=.38 if wood != "bamboo" else .22,
             knot=wood not in ("bamboo", "birch"))
    return c


def log_side_canvas(name, e, stripped=False):
    wood = wood_of(name) or "oak"
    pr, bark, core, leaf, style = WOODS[wood]
    c = Canvas(32)
    if stripped:
        P.log_side(c, abs(hash(name)) % 9999, get_ramp(core), get_ramp(pr),
                   get_ramp(core), bark=False)
    elif wood in ("cherry", "crimson", "warped", "mangrove"):
        P.log_side(c, abs(hash(name)) % 9999, get_ramp(bark), get_ramp(core),
                   get_ramp(pr), bark=True)
    elif style == "bamboo":
        P.log_side(c, abs(hash(name)) % 9999, get_ramp("sour_apple"),
                   get_ramp("pistachio"), get_ramp("mint"), bark=False)
    else:
        P.log_side(c, abs(hash(name)) % 9999, get_ramp(bark), get_ramp(core),
                   get_ramp(pr), bark=True)
    return c


def log_end_canvas(name, e, stripped=False):
    wood = wood_of(name) or "oak"
    pr, bark, core, leaf, style = WOODS[wood]
    c = Canvas(32)
    if stripped:
        P.log_end(c, abs(hash(name)) % 9999, get_ramp(core), get_ramp(pr),
                  get_ramp(core))
    else:
        P.log_end(c, abs(hash(name)) % 9999, get_ramp(core), get_ramp(bark),
                  get_ramp(pr))
    return c


def block_canvas(name, e):
    """Return a Canvas for one block texture."""
    seed = abs(hash(name)) % 99999

    # ---------------------------------------------------------- plants
    if (name.startswith("leaves_") or name.endswith("_leaves")
            or "leaves" in name):
        return leaf_canvas(name, e)

    # ---------------------------------------------------------- wood
    if name.endswith("planks") or name.endswith("bamboo_mosaic"):
        return planks_canvas(name, e)
    if name.startswith("stripped_") and "top" not in name and (
            "log" in name or "stem" in name):
        return log_side_canvas(name, e, stripped=True)
    if name.startswith("stripped_") and "top" in name:
        return log_end_canvas(name, e, stripped=True)
    if name.endswith("_log") or name.endswith("_log_side") or \
            name.endswith("_stem_side") or name in ("log_oak", "log_spruce",
                                                    "log_birch", "log_jungle",
                                                    "log_acacia", "log_big_oak"):
        if not name.endswith("_top"):
            return log_side_canvas(name, e)
    if name.endswith("_log_top") or name.endswith("_stem_top") or \
            name.endswith("log_top"):
        return log_end_canvas(name, e)

    # ---------------------------------------------------------- ores / stone
    if "_ore" in name:
        c = ores(name)
        if c:
            return c

    if name == "stone":
        return _rock("rock_candy_pink", seed, cells=4.0, facet=.9, grain=.7)
    if name == "cobblestone":
        c = Canvas(32)
        P.cobble(c, seed, get_ramp("rock_candy"),
                 ["rock_candy", "rock_candy_pink", "rock_candy_mint",
                  "rock_candy_lilac"], get_ramp("meringue"), cells=5)
        return c
    if name == "cobblestone_mossy":
        c = Canvas(32)
        P.cobble(c, seed, get_ramp("rock_candy"),
                 ["rock_candy", "rock_candy_mint", "rock_candy_lilac"],
                 get_ramp("meringue"), cells=5)
        P.leaves(c, seed + 3, get_ramp("mint"), opaque=True, density=.35)
        return c
    if name.startswith("stonebrick"):
        return _bricks("rock_candy_pink", "meringue", seed, rows=4,
                       crack=("cracked" in name), mossy=("mossy" in name),
                       carved=("carved" in name))
    if name.startswith("stone_granite"):
        return _rock("rock_candy_pink", seed, cells=4.2, facet=.55, grain=.7)
    if name.startswith("stone_diorite"):
        return _rock("rock_candy", seed, cells=5.0, facet=.35, grain=.5)
    if name.startswith("stone_andesite"):
        return _rock("clay_lavender", seed, cells=4.5, facet=.5, grain=.55)
    if name in ("stone_slab_side", "stone_slab_top"):
        return _rock("rock_candy_pink", seed, cells=4.0, facet=.8, grain=.7)

    if name.startswith("deepslate") or name.startswith("cobbled_deepslate") or \
            name.startswith("polished_deepslate") or \
            name.startswith("chiseled_deepslate") or \
            name.startswith("cracked_deepslate"):
        if "bricks" in name or "tiles" in name:
            return _bricks("obsidian_jelly", "licorice", seed, rows=4,
                           crack=("cracked" in name))
        if name == "cobbled_deepslate":
            c = Canvas(32)
            P.cobble(c, seed, get_ramp("obsidian_jelly"),
                     ["obsidian_jelly", "blackberry_jelly", "grape_jelly"],
                     get_ramp("licorice"), cells=5)
            return c
        return _rock("obsidian_jelly", seed, cells=5.5, facet=.45, grain=.4)

    if name.startswith("tuff") and "brick" not in name:
        return _rock("pistachio", seed, cells=5.0, facet=.35, grain=.45)
    if name.startswith("tuff") and "brick" in name:
        return _bricks("pistachio", "meringue", seed, rows=4)

    if name == "calcite":
        return _rock("quartz_candy", seed, cells=6.0, facet=.2, grain=.28)
    if name.startswith("dripstone"):
        return _rock("peanut_brittle", seed, cells=4.0, facet=.3, grain=.5)

    if name.startswith("blackstone") or name.startswith("polished_blackstone") \
            or name.startswith("chiseled_polished_blackstone") \
            or name.startswith("cracked_polished_blackstone"):
        if "bricks" in name:
            return _bricks("licorice", "obsidian_jelly", seed, rows=4,
                           crack=("cracked" in name),
                           mossy=("gilded" in name), gold=("gilded" in name))
        return _rock("licorice", seed, cells=4.5, facet=.45, grain=.4,
                     sparkle=.003 if "gilded" in name else 0)
    if name.startswith("basalt") or name.startswith("polished_basalt") or \
            name == "smooth_basalt":
        return _rock("obsidian_jelly", seed, cells=6.0, facet=.3, grain=.35)
    if name.startswith("nether_brick") or name.startswith("red_nether_brick") \
            or name.startswith("cracked_nether_bricks") \
            or name.startswith("chiseled_nether_bricks"):
        return _bricks("red_velvet", "chocolate_chip", seed, rows=4,
                       crack=("cracked" in name))
    if name.startswith("netherrack"):
        c = Canvas(32)
        P.crumb(c, seed, get_ramp("red_velvet"), get_ramp("strawberry"),
                holes=.035)
        return c
    if name.startswith("soul_sand") or name.startswith("soul_soil"):
        c = Canvas(32)
        P.crumb(c, seed, get_ramp("soul_fudge"), holes=.03)
        return c
    if name.startswith("end_stone") or name.startswith("end_bricks"):
        if "bricks" in name:
            return _bricks("lemon_meringue", "meringue", seed, rows=4)
        return _rock("lemon_meringue", seed, cells=5.0, facet=.25, grain=.35)
    if name.startswith("purpur"):
        c = Canvas(32)
        P.taffy(c, seed, get_ramp("purpur_taffy"))
        return c
    if name.startswith("prismarine"):
        if "bricks" in name:
            return _bricks("prismarine_jelly", "sea_glass", seed, rows=3)
        return _rock("prismarine_jelly", seed, cells=4.0, facet=.35, grain=.5)
    if name.startswith("quartz"):
        if "bricks" in name:
            return _bricks("quartz_candy", "marshmallow", seed, rows=3)
        return _rock("quartz_candy", seed, cells=6.0, facet=.15, grain=.22)
    if name.startswith("sandstone") or name.startswith("red_sandstone"):
        ramp = "orange_sherbet" if name.startswith("red") else "sugar"
        if name.endswith(("_top", "_bottom")):
            c = Canvas(32)
            P.sugar(c, seed, get_ramp(ramp))
            return c
        if "carved" in name or "chiseled" in name or "smooth" in name:
            return restyle.restyle(e, get_ramp(ramp), keep_hue=.1,
                                   contrast=1.05)
        c = Canvas(32)
        P.sandstone(c, seed, get_ramp(ramp), get_ramp("caramel"))
        return c
    if name.startswith("sand") or name.startswith("red_sand"):
        c = Canvas(32)
        P.sugar(c, seed, get_ramp("orange_sherbet" if name.startswith("red")
                                  else "sugar"))
        return c
    if name == "gravel" or name.startswith("suspicious_gravel"):
        c = Canvas(32)
        P.gravel(c, seed, ["rock_candy", "sugar", "licorice"],
                 get_ramp("caramel"))
        return c
    if name.startswith("suspicious_sand"):
        c = Canvas(32)
        P.sugar(c, seed, get_ramp("sugar"), sparkle=True)
        return c
    if name == "clay" or name == "hardened_clay" or \
            name.startswith("hardened_clay_stained_"):
        c = Canvas(32)
        P.terracotta(c, seed, dye_ramp(name) if "stained" in name
                     else get_ramp("clay_lavender"))
        return c
    if name.startswith("mud_bricks"):
        return _bricks("mud_pudding", "meringue", seed, rows=4)
    if name in ("mud", "packed_mud"):
        c = Canvas(32)
        P.crumb(c, seed, get_ramp("mud_pudding"), holes=.02)
        return c
    if name.startswith("moss_block"):
        c = Canvas(32)
        P.leaves(c, seed, get_ramp("pistachio"), opaque=True, density=.93)
        return c
    if name in ("snow", "powder_snow"):
        c = Canvas(32)
        P.snow(c, seed, get_ramp("snow_fluff"))
        return c
    if name.startswith("ice") or name.startswith("frosted_ice") or \
            name.startswith("blue_ice") or name.startswith("packed_ice"):
        c = Canvas(32)
        P.ice(c, seed, get_ramp("ice_blue" if "blue" in name else "sugar_glass"))
        return c
    if name.startswith("magma"):
        c = Canvas(32)
        P.fluid_still(c, seed, get_ramp("magma_jam"), (255, 230, 150), 0, 1)
        return c
    if name.startswith(("glowstone", "shroomlight", "sea_lantern",
                        "ochre_froglight", "verdant_froglight",
                        "pearlescent_froglight")):
        c = Canvas(32)
        P.glowstone(c, seed, get_ramp("lemon_drop" if "ochre" in name else
                                      "honeycomb"))
        return c
    if name.startswith("amethyst_block") or name.startswith("budding_amethyst"):
        c = Canvas(32)
        P.gem_block(c, seed, get_ramp("amethyst_candy"), style="speckle")
        return c
    if name.startswith("sponge"):
        c = Canvas(32)
        P.sponge(c, seed, get_ramp("sponge_cake"),
                 get_ramp("caramel").at(.35))
        return c
    if name.startswith("honeycomb") or name.startswith("honey_"):
        c = Canvas(32)
        P.honeycomb(c, seed, get_ramp("honeycomb"), (120, 72, 18))
        return c
    if name.startswith("slime"):
        c = Canvas(32)
        P.sugar(c, seed, get_ramp("gummy_green"), sparkle=True)
        return c
    if name.startswith("mushroom_block_"):
        c = Canvas(32)
        if name.endswith("_red"):
            P.mushroom_skin(c, seed, "strawberry", "meringue", spots=5)
        elif name.endswith("_brown"):
            P.mushroom_skin(c, seed, "milk_chocolate", "vanilla", spots=6)
        elif name.endswith("_stem"):
            P.mushroom_stem(c, seed, "mushroom_cream")
        else:
            P.mushroom_inside(c, seed, "meringue")
        return c
    if name.startswith("melon"):
        c = Canvas(32)
        if "top" in name or "stem" in name:
            if "stem" in name:
                return restyle.restyle(e, get_ramp("pistachio"), keep_hue=.1)
            P.sugar(c, seed, get_ramp("pistachio"))
        else:
            P.melon(c, seed, get_ramp("melon_taffy"),
                    (250, 240, 220), (40, 20, 30))
        return c
    if name.startswith("pumpkin"):
        if "stem" in name or "face" in name:
            return restyle.restyle(e, get_ramp("caramel"), keep_hue=.15)
        c = Canvas(32)
        P.pumpkin(c, seed, get_ramp("orange_sherbet"),
                  get_ramp("pistachio").at(.35))
        return c
    if name.startswith("cactus"):
        c = Canvas(32)
        P.cactus(c, seed, get_ramp("cactus_gummy"), (250, 240, 210))
        return c
    if "lightning_rod" in name:
        ramp = ("sea_glass" if "oxidized" in name else
                "copper_wrap" if "weathered" in name else "copper_candy")
        return restyle.restyle(e, get_ramp(ramp), keep_hue=.10,
                               contrast=1.15)

    # ---------------------------------------------------------- dyes
    if name.startswith("wool_colored_"):
        c = Canvas(32)
        P.wool(c, seed, dye_ramp(name), accent=dye_col(name))
        return c
    if name.startswith("concrete_powder_"):
        c = Canvas(32)
        P.sugar(c, seed, dye_ramp(name))
        return c
    if name.startswith("concrete_"):
        c = Canvas(32)
        P.concrete(c, seed, dye_ramp(name))
        return c
    if name.startswith("glass_pane_top"):
        return restyle.restyle(e, dye_ramp(name) if dye_of(name)
                               else get_ramp("sugar_glass"),
                               keep_hue=.08, contrast=1.1)
    if name == "glass" or name.startswith("glass_"):
        c = Canvas(32)
        tint = dye_col(name) if dye_of(name) else (236, 250, 255)
        P.glass(c, seed, tint=tint)
        return c
    if name.startswith("shulker_top"):
        pal = dye_ramp(name) if dye_of(name) else get_ramp("grape_taffy")
        return restyle.restyle(e, pal, keep_hue=.15, contrast=1.05)
    if name.startswith("candle"):
        pal = dye_ramp(name) if dye_of(name) else get_ramp("marshmallow")
        c = restyle.restyle(e, pal, keep_hue=.05, contrast=1.0)
        if "lit" in name:
            restyle.glow(c, (255, 230, 150), .4)
        return c

    # ---------------------------------------------------------- fluids
    if name in ("water_placeholder", "lava_placeholder",
                "fire_0_placeholder", "fire_1_placeholder",
                "portal_placeholder", "water_flow_grey_placeholder",
                "cauldron_water_placeholder"):
        return restyle.restyle(e, get_ramp("blue_raspberry"), keep_hue=.1)
    if name == "grass_side":
        # Bedrock keeps the dirt RGB under alpha=0 and the tint mask at
        # alpha=255.  Restyling only the visible pixels would turn the hidden
        # dirt black, so map both layers here.
        w, h, px = restyle.load_source(e)
        scale = restyle.scale_for(e)
        out = Canvas(w * scale, h * scale)
        dirt = get_ramp("chocolate")
        for y in range(h):
            for x in range(w):
                i = (y * w + x) * 4
                r, g, b, a = px[i], px[i + 1], px[i + 2], px[i + 3]
                l = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
                if a:
                    v = int(clamp(90 + l * 162))
                    col = (v, v, v)
                else:
                    col = dirt.at(clamp((l - .16) / .66, 0.0, 1.0))
                for sy in range(scale):
                    for sx in range(scale):
                        out.set(x * scale + sx, y * scale + sy, col, a)
        return out

    if name in ("water_still_grey", "water_flow_grey"):
        grey_water = make_ramp("#d5d7de", shadow="#6e7079", light="#ffffff")
        if name == "water_still_grey":
            return frames_canvas(32, lambda f, c: P.fluid_still(
                c, seed, grey_water, (255, 255, 255), f, 32))
        return frames_canvas(e["frames"], lambda f, c: P.fluid_flow(
            c, seed, grey_water, (255, 255, 255), f, e["frames"]))
    if name == "water_still":
        return frames_canvas(32, lambda f, c: P.fluid_still(
            c, seed, get_ramp("blue_raspberry"), (235, 252, 255), f, 32))
    if name == "water_flow":
        return frames_canvas(e["frames"], lambda f, c: P.fluid_flow(
            c, seed, get_ramp("blue_raspberry"), (235, 252, 255), f, e["frames"]))
    if name.startswith("lava_still"):
        return frames_canvas(32, lambda f, c: P.fluid_still(
            c, seed, get_ramp("magma_jam"), (255, 235, 150), f, 32))
    if name.startswith("lava_flow"):
        return frames_canvas(e["frames"], lambda f, c: P.fluid_flow(
            c, seed, get_ramp("magma_jam"), (255, 235, 150), f, e["frames"]))
    if name == "portal":
        return frames_canvas(32, lambda f, c: P.fluid_still(
            c, seed, get_ramp("grape_jelly"), (235, 200, 255), f, 32))
    if name.startswith("cauldron_water"):
        return frames_canvas(32, lambda f, c: P.fluid_still(
            c, seed, get_ramp("blue_raspberry"), (235, 252, 255), f, 32))
    if name in ("water_placeholder", "lava_placeholder",
                "fire_0_placeholder", "fire_1_placeholder",
                "portal_placeholder", "water_flow_grey_placeholder"):
        return restyle.restyle(e, get_ramp("blue_raspberry"), keep_hue=.1)

    # ---------------------------------------------------------- fallback
    pal = fallback_palette(name)
    if e.get("tint_mask"):
        return restyle.restyle(e, get_ramp(pal), grey=True, contrast=1.05)
    if name.startswith(("fire", "soul_fire", "campfire", "soul_campfire")):
        c = restyle.restyle(e, get_ramp("lemon_drop"), keep_hue=.35,
                            contrast=1.1)
        restyle.glow(c, (255, 240, 170), .25)
        return c
    if restyle.has_transparency(e):
        return restyle.candy_paint(e, outline=(48, 26, 42))
    return restyle.restyle(e, get_ramp(pal), keep_hue=keep_hue_for(name),
                           contrast=1.08)


def fallback_palette(name):
    rules = [
        ("sculk", "sculk_jam"), ("coral", "cotton_candy"),
        ("oxidized_lightning_rod", "sea_glass"),
        ("weathered_lightning_rod", "copper_wrap"),
        ("lightning_rod", "copper_candy"),
        ("ancient_debris", "ancient_chocolate"),
        ("netherite", "netherite_dark"), ("obsidian", "obsidian_jelly"),
        ("copper", "copper_wrap"), ("cinnabar", "cherry"),
        ("sulfur", "sulfur_sherbet"), ("resin", "resin_caramel"),
        ("redstone", "redstone_candy"), ("command", "mint"),
        ("structure", "lavender"), ("jigsaw", "blueberry"),
        ("bed_", "cherry"), ("door_", "wafer"), ("_door_", "wafer"),
        ("trapdoor", "wafer"), ("shelf", "wafer"), ("fence", "wafer"),
        ("_log", "bark_wafer"), ("_planks", "wafer"),
        ("bookshelf", "wafer"), ("barrel", "wafer"), ("chest", "wafer"),
        ("crafting_table", "wafer"), ("lectern", "wafer"),
        ("loom", "wafer"), ("cartography", "wafer"),
        ("fletching", "wafer"), ("smithing", "wafer"),
        ("composter", "wafer"), ("bee", "honeycomb"),
        ("honey", "honeycomb"), ("furnace", "rock_candy_pink"),
        ("smoker", "rock_candy_pink"), ("blast", "rock_candy_pink"),
        ("stonecutter", "rock_candy_pink"), ("grindstone", "rock_candy_pink"),
        ("anvil", "silver_sugar"), ("cauldron", "silver_sugar"),
        ("hopper", "silver_sugar"), ("brewing", "silver_sugar"),
        ("piston", "silver_sugar"), ("observer", "silver_sugar"),
        ("dispenser", "silver_sugar"), ("dropper", "silver_sugar"),
        ("repeater", "redstone_candy"), ("comparator", "redstone_candy"),
        ("rail", "silver_sugar"), ("lever", "silver_sugar"),
        ("trip_wire", "silver_sugar"), ("target", "marshmallow"),
        ("jukebox", "wafer"), ("noteblock", "wafer"),
        ("enchanting", "grape_jelly"), ("end_portal", "obsidian_jelly"),
        ("end_gateway", "obsidian_jelly"), ("endframe", "lemon_meringue"),
        ("dragon_egg", "purpur_taffy"), ("beacon", "diamond_candy"),
        ("conduit", "sea_glass"), ("daylight", "gold_candy"),
        ("redstone_lamp", "gold_candy"), ("tnt", "cherry"),
        ("slime", "gummy_green"), ("froglight", "lemon_drop"),
        ("frogspawn", "mint"), ("egg", "meringue"),
        ("pottery", "clay_lavender"), ("decorated_pot", "clay_lavender"),
        ("banner", "cherry"), ("sign", "wafer"),
        ("bed", "cherry"), ("cake", "sponge_cake"),
        ("flower_pot", "clay_lavender"), ("item_frame", "wafer"),
        ("glow_item_frame", "wafer"), ("ladder", "wafer"),
        ("scaffolding", "wafer"), ("web", "marshmallow"),
        ("vine", "mint"), ("kelp", "sour_apple"), ("seagrass", "sour_apple"),
        ("lily", "mint"), ("reeds", "sour_apple"),
        ("cactus", "cactus_gummy"), ("bamboo", "sour_apple"),
        ("chorus", "purpur_taffy"), ("shulker", "grape_taffy"),
        ("glass", "sugar_glass"), ("ice", "ice_blue"),
        ("snow", "snow_fluff"), ("sand", "sugar"),
        ("dirt", "chocolate"), ("grass", "mint"), ("leaves", "mint"),
        ("log", "bark_wafer"), ("planks", "wafer"),
        ("stone", "rock_candy_pink"), ("deepslate", "obsidian_jelly"),
        ("nether", "red_velvet"), ("end", "lemon_meringue"),
        ("purpur", "purpur_taffy"), ("prismarine", "prismarine_jelly"),
        ("quartz", "quartz_candy"), ("gold", "gold_wrap"),
        ("iron", "iron_candy"), ("diamond", "diamond_candy"),
        ("emerald", "emerald_candy"), ("lapis", "lapis_candy"),
        ("coal", "coal_candy"), ("wool", "cotton_candy"),
        ("terracotta", "clay_lavender"), ("coral", "cotton_candy"),
        ("mushroom", "mushroom_cream"), ("pumpkin", "orange_sherbet"),
        ("melon", "melon_taffy"), ("sugar", "sugar"),
        ("bone", "bone_white"), ("totem", "gold_candy"),
    ]
    for k, v in rules:
        if k in name:
            return v
    return "rock_candy_pink"


def keep_hue_for(name):
    if any(k in name for k in ("coral", "flower", "pottery", "glazed",
                               "bed", "banner", "candle", "shulker",
                               "concrete", "terracotta", "carpet")):
        return .25
    if any(k in name for k in ("chest", "door", "planks", "log", "shelf",
                               "barrel", "table", "wood", "bamboo")):
        return .10
    return .06


def _rock(pal, seed, **kw):
    c = Canvas(32)
    P.rock(c, seed, get_ramp(pal), **kw)
    return c


def _bricks(pal, mortar, seed, rows=4, crack=False, mossy=False,
            carved=False, gold=False):
    c = Canvas(32)
    P.bricks(c, seed, get_ramp(pal), get_ramp(mortar), rows=rows, cols=2,
             crack=1.0 if crack else 0.0)
    if mossy:
        rnd = random.Random(seed + 4)
        for _ in range(4):
            x, y = rnd.randrange(32), rnd.randrange(32)
            for yy in range(3):
                for xx in range(3):
                    if rnd.random() < .6:
                        c.set((x + xx) % 32, (y + yy) % 32,
                              get_ramp("mint" if not gold else "gold_candy").at(.8))
    if carved:
        for i in range(8):
            ang = i * math.pi / 4
            for r in range(2, 7):
                c.set(int(16 + math.cos(ang) * r) % 32,
                      int(16 + math.sin(ang) * r) % 32,
                      get_ramp(mortar).at(.9))
    return c
