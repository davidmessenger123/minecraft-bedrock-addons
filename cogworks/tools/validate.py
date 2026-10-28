"""Structural validation for the Cogworks add-on."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
PREVIEWS = ROOT / "previews"
TOOLS = ROOT / "tools"
VERSION = (TOOLS / "VERSION").read_text(encoding="utf-8").strip()
PARTS = [int(v) for v in VERSION.split(".")]
ADDON = ROOT / f"Cogworks-{VERSION}.mcaddon"

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


def main() -> int:
    bp_manifest = load(BP / "manifest.json")
    rp_manifest = load(RP / "manifest.json")
    for name, data in (("BP", bp_manifest), ("RP", rp_manifest)):
        if not data:
            continue
        header = data.get("header", {})
        if header.get("version") != PARTS:
            fail(f"{name} manifest version is not {PARTS}")
        if header.get("min_engine_version") != [1, 26, 60]:
            fail(f"{name} manifest min_engine_version must be [1,26,60]")
        if not header.get("uuid"):
            fail(f"{name} manifest has no UUID")
        modules = data.get("modules", [])
        if not any(module.get("type") == "script" for module in modules) and name == "BP":
            fail("BP has no script module")
        if not any(module.get("type") == "resources" for module in modules) and name == "RP":
            fail("RP has no resources module")
        for module in modules:
            if module.get("version") != PARTS:
                fail(f"{name} module version does not match {PARTS}")

    block_ids: set[str] = set()
    block_data: dict[str, dict] = {}
    for path in sorted((BP / "blocks").glob("*.json")):
        data = load(path)
        if not data:
            continue
        block = data.get("minecraft:block", {})
        desc = block.get("description", {})
        ident = desc.get("identifier", "")
        if not ident.startswith("cw:"):
            fail(f"{path.name}: block identifier must use cw:")
        if ident in block_ids:
            fail(f"{path.name}: duplicate block {ident}")
        block_ids.add(ident)
        components = block.get("components", {})
        if not components.get("minecraft:geometry"):
            fail(f"{path.name}: missing geometry")
        if components.get("cw:machine") is not None:
            if "minecraft:tick" not in components:
                fail(f"{path.name}: machine has no tick component")
            if "minecraft:block_entity" not in components:
                fail(f"{path.name}: machine has no block entity")
        loot = components.get("minecraft:loot")
        if loot and not (BP / loot).is_file():
            fail(f"{path.name}: missing loot table {loot}")
        if ident == "cw:conveyor":
            states = desc.get("states", {})
            if "cw:facing" not in states:
                fail("conveyor: missing cw:facing state")
            if not block.get("permutations"):
                fail("conveyor: missing direction permutations")
        block_data[ident] = data

    geo_ids: set[str] = set()
    for path in sorted((RP / "models" / "blocks").glob("*.geo.json")):
        data = load(path)
        if not data:
            continue
        for entry in data.get("minecraft:geometry", []):
            ident = entry.get("description", {}).get("identifier", "")
            if not ident:
                fail(f"{path.name}: missing geometry identifier")
            geo_ids.add(ident)

    terrain = load(RP / "textures" / "terrain_texture.json") or {}
    terrain_data = terrain.get("texture_data", {})
    if "cw_blocks" not in terrain_data:
        fail("terrain_texture.json missing cw_blocks")
    elif not (RP / (terrain_data["cw_blocks"].get("textures", "") + ".png")).is_file():
        fail("cw_blocks atlas PNG is missing")

    item_data = load(RP / "textures" / "item_texture.json") or {}
    item_ids: set[str] = set()
    for path in sorted((BP / "items").glob("*.json")):
        data = load(path)
        if not data:
            continue
        item = data.get("minecraft:item", {})
        desc = item.get("description", {})
        ident = desc.get("identifier", "")
        if not ident.startswith("cw:"):
            fail(f"{path.name}: item identifier must use cw:")
        if not str(data.get("format_version", "")).startswith("1."):
            fail(f"{path.name}: invalid item format version")
        item_ids.add(ident)
        icon = item.get("components", {}).get("minecraft:icon", {})
        short = icon.get("textures", {}).get("default") if isinstance(icon, dict) else None
        if short and short not in item_data.get("texture_data", {}):
            fail(f"{path.name}: icon {short} missing from item_texture.json")

    for path in sorted((BP / "recipes").glob("*.json")):
        data = load(path)
        if not data:
            continue
        recipe = data.get("minecraft:recipe_shaped") or data.get("minecraft:recipe_shapeless")
        if not recipe:
            fail(f"{path.name}: unknown recipe type")
            continue
        result = recipe.get("result", {}).get("item")
        if result and result.startswith("cw:") and result not in item_ids and result not in block_ids:
            fail(f"{path.name}: unknown result {result}")
        ingredients = recipe.get("ingredients", [])
        if recipe.get("pattern"):
            for values in recipe.get("key", {}).values():
                ingredients.append(values)
        for ingredient in ingredients:
            name = ingredient.get("item") if isinstance(ingredient, dict) else None
            if name and name.startswith("cw:") and name not in item_ids and name not in block_ids:
                fail(f"{path.name}: unknown ingredient {name}")

    for block_id, data in block_data.items():
        components = data.get("minecraft:block", {}).get("components", {})
        geometry = components.get("minecraft:geometry")
        if geometry not in geo_ids:
            fail(f"{block_id}: geometry {geometry} not found")
        for material in components.get("minecraft:material_instances", {}).values():
            if isinstance(material, dict) and material.get("texture") not in terrain_data:
                fail(f"{block_id}: material texture missing from atlas")

    lang = (BP / "texts" / "en_US.lang").read_text(encoding="utf-8")
    for block_id in block_ids:
        key = f"tile.{block_id}.name"
        if key not in lang:
            fail(f"missing language key {key}")
    for item_id in item_ids:
        key = f"item.{item_id}.name"
        if key not in lang:
            fail(f"missing language key {key}")

    script = (BP / "scripts" / "main.js").read_text(encoding="utf-8")
    if "registerCustomComponent" not in script:
        fail("script does not register the machine custom component")
    if "cw:machine" not in script:
        fail("script does not refer to cw:machine")

    if not (ROOT / "blockbench" / "blocks").is_dir():
        fail("Blockbench source directory is missing")
    sources = list((ROOT / "blockbench" / "blocks").glob("*.bbmodel"))
    if len(sources) != len(block_ids):
        fail(f"Blockbench sources {len(sources)} != blocks {len(block_ids)}")
    if not (PREVIEWS / "models.png").is_file():
        fail("previews/models.png is missing")
    if not (PREVIEWS / "materials.png").is_file():
        fail("previews/materials.png is missing")

    if not ADDON.is_file():
        fail("packaged .mcaddon is missing")
    else:
        with zipfile.ZipFile(ADDON) as z:
            names = set(z.namelist())
            for folder in ("Cogworks_BP/manifest.json", "Cogworks_RP/manifest.json"):
                if folder not in names:
                    fail(f"package missing {folder}")

    print("Cogworks validation")
    print(f"  blocks: {len(block_ids)}")
    print(f"  items: {len(item_ids)}")
    print(f"  geometries: {len(geo_ids)}")
    print(f"  Blockbench sources: {len(sources)}")
    print(f"  add-on: {ADDON.name} ({ADDON.stat().st_size if ADDON.exists() else 0} bytes)")
    if notes:
        for note in notes:
            print(f"  note: {note}")
    if errors:
        print("FAILED")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
