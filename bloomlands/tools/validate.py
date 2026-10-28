"""
Structural and asset validator for Bloomlands.

The validator is intentionally stricter than ``python -m json.tool``:
it resolves every custom identifier, model, texture, animation, recipe,
language key and packaged file used by the add-on.  It also checks the
limits Bedrock applies to custom block geometry and the wiring between
client entities and animation controllers.

Run from the repository root:

    python bloomlands/tools/validate.py
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
VERSION = (ROOT / "tools" / "VERSION").read_text(encoding="utf-8").strip()
VERSION_PARTS = [int(p) for p in VERSION.split(".")]
MCADDON = ROOT / f"Bloomlands-{VERSION}.mcaddon"

FACE_KEYS = {"north", "south", "east", "west", "up", "down"}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
NS = "bl:"

errors: list[str] = []
notes: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path.relative_to(ROOT)}: {exc}")
        return None


def texture_size(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as image:
            return image.size
    except Exception as exc:
        fail(f"{path.relative_to(ROOT)}: cannot read PNG: {exc}")
        return None


def lang_keys() -> set[str]:
    keys: set[str] = set()
    for pack in (BP, RP):
        path = pack / "texts" / "en_US.lang"
        if not path.exists():
            fail(f"{path.relative_to(ROOT)}: missing")
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                keys.add(line.split("=", 1)[0].strip())
    return keys


def check_manifest(pack: Path, kind: str, *, friend: str | None = None) -> dict | None:
    path = pack / "manifest.json"
    data = load(path)
    if not data:
        return None
    header = data.get("header", {})
    if data.get("format_version") != 2:
        fail(f"{path.relative_to(ROOT)}: format_version must be 2")
    if header.get("version") != VERSION_PARTS:
        fail(f"{path.relative_to(ROOT)}: header.version {header.get('version')} != {VERSION_PARTS}")
    if header.get("min_engine_version") != [1, 26, 60]:
        fail(f"{path.relative_to(ROOT)}: min_engine_version must be [1,26,60]")
    for key in ("name", "description", "uuid"):
        if not header.get(key):
            fail(f"{path.relative_to(ROOT)}: missing header.{key}")
    if header.get("uuid") and not UUID_RE.match(header["uuid"]):
        fail(f"{path.relative_to(ROOT)}: invalid header UUID")
    modules = data.get("modules", [])
    if not modules:
        fail(f"{path.relative_to(ROOT)}: no modules")
    seen_uuids: set[str] = set()
    for module in modules:
        module_uuid = module.get("uuid", "")
        if not module_uuid or not UUID_RE.match(module_uuid):
            fail(f"{path.relative_to(ROOT)}: invalid module UUID {module_uuid!r}")
        if module_uuid in seen_uuids:
            fail(f"{path.relative_to(ROOT)}: duplicate module UUID {module_uuid}")
        seen_uuids.add(module_uuid)
        if module.get("version") != VERSION_PARTS:
            fail(f"{path.relative_to(ROOT)}: module version != {VERSION_PARTS}")
        expected = "data" if kind == "data" else "resources"
        if module.get("type") not in {expected, "script"}:
            fail(f"{path.relative_to(ROOT)}: unexpected module type {module.get('type')!r}")
        if module.get("type") == "script":
            if module.get("language") != "javascript":
                fail(f"{path.relative_to(ROOT)}: script module must use javascript")
            entry = module.get("entry")
            if not entry or not (pack / entry).exists():
                fail(f"{path.relative_to(ROOT)}: script entry {entry!r} does not exist")
        if module.get("type") == "data" and kind != "data":
            fail(f"{path.relative_to(ROOT)}: resource manifest has a data module")
    if kind == "data":
        if not any(module.get("type") == "data" for module in modules):
            fail(f"{path.relative_to(ROOT)}: missing data module")
        if not any(module.get("type") == "script" for module in modules):
            fail(f"{path.relative_to(ROOT)}: missing script module")
    if friend and not any(dep.get("uuid") == friend for dep in data.get("dependencies", [])):
        fail(f"{path.relative_to(ROOT)}: missing dependency {friend}")
    return data


def geo_index(directory: Path) -> dict[str, tuple[Path, dict]]:
    index: dict[str, tuple[Path, dict]] = {}
    for path in sorted(directory.glob("*.geo.json")):
        data = load(path)
        if not data:
            continue
        entries = data.get("minecraft:geometry", [])
        if len(entries) != 1:
            fail(f"{path.relative_to(ROOT)}: expected one geometry entry")
            continue
        entry = entries[0]
        identifier = entry.get("description", {}).get("identifier", "")
        if not identifier:
            fail(f"{path.relative_to(ROOT)}: missing geometry identifier")
            continue
        if identifier in index:
            fail(f"{path.relative_to(ROOT)}: duplicate geometry identifier {identifier}")
        index[identifier] = (path, entry)
    return index


def check_geometry(path: Path, entry: dict, texture_width: int, texture_height: int, *, block: bool) -> set[str]:
    bones = entry.get("bones", [])
    if not bones:
        fail(f"{path.relative_to(ROOT)}: geometry has no bones")
        return set()
    bone_names = {bone.get("name", "") for bone in bones}
    if "" in bone_names:
        fail(f"{path.relative_to(ROOT)}: unnamed bone")
    cubes = 0
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for bone in bones:
        for index, cube in enumerate(bone.get("cubes", [])):
            cubes += 1
            origin = cube.get("origin")
            size = cube.get("size")
            if not isinstance(origin, list) or len(origin) != 3:
                fail(f"{path.relative_to(ROOT)}: cube missing 3D origin")
                continue
            if not isinstance(size, list) or len(size) != 3 or any(v <= 0 for v in size):
                fail(f"{path.relative_to(ROOT)}: cube has invalid size {size}")
                continue
            for axis in range(3):
                lo[axis] = min(lo[axis], float(origin[axis]))
                hi[axis] = max(hi[axis], float(origin[axis]) + float(size[axis]))
            for face in FACE_KEYS:
                face_data = cube.get("uv", {}).get(face)
                if not face_data:
                    fail(f"{path.relative_to(ROOT)}: cube missing {face} UV")
                    continue
                uv = face_data.get("uv", [0, 0])
                uv_size = face_data.get("uv_size", [0, 0])
                if not isinstance(uv, list) or len(uv) != 2 or not isinstance(uv_size, list) or len(uv_size) != 2:
                    fail(f"{path.relative_to(ROOT)}: malformed {face} UV")
                    continue
                u, v = uv
                uw, uh = uv_size
                if uw <= 0 or uh <= 0:
                    fail(f"{path.relative_to(ROOT)}: {face} has non-positive uv_size")
                if u < 0 or v < 0 or u + uw > texture_width or v + uh > texture_height:
                    fail(f"{path.relative_to(ROOT)}: {face} UV outside {texture_width}x{texture_height}: {uv} {uv_size}")
    if not cubes:
        fail(f"{path.relative_to(ROOT)}: geometry has no cubes")
    if block and cubes:
        if any(hi[i] - lo[i] > 30 for i in range(3)):
            fail(f"{path.relative_to(ROOT)}: block model exceeds 30px on an axis: {lo}..{hi}")
        if any(hi[i] < 0 or lo[i] > 16 for i in range(3)):
            fail(f"{path.relative_to(ROOT)}: block model has no pixel inside the block unit: {lo}..{hi}")
    notes.append(f"{path.relative_to(ROOT)}: {cubes} cubes, bounds {lo}..{hi}")
    return bone_names


def check_selection(path: Path, components: dict) -> None:
    selection = components.get("minecraft:selection_box")
    if not selection:
        return
    origin = selection.get("origin")
    size = selection.get("size")
    if not isinstance(origin, list) or not isinstance(size, list) or len(origin) != 3 or len(size) != 3:
        fail(f"{path.relative_to(ROOT)}: malformed selection_box")
        return
    lows = (-8, 0, -8)
    highs = (8, 16, 8)
    for axis in range(3):
        if origin[axis] < lows[axis] or origin[axis] > highs[axis]:
            fail(f"{path.relative_to(ROOT)}: selection origin outside block bounds")
        if origin[axis] + size[axis] < lows[axis] or origin[axis] + size[axis] > highs[axis]:
            fail(f"{path.relative_to(ROOT)}: selection extent outside block bounds")


def check_blockbench(path: Path) -> None:
    data = load(path)
    if not data:
        return
    meta = data.get("meta", {})
    if meta.get("model_format") != "bedrock":
        fail(f"{path.relative_to(ROOT)}: .bbmodel is not in Bedrock format")
    if not data.get("textures"):
        fail(f"{path.relative_to(ROOT)}: .bbmodel has no embedded texture")
    if not data.get("elements"):
        fail(f"{path.relative_to(ROOT)}: .bbmodel has no elements")
    for texture in data.get("textures", []):
        if not texture.get("source", "").startswith("data:image/png;base64,"):
            fail(f"{path.relative_to(ROOT)}: texture source is not embedded PNG data")
    for group in data.get("groups", []):
        if not UUID_RE.match(group.get("uuid", "")):
            fail(f"{path.relative_to(ROOT)}: invalid group UUID")
    if not data.get("outliner"):
        fail(f"{path.relative_to(ROOT)}: .bbmodel has an empty outliner")


def check_particles() -> dict[str, dict]:
    particles: dict[str, dict] = {}
    atlas_path = RP / "textures" / "particle" / "bloom_particles.png"
    atlas_size = texture_size(atlas_path) or (0, 0)
    for path in sorted((RP / "particles").glob("*.json")):
        data = load(path)
        if not data:
            continue
        effect = data.get("particle_effect", {})
        description = effect.get("description", {})
        identifier = description.get("identifier", "")
        if not identifier.startswith(NS):
            fail(f"{path.relative_to(ROOT)}: particle identifier must use bl:")
        if identifier in particles:
            fail(f"{path.relative_to(ROOT)}: duplicate particle {identifier}")
        particles[identifier] = data
        texture = description.get("basic_render_parameters", {}).get("texture", "")
        if not texture:
            fail(f"{path.relative_to(ROOT)}: particle has no texture")
        elif not (RP / (texture + ".png")).exists():
            fail(f"{path.relative_to(ROOT)}: missing particle texture {texture}.png")
        appearance = effect.get("components", {}).get("minecraft:particle_appearance_billboard", {})
        uv = appearance.get("uv", {})
        width = uv.get("texture_width")
        height = uv.get("texture_height")
        if (width, height) != atlas_size:
            fail(f"{path.relative_to(ROOT)}: particle texture size {width}x{height} != atlas {atlas_size}")
        u, v = uv.get("uv", [0, 0])
        uw, uh = uv.get("uv_size", [0, 0])
        if u < 0 or v < 0 or u + uw > (width or 0) or v + uh > (height or 0):
            fail(f"{path.relative_to(ROOT)}: particle UV outside atlas")
        if not effect.get("components"):
            fail(f"{path.relative_to(ROOT)}: particle has no components")
    return particles


def main() -> int:
    keys = lang_keys()
    bp_manifest = check_manifest(BP, "data")
    rp_uuid = rp_manifest.get("header", {}).get("uuid") if (rp_manifest := check_manifest(RP, "resources")) else None
    if bp_manifest and rp_uuid:
        if not any(dep.get("uuid") == rp_uuid for dep in bp_manifest.get("dependencies", [])):
            fail("behavior pack manifest does not depend on the resource pack UUID")
    if bp_manifest:
        server = [dep for dep in bp_manifest.get("dependencies", []) if dep.get("module_name") == "@minecraft/server"]
        if not server or server[0].get("version") != "2.0.0":
            fail("behavior pack must depend on @minecraft/server 2.0.0")
    if rp_manifest:
        for dep in rp_manifest.get("dependencies", []):
            if dep.get("uuid") and not UUID_RE.match(dep["uuid"]):
                fail("resource pack has an invalid dependency UUID")

    terrain = load(RP / "textures" / "terrain_texture.json") or {}
    item_atlas = load(RP / "textures" / "item_texture.json") or {}
    terrain_data = terrain.get("texture_data", {})
    item_data = item_atlas.get("texture_data", {})
    if not terrain_data:
        fail("terrain_texture.json has no texture_data")
    if not item_data:
        fail("item_texture.json has no texture_data")
    for key, value in terrain_data.items():
        texture_path = RP / (value.get("textures", "") + ".png")
        if not texture_path.exists():
            fail(f"terrain_texture {key}: missing {texture_path.relative_to(ROOT)}")
        else:
            texture_size(texture_path)
    for key, value in item_data.items():
        texture_path = RP / (value.get("textures", "") + ".png")
        if not texture_path.exists():
            fail(f"item_texture {key}: missing {texture_path.relative_to(ROOT)}")
        else:
            texture_size(texture_path)

    block_geo = geo_index(RP / "models" / "blocks")
    entity_geo = geo_index(RP / "models" / "entity")
    block_ids: set[str] = set()
    block_loot: dict[str, Path] = {}
    block_geometry_ids: set[str] = set()
    block_geo_checked: set[str] = set()
    for path in sorted((BP / "blocks").glob("*.json")):
        data = load(path)
        if not data:
            continue
        block = data.get("minecraft:block")
        if not block:
            fail(f"{path.relative_to(ROOT)}: missing minecraft:block")
            continue
        description = block.get("description", {})
        identifier = description.get("identifier", "")
        if not identifier.startswith(NS):
            fail(f"{path.relative_to(ROOT)}: block identifier must use bl:")
        if identifier in block_ids:
            fail(f"{path.relative_to(ROOT)}: duplicate block {identifier}")
        block_ids.add(identifier)
        components = block.get("components", {})
        if "minecraft:material_instances" not in components:
            fail(f"{path.relative_to(ROOT)}: missing material_instances")
        for face, material in components.get("minecraft:material_instances", {}).items():
            if face not in FACE_KEYS and face != "*":
                fail(f"{path.relative_to(ROOT)}: invalid material face {face}")
            texture = material.get("texture") if isinstance(material, dict) else None
            if texture not in terrain_data:
                fail(f"{path.relative_to(ROOT)}: material texture {texture!r} missing from terrain_texture.json")
        geometry = components.get("minecraft:geometry")
        if isinstance(geometry, str) and geometry.startswith("geometry."):
            if geometry not in block_geo:
                fail(f"{path.relative_to(ROOT)}: geometry {geometry} not found")
            else:
                block_geometry_ids.add(geometry)
                material = components.get("minecraft:material_instances", {}).get("*", {})
                texture_key = material.get("texture") if isinstance(material, dict) else None
                texture_path = RP / (terrain_data.get(texture_key, {}).get("textures", "") + ".png")
                if texture_path.exists():
                    size = texture_size(texture_path)
                    if size:
                        check_geometry(block_geo[geometry][0], block_geo[geometry][1], size[0], size[1], block=True)
                        block_geo_checked.add(geometry)
        elif geometry not in (None, "minecraft:geometry.full_block"):
            fail(f"{path.relative_to(ROOT)}: unexpected block geometry {geometry!r}")
        visual = components.get("minecraft:item_visual", {})
        if visual:
            visual_material = visual.get("material_instances", {}).get("*", {})
            visual_texture = visual_material.get("texture") if isinstance(visual_material, dict) else None
            if visual_texture not in terrain_data:
                fail(f"{path.relative_to(ROOT)}: item_visual texture missing")
            if visual.get("geometry") not in (geometry, "minecraft:geometry.full_block"):
                fail(f"{path.relative_to(ROOT)}: item_visual geometry mismatch")
        check_selection(path, components)
        light = components.get("minecraft:light_emission", 0)
        if not isinstance(light, int) or not 0 <= light <= 15:
            fail(f"{path.relative_to(ROOT)}: light_emission must be 0..15")
        display = components.get("minecraft:display_name", "")
        if display not in keys:
            fail(f"{path.relative_to(ROOT)}: missing language key {display}")
        loot = components.get("minecraft:loot")
        if loot:
            loot_path = BP / loot
            if not loot_path.exists():
                fail(f"{path.relative_to(ROOT)}: loot table {loot} missing")
            block_loot[identifier] = loot_path
        elif identifier not in {"bl:rainbow_portal", "bl:bloomheart"}:
            # The portal surface and the legacy decorative Bloomheart are
            # hidden world blocks; they intentionally have no item or loot.
            fail(f"{path.relative_to(ROOT)}: missing minecraft:loot")
        for face, material in components.get("minecraft:material_instances", {}).items():
            if not isinstance(material, dict):
                fail(f"{path.relative_to(ROOT)}: material {face} is not an object")
        destruction = components.get("minecraft:destruction_particles", {})
        if destruction:
            texture = destruction.get("texture")
            if texture not in terrain_data:
                fail(f"{path.relative_to(ROOT)}: destruction particle texture {texture!r} missing")
        for condition in components.get("minecraft:placement_filter", {}).get("conditions", []):
            for allowed in condition.get("allowed_blocks", []):
                if isinstance(allowed, str) and allowed.startswith(NS) and allowed not in block_ids:
                    # Custom blocks in placement filters are resolved in a second pass.
                    notes.append(f"{path.relative_to(ROOT)}: placement filter mentions {allowed}")

    # Resolve custom placement-filter references now that all block IDs are known.
    for path in sorted((BP / "blocks").glob("*.json")):
        data = load(path) or {}
        components = data.get("minecraft:block", {}).get("components", {})
        for condition in components.get("minecraft:placement_filter", {}).get("conditions", []):
            for allowed in condition.get("allowed_blocks", []):
                if isinstance(allowed, str) and allowed.startswith(NS) and allowed not in block_ids:
                    fail(f"{path.relative_to(ROOT)}: placement filter references unknown block {allowed}")

    if len(block_geo_checked) != len(block_geometry_ids):
        missing = block_geometry_ids - block_geo_checked
        if missing:
            fail(f"unchecked block geometries: {sorted(missing)}")

    item_ids: set[str] = set()
    for path in sorted((BP / "items").glob("*.json")):
        data = load(path)
        if not data:
            continue
        item = data.get("minecraft:item")
        if not item:
            fail(f"{path.relative_to(ROOT)}: missing minecraft:item")
            continue
        description = item.get("description", {})
        identifier = description.get("identifier", "")
        if not identifier.startswith(NS):
            fail(f"{path.relative_to(ROOT)}: item identifier must use bl:")
        if identifier in item_ids:
            fail(f"{path.relative_to(ROOT)}: duplicate item {identifier}")
        item_ids.add(identifier)
        components = item.get("components", {})
        icon = components.get("minecraft:icon", {}).get("textures", {}).get("default")
        if icon not in item_data:
            fail(f"{path.relative_to(ROOT)}: icon {icon!r} missing from item_texture.json")
        display = components.get("minecraft:display_name", {}).get("value", "")
        if display not in keys:
            fail(f"{path.relative_to(ROOT)}: missing language key {display}")
        if "minecraft:max_stack_size" in components and not 1 <= components["minecraft:max_stack_size"] <= 64:
            fail(f"{path.relative_to(ROOT)}: max_stack_size outside 1..64")

    for path in sorted((BP / "recipes").glob("*.json")):
        data = load(path)
        if not data:
            continue
        recipe = data.get("minecraft:recipe_shaped") or data.get("minecraft:recipe_shapeless")
        if not recipe:
            fail(f"{path.relative_to(ROOT)}: not a shaped/shapeless recipe")
            continue
        result = recipe.get("result", {}).get("item", "")
        if result not in item_ids and result not in block_ids:
            fail(f"{path.relative_to(ROOT)}: recipe result {result!r} is not a custom item or block")
        if not isinstance(recipe.get("result", {}).get("count", 1), int):
            fail(f"{path.relative_to(ROOT)}: recipe result count must be an integer")
        ingredients = list(recipe.get("ingredients", []))
        for row in recipe.get("pattern", []):
            ingredients.extend(recipe.get("key", {}).get(char, {"item": ""}).get("item") for char in row if char != " ")
        if not ingredients:
            fail(f"{path.relative_to(ROOT)}: recipe has no ingredients")
        for ingredient in ingredients:
            if isinstance(ingredient, dict):
                value = ingredient.get("item", "")
                if value.startswith(NS) and value not in item_ids and value not in block_ids:
                    fail(f"{path.relative_to(ROOT)}: unknown recipe ingredient {value}")
            elif isinstance(ingredient, str) and ingredient.startswith(NS):
                if ingredient not in item_ids and ingredient not in block_ids:
                    fail(f"{path.relative_to(ROOT)}: unknown recipe ingredient {ingredient}")

    for block_id, loot_path in block_loot.items():
        data = load(loot_path)
        if not data:
            continue
        entries = []
        for pool in data.get("pools", []):
            entries.extend(pool.get("entries", []))
        if not entries:
            fail(f"{loot_path.relative_to(ROOT)}: loot table has no entries")
        for entry in entries:
            name = entry.get("name", "")
            if name.startswith(NS) and name not in block_ids and name not in item_ids:
                fail(f"{loot_path.relative_to(ROOT)}: unknown loot item {name}")

    # Dimension and biome wiring.
    dimension_path = BP / "dimensions" / "bloomlands.json"
    dimension = load(dimension_path)
    if not dimension:
        fail(f"{dimension_path.relative_to(ROOT)}: missing")
    else:
        dimension_data = dimension.get("minecraft:dimension", {})
        if dimension_data.get("description", {}).get("identifier") != "bl:bloomlands":
            fail(f"{dimension_path.relative_to(ROOT)}: unexpected dimension identifier")
        generation = dimension_data.get("components", {}).get("minecraft:generation", {})
        if generation.get("generator_type") != "void":
            fail(f"{dimension_path.relative_to(ROOT)}: generator_type must be void")
        height = dimension_data.get("components", {}).get("minecraft:dimension_height", {})
        if height.get("min_y") != 0 or height.get("height_range") != 256:
            fail(f"{dimension_path.relative_to(ROOT)}: unexpected dimension height")
        default_biome = dimension_data.get("components", {}).get("minecraft:default_biome", {}).get("biome")
        if default_biome != "bl:bloomlands":
            fail(f"{dimension_path.relative_to(ROOT)}: default biome must be bl:bloomlands")

    biome_path = BP / "biomes" / "bloomlands.biome.json"
    biome = load(biome_path)
    biome_tags: set[str] = set()
    if not biome:
        fail(f"{biome_path.relative_to(ROOT)}: missing")
    else:
        biome_data = biome.get("minecraft:biome", {})
        if biome_data.get("description", {}).get("identifier") != "bl:bloomlands":
            fail(f"{biome_path.relative_to(ROOT)}: unexpected biome identifier")
        tags = biome_data.get("components", {}).get("minecraft:tags", {}).get("tags", [])
        biome_tags = set(tags)
        if "bloomlands" not in tags:
            fail(f"{biome_path.relative_to(ROOT)}: missing bloomlands tag")
        if "animal" not in tags:
            fail(f"{biome_path.relative_to(ROOT)}: missing animal tag")
        if "monster" in tags:
            fail(f"{biome_path.relative_to(ROOT)}: hostile monster tag is not allowed")
        probability = biome_data.get("components", {}).get("minecraft:creature_spawn_probability", {}).get("probability")
        if not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
            fail(f"{biome_path.relative_to(ROOT)}: invalid creature_spawn_probability")

    client_biome_path = RP / "biomes" / "bloomlands.client_biome.json"
    client_biome = load(client_biome_path)
    fog_ids: set[str] = set()
    for path in sorted((RP / "fogs").glob("*.json")):
        data = load(path)
        if not data:
            continue
        fog = data.get("minecraft:fog_settings", {})
        identifier = fog.get("description", {}).get("identifier", "")
        if not identifier.startswith(NS):
            fail(f"{path.relative_to(ROOT)}: fog identifier must use bl:")
        if identifier in fog_ids:
            fail(f"{path.relative_to(ROOT)}: duplicate fog {identifier}")
        fog_ids.add(identifier)
        distance = fog.get("distance", {})
        for kind, settings in distance.items():
            if kind not in {"air", "water", "weather"}:
                fail(f"{path.relative_to(ROOT)}: invalid fog distance kind {kind}")
            start, end = settings.get("fog_start"), settings.get("fog_end")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < 0 or end <= start:
                fail(f"{path.relative_to(ROOT)}: invalid fog range {start}..{end}")
            color = settings.get("fog_color")
            if not color or not HEX_RE.match(color):
                fail(f"{path.relative_to(ROOT)}: invalid fog color {color!r}")
    if not client_biome:
        fail(f"{client_biome_path.relative_to(ROOT)}: missing")
    else:
        client_data = client_biome.get("minecraft:client_biome", {})
        if client_data.get("description", {}).get("identifier") != "bl:bloomlands":
            fail(f"{client_biome_path.relative_to(ROOT)}: unexpected client biome identifier")
        fog = client_data.get("components", {}).get("minecraft:fog_appearance", {}).get("fog_identifier")
        if fog not in fog_ids:
            fail(f"{client_biome_path.relative_to(ROOT)}: unknown fog {fog!r}")

    # Entities, client entities, animations, controllers, spawn rules.
    entity_ids: set[str] = set()
    entity_loot: dict[str, Path] = {}
    for path in sorted((BP / "entities").glob("*.json")):
        data = load(path)
        if not data:
            continue
        entity = data.get("minecraft:entity", {})
        description = entity.get("description", {})
        identifier = description.get("identifier", "")
        if not identifier.startswith(NS):
            fail(f"{path.relative_to(ROOT)}: entity identifier must use bl:")
        if identifier in entity_ids:
            fail(f"{path.relative_to(ROOT)}: duplicate entity {identifier}")
        entity_ids.add(identifier)
        if not description.get("is_spawnable") or not description.get("is_summonable"):
            fail(f"{path.relative_to(ROOT)}: entity must be spawnable and summonable")
        components = entity.get("components", {})
        family = components.get("minecraft:type_family", {}).get("family", [])
        if "bloomling" not in family:
            fail(f"{path.relative_to(ROOT)}: entity is not in the bloomling family")
        if "monster" in family:
            fail(f"{path.relative_to(ROOT)}: entity may not be in the monster family")
        for component in ("minecraft:health", "minecraft:collision_box", "minecraft:movement", "minecraft:physics", "minecraft:persistent"):
            if component not in components:
                fail(f"{path.relative_to(ROOT)}: missing {component}")
        loot = components.get("minecraft:loot")
        if loot:
            loot_path = BP / loot
            if not loot_path.exists():
                fail(f"{path.relative_to(ROOT)}: loot table {loot} missing")
            else:
                entity_loot[identifier] = loot_path
        else:
            fail(f"{path.relative_to(ROOT)}: missing minecraft:loot")
        spawn_path = BP / "spawn_rules" / f"{path.stem}.json"
        spawn = load(spawn_path)
        if not spawn:
            fail(f"{spawn_path.relative_to(ROOT)}: missing spawn rules")
        else:
            spawn_rules = spawn.get("minecraft:spawn_rules", {})
            if spawn_rules.get("description", {}).get("identifier") != identifier:
                fail(f"{spawn_path.relative_to(ROOT)}: spawn rule identifier mismatch")
            conditions = spawn_rules.get("conditions", [])
            if not conditions:
                fail(f"{spawn_path.relative_to(ROOT)}: no spawn conditions")
            for condition in conditions:
                biome_filter = condition.get("minecraft:biome_filter", {})
                if biome_filter.get("value") not in biome_tags:
                    fail(f"{spawn_path.relative_to(ROOT)}: biome filter value not in biome tags")
                if "minecraft:weight" not in condition:
                    fail(f"{spawn_path.relative_to(ROOT)}: missing weight")

        client_path = RP / "entity" / f"{path.stem}.entity.json"
        client = load(client_path)
        if not client:
            fail(f"{client_path.relative_to(ROOT)}: missing")
            continue
        client_description = client.get("minecraft:client_entity", {}).get("description", {})
        if client_description.get("identifier") != identifier:
            fail(f"{client_path.relative_to(ROOT)}: identifier mismatch")
        geometry_id = client_description.get("geometry", {}).get("default")
        if geometry_id not in entity_geo:
            fail(f"{client_path.relative_to(ROOT)}: geometry {geometry_id} not found")
        texture_path = RP / (client_description.get("textures", {}).get("default", "") + ".png")
        if not texture_path.exists():
            fail(f"{client_path.relative_to(ROOT)}: missing texture {texture_path.relative_to(ROOT)}")
        texture_dimensions = texture_size(texture_path) if texture_path.exists() else None
        bone_names: set[str] = set()
        if geometry_id in entity_geo and texture_dimensions:
            bone_names = check_geometry(entity_geo[geometry_id][0], entity_geo[geometry_id][1],
                                        texture_dimensions[0], texture_dimensions[1], block=False)
        animations = client_description.get("animations", {})
        for short_name, animation_id in animations.items():
            if animation_id.startswith("controller."):
                continue
            supplier = None
            for animation_path in sorted((RP / "animations").glob("*.json")):
                animation_data = load(animation_path) or {}
                if animation_id in animation_data.get("animations", {}):
                    supplier = animation_data
                    break
            if not supplier:
                fail(f"{client_path.relative_to(ROOT)}: animation {animation_id} not found")
                continue
            for bone_name in supplier["animations"][animation_id].get("bones", {}):
                if bone_name not in bone_names:
                    fail(f"{client_path.relative_to(ROOT)}: animation {animation_id} references unknown bone {bone_name}")
        for short_name in client_description.get("scripts", {}).get("animate", []):
            if short_name not in animations:
                fail(f"{client_path.relative_to(ROOT)}: scripts.animate references undefined {short_name}")
        for controller_id in client_description.get("render_controllers", []):
            found = False
            for rc_path in sorted((RP / "render_controllers").glob("*.json")):
                rc = load(rc_path) or {}
                if controller_id in rc.get("render_controllers", {}):
                    found = True
                    break
            if not found:
                fail(f"{client_path.relative_to(ROOT)}: render controller {controller_id} not found")
        for controller_id in [value for value in animations.values() if value.startswith("controller.")]:
            controller_file = None
            for rc_path in sorted((RP / "animation_controllers").glob("*.json")):
                rc = load(rc_path) or {}
                if controller_id in rc.get("animation_controllers", {}):
                    controller_file = rc
                    break
            if not controller_file:
                fail(f"{client_path.relative_to(ROOT)}: animation controller {controller_id} not found")
                continue
            states = controller_file["animation_controllers"][controller_id].get("states", {})
            for state_name, state in states.items():
                for animation_name in state.get("animations", []):
                    if animation_name not in animations:
                        fail(f"{client_path.relative_to(ROOT)}: controller state {state_name} references undefined animation {animation_name}")
        if "spawn_egg" not in client_description:
            fail(f"{client_path.relative_to(ROOT)}: missing spawn_egg")
        for color_key in ("base_color", "overlay_color"):
            color = client_description.get("spawn_egg", {}).get(color_key)
            if not color or not HEX_RE.match(color):
                fail(f"{client_path.relative_to(ROOT)}: invalid spawn egg {color_key}")

    for entity_id, loot_path in entity_loot.items():
        data = load(loot_path) or {}
        for pool in data.get("pools", []):
            for entry in pool.get("entries", []):
                name = entry.get("name", "")
                if name.startswith(NS) and name not in item_ids and name not in block_ids:
                    fail(f"{loot_path.relative_to(ROOT)}: unknown loot item {name}")

    # Language coverage.
    for block_id in sorted(block_ids):
        if f"tile.{block_id}.name" not in keys:
            fail(f"missing language key tile.{block_id}.name")
    for item_id in sorted(item_ids):
        if f"item.{item_id}.name" not in keys:
            fail(f"missing language key item.{item_id}.name")
    for entity_id in sorted(entity_ids):
        if f"entity.{entity_id}.name" not in keys:
            fail(f"missing language key entity.{entity_id}.name")
        if f"item.spawn_egg.entity.{entity_id}.name" not in keys:
            fail(f"missing language key item.spawn_egg.entity.{entity_id}.name")
    for key in (
        "pack.name",
        "pack.description",
        "dimension.bl:bloomlands",
        "biome.bl:bloomlands",
        "bl.title.bloomlands",
        "bl.subtitle.bloomlands",
        "bl.portal.enter",
        "bl.portal.return",
        "bl.portal.rearm",
        "bl.portal.rooted",
    ):
        if key not in keys:
            fail(f"missing language key {key}")

    # Sound and particle references in the script.
    script_path = BP / "scripts" / "main.js"
    script = script_path.read_text(encoding="utf-8") if script_path.exists() else ""
    if not script:
        fail(f"{script_path.relative_to(ROOT)}: missing script")
    else:
        particles = check_particles()
        for particle_id in set(re.findall(r"spawnParticle\(\s*['\"]([^'\"]+)", script)):
            if particle_id not in particles:
                fail(f"{script_path.relative_to(ROOT)}: spawnParticle references unknown {particle_id}")
        for fog_id in set(re.findall(r"['\"](bl:bloomlands_[a-z_]+)['\"]", script)):
            if fog_id not in fog_ids:
                fail(f"{script_path.relative_to(ROOT)}: unknown fog {fog_id}")
        for required in ("world.tickingAreaManager", "playerInteractWithBlock", "world.afterEvents.worldLoad"):
            if required not in script:
                fail(f"{script_path.relative_to(ROOT)}: expected {required}")

    # Flipbook and texture-list integrity.
    flip = load(RP / "textures" / "flipbook_textures.json")
    if not flip:
        fail("flipbook_textures.json missing")
    else:
        for entry in flip:
            tile = entry.get("flipbook_texture", "")
            if not tile:
                fail("flipbook entry missing flipbook_texture")
                continue
            path = RP / (tile + ".png")
            if not path.exists():
                fail(f"flipbook texture {tile} missing")
                continue
            frames = entry.get("frames", [])
            if not frames:
                fail(f"flipbook texture {tile} has no frames")
            size = texture_size(path)
            if size:
                frame_height = size[1] // max(1, len(frames))
                if frame_height <= 0 or size[1] % max(1, len(frames)):
                    fail(f"flipbook texture {tile} height {size[1]} is not divisible by {len(frames)} frames")
    textures_list = load(RP / "textures" / "textures_list.json")
    if not isinstance(textures_list, list) or not textures_list:
        fail("textures_list.json is not a non-empty list")

    # Starter function.
    starter = BP / "functions" / "bloomlands" / "kit.mcfunction"
    if not starter.exists():
        fail(f"{starter.relative_to(ROOT)}: missing")
    else:
        for line in starter.read_text(encoding="utf-8").splitlines():
            words = line.strip().split()
            if len(words) >= 3 and words[0] == "give":
                item = words[2]
                if item.startswith(NS) and item not in item_ids and item not in block_ids:
                    fail(f"{starter.relative_to(ROOT)}: give references unknown item {item}")

    # Blockbench sources and previews.
    blockbench = ROOT / "blockbench"
    bbmodels = sorted(blockbench.rglob("*.bbmodel"))
    if len(bbmodels) < 10:
        fail(f"{blockbench.relative_to(ROOT)}: expected at least 10 Blockbench sources, found {len(bbmodels)}")
    for path in bbmodels:
        check_blockbench(path)
    for preview in ("block_textures.png", "entity_textures.png", "models.png", "portal_layout.png", "region_map.png"):
        preview_path = ROOT / "previews" / preview
        if not preview_path.exists():
            fail(f"{preview_path.relative_to(ROOT)}: missing preview")
    for test_preview in (ROOT / "previews").glob("_test_*.png"):
        fail(f"{test_preview.relative_to(ROOT)}: scratch preview should be removed")

    # Package.
    if not MCADDON.exists():
        fail(f"{MCADDON.relative_to(ROOT)}: missing")
    else:
        with zipfile.ZipFile(MCADDON) as zf:
            names = set(zf.namelist())
            expected = {
                f"Bloomlands_BP/{path.relative_to(BP).as_posix()}"
                for path in BP.rglob("*") if path.is_file()
            }
            expected |= {
                f"Bloomlands_RP/{path.relative_to(RP).as_posix()}"
                for path in RP.rglob("*") if path.is_file()
            }
            missing = expected - names
            extra = names - expected
            if missing:
                fail(f"{MCADDON.relative_to(ROOT)}: missing {len(missing)} packaged files: {sorted(missing)[:5]}")
            if extra:
                fail(f"{MCADDON.relative_to(ROOT)}: unexpected packaged files: {sorted(extra)[:5]}")
            for required in ("Bloomlands_BP/manifest.json", "Bloomlands_RP/manifest.json"):
                if required not in names:
                    fail(f"{MCADDON.relative_to(ROOT)}: missing {required}")

    if errors:
        print("FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Bloomlands validation passed")
    print(f"  blocks: {len(block_ids)}")
    print(f"  items: {len(item_ids)}")
    print(f"  entities: {len(entity_ids)}")
    print(f"  fogs: {len(fog_ids)}")
    print(f"  block geometries: {len(block_geo_checked)}")
    print(f"  entity geometries: {len(entity_geo)}")
    print(f"  language keys: {len(keys)}")
    print(f"  Blockbench sources: {len(bbmodels)}")
    print(f"  add-on: {MCADDON.name} ({MCADDON.stat().st_size} bytes)")
    for note in dict.fromkeys(notes):
        print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
