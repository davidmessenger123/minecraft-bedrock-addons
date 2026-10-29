# Cogworks

A Minecraft Bedrock automation add-on: generate power, run conveyors, automate
crafting, expand storage and carve out a quarry. All block models are included
as editable `.bbmodel` sources in `blockbench/blocks/`.

**Download:** [Cogworks-1.9.1.mcaddon](Cogworks-1.9.1.mcaddon)

- **Blocks:** Coal Generator, Wind Turbine, Solar Panel, Water Wheel, Power
  Transformer, Copper Cable, MV Cable, HV Cable, Battery Bank, Tool Charger,
  Energy Meter, Conveyor Belt, Conveyor Lift, Item Filter, Belt Splitter, Belt
  Merger, Storage Extractor, Storage Terminal, Storage Port, Electric Furnace,
  Crusher, Sawmill, Alloy Smelter, Crafting Assembler, Storage Core, Storage
  Extension and Quarry Controller.
- **Items:** Powered Drill, Powered Chainsaw, Battery Drill, Battery Chainsaw,
  Cogworks Wrench, Quarry Surveyor, Cogwork Gear, Control Circuit and Electric
  Motor.
- **Held items:** all nine custom items have 3D attachable models that render
  in the player's hand. The Battery Drill and Battery Chainsaw reuse the drill
  and chainsaw geometry with their own rechargeable item behavior. First- and
  third-person hold and swing animations are included.
- **Power:** coal/charcoal/coal-block generation, wind, daylight solar and water
  wheels, a 10,000 E Power Transformer buffer, 5,000 E batteries, copper cable
  networks and machine energy costs.
- **Power tiers:** Copper (LV), MV and HV cables carry 128/512/2,048 E per
  transfer operation. Machines have a configurable LV/MV/HV voltage requirement;
  the Power Transformer tier contributes to network voltage and can step a
  network up or down.
- **Machine modules:** processor UI upgrades Speed, Efficiency and Parallel
  using gears, circuits and motors.
- **Machine I/O:** processors and the assembler have per-side input/output/both/
  disabled modes, auto-output and side item filters. Sneak-use a machine side
  with an item to toggle that side's filter.
- **Tool Charger:** a dedicated station that recharges Battery Drill and
  Battery Chainsaw from the connected power network.
- **Ownership:** processors, assembler, Tool Charger and quarry can be claimed
  and shared with named players; `cw:admin` bypasses locks.
- **Vertical transport:** Conveyor Lift moves one stack per block up or down
  through stacked lift columns. Wrench changes direction; right-click with an
  item toggles its filter.
- **Quarry jobs:** save surveyed areas, load queued jobs, auto-start the next
  job, auto-restart the current area, and send completion notices to the owner,
  members or nearby players.
- **Performance:** short-lived energy and storage-network caches reduce repeated
  BFS scans; caches invalidate on placement, breaking, channel changes and
  blueprint channel edits.
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
  belts with priority and allow/deny filter modes. Networks can be claimed by
  a player and shared with named members.
- **Terminal and native bridge:** the Storage Terminal adds search, withdrawal,
  remote links and a persistent recipe queue with running/queued states,
  progress, cancel and rotate controls. Requests specify an output quantity and
  recursively queue missing sub-crafts; queue execution uses a multiplayer
  lease so only one terminal processes a job at a time. The Storage Port bridges
  an adjacent chest, barrel or hopper into the virtual storage network for
  vanilla-style input/output.
- **Request crafting:** select a recipe in the terminal and enter an output
  quantity. Missing ingredients are planned as child jobs where a Cogworks
  recipe exists, then the parent job runs when its inputs are ready.
- **Processing:** Electric Furnace, Crusher, Sawmill and Alloy Smelter use
  data-driven recipes from `tools/recipes.json`, with per-recipe energy and
  processing time. Crusher doubles ore output; Sawmill cuts logs; Alloy Smelter
  makes netherite.
- **Power:** Wind Turbine, Solar Panel and Water Wheel add renewable
  generation; the Power Transformer buffers 10,000 E and the Energy Meter shows
  the connected network total.
- **Blueprints:** sneak-use the Cogworks Wrench on a machine to open a named
  blueprint library; save settings and apply up to 32 named blueprints. Normal
  wrench use applies the last blueprint to a matching machine.
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
  splitters, mergers and extractors. Battery Drill and Battery Chainsaw store
  500 charge; right-click a Tool Charger or connected Battery Bank to recharge
  them.

### Held item models

All nine custom items use Bedrock attachables:

- `resource_pack/models/entity/cw_drill.geo.json`
- `resource_pack/attachables/cw_drill.json`
- `resource_pack/animations/cw_drill.animation.json`

The same pattern is used for `chainsaw`, `wrench`, `surveyor`, `gear`,
`circuit` and `motor`. `cw_battery_drill.json` and `cw_battery_chainsaw.json`
reuse the drill/chainsaw geometry and animations. Their root bone is bound with
`q.item_slot_to_bone_name(context.item_slot)`, so the model follows the player's
hand. The attachable definitions include separate first/third-person hold
poses and swing/use poses driven by `variable.attack_time` and
`query.is_using_item`. Their Blockbench sources are in `blockbench/tools/`.

Target: **Minecraft Bedrock 1.26.60+** with stable Script API **2.0.0**.

## Install

1. Open `Cogworks-1.9.1.mcaddon` with Minecraft Bedrock.
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
- **Conveyor Lift:** iron, gears, a conveyor and a motor.
- **MV / HV Cable:** copper cables plus circuits, then MV cable plus circuits.
- **Filter / splitter / merger:** iron, gears, circuit and redstone.
- **Electric Furnace / Crusher / Sawmill / Alloy Smelter:** iron, gears,
  motors, circuits and a furnace or blast furnace.
- **Wind Turbine / Solar Panel / Water Wheel / Energy Meter:** iron, copper,
  gears, motors, circuits, glass, water and fuel-free generation.
- **Storage Core / Extension:** iron, copper/circuit and a barrel.
- **Tool Charger:** iron, circuits and a Battery Bank.
- **Storage Extractor:** iron, circuits, gears and a barrel.
- **Wrench:** iron and copper.
- **Drill / Chainsaw:** iron, gear and motor.
- **Battery Drill / Battery Chainsaw:** the matching powered tool, a Battery
  Bank and a Control Circuit. Right-click a connected Battery Bank with a
  battery tool to recharge it.
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

A **Conveyor Lift** moves its buffered stack to the block above or below,
depending on its direction. Stack lifts to form a vertical line; a lift at the
top can feed a belt or storage. Use the wrench to toggle up/down and
right-click with an item to toggle its filter.

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

### Remote terminals, access and job leases

- **Remote link:** sneak-use the wrench on a Storage Core or Extension to copy
  its coordinates, then use the wrench normally on a Storage Terminal to bind
  that terminal to the remote network. The terminal keeps the linked storage
  area loaded while bound. Sneak-use the terminal with the wrench to clear the
  link.
- **Team access:** open a Storage Core or Terminal and choose **Network access**
  to claim the network, add or remove named players, or release it. The owner
  and listed members can open the network; players with the `cw:admin` tag
  bypass the lock.
- **Multiplayer queue:** recipe jobs carry a terminal lease on the storage
  core. Only one terminal processes a queue at a time; a broken or unloaded
  terminal's lease expires so another terminal can take over.

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

### Machine I/O

Processors and the **Crafting Assembler** expose **Side configuration** in
their forms. Each of the six sides can be **both**, **input**, **output** or
**disabled**. **Auto-output** can be turned off to buffer finished items.
Sneak-use a machine side with an item to add or remove a filter for that side;
the side filter applies to both input and output. This lets belts feed a
machine from the back while it exports from a side or bottom. The default is
all sides `both`, which preserves the original machine behavior.

Machine access is managed from the side-configuration form. Claim a processor,
assembler or Tool Charger to make it private, then add named members. Quarry
access is managed from its controller form. The `cw:admin` tag bypasses machine
locks.

The same form cycles each machine's **Voltage requirement** through LV, MV and
HV. A machine stops when its requirement is above the connected network tier.

### Power

The **Wind Turbine** generates energy based on its height, the **Solar Panel**
generates during daylight, and the **Water Wheel** generates when adjacent to
water. The **Power Transformer** pulls from nearby generation/batteries into a
10,000 E high-capacity buffer. All connect to the same cable network. The
**Energy Meter** shows total stored network energy. The **Tool Charger** uses
that network to refill Battery Drill and Battery Chainsaw charge.

Power networks have three cable tiers: **Copper (LV)**, **MV** and **HV**.
The highest cable or transformer tier in the connected network sets its tier
and transfer capacity (128, 512 and 2,048 E per operation). Processors and the
assembler have a configurable **Voltage requirement** in their Side
configuration form; a machine whose requirement exceeds the network tier stops
with a blocked status. Cycle the **Power Transformer** tier to step a network
up or down. Existing factories default to all-LV, so they keep working.

### Blueprints

Sneak-use the **Cogworks Wrench** on a machine to open the **Blueprint
Library**. Save the current settings under a name, then apply that named
blueprint to any machine of the same type. The last applied blueprint also
remains on the wrench clipboard for normal use on matching machines. Up to 32
named blueprints are stored per player.

Blueprints cover recipes, filters, splitter outputs, modes, priorities,
processor modules, side I/O, auto-output, side filters, quarry
Fortune/Silk/ores-only options and the storage channel.

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

The controller's scheduler can **Save current area**, **Load next saved job**,
**Auto-start next job**, **Auto-restart current** and toggle **Completion
notices**. Completion messages go to the quarry owner/members, or nearby
players when the quarry is unclaimed. Claim access from **Machine access**.

Output is buffered until an adjacent storage block or conveyor accepts it.

## Models and source

The block and held-item models are generated from `tools/content.py`; the
editable Blockbench sources live in `blockbench/blocks/` and
`blockbench/tools/`. The shipped add-on uses the exported `.geo.json` models and
the shared `cw_blocks` texture atlas. The
[block model sheet](previews/models.png) shows all twenty-seven blocks, the
[item model sheet](previews/tools.png) shows all nine held items, and
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
- The nine held items are Bedrock attachables. The geometry is editable, but
  first/third-person grip and swing tuning is best checked in a live world.
  The battery tools share the drill/chainsaw geometry.
- Native hopper support is provided through the Storage Port and an adjacent
  chest, barrel or hopper, because custom block containers still require an
  experimental Bedrock feature.
- The add-on is static-validated here. Live Bedrock testing is still needed for
  the custom block tick component, display entities, UI forms, energy/conveyor
  behavior, quarry depth, attachable rendering and swing animations, remote
  terminal links, storage/machine access lists, battery-tool charge behavior,
  machine side I/O, Tool Charger energy transfer, Conveyor Lift transport,
  quarry scheduling and network cache invalidation, power tiers, cable
  capacity, transformer tier changes and machine voltage cutoffs.
