# Cogworks

A Minecraft Bedrock automation add-on: generate power, run conveyors, automate
crafting, expand storage and carve out a quarry. All block models are included
as editable `.bbmodel` sources in `blockbench/blocks/`.

**Download:** [Cogworks-1.2.0.mcaddon](Cogworks-1.2.0.mcaddon)

- **Blocks:** Coal Generator, Copper Cable, Battery Bank, Conveyor Belt,
  Item Filter, Belt Splitter, Belt Merger, Storage Extractor, Crafting
  Assembler, Storage Core, Storage Extension and Quarry Controller.
- **Items:** Powered Drill, Powered Chainsaw, Cogworks Wrench, Quarry Surveyor,
  Cogwork Gear, Control Circuit and Electric Motor.
- **Held items:** all seven custom items — drill, chainsaw, wrench, surveyor,
  gear, circuit and motor — have 3D attachable models that render in the
  player's hand in first and third person. Their inventory icons remain.
- **Power:** coal/charcoal/coal-block generation, 5,000 E batteries, copper
  cable networks and machine energy costs.
- **Visible transport:** item stacks now ride on belts as display entities.
  Filter pass-lists, three-way splitters and three-input mergers let you build
  real routing lines.
- **Storage:** a core supports 8 item stacks; every connected Storage Extension
  adds another 8. The storage form has search; a Storage Extractor pulls the
  selected items back out onto a belt.
- **Automation:** the assembler has selectable recipes and automatic mode. Working
  machines raise their status light to level 15 and pulse teal; blocked/idle
  machines pulse orange/blue.
- **Quarry:** survey two corners, install the area on the controller, and it
  digs from the top of the surveyed footprint all the way down to the
  dimension floor (bedrock in the Overworld). It reports progress, supports
  output filters, and pushes drops to storage or belts.
- **Tools:** the drill breaks a 3×3 stone/ore face; the chainsaw fells a vertical
  run of logs; the wrench rotates conveyors, filters, splitters, mergers and
  extractors.

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

1. Open `Cogworks-1.2.0.mcaddon` with Minecraft Bedrock.
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

Right-click a belt with an item to add or remove it from that belt's pass-list.
Empty-hand interact to see its buffer and filters. The **Item Filter** rejects
items that are not on its list; **Belt Splitter** cycles items between front,
left and right outputs; **Belt Merger** accepts from its sides and outputs
forward.

### Storage

A **Storage Core** starts with 8 slots. Place **Storage Extensions** next to it
(or in a connected chain) to add 8 slots each. Interact empty-handed to open the
storage form, search by item name or ID, withdraw an item, or deposit the item
in your main hand. Conveyors can deposit directly into a core or extension.

Place a **Storage Extractor** beside storage and point it at a belt to pull
items out. The extractor has its own pass-list and uses the same wrench
rotation as a belt.

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
are collected. Right-click the quarry with an item to toggle that item as an
output filter; use **Clear output filters** in its form.

Output is buffered until an adjacent storage block or conveyor accepts it.

## Models and source

The block and held-item models are generated from `tools/content.py`; the
editable Blockbench sources live in `blockbench/blocks/` and
`blockbench/tools/`. The shipped add-on uses the exported `.geo.json` models and
the shared `cw_blocks` texture atlas. The
[block model sheet](previews/models.png) shows all twelve blocks, the
[item model sheet](previews/tools.png) shows all seven held items, and
[previews/materials.png](previews/materials.png) shows the industrial palette.

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
- The four held tools are Bedrock attachables. The geometry is editable, but
  first/third-person grip tuning is best checked in a live world.
- The add-on is static-validated here. Live Bedrock testing is still needed for
  the custom block tick component, display entities, UI forms, energy/conveyor
  behavior, the new quarry depth and attachable rendering.
