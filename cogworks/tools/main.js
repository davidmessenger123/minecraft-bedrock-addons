/*
 * Cogworks runtime.
 *
 * Machines are custom blocks with block-entity dynamic properties.  Every
 * machine runs its own tick from minecraft:tick; conveyors and storage use a
 * compact virtual item model so a line can move stacks without relying on
 * fragile item entities.
 */

import {
    world,
    system,
    BlockPermutation,
    ItemStack,
    EquipmentSlot,
    MolangVariableMap,
} from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";

const NS = "cw:";
const GENERATOR = "cw:generator";
const CABLE = "cw:cable";
const BATTERY = "cw:battery";
const TOOL_CHARGER = "cw:tool_charger";
const CONVEYOR = "cw:conveyor";
const FILTER = "cw:filter";
const SPLITTER = "cw:splitter";
const MERGER = "cw:merger";
const EXTRACTOR = "cw:extractor";
const ASSEMBLER = "cw:assembler";
const ELECTRIC_FURNACE = "cw:electric_furnace";
const CRUSHER = "cw:crusher";
const SAWMILL = "cw:sawmill";
const ALLOY_SMELTER = "cw:alloy_smelter";
const WIND_TURBINE = "cw:wind_turbine";
const SOLAR_PANEL = "cw:solar_panel";
const WATER_WHEEL = "cw:water_wheel";
const TRANSFORMER = "cw:transformer";
const ENERGY_METER = "cw:energy_meter";
const STORAGE_CORE = "cw:storage_core";
const STORAGE_EXTENSION = "cw:storage_extension";
const STORAGE_TERMINAL = "cw:storage_terminal";
const STORAGE_PORT = "cw:storage_port";
const QUARRY = "cw:quarry";
const DRILL = "cw:drill";
const CHAINSAW = "cw:chainsaw";
const BATTERY_DRILL = "cw:battery_drill";
const BATTERY_CHAINSAW = "cw:battery_chainsaw";
const BATTERY_TOOLS = new Set([BATTERY_DRILL, BATTERY_CHAINSAW]);
const BATTERY_TOOL_MAX = 500;
const WRENCH = "cw:wrench";
const SURVEYOR = "cw:surveyor";
const MACHINE_COMPONENT = "cw:machine";

const ENERGY_TYPES = new Set([GENERATOR, CABLE, BATTERY, WIND_TURBINE, SOLAR_PANEL, WATER_WHEEL, TRANSFORMER]);
const BELT_TYPES = new Set([CONVEYOR, FILTER, SPLITTER, MERGER, EXTRACTOR]);
const LOGISTICS_TYPES = new Set([FILTER, SPLITTER, MERGER, EXTRACTOR]);
const PROCESSOR_TYPES = new Set([ELECTRIC_FURNACE, CRUSHER, SAWMILL, ALLOY_SMELTER]);
const MACHINE_IO_TYPES = new Set([ASSEMBLER, ELECTRIC_FURNACE, CRUSHER, SAWMILL, ALLOY_SMELTER]);
const MACHINE_SIDES = ["north", "east", "south", "west", "up", "down"];
const SIDE_MODES = ["both", "input", "output", "disabled"];
const FACINGS = ["north", "east", "south", "west"];
const STORAGE_CHANNELS = ["copper", "iron", "gold", "amethyst"];
const OPPOSITE = { north: "south", east: "west", south: "north", west: "east", up: "down", down: "up" };
const LEFT_OF = { north: "west", west: "south", south: "east", east: "north" };
const RIGHT_OF = { north: "east", east: "south", south: "west", west: "north" };
const DRILL_MODES = ["1x1", "3x3", "3x3x3"];
const DIRECTIONS = {
    north: { x: 0, y: 0, z: -1 },
    south: { x: 0, y: 0, z: 1 },
    east: { x: 1, y: 0, z: 0 },
    west: { x: -1, y: 0, z: 0 },
    up: { x: 0, y: 1, z: 0 },
    down: { x: 0, y: -1, z: 0 },
};

const DROPS = {
    "minecraft:stone": "minecraft:cobblestone",
    "minecraft:deepslate": "minecraft:cobbled_deepslate",
    "minecraft:cobbled_deepslate": "minecraft:cobbled_deepslate",
    "minecraft:andesite": "minecraft:andesite",
    "minecraft:diorite": "minecraft:diorite",
    "minecraft:granite": "minecraft:granite",
    "minecraft:calcite": "minecraft:calcite",
    "minecraft:tuff": "minecraft:tuff",
    "minecraft:netherrack": "minecraft:netherrack",
    "minecraft:end_stone": "minecraft:end_stone",
    "minecraft:coal_ore": "minecraft:coal",
    "minecraft:deepslate_coal_ore": "minecraft:coal",
    "minecraft:iron_ore": "minecraft:raw_iron",
    "minecraft:deepslate_iron_ore": "minecraft:raw_iron",
    "minecraft:copper_ore": "minecraft:raw_copper",
    "minecraft:deepslate_copper_ore": "minecraft:raw_copper",
    "minecraft:gold_ore": "minecraft:raw_gold",
    "minecraft:deepslate_gold_ore": "minecraft:raw_gold",
    "minecraft:redstone_ore": "minecraft:redstone",
    "minecraft:deepslate_redstone_ore": "minecraft:redstone",
    "minecraft:lapis_ore": "minecraft:lapis_lazuli",
    "minecraft:deepslate_lapis_ore": "minecraft:lapis_lazuli",
    "minecraft:diamond_ore": "minecraft:diamond",
    "minecraft:deepslate_diamond_ore": "minecraft:diamond",
    "minecraft:emerald_ore": "minecraft:emerald",
    "minecraft:deepslate_emerald_ore": "minecraft:emerald",
    "minecraft:grass_block": "minecraft:dirt",
    "minecraft:dirt": "minecraft:dirt",
    "minecraft:sand": "minecraft:sand",
    "minecraft:red_sand": "minecraft:red_sand",
    "minecraft:gravel": "minecraft:gravel",
    "minecraft:oak_log": "minecraft:oak_log",
    "minecraft:birch_log": "minecraft:birch_log",
    "minecraft:spruce_log": "minecraft:spruce_log",
    "minecraft:jungle_log": "minecraft:jungle_log",
    "minecraft:acacia_log": "minecraft:acacia_log",
    "minecraft:dark_oak_log": "minecraft:dark_oak_log",
    "minecraft:mangrove_log": "minecraft:mangrove_log",
    "minecraft:cherry_log": "minecraft:cherry_log",
};

const MACHINE_RECIPES = /*__MACHINE_RECIPES__*/[];
const ASSEMBLER_RECIPES = MACHINE_RECIPES.filter((recipe) => recipe.machine === "assembler");
const PROCESSOR_MACHINE_KEYS = {
    [ELECTRIC_FURNACE]: "furnace",
    [CRUSHER]: "crusher",
    [SAWMILL]: "sawmill",
    [ALLOY_SMELTER]: "alloy_smelter",
};

function recipesForMachine(blockType) {
    const machine = PROCESSOR_MACHINE_KEYS[blockType];
    return machine ? MACHINE_RECIPES.filter((recipe) => recipe.machine === machine) : [];
}

function warn(...args) {
    try { console.warn("[Cogworks]", ...args); } catch { /* ignore */ }
}

function dynamic(block) {
    try { return block.getComponent("minecraft:dynamic_properties"); }
    catch { return undefined; }
}

function read(block, key, fallback) {
    try {
        const component = dynamic(block);
        const value = component?.get(key);
        return value === undefined ? fallback : value;
    } catch {
        return fallback;
    }
}

function readJson(block, key, fallback) {
    const value = read(block, key, undefined);
    if (typeof value !== "string") return fallback;
    try { return JSON.parse(value); } catch { return fallback; }
}

function write(block, key, value) {
    try {
        const component = dynamic(block);
        if (!component) return;
        if (value === undefined || value === null) component.set(key, undefined);
        else component.set(key, value);
    } catch {
        // A chunk can unload between the tick event and the write.
    }
}

function writeJson(block, key, value) {
    write(block, key, JSON.stringify(value));
}

function neighbor(block, name) {
    const d = DIRECTIONS[name];
    if (!d) return undefined;
    try {
        return block.dimension.getBlock({
            x: block.location.x + d.x,
            y: block.location.y + d.y,
            z: block.location.z + d.z,
        });
    } catch {
        return undefined;
    }
}

function allNeighbors(block) {
    return Object.keys(DIRECTIONS).map((name) => neighbor(block, name)).filter(Boolean);
}

function facing(block) {
    try {
        const value = block.permutation.getState("cw:facing");
        return typeof value === "string" && FACINGS.includes(value) ? value : "north";
    } catch {
        return "north";
    }
}

function setFacing(block, value) {
    try {
        const states = { "cw:facing": value };
        const curve = block.permutation.getState("cw:curve");
        if (typeof curve === "string") states["cw:curve"] = curve;
        block.setPermutation(BlockPermutation.resolve(block.typeId, states));
    } catch {
        // It may be a removed block during a tick.
    }
}

function channelOf(block) {
    try {
        const value = block.permutation.getState("cw:channel");
        return typeof value === "string" ? value : "copper";
    } catch {
        return "copper";
    }
}

function sideToward(target, source) {
    const dx = source.location.x - target.location.x;
    const dy = source.location.y - target.location.y;
    const dz = source.location.z - target.location.z;
    if (dx > 0) return "east";
    if (dx < 0) return "west";
    if (dy > 0) return "up";
    if (dy < 0) return "down";
    if (dz > 0) return "south";
    if (dz < 0) return "north";
    return "north";
}

function machineIo(block) {
    const stored = readJson(block, "io", {});
    const result = {};
    for (const side of MACHINE_SIDES) {
        result[side] = SIDE_MODES.includes(stored[side]) ? stored[side] : "both";
    }
    return result;
}

function machineSideMode(block, side) {
    return machineIo(block)[String(side).toLowerCase()] || "both";
}

function cycleMachineSide(block, side) {
    const io = machineIo(block);
    const current = io[side] || "both";
    const next = SIDE_MODES[(SIDE_MODES.indexOf(current) + 1) % SIDE_MODES.length];
    io[side] = next;
    writeJson(block, "io", io);
    return next;
}

function machineSideFilters(block) {
    return readJson(block, "sideFilters", {});
}

function machineSideFilterAllows(block, side, typeId) {
    const filters = machineSideFilters(block)[side];
    if (!filters || !Object.keys(filters).length) return true;
    return filters[typeId] === true;
}

function toggleMachineSideFilter(block, side, typeId) {
    const filters = machineSideFilters(block);
    filters[side] = filters[side] || {};
    if (filters[side][typeId]) delete filters[side][typeId];
    else filters[side][typeId] = true;
    writeJson(block, "sideFilters", filters);
}

function machineAcceptsFrom(block, side, typeId) {
    if (!MACHINE_IO_TYPES.has(block.typeId)) return true;
    const mode = machineSideMode(block, side);
    if (mode !== "both" && mode !== "input") return false;
    return machineSideFilterAllows(block, side, typeId);
}

function machineOutputsTo(block, side, typeId) {
    if (!MACHINE_IO_TYPES.has(block.typeId)) return true;
    const mode = machineSideMode(block, side);
    if (mode !== "both" && mode !== "output") return false;
    return machineSideFilterAllows(block, side, typeId);
}

function machineAutoOutput(block) {
    return read(block, "autoOutput", true) !== false;
}

function cycleStorageChannel(block) {
    const current = channelOf(block);
    const next = STORAGE_CHANNELS[(STORAGE_CHANNELS.indexOf(current) + 1) % STORAGE_CHANNELS.length];
    try {
        block.setPermutation(BlockPermutation.resolve(block.typeId, { "cw:channel": next }));
    } catch {
        // Ignore transient block unloads.
    }
    return next;
}

function curveOf(block) {
    try {
        const value = block.permutation.getState("cw:curve");
        return typeof value === "string" ? value : "straight";
    } catch {
        return "straight";
    }
}

function setCurve(block, curve) {
    if (block.typeId !== CONVEYOR || curveOf(block) === curve) return;
    try {
        block.setPermutation(BlockPermutation.resolve(block.typeId, {
            "cw:facing": facing(block),
            "cw:curve": curve,
        }));
    } catch {
        // The block may have been removed during a tick.
    }
}

function connectable(block) {
    if (!block) return false;
    return BELT_TYPES.has(block.typeId)
        || block.typeId === STORAGE_CORE
        || block.typeId === STORAGE_EXTENSION
        || block.typeId === ASSEMBLER
        || block.typeId === ELECTRIC_FURNACE
        || block.typeId === CRUSHER
        || block.typeId === SAWMILL
        || block.typeId === ALLOY_SMELTER
        || block.typeId === GENERATOR;
}

function updateBeltCurve(block) {
    if (!block || block.typeId !== CONVEYOR) return;
    const output = facing(block);
    let curve = "straight";
    for (const direction of FACINGS) {
        const next = neighbor(block, direction);
        if (!next || !BELT_TYPES.has(next.typeId)) continue;
        if (facing(next) !== OPPOSITE[direction]) continue;
        if (direction === LEFT_OF[output]) curve = "left";
        else if (direction === RIGHT_OF[output]) curve = "right";
        if (curve !== "straight") break;
    }
    setCurve(block, curve);
}

function updateNeighborCurves(block) {
    for (const next of allNeighbors(block)) updateBeltCurve(next);
}

function autoConnectNeighbors(block) {
    // When a belt is placed beside an idle belt, turn the idle belt toward the
    // new block. This is the rail-like part: a straight test line naturally
    // becomes a bend without a separate corner item.
    for (const direction of FACINGS) {
        const next = neighbor(block, direction);
        if (!next || !BELT_TYPES.has(next.typeId)) continue;
        const toward = OPPOSITE[direction];
        if (facing(next) === toward) continue;
        const front = neighbor(next, facing(next));
        if (front && connectable(front)) continue;
        setFacing(next, toward);
    }
}


function formatName(id) {
    const short = String(id).replace(/^minecraft:/, "").replace(/^cw:/, "Cogworks ");
    return short.split("_").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function action(player, key, replacements = {}) {
    let text = key;
    for (const [name, value] of Object.entries(replacements)) {
        text = text.replaceAll(`{${name}}`, String(value));
    }
    try { player.onScreenDisplay.setActionBar(text); } catch { /* ignore */ }
}

function later(callback) {
    system.run(() => {
        try {
            const result = callback();
            if (result && typeof result.catch === "function") result.catch(() => {});
        } catch (error) {
            warn("deferred UI failed", String(error));
        }
    });
}

function markStatus(block, status) {
    const previous = read(block, "status", "idle");
    const pulse = Number(read(block, "statusPulse", 0)) + 1;
    write(block, "status", status);
    write(block, "statusPulse", pulse % 1000);
    try {
        if (block.permutation.getState("cw:status") !== status) {
            block.setPermutation(BlockPermutation.resolve(block.typeId, { "cw:status": status }));
        }
    } catch {
        // Status is also shown by the form and particle pulse.
    }
    if (previous === status && !(status === "working" && pulse % 4 === 0)) return;
    const color = status === "working"
        ? { red: 0.25, green: 0.95, blue: 0.78 }
        : status === "blocked"
            ? { red: 1.0, green: 0.35, blue: 0.12 }
            : { red: 0.35, green: 0.65, blue: 1.0 };
    try {
        const map = new MolangVariableMap();
        map.setColorRGB("variable.color", color);
        block.dimension.spawnParticle(
            "minecraft:colored_flame_particle",
            { x: block.location.x + 0.5, y: block.location.y + 1.18, z: block.location.z + 0.5 },
            map,
        );
    } catch {
        // Particles are cosmetic; never let one stop a machine tick.
    }
}

function displayLocation(block) {
    return { x: block.location.x + 0.5, y: block.location.y + 0.92, z: block.location.z + 0.5 };
}

function displayKey(block) {
    return `${block.location.x},${block.location.y},${block.location.z}`;
}

function removeDisplay(block) {
    const id = read(block, "displayId", undefined);
    if (typeof id === "string") {
        try { world.getEntity(id)?.remove(); } catch { /* already gone */ }
    }
    write(block, "displayId", undefined);
    write(block, "displaySignature", undefined);
}

function syncDisplay(block) {
    const item = readJson(block, "item", null);
    if (!item || item.amount < 1) {
        removeDisplay(block);
        return;
    }
    const signature = JSON.stringify(item);
    let display;
    const id = read(block, "displayId", undefined);
    if (typeof id === "string") {
        try { display = world.getEntity(id); } catch { display = undefined; }
    }
    if (!display) {
        // Recover a display entity if the block's ID was lost during a reload.
        try {
            for (const entity of block.dimension.getEntitiesAtBlockLocation(block.location)) {
                if (entity.getDynamicProperty("cw:display") === true
                    && entity.getDynamicProperty("cw:displayBelt") === displayKey(block)) {
                    display = entity;
                    write(block, "displayId", entity.id);
                    break;
                }
            }
        } catch {
            // Chunk may be unloading.
        }
    }
    if (display && read(block, "displaySignature", "") !== signature) {
        try { display.remove(); } catch { /* already gone */ }
        display = undefined;
    }
    try {
        if (!display) {
            display = block.dimension.spawnItem(
                new ItemStack(item.id, 1),
                displayLocation(block),
            );
            display.setDynamicProperty("cw:display", true);
            display.setDynamicProperty("cw:displayBelt", displayKey(block));
            write(block, "displayId", display.id);
            write(block, "displaySignature", signature);
        } else {
            display.clearVelocity();
            display.teleport(displayLocation(block));
        }
    } catch {
        // The next tick will retry.
    }
}

world.beforeEvents.entityItemPickup?.subscribe((event) => {
    try {
        if (event.item?.getDynamicProperty("cw:display") === true) {
            event.cancel = true;
        }
    } catch {
        // Ignore transient item entities.
    }
});

function addItem(player, typeId, count) {
    if (!count || count < 1) return;
    try {
        const inventory = player.getComponent("minecraft:inventory");
        const container = inventory?.container;
        if (!container) return;
        const stack = new ItemStack(typeId, Math.min(64, count));
        const leftover = container.addItem(stack);
        if (leftover) player.dimension.spawnItem(leftover, player.location);
        if (count > 64) addItem(player, typeId, count - 64);
    } catch (error) {
        warn("could not give item", String(error));
    }
}

function heldItem(player) {
    try {
        const equippable = player.getComponent("minecraft:equippable");
        return equippable?.getEquipment(EquipmentSlot.Mainhand);
    } catch {
        return undefined;
    }
}

function damageHeld(player, item, amount = 1) {
    if (!player || !item) return;
    try {
        const durability = item.getComponent("minecraft:durability");
        const equippable = player.getComponent("minecraft:equippable");
        if (!durability || !equippable) return;
        durability.damage += amount;
        if (durability.damage >= durability.maxDurability) {
            equippable.setEquipment(EquipmentSlot.Mainhand, undefined);
            player.sendMessage("Your Cogworks tool has worn out.");
        } else {
            equippable.setEquipment(EquipmentSlot.Mainhand, item);
        }
    } catch {
        // The player may have changed slot while the action was running.
    }
}

function batteryCharge(item) {
    try {
        const value = item.getDynamicProperty("cw:charge");
        if (typeof value === "number" && Number.isFinite(value)) return Math.max(0, Math.min(BATTERY_TOOL_MAX, value));
    } catch {
        // Older items start at a full charge.
    }
    return BATTERY_TOOL_MAX;
}

function setBatteryCharge(player, item, charge) {
    try {
        item.setDynamicProperty("cw:charge", Math.max(0, Math.min(BATTERY_TOOL_MAX, charge)));
        player.getComponent("minecraft:equippable")?.setEquipment(EquipmentSlot.Mainhand, item);
    } catch {
        // The player may have changed slot.
    }
}

function consumeBatteryTool(player, item) {
    const charge = batteryCharge(item);
    if (charge <= 0) {
        action(player, "Battery empty. Right-click a Battery Bank to recharge.");
        return false;
    }
    setBatteryCharge(player, item, charge - 1);
    action(player, `Battery: ${Math.max(0, charge - 1)}/${BATTERY_TOOL_MAX}`);
    return true;
}

function rechargeBatteryTool(player, block, item) {
    const charge = batteryCharge(item);
    if (charge >= BATTERY_TOOL_MAX) {
        action(player, "Battery tool is already full.");
        return;
    }
    const need = BATTERY_TOOL_MAX - charge;
    const available = networkEnergy(block);
    const energy = Math.min(need, available);
    if (energy < 1 || !drainEnergy(block, energy)) {
        action(player, "The network has no energy available.");
        return;
    }
    setBatteryCharge(player, item, charge + energy);
    action(player, `Recharged battery tool to ${charge + energy}/${BATTERY_TOOL_MAX}.`);
}

function takeHeld(player, typeId, count) {
    try {
        const inventory = player.getComponent("minecraft:inventory");
        const container = inventory?.container;
        if (!container) return 0;
        let left = count;
        for (let slot = 0; slot < container.size && left > 0; slot++) {
            const item = container.getItem(slot);
            if (!item || item.typeId !== typeId) continue;
            const take = Math.min(item.amount, left);
            if (item.amount === take) container.setItem(slot, undefined);
            else {
                item.amount -= take;
                container.setItem(slot, item);
            }
            left -= take;
        }
        return count - left;
    } catch {
        return 0;
    }
}

function inventoryCount(player, typeId) {
    try {
        const container = player.getComponent("minecraft:inventory")?.container;
        if (!container) return 0;
        let total = 0;
        for (let slot = 0; slot < container.size; slot++) {
            const item = container.getItem(slot);
            if (item?.typeId === typeId) total += item.amount;
        }
        return total;
    } catch {
        return 0;
    }
}

function upgradeProcessor(player, block, kind) {
    const definitions = {
        speed: { item: "cw:gear", count: 2, max: 3, label: "Speed" },
        efficiency: { item: "cw:circuit", count: 2, max: 3, label: "Efficiency" },
        parallel: { item: "cw:motor", count: 1, max: 3, label: "Parallel" },
    };
    const definition = definitions[kind];
    if (!definition) return;
    const current = Number(read(block, kind, 0));
    if (current >= definition.max) {
        action(player, `${definition.label} is already max level.`);
        return;
    }
    if (inventoryCount(player, definition.item) < definition.count) {
        action(player, `Need ${definition.count} ${formatName(definition.item)}.`);
        return;
    }
    takeHeld(player, definition.item, definition.count);
    write(block, kind, current + 1);
    action(player, `${definition.label} upgraded to ${current + 1}.`);
}

function insertStorage(start, typeId, amount) {
    if (!start || amount < 1) return 0;
    const group = storageGroup(start);
    if (!group.length) return 0;
    const core = group.find((block) => block.typeId === STORAGE_CORE) || group[0];
    const items = readJson(core, "items", {});
    const capacity = group.length * 8;
    let usedSlots = Object.values(items).reduce(
        (sum, count) => sum + Math.ceil(Number(count || 0) / 64), 0);
    let totalUnits = Object.values(items).reduce((sum, count) => sum + Number(count || 0), 0);
    if (!items[typeId] && usedSlots >= capacity) return 0;
    const maxByUnits = capacity * 64 - totalUnits;
    const accepted = Math.min(amount, Math.max(0, maxByUnits));
    if (accepted < 1) return 0;
    items[typeId] = Number(items[typeId] || 0) + accepted;
    writeJson(core, "items", items);
    return accepted;
}

function storageGroup(start) {
    const queue = [start];
    const seen = new Set();
    const blocks = [];
    const channel = channelOf(start);
    while (queue.length) {
        const block = queue.shift();
        if (!block) continue;
        const key = `${block.location.x},${block.location.y},${block.location.z}`;
        if (seen.has(key)) continue;
        seen.add(key);
        if (block.typeId !== STORAGE_CORE && block.typeId !== STORAGE_EXTENSION) continue;
        if (channelOf(block) !== channel) continue;
        blocks.push(block);
        for (const next of allNeighbors(block)) {
            if (next && (next.typeId === STORAGE_CORE || next.typeId === STORAGE_EXTENSION)) {
                queue.push(next);
            }
        }
    }
    return blocks;
}

function takeStorage(start, typeId, amount) {
    const group = storageGroup(start);
    const core = group.find((block) => block.typeId === STORAGE_CORE) || group[0];
    if (!core) return 0;
    const items = readJson(core, "items", {});
    const have = Number(items[typeId] || 0);
    const take = Math.min(have, amount);
    if (take > 0) {
        if (have === take) delete items[typeId];
        else items[typeId] = have - take;
        writeJson(core, "items", items);
    }
    return take;
}

function storageInfo(start) {
    const group = storageGroup(start);
    const core = group.find((block) => block.typeId === STORAGE_CORE) || group[0];
    return {
        core,
        capacity: group.length * 8,
        items: core ? readJson(core, "items", {}) : {},
    };
}

function storageOwner(core) {
    return core ? String(read(core, "owner", "") || "") : "";
}

function storageMembers(core) {
    return core ? readJson(core, "members", []) : [];
}

function canAccessStorage(core, player) {
    if (!core || !player) return false;
    const owner = storageOwner(core);
    if (!owner) return true;
    return owner === player.name
        || storageMembers(core).includes(player.name)
        || (typeof player.hasTag === "function" && player.hasTag("cw:admin"));
}

function isStorageAdmin(core, player) {
    const owner = storageOwner(core);
    return !owner || owner === player.name
        || (typeof player.hasTag === "function" && player.hasTag("cw:admin"));
}

function claimStorage(player, core) {
    const owner = storageOwner(core);
    if (owner && owner !== player.name && !(typeof player.hasTag === "function" && player.hasTag("cw:admin"))) {
        action(player, "This storage network already has an owner.");
        return;
    }
    write(core, "owner", player.name);
    const members = new Set(storageMembers(core));
    members.add(player.name);
    writeJson(core, "members", [...members]);
    action(player, `Storage network claimed by ${player.name}.`);
}

function addStorageMember(player, core, name) {
    if (!isStorageAdmin(core, player)) {
        action(player, "Only the network owner can manage members.");
        return;
    }
    const target = String(name || "").trim();
    if (!target) return;
    const members = new Set(storageMembers(core));
    members.add(target);
    writeJson(core, "members", [...members]);
    action(player, `Added ${target} to the storage network.`);
}

function removeStorageMember(player, core, name) {
    if (!isStorageAdmin(core, player)) {
        action(player, "Only the network owner can manage members.");
        return;
    }
    const target = String(name || "").trim();
    const owner = storageOwner(core);
    if (!target || target === owner) {
        action(player, "The network owner cannot be removed.");
        return;
    }
    writeJson(core, "members", storageMembers(core).filter((member) => member !== target));
    action(player, `Removed ${target} from the storage network.`);
}

function releaseStorage(player, core) {
    if (!isStorageAdmin(core, player)) {
        action(player, "Only the network owner can release it.");
        return;
    }
    write(core, "owner", "");
    writeJson(core, "members", []);
    action(player, "Storage network released to public access.");
}

function openAccessForm(player, core) {
    const form = new ActionFormData()
        .title("Storage Network Access")
        .body(`Owner: ${storageOwner(core) || "unclaimed"}\nMembers: ${storageMembers(core).join(", ") || "none"}\n\nOnly the owner or members can open this network. Tags with cw:admin bypass the lock.`)
        .button("Claim network")
        .button("Add member")
        .button("Remove member")
        .button("Release network")
        .button("Close");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection === 0) {
            claimStorage(player, core);
            return;
        }
        if (response.selection === 1 || response.selection === 2) {
            const modal = new ModalFormData()
                .title(response.selection === 1 ? "Add Storage Member" : "Remove Storage Member")
                .textField("Player name", "exact player name");
            modal.show(player).then((result) => {
                if (!result || result.canceled) return;
                const name = String(result.formValues?.[0] || "");
                if (response.selection === 1) addStorageMember(player, core, name);
                else removeStorageMember(player, core, name);
            }).catch(() => {});
            return;
        }
        if (response.selection === 3) releaseStorage(player, core);
    }).catch(() => {});
}

function linkedStorage(terminal) {
    const link = readJson(terminal, "linked", null);
    if (!link || typeof link.x !== "number") return undefined;
    try {
        const dimension = link.dimension ? world.getDimension(link.dimension) : terminal.dimension;
        const block = dimension.getBlock({ x: link.x, y: link.y, z: link.z });
        if (block && (block.typeId === STORAGE_CORE || block.typeId === STORAGE_EXTENSION)) return block;
    } catch {
        // Chunk unloaded or link is invalid.
    }
    return undefined;
}

function terminalStorage(terminal) {
    return adjacentStorage(terminal) || linkedStorage(terminal);
}

function copyStorageLink(player, block) {
    const core = storageInfo(block).core || block;
    if (!canAccessStorage(core, player)) {
        action(player, "This storage network is private.");
        return;
    }
    player.setDynamicProperty("cw:storage_link", JSON.stringify({
        x: block.location.x,
        y: block.location.y,
        z: block.location.z,
        dimension: block.dimension.id,
        channel: channelOf(block),
    }));
    action(player, "Storage link copied. Use the wrench on a Storage Terminal to bind it.");
}

function remoteChunkName(terminal) {
    const dimension = String(terminal.dimension.id || "minecraft:overworld").replace(/[^a-z0-9]/gi, "");
    return `cw_remote_${dimension}_${terminal.location.x}_${terminal.location.y}_${terminal.location.z}`;
}

function releaseRemoteChunk(terminal) {
    const name = remoteChunkName(terminal);
    try {
        const manager = world.tickingAreaManager;
        if (manager?.hasTickingArea(name)) manager.removeTickingArea(name);
    } catch {
        // Fall through to the command.
    }
    try {
        terminal.dimension.runCommand(`tickingarea remove ${name}`);
    } catch {
        // It may not exist.
    }
}

function ensureRemoteChunk(terminal, link) {
    if (!link || typeof link.x !== "number") return;
    let dimension;
    try { dimension = link.dimension ? world.getDimension(link.dimension) : terminal.dimension; } catch { return; }
    const name = remoteChunkName(terminal);
    const from = { x: link.x - 16, y: Math.max(-64, link.y - 16), z: link.z - 16 };
    const to = { x: link.x + 16, y: Math.min(320, link.y + 16), z: link.z + 16 };
    try {
        const manager = world.tickingAreaManager;
        if (manager?.hasTickingArea(name)) return;
        if (manager && (!manager.hasCapacity || manager.hasCapacity({ dimension, from, to }))) {
            const pending = manager.createTickingArea(name, { dimension, from, to });
            if (pending?.catch) pending.catch(() => {});
            return;
        }
    } catch {
        // Fall through to the command.
    }
    try {
        dimension.runCommand(`tickingarea add ${from.x} ${from.y} ${from.z} ${to.x} ${to.y} ${to.z} ${name}`);
    } catch {
        // Already exists or area capacity is full.
    }
}

function applyStorageLink(player, terminal) {
    const raw = player.getDynamicProperty("cw:storage_link");
    if (typeof raw !== "string") return false;
    try {
        const link = JSON.parse(raw);
        releaseRemoteChunk(terminal);
        writeJson(terminal, "linked", link);
        ensureRemoteChunk(terminal, link);
        action(player, `Storage Terminal linked to ${link.x},${link.y},${link.z}.`);
        return true;
    } catch {
        return false;
    }
}

function terminalKey(terminal) {
    const dimension = String(terminal.dimension.id || "minecraft:overworld").replace(/[^a-z0-9]/gi, "");
    return `cw_term_${dimension}_${terminal.location.x}_${terminal.location.y}_${terminal.location.z}`;
}

async function openStorage(player, block, query = "", terminal = false) {
    const info = storageInfo(block);
    if (!info.core) {
        player.sendMessage("Connect a Storage Extension to a Storage Core first.");
        return;
    }
    if (!canAccessStorage(info.core, player)) {
        action(player, "This storage network is private. Ask the owner for access.");
        return;
    }
    const needle = String(query || "").trim().toLowerCase();
    const entries = Object.entries(info.items)
        .filter(([typeId]) => !needle
            || typeId.toLowerCase().includes(needle)
            || formatName(typeId).toLowerCase().includes(needle))
        .sort(([a], [b]) => a.localeCompare(b));
    const used = Object.values(info.items).reduce((sum, count) => sum + Math.ceil(Number(count || 0) / 64), 0);
    const form = new ActionFormData()
        .title(terminal ? "Storage Terminal" : "Storage Core")
        .body(`Capacity: ${used}/${info.capacity} slots\nConnected blocks: ${info.capacity / 8}\nChannel: ${channelOf(info.core)}\nOwner: ${storageOwner(info.core) || "unclaimed"}\nEnergy: ${networkEnergy(info.core)}\n${needle ? `Search: ${query}\n` : ""}${terminal ? "Search, withdraw, craft or manage access." : "Use a Storage Extractor to pull items onto belts."}`);
    form.button("Search items");
    form.button("Deposit held item");
    if (terminal) form.button("Recipe Terminal");
    form.button("Network access");
    const entryStart = terminal ? 4 : 3;
    if (!entries.length) form.button(needle ? "No matching items" : "No stored items");
    for (const [typeId, count] of entries) {
        form.button(`${formatName(typeId)}  x${count}`);
    }
    let response;
    try { response = await form.show(player); } catch { return; }
    if (response.canceled) return;
    if (response.selection === 0) {
        const search = new ModalFormData()
            .title("Search Storage")
            .textField("Item name or identifier", "e.g. iron or minecraft:coal", { defaultValue: query });
        let result;
        try { result = await search.show(player); } catch { return; }
        if (result.canceled) return;
        const nextQuery = String(result.formValues?.[0] || "");
        later(() => openStorage(player, block, nextQuery, terminal));
        return;
    }
    if (response.selection === 1) {
        const item = heldItem(player);
        if (!item) {
            action(player, "Hold an item to deposit it.");
            return;
        }
        const accepted = insertStorage(block, item.typeId, item.amount);
        if (accepted < 1) {
            action(player, "Storage is full.");
            return;
        }
        takeHeld(player, item.typeId, accepted);
        action(player, `Deposited ${accepted} ${formatName(item.typeId)}.`);
        return;
    }
    if (terminal && response.selection === 2) {
        later(() => openRecipeTerminal(player, info.core));
        return;
    }
    if (response.selection === (terminal ? 3 : 2)) {
        later(() => openAccessForm(player, info.core));
        return;
    }
    const [typeId, count] = entries[response.selection - entryStart] || [];
    if (!typeId) return;
    const take = Math.min(64, count);
    const taken = takeStorage(block, typeId, take);
    addItem(player, typeId, taken);
    action(player, `Withdrew ${taken} ${formatName(typeId)}.`);
}

function adjacentStorage(block, channel = null) {
    for (const next of allNeighbors(block)) {
        if (!next || (next.typeId !== STORAGE_CORE && next.typeId !== STORAGE_EXTENSION)) continue;
        if (channel === null || channelOf(next) === channel) return next;
    }
    return undefined;
}

function nativeContainer(block) {
    try {
        return block?.getComponent("minecraft:inventory")?.container;
    } catch {
        return undefined;
    }
}

function adjacentNativeContainer(port) {
    for (const next of allNeighbors(port)) {
        if (!next) continue;
        if (next.typeId === "minecraft:chest"
            || next.typeId === "minecraft:trapped_chest"
            || next.typeId === "minecraft:barrel"
            || next.typeId === "minecraft:hopper") {
            const container = nativeContainer(next);
            if (container) return { block: next, container };
        }
    }
    return undefined;
}

function tickStoragePort(port) {
    const storage = adjacentStorage(port, channelOf(port));
    const native = adjacentNativeContainer(port);
    if (!storage || !native) return;
    const mode = read(port, "mode", "import");
    const filters = beltFilters(port);
    const hasFilter = Object.keys(filters).length > 0;
    const allows = (typeId) => !hasFilter || filters[typeId] === true;
    const { container } = native;
    if (mode === "import") {
        for (let slot = 0; slot < container.size; slot++) {
            const item = container.getItem(slot);
            if (!item || !allows(item.typeId)) continue;
            const accepted = insertStorage(storage, item.typeId, item.amount);
            if (accepted <= 0) continue;
            if (accepted >= item.amount) container.setItem(slot, undefined);
            else {
                item.amount -= accepted;
                container.setItem(slot, item);
            }
        }
    } else {
        const items = storageInfo(storage).items;
        for (const [typeId, count] of Object.entries(items)) {
            if (!allows(typeId)) continue;
            const stack = new ItemStack(typeId, Math.min(64, count));
            let leftover;
            try { leftover = container.addItem(stack); } catch { continue; }
            const remaining = leftover ? leftover.amount : 0;
            const moved = Math.min(64, count) - remaining;
            if (moved > 0) takeStorage(storage, typeId, moved);
        }
    }
}

function openPort(player, block) {
    const storage = adjacentStorage(block, channelOf(block));
    const core = storage ? storageInfo(storage).core : undefined;
    if (core && !canAccessStorage(core, player)) {
        action(player, "This storage network is private.");
        return;
    }
    const native = adjacentNativeContainer(block);
    const form = new ActionFormData()
        .title("Storage Port")
        .body(`Channel: ${channelOf(block)}\nMode: ${read(block, "mode", "import")}\nStorage: ${storage ? "connected" : "missing"}\nNative inventory: ${native ? native.block.typeId.replace("minecraft:", "") : "missing"}\nFilters: ${Object.keys(beltFilters(block)).map(formatName).join(", ") || "none"}\n\nPlace a chest, barrel or hopper beside the port and a Storage Core beside it. Right-click the port with an item to toggle a filter. Use the wrench to cycle channels.`);
    form.button("Toggle import / export");
    form.button("Clear filters");
    form.button("Close");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection === 0) {
            const next = read(block, "mode", "import") === "import" ? "export" : "import";
            write(block, "mode", next);
            action(player, `Storage Port mode: ${next}.`);
        } else if (response.selection === 1) {
            writeJson(block, "filters", {});
            action(player, "Storage Port filters cleared.");
        }
    }).catch(() => {});
}

function openTerminal(player, terminal) {
    const link = readJson(terminal, "linked", null);
    if (link) ensureRemoteChunk(terminal, link);
    const storage = terminalStorage(terminal);
    if (!storage) {
        action(player, "Place the Storage Terminal beside storage, or bind a remote Storage Core with the wrench.");
        return;
    }
    const core = storageInfo(storage).core || storage;
    if (!canAccessStorage(core, player)) {
        action(player, "This storage network is private.");
        return;
    }
    void openStorage(player, storage, "", true);
}

function storageHas(core, recipe) {
    const items = storageInfo(core).items;
    for (const [typeId, count] of Object.entries(recipe.input)) {
        if (Number(items[typeId] || 0) < count) return false;
    }
    return true;
}

function openRecipeTerminal(player, core) {
    if (!canAccessStorage(core, player)) {
        action(player, "This storage network is private.");
        return;
    }
    const queue = readJson(core, "queue", []);
    const current = MACHINE_RECIPES.find((recipe) => recipe.id === queue[0]);
    const progress = Number(read(core, "queueProgress", 0));
    const currentText = current
        ? `Running: ${current.name} ${progress}/${Number(current.time || 40)}`
        : "No active job";
    const form = new ActionFormData()
        .title("Storage Terminal — Recipe Queue")
        .body(`${currentText}\nQueued jobs: ${queue.length}\nSelect a machine recipe to append it to the queue. The terminal consumes stored ingredients and returns results to storage.`);
    let index = 0;
    let cancelIndex = -1;
    let rotateIndex = -1;
    if (queue.length) {
        cancelIndex = index++;
        form.button("Cancel current job");
        rotateIndex = index++;
        form.button("Move first job to back");
    }
    const recipeStart = index;
    for (const recipe of MACHINE_RECIPES) {
        form.button(`${recipe.name} [${recipe.machine}]`);
        index++;
    }
    const clearIndex = index++;
    form.button("Clear queue");
    const backIndex = index++;
    form.button("Back");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection === cancelIndex) {
            const next = readJson(core, "queue", []);
            next.shift();
            writeJson(core, "queue", next);
            write(core, "queueProgress", 0);
            action(player, "Current job cancelled.");
            return;
        }
        if (response.selection === rotateIndex) {
            const next = readJson(core, "queue", []);
            next.push(next.shift());
            writeJson(core, "queue", next);
            write(core, "queueProgress", 0);
            action(player, "Queue rotated.");
            return;
        }
        if (response.selection === clearIndex) {
            writeJson(core, "queue", []);
            write(core, "queueProgress", 0);
            action(player, "Recipe queue cleared.");
            return;
        }
        if (response.selection === backIndex) {
            later(() => openStorage(player, core, "", true));
            return;
        }
        const recipe = MACHINE_RECIPES[response.selection - recipeStart];
        if (!recipe) return;
        const next = readJson(core, "queue", []);
        if (next.length >= 64) {
            action(player, "The recipe queue is full.");
            return;
        }
        next.push(recipe.id);
        writeJson(core, "queue", next);
        action(player, `Queued ${recipe.name}.`);
    }).catch(() => {});
}

function storageCanAccept(core, output) {
    const info = storageInfo(core);
    const units = Object.values(info.items).reduce((sum, count) => sum + Number(count || 0), 0);
    const capacity = info.capacity * 64;
    const needed = Object.values(output).reduce((sum, count) => sum + Number(count || 0), 0);
    return units + needed <= capacity;
}

function tickTerminal(terminal) {
    const link = readJson(terminal, "linked", null);
    if (link) ensureRemoteChunk(terminal, link);
    const storage = terminalStorage(terminal);
    if (!storage) return;
    const core = storageInfo(storage).core || storage;
    const key = terminalKey(terminal);
    const now = Number(system.currentTick || 0);
    const owner = String(read(core, "queueOwner", "") || "");
    const lease = Number(read(core, "queueLease", 0));
    if (owner && owner !== key && now < lease) return;
    if (!owner || owner !== key || lease < now) {
        write(core, "queueOwner", key);
        write(core, "queueLease", now + 200);
    }
    const queue = readJson(core, "queue", []);
    if (!queue.length) {
        write(core, "queueOwner", "");
        write(core, "queueLease", 0);
        return;
    }
    const recipe = MACHINE_RECIPES.find((candidate) => candidate.id === queue[0]);
    if (!recipe) {
        queue.shift();
        writeJson(core, "queue", queue);
        return;
    }
    if (!storageHas(core, recipe) || !storageCanAccept(core, recipe.output)) return;
    const progress = Number(read(core, "queueProgress", 0));
    if (progress < Number(recipe.time || 40)) {
        write(core, "queueProgress", progress + 1);
        return;
    }
    for (const [typeId, count] of Object.entries(recipe.input)) takeStorage(core, typeId, count);
    for (const [typeId, count] of Object.entries(recipe.output)) insertStorage(core, typeId, count);
    queue.shift();
    writeJson(core, "queue", queue);
    write(core, "queueProgress", 0);
    write(core, "queueLease", now + 200);
    if (!queue.length) {
        write(core, "queueOwner", "");
        write(core, "queueLease", 0);
    }
}

function insertAssembler(assembler, typeId, amount) {
    const input = readJson(assembler, "input", {});
    if (!input[typeId] && Object.keys(input).length >= 16) return 0;
    input[typeId] = Number(input[typeId] || 0) + amount;
    writeJson(assembler, "input", input);
    return amount;
}

function insertProcessor(processor, typeId, amount) {
    return insertAssembler(processor, typeId, amount);
}

function splitterOutputFilters(block) {
    return readJson(block, "outputFilters", { front: {}, left: {}, right: {} });
}

function splitterAllows(block, side, typeId) {
    const filters = splitterOutputFilters(block)[side] || {};
    return Object.keys(filters).length === 0 || filters[typeId] === true;
}

function toggleSplitterOutputFilter(block, side, typeId) {
    const filters = splitterOutputFilters(block);
    filters[side] = filters[side] || {};
    if (filters[side][typeId]) delete filters[side][typeId];
    else filters[side][typeId] = true;
    writeJson(block, "outputFilters", filters);
}

function beltFilters(block) {
    return readJson(block, "filters", {});
}

function beltAllows(block, typeId) {
    const filters = beltFilters(block);
    return Object.keys(filters).length === 0 || filters[typeId] === true;
}

function insertConveyor(conveyor, typeId, amount) {
    if (!beltAllows(conveyor, typeId)) return 0;
    const current = readJson(conveyor, "item", null);
    if (!current) {
        writeJson(conveyor, "item", { id: typeId, amount });
        return amount;
    }
    if (current.id !== typeId || current.amount >= 64) return 0;
    const accepted = Math.min(amount, 64 - current.amount);
    current.amount += accepted;
    writeJson(conveyor, "item", current);
    return accepted;
}

function insertGenerator(generator, typeId, amount) {
    const value = typeId === "minecraft:coal" ? 200
        : typeId === "minecraft:charcoal" ? 200
        : typeId === "minecraft:coal_block" ? 1800 : 0;
    if (!value) return 0;
    write(generator, "fuel", Number(read(generator, "fuel", 0)) + value * amount);
    return amount;
}

function acceptItem(block, typeId, amount, fromSide = null) {
    if (!block) return 0;
    switch (block.typeId) {
        case STORAGE_CORE:
        case STORAGE_EXTENSION:
            return insertStorage(block, typeId, amount);
        case CONVEYOR:
        case FILTER:
        case SPLITTER:
        case MERGER:
            return insertConveyor(block, typeId, amount);
        case ASSEMBLER:
            if (fromSide && !machineAcceptsFrom(block, fromSide, typeId)) return 0;
            return insertAssembler(block, typeId, amount);
        case ELECTRIC_FURNACE:
        case CRUSHER:
        case SAWMILL:
        case ALLOY_SMELTER:
            if (fromSide && !machineAcceptsFrom(block, fromSide, typeId)) return 0;
            return insertProcessor(block, typeId, amount);
        case GENERATOR:
            return insertGenerator(block, typeId, amount);
        default:
            return 0;
    }
}

function outputAdjacent(block, typeId, amount) {
    if (MACHINE_IO_TYPES.has(block.typeId) && !machineAutoOutput(block)) return 0;
    for (const side of MACHINE_SIDES) {
        if (MACHINE_IO_TYPES.has(block.typeId) && !machineOutputsTo(block, side, typeId)) continue;
        const next = neighbor(block, side);
        if (!next) continue;
        const accepted = acceptItem(next, typeId, amount, OPPOSITE[side]);
        if (accepted > 0) return accepted;
    }
    return 0;
}

function energyBlocks(start) {
    const queue = [];
    const seen = new Set();
    const result = [];
    for (const next of allNeighbors(start)) {
        if (next && ENERGY_TYPES.has(next.typeId)) queue.push(next);
    }
    while (queue.length) {
        const block = queue.shift();
        if (!block) continue;
        const key = `${block.location.x},${block.location.y},${block.location.z}`;
        if (seen.has(key)) continue;
        seen.add(key);
        if (!ENERGY_TYPES.has(block.typeId)) continue;
        result.push(block);
        for (const next of allNeighbors(block)) {
            if (next && ENERGY_TYPES.has(next.typeId)) queue.push(next);
        }
    }
    return result;
}

function networkEnergy(block) {
    let total = 0;
    for (const part of energyBlocks(block)) {
        if ([BATTERY, GENERATOR, WIND_TURBINE, SOLAR_PANEL, WATER_WHEEL, TRANSFORMER].includes(part.typeId)) {
            total += Number(read(part, "energy", 0));
        }
    }
    return Math.floor(total);
}

function drainEnergy(block, amount) {
    const sources = new Set([BATTERY, GENERATOR, WIND_TURBINE, SOLAR_PANEL, WATER_WHEEL, TRANSFORMER]);
    const parts = energyBlocks(block).filter((part) => sources.has(part.typeId));
    let total = parts.reduce((sum, part) => sum + Number(read(part, "energy", 0)), 0);
    if (total < amount) return false;
    let left = amount;
    for (const part of parts) {
        if (left <= 0) break;
        const current = Number(read(part, "energy", 0));
        const used = Math.min(current, left);
        if (used > 0) write(part, "energy", current - used);
        left -= used;
    }
    return true;
}

function tickGenerator(block) {
    let energy = Number(read(block, "energy", 0));
    let fuel = Number(read(block, "fuel", 0));
    if (fuel > 0 && energy < 2000) {
        const burn = Math.min(fuel, 10);
        fuel -= burn;
        energy = Math.min(2000, energy + burn * 10);
        write(block, "fuel", fuel);
    }
    // Push generated energy into connected batteries so a bank can buffer the
    // network between bursts of machine use.
    if (energy > 0) {
        for (const part of energyBlocks(block)) {
            if (part.typeId !== BATTERY) continue;
            const stored = Number(read(part, "energy", 0));
            if (stored >= 5000) continue;
            const moved = Math.min(energy, 5000 - stored);
            if (moved > 0) {
                write(part, "energy", stored + moved);
                energy -= moved;
                if (energy <= 0) break;
            }
        }
    }
    write(block, "energy", Math.max(0, energy));
    markStatus(block, fuel > 0 ? "working" : "idle");
}

function tickToolCharger(block) {
    markStatus(block, networkEnergy(block) > 0 ? "working" : "blocked");
}

function tickWindTurbine(block) {
    const current = Number(read(block, "energy", 0));
    const altitude = Math.max(0, Math.min(12, Math.floor((block.location.y + 64) / 32)));
    const generated = 4 + altitude;
    const budget = Math.min(2000, current + generated);
    const leftover = chargeBatteries(block, budget);
    write(block, "energy", leftover);
}

function chargeBatteries(source, budget) {
    let energy = budget;
    for (const part of energyBlocks(source)) {
        if (part.typeId !== BATTERY) continue;
        const stored = Number(read(part, "energy", 0));
        if (stored >= 5000) continue;
        const moved = Math.min(energy, 5000 - stored);
        if (moved > 0) {
            write(part, "energy", stored + moved);
            energy -= moved;
            if (energy <= 0) break;
        }
    }
    return Math.max(0, energy);
}

function tickSolarPanel(block) {
    let daylight = true;
    try {
        const time = world.getTimeOfDay() % 24000;
        daylight = time < 12000;
    } catch {
        // Keep generating if the clock is unavailable.
    }
    if (!daylight) return;
    const current = Number(read(block, "energy", 0));
    const budget = Math.min(2000, current + 7);
    write(block, "energy", chargeBatteries(block, budget));
}

function tickWaterWheel(block) {
    let water = 0;
    for (const next of allNeighbors(block)) {
        if (next && (next.typeId === "minecraft:water" || next.typeId === "minecraft:flowing_water")) water++;
    }
    if (!water) return;
    const current = Number(read(block, "energy", 0));
    const budget = Math.min(2000, current + Math.min(12, 2 + water * 2));
    write(block, "energy", chargeBatteries(block, budget));
}

function tickTransformer(block) {
    let energy = Number(read(block, "energy", 0));
    if (energy < 10000) {
        for (const next of allNeighbors(block)) {
            if (!next || ![GENERATOR, WIND_TURBINE, SOLAR_PANEL, WATER_WHEEL, BATTERY].includes(next.typeId)) continue;
            const available = Number(read(next, "energy", 0));
            if (available <= 0) continue;
            const moved = Math.min(available, 10000 - energy);
            if (moved <= 0) continue;
            write(next, "energy", available - moved);
            energy += moved;
            if (energy >= 10000) break;
        }
    }
    write(block, "energy", energy);
    markStatus(block, energy > 0 ? "working" : "idle");
}

function storageAdjacent(block) {
    for (const next of allNeighbors(block)) {
        if (next && (next.typeId === STORAGE_CORE || next.typeId === STORAGE_EXTENSION)) return next;
    }
    return undefined;
}

function pullFromStorage(extractor) {
    const source = storageAdjacent(extractor);
    if (!source) return;
    const ownPriority = Number(read(extractor, "priority", 1));
    let highest = ownPriority;
    for (const next of allNeighbors(source)) {
        if (next?.typeId === EXTRACTOR) highest = Math.max(highest, Number(read(next, "priority", 1)));
    }
    if (ownPriority < highest) return;
    const info = storageInfo(source);
    const filters = beltFilters(extractor);
    const mode = read(extractor, "filterMode", "allow");
    const hasFilter = Object.keys(filters).length > 0;
    const entry = Object.entries(info.items).find(([typeId]) => {
        if (!hasFilter) return true;
        const listed = filters[typeId] === true;
        return mode === "deny" ? !listed : listed;
    });
    if (!entry) return;
    const [typeId, count] = entry;
    const take = takeStorage(source, typeId, Math.min(64, count));
    if (take > 0) writeJson(extractor, "item", { id: typeId, amount: take });
}

function moveBeltItem(block, item, direction) {
    const next = neighbor(block, direction);
    if (!next) return 0;
    return acceptItem(next, item.id, item.amount, sideToward(next, block));
}

function tickConveyor(block) {
    if (block.typeId === CONVEYOR) updateBeltCurve(block);
    syncDisplay(block);
    if (block.typeId === EXTRACTOR) pullFromStorage(block);
    let item = readJson(block, "item", null);
    if (!item || item.amount < 1) {
        syncDisplay(block);
        return;
    }

    let accepted = 0;
    if (block.typeId === SPLITTER) {
        const order = [facing(block), LEFT_OF[facing(block)], RIGHT_OF[facing(block)]];
        const sides = ["front", "left", "right"];
        const start = Number(read(block, "splitIndex", 0)) % order.length;
        for (let step = 0; step < order.length; step++) {
            const index = (start + step) % order.length;
            if (!splitterAllows(block, sides[index], item.id)) continue;
            accepted = moveBeltItem(block, item, order[index]);
            if (accepted > 0) {
                write(block, "splitIndex", (index + 1) % order.length);
                break;
            }
        }
    } else {
        accepted = moveBeltItem(block, item, facing(block));
    }

    if (accepted >= item.amount) {
        writeJson(block, "item", null);
    } else if (accepted > 0) {
        item.amount -= accepted;
        writeJson(block, "item", item);
    }
    syncDisplay(block);
}

function hasRecipe(input, recipe) {
    for (const [typeId, count] of Object.entries(recipe.input)) {
        if (Number(input[typeId] || 0) < count) return false;
    }
    return true;
}

function consumeRecipe(input, recipe) {
    for (const [typeId, count] of Object.entries(recipe.input)) {
        input[typeId] = Number(input[typeId] || 0) - count;
        if (input[typeId] <= 0) delete input[typeId];
    }
}

function tickAssembler(block) {
    const output = readJson(block, "output", {});
    for (const [typeId, amount] of Object.entries(output)) {
        const accepted = outputAdjacent(block, typeId, amount);
        if (accepted >= amount) delete output[typeId];
        else output[typeId] = amount - accepted;
    }
    writeJson(block, "output", output);
    const input = readJson(block, "input", {});
    const selected = read(block, "recipe", "");
    const recipes = selected
        ? ASSEMBLER_RECIPES.filter((recipe) => recipe.name === selected)
        : ASSEMBLER_RECIPES;
    const recipe = recipes.find((candidate) => hasRecipe(input, candidate));
    if (!recipe) {
        markStatus(block, Object.keys(input).length ? "blocked" : "idle");
        return;
    }
    if (!drainEnergy(block, recipe.energy)) {
        markStatus(block, "blocked");
        return;
    }
    consumeRecipe(input, recipe);
    for (const [typeId, amount] of Object.entries(recipe.output)) {
        output[typeId] = Number(output[typeId] || 0) + amount;
    }
    writeJson(block, "input", input);
    writeJson(block, "output", output);
    markStatus(block, "working");
}

function tickProcessor(block) {
    const output = readJson(block, "output", {});
    for (const [typeId, amount] of Object.entries(output)) {
        const accepted = outputAdjacent(block, typeId, amount);
        if (accepted >= amount) delete output[typeId];
        else output[typeId] = amount - accepted;
    }
    writeJson(block, "output", output);
    const input = readJson(block, "input", {});
    const recipes = recipesForMachine(block.typeId);
    const selected = read(block, "recipe", "");
    const candidates = selected ? recipes.filter((recipe) => recipe.name === selected) : recipes;
    const recipe = candidates.find((candidate) => hasRecipe(input, candidate));
    if (!recipe) {
        write(block, "progress", 0);
        markStatus(block, Object.keys(input).length ? "blocked" : "idle");
        return;
    }
    const progress = Number(read(block, "progress", 0));
    const speed = Number(read(block, "speed", 0));
    const efficiency = Number(read(block, "efficiency", 0));
    const parallel = Number(read(block, "parallel", 0));
    if (progress < Number(recipe.time || 40)) {
        const cost = Math.max(0, Math.round(1 - efficiency * 0.2));
        if (cost > 0 && !drainEnergy(block, cost)) {
            markStatus(block, "blocked");
            return;
        }
        write(block, "progress", Math.min(Number(recipe.time || 40), progress + 1 + speed));
        markStatus(block, "working");
        return;
    }
    const recipeEnergy = Math.max(1, Math.round(recipe.energy * (1 - efficiency * 0.15)));
    if (!drainEnergy(block, recipeEnergy)) {
        markStatus(block, "blocked");
        return;
    }
    consumeRecipe(input, recipe);
    const copies = 1 + Math.min(3, parallel);
    for (const [typeId, amount] of Object.entries(recipe.output)) {
        output[typeId] = Number(output[typeId] || 0) + amount * copies;
    }
    write(block, "progress", 0);
    writeJson(block, "input", input);
    writeJson(block, "output", output);
    markStatus(block, "working");
}

function quarryArea(data) {
    const a = data.area;
    if (!a || !a.min || !a.max) return false;
    return true;
}

function dimensionBottom(block) {
    try {
        return Math.floor(block.dimension.heightRange.min);
    } catch {
        return -64;
    }
}

function quarryAllows(data, drop) {
    const filters = data.filters || {};
    return Object.keys(filters).length === 0 || filters[drop] === true;
}

function mineable(block) {
    const type = block.typeId;
    if (type.startsWith("cw:")) return false;
    if (type === "minecraft:bedrock" || type === "minecraft:water" || type === "minecraft:lava") return false;
    if (type.includes("air") || type.includes("portal") || type.includes("barrier")) return false;
    return true;
}

function dropFor(typeId) {
    if (DROPS[typeId]) return DROPS[typeId];
    if (typeId.endsWith("_log") || typeId.endsWith("_wood")) return typeId;
    return typeId;
}

function quarryChunkName(block) {
    return `cw_quarry_${block.location.x}_${block.location.y}_${block.location.z}`;
}

function ensureQuarryChunks(block, data) {
    if (!data.area) return;
    const name = data.chunkArea || quarryChunkName(block);
    data.chunkArea = name;
    const from = { x: data.area.min.x, y: data.area.min.y, z: data.area.min.z };
    const to = { x: data.area.max.x, y: data.area.max.y, z: data.area.max.z };
    try {
        const manager = world.tickingAreaManager;
        if (manager?.hasTickingArea(name)) return;
        if (manager && (!manager.hasCapacity || manager.hasCapacity({ dimension: block.dimension, from, to }))) {
            const pending = manager.createTickingArea(name, { dimension: block.dimension, from, to });
            if (pending?.catch) pending.catch(() => {});
            return;
        }
    } catch {
        // Fall through to the command.
    }
    try {
        block.dimension.runCommand(`tickingarea add ${from.x} ${from.y} ${from.z} ${to.x} ${to.y} ${to.z} ${name}`);
    } catch {
        // Already exists or area capacity is full.
    }
}

function releaseQuarryChunks(block, data) {
    const name = data.chunkArea || quarryChunkName(block);
    try {
        const manager = world.tickingAreaManager;
        if (manager?.hasTickingArea(name)) manager.removeTickingArea(name);
    } catch {
        // Fall through to the command.
    }
    try {
        block.dimension.runCommand(`tickingarea remove ${name}`);
    } catch {
        // It may not exist.
    }
    data.chunkArea = undefined;
}

function showQuarryMarkers(block, data) {
    if (!data.area) return;
    try {
        const y = data.area.max.y + 1;
        const map = new MolangVariableMap();
        map.setColorRGB("variable.color", { red: 0.25, green: 0.95, blue: 0.78 });
        for (const x of [data.area.min.x, data.area.max.x]) {
            for (const z of [data.area.min.z, data.area.max.z]) {
                block.dimension.spawnParticle(
                    "minecraft:colored_flame_particle",
                    { x: x + 0.5, y, z: z + 0.5 },
                    map,
                );
            }
        }
    } catch {
        // Markers are cosmetic.
    }
}

function tickQuarry(block) {
    const data = readJson(block, "data", { buffer: {} });
    data.buffer = data.buffer || {};
    if (data.area) {
        const bottom = dimensionBottom(block);
        if (data.area.min.y > bottom) {
            data.area.min.y = bottom;
            data.total = (data.area.max.x - data.area.min.x + 1)
                * (data.area.max.z - data.area.min.z + 1)
                * (data.area.max.y - data.area.min.y + 1);
        }
    }
    for (const [typeId, amount] of Object.entries(data.buffer)) {
        const accepted = outputAdjacent(block, typeId, amount);
        if (accepted >= amount) delete data.buffer[typeId];
        else data.buffer[typeId] = amount - accepted;
    }
    if (data.active && !data.chunkArea && quarryArea(data)) ensureQuarryChunks(block, data);
    if (!data.active || !quarryArea(data)) {
        markStatus(block, data.active ? "blocked" : "idle");
        if (!data.active && data.chunkArea) releaseQuarryChunks(block, data);
        writeJson(block, "data", data);
        return;
    }

    let mined = 0;
    let attempts = 0;
    let blocked = false;
    while (mined < 8 && attempts < 64) {
        attempts++;
        const cursor = data.cursor;
        if (!cursor) {
            data.active = false;
            data.complete = true;
            break;
        }
        const a = data.area;
        const x = cursor.x, y = cursor.y, z = cursor.z;
        if (y < a.min.y) {
            data.active = false;
            data.complete = true;
            data.cursor = undefined;
            break;
        }
        const target = block.dimension.getBlock({ x, y, z });
        let nextX = x + 1;
        let nextZ = z;
        if (nextX > a.max.x) {
            nextX = a.min.x;
            nextZ = z + 1;
            if (nextZ > a.max.z) {
                nextZ = a.min.z;
                data.cursor = { x: nextX, y: y - 1, z: nextZ };
            } else {
                data.cursor = { x: nextX, y, z: nextZ };
            }
        } else {
            data.cursor = { x: nextX, y, z: nextZ };
        }
        data.scanned = Number(data.scanned || 0) + 1;
        if (!target || !mineable(target)) continue;
        if (data.oreOnly && !target.typeId.includes("ore")) continue;
        if (!drainEnergy(block, 2)) {
            data.active = false;
            blocked = true;
            break;
        }
        let drop = dropFor(target.typeId);
        let amount = 1;
        if (data.silk) {
            drop = target.typeId;
        } else if (data.fortune && (target.typeId.includes("ore") || target.typeId.includes("deepslate"))) {
            amount = 1 + Math.floor(Math.random() * 3);
        }
        target.setType("minecraft:air");
        data.mined = Number(data.mined || 0) + 1;
        if (quarryAllows(data, drop)) {
            data.buffer[drop] = Number(data.buffer[drop] || 0) + amount;
        }
        mined++;
    }
    if (!data.active && data.chunkArea) releaseQuarryChunks(block, data);
    markStatus(block, blocked ? "blocked" : data.active ? "working" : "idle");
    writeJson(block, "data", data);
}

function tickMachine(block) {
    if (!block) return;
    try {
        switch (block.typeId) {
            case GENERATOR: tickGenerator(block); break;
            case TOOL_CHARGER: tickToolCharger(block); break;
            case WIND_TURBINE: tickWindTurbine(block); break;
            case SOLAR_PANEL: tickSolarPanel(block); break;
            case WATER_WHEEL: tickWaterWheel(block); break;
            case TRANSFORMER: tickTransformer(block); break;
            case CONVEYOR:
            case FILTER:
            case SPLITTER:
            case MERGER:
            case EXTRACTOR:
                tickConveyor(block);
                break;
            case ASSEMBLER: tickAssembler(block); break;
            case ELECTRIC_FURNACE:
            case CRUSHER:
            case SAWMILL:
            case ALLOY_SMELTER:
                tickProcessor(block);
                break;
            case STORAGE_PORT: tickStoragePort(block); break;
            case STORAGE_TERMINAL: tickTerminal(block); break;
            case QUARRY: tickQuarry(block); break;
        }
    } catch (error) {
        warn("machine tick failed", block.typeId, String(error));
    }
}

// Custom components are registered before world load.
system.beforeEvents.startup.subscribe((init) => {
    init.blockComponentRegistry.registerCustomComponent(MACHINE_COMPONENT, {
        onTick: (event) => tickMachine(event.block),
    });
});

function setQuarryArea(player, quarry, a, b) {
    const minX = Math.min(a.x, b.x);
    const maxX = Math.max(a.x, b.x);
    const minZ = Math.min(a.z, b.z);
    const maxZ = Math.max(a.z, b.z);
    const minY = dimensionBottom(quarry);
    let maxY;
    try {
        maxY = Math.min(quarry.dimension.heightRange.max, Math.max(a.y, b.y));
    } catch {
        maxY = Math.max(a.y, b.y);
    }
    if (maxX - minX > 31 || maxZ - minZ > 31) {
        action(player, "The quarry footprint is too large (max 32x32).");
        return;
    }
    if (maxY < minY) {
        action(player, "The quarry corners are below this dimension's floor.");
        return;
    }
    const min = { x: minX, y: minY, z: minZ };
    const max = { x: maxX, y: maxY, z: maxZ };
    const data = readJson(quarry, "data", { buffer: {} });
    if (data.chunkArea) releaseQuarryChunks(quarry, data);
    data.area = { min, max };
    data.cursor = { x: min.x, y: max.y, z: min.z };
    data.active = false;
    data.complete = false;
    data.scanned = 0;
    data.mined = 0;
    data.total = (maxX - minX + 1) * (maxZ - minZ + 1) * (maxY - minY + 1);
    data.filters = data.filters || {};
    data.fortune = Boolean(data.fortune);
    data.silk = Boolean(data.silk);
    data.oreOnly = Boolean(data.oreOnly);
    data.buffer = data.buffer || {};
    writeJson(quarry, "data", data);
    action(player, `Quarry area set (${maxX - minX + 1}x${maxZ - minZ + 1}, to bedrock). Connect storage and power.`);
}

function surveyorUse(player, block) {
    if (block.typeId === QUARRY) {
        const a = player.getDynamicProperty("cw:corner_a");
        const b = player.getDynamicProperty("cw:corner_b");
        if (typeof a !== "string" || typeof b !== "string") {
            action(player, "Use the Quarry Surveyor on two corners first.");
            return;
        }
        try {
            setQuarryArea(player, block, JSON.parse(a), JSON.parse(b));
            player.setDynamicProperty("cw:corner_a", undefined);
            player.setDynamicProperty("cw:corner_b", undefined);
        } catch {
            action(player, "The survey corners are invalid.");
        }
        return;
    }
    const point = JSON.stringify({
        x: block.location.x,
        y: block.location.y,
        z: block.location.z,
    });
    if (player.getDynamicProperty("cw:corner_a") === undefined) {
        player.setDynamicProperty("cw:corner_a", point);
        action(player, "Quarry corner A set. Use the surveyor on a second corner.");
    } else {
        player.setDynamicProperty("cw:corner_b", point);
        action(player, "Quarry corner B set. Use the surveyor on the Quarry Controller.");
    }
}

function isDrillBlock(block) {
    const type = block?.typeId || "";
    return type.includes("stone") || type.includes("ore") || type.includes("deepslate")
        || ["minecraft:andesite", "minecraft:diorite", "minecraft:granite", "minecraft:calcite",
            "minecraft:tuff", "minecraft:netherrack", "minecraft:end_stone"].includes(type);
}

function drill(player, block, face, mode = 1) {
    const normal = DIRECTIONS[String(face).toLowerCase()] || DIRECTIONS.up;
    const targets = [];
    for (let a = -1; a <= 1; a++) {
        for (let b = -1; b <= 1; b++) {
            let dx = 0, dy = 0, dz = 0;
            if (normal.x) {
                dy = a;
                dz = b;
            } else if (normal.y) {
                dx = a;
                dz = b;
            } else {
                dx = a;
                dy = b;
            }
            targets.push({
                x: block.location.x + dx,
                y: block.location.y + dy,
                z: block.location.z + dz,
            });
        }
    }
    const plane = targets;
    const volume = [];
    for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
            for (let dz = -1; dz <= 1; dz++) {
                volume.push({
                    x: block.location.x + dx,
                    y: block.location.y + dy,
                    z: block.location.z + dz,
                });
            }
        }
    }
    const selected = mode === 0 ? [block.location] : mode === 2 ? volume : plane;
    let mined = 0;
    for (const pos of selected) {
        const target = block.dimension.getBlock(pos);
        if (!target || !isDrillBlock(target)) continue;
        const drop = dropFor(target.typeId);
        target.setType("minecraft:air");
        addItem(player, drop, 1);
        mined++;
    }
    if (!mined) action(player, "The drill needs stone or ore.");
    return mined > 0;
}

function chainsaw(player, block) {
    if (!block.typeId.endsWith("_log") && !block.typeId.endsWith("_wood")) {
        action(player, "The chainsaw needs logs.");
        return false;
    }
    let mined = 0;
    const queue = [block];
    const seen = new Set();
    while (queue.length && mined < 64) {
        const cursor = queue.shift();
        if (!cursor) continue;
        const key = `${cursor.location.x},${cursor.location.y},${cursor.location.z}`;
        if (seen.has(key)) continue;
        seen.add(key);
        if (!cursor.typeId.endsWith("_log") && !cursor.typeId.endsWith("_wood")) continue;
        const drop = dropFor(cursor.typeId);
        cursor.setType("minecraft:air");
        addItem(player, drop, 1);
        mined++;
        for (const next of allNeighbors(cursor)) {
            if (next && (next.typeId.endsWith("_log") || next.typeId.endsWith("_wood"))) queue.push(next);
        }
    }
    action(player, `Chainsaw cut ${mined} log${mined === 1 ? "" : "s"}.`);
    return mined > 0;
}

function copyBlueprint(player, block) {
    const keys = ["recipe", "filters", "outputFilters", "priority", "filterMode", "mode", "speed", "efficiency", "parallel"];
    const dataKeys = ["filters", "fortune", "silk", "oreOnly"];
    const values = {};
    for (const key of keys) {
        const value = read(block, key, undefined);
        if (value !== undefined) values[key] = value;
    }
    const data = readJson(block, "data", null);
    const nested = {};
    if (data) {
        for (const key of dataKeys) {
            if (data[key] !== undefined) nested[key] = data[key];
        }
    }
    player.setDynamicProperty("cw:blueprint", JSON.stringify({
        typeId: block.typeId,
        channel: channelOf(block),
        values,
        data: nested,
    }));
    action(player, `Blueprint copied from ${formatName(block.typeId)}.`);
}

function applyBlueprint(player, block) {
    const raw = player.getDynamicProperty("cw:blueprint");
    if (typeof raw !== "string") return false;
    let blueprint;
    try { blueprint = JSON.parse(raw); } catch { return false; }
    if (!blueprint || blueprint.typeId !== block.typeId) {
        action(player, "The blueprint is for a different machine.");
        return true;
    }
    for (const [key, value] of Object.entries(blueprint.values || {})) {
        write(block, key, value);
    }
    if (blueprint.channel) {
        try {
            const current = block.permutation.getState("cw:channel");
            if (typeof current === "string") {
                block.setPermutation(BlockPermutation.resolve(block.typeId, { "cw:channel": blueprint.channel }));
            }
        } catch {
            // The destination may not have channels.
        }
    }
    if (blueprint.data && Object.keys(blueprint.data).length) {
        const data = readJson(block, "data", {});
        Object.assign(data, blueprint.data);
        writeJson(block, "data", data);
    }
    action(player, `Blueprint applied to ${formatName(block.typeId)}.`);
    return true;
}

function rotateConveyor(block) {
    const current = facing(block);
    const next = FACINGS[(FACINGS.indexOf(current) + 1) % FACINGS.length];
    setFacing(block, next);
    updateBeltCurve(block);
    updateNeighborCurves(block);
    return next;
}

function openRecipePicker(player, block) {
    const form = new ActionFormData()
        .title("Assembler Recipe")
        .body("Choose a fixed recipe, or let the assembler use the first available recipe.");
    form.button("Auto — first available");
    for (const recipe of ASSEMBLER_RECIPES) form.button(recipe.name);
    form.button("Cancel");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection === 0) {
            write(block, "recipe", "");
            action(player, "Assembler set to automatic recipe.");
            return;
        }
        const recipe = ASSEMBLER_RECIPES[response.selection - 1];
        if (!recipe) return;
        write(block, "recipe", recipe.name);
        action(player, `Assembler recipe: ${recipe.name}.`);
    }).catch(() => {});
}

function openLogistics(player, block) {
    const item = readJson(block, "item", null);
    const filters = Object.keys(beltFilters(block));
    const isSplitter = block.typeId === SPLITTER;
    const isExtractor = block.typeId === EXTRACTOR;
    const outputs = isSplitter ? splitterOutputFilters(block) : null;
    const outputText = isSplitter
        ? `\nFront: ${Object.keys(outputs.front || {}).map(formatName).join(", ") || "all"}\nLeft: ${Object.keys(outputs.left || {}).map(formatName).join(", ") || "all"}\nRight: ${Object.keys(outputs.right || {}).map(formatName).join(", ") || "all"}`
        : "";
    const extractorText = isExtractor
        ? `\nPriority: ${Number(read(block, "priority", 1))}\nFilter mode: ${read(block, "filterMode", "allow")}`
        : "";
    const form = new ActionFormData()
        .title(formatName(block.typeId))
        .body(`Facing: ${facing(block)}\nBuffer: ${item ? `${formatName(item.id)} x${item.amount}` : "empty"}\nFilters: ${filters.length ? filters.map(formatName).join(", ") : "none (pass all)"}${outputText}${extractorText}\n\nRight-click a belt with an item to toggle its input filter. On a splitter, click an output side to filter that side. Use the wrench to rotate.`);
    form.button("Clear input filters");
    if (isSplitter) form.button("Clear output filters");
    if (isExtractor) {
        form.button("Cycle priority");
        form.button("Toggle filter mode");
    }
    form.button("Close");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection === 0) {
            writeJson(block, "filters", {});
            action(player, "Input filters cleared.");
            return;
        }
        if (isSplitter && response.selection === 1) {
            writeJson(block, "outputFilters", { front: {}, left: {}, right: {} });
            action(player, "Splitter output filters cleared.");
            return;
        }
        if (isExtractor) {
            if (response.selection === 1) {
                const next = (Number(read(block, "priority", 1)) + 1) % 3;
                write(block, "priority", next);
                action(player, `Extractor priority: ${next}.`);
            } else if (response.selection === 2) {
                const next = read(block, "filterMode", "allow") === "allow" ? "deny" : "allow";
                write(block, "filterMode", next);
                action(player, `Extractor filter mode: ${next}.`);
            }
        }
    }).catch(() => {});
}

function splitterSideForFace(block, face) {
    const direction = String(face || "").toLowerCase();
    if (direction === facing(block)) return "front";
    if (direction === LEFT_OF[facing(block)]) return "left";
    if (direction === RIGHT_OF[facing(block)]) return "right";
    return "input";
}


function toggleBeltFilter(player, block, typeId) {
    const filters = beltFilters(block);
    if (filters[typeId]) {
        delete filters[typeId];
        action(player, `Removed filter: ${formatName(typeId)}.`);
    } else {
        filters[typeId] = true;
        action(player, `Added filter: ${formatName(typeId)}.`);
    }
    writeJson(block, "filters", filters);
}

function toggleQuarryFilter(player, block, typeId) {
    const data = readJson(block, "data", {});
    data.filters = data.filters || {};
    if (data.filters[typeId]) {
        delete data.filters[typeId];
        action(player, `Removed quarry filter: ${formatName(typeId)}.`);
    } else {
        data.filters[typeId] = true;
        action(player, `Added quarry filter: ${formatName(typeId)}.`);
    }
    writeJson(block, "data", data);
}

function openSideConfig(player, block) {
    const io = machineIo(block);
    const filters = machineSideFilters(block);
    const lines = MACHINE_SIDES.map((side) => {
        const count = Object.keys(filters[side] || {}).length;
        return `${side.toUpperCase()}: ${io[side]}${count ? ` (${count} filter${count === 1 ? "" : "s"})` : ""}`;
    });
    const form = new ActionFormData()
        .title(`Machine I/O — ${formatName(block.typeId)}`)
        .body(`${lines.join("\n")}\n\nClick a side to cycle: both → input → output → disabled.\nSneak-use the machine with an item on a side to toggle that side's item filter.\nAuto-output pushes finished items to adjacent machines, belts and storage.`)
    for (const side of MACHINE_SIDES) {
        const count = Object.keys(filters[side] || {}).length;
        form.button(`${side.toUpperCase()} — ${io[side]}${count ? ` (${count})` : ""}`);
    }
    form.button(`Auto-output: ${machineAutoOutput(block) ? "on" : "off"}`);
    form.button("Clear side filters");
    form.button("Back");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection < MACHINE_SIDES.length) {
            const side = MACHINE_SIDES[response.selection];
            const next = cycleMachineSide(block, side);
            action(player, `${side.toUpperCase()} side: ${next}.`);
            return;
        }
        if (response.selection === MACHINE_SIDES.length) {
            write(block, "autoOutput", !machineAutoOutput(block));
            action(player, `Auto-output: ${machineAutoOutput(block) ? "on" : "off"}.`);
            return;
        }
        if (response.selection === MACHINE_SIDES.length + 1) {
            writeJson(block, "sideFilters", {});
            action(player, "Machine side filters cleared.");
            return;
        }
        later(() => openMachine(player, block));
    }).catch(() => {});
}

function openProcessor(player, block) {
    const input = readJson(block, "input", {});
    const output = readJson(block, "output", {});
    const recipes = recipesForMachine(block.typeId);
    const lines = recipes.map((recipe) => `${recipe.name} (${recipe.energy} E, ${recipe.time} ticks)`);
    const speed = Number(read(block, "speed", 0));
    const efficiency = Number(read(block, "efficiency", 0));
    const parallel = Number(read(block, "parallel", 0));
    const form = new ActionFormData()
        .title(formatName(block.typeId))
        .body(`Status: ${read(block, "status", "idle")}\nProgress: ${Number(read(block, "progress", 0))}\nModules: Speed ${speed}/3, Efficiency ${efficiency}/3, Parallel ${parallel}/3\nInput: ${Object.entries(input).map(([id, n]) => `${formatName(id)} x${n}`).join(", ") || "empty"}\nOutput: ${Object.entries(output).map(([id, n]) => `${formatName(id)} x${n}`).join(", ") || "empty"}\nEnergy: ${networkEnergy(block)}\n\nRecipes:\n${lines.join("\n")}`)
        .button(`Speed +1 (2 gears)`)
        .button(`Efficiency +1 (2 circuits)`)
        .button(`Parallel +1 (1 motor)`)
        .button("Side configuration")
        .button("Close");
    form.show(player).then((response) => {
        if (!response || response.canceled) return;
        if (response.selection === 0) upgradeProcessor(player, block, "speed");
        else if (response.selection === 1) upgradeProcessor(player, block, "efficiency");
        else if (response.selection === 2) upgradeProcessor(player, block, "parallel");
        else if (response.selection === 3) later(() => openSideConfig(player, block));
    }).catch(() => {});
}

function openMachine(player, block) {
    if (block.typeId === STORAGE_CORE || block.typeId === STORAGE_EXTENSION) {
        void openStorage(player, block);
        return;
    }
    if (block.typeId === STORAGE_TERMINAL) {
        openTerminal(player, block);
        return;
    }
    if (block.typeId === WIND_TURBINE || block.typeId === SOLAR_PANEL || block.typeId === WATER_WHEEL) {
        const energy = Number(read(block, "energy", 0));
        const form = new ActionFormData().title(formatName(block.typeId))
            .body(`Energy: ${Math.floor(energy)}/2000\nNetwork: ${networkEnergy(block)}\nHeight: Y ${block.location.y}`);
        form.button("Close");
        form.show(player).catch(() => {});
        return;
    }
    if (block.typeId === TRANSFORMER) {
        const energy = Number(read(block, "energy", 0));
        const form = new ActionFormData().title("Power Transformer")
            .body(`Buffered energy: ${Math.floor(energy)}/10,000\nNetwork: ${networkEnergy(block)}\n\nPulls adjacent generation/battery energy into its high-capacity buffer.`);
        form.button("Close");
        form.show(player).catch(() => {});
        return;
    }
    if (block.typeId === ENERGY_METER) {
        const form = new ActionFormData().title("Energy Meter")
            .body(`Network energy: ${networkEnergy(block)}\n\nConnect the meter to the same cable network as generators, batteries and machines.`);
        form.button("Close");
        form.show(player).catch(() => {});
        return;
    }
    if (PROCESSOR_TYPES.has(block.typeId)) {
        openProcessor(player, block);
        return;
    }
    if (block.typeId === STORAGE_PORT) {
        openPort(player, block);
        return;
    }
    if (BELT_TYPES.has(block.typeId)) {
        openLogistics(player, block);
        return;
    }
    if (block.typeId === GENERATOR) {
        const fuel = Number(read(block, "fuel", 0));
        const energy = Number(read(block, "energy", 0));
        const form = new ActionFormData().title("Coal Generator")
            .body(`Status: ${read(block, "status", "idle")}\nFuel: ${Math.floor(fuel)}\nEnergy: ${Math.floor(energy)}/2000\nNetwork: ${networkEnergy(block)}`);
        form.button("Close");
        void form.show(player).catch(() => {});
        return;
    }
    if (block.typeId === TOOL_CHARGER) {
        const item = heldItem(player);
        const charge = item && BATTERY_TOOLS.has(item.typeId) ? batteryCharge(item) : null;
        const form = new ActionFormData().title("Tool Charger")
            .body(`Network energy: ${networkEnergy(block)}\nHeld battery tool: ${charge === null ? "none" : `${charge}/${BATTERY_TOOL_MAX}`}\n\nHold a Battery Drill or Battery Chainsaw and use the charger, or press Charge held tool.`)
            .button("Charge held tool")
            .button("Close");
        form.show(player).then((response) => {
            if (!response || response.canceled) return;
            if (response.selection === 0) {
                const tool = heldItem(player);
                if (!tool || !BATTERY_TOOLS.has(tool.typeId)) {
                    action(player, "Hold a Battery Drill or Battery Chainsaw first.");
                    return;
                }
                rechargeBatteryTool(player, block, tool);
            }
        }).catch(() => {});
        return;
    }
    if (block.typeId === BATTERY) {
        const energy = Number(read(block, "energy", 0));
        const form = new ActionFormData().title("Battery Bank")
            .body(`Energy: ${Math.floor(energy)}/5000\nNetwork: ${networkEnergy(block)}`);
        form.button("Close");
        void form.show(player).catch(() => {});
        return;
    }
    if (block.typeId === ASSEMBLER) {
        const input = readJson(block, "input", {});
        const output = readJson(block, "output", {});
        const selected = read(block, "recipe", "");
        const form = new ActionFormData().title("Crafting Assembler")
            .body(`Status: ${read(block, "status", "idle")}\nRecipe: ${selected || "Auto — first available"}\nInput: ${Object.entries(input).map(([id, n]) => `${formatName(id)} x${n}`).join(", ") || "empty"}\nOutput: ${Object.entries(output).map(([id, n]) => `${formatName(id)} x${n}`).join(", ") || "empty"}\nEnergy: ${networkEnergy(block)}`)
            .button("Select recipe")
            .button("Use automatic recipe")
            .button("Side configuration")
            .button("Close");
        form.show(player).then((response) => {
            if (!response || response.canceled) return;
            if (response.selection === 0) {
                later(() => openRecipePicker(player, block));
            } else if (response.selection === 1) {
                write(block, "recipe", "");
                action(player, "Assembler set to automatic recipe.");
            } else if (response.selection === 2) {
                later(() => openSideConfig(player, block));
            }
        }).catch(() => {});
        return;
    }
    if (block.typeId === QUARRY) {
        const data = readJson(block, "data", {});
        const area = data.area
            ? `${data.area.min.x},${data.area.min.y},${data.area.min.z} -> ${data.area.max.x},${data.area.max.y},${data.area.max.z}`
            : "not set";
        const total = Math.max(1, Number(data.total || 0));
        const scanned = Number(data.scanned || 0);
        const percent = Math.min(100, Math.floor(scanned / total * 100));
        const filters = Object.keys(data.filters || {});
        const form = new ActionFormData().title("Quarry Controller")
            .body(`Status: ${data.complete ? "complete" : data.active ? "active" : "paused"}${read(block, "status", "") ? ` (${read(block, "status", "")})` : ""}\nProgress: ${percent}% (${scanned}/${total})\nMined: ${Number(data.mined || 0)}\nArea: ${area}\nBottom: bedrock (${data.area ? data.area.min.y : dimensionBottom(block)})\nFilters: ${filters.length ? filters.map(formatName).join(", ") : "none (collect all drops)"}\nFortune: ${data.fortune ? "on" : "off"}\nSilk Touch: ${data.silk ? "on" : "off"}\nOres only: ${data.oreOnly ? "on" : "off"}\nChunk loading: ${data.chunkArea ? "active" : "off"}\nBuffer: ${Object.values(data.buffer || {}).reduce((a, b) => a + b, 0)} items\nEnergy: ${networkEnergy(block)}`)
            .button(data.active ? "Pause quarry" : "Start quarry")
            .button("Clear output filters")
            .button("Toggle fortune")
            .button("Toggle silk touch")
            .button("Toggle ores only")
            .button("Close");
        form.show(player).then((response) => {
            if (!response || response.canceled) return;
            if (response.selection === 1) {
                data.filters = {};
                writeJson(block, "data", data);
                action(player, "Quarry output filters cleared.");
                return;
            }
            if (response.selection === 2) {
                data.fortune = !data.fortune;
                writeJson(block, "data", data);
                action(player, `Quarry fortune: ${data.fortune ? "on" : "off"}.`);
                return;
            }
            if (response.selection === 3) {
                data.silk = !data.silk;
                writeJson(block, "data", data);
                action(player, `Quarry silk touch: ${data.silk ? "on" : "off"}.`);
                return;
            }
            if (response.selection === 4) {
                data.oreOnly = !data.oreOnly;
                writeJson(block, "data", data);
                action(player, `Quarry ores only: ${data.oreOnly ? "on" : "off"}.`);
                return;
            }
            if (response.selection !== 0) return;
            if (!quarryArea(data)) {
                action(player, "Use the Quarry Surveyor on two corners first.");
                return;
            }
            if (data.complete) {
                action(player, "This quarry area is complete. Survey a new area.");
                return;
            }
            data.active = !data.active;
            if (data.active) {
                ensureQuarryChunks(block, data);
                showQuarryMarkers(block, data);
            } else releaseQuarryChunks(block, data);
            writeJson(block, "data", data);
            action(player, data.active ? "Quarry started." : "Quarry paused.");
        }).catch(() => {});
    }
}

function interact(event) {
    if (event.isFirstEvent === false) return;
    const player = event.player;
    const block = event.block;
    const item = event.itemStack;
    if (!player || !block) return;

    if (item?.typeId === WRENCH && [STORAGE_CORE, STORAGE_EXTENSION].includes(block.typeId)) {
        if (player.isSneaking) {
            copyStorageLink(player, block);
        } else {
            const channel = cycleStorageChannel(block);
            action(player, `Storage channel: ${channel}.`);
        }
        return;
    }
    if (item?.typeId === WRENCH && block.typeId === STORAGE_PORT) {
        const channel = cycleStorageChannel(block);
        action(player, `Storage channel: ${channel}.`);
        return;
    }
    if (item?.typeId === WRENCH && block.typeId === STORAGE_TERMINAL) {
        if (player.isSneaking) {
            releaseRemoteChunk(block);
            writeJson(block, "linked", null);
            action(player, "Storage Terminal remote link cleared.");
        } else if (!applyStorageLink(player, block)) {
            action(player, "Sneak-use the wrench on a Storage Core to copy a remote link.");
        }
        return;
    }
    if (item?.typeId === WRENCH) {
        if (player.isSneaking) {
            copyBlueprint(player, block);
            return;
        }
        if (!BELT_TYPES.has(block.typeId)) {
            if (!applyBlueprint(player, block)) action(player, "Sneak-use the wrench on a machine to copy its settings.");
            return;
        }
    }
    if (item?.typeId === WRENCH && BELT_TYPES.has(block.typeId)) {
        const direction = rotateConveyor(block);
        damageHeld(player, item);
        action(player, `Conveyor direction: ${direction}`);
        return;
    }
    if (item?.typeId === SURVEYOR) {
        surveyorUse(player, block);
        return;
    }
    if (block.typeId === BATTERY && item && BATTERY_TOOLS.has(item.typeId)) {
        rechargeBatteryTool(player, block, item);
        return;
    }
    if (block.typeId === TOOL_CHARGER && item && BATTERY_TOOLS.has(item.typeId)) {
        rechargeBatteryTool(player, block, item);
        return;
    }
    if (item?.typeId === BATTERY_DRILL || item?.typeId === BATTERY_CHAINSAW) {
        const isDrill = item.typeId === BATTERY_DRILL;
        if (isDrill && player.isSneaking) {
            const next = (Number(player.getDynamicProperty("cw:drill_mode") ?? 1) + 1) % DRILL_MODES.length;
            player.setDynamicProperty("cw:drill_mode", next);
            action(player, `Drill mode: ${DRILL_MODES[next]}.`);
            return;
        }
        const mode = Number(player.getDynamicProperty("cw:drill_mode") ?? 1);
        const worked = isDrill
            ? drill(player, block, event.blockFace, mode)
            : chainsaw(player, block);
        if (worked) consumeBatteryTool(player, item);
        return;
    }
    if (item?.typeId === DRILL) {
        if (player.isSneaking) {
            const next = (Number(player.getDynamicProperty("cw:drill_mode") ?? 1) + 1) % DRILL_MODES.length;
            player.setDynamicProperty("cw:drill_mode", next);
            action(player, `Drill mode: ${DRILL_MODES[next]}.`);
            return;
        }
        const mode = Number(player.getDynamicProperty("cw:drill_mode") ?? 1);
        if (drill(player, block, event.blockFace, mode)) damageHeld(player, item);
        return;
    }
    if (item?.typeId === CHAINSAW) {
        if (chainsaw(player, block)) damageHeld(player, item);
        return;
    }

    if (block.typeId === QUARRY) {
        if (item) {
            toggleQuarryFilter(player, block, item.typeId);
        } else {
            later(() => openMachine(player, block));
        }
        return;
    }
    if (BELT_TYPES.has(block.typeId)) {
        if (item) {
            if (block.typeId === SPLITTER) {
                const side = splitterSideForFace(block, event.blockFace);
                if (side === "input") {
                    toggleBeltFilter(player, block, item.typeId);
                } else {
                    toggleSplitterOutputFilter(block, side, item.typeId);
                    action(player, `Splitter ${side} filter: ${formatName(item.typeId)}.`);
                }
            } else {
                toggleBeltFilter(player, block, item.typeId);
            }
        } else {
            later(() => openMachine(player, block));
        }
        return;
    }

    if (PROCESSOR_TYPES.has(block.typeId)) {
        if (item) {
            const side = String(event.blockFace || "north").toLowerCase();
            if (player.isSneaking) {
                toggleMachineSideFilter(block, side, item.typeId);
                action(player, `Machine ${side} filter: ${formatName(item.typeId)}.`);
                return;
            }
            if (!machineAcceptsFrom(block, side, item.typeId)) {
                action(player, `The ${side} side is not an input.`);
                return;
            }
            const accepted = insertProcessor(block, item.typeId, item.amount);
            if (accepted > 0) {
                takeHeld(player, item.typeId, accepted);
                action(player, `Inserted ${accepted} ${formatName(item.typeId)}.`);
            } else {
                action(player, "The machine input is full.");
            }
        } else {
            later(() => openMachine(player, block));
        }
        return;
    }

    if (block.typeId === STORAGE_TERMINAL) {
        later(() => openTerminal(player, block));
        return;
    }
    if (block.typeId === WIND_TURBINE || block.typeId === SOLAR_PANEL || block.typeId === WATER_WHEEL || block.typeId === TRANSFORMER || block.typeId === ENERGY_METER) {
        later(() => openMachine(player, block));
        return;
    }
    if (block.typeId === STORAGE_PORT) {
        if (item) toggleBeltFilter(player, block, item.typeId);
        else later(() => openMachine(player, block));
        return;
    }

    if (block.typeId === STORAGE_CORE || block.typeId === STORAGE_EXTENSION) {
        const core = storageInfo(block).core;
        if (!canAccessStorage(core, player)) {
            action(player, "This storage network is private.");
            return;
        }
        if (item) {
            const accepted = insertStorage(block, item.typeId, item.amount);
            if (accepted > 0) {
                takeHeld(player, item.typeId, accepted);
                action(player, `Deposited ${accepted} ${formatName(item.typeId)}.`);
            } else {
                action(player, "Storage is full.");
            }
        } else {
            later(() => openStorage(player, block));
        }
        return;
    }
    if (block.typeId === GENERATOR) {
        if (item) {
            const accepted = insertGenerator(block, item.typeId, item.amount);
            if (accepted > 0) {
                takeHeld(player, item.typeId, accepted);
                action(player, "Fuel added.");
            } else {
                action(player, "The generator only accepts coal, charcoal or coal blocks.");
            }
        } else {
            later(() => openMachine(player, block));
        }
        return;
    }
    if (block.typeId === ASSEMBLER) {
        if (item) {
            const side = String(event.blockFace || "north").toLowerCase();
            if (player.isSneaking) {
                toggleMachineSideFilter(block, side, item.typeId);
                action(player, `Machine ${side} filter: ${formatName(item.typeId)}.`);
                return;
            }
            if (!machineAcceptsFrom(block, side, item.typeId)) {
                action(player, `The ${side} side is not an input.`);
                return;
            }
            const accepted = insertAssembler(block, item.typeId, item.amount);
            if (accepted > 0) {
                takeHeld(player, item.typeId, accepted);
                action(player, `Inserted ${accepted} ${formatName(item.typeId)}.`);
            } else {
                action(player, "The assembler input is full.");
            }
        } else {
            later(() => openMachine(player, block));
        }
        return;
    }
    if (block.typeId === BATTERY) {
        later(() => openMachine(player, block));
    }
    if (block.typeId === TOOL_CHARGER) {
        if (item) action(player, "The Tool Charger accepts Battery Drill and Battery Chainsaw.");
        else later(() => openMachine(player, block));
    }
}

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
    try { interact(event); } catch (error) { warn("interaction failed", String(error)); }
});

world.afterEvents.playerPlaceBlock.subscribe((event) => {
    try {
        if (!BELT_TYPES.has(event.block.typeId)) return;
        const yaw = event.player.getRotation().y;
        const index = Math.round(((yaw % 360) + 360) % 360 / 90) % 4;
        setFacing(event.block, ["south", "west", "north", "east"][index]);
        autoConnectNeighbors(event.block);
        updateBeltCurve(event.block);
        updateNeighborCurves(event.block);
    } catch {
        // Ignore placement orientation failures.
    }
});

world.beforeEvents.playerBreakBlock?.subscribe((event) => {
    try {
        if (BELT_TYPES.has(event.block.typeId)) {
            const id = read(event.block, "displayId", undefined);
            if (typeof id === "string") {
                system.run(() => {
                    try { world.getEntity(id)?.remove(); } catch { /* already gone */ }
                });
            }
        }
        if (event.block.typeId === QUARRY) {
            const data = readJson(event.block, "data", {});
            if (data.chunkArea) releaseQuarryChunks(event.block, data);
        }
        if (event.block.typeId === STORAGE_TERMINAL) {
            releaseRemoteChunk(event.block);
            const storage = terminalStorage(event.block);
            const core = storage ? (storageInfo(storage).core || storage) : undefined;
            if (core && read(core, "queueOwner", "") === terminalKey(event.block)) {
                write(core, "queueOwner", "");
                write(core, "queueLease", 0);
            }
        }
    } catch {
        // Ignore.
    }
});

world.afterEvents.playerBreakBlock.subscribe((event) => {
    try {
        if (event.block.typeId === BATTERY) {
            const energy = Number(read(event.block, "energy", 0));
            if (energy > 0) event.player.sendMessage(`Battery removed with ${Math.floor(energy)} energy.`);
        }
        updateNeighborCurves(event.block);
    } catch {
        // Ignore.
    }
});

world.afterEvents.worldLoad.subscribe(() => {
    warn("Cogworks loaded");
});
