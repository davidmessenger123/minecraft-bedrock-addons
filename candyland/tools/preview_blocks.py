"""Render a review sheet of the block pattern library."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from candy import Canvas, get_ramp, dye_ramp  # noqa: E402
import patterns as P  # noqa: E402
from preview import save, contact  # noqa: E402

T = {}


def tile(name, fn, size=32):
    c = Canvas(size)
    fn(c)
    T[name] = save(c, name, 4)


def build():
    tile("stone", lambda c: P.rock(c, 11, get_ramp("rock_candy"), scale=4.0,
                                  cells=4.0, facet=.9, grain=.7))
    tile("cobble", lambda c: P.cobble(
        c, 12, get_ramp("rock_candy"),
        ["rock_candy", "rock_candy_pink", "rock_candy_mint", "rock_candy_lilac"],
        get_ramp("licorice"), cells=5))
    tile("deepslate", lambda c: P.rock(c, 13, get_ramp("obsidian_jelly"),
                                       cells=5.5, facet=.45, grain=.4))
    tile("dirt", lambda c: P.crumb(c, 14, get_ramp("chocolate"), scale=5.0,
                                   sprinkles=[(230, 170, 110)]))
    tile("grass", lambda c: P.grass_top(c, 15, get_ramp("mint"), colored=False))
    tile("grass_side", lambda c: P.grass_side_mask(c, 16, get_ramp("mint")))
    tile("sand", lambda c: P.sugar(c, 17, get_ramp("sugar")))
    tile("planks", lambda c: P.planks(c, 18, get_ramp("wafer"), get_ramp("caramel")))
    tile("log", lambda c: P.log_side(c, 19, get_ramp("bark_wafer"),
                                     get_ramp("chocolate"), get_ramp("caramel")))
    tile("log_end", lambda c: P.log_end(c, 20, get_ramp("wafer"),
                                        get_ramp("chocolate"), get_ramp("caramel")))
    tile("leaves", lambda c: P.leaves(c, 21, get_ramp("mint"), colored=False))
    tile("wool", lambda c: P.wool(c, 22, get_ramp("cotton_candy")))
    tile("glass", lambda c: P.glass(c, 23))
    tile("ore_coal", lambda c: P.ore(c, 24, get_ramp("rock_candy"),
                                     get_ramp("coal_candy"), gems=4))
    tile("ore_dia", lambda c: P.ore(c, 25, get_ramp("rock_candy"),
                                    get_ramp("diamond_candy"), gems=4))
    tile("gem_dia", lambda c: P.gem_block(c, 26, get_ramp("diamond_candy")))
    tile("gem_em", lambda c: P.gem_block(c, 27, get_ramp("emerald_candy")))
    tile("bricks", lambda c: P.bricks(c, 28, get_ramp("strawberry"), get_ramp("meringue")))
    tile("cake_top", lambda c: P.cake_top(
        c, 29, get_ramp("sponge_cake"), get_ramp("marshmallow"),
        [(255, 120, 160), (120, 220, 255), (255, 230, 120)], (230, 40, 70)))
    tile("cake_side", lambda c: P.cake_side(
        c, 30, get_ramp("sponge_cake"), get_ramp("marshmallow"),
        [(255, 120, 160), (120, 220, 255), (255, 230, 120)], (230, 40, 70)))
    tile("metal", lambda c: P.metal(c, 31, get_ramp("gold_wrap")))
    tile("water", lambda c: P.fluid_still(c, 32, get_ramp("blue_raspberry"),
                                          (230, 250, 255), 0, 1))
    tile("lava", lambda c: P.fluid_still(c, 33, get_ramp("magma_jam"),
                                         (255, 240, 150), 0, 1))
    tile("fudge", lambda c: P.fudge(c, 34, get_ramp("milk_chocolate")))
    tile("taffy", lambda c: P.taffy(c, 35, get_ramp("purpur_taffy")))
    tile("honeycomb", lambda c: P.honeycomb(c, 36, get_ramp("honeycomb"), (120, 72, 18)))
    tile("gravel", lambda c: P.gravel(c, 37, ["rock_candy", "sugar", "licorice"],
                                      get_ramp("caramel")))
    tile("netherrack", lambda c: P.crumb(c, 39, get_ramp("red_velvet"),
                                         get_ramp("strawberry"), holes=.04))
    tile("endstone", lambda c: P.rock(c, 40, get_ramp("lemon_meringue"), scale=4.0,
                                      cells=5.0, facet=.25, grain=.35))
    tile("obsidian", lambda c: P.rock(c, 41, get_ramp("obsidian_jelly"), scale=3.0,
                                      grain=.5, sparkle=.02))
    tile("mud", lambda c: P.crumb(c, 42, get_ramp("mud_pudding"), holes=.02))
    tile("clay", lambda c: P.rock(c, 43, get_ramp("clay_lavender"), scale=6.0,
                                  cells=6.0, facet=.15, grain=.3))
    contact(list(T), out="candy_sheet", scale=4, cols=8)


if __name__ == "__main__":
    build()
    print("ok", len(T))
