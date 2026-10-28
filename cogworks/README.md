# Cogworks

A Minecraft Bedrock automation add-on: generate power, run conveyors, automate
crafting, expand storage and carve out a quarry. All block models are included
as editable `.bbmodel` sources in `blockbench/blocks/`.

**Download:** [Cogworks-1.0.0.mcaddon](Cogworks-1.0.0.mcaddon)

- **Blocks:** Coal Generator, Copper Cable, Battery Bank, Conveyor Belt,
  Crafting Assembler, Storage Core, Storage Extension, Quarry Controller.
- **Items:** Powered Drill, Powered Chainsaw, Cogworks Wrench, Quarry Surveyor,
  Cogwork Gear, Control Circuit, Electric Motor.
- **Power:** the generator burns coal/charcoal/coal blocks; batteries buffer
  energy; copper cables connect machines.
- **Transport:** conveyors move virtual stacks between machines and storage.
- **Storage:** a core supports 8 item stacks; every connected Storage Extension
  adds another 8. Use the Storage Core form to deposit or withdraw.
- **Automation:** the assembler processes a recipe when its input contains the
  ingredients and the network has enough energy.
- **Quarry:** use the Quarry Surveyor on two corners, then on the Quarry
  Controller. It mines the selected volume and sends drops to connected storage
  or conveyors.
- **Tools:** the drill breaks a 3×3 stone/ore face; the chainsaw fells a vertical
  run of logs; the wrench rotates conveyors.

Target: **Minecraft Bedrock 1.26.60+** with stable Script API **2.0.0**.

## Install

1. Open `Cogworks-1.0.0.mcaddon` with Minecraft Bedrock.
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
- **Storage Core / Extension:** iron, copper/circuit and a barrel.
- **Wrench:** iron and copper.
- **Drill / Chainsaw:** iron, gear and motor.
- **Quarry:** iron blocks, gears, a motor and a circuit.

Place a generator next to a cable network, add a battery, then place machines
on the same network. Right-click a generator with coal to fuel it.

### Conveyor setup

Place conveyors facing the direction the player is looking. Use the **Cogworks
Wrench** to cycle a conveyor's direction. A conveyor carries one stack at a time
and passes it to a storage block, assembler, generator or the next conveyor.

### Storage

A **Storage Core** starts with 8 slots. Place **Storage Extensions** next to it
(or in a connected chain) to add 8 slots each. Interact empty-handed to open the
storage form; hold an item and interact to deposit it. Conveyors can deposit
directly into a core or extension.

### Assembler

The **Crafting Assembler** accepts items from a conveyor or by right-clicking
with an item. It automatically runs the first available recipe:

- oak logs → oak planks
- oak planks → sticks
- raw iron + coal → iron ingots
- raw gold + coal → gold ingots
- raw copper → copper ingots
- iron ingots → gears
- redstone + gold → control circuits
- gears + circuit + copper → electric motors

Each recipe costs energy. Output is pushed to an adjacent conveyor or storage.

### Quarry

1. Right-click two blocks with the **Quarry Surveyor** to set opposite corners.
2. Right-click a **Quarry Controller** with the surveyor to install the area.
3. Connect a Storage Core or conveyor and a powered cable network.
4. Interact empty-handed with the quarry to start or pause it.

The quarry is limited to **32×32×32** and skips air, fluids, bedrock and
Cogworks machines. Drops are buffered until an adjacent storage block or
conveyor accepts them.

## Models and source

The block models are generated from `tools/content.py`; the editable Blockbench
sources live in `blockbench/blocks/`. The shipped add-on uses the exported
`.geo.json` models and the shared `cw_blocks` texture atlas. The
[model sheet](previews/models.png) shows all eight blocks, and
[previews/materials.png](previews/materials.png) shows the industrial palette.

```text
cogworks/
  behavior_pack/   blocks, items, recipes, scripts, language, manifest
  resource_pack/   geometry, terrain/item atlases, texture, language, manifest
  blockbench/      editable block .bbmodel sources
  tools/           content.py, generate.py, main.js, validate.py, VERSION
```

Rebuild:

```bash
/tmp/opencode/bloom-venv/bin/python cogworks/tools/generate.py
node --check cogworks/behavior_pack/scripts/main.js
```

## Notes

- This is a first release. Machine state is stored in block-entity dynamic
  properties; item transport and storage are virtual rather than native chest
  inventories, so the forms are the primary player interface.
- The add-on is static-validated here. Live Bedrock testing is still needed for
  the custom block tick component, UI forms and energy/conveyor behavior.
