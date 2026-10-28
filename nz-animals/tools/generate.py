"""
Generate the "NZ Animals" Minecraft Bedrock add-on (behaviour + resource pack).

Usage:  python3 tools/generate.py [output_dir]

The roster covers New Zealand native animals that have no equivalent mob in
Minecraft Bedrock. The green sea turtle (minecraft:turtle) and the bottlenose
dolphin (minecraft:dolphin) are deliberately excluded: vanilla's turtle IS
Chelonia mydas and vanilla's dolphin IS Tursiops truncatus, both NZ natives.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nzlib
from nzarchetypes import BUILDERS
from textures_recipes import PALETTE_EXTRAS, RECIPES, species_palette

NS = "nza"
PACK_NAME = "NZ Animals"
ADDON_FILENAME = "NZ_Animals.mcaddon"
MIN_ENGINE = [1, 21, 130]
# One Minecraft unit is 1/16 block. With a standard 1 m block this is
# 6.25 cm, so the whole roster shares one real-world scale.
#
# Small species are authored at a larger internal resolution and then
# reduced with the client entity's `scripts.scale`.  That keeps real-world
# size and collision while avoiding the detail loss that comes from packing
# a 40-70 cube kiwi or tuatara into only seven model units.
CM_PER_UNIT = 6.25
MIN_TARGET = 3.0
DETAIL_TARGET = 24.0

# ---------------------------------------------------------------------------
# roster
# ---------------------------------------------------------------------------
# kind:   ground | fly | swim | amphib
# motion: which animation profile the client entity uses
# biome:  a valid Bedrock biome tag
# drops:  (item, min, max)

from roster import ROSTER  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")


def next_version() -> list[int]:
    """
    The version stamped into both manifests.

    It has to change on every build. Bedrock identifies a pack by
    (uuid, version), so a rebuild that keeps the same version can be
    silently ignored on import - the old files stay installed and it looks
    like the fix did nothing. The build counter lives in tools/VERSION and
    is bumped here.
    """
    try:
        with open(VERSION_FILE, encoding="utf-8") as fh:
            cur = [int(x) for x in fh.read().strip().split(".")]
    except (OSError, ValueError):
        cur = [1, 0, 0]
    while len(cur) < 3:
        cur.append(0)
    # A model/animation overhaul is a minor release, not a three-digit patch.
    if cur[2] >= 99:
        cur[1] += 1
        cur[2] = 0
    else:
        cur[2] += 1
    with open(VERSION_FILE, "w", encoding="utf-8") as fh:
        fh.write(".".join(str(x) for x in cur) + "\n")
    return cur


def uid(*parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# Bones that define the solid body for collision.  Wings, fins, flippers,
# tails and antennae are deliberately excluded: a bird's wingspan or an
# orca's flukes must not become a three-block-wide hitbox.
COLLISION_BONES = {
    "body", "head", "neck", "torso", "chest", "rump", "skull", "shell",
    "thorax", "abdomen", "muzzle", "jaw", "beak", "crest",
    "left_leg", "right_leg", "left_foot", "right_foot",
    "left_front_leg", "right_front_leg", "left_back_leg", "right_back_leg",
    # Insect legs are part of the animal's footprint; without them the weta
    # collapses to a 0.2-block hitbox.
    "left_leg0", "right_leg0", "left_leg1", "right_leg1",
    "left_leg2", "right_leg2",
}


def model_bounds(model: nzlib.Model) -> tuple[list[int], list[int]]:
    cubes = [c for c in model.cubes if c.bone in COLLISION_BONES]
    if not cubes:
        cubes = model.cubes
    lo = [min(c.lo[i] for c in cubes) for i in range(3)]
    hi = [max(c.hi[i] for c in cubes) for i in range(3)]
    return lo, hi


# ---------------------------------------------------------------------------
# behaviour components
# ---------------------------------------------------------------------------

def behaviour_components(spec: dict, lo: list[int], hi: list[int]) -> dict:
    width = round((hi[0] - lo[0]) / 16.0, 2)
    height = round((hi[1] - lo[1]) / 16.0, 2)
    comp: dict = {
        "minecraft:type_family": {"family": [f"{NS}:{spec['id']}", "animal", "mob"]},
        "minecraft:health": {"value": spec["hp"], "max": spec["hp"]},
        "minecraft:collision_box": {"width": max(width, 0.2), "height": max(height, 0.2)},
        "minecraft:movement": {"value": spec["speed"]},
        "minecraft:conditional_bandwidth_optimization": {},
        "minecraft:despawn": {"despawn_from_distance": {"min_distance": 32, "max_distance": 64}},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": False},
        "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.5},
        "minecraft:behavior.hurt_by_target": {"priority": 2},
        "minecraft:behavior.random_look_around": {"priority": 8},
        "minecraft:behavior.look_at_player": {
            "priority": 7, "look_distance": 8.0, "probability": 0.02,
        },
    }

    kind = spec["kind"]
    if kind == "ground":
        comp["minecraft:movement.basic"] = {}
        comp["minecraft:navigation.walk"] = {
            "can_path_over_water": True, "avoid_damage_blocks": True,
        }
        comp["minecraft:jump.static"] = {}
        comp["minecraft:physics"] = {"has_collision": True, "has_gravity": True}
        comp["minecraft:breathable"] = {
            "breathes_air": True, "breathes_water": False, "total_supply": 15, "suffocate_time": 0,
        }
        comp["minecraft:behavior.random_stroll"] = {
            "priority": 6, "speed_multiplier": spec.get("stroll", 1.0),
        }
    elif kind == "fly":
        comp["minecraft:can_fly"] = {}
        comp["minecraft:movement.fly"] = {}
        comp["minecraft:navigation.fly"] = {
            "can_path_from_air": True, "can_path_over_water": True,
        }
        comp["minecraft:physics"] = {"has_collision": True, "has_gravity": False}
        comp["minecraft:buoyant"] = {
            "apply_gravity": False, "base_buoyancy": 1,
            "liquid_blocks": ["minecraft:water"], "movement_type": "bobbing",
        }
        comp["minecraft:breathable"] = {
            "breathes_air": True, "breathes_water": False, "total_supply": 15, "suffocate_time": 0,
        }
        comp["minecraft:behavior.random_fly"] = {
            "priority": 6, "xz_dist": 10, "y_dist": 4, "y_offset": 0, "speed_multiplier": 1.0,
        }
        comp["minecraft:behavior.float"] = {"priority": 0}
    elif kind == "swim":
        comp["minecraft:movement.generic"] = {}
        comp["minecraft:navigation.generic"] = {
            "can_breach": False, "can_walk": False, "can_path_over_water": False,
            "can_sink": False, "can_swim": True, "is_amphibious": False,
        }
        comp["minecraft:physics"] = {"has_collision": True, "has_gravity": False}
        comp["minecraft:underwater_movement"] = {"value": spec["speed"]}
        comp["minecraft:breathable"] = {
            "breathes_air": False, "breathes_water": True, "total_supply": 15, "suffocate_time": 0,
        }
        comp["minecraft:buoyant"] = {
            "apply_gravity": False, "base_buoyancy": 1,
            "liquid_blocks": ["minecraft:water", "minecraft:flowing_water"],
            "movement_type": "waves",
        }
        comp["minecraft:behavior.random_swim"] = {"priority": 6, "speed_multiplier": 1.0}
    elif kind == "amphib":
        comp["minecraft:movement.generic"] = {}
        comp["minecraft:navigation.generic"] = {
            "can_breach": False, "can_walk": True, "can_path_over_water": True,
            "can_sink": False, "can_swim": True, "is_amphibious": True,
        }
        comp["minecraft:physics"] = {"has_collision": True, "has_gravity": True}
        comp["minecraft:breathable"] = {
            "breathes_air": True, "breathes_water": True, "total_supply": 15, "suffocate_time": 0,
        }
        comp["minecraft:buoyant"] = {
            "apply_gravity": False, "base_buoyancy": 0.8,
            "liquid_blocks": ["minecraft:water", "minecraft:flowing_water"],
            "movement_type": "bobbing",
        }
        comp["minecraft:behavior.random_stroll"] = {"priority": 6, "speed_multiplier": 0.6}
        comp["minecraft:behavior.random_swim"] = {"priority": 5, "speed_multiplier": 1.0}

    if spec.get("drops"):
        comp["minecraft:loot"] = {"table": f"loot_tables/entities/{spec['id']}.json"}
    return comp


def behaviour_entity(spec: dict, lo, hi) -> dict:
    return {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {
                "identifier": f"{NS}:{spec['id']}",
                # every vanilla mob declares a spawn category, and newer
                # Bedrock versions expect one
                "spawn_category": "creature",
                "is_spawnable": True,
                "is_summonable": True,
                "is_experimental": False,
            },
            "components": behaviour_components(spec, lo, hi),
        },
    }


def spawn_rules(spec: dict) -> dict:
    """
    One condition block per allowed biome tag.

    In Bedrock the `conditions` array holds *alternatives* (any one may match),
    while a `biome_filter` array is AND-ed. That gives us OR across biomes
    and AND for the "not warm ocean" exclusions.
    """
    kind = spec["kind"]
    population = "water_animal" if kind == "swim" else "animal"
    tags = spec["biome"] if isinstance(spec["biome"], list) else [spec["biome"]]
    excludes = spec.get("exclude", [])

    conditions = []
    for tag in tags:
        filters = [{"test": "has_biome_tag", "operator": "==", "value": tag}]
        for ex in excludes:
            filters.append({"test": "has_biome_tag", "operator": "!=", "value": ex})
        cond = {
            "minecraft:weight": {"default": spec["weight"]},
            "minecraft:herd": {"min_size": spec["herd"][0], "max_size": spec["herd"][1]},
            "minecraft:brightness_filter": {
                "min": spec["brightness"][0], "max": spec["brightness"][1],
                "adjust_for_weather": False,
            },
            "minecraft:biome_filter": filters if len(filters) > 1 else filters[0],
        }
        if kind == "swim":
            cond["minecraft:spawns_underwater"] = {}
        else:
            cond["minecraft:spawns_on_surface"] = {}
        conditions.append(cond)

    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {
                "identifier": f"{NS}:{spec['id']}",
                "population_control": population,
            },
            "conditions": conditions,
        },
    }


def loot_table(spec: dict) -> dict:
    pools = []
    for item, lo, hi in spec.get("drops", []):
        pools.append({
            "rolls": 1,
            "entries": [{
                "type": "item",
                "name": item,
                "weight": 1,
                "functions": [{"function": "set_count", "count": {"min": lo, "max": hi}}],
            }],
        })
    return {"pools": pools}


# ---------------------------------------------------------------------------
# client entity + animations
# ---------------------------------------------------------------------------

def egg_colors(spec: dict) -> tuple[str, str]:
    """Spawn egg tint, derived from the species palette unless overridden."""
    if spec.get("egg"):
        return spec["egg"]
    body = spec["pal"]["body"]
    head = spec["pal"].get("head", body)
    hexify = lambda c: "#%02X%02X%02X" % c
    return hexify(body), hexify(head)


def client_entity(spec: dict, render_scale: float) -> dict:
    base, overlay = egg_colors(spec)
    scripts: dict = {"animate": ["movement"]}
    if abs(render_scale - 1.0) > 1e-4:
        # Constant Molang scale.  Geometry, UVs and animations stay at the
        # detailed internal resolution; only the rendered model is reduced
        # to the species' real-world size.
        scripts["scale"] = f"{render_scale:.5f}"
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": f"{NS}:{spec['id']}",
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": f"textures/entity/{spec['id']}/{spec['id']}"},
                "geometry": {"default": f"geometry.{NS}.{spec['id']}"},
                "animations": {
                    # a short alias, exactly like vanilla does it: the sheep
                    # maps "move" to "controller.animation.sheep.move"
                    "movement": f"controller.animation.{NS}.{spec['motion']}",
                    "walk": f"animation.{NS}.{spec['motion']}.walk",
                    "idle": f"animation.{NS}.{spec['motion']}.idle",
                },
                "scripts": scripts,
                "render_controllers": [f"controller.render.{NS}"],
                "spawn_egg": {"base_color": base, "overlay_color": overlay},
            }
        },
    }


def animation_controller(profile: str) -> dict:
    """
    Locomotion controller.

    The walk animation is always in the graph and its *weight* is the mob's
    move speed - which is how vanilla drives it (sheep, spider, fox, goat,
    llama, ... all use `{"walk": "query.modified_move_speed"}`).

    A state machine on `query.modified_move_speed > 0.01` looks equivalent but
    is not: if that transition never fires, the mob is left with whatever the
    default state holds. An earlier revision of this pack used exactly that
    state machine, and the result was mobs that never moved a bone.

    The idle animation runs alongside the walk, on bones the walk does not
    touch (head, tail, antennae), so a standing mob still breathes, sways and
    looks around instead of standing like a statue.
    """
    return {
        "format_version": "1.10.0",
        "animation_controllers": {
            f"controller.animation.{NS}.{profile}": {
                "initial_state": "default",
                "states": {
                    "default": {
                        "blend_transition": 0.2,
                        "animations": [
                            # weight = how fast the mob is going; the walk is
                            # faded in and out with the speed instead of being
                            # switched on and off.  The multiplier is high
                            # enough that a slow mob (kiwi, snail) still gets
                            # a full-strength stride at its normal speed.
                            {"walk": "math.min(1.0, query.modified_move_speed * 6.0)"},
                            "idle",
                        ],
                    },
                },
            }
        },
    }


# ---------------------------------------------------------------------------
# Stride phase
# ---------------------------------------------------------------------------
# The phase of the walk cycle comes from `query.life_time`, NOT from
# `query.anim_time` with `anim_time_update: "query.modified_distance_moved"`.
#
# `anim_time_update` re-bases `query.anim_time` on a distance query. If that
# query does not advance for a custom entity, `query.anim_time` stays pinned at
# 0 and every bone driven by it freezes in a single pose - which looks exactly
# like "no animation at all". Vanilla gets away with it because its mobs are
# native; a data-driven entity is not guaranteed the same treatment.
#
# `query.life_time` is the entity's age in seconds. It always advances, for
# every entity, in every profile - the vanilla dolphin uses nothing else.
#
# The cycle rate is scaled by the move speed so the stride keeps up with the
# ground, but with a floor so the legs can never be frozen solid:
#
#     math.cos(query.life_time * 8.0 * math.max(query.modified_move_speed, 0.25))
#
# 8.0 rad/s is about 1.3 strides a second, which is slow enough to read.
# The floor only keeps the phase advancing; the controller weight is what
# fades the walk out when the mob is standing still.
STRIDE_BASE = 8.0
STRIDE_FLOOR = 0.25


def _stride(freq: float = STRIDE_BASE) -> str:
    """A walk-cycle phase that is guaranteed to advance."""
    return (f"query.life_time * {freq} * "
            f"math.max(query.modified_move_speed, {STRIDE_FLOOR})")


def _cos_leg(freq: float = STRIDE_BASE) -> str:
    return f"math.cos({_stride(freq)})"


def _sin_time(freq: float) -> str:
    return f"math.sin(query.life_time * {freq})"


def _cos_time(freq: float) -> str:
    return f"math.cos(query.life_time * {freq})"


def animations(profile: str) -> dict:
    """
    Animation set for a motion profile.

    Every walk is a readable, exaggerated cycle rather than a twitch: the
    leg swing is 24-32 degrees, wings beat 48 degrees, and the body carries a
    small counter-roll.  Idle animations deliberately use only bones the walk
    does not touch, so blending the two never fights over a channel.
    """
    out: dict = {}
    walk: dict = {"loop": True, "animation_length": 1.0, "bones": {}}
    idle: dict = {"loop": True, "animation_length": 3.0, "bones": {}}

    if profile == "bird_ground":
        walk["bones"] = {
            "left_leg": {"rotation": [f"{_cos_leg()} * 32.0", 0.0, 0.0]},
            "right_leg": {"rotation": [f"{_cos_leg()} * -32.0", 0.0, 0.0]},
            "body": {"rotation": [f"{_sin_time(16.0)} * 1.5", 0.0,
                                   f"{_cos_leg()} * 3.0"]},
            "tail": {"rotation": [0.0, f"{_cos_leg()} * 8.0", 0.0]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.6)} * 10.0",
                             f"{_sin_time(0.9)} * 12.0",
                             f"{_sin_time(1.1)} * 3.0"],
                "position": [0.0, f"{_cos_time(1.6)} * 0.6", 0.0],
            },
            "left_wing": {"rotation": [0.0, 0.0, f"{_sin_time(0.8)} * 3.0"]},
            "right_wing": {"rotation": [0.0, 0.0, f"{_sin_time(0.8)} * -3.0"]},
        }
    elif profile == "bird_fly":
        walk["bones"] = {
            "left_wing": {"rotation": [0.0, f"{_cos_time(18.0)} * 8.0",
                                       f"{_sin_time(18.0)} * -48.0"]},
            "right_wing": {"rotation": [0.0, f"{_cos_time(18.0)} * -8.0",
                                        f"{_sin_time(18.0)} * 48.0"]},
            "body": {"rotation": [f"{_sin_time(18.0)} * 5.0", 0.0,
                                   f"{_sin_time(9.0)} * 2.0"]},
            "tail": {"rotation": [f"{_cos_time(18.0)} * 7.0", 0.0, 0.0]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.7)} * 8.0",
                             f"{_sin_time(0.8)} * 10.0", 0.0],
                "position": [0.0, f"{_cos_time(1.7)} * 0.5", 0.0],
            },
            "left_leg": {"rotation": [f"{_sin_time(1.7)} * 10.0", 0.0, 0.0]},
            "right_leg": {"rotation": [f"{_sin_time(1.7)} * -10.0", 0.0, 0.0]},
        }
    elif profile == "quadruped":
        walk["bones"] = {
            "left_front_leg": {"rotation": [f"{_cos_leg()} * 30.0", 0.0, 0.0]},
            "right_front_leg": {"rotation": [f"{_cos_leg()} * -30.0", 0.0, 0.0]},
            "left_back_leg": {"rotation": [f"{_cos_leg()} * -30.0", 0.0, 0.0]},
            "right_back_leg": {"rotation": [f"{_cos_leg()} * 30.0", 0.0, 0.0]},
            "body": {"rotation": [f"{_sin_time(16.0)} * 1.5", 0.0,
                                   f"{_cos_leg()} * 3.0"]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.4)} * 7.0",
                             f"{_sin_time(0.7)} * 14.0", 0.0],
                "position": [0.0, f"{_cos_time(1.4)} * 0.5", 0.0],
            },
            "tail": {"rotation": [0.0, f"{_sin_time(2.2)} * 16.0", 0.0]},
        }
    elif profile == "seal":
        walk["bones"] = {
            "left_flipper": {"rotation": [f"{_cos_leg(5.5)} * 30.0", 0.0, 0.0]},
            "right_flipper": {"rotation": [f"{_cos_leg(5.5)} * -30.0", 0.0, 0.0]},
            "left_hind_flipper": {"rotation": [f"{_cos_leg(5.5)} * -24.0", 0.0, 0.0]},
            "right_hind_flipper": {"rotation": [f"{_cos_leg(5.5)} * 24.0", 0.0, 0.0]},
            "body": {"rotation": [f"{_sin_time(11.0)} * 2.0", 0.0,
                                   f"{_cos_leg(5.5)} * 4.0"]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.2)} * 7.0",
                             f"{_sin_time(0.6)} * 12.0", 0.0],
                "position": [0.0, f"{_cos_time(1.2)} * 0.6", 0.0],
            },
            "tail": {"rotation": [0.0, f"{_sin_time(1.8)} * 14.0", 0.0]},
        }
    elif profile == "penguin":
        walk["bones"] = {
            "left_foot": {"rotation": [f"{_cos_leg()} * 26.0", 0.0, 0.0]},
            "right_foot": {"rotation": [f"{_cos_leg()} * -26.0", 0.0, 0.0]},
            "body": {"rotation": [0.0, 0.0, f"{_cos_leg()} * 9.0"]},
            "left_flipper": {"rotation": [0.0, 0.0,
                                           f"{_sin_time(16.0)} * -22.0"]},
            "right_flipper": {"rotation": [0.0, 0.0,
                                            f"{_sin_time(16.0)} * 22.0"]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.6)} * 8.0",
                             f"{_sin_time(0.8)} * 10.0", 0.0],
                "position": [0.0, f"{_cos_time(1.6)} * 0.5", 0.0],
            },
            "tail": {"rotation": [0.0, f"{_sin_time(1.6)} * 10.0", 0.0]},
        }
    elif profile == "ratite":
        walk["bones"] = {
            "left_leg": {"rotation": [f"{_cos_leg(6.0)} * 32.0", 0.0, 0.0]},
            "right_leg": {"rotation": [f"{_cos_leg(6.0)} * -32.0", 0.0, 0.0]},
            "body": {"rotation": [0.0, 0.0, f"{_cos_leg(6.0)} * 3.0"]},
            "neck": {"rotation": [f"{_sin_time(12.0)} * 6.0", 0.0, 0.0]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.1)} * 10.0",
                             f"{_sin_time(0.55)} * 14.0", 0.0],
                "position": [0.0, f"{_cos_time(1.1)} * 0.8", 0.0],
            },
            "tail": {"rotation": [0.0, f"{_sin_time(1.5)} * 12.0", 0.0]},
        }
    elif profile == "swim":
        walk["bones"] = {
            "tail": {"rotation": [0.0, f"{_sin_time(6.0)} * 32.0", 0.0]},
            "body": {"rotation": [f"{_sin_time(6.0)} * 3.0",
                                   f"{_sin_time(3.0)} * 1.5", 0.0]},
            "left_fin": {"rotation": [0.0, 0.0,
                                       f"{_sin_time(6.0)} * 18.0"]},
            "right_fin": {"rotation": [0.0, 0.0,
                                        f"{_sin_time(6.0)} * -18.0"]},
            "dorsal_fin": {"rotation": [f"{_sin_time(6.0)} * 3.0", 0.0, 0.0]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [0.0, f"{_sin_time(1.3)} * 10.0",
                             f"{_sin_time(1.3)} * 2.0"],
                "position": [0.0, f"{_cos_time(1.3)} * 0.6", 0.0],
            },
        }
    elif profile == "insect":
        walk["bones"] = {
            "left_leg0": {"rotation": [0.0, f"{_cos_leg(14.0)} * 28.0", 0.0]},
            "right_leg0": {"rotation": [0.0, f"{_cos_leg(14.0)} * -28.0", 0.0]},
            "left_leg1": {"rotation": [0.0, f"{_cos_leg(14.0)} * -28.0", 0.0]},
            "right_leg1": {"rotation": [0.0, f"{_cos_leg(14.0)} * 28.0", 0.0]},
            "left_leg2": {"rotation": [0.0, f"{_cos_leg(14.0)} * 28.0", 0.0]},
            "right_leg2": {"rotation": [0.0, f"{_cos_leg(14.0)} * -28.0", 0.0]},
            "body": {"rotation": [0.0, 0.0, f"{_cos_leg(14.0)} * 2.5"]},
            "abdomen": {"rotation": [f"{_sin_time(14.0)} * 2.0", 0.0, 0.0]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(3.0)} * 8.0",
                             f"{_sin_time(1.5)} * 10.0", 0.0],
                "position": [0.0, f"{_cos_time(3.0)} * 0.4", 0.0],
            },
            "left_antenna": {"rotation": [0.0, 0.0,
                                           f"{_sin_time(4.0)} * 14.0"]},
            "right_antenna": {"rotation": [0.0, 0.0,
                                            f"{_sin_time(4.0)} * -14.0"]},
        }
    elif profile == "snail":
        walk["bones"] = {
            "body": {"rotation": [0.0, 0.0, f"{_cos_leg(3.0)} * 4.0"]},
            "shell": {"rotation": [0.0, 0.0, f"{_cos_leg(3.0)} * 1.5"]},
        }
        idle["bones"] = {
            "head": {
                "rotation": [f"{_sin_time(1.1)} * 6.0",
                             f"{_sin_time(0.55)} * 8.0", 0.0],
                "position": [0.0, f"{_cos_time(1.1)} * 0.5", 0.0],
            },
            "left_tentacle": {"rotation": [0.0, 0.0,
                                            f"{_sin_time(1.6)} * 10.0"]},
            "right_tentacle": {"rotation": [0.0, 0.0,
                                             f"{_sin_time(1.6)} * -10.0"]},
        }
    else:
        raise ValueError(f"unknown motion profile {profile!r}")

    out[f"animation.{NS}.{profile}.walk"] = walk
    out[f"animation.{NS}.{profile}.idle"] = idle
    return {"format_version": "1.10.0", "animations": out}


RENDER_CONTROLLER = {
    "format_version": "1.10.0",
    "render_controllers": {
        f"controller.render.{NS}": {
            "geometry": "geometry.default",
            "materials": [{"*": "material.default"}],
            "textures": ["texture.default"],
            "is_hurt_color": {"r": 1.0, "g": 0.0, "b": 0.0, "a": 0.4},
        }
    },
}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    out_root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
    bp = os.path.join(out_root, "behavior_pack")
    rp = os.path.join(out_root, "resource_pack")
    if os.path.isdir(out_root):
        shutil.rmtree(out_root)

    profiles = sorted({s["motion"] for s in ROSTER})

    # ---- resource pack: animations & controllers ----
    for prof in profiles:
        write_json(os.path.join(rp, "animations", f"{prof}.animations.json"), animations(prof))
        write_json(os.path.join(rp, "animation_controllers", f"{prof}.ac.json"), animation_controller(prof))
    write_json(os.path.join(rp, "render_controllers", "common.rc.json"), RENDER_CONTROLLER)

    # ---- per species ----
    for spec in ROSTER:
        sid = spec["id"]
        params = dict(spec["real"])
        params["name"] = sid
        # Builders need to know whether a bird flies and which species they
        # are building (e.g. the sperm whale's square head, the huhu's elytra).
        params["id"] = sid
        params["kind"] = spec["kind"]
        params["motion"] = spec["motion"]
        params["arch"] = spec["arch"]

        # palette: the species palette plus the recipe's extra keys
        palette = species_palette(spec)

        model = BUILDERS[spec["arch"]](params, palette)
        model.attach_markings(RECIPES.get(sid, []))
        # The builders work in real-world centimetres; scale to the shared
        # real-world model scale (1 unit = 6.25 cm) or to the 24-unit detail
        # floor, then shrink the rendered mesh on the client.
        lo_cm = [min(c.lo[i] for c in model.cubes) for i in range(3)]
        hi_cm = [max(c.hi[i] for c in model.cubes) for i in range(3)]
        if spec.get("scale_by") == "height":
            # upright animals (penguins, the moa) are sized by how tall they stand
            ref_cm = hi_cm[1] - lo_cm[1]
        else:
            ref_cm = max(hi_cm[0] - lo_cm[0], hi_cm[2] - lo_cm[2])
        # Real-world size in Minecraft units.  1 unit = 6.25 cm; a small
        # floor keeps the tiniest invertebrates from disappearing.
        real_units = max(MIN_TARGET, ref_cm / CM_PER_UNIT)
        # Build small species at a detailed internal resolution, then scale
        # the rendered model back down on the client.  Large species are
        # already above the detail floor.
        detail_units = max(real_units, DETAIL_TARGET)
        render_scale = real_units / detail_units
        model.scaled(detail_units / max(1e-6, ref_cm))
        # Boxes that end up flush after scaling would z-fight, and the
        # texture would flicker. Inset them by half a unit, then re-ground:
        # the per-cube offsets can otherwise push the whole model a fraction
        # of a unit below y=0.
        model.deconflict()
        model.ground()
        pixels, w, h, offsets = nzlib.render_texture(model, palette)
        nzlib.write_png(os.path.join(rp, "textures", "entity", sid, f"{sid}.png"), pixels, w, h)

        geo = nzlib.to_geo_json(model, offsets, f"geometry.{NS}.{sid}", (w, h))
        write_json(os.path.join(rp, "models", "entity", f"{sid}.geo.json"), geo)
        write_json(os.path.join(rp, "entity", f"{sid}.entity.json"),
                   client_entity(spec, render_scale))

        lo, hi = model_bounds(model)
        # Collision is in real-world units, not the detailed internal mesh.
        lo = [v * render_scale for v in lo]
        hi = [v * render_scale for v in hi]
        write_json(os.path.join(bp, "entities", f"{sid}.json"), behaviour_entity(spec, lo, hi))
        write_json(os.path.join(bp, "spawn_rules", f"{sid}.json"), spawn_rules(spec))
        write_json(os.path.join(bp, "loot_tables", "entities", f"{sid}.json"), loot_table(spec))

    # ---- manifests ----
    version = next_version()
    print(f"pack version: {version}")
    bp_uuid = uid("bp", PACK_NAME)
    write_json(os.path.join(bp, "manifest.json"), {
        "format_version": 2,
        "header": {
            "name": f"{PACK_NAME} Behaviour Pack",
            "description": "Adds New Zealand native animals that are not in vanilla Minecraft.",
            "uuid": bp_uuid,
            "version": version,
            "min_engine_version": MIN_ENGINE,
        },
        "modules": [{
            "description": "NZ Animals behaviours",
            "type": "data",
            "uuid": uid("bp-module", PACK_NAME),
            "version": version,
        }],
        "dependencies": [],
        "metadata": {"authors": ["OpenCode"], "license": "MIT"},
    })
    write_json(os.path.join(rp, "manifest.json"), {
        "format_version": 2,
        "header": {
            "name": f"{PACK_NAME} Resource Pack",
            "description": "Models, textures and animations for the NZ Animals add-on.",
            "uuid": uid("rp", PACK_NAME),
            "version": version,
            "min_engine_version": MIN_ENGINE,
        },
        "modules": [{
            "description": "NZ Animals resources",
            "type": "resources",
            "uuid": uid("rp-module", PACK_NAME),
            "version": version,
        }],
        "dependencies": [{"uuid": bp_uuid, "version": version}],
        "metadata": {"authors": ["OpenCode"], "license": "MIT"},
    })

    # ---- texts ----
    # Bedrock resolves entity display names and spawn-egg names from language
    # keys. Vanilla flattens the namespace away ("entity.pig.name") while
    # add-on documentation uses the namespaced form ("entity.nza:kiwi.name").
    # Both are emitted so the name resolves whichever the game looks up.
    lang_lines = [
        f"pack.name={PACK_NAME}",
        "pack.description=Adds New Zealand native animals that are not in vanilla Minecraft.",
    ]
    for spec in ROSTER:
        sid = spec["id"]
        name = spec["name"]
        lang_lines += [
            f"entity.{NS}.{sid}.name={name}",
            f"entity.{NS}:{sid}.name={name}",
            f"item.spawn_egg.entity.{NS}.{sid}.name={name} Spawn Egg",
            f"item.spawn_egg.entity.{NS}:{sid}.name={name} Spawn Egg",
        ]
    for pack in (bp, rp):
        os.makedirs(os.path.join(pack, "texts"), exist_ok=True)
        write_json(os.path.join(pack, "texts", "languages.json"), ["en_US"])
        with open(os.path.join(pack, "texts", "en_US.lang"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lang_lines) + "\n")

    # ---- pack icon: the kiwi on a green tile ----
    import preview
    icon_img = preview.make_icon(
        os.path.join(rp, "models", "entity", "kiwi.geo.json"),
        os.path.join(rp, "textures", "entity", "kiwi", "kiwi.png"),
    )
    for pack in (bp, rp):
        icon_img.save(os.path.join(pack, "pack_icon.png"))

    # ---- package ----
    addon = os.path.normpath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ADDON_FILENAME))
    if os.path.exists(addon):
        os.remove(addon)
    with zipfile.ZipFile(addon, "w", zipfile.ZIP_DEFLATED) as z:
        for pack in (bp, rp):
            for root, _dirs, files in os.walk(pack):
                for f in files:
                    full = os.path.join(root, f)
                    z.write(full, os.path.relpath(full, out_root))

    print(f"roster: {len(ROSTER)} species")
    print(f"profiles: {', '.join(profiles)}")
    print(f"output: {out_root}")
    print(f"addon:  {addon}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
