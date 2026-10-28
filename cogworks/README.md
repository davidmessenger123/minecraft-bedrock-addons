# Cogworks

A Minecraft Bedrock automation add-on: generate power, run conveyors, automate
crafting, expand storage and carve out a quarry. All block models are included
as editable `.bbmodel` sources in `blockbench/blocks/`.

**Download:** [Cogworks-1.7.0.mcaddon](Cogworks-1.7.0.mcaddon)

- **Blocks:** Coal Generator, Wind Turbine, Solar Panel, Water Wheel, Power
  Transformer, Copper Cable, Battery Bank, Energy Meter, Conveyor Belt, Item
  Filter, Belt Splitter, Belt Merger, Storage Extractor, Storage Terminal,
  Storage Port, Electric Furnace, Crusher, Sawmill, Alloy Smelter, Crafting
  Assembler, Storage Core, Storage Extension and Quarry Controller.
- **Items:** Powered Drill, Powered Chainsaw, Cogworks Wrench, Quarry Surveyor,
  Cogwork Gear, Control Circuit and Electric Motor.
- **Held items:** all seven custom items — drill, chainsaw, wrench, surveyor,
  gear, circuit and motor — have 3D attachable models that render in the
  player's hand in first and third person. Their inventory icons remain.
- **Power:** coal/charcoal/coal-block generation, wind, daylight solar and water
  wheels, a 10,000 E Power Transformer buffer, 5,000 E batteries, copper cable
  networks and machine energy costs.
- **Machine modules:** processor UI upgrades Speed, Efficiency and Parallel
  using gears, circuits and motors.
- **Visible transport:** item stacks ride on belts as display entities.
  Filter pass-lists, three-way splitters and three-input mergers let you build
  real routing lines. Belts automatically choose straight, left-corner or
  right-corner geometry from adjacent belt connections — there is no separate
  corner item.
- **Splitter filtering:** each splitter output (front/left/right) has its own
  pass-list; click that side with an item to configure it.
- **Storage:** a core supports 8 item stacks; every connected Storage Extension
  adds another 8. Use the wrench on storage blocks and ports to cycle a
  copper/iron/gold/amethyst channel; only matching channels connect. The
  storage form has search; a Storage Extractor pulls selected items back onto
  belts with priority and allow/deny filter modes.
- **Terminal and native bridge:** the Storage Terminal adds search, withdrawal
  and a persistent recipe queue with running/queued states, progress, cancel
  and rotate controls. The Storage Port bridges an adjacent chest, barrel or
  hopper into the virtual storage network for vanilla-style input/output.
- **Processing:** Electric Furnace, Crusher, Sawmill and Alloy Smelter use
  data-driven recipes from `tools/recipes.json`, with per-recipe energy and
  processing time. Crusher doubles ore output; Sawmill cuts logs; Alloy Smelter
  makes netherite.
- **Power:** Wind Turbine, Solar Panel and Water Wheel add renewable
  generation; the Power Transformer buffers 10,000 E and the Energy Meter shows
  the connected network total.
- **Blueprint preview (1.7 start):** sneak-use the Cogworks Wrench on a machine
  to copy settings; use it normally on the same machine type to paste them.
- **Automation:** the assembler has selectable recipes and automatic mode. Working
  machines raise their status light to level 15 and pulse teal; blocked/idle
  machines pulse orange/blue.
- **Quarry:** survey two corners, install the area on the controller, and it
  digs from the top of the surveyed footprint all the way down to the
  dimension floor (bedrock in the Overworld). It reports progress, supports
  output filters, Fortune/Silk Touch, an ores-only mode, area marker particles
  and chunk loading, and pushes drops to storage or belts.
- **Tools:** the drill supports 1×1, 3×3 and 3×3×3 modes (sneak-use to cycle);
  the chainsaw fells the connected tree; the wrench rotates conveyors, filters,
  splitters, mergers and extractors.

### Held item models

All seven custom items use Bedrock attachables:

- `resource_pack/models/entity/cw_drill.geo.json`
- `resource_pack/attachables/cw_drill.json`
- `resource_pack/animations/cw_drill.animation.json`

The same pattern is used for `chainsaw`, `wrench`, `surveyor`, `gear`, `circuit`
and `motor`. Their root bone is bound with
`q.item_slot_to_bone_name(context.item_slot)`, so the model follows the player's
hand. The attachable animations select separate first- and third-person poses.
Their Blockbench sources are in `blockbench/tools/`.

Target: **Minecraft Bedrock 1.26.60+** with stable Script API **2.0.0**.

## Install

1. Open `Cogworks-1.7.0.mcaddon` with Minecraft Bedrock.
2. Enable **Cogworks Behaviour Pack** and **Cogworks Resource Pack** for the world.
3. Reload the world. No experiments are required unless your build exposes the
   stable Script API modules behind **Beta APIs**.

## Getting started

Craft a **Coal Generator**, **Copper Cable**, **Battery Bank**, **Conveyor Belt**
and **Storage Core**:

- **Gear:** iron ingots + copper ingots.
- **Circuit:** redstone + gold ingot.
- **Motor:** two gears + circuit + four copper ingots.
- **Generator:** iron, copper and a furnace.
- **Conveyor:** iron, gears and redstone.
- **Filter / splitter / merger:** iron, gears, circuit and redstone.
- **Electric Furnace / Crusher / Sawmill / Alloy Smelter:** iron, gears,
  motors, circuits and a furnace or blast furnace.
- **Wind Turbine / Solar Panel / Water Wheel / Energy Meter:** iron, copper,
  gears, motors, circuits, glass, water and fuel-free generation.
- **Storage Core / Extension:** iron, copper/circuit and a barrel.
- **Storage Extractor:** iron, circuits, gears and a barrel.
- **Wrench:** iron and copper.
- **Drill / Chainsaw:** iron, gear and motor.
- **Quarry:** iron blocks, gears, a motor and a circuit.

Place a generator next to a cable network, add a battery, then place machines
on the same network. Right-click a generator with coal to fuel it.

### Conveyor setup

Place conveyors facing the direction the player is looking. Use the **Cogworks
Wrench** to cycle a machine's direction. A belt carries one visible stack at a
time and passes it to a storage block, assembler, generator, filter or the next
belt.

Belts auto-connect like rails: placing a belt beside an idle belt turns the
idle belt toward it, and the block automatically switches between straight,
left-corner and right-corner geometry based on the incoming neighbor. There is
no separate belt-corner block or item.

Right-click a belt with an item to add or remove it from that belt's input
pass-list. Empty-hand interact to see its buffer and filters. The **Item
Filter** rejects items that are not on its list; **Belt Splitter** cycles items
between front, left and right outputs. Click a splitter's output side with an
item to give that output its own filter. **Belt Merger** accepts from its sides
and outputs forward.

### Storage

A **Storage Core** starts with 8 slots. Place **Storage Extensions** next to it
(or in a connected chain) to add 8 slots each. Interact empty-handed to open the
storage form, search by item name or ID, withdraw an item, or deposit the item
in your main hand. Conveyors can deposit directly into a core or extension.

Place a **Storage Extractor** beside storage and point it at a belt to pull
items out. It has a pass-list, three priority levels and an allow/deny filter
mode. Higher-priority extractors on the same storage are serviced first.

Storage networks have four channels: **copper, iron, gold and amethyst**. Use
the wrench on a Storage Core, Extension or Port to cycle its channel. Only
storage blocks and ports on the same channel share a network.

A **Storage Terminal** placed beside storage opens the same search form plus a
**Recipe Terminal** page. It shows the running job and progress, with cancel,
rotate-first and clear-queue controls. A **Storage Port** placed beside storage
and a chest, barrel or hopper bridges that native inventory into the network;
toggle it between import and export. This gives vanilla hoppers a supported
route into and out of Cogworks storage without requiring experimental
custom-block containers.

### Assembler

The **Crafting Assembler** accepts items from a conveyor or by right-clicking
with an item. Interact empty-handed to open its status and choose **Select
recipe** or **Use automatic recipe**. It can run:

- oak logs → oak planks
- oak planks → sticks
- raw iron + coal → iron ingots
- raw gold + coal → gold ingots
- raw copper → copper ingots
- iron ingots → gears
- redstone + gold → control circuits
- gears + circuit + copper → electric motors

Each recipe costs energy. Output is pushed to an adjacent conveyor or storage.
Working machines pulse teal; blocked or waiting machines pulse orange/blue.

### Processing machines

The **Electric Furnace**, **Crusher**, **Sawmill** and **Alloy Smelter** accept
items by right-clicking or from belts. Empty-hand interact to inspect their
input, output, progress and recipes. Output is pushed to an adjacent belt or
storage. Recipes, energy costs and processing times live in
`tools/recipes.json` and are injected into the script at build time.

- Electric Furnace smelts raw ores, sand and cobblestone.
- Crusher doubles iron/gold/copper ore output and crushes stone/gravel.
- Sawmill turns vanilla logs into matching planks.
- Alloy Smelter turns netherite scrap and gold into netherite ingots.

Processors have three module levels: **Speed** (2 gears), **Efficiency**
(2 circuits) and **Parallel** (1 motor). Speed accelerates progress,
Efficiency reduces energy use, and Parallel multiplies output.

### Power

The **Wind Turbine** generates energy based on its height, the **Solar Panel**
generates during daylight, and the **Water Wheel** generates when adjacent to
water. The **Power Transformer** pulls from nearby generation/batteries into a
10,000 E high-capacity buffer. All connect to the same cable network. The
**Energy Meter** shows total stored network energy.

### Blueprints — start of 1.7

Sneak-use the **Cogworks Wrench** on a machine to copy its settings. Use the
wrench normally on another block of the same type to paste those settings. This
previews the 1.7 factory-control work.

### Quarry

1. Right-click two blocks with the **Quarry Surveyor** to set the X/Z footprint.
2. Right-click a **Quarry Controller** with the surveyor to install the area.
3. Connect a Storage Core or conveyor, a Storage Extractor and a powered cable
   network.
4. Interact empty-handed with the quarry to start or pause it.

The quarry's footprint is limited to **32×32**, but its depth is the full
dimension height from the top surveyed Y down to the dimension floor. In the
Overworld this reaches **bedrock at Y=-64**. It skips air, fluids, bedrock and
Cogworks machines, reports scanned/mined progress, and can filter which drops
are collected. The controller can toggle **Fortune** and **Silk Touch**, and it
loads its excavation area while active. Right-click the quarry with an item to
toggle that item as an output filter; use **Clear output filters** in its form.

Output is buffered until an adjacent storage block or conveyor accepts it.

## Models and source

The block and held-item models are generated from `tools/content.py`; the
editable Blockbench sources live in `blockbench/blocks/` and
`blockbench/tools/`. The shipped add-on uses the exported `.geo.json` models and
the shared `cw_blocks` texture atlas. The
[block model sheet](previews/models.png) shows all twenty-three blocks, the
[item model sheet](previews/tools.png) shows all seven held items, and
[belt shape sheet](previews/belt_shapes.png) shows the automatic corner
variants. [previews/materials.png](previews/materials.png) shows the industrial
palette.

```text
cogworks/
  behavior_pack/   blocks, items, recipes, loot, scripts, language, manifest
  resource_pack/   geometry, terrain/item atlases, texture, language, manifest
  blockbench/      editable block and held-tool .bbmodel sources
  tools/           content.py, generate.py, main.js, render.py, validate.py, VERSION
```

Rebuild:

```bash
/tmp/opencode/bloom-venv/bin/python cogworks/tools/generate.py
node --check cogworks/behavior_pack/scripts/main.js
/tmp/opencode/bloom-venv/bin/python cogworks/tools/validate.py
```

## Notes

- Item transport and storage are script-driven virtual inventories. Visible
  belt stacks are display entities and cannot be picked up by players; the
  actual authoritative stack is still in the belt/machine data.
- The seven held items are Bedrock attachables. The geometry is editable, but
  first/third-person grip tuning is best checked in a live world.
- Native hopper support is provided through the Storage Port and an adjacent
  chest, barrel or hopper, because custom block containers still require an
  experimental Bedrock feature.
- The add-on is static-validated here. Live Bedrock testing is still needed for
  the custom block tick component, display entities, UI forms, energy/conveyor
  behavior, the new quarry depth and attachable rendering.
