"""Offline structural validation for Petal & Star."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from PIL import Image, ImageChops

from content import build_textures, pack_icon

ROOT = Path(__file__).resolve().parent.parent
RP = ROOT / "resource_pack"
VERSION = (ROOT / "tools" / "VERSION").read_text(encoding="utf-8").strip()
ARCHIVE = ROOT / f"PetalAndStar-{VERSION}.mcpack"

EXPECTED_SIZES = {
    "blocks/water_still.png": (16, 512),
    "blocks/water_flow.png": (32, 1024),
    "blocks/lantern.png": (16, 48),
    "environment/sun.png": (32, 32),
    "environment/moon_phases.png": (128, 64),
    "environment/clouds.png": (256, 256),
}

CUTOUT_PATHS = {
    "blocks/glass.png",
    "blocks/glass_pane_top.png",
    "blocks/torch_on.png",
    "blocks/lantern.png",
    "blocks/tallgrass.png",
    "blocks/leaves_oak.png",
    "blocks/leaves_birch.png",
    "blocks/leaves_spruce.png",
    "blocks/leaves_jungle.png",
    "blocks/leaves_acacia.png",
    "blocks/leaves_big_oak.png",
    "blocks/cherry_leaves.png",
    "blocks/mangrove_leaves.png",
    "environment/sun.png",
    "environment/moon_phases.png",
    "environment/clouds.png",
}

CUTOUT_PATHS.update(
    {
        f"blocks/flower_{name}.png"
        for name in (
            "dandelion", "rose", "allium", "blue_orchid", "cornflower",
            "oxeye_daisy", "tulip_pink", "tulip_red", "tulip_orange",
            "tulip_white", "lily_of_the_valley", "houstonia", "paeonia",
            "wither_rose", "rose_blue",
        )
    }
)
CUTOUT_PATHS.update(
    {
        "blocks/double_plant_sunflower_front.png",
        "blocks/double_plant_sunflower_back.png",
        "blocks/double_plant_sunflower_top.png",
        "blocks/double_plant_sunflower_bottom.png",
    }
)

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def check_manifest() -> None:
    path = RP / "manifest.json"
    if not path.is_file():
        fail("manifest.json is missing")
        return
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"manifest.json is not valid JSON: {exc}")
        return
    if manifest.get("format_version") != 2:
        fail("manifest format_version must be 2")
    header = manifest.get("header", {})
    for key in ("name", "description", "uuid", "version", "min_engine_version"):
        if key not in header:
            fail(f"manifest header is missing {key}")
    if header.get("uuid") == manifest.get("modules", [{}])[0].get("uuid"):
        fail("header and module UUIDs must differ")
    modules = manifest.get("modules", [])
    if len(modules) != 1:
        fail("manifest must contain exactly one module")
    else:
        module = modules[0]
        if module.get("type") != "resources":
            fail("module type must be resources")
        if not module.get("uuid"):
            fail("module UUID is missing")
        if module.get("version") != header.get("version"):
            fail("module version must match header version")
    if not isinstance(manifest.get("metadata"), dict):
        fail("top-level metadata object is missing")
    else:
        authors = manifest["metadata"].get("authors")
        if not isinstance(authors, list) or not authors:
            fail("metadata.authors must be a non-empty list")


def check_textures(expected: dict[str, Image.Image]) -> None:
    tex_root = RP / "textures"
    if not tex_root.is_dir():
        fail("textures directory is missing")
        return
    actual_files = {
        p.relative_to(tex_root).as_posix()
        for p in tex_root.rglob("*")
        if p.is_file()
    }
    expected_files = set(expected)
    missing = sorted(expected_files - actual_files)
    extra = sorted(actual_files - expected_files)
    for rel in missing:
        fail(f"missing texture: {rel}")
    for rel in extra:
        fail(f"unexpected texture: {rel}")

    for rel, expected_img in sorted(expected.items()):
        path = tex_root / rel
        if not path.is_file():
            continue
        try:
            actual = Image.open(path).convert("RGBA")
        except Exception as exc:
            fail(f"cannot open {rel}: {exc}")
            continue
        want_size = EXPECTED_SIZES.get(rel, expected_img.size)
        if actual.size != want_size:
            fail(f"{rel} is {actual.size}, expected {want_size}")
        if actual.size != expected_img.size:
            fail(f"{rel} size changed between build and validation")
            continue
        diff = ImageChops.difference(actual, expected_img.convert("RGBA"))
        if diff.getbbox() is not None:
            fail(f"{rel} does not match the deterministic generator")
        if rel in CUTOUT_PATHS:
            alpha = actual.getchannel("A")
            if alpha.getextrema()[0] == 255:
                fail(f"{rel} should contain transparent pixels")
        if rel.startswith("blocks/") and rel not in CUTOUT_PATHS and not rel.endswith("water_still.png") and not rel.endswith("water_flow.png"):
            # Block textures should be fully opaque.  Water is excluded because
            # it is a special animated surface, and the cutout set is explicit.
            if actual.getchannel("A").getextrema()[0] != 255:
                fail(f"{rel} should be opaque")

    # Entity atlases keep the vanilla UV layout, but their sizes must match.
    entity_sizes = {
        "entity/cow/cow.png": (64, 32),
        "entity/cow/cow_v2.png": (64, 64),
        "entity/pig/pig.png": (64, 32),
        "entity/pig/pig_v3.png": (64, 64),
        "entity/chicken/chicken.png": (64, 32),
        "entity/bee/bee.png": (64, 64),
        "entity/bee/bee_nectar.png": (64, 64),
        "entity/sheep/sheep.tga": (64, 64),
        "entity/rabbit/rabbit_white.png": (64, 64),
        "entity/rabbit/rabbit_brown.png": (64, 64),
    }
    for rel, size in entity_sizes.items():
        path = tex_root / rel
        if not path.is_file():
            fail(f"missing entity texture: {rel}")
            continue
        with Image.open(path) as im:
            if im.size != size:
                fail(f"{rel} is {im.size}, expected {size}")


def check_icon() -> None:
    path = RP / "pack_icon.png"
    if not path.is_file():
        fail("pack_icon.png is missing")
        return
    with Image.open(path) as im:
        if im.size != (256, 256):
            fail(f"pack_icon.png is {im.size}, expected (256, 256)")
        if im.format != "PNG":
            fail("pack_icon.png must be a PNG")
    expected = pack_icon()
    actual = Image.open(path).convert("RGBA")
    if ImageChops.difference(actual, expected).getbbox() is not None:
        fail("pack_icon.png does not match the deterministic generator")


def check_archive() -> None:
    if not ARCHIVE.is_file():
        fail(f"archive is missing: {ARCHIVE.name}")
        return
    if ARCHIVE.stat().st_size == 0:
        fail("archive is empty")
    try:
        with zipfile.ZipFile(ARCHIVE) as zf:
            bad = zf.testzip()
            if bad is not None:
                fail(f"archive contains a corrupt member: {bad}")
            names = zf.namelist()
            if "manifest.json" not in names:
                fail("archive does not contain manifest.json at its root")
            if "pack_icon.png" not in names:
                fail("archive does not contain pack_icon.png at its root")
            source_files = {
                p.relative_to(RP).as_posix()
                for p in RP.rglob("*")
                if p.is_file()
            }
            if set(names) != source_files:
                fail("archive contents do not match resource_pack contents")
            for name in names:
                if name.startswith("/") or ".." in Path(name).parts:
                    fail(f"archive contains an unsafe path: {name}")
                if "__pycache__" in name or name.endswith(".pyc"):
                    fail(f"archive contains a build artefact: {name}")
    except zipfile.BadZipFile as exc:
        fail(f"archive is not a valid zip: {exc}")


def main() -> int:
    expected = build_textures()
    check_manifest()
    check_textures(expected)
    check_icon()
    check_archive()

    if errors:
        print(f"validation failed ({len(errors)} issue(s)):")
        for message in errors:
            print(f"  - {message}")
        return 1
    print(f"Petal & Star {VERSION} validated")
    print(f"  textures: {len(expected)}")
    print(f"  archive: {ARCHIVE.name} ({ARCHIVE.stat().st_size} bytes)")
    print("  manifest, icon, deterministic textures, and zip integrity: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
