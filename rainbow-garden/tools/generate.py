"""
Build the Rainbow Garden Bedrock add-on.

Outputs:
  behavior_pack/             behaviour pack
  resource_pack/             resource pack
  RainbowGarden-<version>.mcaddon
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path

from PIL import Image

import content

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
VERSION = (ROOT / "tools" / "VERSION").read_text(encoding="utf-8").strip()
VERSION_PARTS = [int(p) for p in VERSION.split(".")]
OUT = ROOT / f"RainbowGarden-{VERSION}.mcaddon"

BP_HEADER_UUID = "544a84ed-27aa-4c04-9b68-2266ada591f3"
BP_MODULE_UUID = "e7e18f25-d72e-40e5-94a5-5f429a98a8b9"
RP_HEADER_UUID = "32173581-f636-4ba2-b930-f22fec9cd38c"
RP_MODULE_UUID = "a425237d-f9cf-461d-9ba5-7e8f2356b819"

ENTITY_ID = "rg:rainbow_butterfly"
BUTTERFLY_GEOMETRY = "geometry.rg.rainbow_butterfly"
BUTTERFLY_TEXTURE = "textures/entity/rainbow_butterfly"
BUTTERFLY_ANIMATION = "animation.rg.rainbow_butterfly.fly"
BUTTERFLY_CONTROLLER = "controller.render.rg.rainbow_butterfly"

FLOWER_GEOMETRY = "geometry.rg.rainbow_flower"
TREE_GEOMETRY = "geometry.rg.rainbow_tree"
MUSHROOM_GEOMETRY = "geometry.rg.rainbow_mushroom"
FULL_BLOCK_GEOMETRY = "minecraft:geometry.full_block"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_png(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


def manifest(name: str, description: str, header_uuid: str, module_uuid: str,
             module_type: str, dependency: dict | None = None) -> dict:
    data = {
        "format_version": 2,
        "header": {
            "name": name,
            "description": description,
            "uuid": header_uuid,
            "version": VERSION_PARTS,
            "min_engine_version": [1, 21, 130],
        },
        "modules": [
            {
                "description": description,
                "type": module_type,
                "uuid": module_uuid,
                "version": VERSION_PARTS,
            }
        ],
        "dependencies": [dependency] if dependency else [],
        "metadata": {
            "authors": ["OpenCode"],
            "license": "MIT",
        },
    }
    return data


# ---------------------------------------------------------------------------
# Block and item definitions
# ---------------------------------------------------------------------------

BLOCKS = []
for flower in content.FLOWERS:
    BLOCKS.append({
        "id": f"rg:rainbow_flower_{flower['key']}",
        "name": f"{flower['label']} Rainbow Flower",
        "kind": "flower",
        "texture": f"rg_rainbow_flower_{flower['key']}",
        "geometry": FLOWER_GEOMETRY,
        "map": flower["map"],
        "light": 2,
        "selection": ([-6, 0, -6], [12, 16, 12]),
        "collision": False,
        "render": "alpha_test",
    })

BLOCKS += [
    {
        "id": "rg:rainbow_tree",
        "name": "Rainbow Tree",
        "kind": "tree",
        "texture": "rg_rainbow_tree",
        "geometry": TREE_GEOMETRY,
        "map": "#4fbf6a",
        "light": 3,
        "selection": ([-8, 0, -8], [16, 16, 16]),
        "collision": False,
        "render": "alpha_test",
    },
    {
        "id": "rg:rainbow_mushroom",
        "name": "Rainbow Mushroom",
        "kind": "mushroom",
        "texture": "rg_rainbow_mushroom",
        "geometry": MUSHROOM_GEOMETRY,
        "map": "#ff7ab8",
        "light": 1,
        "selection": ([-7, 0, -7], [14, 16, 14]),
        "collision": False,
        "render": "alpha_test",
    },
    {
        "id": "rg:rainbow_lantern",
        "name": "Rainbow Lantern",
        "kind": "lantern",
        "texture": "rg_rainbow_lantern",
        "geometry": FULL_BLOCK_GEOMETRY,
        "map": "#ffd85a",
        "light": 15,
        "selection": None,
        "collision": True,
        "render": "opaque",
    },
]

ITEMS = []
for flower in content.FLOWERS:
    ITEMS.append({
        "id": f"rg:rainbow_seed_{flower['key']}",
        "name": f"{flower['label']} Rainbow Seed",
        "icon": f"rg_rainbow_seed_{flower['key']}",
        "block": f"rg:rainbow_flower_{flower['key']}",
    })
ITEMS += [
    {
        "id": "rg:rainbow_tree_seed",
        "name": "Rainbow Tree Seed",
        "icon": "rg_rainbow_tree_seed",
        "block": "rg:rainbow_tree",
    },
    {
        "id": "rg:rainbow_mushroom_seed",
        "name": "Rainbow Mushroom Seed",
        "icon": "rg_rainbow_mushroom_seed",
        "block": "rg:rainbow_mushroom",
    },
]


def block_json(block: dict) -> dict:
    components = {
        "minecraft:geometry": block["geometry"],
        "minecraft:material_instances": {
            "*": {
                "texture": block["texture"],
                "render_method": block["render"],
            }
        },
        "minecraft:item_visual": {
            "geometry": block["geometry"],
            "material_instances": {
                "*": {
                    "texture": block["texture"],
                    "render_method": block["render"],
                }
            },
        },
        "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.1},
        "minecraft:destructible_by_explosion": False,
        "minecraft:destruction_particles": {
            "texture": block["texture"],
            "particle_count": 24,
        },
        "minecraft:light_emission": block["light"],
        "minecraft:light_dampening": 0,
        "minecraft:map_color": block["map"],
        "minecraft:display_name": f"tile.{block['id']}.name",
        "minecraft:collision_box": block["collision"],
    }
    if block["selection"] is not None:
        origin, size = block["selection"]
        components["minecraft:selection_box"] = {"origin": origin, "size": size}
    return {
        "format_version": "1.21.90",
        "minecraft:block": {
            "description": {
                "identifier": block["id"],
                "menu_category": {"category": "nature"},
            },
            "components": components,
        },
    }


def item_json(item: dict) -> dict:
    return {
        "format_version": "1.21.90",
        "minecraft:item": {
            "description": {
                "identifier": item["id"],
                "menu_category": {"category": "nature"},
            },
            "components": {
                "minecraft:icon": {"textures": {"default": item["icon"]}},
                "minecraft:display_name": {"value": f"item.{item['id']}"},
                "minecraft:max_stack_size": 64,
                "minecraft:glint": True,
                "minecraft:block_placer": {
                    "block": item["block"],
                    "replace_block_item": False,
                },
            },
        },
    }


def seed_recipe(flower: dict) -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": f"rg:rainbow_seed_{flower['key']}_recipe"},
            "tags": ["crafting_table"],
            "ingredients": [
                {"item": flower["dye"]},
                {"item": "minecraft:wheat_seeds"},
            ],
            "result": {"item": f"rg:rainbow_seed_{flower['key']}", "count": 4},
        },
    }


def tree_recipe() -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": "rg:rainbow_tree_seed_recipe"},
            "tags": ["crafting_table"],
            "ingredients": [
                {"item": "rg:rainbow_seed_red"},
                {"item": "rg:rainbow_seed_orange"},
                {"item": "rg:rainbow_seed_yellow"},
                {"item": "rg:rainbow_seed_green"},
                {"item": "minecraft:oak_sapling"},
            ],
            "result": {"item": "rg:rainbow_tree_seed", "count": 1},
        },
    }


def mushroom_recipe() -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": "rg:rainbow_mushroom_seed_recipe"},
            "tags": ["crafting_table"],
            "ingredients": [
                {"item": "rg:rainbow_seed_red"},
                {"item": "rg:rainbow_seed_purple"},
                {"item": "minecraft:red_mushroom"},
            ],
            "result": {"item": "rg:rainbow_mushroom_seed", "count": 1},
        },
    }


def lantern_recipe() -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shaped": {
            "description": {"identifier": "rg:rainbow_lantern_recipe"},
            "tags": ["crafting_table"],
            "pattern": [" G ", "GLG", " G "],
            "key": {
                "G": {"item": "minecraft:glass"},
                "L": {"item": "minecraft:glowstone_dust"},
            },
            "result": {"item": "rg:rainbow_lantern", "count": 1},
        },
    }


# ---------------------------------------------------------------------------
# Entity, animation, spawn rules
# ---------------------------------------------------------------------------

def entity_json() -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {
                "identifier": ENTITY_ID,
                "spawn_category": "ambient",
                "is_spawnable": True,
                "is_summonable": True,
                "is_experimental": False,
            },
            "components": {
                "minecraft:type_family": {
                    "family": ["rg:rainbow_butterfly", "butterfly", "ambient", "mob"]
                },
                "minecraft:health": {"value": 20, "max": 20},
                "minecraft:collision_box": {"width": 0.35, "height": 0.6},
                "minecraft:movement": {"value": 0.1},
                "minecraft:movement.hover": {},
                "minecraft:navigation.hover": {
                    "can_path_from_air": True,
                    "can_path_over_water": True,
                    "avoid_water": True,
                    "can_sink": False,
                },
                "minecraft:can_fly": {},
                "minecraft:flying_speed": {"value": 0.1},
                "minecraft:physics": {"has_gravity": False, "has_collision": False},
                "minecraft:breathable": {
                    "breathes_air": True,
                    "breathes_water": False,
                    "total_supply": 15,
                    "suffocate_time": 0,
                },
                "minecraft:behavior.float": {"priority": 7},
                "minecraft:behavior.random_hover": {
                    "hover_height": [1, 4],
                    "y_dist": 8,
                    "interval": 1,
                    "xz_dist": 8,
                    "priority": 9,
                    "y_offset": -1,
                },
                "minecraft:behavior.look_at_player": {
                    "priority": 8,
                    "look_distance": 6.0,
                    "probability": 0.02,
                },
                "minecraft:behavior.random_look_around": {"priority": 8},
                "minecraft:damage_sensor": {
                    "triggers": [{"cause": "all", "deals_damage": "no"}]
                },
                "minecraft:persistent": {},
                "minecraft:nameable": {},
                "minecraft:knockback_resistance": {"value": 1.0, "max": 1.0},
                "minecraft:fire_immune": {},
                "minecraft:conditional_bandwidth_optimization": {},
            },
        },
    }


def client_entity_json() -> dict:
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": ENTITY_ID,
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": BUTTERFLY_TEXTURE},
                "geometry": {"default": BUTTERFLY_GEOMETRY},
                "animations": {"fly": BUTTERFLY_ANIMATION},
                "scripts": {"animate": ["fly"]},
                "render_controllers": [BUTTERFLY_CONTROLLER],
                "spawn_egg": {
                    "base_color": "#ff7ab8",
                    "overlay_color": "#7ad7ff",
                },
            }
        },
    }


def animation_json() -> dict:
    return {
        "format_version": "1.10.0",
        "animations": {
            BUTTERFLY_ANIMATION: {
                "loop": True,
                "animation_length": 0.5,
                "bones": {
                    "body": {
                        "position": [0, "math.sin(query.anim_time * 360) * 0.4", 0]
                    },
                    "left_wing": {
                        "rotation": [0, 0, "-math.sin(query.anim_time * 720) * 30"]
                    },
                    "right_wing": {
                        "rotation": [0, 0, "math.sin(query.anim_time * 720) * 30"]
                    },
                },
            }
        },
    }


def render_controller_json() -> dict:
    return {
        "format_version": "1.10.0",
        "render_controllers": {
            BUTTERFLY_CONTROLLER: {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
            }
        },
    }


def spawn_rules_json() -> dict:
    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {
                "identifier": ENTITY_ID,
                "population_control": "ambient",
            },
            "conditions": [
                {
                    "minecraft:spawns_on_surface": {},
                    "minecraft:brightness_filter": {
                        "min": 7,
                        "max": 15,
                        "adjust_for_weather": False,
                    },
                    "minecraft:weight": {"default": 6},
                    "minecraft:herd": {"min_size": 1, "max_size": 2},
                    "minecraft:density_limit": {"surface": 4},
                    "minecraft:biome_filter": [
                        {"test": "has_biome_tag", "operator": "==", "value": "flower_forest"},
                        {"test": "has_biome_tag", "operator": "==", "value": "meadow"},
                        {"test": "has_biome_tag", "operator": "==", "value": "plains"},
                        {"test": "has_biome_tag", "operator": "==", "value": "sunflower_plains"},
                    ],
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# Textures and atlases
# ---------------------------------------------------------------------------

def build_textures() -> None:
    for flower in content.FLOWERS:
        save_png(RP / "textures" / "blocks" / f"rainbow_flower_{flower['key']}.png",
                 content.flower_texture(flower))
        save_png(RP / "textures" / "items" / f"rainbow_seed_{flower['key']}.png",
                 content.seed_icon(flower))
    save_png(RP / "textures" / "blocks" / "rainbow_tree.png", content.tree_texture())
    save_png(RP / "textures" / "blocks" / "rainbow_mushroom.png", content.mushroom_texture())
    save_png(RP / "textures" / "blocks" / "rainbow_lantern.png", content.lantern_texture())
    save_png(RP / "textures" / "items" / "rainbow_tree_seed.png", content.tree_seed_icon())
    save_png(RP / "textures" / "items" / "rainbow_mushroom_seed.png", content.mushroom_seed_icon())
    save_png(RP / "textures" / "entity" / "rainbow_butterfly.png", content.butterfly_texture())
    icon = content.pack_icon()
    save_png(BP / "pack_icon.png", icon)
    save_png(RP / "pack_icon.png", icon)


def build_atlases() -> None:
    terrain = {
        "resource_pack_name": "rainbow_garden",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {},
    }
    item = {
        "resource_pack_name": "rainbow_garden",
        "texture_name": "atlas.items",
        "texture_data": {},
    }
    for flower in content.FLOWERS:
        key = f"rg_rainbow_flower_{flower['key']}"
        terrain["texture_data"][key] = {
            "textures": f"textures/blocks/rainbow_flower_{flower['key']}"
        }
        ikey = f"rg_rainbow_seed_{flower['key']}"
        item["texture_data"][ikey] = {
            "textures": f"textures/items/rainbow_seed_{flower['key']}"
        }
    for key, path in [
        ("rg_rainbow_tree", "textures/blocks/rainbow_tree"),
        ("rg_rainbow_mushroom", "textures/blocks/rainbow_mushroom"),
        ("rg_rainbow_lantern", "textures/blocks/rainbow_lantern"),
    ]:
        terrain["texture_data"][key] = {"textures": path}
    for key, path in [
        ("rg_rainbow_tree_seed", "textures/items/rainbow_tree_seed"),
        ("rg_rainbow_mushroom_seed", "textures/items/rainbow_mushroom_seed"),
    ]:
        item["texture_data"][key] = {"textures": path}
    write_json(RP / "textures" / "terrain_texture.json", terrain)
    write_json(RP / "textures" / "item_texture.json", item)

    textures = []
    for flower in content.FLOWERS:
        textures.append(f"textures/blocks/rainbow_flower_{flower['key']}")
        textures.append(f"textures/items/rainbow_seed_{flower['key']}")
    textures += [
        "textures/blocks/rainbow_tree",
        "textures/blocks/rainbow_mushroom",
        "textures/blocks/rainbow_lantern",
        "textures/items/rainbow_tree_seed",
        "textures/items/rainbow_mushroom_seed",
        "textures/entity/rainbow_butterfly",
    ]
    write_json(RP / "textures" / "textures_list.json", textures)


def build_blocks_json() -> None:
    data = {}
    for block in BLOCKS:
        if block["kind"] == "lantern":
            sound = "glass"
        elif block["kind"] == "tree":
            sound = "wood"
        else:
            sound = "grass"
        data[block["id"]] = {"sound": sound}
    write_json(RP / "blocks.json", data)


def build_language() -> None:
    lines = [
        f"pack.name={content.PACK_NAME}",
        "pack.description=A gentle rainbow garden with giant flowers, glowing trees, mushrooms, lanterns and butterflies. Made for young children.",
        "",
    ]
    for block in BLOCKS:
        lines.append(f"tile.{block['id']}.name={block['name']}")
        lines.append(f"tile.{block['id'].replace(':', '.')}.name={block['name']}")
    lines.append("")
    for item in ITEMS:
        lines.append(f"item.{item['id']}={item['name']}")
        lines.append(f"item.{item['id']}.name={item['name']}")
    lines.append("")
    lines += [
        "entity.rg:rainbow_butterfly.name=Rainbow Butterfly",
        "entity.rg.rainbow_butterfly.name=Rainbow Butterfly",
        "item.spawn_egg.entity.rg:rainbow_butterfly.name=Rainbow Butterfly Spawn Egg",
        "item.spawn_egg.entity.rg.rainbow_butterfly.name=Rainbow Butterfly Spawn Egg",
        "item.rg:rainbow_butterfly_spawn_egg=Rainbow Butterfly Spawn Egg",
        "item.rg:rainbow_butterfly_spawn_egg.name=Rainbow Butterfly Spawn Egg",
        "",
    ]
    text = "\n".join(lines)
    for pack in (BP, RP):
        (pack / "texts").mkdir(parents=True, exist_ok=True)
        (pack / "texts" / "en_US.lang").write_text(text, encoding="utf-8")
        write_json(pack / "texts" / "languages.json", ["en_US"])


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def main() -> int:
    for pack in (BP, RP):
        if pack.exists():
            shutil.rmtree(pack)
    BP.mkdir(parents=True)
    RP.mkdir(parents=True)

    write_json(BP / "manifest.json", manifest(
        content.BP_NAME,
        "Blocks, seeds and a gentle butterfly for Rainbow Garden.",
        BP_HEADER_UUID,
        BP_MODULE_UUID,
        "data",
    ))
    write_json(RP / "manifest.json", manifest(
        content.RP_NAME,
        "Models, textures and animations for Rainbow Garden.",
        RP_HEADER_UUID,
        RP_MODULE_UUID,
        "resources",
        {"uuid": BP_HEADER_UUID, "version": VERSION_PARTS},
    ))

    for block in BLOCKS:
        write_json(BP / "blocks" / f"{block['id'].split(':')[1]}.json", block_json(block))
    for item in ITEMS:
        write_json(BP / "items" / f"{item['id'].split(':')[1]}.json", item_json(item))
    for flower in content.FLOWERS:
        write_json(BP / "recipes" / f"rainbow_seed_{flower['key']}.json", seed_recipe(flower))
    write_json(BP / "recipes" / "rainbow_tree_seed.json", tree_recipe())
    write_json(BP / "recipes" / "rainbow_mushroom_seed.json", mushroom_recipe())
    write_json(BP / "recipes" / "rainbow_lantern.json", lantern_recipe())
    write_json(BP / "entities" / "rainbow_butterfly.json", entity_json())
    write_json(BP / "spawn_rules" / "rainbow_butterfly.json", spawn_rules_json())

    function_dir = BP / "functions" / "rainbow_garden"
    function_dir.mkdir(parents=True, exist_ok=True)
    (function_dir / "starter.mcfunction").write_text(
        "\n".join([
            "# Rainbow Garden starter kit",
            "give @s rg:rainbow_seed_red 8",
            "give @s rg:rainbow_seed_orange 8",
            "give @s rg:rainbow_seed_yellow 8",
            "give @s rg:rainbow_seed_green 8",
            "give @s rg:rainbow_seed_blue 8",
            "give @s rg:rainbow_seed_purple 8",
            "give @s rg:rainbow_tree_seed 4",
            "give @s rg:rainbow_mushroom_seed 4",
            "give @s rg:rainbow_lantern 8",
            "summon rg:rainbow_butterfly ~ ~1 ~",
            "",
        ]),
        encoding="utf-8",
    )

    write_json(RP / "models" / "blocks" / "rainbow_flower.geo.json", content.flower_geometry())
    write_json(RP / "models" / "blocks" / "rainbow_tree.geo.json", content.tree_geometry())
    write_json(RP / "models" / "blocks" / "rainbow_mushroom.geo.json", content.mushroom_geometry())
    write_json(RP / "models" / "entity" / "rainbow_butterfly.geo.json", content.butterfly_geometry())
    write_json(RP / "entity" / "rainbow_butterfly.entity.json", client_entity_json())
    write_json(RP / "animations" / "rainbow_butterfly.animation.json", animation_json())
    write_json(RP / "render_controllers" / "rainbow_butterfly.render_controllers.json",
               render_controller_json())

    build_textures()
    build_atlases()
    build_blocks_json()
    build_language()

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for pack, folder in [(BP, "behavior_pack"), (RP, "resource_pack")]:
            for path in sorted(pack.rglob("*")):
                if path.is_file():
                    zf.write(path, f"{folder}/{path.relative_to(pack).as_posix()}")

    blocks = len(list((BP / "blocks").glob("*.json")))
    items = len(list((BP / "items").glob("*.json")))
    recipes = len(list((BP / "recipes").glob("*.json")))
    textures = len(list((RP / "textures").rglob("*.png")))
    print(f"built Rainbow Garden {VERSION}")
    print(f"  blocks: {blocks}, items: {items}, recipes: {recipes}, textures: {textures}")
    print(f"  behaviour pack: {BP}")
    print(f"  resource pack:  {RP}")
    print(f"  add-on:         {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
