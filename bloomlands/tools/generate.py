"""
Build the Bloomlands Bedrock add-on.

This script writes both packs from the content module: textures, block and item
definitions, equations, recipes, loot tables, the custom dimension and biome,
fogs, particles, language files and the packaged .mcaddon.  The Blockbench
sources and preview images are produced by ``render.py``.

Run it with a Python that has Pillow installed:

    python tools/generate.py
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

import content

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
PREVIEWS = ROOT / "previews"
BLOCKBENCH = ROOT / "blockbench"
VERSION = (TOOLS / "VERSION").read_text(encoding="utf-8").strip()
VERSION_PARTS = [int(part) for part in VERSION.split(".")]
OUT = ROOT / f"Bloomlands-{VERSION}.mcaddon"

BP_HEADER_UUID = "0f5382a4-3c41-59e6-90c5-62335d404872"
BP_DATA_UUID = "a5872a02-3791-5906-91da-cef1bd3f3c19"
BP_SCRIPT_UUID = "16282ad5-85ba-53ff-a7e1-e44ef299439d"
RP_HEADER_UUID = "1c0cc0a0-872d-559e-8732-b0845267f916"
RP_RESOURCES_UUID = "1bf7a589-655c-550c-88e6-23cd53582e98"

MIN_ENGINE = [1, 26, 60]
DIMENSION_ID = "bl:bloomlands"
DIMENSION_FILE_VERSION = "1.26.60"
CLIENT_BIOME_VERSION = "1.21.130"

REGIONS = {
    "meadow": {
        "label": "Sunpetal Meadow",
        "fog": "bl:bloomlands_meadow",
        "color": "#f7d6e4",
        "start": 30,
        "end": 140,
        "water": "#3f9f9a",
    },
    "canopy": {
        "label": "Whispering Canopy",
        "fog": "bl:bloomlands_canopy",
        "color": "#183426",
        "start": 4,
        "end": 42,
        "water": "#123b35",
    },
    "garden": {
        "label": "Giant's Garden",
        "fog": "bl:bloomlands_garden",
        "color": "#ffe0ee",
        "start": 24,
        "end": 120,
        "water": "#4da9a0",
    },
    "hills": {
        "label": "Petal Hills",
        "fog": "bl:bloomlands_hills",
        "color": "#d8eaff",
        "start": 30,
        "end": 150,
        "water": "#57a9b2",
    },
    "pool": {
        "label": "Mirror Pool",
        "fog": "bl:bloomlands_pool",
        "color": "#c7f5ee",
        "start": 20,
        "end": 96,
        "water": "#3aa49d",
    },
    "edge": {
        "label": "Bloomlands Edge",
        "fog": "bl:bloomlands_edge",
        "color": "#e7d7ff",
        "start": 18,
        "end": 100,
        "water": "#578fa8",
    },
}


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_png(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


def manifest(name: str, description: str, header_uuid: str, modules: list[dict],
             dependencies: list[dict] | None = None) -> dict:
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
        "metadata": {
            "authors": ["OpenCode"],
            "license": "MIT",
        },
    }


# ---------------------------------------------------------------------------
# Textures and texture maps
# ---------------------------------------------------------------------------


def build_textures() -> dict[str, Image.Image]:
    textures = content.block_textures()
    for key, image in textures.items():
        save_png(RP / "textures" / "blocks" / f"{key}.png", image)

    portal_icon = content.portal_item_icon()
    save_png(RP / "textures" / "items" / "bloom_portal.png", portal_icon)

    for spec in content.entity_specs():
        save_png(RP / "textures" / "entity" / f"{spec.key}.png", spec.texture)

    save_png(RP / "textures" / "particle" / "bloom_particles.png", content.particle_atlas())

    icon = content.pack_icon()
    save_png(BP / "pack_icon.png", icon)
    save_png(RP / "pack_icon.png", icon)
    save_png(PREVIEWS / "pack_icon.png", icon)
    return textures


def build_atlases() -> None:
    terrain = {
        "resource_pack_name": "bloomlands",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {},
    }
    for key, path in content.terrain_texture_keys().items():
        terrain["texture_data"][key] = {"textures": path}
    write_json(RP / "textures" / "terrain_texture.json", terrain)

    item = {
        "resource_pack_name": "bloomlands",
        "texture_name": "atlas.items",
        "texture_data": {
            "bloom_portal": {"textures": "textures/items/bloom_portal"},
        },
    }
    write_json(RP / "textures" / "item_texture.json", item)

    textures_list = sorted(set(content.terrain_texture_keys().values()))
    textures_list.append("textures/items/bloom_portal")
    textures_list.extend(f"textures/entity/{spec.key}" for spec in content.entity_specs())
    textures_list.append("textures/particle/bloom_particles")
    write_json(RP / "textures" / "textures_list.json", sorted(set(textures_list)))

    write_json(
        RP / "textures" / "flipbook_textures.json",
        [
            {
                "flipbook_texture": "textures/blocks/bl_bloomheart",
                "atlas_tile": "bl_bloomheart",
                "ticks_per_frame": 5,
                "blend_frames": True,
                "frames": [0, 1, 2, 3],
            },
            {
                "flipbook_texture": "textures/blocks/bl_rainbow_portal",
                "atlas_tile": "bl_rainbow_portal",
                "ticks_per_frame": 3,
                "blend_frames": True,
                "frames": list(range(32)),
            },
        ],
    )

    sounds = {f"bl:{spec.key}": {"sound": spec.sound} for spec in content.BLOCK_SPECS}
    write_json(RP / "blocks.json", sounds)


# ---------------------------------------------------------------------------
# Blocks, items, recipes and loot
# ---------------------------------------------------------------------------


def block_json(spec: content.BlockSpec) -> dict:
    mats = content.block_material_instances(spec)
    components = {
        "minecraft:geometry": spec.geometry,
        "minecraft:material_instances": mats,
        "minecraft:item_visual": {
            "geometry": spec.geometry,
            "material_instances": mats,
        },
        "minecraft:destructible_by_mining": {"seconds_to_destroy": spec.hardness},
        "minecraft:destructible_by_explosion": (
            {"explosion_resistance": 3.0} if spec.kind == "full" else False
        ),
        "minecraft:destruction_particles": {
            "texture": spec.texture,
            "particle_count": spec.particle_count,
        },
        "minecraft:light_emission": spec.light,
        "minecraft:light_dampening": spec.dampening,
        "minecraft:map_color": spec.map_color,
        "minecraft:display_name": f"tile.bl:{spec.key}.name",
        "minecraft:collision_box": spec.collision,
        "minecraft:loot": f"loot_tables/blocks/{spec.key}.json",
    }
    if spec.selection is not None:
        origin, size = spec.selection
        components["minecraft:selection_box"] = {"origin": list(origin), "size": list(size)}
    if spec.flammable:
        components["minecraft:flammable"] = {
            "catch_chance_modifier": 5,
            "destroy_chance_modifier": 20,
        }
    if spec.placement:
        components["minecraft:placement_filter"] = {
            "conditions": [
                {
                    "allowed_faces": ["up"],
                    "block_filter": list(spec.placement),
                }
            ]
        }
    if not spec.drop_item:
        components.pop("minecraft:loot", None)
    description: dict = {"identifier": f"bl:{spec.key}"}
    if spec.menu is not None:
        description["menu_category"] = {"category": spec.menu}
    return {
        "format_version": "1.21.90",
        "minecraft:block": {
            "description": description,
            "components": components,
        },
    }


def build_blocks() -> None:
    for spec in content.BLOCK_SPECS:
        write_json(BP / "blocks" / f"{spec.key}.json", block_json(spec))
        if not spec.drop_item:
            continue
        write_json(
            BP / "loot_tables" / "blocks" / f"{spec.key}.json",
            {
                "pools": [
                    {
                        "rolls": 1,
                        "entries": [
                            {
                                "type": "item",
                                "name": f"bl:{spec.key}",
                                "weight": 1,
                            }
                        ],
                    }
                ]
            },
        )


def portal_item_json() -> dict:
    return {
        "format_version": "1.21.90",
        "minecraft:item": {
            "description": {
                "identifier": "bl:bloom_portal",
                "menu_category": {"category": "nature"},
            },
            "components": {
                "minecraft:icon": {"textures": {"default": "bloom_portal"}},
                "minecraft:display_name": {"value": "item.bl:bloom_portal.name"},
                "minecraft:max_stack_size": 16,
                "minecraft:glint": True,
                "minecraft:hand_equipped": True,
            },
        },
    }


def recipe_shaped(identifier: str, pattern: list[str], key: dict, result: str, count: int = 1) -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shaped": {
            "description": {"identifier": identifier},
            "tags": ["crafting_table"],
            "pattern": pattern,
            "key": key,
            "result": {"item": result, "count": count},
        },
    }


def recipe_shapeless(identifier: str, ingredients: list[str], result: str, count: int = 1) -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": identifier},
            "tags": ["crafting_table"],
            "ingredients": [{"item": item} for item in ingredients],
            "result": {"item": result, "count": count},
        },
    }


def build_recipes() -> None:
    recipes = {
        "bloom_portal": recipe_shaped(
            "bl:bloom_portal_recipe",
            ["GFG", "FAF", "GFG"],
            {
                "G": {"item": "minecraft:grass_block"},
                "F": {"item": "minecraft:poppy"},
                "A": {"item": "minecraft:amethyst_block"},
            },
            "bl:bloom_portal",
        ),
        "portal_flower": recipe_shapeless(
            "bl:portal_flower_recipe",
            ["bl:lumen_bell", "bl:rosequartz", "bl:sunpetal", "minecraft:glowstone_dust"],
            "bl:portal_flower",
            2,
        ),
        "bloomwood_planks": recipe_shapeless(
            "bl:bloomwood_planks_recipe", ["bl:bloomwood_log"], "bl:bloomwood_planks", 4
        ),
        "petal_path": recipe_shapeless(
            "bl:petal_path_recipe",
            ["bl:bloom_dirt", "bl:sunpetal", "bl:rosequartz"],
            "bl:petal_path",
            2,
        ),
        "petal_grass": recipe_shapeless(
            "bl:petal_grass_recipe",
            ["bl:bloom_dirt", "bl:sunpetal", "bl:dewgrass"],
            "bl:petal_grass",
        ),
    }
    for name, data in recipes.items():
        write_json(BP / "recipes" / f"{name}.json", data)


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


def entity_behavior(spec: content.EntitySpec) -> dict:
    family = [spec.identifier, spec.family, "mob"]
    if spec.flying:
        family.insert(2, "ambient")
    else:
        family.insert(2, "animal")

    components: dict = {
        "minecraft:type_family": {"family": family},
        "minecraft:health": {"value": spec.health, "max": spec.health},
        "minecraft:collision_box": {"width": spec.width, "height": spec.height},
        "minecraft:movement": {"value": spec.movement},
        "minecraft:breathable": {
            "breathes_air": True,
            "breathes_water": False,
            "total_supply": 15,
            "suffocate_time": 0,
        },
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.look_at_player": {
            "priority": 4,
            "look_distance": 8.0,
            "probability": 0.08,
        },
        "minecraft:behavior.random_look_around": {"priority": 5},
        "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.35},
        "minecraft:damage_sensor": {
            "triggers": [{"cause": "fall", "deals_damage": "no"}]
        },
        "minecraft:persistent": {},
        "minecraft:nameable": {},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {
            "value": 1.0 if spec.key == "dewdrop_snail" else 0.35,
            "max": 1.0,
        },
        "minecraft:conditional_bandwidth_optimization": {},
        "minecraft:loot": f"loot_tables/entities/{spec.key}.json",
    }

    if spec.flying:
        components.update(
            {
                "minecraft:movement.hover": {},
                "minecraft:navigation.hover": {
                    "can_path_from_air": True,
                    "can_path_over_water": True,
                    "avoid_water": True,
                    "can_sink": False,
                },
                "minecraft:can_fly": {},
                "minecraft:flying_speed": {"value": 0.2},
                "minecraft:physics": {"has_gravity": False, "has_collision": False},
                "minecraft:behavior.random_hover": {
                    "priority": 2,
                    "hover_height": [2, 5],
                    "y_dist": 8,
                    "interval": 1,
                    "xz_dist": 10,
                    "y_offset": -1,
                    "speed_multiplier": 1.0,
                },
            }
        )
    else:
        components.update(
            {
                "minecraft:movement.basic": {},
                "minecraft:navigation.walk": {
                    "can_path_over_water": False,
                    "avoid_water": True,
                    "avoid_damage_blocks": True,
                },
                "minecraft:jump.static": {},
                "minecraft:physics": {"has_gravity": True, "has_collision": True},
                "minecraft:behavior.random_stroll": {
                    "priority": 2,
                    "speed_multiplier": 0.65 if spec.key == "dewdrop_snail" else 1.0,
                    "xz_dist": 8,
                    "interval": 200 if spec.key == "dewdrop_snail" else 120,
                },
            }
        )

    return {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {
                "identifier": spec.identifier,
                "spawn_category": "ambient" if spec.flying else "creature",
                "is_spawnable": True,
                "is_summonable": True,
                "is_experimental": False,
            },
            "components": components,
        },
    }


def entity_loot(spec: content.EntitySpec) -> dict:
    drops = {
        "petalwing": "minecraft:glowstone_dust",
        "mossling": "minecraft:moss_block",
        "dewdrop_snail": "minecraft:slime_ball",
    }
    return {
        "pools": [
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "item",
                        "name": drops[spec.key],
                        "weight": 1,
                        "functions": [
                            {
                                "function": "set_count",
                                "count": {"min": 0, "max": 1},
                            }
                        ],
                    }
                ],
            }
        ]
    }


def client_entity(spec: content.EntitySpec) -> dict:
    animations = {}
    for full_name in spec.animations.get("animations", {}):
        animations[full_name.split(".")[-1]] = full_name
    if spec.controller:
        animations["controller"] = spec.controller
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": spec.identifier,
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": f"textures/entity/{spec.key}"},
                "geometry": {"default": spec.geometry_id},
                "animations": animations,
                "scripts": {"animate": spec.animate},
                "render_controllers": ["controller.render.bl.bloomling"],
                "spawn_egg": {
                    "base_color": spec.egg_base,
                    "overlay_color": spec.egg_overlay,
                },
                "enable_attachables": False,
            }
        },
    }


def spawn_rules(spec: content.EntitySpec) -> dict:
    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {
                "identifier": spec.identifier,
                "population_control": "ambient" if spec.flying else "animal",
            },
            "conditions": [
                {
                    "minecraft:spawns_on_surface": {},
                    "minecraft:brightness_filter": {
                        "min": 8 if spec.flying else 4,
                        "max": 15,
                        "adjust_for_weather": False,
                    },
                    "minecraft:weight": {"default": spec.spawn_weight},
                    "minecraft:herd": {
                        "min_size": spec.spawn_group_min,
                        "max_size": spec.spawn_group_max,
                    },
                    "minecraft:density_limit": {"surface": 4 if spec.flying else 5},
                    "minecraft:biome_filter": {
                        "test": "has_biome_tag",
                        "operator": "==",
                        "value": "bloomlands",
                    },
                }
            ],
        },
    }


def build_entities() -> None:
    for spec in content.entity_specs():
        write_json(BP / "entities" / f"{spec.key}.json", entity_behavior(spec))
        write_json(BP / "loot_tables" / "entities" / f"{spec.key}.json", entity_loot(spec))
        write_json(BP / "spawn_rules" / f"{spec.key}.json", spawn_rules(spec))
        write_json(RP / "entity" / f"{spec.key}.entity.json", client_entity(spec))
        write_json(RP / "models" / "entity" / f"{spec.key}.geo.json", spec.geometry)
        write_json(RP / "animations" / f"{spec.key}.animation.json", spec.animations)
        if spec.controller_json:
            write_json(
                RP / "animation_controllers" / f"{spec.key}.animation_controllers.json",
                spec.controller_json,
            )

    write_json(
        RP / "render_controllers" / "bloomling.render_controllers.json",
        {
            "format_version": "1.10.0",
            "render_controllers": {
                "controller.render.bl.bloomling": {
                    "geometry": "Geometry.default",
                    "materials": [{"*": "Material.default"}],
                    "textures": ["Texture.default"],
                }
            },
        },
    )


# ---------------------------------------------------------------------------
# Dimension, biome, fog and particles
# ---------------------------------------------------------------------------


def build_dimension() -> None:
    write_json(
        BP / "dimensions" / "bloomlands.json",
        {
            "format_version": DIMENSION_FILE_VERSION,
            "minecraft:dimension": {
                "description": {"identifier": DIMENSION_ID},
                "components": {
                    "minecraft:generation": {"generator_type": "void"},
                    "minecraft:dimension_height": {"min_y": 0, "height_range": 256},
                    "minecraft:default_biome": {"biome": "bl:bloomlands"},
                },
            },
        },
    )

    write_json(
        BP / "biomes" / "bloomlands.biome.json",
        {
            "format_version": DIMENSION_FILE_VERSION,
            "minecraft:biome": {
                "description": {"identifier": "bl:bloomlands"},
                "components": {
                    "minecraft:climate": {"temperature": 0.8, "downfall": 0.7},
                    "minecraft:creature_spawn_probability": {"probability": 0.03},
                    "minecraft:humidity": {"is_humid": True},
                    "minecraft:tags": {
                        "tags": ["animal", "bloomlands", "bl:bloomlands"]
                    },
                },
            },
        },
    )

    write_json(
        RP / "biomes" / "bloomlands.client_biome.json",
        {
            "format_version": CLIENT_BIOME_VERSION,
            "minecraft:client_biome": {
                "description": {"identifier": "bl:bloomlands"},
                "components": {
                    "minecraft:sky_color": {"sky_color": "#a8d8ff"},
                    "minecraft:fog_appearance": {"fog_identifier": "bl:bloomlands_air"},
                    "minecraft:water_appearance": {
                        "surface_color": "#5fc7c0",
                        "surface_opacity": 0.72,
                    },
                    "minecraft:grass_appearance": {"color": "#8fd36f"},
                    "minecraft:foliage_appearance": {"color": "#75c45f"},
                },
            },
        },
    )


def fog_json(identifier: str, color: str, start: float, end: float, water: str) -> dict:
    return {
        "format_version": "1.16.100",
        "minecraft:fog_settings": {
            "description": {"identifier": identifier},
            "distance": {
                "air": {
                    "fog_start": start,
                    "fog_end": end,
                    "fog_color": color,
                    "render_distance_type": "fixed",
                },
                "water": {
                    "fog_start": 2,
                    "fog_end": 24,
                    "fog_color": water,
                    "render_distance_type": "fixed",
                },
            },
        },
    }


def build_fogs() -> None:
    base = fog_json("bl:bloomlands_air", "#f7d6e4", 30, 140, "#3f9f9a")
    write_json(RP / "fogs" / "bloomlands_air.json", base)
    for region in REGIONS.values():
        write_json(
            RP / "fogs" / f"{region['fog'].split(':')[1]}.json",
            fog_json(region["fog"], region["color"], region["start"], region["end"], region["water"]),
        )


def particle(
    identifier: str,
    material: str,
    uv_xy: tuple[int, int],
    *,
    lifetime: tuple[float, float] = (2.0, 4.0),
    speed: str | float = 0.2,
    size: str | float = 0.08,
    gradient: list[list[float]] | None = None,
    emitter: dict | None = None,
    shape: dict | None = None,
    acceleration: list[float] | None = None,
    drag: float = 1.0,
    spin: bool = False,
    lighting: bool = False,
    local_space: bool = False,
) -> dict:
    components: dict = {}
    if local_space:
        components["minecraft:emitter_local_space"] = {
            "position": True,
            "rotation": False,
            "velocity": True,
        }
    components.update(emitter or {
        "minecraft:emitter_rate_steady": {"spawn_rate": 3, "max_particles": 16},
        "minecraft:emitter_lifetime_looping": {"active_time": 2.0, "sleep_time": 0.01},
    })
    shape_data = shape or {
        "offset": [0, 0, 0],
        "direction": [0, 1, 0],
    }
    if shape_data.get("shape") == "sphere" or "radius" in shape_data:
        sphere = {key: value for key, value in shape_data.items() if key != "shape"}
        components["minecraft:emitter_shape_sphere"] = sphere
    else:
        components["minecraft:emitter_shape_point"] = shape_data
    components["minecraft:particle_lifetime_expression"] = {
        "max_lifetime": f"math.random({lifetime[0]}, {lifetime[1]})"
    }
    components["minecraft:particle_initial_speed"] = speed
    dynamic: dict = {"linear_drag_coefficient": drag}
    if acceleration:
        dynamic["linear_acceleration"] = acceleration
    components["minecraft:particle_motion_dynamic"] = dynamic
    components["minecraft:particle_appearance_billboard"] = {
        "size": [size, size] if not isinstance(size, str) else [size, size],
        "facing_camera_mode": "lookat_xyz",
        "uv": {
            "texture_width": 64,
            "texture_height": 64,
            "uv": [uv_xy[0], uv_xy[1]],
            "uv_size": [16, 16],
        },
    }
    if spin:
        components["minecraft:particle_initial_spin"] = {
            "rotation": "math.random(0, 360)",
            "rotation_rate": "math.random(-90, 90)",
        }
    if gradient:
        components["minecraft:particle_appearance_tinting"] = {
            "color": {
                "interpolant": "variable.particle_age / variable.particle_lifetime",
                "gradient": gradient,
            }
        }
    if lighting:
        components["minecraft:particle_appearance_lighting"] = {}
    return {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": identifier,
                "basic_render_parameters": {
                    "material": material,
                    "texture": "textures/particle/bloom_particles",
                },
            },
            "components": components,
        },
    }


def build_particles() -> None:
    particles = {
        "portal_aura": particle(
            "bl:portal_aura",
            "particles_blend",
            (16, 16),
            lifetime=(1.5, 3.0),
            speed=0.25,
            size="math.random(0.05, 0.11)",
            gradient=[
                [1.0, 0.55, 0.62, 0.95],
                [1.0, 0.88, 0.42, 0.78],
                [0.52, 0.95, 0.72, 0.58],
                [0.52, 0.78, 1.0, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_steady": {"spawn_rate": 5, "max_particles": 28},
                "minecraft:emitter_lifetime_looping": {"active_time": 2.0, "sleep_time": 0.01},
            },
            shape={
                "offset": [0, 0, 0],
                "radius": 0.7,
                "direction": "outwards",
                "shape": "sphere",
            },
            acceleration=[0, 0.25, 0],
            drag=1.1,
        ),
        "portal_charge": particle(
            "bl:portal_charge",
            "particles_add",
            (16, 0),
            lifetime=(0.8, 1.8),
            speed="math.random(0.4, 1.4)",
            size="math.random(0.06, 0.16)",
            gradient=[
                [1.0, 0.95, 0.7, 1.0],
                [1.0, 0.75, 0.86, 0.7],
                [1.0, 0.8, 1.0, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_instant": {"num_particles": 36},
                "minecraft:emitter_lifetime_once": {"active_time": 0.1},
            },
            shape={
                "offset": [0, 0, 0],
                "radius": 0.45,
                "direction": "outwards",
                "shape": "sphere",
            },
            acceleration=[0, 0.8, 0],
            drag=0.9,
            spin=True,
        ),
        "portal_burst": particle(
            "bl:portal_burst",
            "particles_alpha",
            (0, 0),
            lifetime=(1.8, 3.2),
            speed="math.random(0.8, 2.6)",
            size="math.random(0.08, 0.2)",
            gradient=[
                [1.0, 0.8, 0.9, 1.0],
                [1.0, 0.55, 0.75, 1.0],
                [0.95, 0.7, 1.0, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_instant": {"num_particles": 44},
                "minecraft:emitter_lifetime_once": {"active_time": 0.1},
            },
            shape={
                "offset": [0, 0, 0],
                "radius": 0.55,
                "direction": "outwards",
                "shape": "sphere",
            },
            acceleration=[0, -1.5, 0],
            drag=0.75,
            spin=True,
        ),
        "petal_mote": particle(
            "bl:petal_mote",
            "particles_alpha",
            (0, 0),
            lifetime=(4.0, 7.0),
            speed="math.random(0.05, 0.25)",
            size="math.random(0.05, 0.12)",
            gradient=[
                [1.0, 0.75, 0.88, 0.0],
                [1.0, 0.85, 0.93, 0.9],
                [0.95, 0.6, 0.8, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_steady": {"spawn_rate": 1, "max_particles": 8},
                "minecraft:emitter_lifetime_looping": {"active_time": 2.0, "sleep_time": 0.01},
            },
            acceleration=[0, -0.02, 0],
            drag=0.4,
            spin=True,
            lighting=True,
        ),
        "pollen": particle(
            "bl:pollen",
            "particles_alpha",
            (48, 0),
            lifetime=(3.0, 6.0),
            speed="math.random(0.05, 0.3)",
            size="math.random(0.03, 0.07)",
            gradient=[
                [1.0, 0.9, 0.5, 0.0],
                [1.0, 0.95, 0.65, 0.9],
                [1.0, 0.85, 0.4, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_steady": {"spawn_rate": 2, "max_particles": 14},
                "minecraft:emitter_lifetime_looping": {"active_time": 2.0, "sleep_time": 0.01},
            },
            acceleration=[0, 0.03, 0],
            drag=0.5,
            lighting=True,
        ),
        "firefly": particle(
            "bl:firefly",
            "particles_blend",
            (32, 0),
            lifetime=(3.0, 6.0),
            speed="math.random(0.02, 0.15)",
            size="math.random(0.05, 0.1)",
            gradient=[
                [0.8, 1.0, 0.65, 0.0],
                [0.85, 1.0, 0.7, 1.0],
                [0.6, 0.95, 0.5, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_steady": {"spawn_rate": 1, "max_particles": 10},
                "minecraft:emitter_lifetime_looping": {"active_time": 3.0, "sleep_time": 0.01},
            },
            acceleration=[0, 0.02, 0],
            drag=0.3,
        ),
        "canopy_mote": particle(
            "bl:canopy_mote",
            "particles_blend",
            (32, 16),
            lifetime=(4.0, 8.0),
            speed="math.random(0.02, 0.12)",
            size="math.random(0.04, 0.09)",
            gradient=[
                [0.7, 1.0, 0.7, 0.0],
                [0.75, 1.0, 0.8, 0.8],
                [0.5, 0.9, 0.6, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_steady": {"spawn_rate": 1, "max_particles": 8},
                "minecraft:emitter_lifetime_looping": {"active_time": 3.0, "sleep_time": 0.01},
            },
            acceleration=[0, 0.01, 0],
            drag=0.3,
        ),
        "water_ripple": particle(
            "bl:water_ripple",
            "particles_alpha",
            (0, 16),
            lifetime=(1.0, 2.2),
            speed=0.0,
            size="math.random(0.25, 0.45)",
            gradient=[
                [0.7, 1.0, 0.95, 0.0],
                [0.75, 1.0, 0.95, 0.65],
                [0.7, 1.0, 0.95, 0.0],
            ],
            emitter={
                "minecraft:emitter_rate_steady": {"spawn_rate": 0.7, "max_particles": 3},
                "minecraft:emitter_lifetime_looping": {"active_time": 2.0, "sleep_time": 0.01},
            },
            acceleration=[0, 0, 0],
            drag=0.0,
        ),
    }
    for name, data in particles.items():
        write_json(RP / "particles" / f"{name}.json", data)


# ---------------------------------------------------------------------------
# Language and functions
# ---------------------------------------------------------------------------


LANG = {
    "pack.name": "Bloomlands",
    "pack.description": "A flower-filled custom dimension, a 4x4 flower Bloomgate and three peaceful Bloomlings.",
    "dimension.bl:bloomlands": "The Bloomlands",
    "biome.bl:bloomlands": "Bloomlands",
    "bl.title.bloomlands": "The Bloomlands",
    "bl.subtitle.bloomlands": "A garden beyond the flowers",
    "bl.region.meadow": "Sunpetal Meadow",
    "bl.region.canopy": "Whispering Canopy",
    "bl.region.garden": "Giant's Garden",
    "bl.region.hills": "Petal Hills",
    "bl.region.pool": "Mirror Pool",
    "bl.region.edge": "Bloomlands Edge",
    "bl.portal.ready": "The Bloomgate spreads a flower bed around the rainbow portal. Step onto its centre.",
    "bl.portal.ground": "Use the Bloomgate while looking at a grass block.",
    "bl.portal.grass": "Use the Bloomgate while looking at a grass block.",
    "bl.portal.grass_square": "The Bloomgate needs a 4x4 patch of grass; stone, sand and other ground will not work.",
    "bl.portal.no_room": "There is not enough clear space above the grass for the flower bed.",
    "bl.portal.building": "The Bloomgate is waking...",
    "bl.portal.waking": "The Bloomlands are still waking. Please wait a moment.",
    "bl.portal.failed": "The Bloomgate could not open. Try again in a moment.",
    "bl.portal.cooldown": "The Bloomgate is still humming from your last journey.",
    "bl.portal.rearm": "Step off the rainbow portal to wake the Bloomgate again.",
    "bl.portal.rooted": "The return rainbow portal is rooted in the island.",
    "bl.portal.enter": "The Bloomlands open around you.",
    "bl.portal.return": "You step back through the flowers.",
    "bl.portal.leave": "The Bloomgate carries you home.",
    "bl.portal.no_return": "The way home is missing; the Bloomgate returns you to the world spawn.",
    "bl.voidrescue": "The flowers catch you and set you down gently.",
    "bl.region.enter": "Entering the Bloomlands",
    "bl.item.bloom_portal.desc": "Use on a 4x4 patch of grass to spread a flower bed and rainbow portal.",
}

BLOCK_LANG = {
    "petal_grass": "Petal Grass",
    "bloom_dirt": "Bloom Dirt",
    "bloom_stone": "Bloom Stone",
    "bloomwood_log": "Bloomwood Log",
    "bloomwood_planks": "Bloomwood Planks",
    "petal_path": "Petal Path",
    "canopy_leaves": "Canopy Leaves",
    "glowbud_leaves": "Glowbud Leaves",
    "dewgrass": "Dewgrass",
    "lily_bloom": "Lily Bloom",
    "portal_flower": "Bloomgate Flower",
    "rainbow_portal": "Rainbow Bloomgate",
    "bloomheart": "Bloomheart",
    "giant_sunflower": "Giant Sunflower",
    "giant_rosequartz": "Giant Rosequartz",
    "giant_skybell": "Giant Skybell",
    "giant_amethyst": "Giant Amethyst",
    "giant_emberbloom": "Giant Emberbloom",
    "giant_lumen": "Giant Lumen Bloom",
    "sunpetal": "Sunpetal",
    "rosequartz": "Rosequartz",
    "skybell": "Skybell",
    "moondrop": "Moondrop",
    "emberbloom": "Emberbloom",
    "amethyst_bell": "Amethyst Bell",
    "lumen_bell": "Lumen Bell",
}


def build_language() -> None:
    lines = [
        f"pack.name={LANG['pack.name']}",
        f"pack.description={LANG['pack.description']}",
        "",
    ]
    for key in ("dimension.bl:bloomlands", "biome.bl:bloomlands",
                "bl.title.bloomlands", "bl.subtitle.bloomlands",
                "bl.region.meadow", "bl.region.canopy", "bl.region.garden",
                "bl.region.hills", "bl.region.pool", "bl.region.edge",
                "bl.portal.ready", "bl.portal.ground", "bl.portal.grass",
                "bl.portal.grass_square", "bl.portal.no_room",
                "bl.portal.building", "bl.portal.waking", "bl.portal.failed",
                "bl.portal.cooldown", "bl.portal.rearm", "bl.portal.rooted",
                "bl.portal.enter", "bl.portal.return",
                "bl.portal.leave", "bl.portal.no_return", "bl.voidrescue",
                "bl.region.enter", "bl.item.bloom_portal.desc"):
        lines.append(f"{key}={LANG[key]}")
    lines.append("")

    for key, label in BLOCK_LANG.items():
        lines.append(f"tile.bl:{key}.name={label}")
        lines.append(f"tile.bl.{key}.name={label}")
    lines.append("")
    lines.append("item.bl:bloom_portal.name=Bloomgate")
    lines.append("item.bl.bloom_portal.name=Bloomgate")
    lines.append("item.bloom_portal.name=Bloomgate")
    lines.append("item.bl:bloom_portal=Bloomgate")
    lines.append("")
    for spec in content.entity_specs():
        lines.append(f"entity.{spec.identifier}.name={spec.label}")
        lines.append(f"entity.{spec.identifier.replace(':', '.')}.name={spec.label}")
        lines.append(f"item.spawn_egg.entity.{spec.identifier}.name={spec.label} Spawn Egg")
        lines.append(f"item.spawn_egg.entity.{spec.identifier.replace(':', '.')}.name={spec.label} Spawn Egg")
        lines.append(f"item.{spec.identifier}_spawn_egg.name={spec.label} Spawn Egg")
    lines.append("")

    text = "\n".join(lines)
    for pack in (BP, RP):
        write_text(pack / "texts" / "en_US.lang", text)
        write_json(pack / "texts" / "languages.json", ["en_US"])


def build_functions() -> None:
    write_text(
        BP / "functions" / "bloomlands" / "kit.mcfunction",
        "\n".join(
            [
                "# Bloomlands starter kit",
                "give @s bl:bloom_portal 2",
                "give @s bl:sunpetal 16",
                "give @s bl:rosequartz 16",
                "give @s bl:skybell 16",
                "give @s bl:lumen_bell 8",
                "give @s bl:petal_grass 32",
                "give @s bl:petal_path 32",
                "",
            ]
        ),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_packs() -> None:
    for pack in (BP, RP):
        if pack.exists():
            shutil.rmtree(pack)
        pack.mkdir(parents=True)

    write_json(
        BP / "manifest.json",
        manifest(
            content.BP_NAME,
            "The Bloomlands dimension, Bloomgate and peaceful Bloomling mobs.",
            BP_HEADER_UUID,
            [
                {
                    "description": "Bloomlands data",
                    "type": "data",
                    "uuid": BP_DATA_UUID,
                    "version": VERSION_PARTS,
                },
                {
                    "description": "Bloomlands dimension, portal and population script",
                    "type": "script",
                    "language": "javascript",
                    "entry": "scripts/main.js",
                    "uuid": BP_SCRIPT_UUID,
                    "version": VERSION_PARTS,
                },
            ],
            [
                {"uuid": RP_HEADER_UUID, "version": VERSION_PARTS},
                {"module_name": "@minecraft/server", "version": "2.0.0"},
            ],
        ),
    )
    write_json(
        RP / "manifest.json",
        manifest(
            content.RP_NAME,
            "Textures, models, animations and fog for the Bloomlands.",
            RP_HEADER_UUID,
            [
                {
                    "description": "Bloomlands resources",
                    "type": "resources",
                    "uuid": RP_RESOURCES_UUID,
                    "version": VERSION_PARTS,
                }
            ],
        ),
    )

    build_textures()
    build_atlases()
    build_blocks()
    write_json(BP / "items" / "bloom_portal.json", portal_item_json())
    build_recipes()
    build_entities()
    build_dimension()
    build_fogs()
    build_particles()
    build_language()
    build_functions()

    for name, geometry in content.block_geometry_files().items():
        write_json(RP / "models" / "blocks" / f"{name}.geo.json", geometry)

    write_text(BP / "scripts" / "main.js", (TOOLS / "main.js").read_text(encoding="utf-8"))


def package() -> None:
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for pack, folder in ((BP, "Bloomlands_BP"), (RP, "Bloomlands_RP")):
            for path in sorted(pack.rglob("*")):
                if path.is_file():
                    zf.write(path, f"{folder}/{path.relative_to(pack).as_posix()}")


def build_extras() -> None:
    try:
        import render
    except Exception as exc:  # pragma: no cover - reported in the build log
        print(f"  warning: preview/Blockbench generation skipped: {exc}")
        return

    render.build_all(
        root=ROOT,
        previews=PREVIEWS,
        blockbench=BLOCKBENCH,
        block_textures=content.block_textures(),
        block_geometries=content.block_geometry_files(),
        entities=content.entity_specs(),
        block_specs=content.BLOCK_SPECS,
        giant_specs=content.GIANT_FLOWERS,
        small_specs=content.SMALL_FLOWERS,
    )


def main() -> int:
    build_packs()
    build_extras()
    package()

    blocks = len(list((BP / "blocks").glob("*.json")))
    items = len(list((BP / "items").glob("*.json")))
    entities = len(list((BP / "entities").glob("*.json")))
    recipes = len(list((BP / "recipes").glob("*.json")))
    textures = len(list((RP / "textures").rglob("*.png")))
    print(f"built Bloomlands {VERSION}")
    print(f"  blocks: {blocks}, items: {items}, entities: {entities}, recipes: {recipes}, textures: {textures}")
    print(f"  behaviour pack: {BP}")
    print(f"  resource pack:  {RP}")
    print(f"  add-on:         {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
