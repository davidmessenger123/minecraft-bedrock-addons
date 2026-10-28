# Bloomlands

A flower-filled custom dimension for **Minecraft Bedrock Edition**, entered through a
ring of flowers on the ground. The island is a gentle garden of five themed regions
plus the Bloomlands Edge, giant tree-sized blooms, a dense glowing canopy, terraced
petal hills, a mirror lake and three hand-modelled peaceful Bloomling mobs.

- **Dimension:** `bl:bloomlands` — a void dimension with a script-built floating island.
- **Portal:** a 7×7 petal-path plaza, eight Bloomgate flowers and one Bloomheart.
- **Regions:** Sunpetal Meadow, Whispering Canopy, Giant's Garden, Petal Hills,
  Mirror Pool and the Bloomlands Edge.
- **Mobs:** Petalwing, Mossling and Dewdrop Snail, each with a 128×128 atlas,
  detailed geometry, idle/move animations and a Creative spawn egg.
- **Blocks:** 25 custom blocks, including seven small flowers, six giant blooms,
  Bloomwood, petal grass, paths, canopy leaves and the animated Bloomheart.
- **No hostile mobs.** The biome omits the `monster` tag and a runtime sweep removes
  any vanilla hostile that somehow appears.
- **No experiments required.** Built for Bedrock **1.26.60+** with stable
  `@minecraft/server` **2.0.0**.

## Install

1. Open `Bloomlands-1.0.0.mcaddon` with Minecraft Bedrock.
2. Enable **Bloomlands Behaviour Pack** and **Bloomlands Resource Pack** for the world.
3. Reload the world. The first load creates the island; this can take a little while
   because the dimension is void-generated and every block is placed by the script.
4. No experimental toggles are needed. If your build exposes stable Script API 2.0.0
   behind **Beta APIs**, enable that experiment.

The add-on targets Bedrock **1.26.60** and newer. Custom dimensions require
**1.26.50+**; the manifests use the newer version so the dimension, biomes and
script modules all load together.

## Getting to the Bloomlands

### Craft a Bloomgate

The **Bloomgate** item (`bl:bloom_portal`) is made with a ring of poppies and ferns
around an amethyst shard:

```text
F S F
S A S
F S F

F = minecraft:poppy
S = minecraft:fern
A = minecraft:amethyst_shard
```

Use the Bloomgate on the **top face of a ground block** in the Overworld, Nether or
End. It builds a 7×7 petal-path plaza, places eight Bloomgate flowers in a ring and
sets a Bloomheart in the centre. The area must be clear enough for the 7×7 plaza.

A starter kit is also available:

```mcfunction
/function bloomlands/kit
```

### Travel and return

Stand on the central **Bloomheart** to open the way. The first visit generates the
island and then teleports you to the arrival platform south of the return Bloomgate.

To go home, stand on the Bloomgate at the island's spawn, or on any other
Bloomheart. Your exact return position and dimension are saved. The Bloomheart is
disarmed after a journey until you step off it, so returning onto the same spot does
not immediately send you back.

The return Bloomheart at the island spawn is rooted: it cannot be broken, so a
curious explorer cannot strand themselves.

## The island

The island is roughly 120 blocks across, with its surface at **Y = 64**. Terrain,
flowers, trees, paths, water and the return gate are all placed once and then saved
with the world.

| Region | Direction | Character |
| --- | --- | --- |
| **Sunpetal Meadow** | South / spawn | Open flower fields, the arrival path and the return Bloomgate |
| **Whispering Canopy** | North | Dense Bloomwood forest with a closed leaf ceiling, glowbud patches, fireflies and dim green fog |
| **Giant's Garden** | East | Giant flower trees, broad petals, warm pink fog and drifting pollen |
| **Petal Hills** | North-west | Six walkable terraces with a spiral path, overlooks and giant crown blooms |
| **Mirror Pool** | West | A still lake, lily blooms, a small central island and a giant skybell |
| **Bloomlands Edge** | Outer rim | A stone rim, floating islets and the open sky beyond the garden |

The canopy is deliberately solid overhead: when you are under the trees, the leaf
ceiling blocks the sky. Region fog, action-bar names, particles and ambient colour
change as you cross between areas.

## Blocks and recipes

The main building blocks are Bloom Dirt, Bloom Stone, Petal Grass, Petal Path,
Bloomwood Logs and Bloomwood Planks. The flowers are Sunpetal, Rosequartz, Skybell,
Moondrop, Emberbloom, Amethyst Bell and Lumen Bell. Giant versions of the blooms can
be placed as tree-sized centrepieces.

Useful recipes:

- **Bloomgate:** poppy / fern / amethyst shard pattern above.
- **Bloomheart:** four Bloomgate Flowers + one glowstone.
- **Bloomgate Flower:** Lumen Bell + Rosequartz + Sunpetal + glowstone dust → 2.
- **Petal Grass:** Bloom Dirt + Sunpetal + Dewgrass.
- **Petal Path:** Bloom Dirt + Sunpetal + Rosequartz → 2.
- **Bloomwood Planks:** one Bloomwood Log → 4.

The animated Bloomheart uses a four-frame flipbook. Giant blooms and the Bloomgate
flower have custom geometry and glow; the small flowers share one detailed model
with per-colour textures.

## Bloomlings

All three mobs are passive, persistent and spawnable with Creative spawn eggs or
`/summon`.

- **Petalwing** (`bl:petalwing`) — a moth-like flyer with layered wings, antennae,
  a soft body and a gentle hover. It drifts above the meadow and garden.
- **Mossling** (`bl:mossling`) — a walking moss spirit with a flower crown, leafy
  shoulders, stubby legs and a curious idle. It wanders the forest and terraces.
- **Dewdrop Snail** (`bl:dewdrop_snail`) — a slow snail with a spiral shell, a
  leaf canopy and a soft foot. It prefers the pool edges and damp forest floor.

Natural spawn rules are limited to the `bloomlands` biome tag. The script also
maintains a small population near players so the island never feels empty.

## Source and build

```text
bloomlands/
  behavior_pack/       generated BP: manifests, dimension, biome, blocks, items,
                       recipes, loot, entities, spawn rules, functions, scripts
  resource_pack/       generated RP: manifests, client biome, fogs, textures,
                       models, animations, controllers, particles
  blockbench/          editable .bbmodel sources for blocks and mobs
  previews/            texture sheets, model contact sheet, portal diagram, map
  tools/content.py     original textures, geometry, entity and animation definitions
  tools/generate.py    build and package script
  tools/main.js        runtime portal, terrain, fog, mob and rescue script
  tools/render.py      preview and .bbmodel renderer
  tools/validate.py    structural validator
```

Rebuild and validate from the repository root:

```bash
/tmp/opencode/bloom-venv/bin/python bloomlands/tools/generate.py
/tmp/opencode/bloom-venv/bin/python bloomlands/tools/validate.py
node --check bloomlands/behavior_pack/scripts/main.js
```

The generated `.mcaddon` is `bloomlands/Bloomlands-1.0.0.mcaddon`. The validator
checks manifests, both script/data modules, dimension and biome wiring, every block
and item texture, model UVs and bounds, recipes, loot, entity client/behavior
pairs, animation bones, controllers, particles, language keys, Blockbench sources
and the contents of the package.

The `.bbmodel` files are sources for editing; the shipped add-on uses the exported
`.geo.json`, animation and texture files.

## Notes

- The dimension is data-driven but **void-generated**; Bedrock does not provide
  engine terrain, portals or multiple biomes for a custom dimension. The island,
  vegetation and themed regions are therefore built and dressed by the script.
- The first world load does the heavy generation. Later loads reuse the saved
  blocks and keep only the spawn/return area ticking.
- If you remove the behavior pack from a world, the saved island blocks remain in
  the dimension data but the portal and scripted mobs stop working.
- Models, textures and code in this project are original and released under the
  repository's MIT license.

## Preview

- [Portal layout](previews/portal_layout.png)
- [Region map](previews/region_map.png)
- [Block textures](previews/block_textures.png)
- [Mob atlases](previews/entity_textures.png)
- [Model contact sheet](previews/models.png)
