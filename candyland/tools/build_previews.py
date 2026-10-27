#!/usr/bin/env python3
"""Build the handful of contact sheets used by the README."""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "resource_pack", "textures")
OUT = os.path.join(ROOT, "previews")
BG = "#2a1626"

BLOCK_BASES = """
blocks/grass_top blocks/grass_side blocks/dirt blocks/stone blocks/sand
blocks/red_sand blocks/sandstone_normal blocks/red_sandstone_normal
blocks/gravel blocks/clay blocks/snow blocks/ice blocks/dirt_podzol_top
blocks/mycelium_top blocks/moss_block blocks/mud blocks/deepslate/deepslate
blocks/tuff blocks/calcite blocks/basalt_side blocks/blackstone
blocks/netherrack blocks/soul_sand blocks/end_stone blocks/purpur_block
blocks/prismarine_rough blocks/amethyst_block blocks/sculk blocks/copper_block
blocks/lightning_rod blocks/planks_oak blocks/planks_spruce blocks/planks_birch
blocks/cherry_planks blocks/bamboo_planks blocks/brick blocks/stonebrick
blocks/mud_bricks blocks/quartz_bricks blocks/wool_colored_pink
blocks/wool_colored_lime blocks/glass blocks/glass_pane_top blocks/cake_side
blocks/mushroom_block_skin_red blocks/mushroom_block_skin_brown
blocks/coral_red blocks/coral_fan_red blocks/flower_rose
blocks/flower_tulip_red blocks/leaves_oak blocks/cherry_leaves
blocks/azalea_leaves_flowers blocks/cactus_side blocks/melon_side
blocks/pumpkin_side blocks/target_side blocks/bookshelf
blocks/crafting_table_top blocks/furnace_front_off blocks/tnt_side
blocks/sponge blocks/sea_lantern blocks/glowstone
""".split()

ITEM_BASES = """
items/apple items/apple_golden items/bread items/cookie items/cake
items/carrot items/potato_baked items/beetroot items/sweet_berries
items/honey_bottle items/bucket_milk items/amethyst_shard items/diamond
items/emerald items/quartz items/gold_ingot items/iron_ingot
items/copper_ingot items/netherite_ingot items/coal items/redstone_dust
items/stick items/string items/feather items/leather items/rabbit_hide
items/blaze_rod items/ender_pearl items/ghast_tear items/nether_star
items/echo_shard items/diamond_sword items/diamond_pickaxe items/diamond_axe
items/diamond_shovel items/diamond_hoe items/diamond_helmet
items/diamond_chestplate items/diamond_leggings items/diamond_boots
items/bow_standby items/arrow items/shield items/trident
items/crossbow_standby items/fishing_rod_uncast items/flint_and_steel
items/shears items/saddle items/name_tag items/lead items/bone items/gunpowder
items/glowstone_dust items/sugar items/wheat items/pumpkin_pie
items/chorus_fruit items/book_normal items/book_enchanted items/paper
items/spawn_eggs/spawn_egg_bee items/spawn_eggs/spawn_egg_axolotl
items/spawn_eggs/spawn_egg_allay items/spawn_eggs/spawn_egg_warden
""".split()


def inventory_paths():
    inv = json.load(open(os.path.join(ROOT, "build", "inventory.json")))
    out = {}
    for t in inv["textures"]:
        if t["category"] == "colormap":
            rel = "colormap/" + t["name"] + ".png"
        else:
            rel = t["base"] + "." + t["src_ext"]
        out[t["base"]] = os.path.join(PACK, *rel.split("/"))
    return out


def montage(paths, out, tile="8x"):
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        return
    # grass_side keeps its dirt under alpha=0; flatten it for the catalog so
    # the preview shows the dirt pattern instead of an empty cutout.
    fixed = []
    for p in paths:
        if p.endswith("grass_side.tga"):
            tmp = "/tmp/opencode/grass_side_flat.png"
            subprocess.run(["magick", p, "-alpha", "off", tmp], check=True)
            p = tmp
        fixed.append(p)
    paths = fixed
    subprocess.run(
        ["magick", "montage"] + paths + [
            "-background", BG,
            "-tile", tile,
            "-geometry", "128x128+8+8",
            "-filter", "point",
            out,
        ], check=True)
    print(out, len(paths), "tiles")


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = inventory_paths()
    blocks = [paths[b] for b in BLOCK_BASES if b in paths]
    items = [paths[b] for b in ITEM_BASES if b in paths]
    montage(blocks, os.path.join(OUT, "blocks.png"))
    montage(items, os.path.join(OUT, "items.png"))

    # Existing full-category sheets are cheap and already cover the categories
    # that are hard to tile meaningfully (mob skins, UI elements, sky art).
    for src, dst in (
        ("/tmp/opencode/envsrc/entity_key.png", "entities.png"),
        ("/tmp/opencode/envsrc/ui_out.png", "ui.png"),
        ("/tmp/opencode/envsrc/env_out.png", "environment.png"),
    ):
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(OUT, dst))
            print(dst)
    icon = os.path.join(ROOT, "resource_pack", "pack_icon.png")
    if os.path.isfile(icon):
        shutil.copyfile(icon, os.path.join(OUT, "icon.png"))


if __name__ == "__main__":
    main()
