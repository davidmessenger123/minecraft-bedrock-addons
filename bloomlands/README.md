# Bloomlands

A flower-filled custom dimension for **Minecraft Bedrock Edition**, entered through a
4×4 flower bed and a rainbow portal on the ground. The world is a gently rolling
procedural garden of five themed regions plus the Bloomlands Edge, giant tree-sized
blooms, a dense glowing canopy, terraced petal hills, a mirror lake and three
hand-modelled peaceful Bloomling mobs.

- **Dimension:** `bl:bloomlands` — a void dimension with a lazy, deterministic
  script generator. Only the spawn sanctuary is built up front; the wider garden is
  generated in 16×16 chunks as players explore.
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

## What changed in 3.0.0

- **Procedural generation:** new worlds now build a small arrival/return sanctuary
  and then generate the Bloomlands lazily in deterministic 16×16 chunks around
  players. The old 480-block prebuilt island is no longer built for new worlds.
- **Fast first entry:** the Bloomgate only waits for the spawn sanctuary and its
  immediate chunks instead of the entire island.
- **Chunk queue:** two nearby chunks are generated per world tick; explored chunks
  are recorded so they do not rebuild after reload.
- **Giant's Garden redesign:** cleaner five-petal giant blooms with domed centres,
  layered glowing tree crowns, flared roots and denser flower paths around the
  garden trees.
- **Backward compatibility:** worlds that already contain the legacy handcrafted
  island keep it. New worlds use the procedural layout. Existing legacy worlds can
  keep the updated blocks/models without being regenerated.

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

1. Open `Bloomlands-3.0.0.mcaddon` with Minecraft Bedrock.
2. Enable **Bloomlands Behaviour Pack** and **Bloomlands Resource Pack** for the world.
3. Reload the world. New worlds build only the arrival/return sanctuary first;
   the surrounding garden streams in as you explore. Expect a few seconds for the
   sanctuary and brief generation pop-in at new chunk borders. Existing 2.2.x
   worlds keep their prebuilt island.
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
The first visit builds the small arrival sanctuary and teleports you to the platform
south of the return portal. The surrounding garden then streams in as you explore.

To go home, step onto the return portal at the island spawn. Your exact return
position and dimension are saved. The portal is disarmed after a journey until you
step off it, so returning onto the same spot does not immediately send you back.

The return rainbow portal at the island spawn is rooted: its portal blocks cannot
be broken, so a curious explorer cannot strand themselves.

## World generation

New Bloomlands worlds are **procedural**. The script builds a compact arrival and
return sanctuary at the portal, then generates the surrounding garden lazily in
deterministic 16×16 chunks. A small queue adds two nearby chunks per world tick as
players explore; generated chunk coordinates are saved so they are not rebuilt
after a reload.

- The base terrain sits around **Y = 64**, with rolling meadow swells, higher
  hill bluffs, canopy rises and lower pool basins.
- The spawn sanctuary contains the arrival platform, path and rooted return gate.
- The wider garden is regenerated from coordinate hashes, so the landscape is
  continuous and repeatable without storing a 480-block island.
- Brief void or pop-in can appear at a chunk border while the queue catches up.
- Worlds created before 3.0.0 keep their legacy handcrafted island. Create a new
  world to get the procedural layout.

| Region | Direction | Character |
| --- | --- | --- |
| **Sunpetal Meadow** | South / spawn | Open flower fields, the arrival path and the return portal |
| **Whispering Canopy** | North | Dense Bloomwood forest with a closed leaf ceiling, glowbud patches, fireflies and dim green fog |
| **Giant's Garden** | East | Redesigned giant flower trees with layered crowns, broad five-petal blooms, petal paths and drifting pollen |
| **Petal Hills** | North-west | Rolling high bluffs and flower slopes |
| **Mirror Pool** | West | Low damp basins, lily blooms and a giant skybell |
| **Bloomlands Edge** | Outer ring | Stone outcrops and the open sky beyond the garden |

Region fog, action-bar names, particles and ambient colour change as you cross
between areas. The giant garden's blooms use five broad outer petals, five inner
petals and a domed centre; its trees have 3×3 trunks, flared roots and layered
glowing crowns.

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

The generated `.mcaddon` is `bloomlands/Bloomlands-3.0.0.mcaddon`. The validator
checks manifests, both script/data modules, dimension and biome wiring, every block
and item texture, model UVs and bounds, recipes, loot, entity client/behavior
pairs, animation bones, controllers, particles, language keys, Blockbench sources
and the contents of the package.

The `.bbmodel` files are sources for editing; the shipped add-on uses the exported
`.geo.json`, animation and texture files.

## Notes

- The dimension is data-driven but **void-generated**; Bedrock custom dimensions
  support only the void generator. The terrain, vegetation and regions are
  therefore generated by the script.
- New worlds use the lazy 16×16 procedural generator; only the sanctuary and its
  nearby chunks are built up front. Existing 1.0.0–2.2.x worlds keep their legacy
  handcrafted island. Create a new world to receive the procedural layout.
- Generated chunks are saved by coordinate key. Player edits remain in the world;
  a chunk is not rebuilt after reload unless its marker is missing.
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
