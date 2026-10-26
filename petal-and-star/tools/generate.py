"""
Build the Petal & Star resource pack and .mcpack archive.

Run from the project root:
    python3 tools/generate.py
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from content import build_textures, pack_icon

ROOT = Path(__file__).resolve().parent.parent
RP = ROOT / "resource_pack"
VERSION = (ROOT / "tools" / "VERSION").read_text(encoding="utf-8").strip()
VERSION_PARTS = [int(part) for part in VERSION.split(".")]
OUT = ROOT / f"PetalAndStar-{VERSION}.mcpack"

HEADER_UUID = "4f7f2e2a-7a1b-4f2c-9d4e-2b6a9c8d1e01"
MODULE_UUID = "a1c3e5f7-2b4d-4c6e-8f90-1a2b3c4d5e02"


def manifest() -> dict:
    return {
        "format_version": 2,
        "header": {
            "name": "Petal & Star",
            "description": "A soft pastel storybook texture pack for little adventurers. Flowers, stars, and friendly animals.",
            "uuid": HEADER_UUID,
            "version": VERSION_PARTS,
            "min_engine_version": [1, 21, 0],
        },
        "modules": [
            {
                "description": "Soft pastel blocks, flowers, items, sky and friendly animal textures.",
                "type": "resources",
                "uuid": MODULE_UUID,
                "version": VERSION_PARTS,
            }
        ],
        "metadata": {
            "authors": ["Petal & Star"],
            "license": "MIT",
        },
    }


def write_textures() -> int:
    textures = build_textures()
    tex_root = RP / "textures"
    if tex_root.exists():
        shutil.rmtree(tex_root)
    count = 0
    for rel, img in sorted(textures.items()):
        dest = tex_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.suffix.lower() == ".tga":
            img.save(dest, format="TGA")
        else:
            img.save(dest, format="PNG", compress_level=9)
        count += 1
    return count


def write_manifest() -> None:
    RP.mkdir(parents=True, exist_ok=True)
    (RP / "manifest.json").write_text(
        json.dumps(manifest(), indent=2) + "\n", encoding="utf-8"
    )
    pack_icon().save(RP / "pack_icon.png", format="PNG", compress_level=9)


def build_archive() -> int:
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(RP.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(RP).as_posix())
    return OUT.stat().st_size


def main() -> int:
    count = write_textures()
    write_manifest()
    size = build_archive()
    print(f"built Petal & Star {VERSION}")
    print(f"  textures: {count}")
    print(f"  resource pack: {RP}")
    print(f"  pack: {OUT} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
