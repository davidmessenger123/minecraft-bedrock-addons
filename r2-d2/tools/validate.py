#!/usr/bin/env python3
"""Structural validator for the R2-D2 Droid add-on."""

from __future__ import annotations

import json
import os
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
PACKAGE = ROOT / "R2D2-1.2.0.mcaddon"

errors: list[str] = []
warnings: list[str] = []


def load(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:  # noqa: BLE001 - report every JSON failure
        errors.append(f"{path.relative_to(ROOT)}: {exc}")
        return None


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", header[16:24])
    except OSError:
        return None


bp_manifest = load(BP / "manifest.json")
rp_manifest = load(RP / "manifest.json")
entity = load(BP / "entities" / "r2d2_droid.json")
client = load(RP / "entity" / "r2d2.entity.json")
geometry = load(RP / "models" / "entity" / "r2d2.geo.json")
animations = load(RP / "animations" / "r2d2.animation.json")
controllers = load(RP / "animation_controllers" / "r2d2.animation_controllers.json")
sounds = load(RP / "sounds" / "sound_definitions.json")

if bp_manifest and rp_manifest:
    bp_header = bp_manifest.get("header", {})
    rp_header = rp_manifest.get("header", {})
    if bp_header.get("version") != [1, 2, 0]:
        errors.append("behavior pack header version is not 1.2.0")
    if rp_header.get("version") != [1, 2, 0]:
        errors.append("resource pack header version is not 1.2.0")
    bp_uuid = bp_header.get("uuid")
    rp_uuid = rp_header.get("uuid")
    dependencies = bp_manifest.get("dependencies", [])
    rp_dependency = next((dep for dep in dependencies if dep.get("uuid") == rp_uuid), None)
    if rp_dependency is None:
        errors.append("behavior pack does not depend on the resource pack UUID")
    elif rp_dependency.get("version") != rp_header.get("version"):
        errors.append("behavior pack resource pack dependency version does not match the resource pack header")
    if not any(dep.get("module_name") == "@minecraft/server" for dep in dependencies):
        errors.append("behavior pack does not depend on @minecraft/server")

if entity:
    description = entity.get("minecraft:entity", {}).get("description", {})
    if description.get("identifier") != "r2d2:droid":
        errors.append("entity identifier is not r2d2:droid")
    if description.get("is_spawnable") is not True:
        errors.append("entity is not spawnable")
    holo_property = description.get("properties", {}).get("r2d2:holo_active", {})
    if holo_property.get("type") != "bool":
        errors.append("entity property r2d2:holo_active is missing or not a bool")
    if holo_property.get("client_sync") is not True:
        errors.append("entity property r2d2:holo_active is not client-synced")
    components = entity.get("minecraft:entity", {}).get("components", {})
    interactions = components.get("minecraft:interact", {}).get("interactions", [])
    if not any(item.get("interact_text") == "action.interact.holo" for item in interactions):
        errors.append("entity is missing the holoprojector interact prompt")

if client:
    desc = client.get("minecraft:client_entity", {}).get("description", {})
    if desc.get("geometry", {}).get("default") != "geometry.r2d2":
        errors.append("client entity does not use geometry.r2d2")
    if desc.get("textures", {}).get("default") != "textures/entity/r2d2":
        errors.append("client entity does not use textures/entity/r2d2")
    anims = desc.get("animations", {})
    for key in ("idle", "move", "holo", "controller", "holo_controller"):
        if key not in anims:
            errors.append(f"client entity missing animation key {key!r}")
    particle_effects = desc.get("particle_effects", {})
    for key in ("holo_beam", "holo_orb", "holo_motes"):
        if key not in particle_effects:
            errors.append(f"client entity missing particle effect key {key!r}")

if geometry:
    geo = geometry.get("minecraft:geometry", [{}])[0]
    desc = geo.get("description", {})
    if desc.get("identifier") != "geometry.r2d2":
        errors.append("geometry identifier is not geometry.r2d2")
    if desc.get("texture_width") != 256 or desc.get("texture_height") != 256:
        errors.append("geometry texture size is not 256x256")
    bones = geo.get("bones", [])
    bone_names = {bone.get("name") for bone in bones}
    for required in ("root", "body", "dome", "left_leg", "right_leg", "center_foot"):
        if required not in bone_names:
            errors.append(f"geometry missing bone {required!r}")
    dome = next((bone for bone in bones if bone.get("name") == "dome"), {})
    locators = dome.get("locators", {})
    for required in ("holo_projector", "holo_display"):
        if required not in locators:
            errors.append(f"geometry missing holoprojector locator {required!r}")
    cube_count = 0
    for bone in bones:
        for cube in bone.get("cubes", []):
            cube_count += 1
            uv = cube.get("uv")
            if isinstance(uv, dict):
                for face, rect in uv.items():
                    if not isinstance(rect, dict):
                        continue
                    values = list(rect.get("uv", [])) + list(rect.get("uv_size", []))
                    if values and (min(values) < -256 or max(values) > 256):
                        errors.append(f"cube UV out of range in bone {bone.get('name')!r}")
    if cube_count < 90:
        warnings.append(f"only {cube_count} cubes in geometry")

if animations:
    anims = animations.get("animations", {})
    for key in ("animation.r2d2.idle", "animation.r2d2.move", "animation.r2d2.holo"):
        if key not in anims:
            errors.append(f"animation file missing {key}")
    holo_animation = anims.get("animation.r2d2.holo", {})
    if not holo_animation.get("particle_effects"):
        errors.append("animation.r2d2.holo has no particle keyframes")

if controllers:
    controllers_map = controllers.get("animation_controllers", {})
    for key in (
        "controller.animation.r2d2.general",
        "controller.animation.r2d2.holo",
    ):
        if key not in controllers_map:
            errors.append(f"animation controller {key} is missing")

if sounds:
    for event, entry in sounds.items():
        for sound_path in entry.get("sounds", []):
            candidates = [RP / f"{sound_path}.wav", RP / f"{sound_path}.ogg", RP / f"{sound_path}.fsb"]
            if not any(path.exists() for path in candidates):
                errors.append(f"sound file missing for {event}: {sound_path}")
    for event in ("mob.r2d2.holo_on", "mob.r2d2.holo_off"):
        if event not in sounds:
            errors.append(f"sound event {event} is missing")

for name, identifier in {
    "holo_beam": "r2d2:holo_beam",
    "holo_orb": "r2d2:holo_orb",
    "holo_motes": "r2d2:holo_motes",
}.items():
    particle = load(RP / "particles" / f"{name}.json")
    if particle:
        actual = particle.get("particle_effect", {}).get("description", {}).get("identifier")
        if actual != identifier:
            errors.append(f"particle {name} identifier is {actual!r}, expected {identifier!r}")

texture = RP / "textures" / "entity" / "r2d2.png"
size = png_size(texture)
if size != (256, 256):
    errors.append(f"entity texture is not 256x256: {size}")

if PACKAGE.exists():
    with zipfile.ZipFile(PACKAGE) as archive:
        names = set(archive.namelist())
        for required in (
            "behavior_pack/manifest.json",
            "resource_pack/manifest.json",
            "resource_pack/models/entity/r2d2.geo.json",
            "resource_pack/textures/entity/r2d2.png",
            "behavior_pack/scripts/r2d2_droid.js",
            "resource_pack/particles/holo_beam.json",
            "resource_pack/particles/holo_orb.json",
            "resource_pack/particles/holo_motes.json",
            "resource_pack/sounds/r2d2/holo_on.wav",
            "resource_pack/sounds/r2d2/holo_off.wav",
        ):
            if required not in names:
                errors.append(f"package missing {required}")
        if archive.testzip() is not None:
            errors.append("package zip is corrupt")
else:
    warnings.append(f"package not built yet: {PACKAGE.name}")

print(f"Checked {ROOT}")
print(f"Geometry cubes: {cube_count if geometry else 'n/a'}")
print(f"Errors: {len(errors)}")
for item in errors:
    print(f"  ERROR: {item}")
print(f"Warnings: {len(warnings)}")
for item in warnings:
    print(f"  WARN: {item}")
raise SystemExit(1 if errors else 0)
