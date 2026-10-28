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
} from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

const NS = "cw:";
const GENERATOR = "cw:generator";
const CABLE = "cw:cable";
const BATTERY = "cw:battery";
const CONVEYOR = "cw:conveyor";
const ASSEMBLER = "cw:assembler";
const STORAGE_CORE = "cw:storage_core";
const STORAGE_EXTENSION = "cw:storage_extension";
const QUARRY = "cw:quarry";
const DRILL = "cw:drill";
const CHAINSAW = "cw:chainsaw";
const WRENCH = "cw:wrench";
const SURVEYOR = "cw:surveyor";
const MACHINE_COMPONENT = "cw:machine";

const ENERGY_TYPES = new Set([GENERATOR, CABLE, BATTERY]);
const FACINGS = ["north", "east", "south", "west"];
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

const ASSEMBLER_RECIPES = [
    { name: "Oak Planks", input: { "minecraft:oak_log": 1 }, output: { "minecraft:oak_planks": 4 }, energy: 20 },
    { name: "Sticks", input: { "minecraft:oak_planks": 2 }, output: { "minecraft:stick": 4 }, energy: 10 },
    { name: "Iron Ingots", input: { "minecraft:raw_iron": 1, "minecraft:coal": 1 }, output: { "minecraft:iron_ingot": 2 }, energy: 35 },
    { name: "Gold Ingots", input: { "minecraft:raw_gold": 1, "minecraft:coal": 1 }, output: { "minecraft:gold_ingot": 2 }, energy: 35 },
    { name: "Copper Ingots", input: { "minecraft:raw_copper": 1 }, output: { "minecraft:copper_ingot": 2 }, energy: 20 },
    { name: "Cogwork Gear", input: { "minecraft:iron_ingot": 4 }, output: { "cw:gear": 1 }, energy: 25 },
    { name: "Control Circuit", input: { "minecraft:redstone": 4, "minecraft:gold_ingot": 1 }, output: { "cw:circuit": 1 }, energy: 30 },
    { name: "Electric Motor", input: { "cw:gear": 2, "cw:circuit": 1, "minecraft:copper_ingot": 4 }, output: { "cw:motor": 1 }, energy: 50 },
];

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
        block.setPermutation(BlockPermutation.resolve(CONVEYOR, { "cw:facing": value }));
    } catch {
        // It may be a removed block during a tick.
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
    while (queue.length) {
        const block = queue.shift();
        if (!block) continue;
        const key = `${block.location.x},${block.location.y},${block.location.z}`;
        if (seen.has(key)) continue;
        seen.add(key);
        if (block.typeId !== STORAGE_CORE && block.typeId !== STORAGE_EXTENSION) continue;
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

async function openStorage(player, block) {
    const info = storageInfo(block);
    if (!info.core) {
        player.sendMessage("Connect a Storage Extension to a Storage Core first.");
        return;
    }
    const entries = Object.entries(info.items).sort(([a], [b]) => a.localeCompare(b));
    const used = Object.values(info.items).reduce((sum, count) => sum + Math.ceil(Number(count || 0) / 64), 0);
    const form = new ActionFormData()
        .title("Storage Core")
        .body(`Capacity: ${used}/${info.capacity} slots\nConnected blocks: ${info.capacity / 8}\nEnergy: ${networkEnergy(block)}`);
    form.button("Deposit held item");
    for (const [typeId, count] of entries) {
        form.button(`${formatName(typeId)}  x${count}`);
    }
    let response;
    try { response = await form.show(player); } catch { return; }
    if (response.canceled) return;
    if (response.selection === 0) {
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
    const [typeId, count] = entries[response.selection - 1] || [];
    if (!typeId) return;
    const take = Math.min(64, count);
    const taken = takeStorage(block, typeId, take);
    addItem(player, typeId, taken);
    action(player, `Withdrew ${taken} ${formatName(typeId)}.`);
}

function insertAssembler(assembler, typeId, amount) {
    const input = readJson(assembler, "input", {});
    if (!input[typeId] && Object.keys(input).length >= 16) return 0;
    input[typeId] = Number(input[typeId] || 0) + amount;
    writeJson(assembler, "input", input);
    return amount;
}

function insertConveyor(conveyor, typeId, amount) {
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

function acceptItem(block, typeId, amount) {
    if (!block) return 0;
    switch (block.typeId) {
        case STORAGE_CORE:
        case STORAGE_EXTENSION:
            return insertStorage(block, typeId, amount);
        case CONVEYOR:
            return insertConveyor(block, typeId, amount);
        case ASSEMBLER:
            return insertAssembler(block, typeId, amount);
        case GENERATOR:
            return insertGenerator(block, typeId, amount);
        default:
            return 0;
    }
}

function outputAdjacent(block, typeId, amount) {
    for (const next of allNeighbors(block)) {
        if (!next) continue;
        const accepted = acceptItem(next, typeId, amount);
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
        if (part.typeId === BATTERY || part.typeId === GENERATOR) {
            total += Number(read(part, "energy", 0));
        }
    }
    return Math.floor(total);
}

function drainEnergy(block, amount) {
    const parts = energyBlocks(block).filter((part) => part.typeId === BATTERY || part.typeId === GENERATOR);
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
        energy = Math.min(2000, energy + burn * 2);
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
}

function tickConveyor(block) {
    const item = readJson(block, "item", null);
    if (!item || item.amount < 1) return;
    const next = neighbor(block, facing(block));
    if (!next) return;
    const accepted = acceptItem(next, item.id, item.amount);
    if (accepted >= item.amount) writeJson(block, "item", null);
    else if (accepted > 0) {
        item.amount -= accepted;
        writeJson(block, "item", item);
    }
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
    for (const recipe of ASSEMBLER_RECIPES) {
        if (!hasRecipe(input, recipe)) continue;
        if (!drainEnergy(block, recipe.energy)) return;
        consumeRecipe(input, recipe);
        for (const [typeId, amount] of Object.entries(recipe.output)) {
            output[typeId] = Number(output[typeId] || 0) + amount;
        }
        writeJson(block, "input", input);
        writeJson(block, "output", output);
        return;
    }
}

function quarryArea(data) {
    const a = data.area;
    if (!a || !a.min || !a.max) return false;
    return true;
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

function tickQuarry(block) {
    const data = readJson(block, "data", { buffer: {} });
    data.buffer = data.buffer || {};
    for (const [typeId, amount] of Object.entries(data.buffer)) {
        const accepted = outputAdjacent(block, typeId, amount);
        if (accepted >= amount) delete data.buffer[typeId];
        else data.buffer[typeId] = amount - accepted;
    }
    if (!data.active || !quarryArea(data)) {
        writeJson(block, "data", data);
        return;
    }
    let mined = 0;
    let attempts = 0;
    while (mined < 3 && attempts < 24) {
        attempts++;
        const cursor = data.cursor;
        if (!cursor) {
            data.active = false;
            break;
        }
        const a = data.area;
        const x = cursor.x, y = cursor.y, z = cursor.z;
        if (y < a.min.y) {
            data.active = false;
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
        if (!target || !mineable(target)) continue;
        if (!drainEnergy(block, 8)) {
            data.active = false;
            break;
        }
        const drop = dropFor(target.typeId);
        target.setType("minecraft:air");
        data.buffer[drop] = Number(data.buffer[drop] || 0) + 1;
        mined++;
    }
    writeJson(block, "data", data);
}

function tickMachine(block) {
    if (!block) return;
    try {
        switch (block.typeId) {
            case GENERATOR: tickGenerator(block); break;
            case CONVEYOR: tickConveyor(block); break;
            case ASSEMBLER: tickAssembler(block); break;
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
    const min = { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), z: Math.min(a.z, b.z) };
    const max = { x: Math.max(a.x, b.x), y: Math.max(a.y, b.y), z: Math.max(a.z, b.z) };
    if (max.x - min.x > 31 || max.y - min.y > 31 || max.z - min.z > 31) {
        action(player, "The quarry area is too large (max 32x32x32).");
        return;
    }
    const data = readJson(quarry, "data", { buffer: {} });
    data.area = { min, max };
    data.cursor = { x: min.x, y: max.y, z: min.z };
    data.active = false;
    data.buffer = data.buffer || {};
    writeJson(quarry, "data", data);
    action(player, "Quarry area set. Connect storage and power.");
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

function drill(player, block, face) {
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
    let mined = 0;
    for (const pos of targets) {
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
    let cursor = block;
    for (let i = 0; i < 10 && cursor; i++) {
        if (cursor.typeId.endsWith("_log") || cursor.typeId.endsWith("_wood")) {
            const drop = dropFor(cursor.typeId);
            cursor.setType("minecraft:air");
            addItem(player, drop, 1);
            mined++;
        }
        cursor = neighbor(cursor, "up");
    }
    action(player, `Chainsaw cut ${mined} log${mined === 1 ? "" : "s"}.`);
    return mined > 0;
}

function rotateConveyor(block) {
    const current = facing(block);
    const next = FACINGS[(FACINGS.indexOf(current) + 1) % FACINGS.length];
    setFacing(block, next);
    return next;
}

function openMachine(player, block) {
    if (block.typeId === STORAGE_CORE || block.typeId === STORAGE_EXTENSION) {
        void openStorage(player, block);
        return;
    }
    if (block.typeId === GENERATOR) {
        const fuel = Number(read(block, "fuel", 0));
        const energy = Number(read(block, "energy", 0));
        const form = new ActionFormData().title("Coal Generator")
            .body(`Fuel: ${Math.floor(fuel)}\nEnergy: ${Math.floor(energy)}/2000\nNetwork: ${networkEnergy(block)}`);
        form.button("Close");
        void form.show(player).catch(() => {});
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
        const lines = [];
        for (const recipe of ASSEMBLER_RECIPES) lines.push(`${recipe.name} (${recipe.energy} E)`);
        const form = new ActionFormData().title("Crafting Assembler")
            .body(`Input: ${Object.entries(input).map(([id, n]) => `${formatName(id)} x${n}`).join(", ") || "empty"}\nOutput: ${Object.entries(output).map(([id, n]) => `${formatName(id)} x${n}`).join(", ") || "empty"}\nEnergy: ${networkEnergy(block)}\n\n${lines.join("\n")}`);
        form.button("Close");
        void form.show(player).catch(() => {});
        return;
    }
    if (block.typeId === QUARRY) {
        const data = readJson(block, "data", {});
        const area = data.area ? `${data.area.min.x},${data.area.min.y},${data.area.min.z} -> ${data.area.max.x},${data.area.max.y},${data.area.max.z}` : "not set";
        const form = new ActionFormData().title("Quarry Controller")
            .body(`Status: ${data.active ? "active" : "paused"}\nArea: ${area}\nBuffer: ${Object.values(data.buffer || {}).reduce((a, b) => a + b, 0)} items\nEnergy: ${networkEnergy(block)}`)
            .button(data.active ? "Pause quarry" : "Start quarry")
            .button("Close");
        void form.show(player).then((response) => {
            if (response.canceled || response.selection !== 0) return;
            data.active = !data.active;
            if (data.active && !quarryArea(data)) {
                action(player, "Use the Quarry Surveyor on two corners first.");
                return;
            }
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

    if (item?.typeId === WRENCH && block.typeId === CONVEYOR) {
        const direction = rotateConveyor(block);
        damageHeld(player, item);
        action(player, `Conveyor direction: ${direction}`);
        return;
    }
    if (item?.typeId === SURVEYOR) {
        surveyorUse(player, block);
        return;
    }
    if (item?.typeId === DRILL) {
        if (drill(player, block, event.blockFace)) damageHeld(player, item);
        return;
    }
    if (item?.typeId === CHAINSAW) {
        if (chainsaw(player, block)) damageHeld(player, item);
        return;
    }

    if (block.typeId === STORAGE_CORE || block.typeId === STORAGE_EXTENSION) {
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
    if (block.typeId === BATTERY || block.typeId === QUARRY) {
        later(() => openMachine(player, block));
    }
}

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
    try { interact(event); } catch (error) { warn("interaction failed", String(error)); }
});

world.afterEvents.playerPlaceBlock.subscribe((event) => {
    try {
        if (event.block.typeId !== CONVEYOR) return;
        const yaw = event.player.getRotation().y;
        const index = Math.round(((yaw % 360) + 360) % 360 / 90) % 4;
        setFacing(event.block, ["south", "west", "north", "east"][index]);
    } catch {
        // Ignore placement orientation failures.
    }
});

world.afterEvents.playerBreakBlock.subscribe((event) => {
    try {
        if (event.block.typeId === BATTERY) {
            const energy = Number(read(event.block, "energy", 0));
            if (energy > 0) event.player.sendMessage(`Battery removed with ${Math.floor(energy)} energy.`);
        }
    } catch {
        // Ignore.
    }
});

world.afterEvents.worldLoad.subscribe(() => {
    warn("Cogworks loaded");
});
