# Bloomlands

A flower-filled custom dimension for **Minecraft Bedrock Edition**, entered through a
4×4 flower bed and a rainbow portal on the ground. The island is a gentle garden of
five themed regions plus the Bloomlands Edge, giant tree-sized blooms, a dense
glowing canopy, terraced petal hills, a mirror lake and three hand-modelled peaceful
Bloomling mobs.

- **Dimension:** `bl:bloomlands` — a void dimension with a script-built floating island.
- **Portal:** a 4×4 flower bed surrounding a 2×2 End-portal-style rainbow surface.
- **Regions:** Sunpetal Meadow, Whispering Canopy, Giant's Garden, Petal Hills,
  Mirror Pool and the Bloomlands Edge.
- **Mobs:** Petalwing, Mossling and Dewdrop Snail, each with a 128×128 atlas,
  detailed geometry, idle/move animations and a Creative spawn egg.
- **Blocks:** 26 custom blocks, including seven small flowers, six giant blooms,
  Bloomwood, petal grass, paths, canopy leaves and the rainbow portal surface.
- **No hostile mobs.** The biome omits the `monster` tag and a runtime sweep removes
  any vanilla hostile that somehow appears.
- **No experiments required.** Built for Bedrock **1.26.60+** with stable
  `@minecraft/server` **2.0.0**.

## What changed in 2.2.5

- The Bloomgate now shows **“The Bloomlands are still waking”** while the
  first-time island build runs, instead of announcing arrival before the
  teleport has happened.
- Cross-dimension teleport is retried and verified; a fallback teleport without
  facing data is attempted if the first form is rejected.
- Portal detection checks both the block at the player's feet and the block
  directly below, so it works whether the flat portal surface has collision or
  not.
- The first visit can still take several minutes while the island is generated;
  progress feedback remains visible during that wait.

## What changed in 2.2.4

- Fixed Bloomgate activation when clicking a grass block. The item now uses a
  registered `bl:bloomgate` custom component with `onUseOn`/`onUse`, instead of
  relying only on the block-interaction after-event.
- The portal builder now searches all 4×4 grass patches around the clicked
  block. Clicking near the edge of a grass field no longer fails just because
  the clicked block was treated as the centre.
- Added fallback view-ray targeting and support for the `minecraft:grass` alias
  and `bl:petal_grass` in addition to `minecraft:grass_block`.
- Repeated use is guarded by the existing build/cooldown state.

## What changed in 2.2.3

- Changed the Bloomgate recipe from grass blocks to dirt. The portal still has
  to be built on a 4x4 grass patch, but the item itself is now obtainable
  without a Silk Touch pickaxe.
- The recipe still uses only vanilla blocks: dirt, poppies and an amethyst block.

## What changed in 2.2.2

- Bloomgate now builds the portal itself: use it while looking at a **grass
  block**, and the surrounding 4×4 flower bed and 2×2 rainbow surface are
  created automatically.
- The 4×4 footprint must be entirely `minecraft:grass_block`; stone, sand,
  dirt, podzol and mixed ground are rejected.
- Replaced the Bloomgate crafting recipe with one that uses only vanilla
  blocks: grass blocks, poppies and an amethyst block.

## What changed in 2.2.1

- Fixed flower targeting when Bedrock reports the ground block under a flower
  instead of the flower block itself. Oxeye daisies and other vanilla flowers
  now work from either surface.

## What changed in 2.2.0

- Replaced the old 7×7 plaza/Bloomheart entrance with a **4×4 flower ritual**:
  place any 16 flowers in a square, use Bloomgate on one flower, and step onto
  the central **2×2 rainbow portal**.
- The portal uses a **recoloured vanilla Nether-portal animation sheet**, so it
  keeps the original portal motion with a full rainbow palette.
- Cleaned up the custom flower silhouettes: five outer petals instead of six,
  simpler giant-bloom crowns, softer grass and path colours, and a new
  flower-bed portal icon.

## Install

1. Open `Bloomlands-2.2.5.mcaddon` with Minecraft Bedrock.
2. Enable **Bloomlands Behaviour Pack** and **Bloomlands Resource Pack** for the world.
3. Reload the world. The first load creates the island; this can take several minutes
   because the dimension is void-generated, every block is placed by the script, and
   the 480-block garden is built in sixteen chunk-loading passes.
4. No experimental toggles are needed. If your build exposes stable Script API 2.0.0
   behind **Beta APIs**, enable that experiment.

The add-on targets Bedrock **1.26.60** and newer. Custom dimensions require
**1.26.50+**; the manifests use the newer version so the dimension, biomes and
script modules all load together.

## Getting to the Bloomlands

### Craft a Bloomgate

The **Bloomgate** item (`bl:bloom_portal`) uses only vanilla blocks:

```text
D F D
F A F
D F D

D = minecraft:dirt
F = minecraft:poppy
A = minecraft:amethyst_block
```

Use the Bloomgate while looking at or clicking a **grass block** in the
Overworld, Nether or End. The builder searches for a valid 4×4 grass patch
around the clicked block, clears small plants and creates the 4×4 flower bed
with the flat animated rainbow portal in the central 2×2. Grass-block aliases
and Bloomlands petal grass are accepted; stone, sand, dirt, podzol and mixed
ground are rejected. The area above the bed must be clear of solid blocks.

A starter kit is also available:

```mcfunction
/function bloomlands/kit
```

### Travel and return

Step onto the **rainbow surface** in the centre of the flower bed to open the way.
The first visit generates the island and teleports you to the arrival platform
south of the return portal.

To go home, step onto the return portal at the island spawn. Your exact return
position and dimension are saved. The portal is disarmed after a journey until you
step off it, so returning onto the same spot does not immediately send you back.

The return rainbow portal at the island spawn is rooted: its portal blocks cannot
be broken, so a curious explorer cannot strand themselves.

## The island

The island is roughly 480 blocks across (a 240-block radius), with its base surface
at **Y = 64**. Broad grass swells and smaller knolls raise much of the meadow,
forest and garden by one to four blocks, while paths cut level benches through
them. The arrival platform sits south of the return portal: the southern rim
is about 114 blocks away, the centre about 126 blocks, and the northern rim about
366 blocks. Terrain, flowers, trees, paths, water and the return gate are all
placed once and then saved with the world.

The script builds the island in sixteen 8x8-chunk tiles with a one-chunk feature
margin. Each tile gets its own temporary ticking area, so generation stays inside
Bedrock's ticking-area budget; the central tile is built last so the arrival and
return areas can be probed before the island is marked complete.

| Region | Direction | Character |
| --- | --- | --- |
| **Sunpetal Meadow** | South / spawn | Open flower fields, the arrival path and the return portal |
| **Whispering Canopy** | North | Dense Bloomwood forest with a closed leaf ceiling, glowbud patches, fireflies and dim green fog |
| **Giant's Garden** | East | Giant flower trees, broad petals, warm pink fog and drifting pollen |
| **Petal Hills** | North-west | Six walkable terraces with a spiral path, overlooks and giant crown blooms |
| **Mirror Pool** | West | A still lake, lily blooms, a small central island and a giant skybell |
| **Bloomlands Edge** | Outer rim | A stone rim, floating islets and the open sky beyond the garden |

The canopy is deliberately solid overhead: old-growth Bloomwoods have 3×3
trunks, 5×5 ancient trunks, flared roots, branch arms and overlapping rounded
crowns. When you are under the trees, the leaf ceiling blocks the sky. Region
fog, action-bar names, particles and ambient colour change as you cross between
areas.

## Blocks and recipes

The main building blocks are Bloom Dirt, Bloom Stone, Petal Grass, Petal Path,
Bloomwood Logs and Bloomwood Planks. The flowers are Sunpetal, Rosequartz, Skybell,
Moondrop, Emberbloom, Amethyst Bell and Lumen Bell. Giant versions of the blooms can
be placed as tree-sized centrepieces.

Useful recipes:

- **Bloomgate:** poppy / fern / amethyst shard pattern above.
- **Bloomgate Flower:** Lumen Bell + Rosequartz + Sunpetal + glowstone dust → 2.
- **Petal Grass:** Bloom Dirt + Sunpetal + Dewgrass.
- **Petal Path:** Bloom Dirt + Sunpetal + Rosequartz → 2.
- **Bloomwood Planks:** one Bloomwood Log → 4.

The rainbow portal uses the Nether portal's animated surface treatment with
rainbow colour bands. Giant blooms and the Bloomgate flower have custom geometry
and glow; the small flowers share one detailed model with per-colour textures.

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

The generated `.mcaddon` is `bloomlands/Bloomlands-2.2.5.mcaddon`. The validator
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
  blocks and keep only the spawn/return area ticking. Existing 1.0.0 and 2.0.0
  worlds use a fresh generation marker and are rebuilt around the old garden, so
  they receive the rolling ground and the new old-growth canopy. Rebuilding can
  overwrite player changes made inside the generated island footprint.
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
