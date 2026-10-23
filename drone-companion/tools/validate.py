#!/usr/bin/env python3
"""Static validation for the Drone Companion packs.

This checks JSON syntax, manifest UUID wiring, cross-file identifiers, geometry
structure, animation references, texture paths, and PNG dimensions.  It does not
replace an in-game test.

    python3 tools/validate.py
"""
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def fail(message):
    errors.append(message)


def load(path):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:  # noqa: BLE001
        fail(f"{path}: {exc}")
        return None


def png_size(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        fail(f"missing file: {path}")
        return None
    with open(full, "rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{path}: not a PNG")
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def require_file(path):
    if not os.path.exists(os.path.join(ROOT, path)):
        fail(f"missing file: {path}")


def require_equal(actual, expected, label):
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


# ---------------------------------------------------------------------------
# Manifests
# ---------------------------------------------------------------------------
behavior_manifest = load("behavior_pack/manifest.json")
resource_manifest = load("resource_pack/manifest.json")

if behavior_manifest and resource_manifest:
    behavior_header = behavior_manifest.get("header", {})
    resource_header = resource_manifest.get("header", {})

    for label, header in (("behavior", behavior_header), ("resource", resource_header)):
        if not header.get("uuid"):
            fail(f"{label} manifest: missing header uuid")
        if header.get("min_engine_version") != [1, 21, 80]:
            fail(f"{label} manifest: min_engine_version should be [1, 21, 80]")

    if behavior_header.get("uuid") == resource_header.get("uuid"):
        fail("behavior and resource manifests share a header uuid")

    behavior_modules = {module.get("type"): module for module in behavior_manifest.get("modules", [])}
    if "data" not in behavior_modules:
        fail("behavior manifest: missing data module")
    if "script" not in behavior_modules:
        fail("behavior manifest: missing script module")
    else:
        entry = behavior_modules["script"].get("entry")
        require_equal(entry, "scripts/drone_companion.js", "script entry")
        if entry:
            require_file(os.path.join("behavior_pack", entry))

    resource_modules = resource_manifest.get("modules", [])
    if not any(module.get("type") == "resources" for module in resource_modules):
        fail("resource manifest: missing resources module")

    dependencies = behavior_manifest.get("dependencies", [])
    resource_dependency = next(
        (dep for dep in dependencies if dep.get("uuid") == resource_header.get("uuid")),
        None,
    )
    if not resource_dependency:
        fail("behavior manifest: no dependency on the resource pack header uuid")
    else:
        require_equal(
            resource_dependency.get("version"),
            resource_header.get("version"),
            "behavior -> resource dependency version",
        )

    module_versions = {
        dep.get("module_name"): dep.get("version")
        for dep in dependencies
        if dep.get("module_name")
    }
    require_equal(module_versions.get("@minecraft/server"), "2.0.0", "@minecraft/server dependency")
    require_equal(module_versions.get("@minecraft/server-ui"), "2.0.0", "@minecraft/server-ui dependency")

# ---------------------------------------------------------------------------
# Pack icons and textures
# ---------------------------------------------------------------------------
for path in ("behavior_pack/pack_icon.png", "resource_pack/pack_icon.png"):
    size = png_size(path)
    if size and size != (256, 256):
        fail(f"{path}: expected 256x256, got {size[0]}x{size[1]}")

entity_texture_size = png_size("resource_pack/textures/entity/drone_companion.png")
if entity_texture_size and entity_texture_size != (64, 64):
    fail(f"entity texture: expected 64x64, got {entity_texture_size}")

controller_texture_size = png_size("resource_pack/textures/items/drone_controller.png")
if controller_texture_size and controller_texture_size != (64, 64):
    fail(f"controller icon: expected 64x64, got {controller_texture_size}")

# ---------------------------------------------------------------------------
# Entity, item, recipe
# ---------------------------------------------------------------------------
behavior_entity = load("behavior_pack/entities/drone_companion.json")
client_entity = load("resource_pack/entity/drone_companion.entity.json")
item = load("behavior_pack/items/drone_controller.json")
recipe = load("behavior_pack/recipes/drone_controller.json")
geometry = load("resource_pack/models/entity/drone_companion.geo.json")
animations = load("resource_pack/animations/drone_companion.animation.json")
item_texture = load("resource_pack/textures/item_texture.json")
languages = load("resource_pack/texts/languages.json")

if behavior_entity and client_entity:
    behavior_id = behavior_entity.get("minecraft:entity", {}).get("description", {}).get("identifier")
    client_description = client_entity.get("minecraft:client_entity", {}).get("description", {})
    require_equal(behavior_id, "drone:companion", "behavior entity identifier")
    require_equal(client_description.get("identifier"), behavior_id, "client entity identifier")

if item and recipe:
    item_id = item.get("minecraft:item", {}).get("description", {}).get("identifier")
    require_equal(item_id, "drone:controller", "item identifier")
    require_equal(
        recipe.get("minecraft:recipe_shaped", {}).get("result", {}).get("item"),
        item_id,
        "recipe result",
    )
    icon = item.get("minecraft:item", {}).get("components", {}).get("minecraft:icon", {})
    icon_key = icon.get("texture") if isinstance(icon, dict) else icon
    if item_texture and icon_key:
        texture_data = item_texture.get("texture_data", {})
        if icon_key not in texture_data:
            fail(f"item icon key {icon_key!r} is not registered in item_texture.json")
        else:
            texture_path = texture_data[icon_key].get("textures")
            if isinstance(texture_path, str):
                require_file(os.path.join("resource_pack", texture_path + ".png"))

if client_entity:
    description = client_entity.get("minecraft:client_entity", {}).get("description", {})
    texture_path = description.get("textures", {}).get("default")
    if texture_path:
        require_file(os.path.join("resource_pack", texture_path + ".png"))
    geometry_id = description.get("geometry", {}).get("default")
    if geometry and geometry_id:
        require_equal(
            geometry.get("minecraft:geometry", [{}])[0].get("description", {}).get("identifier"),
            geometry_id,
            "client geometry identifier",
        )
    if animations:
        animation_data = animations.get("animations", {})
        for name, animation_id in description.get("animations", {}).items():
            if animation_id not in animation_data:
                fail(f"client animation {name!r} points to missing {animation_id!r}")

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
if geometry:
    geometries = geometry.get("minecraft:geometry", [])
    if len(geometries) != 1:
        fail(f"geometry: expected one geometry, got {len(geometries)}")
    else:
        geo = geometries[0]
        desc = geo.get("description", {})
        require_equal(desc.get("texture_width"), 64, "geometry texture_width")
        require_equal(desc.get("texture_height"), 64, "geometry texture_height")

        bones = geo.get("bones", [])
        bone_names = {bone.get("name") for bone in bones}
        if len(bone_names) != len(bones):
            fail("geometry: duplicate bone names")
        cube_count = 0
        for bone in bones:
            parent = bone.get("parent")
            if parent and parent not in bone_names:
                fail(f"geometry bone {bone.get('name')!r}: missing parent {parent!r}")
            if len(bone.get("pivot", [])) != 3:
                fail(f"geometry bone {bone.get('name')!r}: invalid pivot")
            for cube in bone.get("cubes", []):
                cube_count += 1
                if len(cube.get("origin", [])) != 3 or len(cube.get("size", [])) != 3:
                    fail(f"geometry bone {bone.get('name')!r}: invalid cube origin/size")
                faces = cube.get("uv", {})
                if set(faces) != {"north", "east", "south", "west", "up", "down"}:
                    fail(f"geometry bone {bone.get('name')!r}: missing cube faces")
                for face_name, face in faces.items():
                    uv = face.get("uv", [])
                    size = face.get("uv_size", [])
                    if len(uv) != 2 or len(size) != 2:
                        fail(f"geometry {bone.get('name')!r}/{face_name}: invalid uv")
                        continue
                    x0, x1 = sorted((uv[0], uv[0] + size[0]))
                    y0, y1 = sorted((uv[1], uv[1] + size[1]))
                    if not (0 <= x0 <= 64 and 0 <= x1 <= 64 and 0 <= y0 <= 64 and 0 <= y1 <= 64):
                        fail(f"geometry {bone.get('name')!r}/{face_name}: uv outside 64x64 atlas")
        require_equal(cube_count, 35, "geometry cube count")
        require_equal(len(bones), 6, "geometry bone count")
        for expected_bone in ("body", "rotor_fl", "rotor_fr", "rotor_bl", "rotor_br", "camera"):
            if expected_bone not in bone_names:
                fail(f"geometry: missing bone {expected_bone!r}")

# ---------------------------------------------------------------------------
# Animations and localisation
# ---------------------------------------------------------------------------
if animations and geometry:
    animation_data = animations.get("animations", {})
    expected_animations = {
        "animation.drone_companion.rotors",
        "animation.drone_companion.hover",
        "animation.drone_companion.camera",
    }
    missing = expected_animations - set(animation_data)
    if missing:
        fail(f"animations: missing {sorted(missing)}")
    bone_names = {
        bone.get("name")
        for bone in geometry.get("minecraft:geometry", [{}])[0].get("bones", [])
    }
    for animation_id, animation in animation_data.items():
        for bone_name in animation.get("bones", {}):
            if bone_name not in bone_names:
                fail(f"animation {animation_id!r}: unknown bone {bone_name!r}")

lang_path = os.path.join(ROOT, "resource_pack/texts/en_US.lang")
if os.path.exists(lang_path):
    with open(lang_path, encoding="utf-8") as handle:
        lang = handle.read()
    for key in ("item.drone.controller=", "entity.drone:companion.name="):
        if key not in lang:
            fail(f"en_US.lang: missing {key!r}")
else:
    fail("missing resource_pack/texts/en_US.lang")

if languages is not None and "en_US" not in languages:
    fail("languages.json: en_US is not listed")

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
if errors:
    print(f"{len(errors)} validation error(s):")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

print("Drone Companion validation passed.")
print("  manifests, entity, item, recipe, geometry, animations, textures, lang: OK")
