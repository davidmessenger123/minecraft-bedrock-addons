"""
Build the Cogworks Bedrock add-on.

Outputs both packs, every model/geometry, the shared industrial texture atlas,
recipes, language files, Blockbench sources and the packaged .mcaddon.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

import content
import render

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
PREVIEWS = ROOT / "previews"
BLOCKBENCH = ROOT / "blockbench"
VERSION = (TOOLS / "VERSION").read_text(encoding="utf-8").strip()
VERSION_PARTS = [int(p) for p in VERSION.split(".")]
OUT = ROOT / f"Cogworks-{VERSION}.mcaddon"

BP_HEADER_UUID = "f5a4ed5a-1af3-40ea-8a96-ef7b8c0a4d10"
BP_DATA_UUID = "7b1b4f4d-5c3f-49d5-b356-1f9b2c7a10a2"
BP_SCRIPT_UUID = "d9a5de35-bbfa-4c58-9d93-2c8c0c4f7a13"
RP_HEADER_UUID = "1a9d1f88-e2a8-49b8-a6f2-a7d2ef5c1e44"
RP_RESOURCE_UUID = "c2fd6ba3-1c27-4bf6-9f35-3a8fbd0a1c55"

MIN_ENGINE = [1, 26, 60]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_png(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


def manifest(name, description, header_uuid, modules, dependencies=None):
    return {
        "format_version": 2,
        "header": {
            "name": name,
            "description": description,
            "uuid": header_uuid,
            "version": VERSION_PARTS,
            "min_engine_version": MIN_ENGINE,
        },
        "modules": modules,
        "dependencies": dependencies or [],
        "metadata": {"authors": ["OpenCode"], "license": "MIT"},
    }


def geometry_index():
    return content.block_geometries()


def write_geometry():
    texture = content.block_atlas()
    for key, geo in geometry_index().items():
        write_json(RP / "models" / "blocks" / f"{key}.geo.json", geo)
        bb = content.to_bbmodel(geo, texture, f"Cogworks {key.replace('_', ' ')}")
        write_json(BLOCKBENCH / "blocks" / f"{key}.bbmodel", bb)


def attachable_json(key: str, geometry: str) -> dict:
    animation = f"animation.cw.{key}"
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": f"cw:{key}",
                "materials": {
                    "default": "entity_alphatest",
                    "enchanted": "entity_alphatest_glint",
                },
                "textures": {
                    "default": "textures/blocks/cw_blocks",
                    "enchanted": "textures/misc/enchanted_item_glint",
                },
                "geometry": {"default": geometry},
                "animations": {
                    "hold_first_person": f"{animation}.hold_first_person",
                    "hold_third_person": f"{animation}.hold_third_person",
                },
                "scripts": {
                    "animate": [
                        {"hold_first_person": "context.is_first_person == 1.0"},
                        {"hold_third_person": "context.is_first_person == 0.0"},
                    ]
                },
                "render_controllers": ["controller.render.item_default"],
            }
        },
    }


def tool_animation(key: str) -> dict:
    animation = f"animation.cw.{key}"
    return {
        "format_version": "1.10.0",
        "animations": {
            f"{animation}.hold_first_person": {
                "loop": True,
                "bones": {
                    "tool": {
                        "position": [2, 25, -1],
                        "rotation": [58, -48, -44],
                        "scale": 0.8,
                    }
                },
            },
            f"{animation}.hold_third_person": {
                "loop": True,
                "bones": {
                    "tool": {
                        "position": [1, 22, 0],
                        "rotation": [0, 0, 0],
                        "scale": 0.9,
                    }
                },
            },
        },
    }


def write_tool_attachables():
    texture = content.block_atlas()
    for key, geo in content.tool_geometries().items():
        write_json(RP / "models" / "entity" / f"cw_{key}.geo.json", geo)
        write_json(RP / "attachables" / f"cw_{key}.json",
                   attachable_json(key, geo["minecraft:geometry"][0]["description"]["identifier"]))
        write_json(RP / "animations" / f"cw_{key}.animation.json", tool_animation(key))
        bb = content.to_bbmodel(geo, texture, f"Cogworks {key}")
        write_json(BLOCKBENCH / "tools" / f"{key}.bbmodel", bb)


def block_json(spec: content.BlockSpec) -> dict:
    description = {
        "identifier": f"cw:{spec.key}",
        "menu_category": {"category": spec.menu} if spec.menu else {},
    }
    if spec.state:
        description["states"] = {"cw:facing": ["north", "east", "south", "west"]}
    if spec.status_state:
        description.setdefault("states", {})["cw:status"] = ["idle", "working", "blocked"]
    if spec.curve_state:
        description.setdefault("states", {})["cw:curve"] = ["straight", "left", "right"]

    materials = {
        "*": {
            "texture": "cw_blocks",
            "render_method": "opaque",
            "face_dimming": True,
            "ambient_occlusion": True,
        }
    }
    if spec.curve_state:
        geometry = {
            "identifier": spec.geometry,
            "bone_visibility": {
                "straight": "q.block_state('cw:curve') == 'straight'",
                "left": "q.block_state('cw:curve') == 'left'",
                "right": "q.block_state('cw:curve') == 'right'",
            },
        }
        item_geometry = {
            "identifier": spec.geometry,
            "bone_visibility": {"straight": True, "left": False, "right": False},
        }
    else:
        geometry = spec.geometry
        item_geometry = spec.geometry
    components = {
        "minecraft:geometry": geometry,
        "minecraft:material_instances": materials,
        "minecraft:item_visual": {"geometry": item_geometry, "material_instances": materials},
        "minecraft:destructible_by_mining": {"seconds_to_destroy": spec.hardness},
        "minecraft:destructible_by_explosion": {"explosion_resistance": 4},
        "minecraft:light_emission": spec.light,
        "minecraft:light_dampening": 15,
        "minecraft:map_color": "#59616d",
        "minecraft:display_name": f"tile.cw:{spec.key}.name",
        "minecraft:loot": f"loot_tables/blocks/{spec.key}.json",
    }
    if spec.collision is not True:
        components["minecraft:collision_box"] = spec.collision
    if spec.dynamic:
        components["minecraft:block_entity"] = {"dynamic_properties": True}
    if spec.machine:
        components["cw:machine"] = {}
        components["minecraft:tick"] = {
            "interval_range": list(spec.tick_range),
            "looping": True,
        }
    if spec.state:
        components["minecraft:transformation"] = {"rotation": [0, 0, 0]}

    data = {
        "format_version": "1.26.60",
        "minecraft:block": {
            "description": description,
            "components": components,
        },
    }
    permutations = []
    if spec.state:
        permutations.extend([
            {
                "condition": "q.block_state('cw:facing') == 'east'",
                "components": {"minecraft:transformation": {"rotation": [0, 90, 0]}},
            },
            {
                "condition": "q.block_state('cw:facing') == 'south'",
                "components": {"minecraft:transformation": {"rotation": [0, 180, 0]}},
            },
            {
                "condition": "q.block_state('cw:facing') == 'west'",
                "components": {"minecraft:transformation": {"rotation": [0, 270, 0]}},
            },
        ])
    if spec.status_state:
        permutations.extend([
            {
                "condition": "q.block_state('cw:status') == 'working'",
                "components": {"minecraft:light_emission": 15},
            },
            {
                "condition": "q.block_state('cw:status') == 'blocked'",
                "components": {"minecraft:light_emission": 8},
            },
        ])
    if permutations:
        data["minecraft:block"]["permutations"] = permutations
    return data


def item_json(key, label, menu):
    components = {
        "minecraft:icon": {"textures": {"default": f"cw_{key}"}},
        "minecraft:display_name": {"value": f"item.cw:{key}.name"},
        "minecraft:max_stack_size": 64,
    }
    if menu == "equipment":
        components["minecraft:max_stack_size"] = 1
        components["minecraft:hand_equipped"] = True
        components["minecraft:durability"] = {"max_durability": 1200 if key in ("drill", "chainsaw") else 400}
    if key in ("drill", "chainsaw"):
        components["minecraft:digger"] = {
            "use_efficiency": True,
            "destroy_speeds": [
                {"block": {"tags": "query.any_tag('stone')"}, "speed": 12 if key == "drill" else 2},
                {"block": {"tags": "query.any_tag('wood')"}, "speed": 2 if key == "drill" else 14},
            ],
        }
    return {
        "format_version": "1.21.90",
        "minecraft:item": {
            "description": {"identifier": f"cw:{key}", "menu_category": {"category": menu}},
            "components": components,
        },
    }


def shaped(identifier, pattern, key, result, count=1):
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shaped": {
            "description": {"identifier": identifier},
            "tags": ["crafting_table"],
            "pattern": pattern,
            "key": {k: {"item": v} for k, v in key.items()},
            "result": {"item": result, "count": count},
        },
    }


def shapeless(identifier, ingredients, result, count=1):
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": identifier},
            "tags": ["crafting_table"],
            "ingredients": [{"item": i} for i in ingredients],
            "result": {"item": result, "count": count},
        },
    }


def build_recipes() -> None:
    recipes = {
        "gear": shaped("cw:gear_recipe", ["IGI", "G G", "IGI"], {"I": "minecraft:iron_ingot", "G": "minecraft:copper_ingot"}, "cw:gear", 2),
        "circuit": shapeless("cw:circuit_recipe", ["minecraft:redstone", "minecraft:redstone", "minecraft:redstone", "minecraft:redstone", "minecraft:gold_ingot"], "cw:circuit", 2),
        "motor": shapeless("cw:motor_recipe", ["cw:gear", "cw:gear", "cw:circuit", "minecraft:copper_ingot", "minecraft:copper_ingot", "minecraft:copper_ingot", "minecraft:copper_ingot"], "cw:motor", 1),
        "generator": shaped("cw:generator_recipe", ["ICI", "IFI", "ICI"], {"I": "minecraft:iron_ingot", "C": "minecraft:copper_ingot", "F": "minecraft:furnace"}, "cw:generator", 1),
        "conveyor": shaped("cw:conveyor_recipe", ["IGI", "GRG", "IGI"], {"I": "minecraft:iron_ingot", "G": "cw:gear", "R": "minecraft:redstone"}, "cw:conveyor", 4),
        "filter": shaped("cw:filter_recipe", ["IGI", "GCG", "IGI"], {"I": "minecraft:iron_ingot", "G": "cw:gear", "C": "cw:circuit"}, "cw:filter", 1),
        "splitter": shaped("cw:splitter_recipe", ["IGI", "G G", "IGI"], {"I": "minecraft:iron_ingot", "G": "cw:gear"}, "cw:splitter", 1),
        "merger": shaped("cw:merger_recipe", ["IGI", "G G", "IGI"], {"I": "minecraft:copper_ingot", "G": "cw:gear"}, "cw:merger", 1),
        "extractor": shaped("cw:extractor_recipe", ["ICI", "GBG", "ICI"], {"I": "minecraft:iron_ingot", "C": "cw:circuit", "G": "cw:gear", "B": "minecraft:barrel"}, "cw:extractor", 1),
        "assembler": shaped("cw:assembler_recipe", ["IGI", "CTC", "IGI"], {"I": "minecraft:iron_ingot", "G": "cw:gear", "C": "cw:circuit", "T": "minecraft:crafting_table"}, "cw:assembler", 1),
        "cable": shaped("cw:cable_recipe", ["CCC", "C C", "CCC"], {"C": "minecraft:copper_ingot"}, "cw:cable", 8),
        "battery": shaped("cw:battery_recipe", ["CRC", "RGR", "CRC"], {"C": "minecraft:copper_ingot", "R": "minecraft:redstone", "G": "cw:gear"}, "cw:battery", 1),
        "storage_core": shaped("cw:storage_core_recipe", ["ICI", "CBC", "ICI"], {"I": "minecraft:iron_ingot", "C": "cw:circuit", "B": "minecraft:barrel"}, "cw:storage_core", 1),
        "storage_extension": shaped("cw:storage_extension_recipe", ["ICI", "CBC", "ICI"], {"I": "minecraft:iron_ingot", "C": "minecraft:copper_ingot", "B": "minecraft:barrel"}, "cw:storage_extension", 1),
        "storage_terminal": shaped("cw:storage_terminal_recipe", ["IGI", "CBC", "IGI"], {"I": "minecraft:iron_ingot", "G": "cw:gear", "C": "cw:circuit", "B": "minecraft:barrel"}, "cw:storage_terminal", 1),
        "storage_port": shaped("cw:storage_port_recipe", ["ICI", "CBC", "ICI"], {"I": "minecraft:iron_ingot", "C": "cw:circuit", "B": "minecraft:barrel"}, "cw:storage_port", 1),
        "quarry": shaped("cw:quarry_recipe", ["IMI", "GQG", "IMI"], {"I": "minecraft:iron_block", "M": "cw:motor", "G": "cw:gear", "Q": "cw:circuit"}, "cw:quarry", 1),
        "drill": shaped("cw:drill_recipe", [" I ", "IGI", " M "], {"I": "minecraft:iron_ingot", "G": "cw:gear", "M": "cw:motor"}, "cw:drill", 1),
        "chainsaw": shaped("cw:chainsaw_recipe", [" II", "IGI", " M "], {"I": "minecraft:iron_ingot", "G": "cw:gear", "M": "cw:motor"}, "cw:chainsaw", 1),
        "wrench": shaped("cw:wrench_recipe", ["I I", " C ", " I "], {"I": "minecraft:iron_ingot", "C": "minecraft:copper_ingot"}, "cw:wrench", 1),
        "surveyor": shapeless("cw:surveyor_recipe", ["minecraft:copper_ingot", "minecraft:copper_ingot", "minecraft:redstone", "minecraft:stick"], "cw:surveyor", 1),
    }
    for name, data in recipes.items():
        write_json(BP / "recipes" / f"{name}.json", data)


LANG = {
    "pack.name": "Cogworks",
    "pack.description": "Automated crafting, power, conveyors, expanded storage and industrial tools.",
    "cw.ui.storage": "Storage Core",
    "cw.ui.assembler": "Crafting Assembler",
    "cw.ui.generator": "Coal Generator",
    "cw.ui.battery": "Battery Bank",
    "cw.ui.quarry": "Quarry Controller",
    "cw.ui.deposit": "Deposit held item",
    "cw.ui.full": "Storage is full.",
    "cw.ui.empty": "No stored items.",
    "cw.ui.energy": "Energy",
    "cw.ui.no_energy": "No power connected.",
    "cw.ui.area": "Area",
    "cw.ui.active": "Active",
    "cw.ui.paused": "Paused",
    "cw.ui.start": "Start quarry",
    "cw.ui.stop": "Pause quarry",
    "cw.ui.scan": "Show area",
    "cw.msg.corner_a": "Quarry corner A set.",
    "cw.msg.corner_b": "Quarry corner B set.",
    "cw.msg.area_set": "Quarry area set. Connect storage and power.",
    "cw.msg.area_too_big": "The quarry area is too large (max 32x32x32).",
    "cw.msg.no_area": "Use the Quarry Surveyor on two corners first.",
    "cw.msg.wrench": "Conveyor direction: {direction}",
    "cw.msg.no_room": "The target has no room for that item.",
    "cw.msg.fuel": "Fuel added.",
    "cw.msg.no_fuel": "The generator only accepts coal, charcoal or coal blocks.",
    "cw.msg.deposited": "Deposited {count} {item}.",
    "cw.msg.withdrew": "Withdrew {count} {item}.",
    "cw.msg.inventory_full": "Your inventory is full.",
    "cw.msg.quarry_started": "Quarry started.",
    "cw.msg.quarry_stopped": "Quarry paused.",
    "cw.msg.drill": "The drill needs stone or ore.",
    "cw.msg.chainsaw": "The chainsaw needs logs.",
    "cw.msg.machine_input": "Inserted {count} {item}.",
    "cw.msg.no_accept": "This machine does not accept that item.",
    "cw.msg.recipe": "Assembler recipes: planks, sticks, iron, gold, copper, gear, circuit, motor.",
}

BLOCK_LANG = {spec.key: spec.label for spec in content.BLOCKS}
ITEM_LANG = {key: label for key, (label, _) in content.ITEMS.items()}


def build_language():
    lines = [
        f"pack.name={LANG['pack.name']}",
        f"pack.description={LANG['pack.description']}",
        "",
    ]
    for key in LANG:
        if key.startswith("cw.ui.") or key.startswith("cw.msg."):
            lines.append(f"{key}={LANG[key]}")
    for key, label in BLOCK_LANG.items():
        lines.append(f"tile.cw:{key}.name={label}")
        lines.append(f"tile.cw.{key}.name={label}")
    for key, label in ITEM_LANG.items():
        lines.append(f"item.cw:{key}.name={label}")
        lines.append(f"item.cw.{key}.name={label}")
    text = "\n".join(lines) + "\n"
    for pack in (BP, RP):
        (pack / "texts").mkdir(parents=True, exist_ok=True)
        (pack / "texts" / "en_US.lang").write_text(text, encoding="utf-8")
        write_json(pack / "texts" / "languages.json", ["en_US"])


def build_packs():
    bp_manifest = manifest(
        "Cogworks Behaviour Pack",
        "Automated crafting, power, conveyors, storage and quarrying.",
        BP_HEADER_UUID,
        [
            {"description": "Cogworks data", "type": "data", "uuid": BP_DATA_UUID, "version": VERSION_PARTS},
            {"description": "Cogworks machines", "type": "script", "language": "javascript",
             "uuid": BP_SCRIPT_UUID, "entry": "scripts/main.js", "version": VERSION_PARTS},
        ],
        [
            {"module_name": "@minecraft/server", "version": "2.0.0"},
            {"module_name": "@minecraft/server-ui", "version": "2.0.0"},
        ],
    )
    rp_manifest = manifest(
        "Cogworks Resource Pack",
        "Models, textures and UI strings for Cogworks.",
        RP_HEADER_UUID,
        [{"description": "Cogworks resources", "type": "resources", "uuid": RP_RESOURCE_UUID, "version": VERSION_PARTS}],
        [{"uuid": BP_HEADER_UUID, "version": VERSION_PARTS}],
    )
    write_json(BP / "manifest.json", bp_manifest)
    write_json(RP / "manifest.json", rp_manifest)
    (BP / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(TOOLS / "main.js", BP / "scripts" / "main.js")


def build_blocks():
    for spec in content.BLOCKS:
        write_json(BP / "blocks" / f"{spec.key}.json", block_json(spec))
        write_json(BP / "loot_tables" / "blocks" / f"{spec.key}.json", {
            "pools": [{
                "rolls": 1,
                "entries": [{
                    "type": "item",
                    "name": f"cw:{spec.key}",
                    "weight": 1,
                }],
            }],
        })


def build_items():
    for key, (label, menu) in content.ITEMS.items():
        write_json(BP / "items" / f"{key}.json", item_json(key, label, menu))


def build_resources():
    atlas = content.block_atlas()
    save_png(RP / "textures" / "blocks" / "cw_blocks.png", atlas)
    for key, image in content.item_icons().items():
        save_png(RP / "textures" / "items" / f"cw_{key}.png", image)
    save_png(RP / "pack_icon.png", content.pack_icon())
    save_png(BP / "pack_icon.png", content.pack_icon())
    write_json(RP / "textures" / "terrain_texture.json", {
        "resource_pack_name": "cogworks",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {"cw_blocks": {"textures": "textures/blocks/cw_blocks"}},
    })
    write_json(RP / "textures" / "item_texture.json", {
        "resource_pack_name": "cogworks",
        "texture_name": "atlas.items",
        "texture_data": {
            f"cw_{key}": {"textures": f"textures/items/cw_{key}"} for key in content.ITEMS
        },
    })
    write_json(RP / "textures" / "textures_list.json", [
        "textures/blocks/cw_blocks",
        *[f"textures/items/cw_{key}" for key in content.ITEMS],
    ])
    write_json(RP / "blocks.json", {f"cw:{spec.key}": {"sound": spec.sound} for spec in content.BLOCKS})
    write_geometry()
    write_tool_attachables()


def build_extras():
    # A simple texture contact sheet keeps the industrial palette visible in
    # the repository without requiring a full 3D preview renderer.
    atlas = content.block_atlas()
    thumbs = []
    names = ["steel", "copper", "brass", "dark", "energy", "belt", "wood", "warning", "rubber", "light"]
    for i, name in enumerate(names):
        x = (i % 8) * content.TILE
        y = (i // 8) * content.TILE
        tile = atlas.crop((x, y, x + content.TILE, y + content.TILE)).resize((96, 96), Image.Resampling.NEAREST)
        thumbs.append((name, tile))
    sheet = Image.new("RGB", (8 * 112 + 24, 2 * 142 + 70), (23, 27, 33))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 18), "Cogworks material atlas", fill=(241, 232, 209))
    for i, (name, tile) in enumerate(thumbs):
        x = 18 + (i % 8) * 112
        y = 52 + (i // 8) * 142
        sheet.paste(tile, (x, y))
        draw.text((x, y + 104), name, fill=(184, 194, 202))
    save_png(PREVIEWS / "materials.png", sheet)
    render.build_model_sheet(PREVIEWS / "models.png")
    render.build_tool_sheet(PREVIEWS / "tools.png")
    render.build_belt_sheet(PREVIEWS / "belt_shapes.png")


def build_addon():
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, prefix in ((BP, "Cogworks_BP"), (RP, "Cogworks_RP")):
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    z.write(path, f"{prefix}/{path.relative_to(folder).as_posix()}")


def main():
    if ROOT.exists():
        for directory in ("behavior_pack", "resource_pack"):
            shutil.rmtree(ROOT / directory, ignore_errors=True)
    BP.mkdir(parents=True)
    RP.mkdir(parents=True)
    PREVIEWS.mkdir(exist_ok=True)
    BLOCKBENCH.mkdir(exist_ok=True)
    build_packs()
    build_blocks()
    build_items()
    build_recipes()
    build_language()
    build_resources()
    build_extras()
    build_addon()
    print(f"built Cogworks {VERSION}")
    print(f"  blocks: {len(content.BLOCKS)}, items: {len(content.ITEMS)}")
    print(f"  add-on: {OUT}")


if __name__ == "__main__":
    main()
