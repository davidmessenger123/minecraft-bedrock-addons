#!/usr/bin/env python3
"""Validate the finished Candyland resource pack.

Checks:
  * every source colour texture (PBR companions excluded) is represented
  * every generated image exists, decodes, and has the right dimensions
  * terrain/item/flipbook/texture_list references all resolve
  * flipbook frame indices fit inside the strip
  * manifest, icon, language file and packaged .mcpack are present
"""
import json
import os
import re
import struct
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "resource_pack")
TEX = os.path.join(PACK, "textures")
SRC_ROOT = os.environ.get(
    "BEDROCK_SAMPLES", "/tmp/opencode/bedrock-samples/resource_pack")
SRC = os.path.join(SRC_ROOT, "textures")
DIST = os.path.join(ROOT, "dist")
ICON = os.path.join(PACK, "pack_icon.png")
MANIFEST = os.path.join(PACK, "manifest.json")
MCPACK = os.path.join(DIST, "Candyland-v1.0.0.mcpack")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import pnglib  # noqa: E402

IMAGE_EXTS = (".png", ".tga", ".jpg", ".jpeg")
PBR_SUFFIXES = ("_mers", "_mer", "_heightmap", "_height")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def relaxed_json(path):
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read()
    text = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("//"))
    return json.loads(text)


def resolve_ref(ref):
    if not isinstance(ref, str):
        return None
    path = ref[9:] if ref.startswith("textures/") else ref
    path = path.lstrip("/")
    base, ext = os.path.splitext(path)
    if ext.lower() in IMAGE_EXTS:
        candidates = [path]
    else:
        candidates = [path + e for e in IMAGE_EXTS]
    for candidate in candidates:
        full = os.path.join(TEX, *candidate.split("/"))
        if os.path.isfile(full):
            return full
    return None


def walk_refs(value):
    if isinstance(value, str):
        if value.startswith("textures/"):
            yield value
    elif isinstance(value, list):
        for item in value:
            yield from walk_refs(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_refs(item)


def image_size(path):
    if path.lower().endswith((".jpg", ".jpeg")):
        out = subprocess.check_output(
            ["magick", "identify", "-format", "%w %h", path],
            stderr=subprocess.DEVNULL)
        w, h = out.decode().split()
        return int(w), int(h)
    w, h, _px = pnglib.read_image(path)
    return w, h


def expected_path(entry):
    if entry["category"] == "colormap":
        return os.path.join("colormap", entry["name"] + ".png")
    return os.path.join(*entry["base"].split("/")) + "." + entry["src_ext"]


def display_dims(entry):
    """Blocks and items are rendered at the 32px target; the rest is native."""
    w, h = entry["w"], entry["h"]
    if entry["category"] not in ("blocks", "items"):
        return w, h
    if entry["frames"] > 1:
        scale = max(1, 32 // w)
    else:
        short = min(w, h)
        scale = 1 if short >= 32 else max(1, 32 // short)
    return w * scale, h * scale


def main():
    errors = []
    warnings = []
    inv = json.load(open(os.path.join(ROOT, "build", "inventory.json")))
    entries = inv["textures"]

    # ---------------------------------------------------------- source coverage
    source_bases = set()
    for root, _dirs, files in os.walk(SRC):
        for fn in files:
            if not fn.lower().endswith(IMAGE_EXTS):
                continue
            rel = os.path.relpath(os.path.join(root, fn), SRC).replace(os.sep, "/")
            base, ext = os.path.splitext(rel)
            ext = ext[1:].lower()
            name = base.split("/")[-1]
            if name.endswith(PBR_SUFFIXES):
                continue
            if name.endswith("_normal") and ext == "tga":
                continue
            source_bases.add(base)
    inv_bases = {e["base"] for e in entries}
    if source_bases - inv_bases:
        errors.append("source colour textures absent from inventory: %s"
                      % sorted(source_bases - inv_bases)[:20])
    if inv_bases - source_bases:
        warnings.append("inventory has non-source entries: %s"
                        % sorted(inv_bases - source_bases)[:20])

    # ---------------------------------------------------------- image coverage
    expected = {}
    for entry in entries:
        rel = expected_path(entry)
        ew, eh = display_dims(entry)
        expected[rel.replace(os.sep, "/")] = (ew, eh, entry["base"])
    extras = {
        "blocks/cake.png": None,
        "items/camera.png": None,
    }
    actual = set()
    for root, _dirs, files in os.walk(TEX):
        for fn in files:
            if fn.lower().endswith(IMAGE_EXTS):
                actual.add(os.path.relpath(os.path.join(root, fn), TEX).replace(os.sep, "/"))
    missing = sorted(set(expected) - actual)
    unexpected = sorted(actual - set(expected) - set(extras))
    if missing:
        errors.append("missing generated textures: %s" % missing[:30])
    if unexpected:
        warnings.append("unexpected generated images: %s" % unexpected[:30])
    missing_extras = sorted(x for x in extras if x not in actual)
    if missing_extras:
        errors.append("missing compatibility textures: %s" % missing_extras)

    # ---------------------------------------------------------- dimensions/decode
    bad_images = []
    for rel, (ew, eh, base) in sorted(expected.items()):
        full = os.path.join(TEX, *rel.split("/"))
        if not os.path.isfile(full):
            continue
        try:
            w, h = image_size(full)
        except Exception as exc:  # noqa: BLE001
            bad_images.append((rel, "decode: " + repr(exc)))
            continue
        if (w, h) != (ew, eh):
            bad_images.append((rel, "dims %s != %s" % ((w, h), (ew, eh))))
    if bad_images:
        errors.append("bad texture images: %s" % bad_images[:30])

    # The two compatibility textures should at least decode.
    for rel in extras:
        full = os.path.join(TEX, *rel.split("/"))
        if os.path.isfile(full):
            try:
                image_size(full)
            except Exception as exc:  # noqa: BLE001
                errors.append("bad compatibility image %s: %r" % (rel, exc))

    # ---------------------------------------------------------- tint masks
    tint_bad = []
    for entry in entries:
        if not entry["tint_mask"]:
            continue
        full = os.path.join(TEX, *expected_path(entry).split("/"))
        if not os.path.isfile(full):
            continue
        try:
            _w, _h, px = pnglib.read_image(full)
        except Exception:
            continue
        worst = 0
        for i in range(0, len(px), 4):
            if px[i + 3] < 128:
                continue
            spread = max(px[i], px[i + 1], px[i + 2]) - min(px[i], px[i + 1], px[i + 2])
            worst = max(worst, spread)
        if worst > 20:
            tint_bad.append((entry["base"], worst))
    if tint_bad:
        warnings.append("tint masks with visible colour: %s" % tint_bad[:20])

    # ---------------------------------------------------------- atlas references
    refs = []
    for fn in ("terrain_texture.json", "item_texture.json"):
        path = os.path.join(TEX, fn)
        try:
            data = relaxed_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s does not parse: %r" % (fn, exc))
            continue
        refs.extend(walk_refs(data))
    for fn in ("flipbook_textures.json", "texture_list.json"):
        path = os.path.join(TEX, fn)
        try:
            data = relaxed_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s does not parse: %r" % (fn, exc))
            continue
        if fn == "flipbook_textures.json":
            refs.extend(e.get("flipbook_texture", "") for e in data)
        else:
            refs.extend(data)
    unresolved = sorted({r for r in refs if r and resolve_ref(r) is None})
    if unresolved:
        errors.append("unresolved atlas references: %s" % unresolved[:30])

    # ---------------------------------------------------------- flipbook frames
    flip = relaxed_json(os.path.join(TEX, "flipbook_textures.json"))
    bad_flips = []
    for entry in flip:
        ref = entry.get("flipbook_texture", "")
        path = resolve_ref(ref)
        if not path:
            continue
        try:
            w, h = image_size(path)
        except Exception:
            continue
        if not w or h % w:
            bad_flips.append((ref, "not a vertical strip: %dx%d" % (w, h)))
            continue
        count = h // w
        frames = entry.get("frames")
        if frames:
            if max(frames) >= count:
                bad_flips.append((ref, "frame index %d >= %d" % (max(frames), count)))
        if "atlas_tile" not in entry:
            bad_flips.append((ref, "missing atlas_tile"))
    if bad_flips:
        errors.append("bad flipbook metadata: %s" % bad_flips[:20])

    # ---------------------------------------------------------- manifest/icon
    try:
        manifest = relaxed_json(MANIFEST)
    except Exception as exc:  # noqa: BLE001
        errors.append("manifest.json does not parse: %r" % exc)
        manifest = {}
    header = manifest.get("header", {})
    module = (manifest.get("modules") or [{}])[0]
    if header.get("uuid") == module.get("uuid"):
        errors.append("header and module UUID are identical")
    for label, value in (("header", header.get("uuid")), ("module", module.get("uuid"))):
        if not value or not UUID_RE.match(value):
            errors.append("invalid %s UUID: %r" % (label, value))
    if header.get("min_engine_version") != [1, 26, 50]:
        warnings.append("unexpected min_engine_version: %r" % (header.get("min_engine_version"),))
    if header.get("version") != [1, 0, 0]:
        warnings.append("unexpected pack version: %r" % (header.get("version"),))
    if module.get("type") != "resources":
        errors.append("manifest module is not a resources module")
    if not os.path.isfile(ICON):
        errors.append("pack_icon.png is missing")
    else:
        try:
            if image_size(ICON) != (256, 256):
                errors.append("pack_icon.png is not 256x256")
        except Exception as exc:  # noqa: BLE001
            errors.append("pack_icon.png does not decode: %r" % exc)

    # ---------------------------------------------------------- package
    pack_files = set()
    for root, _dirs, files in os.walk(PACK):
        for fn in files:
            if fn == ".DS_Store":
                continue
            pack_files.add(os.path.relpath(os.path.join(root, fn), PACK).replace(os.sep, "/"))
    if not os.path.isfile(MCPACK):
        errors.append("packaged .mcpack is missing")
    else:
        try:
            with zipfile.ZipFile(MCPACK) as z:
                if z.testzip() is not None:
                    errors.append("packaged .mcpack has a corrupt member")
                zipped = set(z.namelist())
            if zipped != pack_files:
                errors.append("zip/file tree mismatch: missing=%s extra=%s"
                              % (sorted(pack_files - zipped)[:10],
                                 sorted(zipped - pack_files)[:10]))
            if "manifest.json" not in zipped or "pack_icon.png" not in zipped:
                errors.append("packaged .mcpack lacks manifest.json or pack_icon.png")
            if any(name.startswith("resource_pack/") for name in zipped):
                errors.append("packaged .mcpack has a resource_pack/ prefix")
        except Exception as exc:  # noqa: BLE001
            errors.append("packaged .mcpack does not open: %r" % exc)

    # ---------------------------------------------------------- report
    summary = {
        "source_colour_bases": len(source_bases),
        "inventory_textures": len(entries),
        "generated_images": len(actual),
        "expected_images": len(expected),
        "compatibility_images": len(extras),
        "atlas_references": len(refs),
        "flipbooks": len(flip),
        "pack_files": len(pack_files),
        "mcpack_bytes": os.path.getsize(MCPACK) if os.path.isfile(MCPACK) else 0,
        "icon": "%dx%d" % image_size(ICON) if os.path.isfile(ICON) else None,
        "errors": errors,
        "warnings": warnings,
    }
    with open(os.path.join(ROOT, "build", "validation.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
