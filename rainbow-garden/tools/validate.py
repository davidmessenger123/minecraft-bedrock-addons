"""
Structural and asset validator for Rainbow Garden.

This is intentionally stricter than a JSON syntax check: it resolves every
identifier, geometry, texture, animation, recipe and language key used by the
packs, and it checks the custom block model limits that Bedrock enforces.
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
MCADDON = ROOT / f"RainbowGarden-{VERSION}.mcaddon"

FACE_KEYS = {"north", "south", "east", "west", "up", "down"}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

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


def check_manifest(pack: Path, expected_type: str, dependency: str | None = None) -> dict | None:
    path = pack / "manifest.json"
    data = load(path)
    if not data:
        return None
    header = data.get("header", {})
    modules = data.get("modules", [])
    if data.get("format_version") != 2:
        fail(f"{path.relative_to(ROOT)}: format_version must be 2")
    if header.get("version") != VERSION_PARTS:
        fail(f"{path.relative_to(ROOT)}: header version {header.get('version')} != {VERSION_PARTS}")
    if header.get("min_engine_version") != [1, 21, 130]:
        fail(f"{path.relative_to(ROOT)}: min_engine_version must be [1,21,130]")
    for key in ("name", "description", "uuid"):
        if not header.get(key):
            fail(f"{path.relative_to(ROOT)}: missing header.{key}")
    if header.get("uuid") and not UUID_RE.match(header["uuid"]):
        fail(f"{path.relative_to(ROOT)}: invalid header UUID")
    if len(modules) != 1:
        fail(f"{path.relative_to(ROOT)}: expected exactly one module")
    else:
        module = modules[0]
        if module.get("type") != expected_type:
            fail(f"{path.relative_to(ROOT)}: module type {module.get('type')} != {expected_type}")
        if module.get("version") != VERSION_PARTS:
            fail(f"{path.relative_to(ROOT)}: module version {module.get('version')} != {VERSION_PARTS}")
        if module.get("uuid") and not UUID_RE.match(module["uuid"]):
            fail(f"{path.relative_to(ROOT)}: invalid module UUID")
    deps = data.get("dependencies", [])
    if dependency:
        if not any(d.get("uuid") == dependency for d in deps):
            fail(f"{path.relative_to(ROOT)}: missing dependency {dependency}")
    elif deps:
        notes.append(f"{path.relative_to(ROOT)}: has {len(deps)} dependency/ies")
    return data


def lang_keys() -> set[str]:
    keys = set()
    for pack in (BP, RP):
        path = pack / "texts" / "en_US.lang"
        if not path.exists():
            fail(f"{path.relative_to(ROOT)}: missing")
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                keys.add(line.split("=", 1)[0])
    return keys


def texture_size(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as img:
            return img.size
    except Exception as exc:
        fail(f"{path.relative_to(ROOT)}: cannot read PNG: {exc}")
        return None


def check_geometry(path: Path, texture_width: int, texture_height: int, block: bool) -> dict | None:
    data = load(path)
    if not data:
        return None
    entries = data.get("minecraft:geometry", [])
    if len(entries) != 1:
        fail(f"{path.relative_to(ROOT)}: expected one geometry entry")
        return None
    entry = entries[0]
    desc = entry.get("description", {})
    geometry_id = desc.get("identifier", "")
    if not geometry_id:
        fail(f"{path.relative_to(ROOT)}: missing geometry identifier")
    cubes = []
    for bone in entry.get("bones", []):
        for cube in bone.get("cubes", []):
            cubes.append(cube)
            size = cube.get("size", [])
            if len(size) != 3 or any(v <= 0 for v in size):
                fail(f"{path.relative_to(ROOT)}: cube has invalid size {size}")
                continue
            for face in FACE_KEYS:
                fuv = cube.get("uv", {}).get(face)
                if not fuv:
                    fail(f"{path.relative_to(ROOT)}: cube missing {face} UV")
                    continue
                u, v = fuv.get("uv", [0, 0])
                uw, uh = fuv.get("uv_size", [0, 0])
                if uw <= 0 or uh <= 0:
                    fail(f"{path.relative_to(ROOT)}: cube {face} has non-positive uv_size")
                if u < 0 or v < 0 or u + uw > texture_width or v + uh > texture_height:
                    fail(f"{path.relative_to(ROOT)}: {face} UV [{u},{v},{uw},{uh}] outside {texture_width}x{texture_height}")
    if not cubes:
        fail(f"{path.relative_to(ROOT)}: geometry has no cubes")
        return entry
    lo = [min(c["origin"][i] for c in cubes) for i in range(3)]
    hi = [max(c["origin"][i] + c["size"][i] for c in cubes) for i in range(3)]
    if block:
        if any(hi[i] - lo[i] > 30 for i in range(3)):
            fail(f"{path.relative_to(ROOT)}: block model exceeds 30px on an axis: {lo}..{hi}")
        if any(hi[i] < 0 or lo[i] > 16 for i in range(3)):
            fail(f"{path.relative_to(ROOT)}: block model has no pixel inside the block unit: {lo}..{hi}")
    notes.append(f"{path.relative_to(ROOT)}: {len(cubes)} cubes, bounds {lo}..{hi}")
    return entry


def main() -> int:
    bp_manifest = check_manifest(BP, "data")
    rp_manifest = check_manifest(RP, "resources", bp_manifest.get("header", {}).get("uuid") if bp_manifest else None)
    keys = lang_keys()

    terrain = load(RP / "textures" / "terrain_texture.json") or {}
    item_atlas = load(RP / "textures" / "item_texture.json") or {}
    terrain_data = terrain.get("texture_data", {})
    item_data = item_atlas.get("texture_data", {})

    block_ids = set()
    item_ids = set()
    block_geometries = {}
    for path in sorted((BP / "blocks").glob("*.json")):
        data = load(path)
        if not data:
            continue
        block = data.get("minecraft:block", {})
        desc = block.get("description", {})
        block_id = desc.get("identifier", "")
        components = block.get("components", {})
        if not block_id.startswith("rg:"):
            fail(f"{path.relative_to(ROOT)}: block identifier must use rg: namespace")
        if block_id in block_ids:
            fail(f"{path.relative_to(ROOT)}: duplicate block {block_id}")
        block_ids.add(block_id)
        geometry = components.get("minecraft:geometry")
        if not geometry:
            fail(f"{path.relative_to(ROOT)}: missing minecraft:geometry")
        if isinstance(geometry, str) and geometry.startswith("geometry."):
            geo_path = RP / "models" / "blocks" / f"{geometry.split('.')[-1]}.geo.json"
            # The file name is not always the last segment; search by identifier below.
            if not geo_path.exists():
                candidates = list((RP / "models" / "blocks").glob("*.geo.json"))
                geo_path = next((p for p in candidates if load(p) and
                                 load(p)["minecraft:geometry"][0]["description"]["identifier"] == geometry), None)
            if not geo_path:
                fail(f"{path.relative_to(ROOT)}: geometry {geometry} not found")
            else:
                block_geometries[block_id] = geo_path
        material = components.get("minecraft:material_instances", {}).get("*", {})
        texture = material.get("texture")
        if not texture:
            fail(f"{path.relative_to(ROOT)}: missing material texture")
        elif texture not in terrain_data:
            fail(f"{path.relative_to(ROOT)}: texture key {texture} missing from terrain_texture.json")
        else:
            tex_path = RP / (terrain_data[texture]["textures"] + ".png")
            size = texture_size(tex_path)
            if size:
                if texture.startswith("rg_rainbow_lantern") and size != (16, 16):
                    notes.append(f"{tex_path.relative_to(ROOT)}: lantern texture is {size}, expected 16x16 for full block")
        if texture and geometry and block_id in block_geometries:
            size = texture_size(RP / (terrain_data[texture]["textures"] + ".png"))
            if size:
                check_geometry(block_geometries[block_id], size[0], size[1], block=True)
        visual = components.get("minecraft:item_visual", {})
        if visual:
            vmat = visual.get("material_instances", {}).get("*", {})
            if vmat.get("texture") not in terrain_data:
                fail(f"{path.relative_to(ROOT)}: item_visual texture missing")
            if visual.get("geometry") not in (geometry, "minecraft:geometry.full_block"):
                fail(f"{path.relative_to(ROOT)}: item_visual geometry mismatch")
        selection = components.get("minecraft:selection_box")
        if selection:
            origin, size = selection.get("origin"), selection.get("size")
            if not origin or not size or len(origin) != 3 or len(size) != 3:
                fail(f"{path.relative_to(ROOT)}: malformed selection_box")
            elif any(origin[i] < (-8 if i != 1 else 0) or origin[i] > 8 for i in range(3)):
                fail(f"{path.relative_to(ROOT)}: selection origin outside [-8,0,-8]..[8,16,8]")
            elif any(origin[i] + size[i] < (-8 if i != 1 else 0) or
                     origin[i] + size[i] > (8 if i != 1 else 16) for i in range(3)):
                fail(f"{path.relative_to(ROOT)}: selection extent outside [-8,0,-8]..[8,16,8]")
        light = components.get("minecraft:light_emission", 0)
        if not isinstance(light, int) or not 0 <= light <= 15:
            fail(f"{path.relative_to(ROOT)}: light_emission must be 0..15")
        name_key = components.get("minecraft:display_name", "")
        if name_key not in keys:
            fail(f"{path.relative_to(ROOT)}: missing language key {name_key}")

    for path in sorted((BP / "items").glob("*.json")):
        data = load(path)
        if not data:
            continue
        item = data.get("minecraft:item", {})
        desc = item.get("description", {})
        item_id = desc.get("identifier", "")
        components = item.get("components", {})
        if not item_id.startswith("rg:"):
            fail(f"{path.relative_to(ROOT)}: item identifier must use rg: namespace")
        if item_id in item_ids:
            fail(f"{path.relative_to(ROOT)}: duplicate item {item_id}")
        item_ids.add(item_id)
        icon = components.get("minecraft:icon", {}).get("textures", {}).get("default")
        if icon not in item_data:
            fail(f"{path.relative_to(ROOT)}: icon key {icon} missing from item_texture.json")
        else:
            texture_size(RP / (item_data[icon]["textures"] + ".png"))
        display = components.get("minecraft:display_name", {}).get("value", "")
        if display not in keys:
            fail(f"{path.relative_to(ROOT)}: missing language key {display}")
        placer = components.get("minecraft:block_placer", {})
        if placer.get("block") not in block_ids:
            fail(f"{path.relative_to(ROOT)}: block_placer references unknown block {placer.get('block')}")

    for path in sorted((BP / "recipes").glob("*.json")):
        data = load(path)
        if not data:
            continue
        recipe = data.get("minecraft:recipe_shaped") or data.get("minecraft:recipe_shapeless")
        if not recipe:
            fail(f"{path.relative_to(ROOT)}: not a shaped/shapeless recipe")
            continue
        result = recipe.get("result", {}).get("item")
        if result not in item_ids and result not in block_ids:
            fail(f"{path.relative_to(ROOT)}: recipe result {result} is not a custom item or block")
        ingredients = recipe.get("ingredients", [])
        if not ingredients:
            for row in recipe.get("pattern", []):
                ingredients += list(row.replace(" ", ""))
        if not ingredients:
            fail(f"{path.relative_to(ROOT)}: recipe has no ingredients")
        for ing in ingredients:
            if isinstance(ing, dict):
                value = ing.get("item")
                if value and value.startswith("rg:") and value not in item_ids:
                    fail(f"{path.relative_to(ROOT)}: unknown recipe ingredient {value}")

    # Entity
    entity_path = BP / "entities" / "rainbow_butterfly.json"
    entity = load(entity_path)
    entity_id = None
    if entity:
        desc = entity.get("minecraft:entity", {}).get("description", {})
        entity_id = desc.get("identifier")
        if entity_id != "rg:rainbow_butterfly":
            fail(f"{entity_path.relative_to(ROOT)}: unexpected identifier {entity_id}")
        if not desc.get("is_spawnable") or not desc.get("is_summonable"):
            fail(f"{entity_path.relative_to(ROOT)}: entity must be spawnable and summonable")
        components = entity.get("minecraft:entity", {}).get("components", {})
        if "minecraft:damage_sensor" not in components:
            fail(f"{entity_path.relative_to(ROOT)}: butterfly should be damage-proof")
        if "minecraft:persistent" not in components:
            fail(f"{entity_path.relative_to(ROOT)}: butterfly should be persistent")
    client_path = RP / "entity" / "rainbow_butterfly.entity.json"
    client = load(client_path)
    if client:
        cdesc = client.get("minecraft:client_entity", {}).get("description", {})
        if cdesc.get("identifier") != entity_id:
            fail(f"{client_path.relative_to(ROOT)}: client identifier mismatch")
        geo_id = cdesc.get("geometry", {}).get("default")
        tex_path = RP / (cdesc.get("textures", {}).get("default", "") + ".png")
        if not tex_path.exists():
            fail(f"{client_path.relative_to(ROOT)}: missing texture {tex_path}")
        else:
            size = texture_size(tex_path)
            if size:
                geo_file = RP / "models" / "entity" / "rainbow_butterfly.geo.json"
                geo = check_geometry(geo_file, size[0], size[1], block=False)
                if geo and geo["description"]["identifier"] != geo_id:
                    fail(f"{client_path.relative_to(ROOT)}: geometry identifier mismatch")
        anim = cdesc.get("animations", {}).get("fly")
        anim_file = RP / "animations" / "rainbow_butterfly.animation.json"
        anim_data = load(anim_file) or {}
        if anim not in anim_data.get("animations", {}):
            fail(f"{client_path.relative_to(ROOT)}: animation {anim} missing")
        controller = cdesc.get("render_controllers", [None])[0]
        rc = load(RP / "render_controllers" / "rainbow_butterfly.render_controllers.json") or {}
        if controller not in rc.get("render_controllers", {}):
            fail(f"{client_path.relative_to(ROOT)}: render controller {controller} missing")
        if "spawn_egg" not in cdesc:
            fail(f"{client_path.relative_to(ROOT)}: missing spawn_egg colours")
    spawn_path = BP / "spawn_rules" / "rainbow_butterfly.json"
    spawn = load(spawn_path)
    if spawn:
        if spawn.get("minecraft:spawn_rules", {}).get("description", {}).get("identifier") != entity_id:
            fail(f"{spawn_path.relative_to(ROOT)}: spawn rule identifier mismatch")

    # Animation bones
    anim_file = RP / "animations" / "rainbow_butterfly.animation.json"
    anim_data = load(anim_file) or {}
    geo_file = RP / "models" / "entity" / "rainbow_butterfly.geo.json"
    geo = load(geo_file) or {}
    bone_names = {b["name"] for b in geo.get("minecraft:geometry", [{}])[0].get("bones", [])}
    for anim_name, anim in anim_data.get("animations", {}).items():
        for bone in anim.get("bones", {}):
            if bone not in bone_names:
                fail(f"{anim_file.relative_to(ROOT)}: animation {anim_name} references unknown bone {bone}")

    # Language
    for key in ["pack.name", "pack.description",
                "entity.rg:rainbow_butterfly.name",
                "entity.rg.rainbow_butterfly.name",
                "item.spawn_egg.entity.rg:rainbow_butterfly.name",
                "item.spawn_egg.entity.rg.rainbow_butterfly.name"]:
        if key not in keys:
            fail(f"missing language key {key}")

    # Atlases / files
    for key, value in terrain_data.items():
        path = RP / (value["textures"] + ".png")
        if not path.exists():
            fail(f"terrain_texture {key}: missing {path.relative_to(ROOT)}")
    for key, value in item_data.items():
        path = RP / (value["textures"] + ".png")
        if not path.exists():
            fail(f"item_texture {key}: missing {path.relative_to(ROOT)}")

    # Optional starter function
    starter = BP / "functions" / "rainbow_garden" / "starter.mcfunction"
    if not starter.exists():
        fail(f"{starter.relative_to(ROOT)}: missing starter function")
    else:
        for line in starter.read_text(encoding="utf-8").splitlines():
            words = line.strip().split()
            if len(words) >= 3 and words[0] == "give":
                item = words[2]
                if item.startswith("rg:") and item not in item_ids and item not in block_ids:
                    fail(f"{starter.relative_to(ROOT)}: give references unknown item {item}")
            if len(words) >= 2 and words[0] == "summon":
                if words[1] != entity_id:
                    fail(f"{starter.relative_to(ROOT)}: summon references unknown entity {words[1]}")

    # Zip
    if not MCADDON.exists():
        fail(f"{MCADDON.relative_to(ROOT)}: missing")
    else:
        with zipfile.ZipFile(MCADDON) as zf:
            names = set(zf.namelist())
            for required in ["behavior_pack/manifest.json", "resource_pack/manifest.json"]:
                if required not in names:
                    fail(f"{MCADDON.relative_to(ROOT)}: missing {required}")
            expected = sum(1 for p in list(BP.rglob("*")) + list(RP.rglob("*")) if p.is_file())
            if len(names) != expected:
                fail(f"{MCADDON.relative_to(ROOT)}: has {len(names)} entries, expected {expected}")

    if errors:
        print("FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Rainbow Garden validation passed")
    print(f"  blocks: {len(block_ids)}")
    print(f"  items: {len(item_ids)}")
    print(f"  custom block geometries: {len(block_geometries)}")
    print(f"  entity: {entity_id}")
    print(f"  language keys: {len(keys)}")
    print(f"  add-on: {MCADDON.name} ({MCADDON.stat().st_size} bytes)")
    for note in dict.fromkeys(notes):
        print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
