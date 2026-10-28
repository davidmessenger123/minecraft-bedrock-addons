"""
Cogworks content builders.

Everything in this addon is authored from this file: a compact industrial
texture atlas, block/item models, behaviour JSON, recipes and the Blockbench
sources used to review the models.

Models are intentionally chunky and readable at Minecraft scale: dark steel
casings, copper power parts, brass fittings and teal energy accents.
"""

from __future__ import annotations

import base64
import json
import math
import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

NS = "cw"
VERSION = "1.0.0"
PACK_NAME = "Cogworks"
TILE = 16
ATLAS = 128

# Palette for the shared 128x128 block atlas.
STEEL = 0
COPPER = 1
BRASS = 2
DARK = 3
ENERGY = 4
BELT = 5
WOOD = 6
WARNING = 7
RUBBER = 8
LIGHT = 9


def _shade(c, f):
    return tuple(max(0, min(255, round(v * f))) for v in c[:3]) + (255,)


def _tile_xy(index: int) -> tuple[int, int]:
    return (index % 8) * TILE, (index // 8) * TILE


def _noise(draw: ImageDraw.ImageDraw, x0, y0, color, seed, count=22):
    rng = random.Random(seed)
    for _ in range(count):
        x = x0 + rng.randrange(TILE)
        y = y0 + rng.randrange(TILE)
        draw.point((x, y), fill=_shade(color, rng.uniform(0.82, 1.12)))


def _rivet(draw: ImageDraw.ImageDraw, x, y, base):
    draw.point((x, y), fill=_shade(base, 1.35))
    draw.point((x + 1, y), fill=_shade(base, 0.68))


def _make_tile(draw: ImageDraw.ImageDraw, index: int, base, kind: str, seed: int):
    x0, y0 = _tile_xy(index)
    draw.rectangle((x0, y0, x0 + TILE - 1, y0 + TILE - 1), fill=base)
    _noise(draw, x0, y0, base, seed)
    if kind == "steel":
        draw.line((x0, y0 + 1, x0 + 15, y0 + 1), fill=_shade(base, 1.22))
        draw.line((x0, y0 + 14, x0 + 15, y0 + 14), fill=_shade(base, 0.60))
        for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
            _rivet(draw, x0 + x, y0 + y, base)
        for x in (4, 8, 12):
            draw.point((x0 + x, y0 + 6), fill=_shade(base, 1.16))
    elif kind == "copper":
        draw.line((x0, y0 + 2, x0 + 15, y0 + 2), fill=_shade(base, 1.35))
        draw.line((x0, y0 + 13, x0 + 15, y0 + 13), fill=_shade(base, 0.58))
        for y in (5, 10):
            draw.line((x0, y0 + y, x0 + 15, y0 + y), fill=_shade(base, 0.72))
    elif kind == "brass":
        for i in range(3):
            draw.rectangle((x0 + 2 + i * 4, y0 + 3, x0 + 4 + i * 4, y0 + 12),
                           outline=_shade(base, 1.25), fill=_shade(base, 0.82))
    elif kind == "dark":
        draw.rectangle((x0 + 2, y0 + 2, x0 + 13, y0 + 13), outline=_shade(base, 0.65))
        draw.line((x0 + 2, y0 + 2, x0 + 13, y0 + 13), fill=_shade(base, 0.68))
    elif kind == "energy":
        draw.rectangle((x0 + 2, y0 + 2, x0 + 13, y0 + 13), fill=_shade(base, 0.35))
        for x, y in ((5, 4), (9, 4), (5, 10), (9, 10)):
            draw.rectangle((x0 + x, y0 + y, x0 + x + 1, y0 + y + 1), fill=(93, 242, 212, 255))
        draw.point((x0 + 8, y0 + 7), fill=(210, 255, 247, 255))
    elif kind == "belt":
        draw.rectangle((x0 + 1, y0 + 4, x0 + 14, y0 + 11), fill=_shade(base, 0.6))
        for x in range(2, 15, 4):
            draw.line((x0 + x, y0 + 5, x0 + x + 2, y0 + 8), fill=(226, 174, 78, 255))
            draw.line((x0 + x + 2, y0 + 8, x0 + x, y0 + 11), fill=(226, 174, 78, 255))
    elif kind == "wood":
        for y in range(3, 14, 4):
            draw.line((x0, y0 + y, x0 + 15, y0 + y), fill=_shade(base, 0.62))
        draw.line((x0 + 5, y0, x0 + 5, y0 + 15), fill=_shade(base, 1.16))
    elif kind == "warning":
        for i in range(-16, 16, 6):
            draw.line((x0 + i, y0 + 15, x0 + i + 15, y0), fill=_shade(base, 1.3), width=3)
    elif kind == "rubber":
        for y in range(2, 14, 3):
            draw.line((x0 + 1, y0 + y, x0 + 14, y0 + y), fill=_shade(base, 0.7))
    elif kind == "light":
        draw.rectangle((x0 + 3, y0 + 3, x0 + 12, y0 + 12), fill=(214, 255, 246, 255))
        draw.rectangle((x0 + 5, y0 + 5, x0 + 10, y0 + 10), fill=(94, 242, 211, 255))


def block_atlas() -> Image.Image:
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tiles = [
        ((57, 66, 76, 255), "steel", 10),
        ((170, 91, 48, 255), "copper", 20),
        ((214, 164, 75, 255), "brass", 30),
        ((30, 36, 43, 255), "dark", 40),
        ((20, 61, 67, 255), "energy", 50),
        ((44, 48, 57, 255), "belt", 60),
        ((105, 72, 43, 255), "wood", 70),
        ((176, 65, 54, 255), "warning", 80),
        ((24, 25, 28, 255), "rubber", 90),
        ((144, 235, 217, 255), "light", 100),
    ]
    for index, (color, kind, seed) in enumerate(tiles):
        _make_tile(d, index, color, kind, seed)
    return img


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

FACES = ("north", "south", "east", "west", "up", "down")


def uv_tile(tile: int) -> dict[str, dict[str, list[int]]]:
    x, y = _tile_xy(tile)
    return {face: {"uv": [x, y], "uv_size": [TILE, TILE]} for face in FACES}


def cube(lo, size, tile: int, faces: dict[str, int] | None = None) -> dict:
    face_uv = uv_tile(tile)
    for face, tile_index in (faces or {}).items():
        face_uv[face] = uv_tile(tile_index)[face]
    return {
        "origin": [round(float(v), 4) for v in lo],
        "size": [round(float(v), 4) for v in size],
        "uv": face_uv,
    }


def block_geo(identifier: str, cubes: list[dict], bounds=(1.0, 1.0, (0, 0.5, 0))) -> dict:
    return {
        "format_version": "1.21.90",
        "minecraft:geometry": [{
            "description": {
                "identifier": identifier,
                "texture_width": ATLAS,
                "texture_height": ATLAS,
                "visible_bounds_width": bounds[0],
                "visible_bounds_height": bounds[1],
                "visible_bounds_offset": list(bounds[2]),
            },
            "bones": [{"name": "body", "pivot": [0, 0, 0], "cubes": cubes}],
        }],
    }


def generator_geo() -> dict:
    return block_geo("geometry.cw.generator", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 7, 12], STEEL),
        cube([-4, 3, -8], [8, 3, 1], ENERGY),
        cube([-3, 6, -8], [6, 1, 1], DARK),
        cube([-2, 9, -2], [4, 3, 4], COPPER),
        cube([-4, 12, -4], [8, 1, 8], BRASS),
        cube([-7, 5, -7], [1, 5, 14], DARK),
        cube([6, 5, -7], [1, 5, 14], DARK),
        cube([-2, 13, -2], [4, 2, 4], COPPER),
    ], (1.2, 1.2, (0, 0.8, 0)))


def cable_geo() -> dict:
    return block_geo("geometry.cw.cable", [
        cube([-2, 0, -2], [4, 16, 4], COPPER),
        cube([-8, 5, -2], [16, 4, 4], COPPER, {"up": BRASS, "down": BRASS}),
        cube([-2, 5, -8], [4, 4, 16], COPPER, {"up": BRASS, "down": BRASS}),
        cube([-3, 0, -3], [6, 2, 6], DARK),
        cube([-3, 14, -3], [6, 2, 6], DARK),
    ], (1.0, 1.0, (0, 0.5, 0)))


def battery_geo() -> dict:
    return block_geo("geometry.cw.battery", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 8, 12], DARK),
        cube([-5, 3, -7], [3, 6, 1], WARNING),
        cube([-1, 3, -7], [3, 6, 1], ENERGY),
        cube([3, 3, -7], [3, 6, 1], LIGHT),
        cube([-4, 10, -4], [8, 1, 8], BRASS),
        cube([-3, 11, -2], [2, 2, 2], COPPER),
        cube([2, 11, 0], [2, 2, 2], COPPER),
        cube([-7, 10, -7], [14, 1, 1], STEEL),
    ], (1.0, 1.0, (0, 0.5, 0)))


def conveyor_cubes() -> list[dict]:
    return [
        cube([-8, 0, -7], [1, 9, 14], STEEL),
        cube([7, 0, -7], [1, 9, 14], STEEL),
        cube([-7, 8, -7], [14, 1, 14], BELT),
        cube([-7, 7, -7], [14, 1, 1], DARK),
        cube([-7, 7, 6], [14, 1, 1], DARK),
        cube([-7, 8, -7], [1, 1, 14], BRASS),
        cube([6, 8, -7], [1, 1, 14], BRASS),
        cube([-6, 1, -6], [2, 6, 2], COPPER),
        cube([4, 1, -6], [2, 6, 2], COPPER),
        cube([-6, 1, 4], [2, 6, 2], COPPER),
        cube([4, 1, 4], [2, 6, 2], COPPER),
    ]


def conveyor_frame_cubes() -> list[dict]:
    return [
        cube([-8, 0, -7], [1, 9, 14], STEEL),
        cube([7, 0, -7], [1, 9, 14], STEEL),
        cube([-7, 7, -7], [14, 1, 1], DARK),
        cube([-7, 7, 6], [14, 1, 1], DARK),
        cube([-7, 8, -7], [1, 1, 14], BRASS),
        cube([6, 8, -7], [1, 1, 14], BRASS),
        cube([-6, 1, -6], [2, 6, 2], COPPER),
        cube([4, 1, -6], [2, 6, 2], COPPER),
        cube([-6, 1, 4], [2, 6, 2], COPPER),
        cube([4, 1, 4], [2, 6, 2], COPPER),
    ]


def conveyor_curve_geo() -> dict:
    """One belt block with straight/left/right geometry selected by state."""
    straight = conveyor_cubes()
    left = conveyor_frame_cubes() + [
        cube([-7, 8, 0], [8, 1, 8], BELT),
        cube([-7, 8, -7], [8, 1, 8], BELT),
        cube([0, 8, -7], [8, 1, 7], BELT),
        cube([-7, 8, 6], [8, 1, 1], BRASS),
        cube([6, 8, -7], [1, 1, 8], BRASS),
    ]
    right = conveyor_frame_cubes() + [
        cube([-1, 8, 0], [8, 1, 8], BELT),
        cube([-1, 8, -7], [8, 1, 8], BELT),
        cube([-8, 8, -7], [8, 1, 7], BELT),
        cube([-8, 8, 6], [8, 1, 1], BRASS),
        cube([-7, 8, -7], [1, 1, 8], BRASS),
    ]
    return {
        "format_version": "1.21.90",
        "minecraft:geometry": [{
            "description": {
                "identifier": "geometry.cw.conveyor",
                "texture_width": ATLAS,
                "texture_height": ATLAS,
                "visible_bounds_width": 1.0,
                "visible_bounds_height": 0.7,
                "visible_bounds_offset": [0, 0.35, 0],
            },
            "bones": [
                {"name": "straight", "pivot": [0, 0, 0], "cubes": straight},
                {"name": "left", "pivot": [0, 0, 0], "cubes": left},
                {"name": "right", "pivot": [0, 0, 0], "cubes": right},
            ],
        }],
    }



def conveyor_geo() -> dict:
    return block_geo("geometry.cw.conveyor", conveyor_cubes(),
                     (1.0, 0.7, (0, 0.35, 0)))


def logistics_geo(kind: str) -> dict:
    """Small, distinct control heads on the same conveyor base."""
    cubes = conveyor_cubes()
    if kind == "filter":
        cubes += [
            cube([-3, 9, -8], [6, 3, 1], ENERGY),
            cube([-2, 10, -7], [4, 1, 3], COPPER),
            cube([-1, 11, -6], [2, 1, 2], LIGHT),
        ]
    elif kind == "splitter":
        cubes += [
            cube([-8, 3, -2], [2, 4, 4], COPPER),
            cube([6, 3, -2], [2, 4, 4], COPPER),
            cube([-2, 9, -2], [4, 1, 4], BRASS),
            cube([-1, 10, -1], [2, 1, 2], LIGHT),
        ]
    elif kind == "merger":
        cubes += [
            cube([-4, 3, 7], [8, 3, 1], COPPER),
            cube([-8, 3, -1], [1, 3, 3], COPPER),
            cube([7, 3, -1], [1, 3, 3], COPPER),
            cube([-2, 9, -2], [4, 1, 4], BRASS),
            cube([-1, 10, -1], [2, 1, 2], ENERGY),
        ]
    else:  # extractor
        cubes += [
            cube([-4, 3, 7], [8, 4, 1], STEEL),
            cube([-2, 7, 6], [4, 3, 2], COPPER),
            cube([-4, 10, 6], [8, 1, 3], BRASS),
            cube([-2, 11, 7], [4, 1, 1], ENERGY),
        ]
    return block_geo(f"geometry.cw.{kind}", cubes, (1.0, 0.8, (0, 0.4, 0)))



def assembler_geo() -> dict:
    return block_geo("geometry.cw.assembler", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 7, 12], DARK),
        cube([-4, 3, -8], [8, 4, 1], ENERGY),
        cube([-5, 9, -5], [10, 1, 10], STEEL),
        cube([-3, 10, -3], [6, 2, 6], BRASS),
        cube([-2, 12, -3], [4, 2, 4], COPPER),
        cube([-7, 5, -7], [1, 3, 14], STEEL),
        cube([6, 5, -7], [1, 3, 14], STEEL),
        cube([-2, 10, -2], [4, 1, 4], ENERGY),
    ], (1.1, 1.1, (0, 0.65, 0)))


def storage_geo(extension: bool = False) -> dict:
    id_ = "geometry.cw.storage_extension" if extension else "geometry.cw.storage_core"
    trim = COPPER if extension else BRASS
    return block_geo(id_, [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 9, 12], WOOD),
        cube([-5, 3, -7], [10, 6, 1], DARK if not extension else COPPER),
        cube([-2, 4, -8], [4, 2, 1], trim),
        cube([-4, 10, -4], [8, 1, 8], STEEL),
        cube([-3, 11, -2], [2, 2, 2], trim),
        cube([2, 11, 0], [2, 2, 2], trim),
        cube([-7, 5, -7], [1, 3, 14], STEEL),
        cube([6, 5, -7], [1, 3, 14], STEEL),
    ], (1.0, 1.0, (0, 0.5, 0)))


def quarry_geo() -> dict:
    return block_geo("geometry.cw.quarry", [
        cube([-7, 0, -7], [14, 3, 14], STEEL),
        cube([-6, 3, -6], [12, 5, 12], DARK),
        cube([-2, 8, -2], [4, 14, 4], COPPER),
        cube([-3, 22, -3], [6, 3, 6], BRASS),
        cube([-1, 25, -1], [2, 2, 2], DARK),
        cube([-7, 4, -7], [1, 8, 1], STEEL),
        cube([6, 4, -7], [1, 8, 1], STEEL),
        cube([-7, 4, 6], [1, 8, 1], STEEL),
        cube([6, 4, 6], [1, 8, 1], STEEL),
        cube([-4, 3, -8], [8, 3, 1], ENERGY),
        cube([-1, 18, -1], [2, 4, 2], WARNING),
    ], (1.2, 1.8, (0, 0.9, 0)))


def storage_terminal_geo() -> dict:
    return block_geo("geometry.cw.storage_terminal", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 7, 12], DARK),
        cube([-5, 3, -7], [10, 4, 1], ENERGY),
        cube([-4, 9, -4], [8, 1, 8], STEEL),
        cube([-5, 10, -5], [10, 1, 10], BRASS),
        cube([-6, 11, -6], [12, 2, 12], COPPER),
        cube([-6, 5, -8], [12, 1, 1], BRASS),
    ], (1.1, 1.1, (0, 0.65, 0)))


def storage_port_geo() -> dict:
    return block_geo("geometry.cw.storage_port", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 6, 12], DARK),
        cube([-4, 8, -4], [8, 3, 8], COPPER),
        cube([-5, 11, -5], [10, 1, 10], BRASS),
        cube([-3, 4, -8], [6, 3, 1], ENERGY),
        cube([-7, 5, -7], [1, 4, 14], STEEL),
        cube([6, 5, -7], [1, 4, 14], STEEL),
    ], (1.1, 1.2, (0, 0.6, 0)))


def electric_furnace_geo() -> dict:
    return block_geo("geometry.cw.electric_furnace", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 8, 12], DARK),
        cube([-4, 3, -8], [8, 4, 1], WARNING),
        cube([-3, 4, -8.2], [6, 2, 1], LIGHT),
        cube([-5, 10, -5], [10, 2, 10], STEEL),
        cube([-2, 12, -2], [4, 3, 4], COPPER),
        cube([-4, 15, -3], [8, 1, 6], BRASS),
        cube([-7, 5, -7], [1, 4, 14], STEEL),
        cube([6, 5, -7], [1, 4, 14], STEEL),
    ], (1.1, 1.4, (0, 0.7, 0)))


def crusher_geo() -> dict:
    return block_geo("geometry.cw.crusher", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 8, 12], DARK),
        cube([-5, 10, -5], [10, 2, 10], STEEL),
        cube([-4, 12, -4], [3, 4, 8], COPPER),
        cube([1, 12, -4], [3, 4, 8], COPPER),
        cube([-2, 12, -5], [4, 2, 10], BRASS),
        cube([-7, 4, -7], [1, 5, 14], STEEL),
        cube([6, 4, -7], [1, 5, 14], STEEL),
        cube([-3, 3, -8], [6, 3, 1], ENERGY),
    ], (1.2, 1.4, (0, 0.7, 0)))


def sawmill_geo() -> dict:
    return block_geo("geometry.cw.sawmill", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 6, 12], DARK),
        cube([-5, 8, -5], [10, 2, 10], STEEL),
        cube([-1, 10, -5], [2, 5, 10], LIGHT),
        cube([-3, 10, -6], [6, 1, 1], BRASS),
        cube([-3, 14, -6], [6, 1, 1], BRASS),
        cube([-7, 4, -7], [1, 4, 14], STEEL),
        cube([6, 4, -7], [1, 4, 14], STEEL),
        cube([-4, 3, -8], [8, 3, 1], ENERGY),
    ], (1.2, 1.4, (0, 0.7, 0)))


def alloy_smelter_geo() -> dict:
    return block_geo("geometry.cw.alloy_smelter", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 7, 12], DARK),
        cube([-5, 9, -5], [10, 2, 10], COPPER),
        cube([-3, 11, -3], [6, 3, 6], STEEL),
        cube([-2, 14, -2], [4, 1, 4], BRASS),
        cube([-4, 4, -8], [8, 4, 1], WARNING),
        cube([-2, 5, -8.2], [4, 2, 1], LIGHT),
        cube([-7, 5, -7], [1, 5, 14], STEEL),
        cube([6, 5, -7], [1, 5, 14], STEEL),
    ], (1.2, 1.5, (0, 0.75, 0)))


def wind_turbine_geo() -> dict:
    return block_geo("geometry.cw.wind_turbine", [
        cube([-7, 0, -7], [14, 3, 14], STEEL),
        cube([-2, 3, -2], [4, 14, 4], COPPER),
        cube([-3, 17, -3], [6, 3, 6], STEEL),
        cube([-1, 20, -1], [2, 2, 2], BRASS),
        cube([-8, 19, -1], [7, 1, 2], BRASS),
        cube([1, 19, -1], [7, 1, 2], BRASS),
        cube([-1, 21, -8], [2, 1, 7], COPPER),
        cube([-1, 21, 1], [2, 1, 7], COPPER),
        cube([-1, 22, -1], [2, 4, 2], BRASS),
    ], (1.2, 1.8, (0, 0.9, 0)))


def energy_meter_geo() -> dict:
    return block_geo("geometry.cw.energy_meter", [
        cube([-7, 0, -7], [14, 2, 14], STEEL),
        cube([-6, 2, -6], [12, 7, 12], DARK),
        cube([-5, 3, -7], [10, 4, 1], ENERGY),
        cube([-4, 9, -4], [8, 1, 8], STEEL),
        cube([-3, 10, -3], [6, 2, 6], BRASS),
        cube([-2, 12, -2], [4, 1, 4], LIGHT),
    ], (1.0, 1.1, (0, 0.55, 0)))


def block_geometries() -> dict[str, dict]:
    return {
        "generator": generator_geo(),
        "cable": cable_geo(),
        "battery": battery_geo(),
        "conveyor": conveyor_curve_geo(),
        "filter": logistics_geo("filter"),
        "splitter": logistics_geo("splitter"),
        "merger": logistics_geo("merger"),
        "extractor": logistics_geo("extractor"),
        "assembler": assembler_geo(),
        "storage_core": storage_geo(False),
        "storage_extension": storage_geo(True),
        "storage_terminal": storage_terminal_geo(),
        "storage_port": storage_port_geo(),
        "electric_furnace": electric_furnace_geo(),
        "crusher": crusher_geo(),
        "sawmill": sawmill_geo(),
        "alloy_smelter": alloy_smelter_geo(),
        "wind_turbine": wind_turbine_geo(),
        "energy_meter": energy_meter_geo(),
        "quarry": quarry_geo(),
    }


# ---------------------------------------------------------------------------
# Held-tool attachable models
# ---------------------------------------------------------------------------

def tool_geo(identifier: str, cubes: list[dict], bounds=(2.0, 2.0, (0, 0, 0))) -> dict:
    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": identifier,
                "texture_width": ATLAS,
                "texture_height": ATLAS,
                "visible_bounds_width": bounds[0],
                "visible_bounds_height": bounds[1],
                "visible_bounds_offset": list(bounds[2]),
            },
            "bones": [{
                "name": "tool",
                "binding": "q.item_slot_to_bone_name(context.item_slot)",
                "pivot": [0, 0, 0],
                "cubes": cubes,
            }],
        }],
    }


def drill_geo() -> dict:
    return tool_geo("geometry.cw.drill", [
        cube([-2.5, 0, -4], [5, 5, 8], STEEL),
        cube([-2, 5, -2], [4, 2, 5], COPPER),
        cube([-1.5, -5, -1], [3, 5, 3], DARK),
        cube([-1, 1, 4], [2, 2, 5], COPPER),
        cube([-0.5, 1.5, 9], [1, 1, 2], LIGHT),
        cube([-2.5, 1, -5], [5, 2, 1], ENERGY),
        cube([-1.5, -6, -1], [3, 1, 3], BRASS),
    ], (2.0, 2.0, (0, 0, 0)))


def chainsaw_geo() -> dict:
    teeth = [
        cube([-1.25, 0.5, z], [0.5, 1, 1], LIGHT)
        for z in (3.0, 5.0, 7.0, 9.0)
    ] + [
        cube([0.75, 0.5, z], [0.5, 1, 1], LIGHT)
        for z in (3.0, 5.0, 7.0, 9.0)
    ]
    return tool_geo("geometry.cw.chainsaw", [
        cube([-2.5, 0, -3], [5, 5, 6], STEEL),
        cube([-1, 0.5, 3], [2, 2, 10], DARK),
        *teeth,
        cube([-1, -4, -2], [2, 4, 3], WOOD),
        cube([-2, 5, -2], [4, 1, 4], COPPER),
        cube([-2.5, 1, -4], [5, 2, 1], ENERGY),
        cube([-2.5, 1, 2], [5, 1, 1], BRASS),
    ], (2.2, 2.0, (0, 0, 0)))


def wrench_geo() -> dict:
    return tool_geo("geometry.cw.wrench", [
        cube([-1, -9, -1], [2, 12, 2], STEEL),
        cube([-1, -1, -1], [2, 3, 2], COPPER),
        cube([-3, 2, -1], [6, 2, 2], BRASS),
        cube([-3, 4, -1], [2, 2, 2], BRASS),
        cube([1, 4, -1], [2, 2, 2], BRASS),
        cube([-3, 3, -1], [1, 1, 2], ENERGY),
        cube([-1.5, -10, -1.5], [3, 1, 3], DARK),
    ], (1.8, 2.0, (0, 0, 0)))


def surveyor_geo() -> dict:
    return tool_geo("geometry.cw.surveyor", [
        cube([-1, -10, -1], [2, 18, 2], WOOD),
        cube([-1, 8, -1], [2, 4, 2], COPPER),
        cube([-3, 10, -1], [6, 3, 2], STEEL),
        cube([-2, 11, -1], [2, 2, 1], ENERGY),
        cube([-1, 13, -1], [2, 1, 2], BRASS),
        cube([-1.5, -11, -1.5], [3, 1, 3], DARK),
    ], (1.8, 2.0, (0, 0, 0)))


def gear_geo() -> dict:
    teeth = []
    for x, z in ((-3, -1), (2, -1), (-1, -3), (-1, 2)):
        teeth.append(cube([x, -1, z], [2, 2, 2], BRASS))
    return tool_geo("geometry.cw.gear", [
        cube([-3, -3, -1], [6, 6, 2], STEEL),
        cube([-2, -2, 1], [4, 4, 1], BRASS),
        cube([-1, -1, 1.8], [2, 2, 1], ENERGY),
        *teeth,
    ], (1.6, 1.6, (0, 0, 0)))


def circuit_geo() -> dict:
    return tool_geo("geometry.cw.circuit", [
        cube([-4, -3, -1], [8, 6, 1], DARK),
        cube([-3, -2, 0], [3, 2, 1], ENERGY),
        cube([1, -2, 0], [2, 2, 1], BRASS),
        cube([-2, 1, 0], [3, 1, 1], COPPER),
        cube([2, 1, 0], [1, 1, 1], WARNING),
    ], (1.6, 1.4, (0, 0, 0)))


def motor_geo() -> dict:
    return tool_geo("geometry.cw.motor", [
        cube([-3, -3, -3], [6, 6, 6], STEEL),
        cube([-2, -2, -4], [4, 4, 1], COPPER),
        cube([-2, -2, 3], [4, 4, 2], BRASS),
        cube([-1, -1, 5], [2, 2, 1], DARK),
        cube([-4, -1, -1], [1, 2, 2], BRASS),
    ], (1.6, 1.6, (0, 0, 0)))


def tool_geometries() -> dict[str, dict]:
    return {
        "drill": drill_geo(),
        "chainsaw": chainsaw_geo(),
        "wrench": wrench_geo(),
        "surveyor": surveyor_geo(),
        "gear": gear_geo(),
        "circuit": circuit_geo(),
        "motor": motor_geo(),
    }


# ---------------------------------------------------------------------------
# Item icons
# ---------------------------------------------------------------------------

def _icon_base() -> Image.Image:
    return Image.new("RGBA", (32, 32), (0, 0, 0, 0))


def gear_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 25, 25), fill=(166, 168, 174, 255), outline=(49, 53, 60, 255), width=2)
    d.ellipse((12, 12, 19, 19), fill=(49, 53, 60, 255))
    for a in range(0, 360, 45):
        x = round(16 + math.cos(math.radians(a)) * 12)
        y = round(16 + math.sin(math.radians(a)) * 12)
        d.rectangle((x - 2, y - 2, x + 2, y + 2), fill=(198, 200, 205, 255), outline=(49, 53, 60, 255))
    return img


def circuit_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.rounded_rectangle((5, 6, 26, 25), radius=3, fill=(30, 65, 58, 255), outline=(91, 65, 36, 255), width=2)
    for x in (9, 15, 21):
        d.rectangle((x, 9, x + 2, 11), fill=(232, 174, 71, 255))
        d.rectangle((x, 17, x + 2, 19), fill=(95, 241, 211, 255))
    d.line((8, 14, 23, 14), fill=(232, 174, 71, 255), width=1)
    return img


def motor_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.rounded_rectangle((5, 7, 26, 24), radius=3, fill=(58, 66, 76, 255), outline=(25, 30, 36, 255), width=2)
    d.ellipse((10, 11, 21, 22), fill=(170, 96, 49, 255), outline=(35, 26, 20, 255), width=2)
    d.ellipse((14, 15, 17, 18), fill=(230, 181, 91, 255))
    d.rectangle((25, 12, 30, 20), fill=(214, 164, 75, 255))
    return img


def drill_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.rectangle((10, 4, 22, 10), fill=(78, 88, 100, 255), outline=(24, 29, 35, 255), width=2)
    d.rectangle((14, 10, 18, 23), fill=(170, 96, 49, 255), outline=(40, 28, 20, 255))
    d.polygon([(14, 23), (18, 23), (16, 30)], fill=(194, 198, 202, 255), outline=(65, 69, 75, 255))
    d.rectangle((5, 6, 10, 9), fill=(214, 164, 75, 255))
    d.rectangle((22, 6, 27, 9), fill=(214, 164, 75, 255))
    return img


def chainsaw_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.rectangle((4, 14, 19, 20), fill=(214, 164, 75, 255), outline=(58, 40, 23, 255), width=2)
    d.rectangle((19, 13, 29, 20), fill=(72, 82, 94, 255), outline=(24, 29, 35, 255), width=2)
    for x in range(20, 30, 3):
        d.point((x, 16), fill=(226, 238, 240, 255))
    d.rectangle((11, 10, 17, 14), fill=(170, 96, 49, 255))
    d.rectangle((2, 15, 5, 18), fill=(88, 96, 106, 255))
    return img


def wrench_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.line((7, 24, 21, 8), fill=(165, 167, 172, 255), width=5)
    d.ellipse((3, 3, 13, 13), outline=(165, 167, 172, 255), width=4)
    d.pieslice((3, 3, 13, 13), 200, 340, fill=(0, 0, 0, 0))
    d.rectangle((23, 4, 28, 9), fill=(170, 96, 49, 255))
    return img


def surveyor_icon() -> Image.Image:
    img = _icon_base(); d = ImageDraw.Draw(img)
    d.line((7, 26, 22, 7), fill=(170, 96, 49, 255), width=3)
    d.line((10, 22, 25, 3), fill=(214, 164, 75, 255), width=1)
    d.rectangle((4, 22, 10, 28), fill=(78, 88, 100, 255))
    d.ellipse((20, 2, 27, 9), fill=(95, 241, 211, 255), outline=(24, 30, 35, 255), width=1)
    return img


def component_icon(kind: str) -> Image.Image:
    if kind == "gear":
        return gear_icon()
    if kind == "circuit":
        return circuit_icon()
    if kind == "motor":
        return motor_icon()
    if kind == "drill":
        return drill_icon()
    if kind == "chainsaw":
        return chainsaw_icon()
    if kind == "wrench":
        return wrench_icon()
    return surveyor_icon()


def item_icons() -> dict[str, Image.Image]:
    return {
        "gear": gear_icon(),
        "circuit": circuit_icon(),
        "motor": motor_icon(),
        "drill": drill_icon(),
        "chainsaw": chainsaw_icon(),
        "wrench": wrench_icon(),
        "surveyor": surveyor_icon(),
    }


def pack_icon() -> Image.Image:
    img = Image.new("RGBA", (256, 256), (18, 22, 28, 255))
    d = ImageDraw.Draw(img)
    for y in range(256):
        d.line((0, y, 255, y), fill=(18 + y // 12, 22 + y // 16, 28 + y // 10, 255))
    # central gear
    d.ellipse((46, 46, 210, 210), fill=(58, 66, 76, 255), outline=(214, 164, 75, 255), width=12)
    d.ellipse((90, 90, 166, 166), fill=(18, 22, 28, 255), outline=(170, 96, 49, 255), width=8)
    for a in range(0, 360, 45):
        x = round(128 + math.cos(math.radians(a)) * 96)
        y = round(128 + math.sin(math.radians(a)) * 96)
        d.rounded_rectangle((x - 24, y - 24, x + 24, y + 24), radius=8,
                            fill=(170, 96, 49, 255), outline=(230, 181, 91, 255), width=4)
    d.rectangle((110, 110, 146, 146), fill=(95, 241, 211, 255))
    return img


# ---------------------------------------------------------------------------
# Block and item definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BlockSpec:
    key: str
    label: str
    geometry: str
    hardness: float
    light: int = 0
    collision: bool | dict = True
    selection: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None
    menu: str | None = "construction"
    sound: str = "stone"
    machine: bool = False
    state: bool = False
    dynamic: bool = True
    fuel: bool = False
    tick_range: tuple[int, int] = (10, 20)
    status_state: bool = False
    curve_state: bool = False


BLOCKS: list[BlockSpec] = [
    BlockSpec("generator", "Coal Generator", "geometry.cw.generator", 3.0, light=8, machine=True, fuel=True, sound="metal", status_state=True),
    BlockSpec("cable", "Copper Cable", "geometry.cw.cable", 1.0, collision={"origin": [-5, 0, -5], "size": [10, 8, 10]}, sound="metal"),
    BlockSpec("battery", "Battery Bank", "geometry.cw.battery", 2.5, light=4, collision={"origin": [-8, 0, -8], "size": [16, 12, 16]}, sound="metal"),
    BlockSpec("conveyor", "Conveyor Belt", "geometry.cw.conveyor", 2.0, collision={"origin": [-8, 0, -8], "size": [16, 8, 16]}, machine=True, state=True, sound="metal", tick_range=(4, 8), curve_state=True),
    BlockSpec("filter", "Item Filter", "geometry.cw.filter", 2.0, collision={"origin": [-8, 0, -8], "size": [16, 8, 16]}, machine=True, state=True, sound="metal", tick_range=(4, 8)),
    BlockSpec("splitter", "Belt Splitter", "geometry.cw.splitter", 2.0, collision={"origin": [-8, 0, -8], "size": [16, 8, 16]}, machine=True, state=True, sound="metal", tick_range=(4, 8)),
    BlockSpec("merger", "Belt Merger", "geometry.cw.merger", 2.0, collision={"origin": [-8, 0, -8], "size": [16, 8, 16]}, machine=True, state=True, sound="metal", tick_range=(4, 8)),
    BlockSpec("extractor", "Storage Extractor", "geometry.cw.extractor", 2.0, collision={"origin": [-8, 0, -8], "size": [16, 8, 16]}, machine=True, state=True, sound="metal", tick_range=(4, 8)),
    BlockSpec("assembler", "Crafting Assembler", "geometry.cw.assembler", 3.0, light=3, machine=True, sound="metal", status_state=True),
    BlockSpec("storage_core", "Storage Core", "geometry.cw.storage_core", 2.0, sound="wood"),
    BlockSpec("storage_extension", "Storage Extension", "geometry.cw.storage_extension", 2.0, sound="wood"),
    BlockSpec("storage_terminal", "Storage Terminal", "geometry.cw.storage_terminal", 2.5, light=4, machine=True, sound="metal", tick_range=(20, 20)),
    BlockSpec("storage_port", "Storage Port", "geometry.cw.storage_port", 2.5, light=3, machine=True, sound="metal", tick_range=(8, 12)),
    BlockSpec("electric_furnace", "Electric Furnace", "geometry.cw.electric_furnace", 3.0, light=4, machine=True, sound="metal", status_state=True),
    BlockSpec("crusher", "Crusher", "geometry.cw.crusher", 3.0, light=3, machine=True, sound="metal", status_state=True),
    BlockSpec("sawmill", "Sawmill", "geometry.cw.sawmill", 3.0, light=3, machine=True, sound="metal", status_state=True),
    BlockSpec("alloy_smelter", "Alloy Smelter", "geometry.cw.alloy_smelter", 3.5, light=5, machine=True, sound="metal", status_state=True),
    BlockSpec("wind_turbine", "Wind Turbine", "geometry.cw.wind_turbine", 3.0, light=0, machine=True, sound="metal", tick_range=(20, 20)),
    BlockSpec("energy_meter", "Energy Meter", "geometry.cw.energy_meter", 2.0, light=2, sound="metal", dynamic=False),
    BlockSpec("quarry", "Quarry Controller", "geometry.cw.quarry", 4.0, light=5, machine=True, sound="metal", tick_range=(1, 1), status_state=True),
]

ITEMS = {
    "gear": ("Cogwork Gear", "items"),
    "circuit": ("Control Circuit", "items"),
    "motor": ("Electric Motor", "items"),
    "drill": ("Powered Drill", "equipment"),
    "chainsaw": ("Powered Chainsaw", "equipment"),
    "wrench": ("Cogworks Wrench", "equipment"),
    "surveyor": ("Quarry Surveyor", "equipment"),
}

ITEM_SIZE = {"gear": (32, 32), "circuit": (32, 32), "motor": (32, 32),
             "drill": (32, 32), "chainsaw": (32, 32), "wrench": (32, 32),
             "surveyor": (32, 32)}


# ---------------------------------------------------------------------------
# Blockbench source writer
# ---------------------------------------------------------------------------

def to_bbmodel(geo: dict, texture: Image.Image, name: str) -> dict:
    """Write a simple, editable Blockbench project for one block geo."""
    import io
    entry = geo["minecraft:geometry"][0]
    texture_data = io.BytesIO()
    texture.save(texture_data, "PNG")
    source = "data:image/png;base64," + base64.b64encode(texture_data.getvalue()).decode("ascii")
    elements = []
    for bone in entry["bones"]:
        for i, c in enumerate(bone.get("cubes", [])):
            from_ = c["origin"]
            to = [from_[j] + c["size"][j] for j in range(3)]
            faces = {}
            for face, data in c["uv"].items():
                u, v = data["uv"]
                w, h = data["uv_size"]
                faces[face] = {
                    "uv": [u, v, u + w, v + h],
                    "texture": 0,
                }
            elements.append({
                "name": f"{bone['name']}_{i}",
                "from": [round(v, 4) for v in from_],
                "to": [round(v, 4) for v in to],
                "origin": [0, 0, 0],
                "faces": faces,
                "type": "cube",
                "uuid": str(uuid.uuid4()),
            })
    groups = []
    for bone in entry["bones"]:
        child_ids = [e["uuid"] for e in elements if e["name"].startswith(bone["name"] + "_")]
        groups.append({
            "name": bone["name"],
            "origin": bone["pivot"],
            "uuid": str(uuid.uuid4()),
            "children": child_ids,
        })
    return {
        "meta": {"format_version": "4.10", "model_format": "bedrock", "box_uv": False},
        "name": name,
        "resolution": {"width": texture.width, "height": texture.height},
        "elements": elements,
        "outliner": groups,
        "textures": [{"name": name, "source": source}],
    }
