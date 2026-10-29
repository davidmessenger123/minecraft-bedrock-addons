# Cogworks 1.9.2 — Live Test Checklist

Test the released `Cogworks-1.9.2.mcaddon` in a **copy** of a test world. Do not
use a world whose Cogworks machines you cannot replace.

## Setup

- [ ] Import the `.mcaddon`; enable both Cogworks behaviour and resource packs.
- [ ] Confirm the world has no Cogworks content-log errors on load.
- [ ] Use Creative, keep cheats enabled for coordinates and test setup.
- [ ] Record the package version (`1.9.2`) and Minecraft version.
- [ ] Optionally start a second player/session for multiplayer tests.
- [ ] Open the Blockbench sources from `blockbench/blocks/` and verify the
      Control Panel, MV Cable, HV Cable, Lift and Tool Charger tabs.

## 1. First smoke test

- [ ] Place one of every Cogworks block and confirm the correct 3D model.
- [ ] Hold every custom item in first and third person.
- [ ] Confirm no missing textures, purple/black models or missing language names.
- [ ] Check that every custom item has its inventory icon and 3D attachable.
- [ ] Swing/use the drill, chainsaw, wrench, surveyor and both battery tools;
      confirm hold and swing poses do not clip badly.
- [ ] Break a belt/lift and confirm its visible display entity disappears.

## 2. Power and voltage

### Generation and storage
- [ ] Coal Generator accepts coal, charcoal and coal blocks.
- [ ] Wind Turbine, Solar Panel and Water Wheel generate under their conditions.
- [ ] Energy Meter reports network energy and network tier.
- [ ] Battery Bank fills and discharges; no negative or overflowing energy.
- [ ] Power Transformer buffers up to 10,000 E.

### Cable tiers
- [ ] Copper/LV network reports LV and 128 E capacity.
- [ ] Replace segments with MV Cable; network reports MV and 512 E.
- [ ] Replace with HV Cable; network reports HV and 2,048 E.
- [ ] Mixed cable networks use the highest connected tier.
- [ ] Placing/breaking cable updates the Energy Meter within one second.
- [ ] Reconnect a split network and confirm the tier/capacity recalculates.

### Transformer tiers
- [ ] Cycle the Power Transformer through LV/MV/HV.
- [ ] Confirm the network tier changes and the cache does not stay stale.
- [ ] Confirm a transformer can raise a network even when the cables are lower
      tier.
- [ ] Cycle back down and confirm high-voltage machines stop.

### Machine voltage
- [ ] Set a processor/assembler to LV and run it on an LV network.
- [ ] Set it to MV on an LV network; confirm blocked status.
- [ ] Upgrade the network to MV; confirm it resumes.
- [ ] Set it to HV on an MV network; confirm blocked.
- [ ] Confirm no inputs are consumed while voltage is insufficient.
- [ ] Recharge a battery tool on LV, MV and HV networks; confirm full recharge
      and energy deduction.

## 3. Conveyors, lifts and logistics

- [ ] Place belts and confirm automatic straight/left/right corners.
- [ ] Confirm no separate corner item is required.
- [ ] Verify visible stacks move and cannot be picked up by players.
- [ ] Configure belt input filters and confirm rejected items do not enter.
- [ ] Configure splitter front/left/right output filters and confirm routing.
- [ ] Confirm merger accepts from side inputs and outputs forward.
- [ ] Set a Conveyor Lift to up; verify items climb stacked lifts.
- [ ] Set a Conveyor Lift to down; verify items descend.
- [ ] Feed a lift from a belt and output into a belt/storage/machine.
- [ ] Toggle a lift filter and confirm it rejects the filtered item.
- [ ] Confirm lift display items update and disappear when empty.
- [ ] Reload/unload the chunk and confirm lift buffers and direction persist.

## 4. Machines and side I/O

### Processing
- [ ] Run one recipe in each processor: Electric Furnace, Crusher, Sawmill,
      Alloy Smelter.
- [ ] Run assembler auto mode and a fixed recipe.
- [ ] Confirm outputs only eject through enabled output sides.
- [ ] Confirm inputs are accepted only through enabled input sides.
- [ ] Confirm disabled sides reject both input and output.
- [ ] Toggle Auto-output off; confirm output remains buffered.
- [ ] Toggle Auto-output on; confirm output ejects.
- [ ] Sneak-use a side with an item; confirm the side filter toggles.
- [ ] Confirm a side filter applies to both input and output.
- [ ] Upgrade Speed/Efficiency/Parallel to max and verify effects.
- [ ] Confirm upgrades persist after chunk reload.

### Redstone
- [ ] Set a processor to Redstone: high; power the block and confirm it runs.
- [ ] Remove power; confirm it stops without consuming inputs.
- [ ] Set Redstone: low; confirm behavior is inverted.
- [ ] Set Redstone: ignore; confirm it always runs.
- [ ] Repeat for the assembler and Quarry Controller.

### Ownership
- [ ] Claim a processor from Machine access.
- [ ] Confirm a second player cannot open or insert items.
- [ ] Add the second player as a member; confirm access works.
- [ ] Remove the member; confirm access is denied again.
- [ ] Release the machine; confirm public access returns.
- [ ] Confirm `cw:admin` tag bypasses a lock.
- [ ] Repeat for assembler, Tool Charger and Quarry Controller.

## 5. Storage and terminals

### Basic storage
- [ ] Deposit by hand and from belts into a Storage Core/Extension.
- [ ] Search, withdraw and deposit through the Storage Core form.
- [ ] Confirm capacity is 8 slots per connected core/extension.
- [ ] Cycle copper/iron/gold/amethyst channels; confirm groups separate.
- [ ] Confirm channel changes update immediately, including cached groups.

### Ports and extraction
- [ ] Storage Port imports from a chest/barrel/hopper.
- [ ] Switch to export; confirm items leave storage.
- [ ] Confirm port filters and channel matching.
- [ ] Storage Extractor pulls items onto a belt.
- [ ] Confirm priority and allow/deny filter modes.

### Remote terminal
- [ ] Sneak-wrench a core/extension to copy a storage link.
- [ ] Use the wrench on a Storage Terminal to bind it.
- [ ] Move away/unload the source chunk; confirm the ticking area loads it.
- [ ] Confirm remote search/deposit/withdraw works.
- [ ] Clear the link and confirm the ticking area is removed.
- [ ] Break the terminal and confirm the ticking area is removed.

### Storage permissions
- [ ] Claim a storage network.
- [ ] Confirm non-members cannot open storage, terminal or port forms.
- [ ] Add/remove members and test access.
- [ ] Release the network to public.
- [ ] Confirm `cw:admin` bypasses the lock.

### Request autocrafting
- [ ] Request 1, 4 and 64 of a basic output.
- [ ] Request an item requiring an ingredient that must itself be crafted.
- [ ] Confirm child jobs run before the parent.
- [ ] Confirm missing ingredients stop the queue rather than voiding inputs.
- [ ] Confirm cancel-current, rotate-first and clear-queue still work.
- [ ] Confirm a quantity larger than one craft produces the expected amount.
- [ ] Confirm queue progress and remaining counts update.
- [ ] Confirm old string-based queue entries migrate.
- [ ] Break/restart the terminal; confirm queue and lease recover.

### Multiplayer queue lease
- [ ] Place two terminals on the same storage network.
- [ ] Queue several jobs and confirm only one terminal processes at a time.
- [ ] Break the processing terminal; confirm the other takes over after the
      lease timeout.
- [ ] Confirm no job is processed twice.

## 6. Blueprint library

- [ ] Sneak-wrench a machine; confirm the Blueprint Library opens.
- [ ] Save a named blueprint.
- [ ] Apply it to another machine of the same type.
- [ ] Confirm recipe, filters, side I/O, auto-output, side filters, processor
      modules and channel copy correctly.
- [ ] Confirm mismatched machine types are rejected.
- [ ] Confirm the last applied blueprint still works with normal wrench use.
- [ ] Save 32 blueprints; confirm the 33rd is rejected.
- [ ] Delete a named blueprint and confirm it disappears.
- [ ] Confirm blueprints cover quarry settings and Power Transformer tier.

## 7. Quarry

### Excavation
- [ ] Survey two corners with the Quarry Surveyor.
- [ ] Install the area on the Quarry Controller.
- [ ] Confirm the footprint is capped at 32×32.
- [ ] Confirm excavation reaches the dimension floor/bedrock.
- [ ] Confirm air, fluids, bedrock and Cogworks blocks are skipped.
- [ ] Confirm output filters, Fortune, Silk Touch and ores-only modes.
- [ ] Confirm marker particles appear at the surveyed corners.
- [ ] Confirm chunk loading starts and stops with the quarry.
- [ ] Confirm the quarry finishes and releases its ticking area.

### Scheduler
- [ ] Save the current area.
- [ ] Load next saved job.
- [ ] Save multiple areas and confirm they process in order.
- [ ] Enable auto-start next job; confirm the next job starts automatically.
- [ ] Enable auto-restart current; confirm the completed area restarts.
- [ ] Toggle completion notices; confirm owner/member/nearby messages.
- [ ] Restart a completed area manually.
- [ ] Confirm job queue persists after reload.
- [ ] Pause the quarry via the Control Panel; confirm mining stops and resumes.
- [ ] Set quarry redstone high/low and confirm the same.

### Dashboard and ownership
- [ ] Open Quarry Dashboard from the Control Panel.
- [ ] Confirm nearby quarries appear with state/job counts.
- [ ] Select one and confirm its controller form opens.
- [ ] Claim the quarry and test member access/denial.

## 8. Control Panel and diagnostics

- [ ] Place a Control Panel near a machine group.
- [ ] Link nearby machines; confirm processors, assembler, Tool Charger and
      quarry are picked up.
- [ ] Pause linked machines; confirm they stop processing.
- [ ] Resume linked machines; confirm they restart.
- [ ] Confirm redstone-mode machines still respect redstone independently.
- [ ] Open Storage Diagnostics; confirm counts and 90% alarm.
- [ ] Open Belt Diagnostics; confirm belt/lift counts, loaded buffers and item
      counts.
- [ ] Fill storage to 90% and confirm the alarm.
- [ ] Fill most transport buffers and confirm the belt alarm.
- [ ] Confirm link state survives reload.

## 9. Tools

- [ ] Drill 1×1, 3×3 and 3×3×3 modes; confirm drops.
- [ ] Chainsaw whole-tree felling; confirm leaves/log limit behavior.
- [ ] Wrench rotates belts, filters, splitters, mergers, extractors and lifts.
- [ ] Surveyor sets corners and installs quarry areas.
- [ ] Battery Drill and Battery Chainsaw start full, consume charge and stop at
      zero.
- [ ] Recharge at Tool Charger and Battery Bank; confirm energy is deducted.
- [ ] Confirm charge persists after inventory move/reload.
- [ ] Confirm first/third-person hold and swing animations under movement,
      sneaking, attacking and using.

## 10. Multiplayer

- [ ] Two players can use public machines simultaneously.
- [ ] Locked machines deny the non-member.
- [ ] Storage and machine member lists work independently.
- [ ] Remote terminals work for members but not strangers.
- [ ] Terminal lease prevents duplicate processing.
- [ ] Control Panel linking/pausing is visible to both players.
- [ ] Quarry completion notice reaches the correct recipients.

## 11. Persistence and cleanup

- [ ] Leave the area and return; confirm all buffers and settings persist.
- [ ] Unload chunks and reload the world.
- [ ] Restart the world/server.
- [ ] Confirm no orphaned display items remain after belts/lifts are removed.
- [ ] Confirm no orphaned ticking areas remain after quarries/terminals are
      broken.
- [ ] Confirm removed machines release ownership/queue data cleanly.
- [ ] Watch the content log for script errors during all transitions.
- [ ] Check performance with at least 20 machines and 50 belts/lifts.
- [ ] Confirm placing/breaking blocks, changing channels and changing
      transformer tiers refresh caches within one second.

## 12. Regression

- [ ] Existing 1.0–1.8 factories still run after upgrading.
- [ ] Legacy machine data, queues and storage items are preserved.
- [ ] Existing belt corners still auto-connect.
- [ ] Existing quarry areas still run and can be rescheduled.
- [ ] Existing tool attachables still render.

## Reporting failures

For each failure record:

1. Cogworks version and Minecraft version.
2. Coordinates and dimension.
3. Block/item and UI form involved.
4. Exact steps to reproduce.
5. Expected result and actual result.
6. Content-log error text.
7. Screenshot or short recording.
8. Whether it happens alone or with a second player.
