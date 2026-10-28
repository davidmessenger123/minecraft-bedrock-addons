/*
 * Bloomlands runtime.
 *
 * The custom dimension is data-driven and void-generated.  Everything in it is
 * placed by this script: a floating island with five garden regions, a return
 * Bloomgate, ambient particles, peaceful Bloomling mobs and a hard guarantee
 * that no hostile mobs remain in the dimension.
 */

import { world, system, BlockVolume } from "@minecraft/server";

const DIMENSION_ID = "bl:bloomlands";
const GROUND_Y = 64;
const ISLAND_RADIUS = 240;
const SPAWN = Object.freeze({ x: 0.5, y: 65, z: 126 });
const PORTAL = Object.freeze({ x: 0, y: 64, z: 96 });
const PORTAL_ITEM = "bl:bloom_portal";
const HEART = "bl:bloomheart";
const RETURN_KEY = "bl:return";
// v2 is deliberately a new key.  Worlds made with the original 120-block
// island keep their old marker, then grow the new 480-block island around it.
const GENERATED_KEY = "bl:generated_v2";
const FOG_TAG = "bloomlands_region";
const LOG = "[Bloomlands]";

// Construction is split into 16 tiles.  Each pass loads at most a 10x10
// chunk window (the engine's ticking-area budget), builds the 8x8 chunk core
// plus a one-chunk feature margin, then releases the area for the next pass.
const TILE_CORE = 128;
const TILE_MARGIN = 16;
const TILE_ORIGINS = Object.freeze([-256, -128, 0, 128]);
const SPAWN_AREA_FROM = Object.freeze({ x: -32, y: 0, z: 64 });
const SPAWN_AREA_TO = Object.freeze({ x: 31, y: 128, z: 143 });

const RING = Object.freeze([
    [0, -3],
    [-2, -2],
    [-3, 0],
    [-2, 2],
    [0, 3],
    [2, 2],
    [3, 0],
    [2, -2],
]);

const REGIONS = Object.freeze({
    meadow: {
        fog: "bl:bloomlands_meadow",
        title: "bl.region.meadow",
        particle: "bl:petal_mote",
    },
    canopy: {
        fog: "bl:bloomlands_canopy",
        title: "bl.region.canopy",
        particle: "bl:firefly",
    },
    garden: {
        fog: "bl:bloomlands_garden",
        title: "bl.region.garden",
        particle: "bl:pollen",
    },
    hills: {
        fog: "bl:bloomlands_hills",
        title: "bl.region.hills",
        particle: "bl:petal_mote",
    },
    pool: {
        fog: "bl:bloomlands_pool",
        title: "bl.region.pool",
        particle: "bl:water_ripple",
    },
    edge: {
        fog: "bl:bloomlands_edge",
        title: "bl.region.edge",
        particle: "bl:petal_mote",
    },
});

const GROUND_TYPES = new Set([
    "minecraft:grass_block",
    "minecraft:dirt",
    "minecraft:coarse_dirt",
    "minecraft:rooted_dirt",
    "minecraft:podzol",
    "minecraft:mycelium",
    "minecraft:moss_block",
    "minecraft:stone",
    "minecraft:deepslate",
    "minecraft:andesite",
    "minecraft:granite",
    "minecraft:diorite",
    "minecraft:calcite",
    "minecraft:tuff",
    "minecraft:sand",
    "minecraft:red_sand",
    "minecraft:gravel",
    "minecraft:snow_block",
    "minecraft:netherrack",
    "minecraft:soul_soil",
    "minecraft:soul_sand",
    "minecraft:basalt",
    "minecraft:blackstone",
    "minecraft:end_stone",
    "minecraft:purpur_block",
    "bl:petal_grass",
    "bl:bloom_dirt",
    "bl:bloom_stone",
    "bl:petal_path",
    "bl:bloomwood_planks",
]);

const PORTAL_GROUND = new Set([
    ...GROUND_TYPES,
    "bl:bloomwood_log",
]);

const PLANT_TYPES = new Set([
    "minecraft:air",
    "minecraft:cave_air",
    "minecraft:void_air",
    "minecraft:short_grass",
    "minecraft:grass",
    "minecraft:tall_grass",
    "minecraft:fern",
    "minecraft:large_fern",
    "minecraft:dandelion",
    "minecraft:poppy",
    "minecraft:blue_orchid",
    "minecraft:allium",
    "minecraft:azure_bluet",
    "minecraft:red_tulip",
    "minecraft:orange_tulip",
    "minecraft:white_tulip",
    "minecraft:pink_tulip",
    "minecraft:oxeye_daisy",
    "minecraft:cornflower",
    "minecraft:lily_of_the_valley",
    "minecraft:sunflower",
    "minecraft:lilac",
    "minecraft:rose_bush",
    "minecraft:peony",
    "minecraft:torchflower",
    "minecraft:pitcher_plant",
    "minecraft:snow_layer",
    "bl:sunpetal",
    "bl:rosequartz",
    "bl:skybell",
    "bl:moondrop",
    "bl:emberbloom",
    "bl:amethyst_bell",
    "bl:lumen_bell",
    "bl:dewgrass",
    "bl:lily_bloom",
    "bl:portal_flower",
]);

const HOSTILE_TYPES = new Set([
    "minecraft:zombie",
    "minecraft:zombie_villager",
    "minecraft:zombie_villager_v2",
    "minecraft:husk",
    "minecraft:drowned",
    "minecraft:skeleton",
    "minecraft:stray",
    "minecraft:bogged",
    "minecraft:creeper",
    "minecraft:spider",
    "minecraft:cave_spider",
    "minecraft:silverfish",
    "minecraft:endermite",
    "minecraft:enderman",
    "minecraft:witch",
    "minecraft:pillager",
    "minecraft:vindicator",
    "minecraft:evoker",
    "minecraft:illusioner",
    "minecraft:ravager",
    "minecraft:vex",
    "minecraft:phantom",
    "minecraft:blaze",
    "minecraft:ghast",
    "minecraft:magma_cube",
    "minecraft:slime",
    "minecraft:guardian",
    "minecraft:elder_guardian",
    "minecraft:wither_skeleton",
    "minecraft:wither",
    "minecraft:ender_dragon",
    "minecraft:shulker",
    "minecraft:piglin",
    "minecraft:piglin_brute",
    "minecraft:zombified_piglin",
    "minecraft:hoglin",
    "minecraft:zoglin",
    "minecraft:warden",
    "minecraft:breeze",
    "minecraft:creaking",
]);

const FLOWERS = Object.freeze({
    meadow: ["sunpetal", "rosequartz", "skybell", "moondrop", "emberbloom", "amethyst_bell"],
    canopy: ["lumen_bell", "moondrop", "skybell"],
    garden: ["rosequartz", "sunpetal", "skybell", "amethyst_bell", "emberbloom"],
    hills: ["skybell", "moondrop", "sunpetal", "rosequartz"],
    pool: ["skybell", "moondrop", "rosequartz", "lumen_bell"],
    edge: ["sunpetal", "rosequartz", "lumen_bell"],
});

const state = {
    islandPromise: null,
    initialized: false,
    fillFailures: 0,
    genClip: null,
    lastHostile: 0,
    lastMob: 0,
    lastAmbient: 0,
    lastMobRescue: 0,
    building: new Set(),
    teleporting: new Set(),
    players: new Map(),
};

function warn(...args) {
    try {
        console.warn(LOG, ...args);
    } catch {
        // Nothing useful to do if the console is unavailable.
    }
}

function getPlayerState(player) {
    let value = state.players.get(player.id);
    if (!value) {
        value = {
            cooldownUntil: 0,
            heartDisarmed: false,
            lastRegion: "",
            lastRegionAt: 0,
            fogSet: false,
        };
        state.players.set(player.id, value);
    }
    return value;
}

function actionBar(player, key) {
    try {
        player.onScreenDisplay.setActionBar({ translate: key });
    } catch {
        // Display calls can fail while a player is disconnecting.
    }
}

function title(player, titleKey, subtitleKey) {
    try {
        player.onScreenDisplay.setTitle(
            { translate: titleKey },
            {
                subtitle: { translate: subtitleKey },
                fadeInDuration: 12,
                stayDuration: 65,
                fadeOutDuration: 20,
            },
        );
    } catch {
        // Ignore display failures.
    }
}

function message(player, key) {
    try {
        player.sendMessage({ translate: key });
    } catch {
        // Ignore display failures.
    }
}

function sound(player, soundId, volume = 0.8, pitch = 1.0) {
    try {
        player.playSound(soundId, { volume, pitch });
    } catch {
        // Sounds are cosmetic.
    }
}

function bloomDimension() {
    try {
        return world.getDimension(DIMENSION_ID);
    } catch {
        return undefined;
    }
}

async function requireDimension() {
    for (let attempt = 0; attempt < 12; attempt++) {
        const dimension = bloomDimension();
        if (dimension) return dimension;
        await system.waitTicks(10);
    }
    throw new Error("dimension bl:bloomlands is not available");
}

function blockAt(dimension, x, y, z) {
    try {
        return dimension.getBlock({
            x: Math.floor(x),
            y: Math.floor(y),
            z: Math.floor(z),
        });
    } catch {
        return undefined;
    }
}

function typeAt(dimension, x, y, z) {
    const block = blockAt(dimension, x, y, z);
    return block ? block.typeId : undefined;
}

function isAirType(typeId) {
    return (
        typeId === "minecraft:air" ||
        typeId === "minecraft:cave_air" ||
        typeId === "minecraft:void_air"
    );
}

function isPlant(typeId) {
    return typeId !== undefined && PLANT_TYPES.has(typeId);
}

function isGround(typeId) {
    return typeId !== undefined && GROUND_TYPES.has(typeId);
}

function hash2(x, z, seed = 0) {
    let h = Math.imul(Math.floor(x) ^ 0x9e3779b9, 0x85ebca6b);
    h ^= Math.imul(Math.floor(z) ^ 0xc2b2ae35, 0x27d4eb2f);
    h ^= seed + 0x7f4a7c15;
    h ^= h >>> 16;
    h = Math.imul(h, 0x7feb352d);
    h ^= h >>> 15;
    h = Math.imul(h, 0x846ca68b);
    h ^= h >>> 16;
    return h >>> 0;
}

function hashPct(x, z, seed = 0) {
    return hash2(x, z, seed) % 100;
}

function clipContains(x, z) {
    const clip = state.genClip;
    return !clip || (x >= clip.minX && x <= clip.maxX && z >= clip.minZ && z <= clip.maxZ);
}

function clipIntersects(minX, maxX, minZ, maxZ) {
    const clip = state.genClip;
    return (
        !clip ||
        (maxX >= clip.minX && minX <= clip.maxX && maxZ >= clip.minZ && minZ <= clip.maxZ)
    );
}

function fill(dimension, x0, y0, z0, x1, y1, z1, type) {
    const from = {
        x: Math.min(x0, x1),
        y: Math.min(y0, y1),
        z: Math.min(z0, z1),
    };
    const to = {
        x: Math.max(x0, x1),
        y: Math.max(y0, y1),
        z: Math.max(z0, z1),
    };
    const clip = dimension.id === DIMENSION_ID ? state.genClip : null;
    if (clip) {
        from.x = Math.max(from.x, clip.minX);
        from.z = Math.max(from.z, clip.minZ);
        to.x = Math.min(to.x, clip.maxX);
        to.z = Math.min(to.z, clip.maxZ);
        if (from.x > to.x || from.z > to.z) return false;
    }
    try {
        dimension.fillBlocks(new BlockVolume(from, to), type, {
            ignoreChunkBoundErrors: true,
        });
        return true;
    } catch (error) {
        state.fillFailures++;
        if (state.fillFailures <= 3) {
            warn("fill failed", `${from.x},${from.y},${from.z}`, `${to.x},${to.y},${to.z}`, type, String(error));
        }
        return false;
    }
}

function place(dimension, x, y, z, type) {
    const ix = Math.floor(x);
    const iz = Math.floor(z);
    const clip = dimension.id === DIMENSION_ID ? state.genClip : null;
    if (clip && (ix < clip.minX || ix > clip.maxX || iz < clip.minZ || iz > clip.maxZ)) {
        return false;
    }
    try {
        const block = blockAt(dimension, ix, y, iz);
        if (!block) return false;
        block.setType(type);
        return true;
    } catch {
        return false;
    }
}

async function tick() {
    await system.waitTicks(1);
}

async function disc(dimension, cx, cz, radius, y0, y1, type, clipRadius = 0) {
    const r = Math.max(0, radius);
    let zStart = Math.floor(cz - r);
    let zEnd = Math.ceil(cz + r);
    const clip = state.genClip;
    if (clip) {
        zStart = Math.max(zStart, clip.minZ);
        zEnd = Math.min(zEnd, clip.maxZ);
    }
    for (let z = zStart; z <= zEnd; z++) {
        const dz = z - cz;
        if (Math.abs(dz) > r) continue;
        let x0 = Math.floor(cx - Math.sqrt(Math.max(0, r * r - dz * dz)));
        let x1 = Math.floor(cx + Math.sqrt(Math.max(0, r * r - dz * dz)));
        if (clipRadius > 0) {
            const half = Math.sqrt(Math.max(0, clipRadius * clipRadius - dz * dz));
            x0 = Math.max(x0, Math.ceil(-half));
            x1 = Math.min(x1, Math.floor(half));
        }
        if (x1 >= x0) {
            fill(dimension, x0, y0, z, x1, y1, z, type);
        }
        if ((z & 7) === 0) await tick();
    }
}

async function ring(dimension, cx, cz, inner, outer, y0, y1, type, clipRadius = 0) {
    let zStart = Math.floor(cz - outer);
    let zEnd = Math.ceil(cz + outer);
    const clip = state.genClip;
    if (clip) {
        zStart = Math.max(zStart, clip.minZ);
        zEnd = Math.min(zEnd, clip.maxZ);
    }
    for (let z = zStart; z <= zEnd; z++) {
        const dz = z - cz;
        if (Math.abs(dz) > outer) continue;
        let x0 = Math.floor(cx - Math.sqrt(Math.max(0, outer * outer - dz * dz)));
        let x1 = Math.floor(cx + Math.sqrt(Math.max(0, outer * outer - dz * dz)));
        if (clipRadius > 0) {
            const half = Math.sqrt(Math.max(0, clipRadius * clipRadius - dz * dz));
            x0 = Math.max(x0, Math.ceil(-half));
            x1 = Math.min(x1, Math.floor(half));
        }
        if (x1 < x0) continue;
        if (Math.abs(dz) >= inner) {
            fill(dimension, x0, y0, z, x1, y1, z, type);
        } else {
            const half = Math.sqrt(Math.max(0, inner * inner - dz * dz));
            const left = Math.ceil(cx - half);
            const right = Math.floor(cx + half);
            if (left - 1 >= x0) {
                fill(dimension, x0, y0, z, left - 1, y1, z, type);
            }
            if (right + 1 <= x1) {
                fill(dimension, right + 1, y0, z, x1, y1, z, type);
            }
        }
        if ((z & 7) === 0) await tick();
    }
}

async function addTickingArea(dimension, name, from, to) {
    // The script API manager is the reliable way to load chunks in a void
    // dimension. Older engines fall back to the command, which still works
    // when the dimension is the command source.
    const manager = world.tickingAreaManager;
    if (manager) {
        try {
            if (manager.hasTickingArea(name)) return true;
            const capacity = typeof manager.hasCapacity === "function"
                ? manager.hasCapacity({ dimension, from, to })
                : true;
            if (capacity) {
                await manager.createTickingArea(name, { dimension, from, to });
                return true;
            }
            warn("ticking area capacity reached", name);
        } catch (error) {
            // Fall through to the command when the API refuses early-execution.
            warn("ticking area API failed", name, String(error));
        }
    }

    const command = `tickingarea add ${from.x} ${from.y} ${from.z} ${to.x} ${to.y} ${to.z} ${name}`;
    try {
        dimension.runCommand(command);
        return true;
    } catch (error) {
        // "Already exists" is expected across restarts.
        const text = String(error);
        if (!text.includes("already") && !text.includes("exist")) {
            warn("ticking area failed", name, text);
        }
        return false;
    }
}

function removeTickingArea(dimension, name) {
    try {
        const manager = world.tickingAreaManager;
        if (manager && manager.hasTickingArea(name)) {
            manager.removeTickingArea(name);
            return;
        }
    } catch {
        // Fall through to the command.
    }
    try {
        dimension.runCommand(`tickingarea remove ${name}`);
    } catch {
        // It may not exist.
    }
}

async function waitForChunks(dimension, area) {
    const probes = area
        ? [
            [Math.floor((area.minX + area.maxX) / 2), 64, Math.floor((area.minZ + area.maxZ) / 2)],
            [area.minX + 8, 64, area.minZ + 8],
            [area.maxX - 8, 64, area.minZ + 8],
            [area.minX + 8, 64, area.maxZ - 8],
            [area.maxX - 8, 64, area.maxZ - 8],
        ]
        : [
            [0, 64, 0],
            [48, 64, 48],
            [-48, 64, 48],
            [48, 64, -48],
            [-48, 64, -48],
            [0, 64, 56],
            [0, 64, -56],
            [44, 104, -34],
        ];
    for (let attempt = 0; attempt < 80; attempt++) {
        let ready = true;
        for (const [x, y, z] of probes) {
            if (!blockAt(dimension, x, y, z)) {
                ready = false;
                break;
            }
        }
        if (ready) return true;
        await system.waitTicks(5);
    }
    warn("chunk load timed out; continuing with loaded chunks", area ? `${area.minX},${area.minZ}` : "legacy");
    return false;
}

function isLandBuilt(dimension) {
    const probes = [
        [8, 8],
        [-8, 8],
        [8, -8],
        [-8, -8],
    ];
    let solid = 0;
    for (const [x, z] of probes) {
        const type = typeAt(dimension, x, GROUND_Y, z);
        if (type !== undefined && !isAirType(type)) solid++;
    }
    return solid >= 3;
}

async function ensureSpawnPlatform(dimension) {
    if (!clipContains(SPAWN.x, SPAWN.z)) return;
    const cz = Math.round(SPAWN.z);
    fill(dimension, -4, 62, cz - 4, 4, 63, cz + 4, "bl:bloom_stone");
    fill(dimension, -4, 64, cz - 4, 4, 64, cz + 4, "bl:petal_grass");
    fill(dimension, -3, 65, cz - 3, 3, 66, cz + 3, "minecraft:air");
    // A soft ring of light around the landing place.
    for (let i = 0; i < 8; i++) {
        const angle = (i * Math.PI) / 4;
        const x = Math.round(Math.cos(angle) * 4);
        const z = cz + Math.round(Math.sin(angle) * 4);
        if (isGround(typeAt(dimension, x, 64, z)) && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, "bl:sunpetal");
        }
    }
    for (let i = 0; i < 4; i++) {
        const angle = (i * Math.PI) / 2 + Math.PI / 4;
        const x = Math.round(Math.cos(angle) * 6);
        const z = cz + Math.round(Math.sin(angle) * 6);
        if (isGround(typeAt(dimension, x, 64, z)) && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, "bl:lumen_bell");
        }
    }
    await tick();
}

async function ensurePortalPlatform(dimension) {
    if (!clipContains(PORTAL.x, PORTAL.z)) return;
    const cz = Math.round(PORTAL.z);
    fill(dimension, -6, 62, cz - 6, 6, 63, cz + 6, "bl:bloom_stone");
    await disc(dimension, PORTAL.x, PORTAL.z, 6, 64, 64, "bl:petal_path");
    fill(dimension, -4, 65, cz - 4, 4, 66, cz + 4, "minecraft:air");
    await tick();
}

async function buildReturnPortal(dimension) {
    if (!clipContains(PORTAL.x, PORTAL.z)) return;
    await ensurePortalPlatform(dimension);
    for (const [dx, dz] of RING) {
        place(dimension, PORTAL.x + dx, PORTAL.y + 1, PORTAL.z + dz, "bl:portal_flower");
    }
    place(dimension, PORTAL.x, PORTAL.y, PORTAL.z, HEART);

    for (let i = 0; i < 8; i++) {
        const angle = (i * Math.PI) / 4;
        const x = PORTAL.x + Math.round(Math.cos(angle) * 7);
        const z = PORTAL.z + Math.round(Math.sin(angle) * 7);
        if (Math.hypot(x - SPAWN.x, z - SPAWN.z) < 3.5) continue;
        if (isGround(typeAt(dimension, x, 64, z)) && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, i % 2 ? "bl:lumen_bell" : "bl:rosequartz");
        }
    }
    for (let i = 0; i < 4; i++) {
        const angle = Math.PI / 4 + (i * Math.PI) / 2;
        const x = PORTAL.x + Math.round(Math.cos(angle) * 10);
        const z = PORTAL.z + Math.round(Math.sin(angle) * 10);
        if (z > PORTAL.z + 2) continue;
        if (isGround(typeAt(dimension, x, 64, z)) && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, "bl:giant_lumen");
        }
    }
    await tick();
}

async function buildBase(dimension) {
    await disc(dimension, 0, 0, ISLAND_RADIUS, 44, 61, "bl:bloom_stone");
    await disc(dimension, 0, 0, ISLAND_RADIUS, 62, 63, "bl:bloom_dirt");
    await disc(dimension, 0, 0, ISLAND_RADIUS, 64, 64, "bl:petal_grass");
    await ring(dimension, 0, 0, ISLAND_RADIUS - 16, ISLAND_RADIUS, 64, 64, "bl:bloom_stone");
    const underside = [
        [43, 216],
        [42, 184],
        [41, 144],
        [40, 96],
        [39, 48],
    ];
    for (const [y, radius] of underside) {
        await disc(dimension, 0, 0, radius, y, y, "bl:bloom_stone");
    }
    await tick();
}

async function buildHills(dimension) {
    const cx = -136;
    const cz = -48;
    if (!clipIntersects(cx - 68, cx + 68, cz - 68, cz + 68)) return;
    const levels = [
        [64, 65],
        [52, 66],
        [40, 67],
        [28, 68],
        [16, 69],
        [8, 70],
    ];

    for (const [radius, top] of levels) {
        if (top - 2 >= 64) {
            await disc(dimension, cx, cz, radius, 64, top - 2, "bl:bloom_stone");
        }
        await disc(dimension, cx, cz, radius, top - 1, top - 1, "bl:bloom_dirt");
        await disc(dimension, cx, cz, radius, top, top, "bl:petal_grass");
    }

    // A spiral path, always one block up so the hill is walkable.
    for (let i = 0; i < 800; i++) {
        const t = i / 800;
        const angle = t * Math.PI * 5.5;
        const radius = 60 - t * 56;
        const level = Math.min(5, Math.floor((64 - radius) / 10));
        const top = 65 + level;
        const x = Math.round(cx + Math.cos(angle) * radius);
        const z = Math.round(cz + Math.sin(angle) * radius);
        if (isGround(typeAt(dimension, x, top, z))) {
            place(dimension, x, top, z, "bl:petal_path");
            if (i % 23 === 0) {
                placeFlowerAt(dimension, x + 1, top, z, "skybell");
            }
        }
        if (i % 40 === 0) await tick();
    }

    // Small flowers on each terrace.
    const terraceFlowers = [
        [60, 65, "sunpetal"],
        [48, 66, "rosequartz"],
        [36, 67, "skybell"],
        [24, 68, "moondrop"],
        [12, 69, "lumen_bell"],
    ];
    for (const [radius, top, flower] of terraceFlowers) {
        for (let i = 0; i < 24; i++) {
            const angle = (i / 24) * Math.PI * 2 + 0.3;
            const x = Math.round(cx + Math.cos(angle) * radius);
            const z = Math.round(cz + Math.sin(angle) * radius);
            placeFlowerAt(dimension, x, top, z, i % 4 === 0 ? "lumen_bell" : flower);
        }
    }

    // Giant blooms on the lower terrace and the crown.
    for (let i = 0; i < 6; i++) {
        const angle = Math.PI / 6 + (i * Math.PI) / 3;
        const x = Math.round(cx + Math.cos(angle) * 52);
        const z = Math.round(cz + Math.sin(angle) * 52);
        if (isGround(typeAt(dimension, x, 66, z)) && isAirType(typeAt(dimension, x, 67, z))) {
            place(dimension, x, 67, z, i % 2 ? "bl:giant_skybell" : "bl:giant_sunflower");
        }
    }
    place(dimension, cx, 71, cz, "bl:giant_lumen");
    place(dimension, cx + 1, 71, cz, "bl:giant_amethyst");
    place(dimension, cx - 1, 71, cz, "bl:lumen_bell");
    await tick();
}

async function buildLake(dimension) {
    const cx = -120;
    const cz = 64;
    if (!clipIntersects(cx - 56, cx + 56, cz - 56, cz + 56)) return;
    await disc(dimension, cx, cz, 36, 57, 57, "bl:bloom_stone");
    await disc(dimension, cx, cz, 36, 58, 64, "minecraft:water");
    await ring(dimension, cx, cz, 40, 44, 64, 64, "bl:petal_path");

    // A tiny island and a tall skybell at the centre of the mirror.
    await disc(dimension, cx, cz, 8, 58, 63, "bl:bloom_stone");
    await disc(dimension, cx, cz, 8, 64, 64, "bl:petal_grass");
    place(dimension, cx, 65, cz, "bl:giant_skybell");

    for (let i = 0; i < 88; i++) {
        const angle = hashPct(i, 3, 4) * 0.0618;
        const radius = 11 + (hashPct(i, 7, 9) / 100) * 22;
        const x = Math.round(cx + Math.cos(angle) * radius);
        const z = Math.round(cz + Math.sin(angle) * radius);
        if (typeAt(dimension, x, 64, z) === "minecraft:water" && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, "bl:lily_bloom");
        }
    }

    for (let i = 0; i < 64; i++) {
        const angle = (i / 64) * Math.PI * 2 + 0.2;
        const radius = 48;
        const x = Math.round(cx + Math.cos(angle) * radius);
        const z = Math.round(cz + Math.sin(angle) * radius);
        placeFlower(dimension, x, z, i % 3 === 0 ? "skybell" : "moondrop");
        if (i % 4 === 0) placeFlower(dimension, x + 1, z, "dewgrass");
    }
    for (let i = 0; i < 8; i++) {
        const angle = Math.PI / 8 + (i * Math.PI) / 4;
        const x = Math.round(cx + Math.cos(angle) * 52);
        const z = Math.round(cz + Math.sin(angle) * 52);
        if (isGround(typeAt(dimension, x, 64, z)) && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, i % 2 ? "bl:giant_rosequartz" : "bl:giant_skybell");
        }
    }
    await tick();
}

function placeFlowerAt(dimension, x, groundY, z, key) {
    const ground = typeAt(dimension, x, groundY, z);
    if (!isGround(ground) || ground === "bl:bloom_stone" || ground === "bl:petal_path") return false;
    if (!isAirType(typeAt(dimension, x, groundY + 1, z))) return false;
    return place(dimension, x, groundY + 1, z, `bl:${key}`);
}

function placeFlower(dimension, x, z, key) {
    return placeFlowerAt(dimension, x, GROUND_Y, z, key);
}

function placeForestTree(dimension, x, z, giant = false) {
    // Keep the main path through the canopy clear.
    if (Math.abs(x) < 10 && z > -216 && z < 136) return false;
    const ground = typeAt(dimension, x, GROUND_Y, z);
    if (!isGround(ground) || ground === "bl:bloom_stone" || ground === "bl:petal_path") return false;
    if (!isAirType(typeAt(dimension, x, GROUND_Y + 1, z))) return false;

    const height = giant ? 14 : 8 + (hashPct(x, z, 7) % 5);
    const top = GROUND_Y + height;
    fill(dimension, x, GROUND_Y + 1, z, x, top, z, "bl:bloomwood_log");

    if (giant) {
        fill(dimension, x - 3, top - 1, z - 3, x + 3, top, z + 3, "bl:canopy_leaves");
        // Restore the central trunk block after the canopy pass so the bloom
        // has a valid log block underneath it.
        place(dimension, x, top, z, "bl:bloomwood_log");
        fill(dimension, x - 2, top + 1, z - 2, x + 2, top + 1, z + 2, "bl:glowbud_leaves");
        place(dimension, x, top + 1, z, "bl:giant_lumen");
    } else {
        fill(dimension, x - 3, top - 1, z - 3, x + 3, top, z + 3, "bl:canopy_leaves");
        fill(dimension, x - 2, top + 1, z - 2, x + 2, top + 1, z + 2, "bl:canopy_leaves");
        fill(dimension, x - 1, top + 2, z - 1, x + 1, top + 2, z + 1, "bl:canopy_leaves");
        fill(dimension, x + 1, top, z + 1, x + 2, top, z + 2, "bl:glowbud_leaves");
    }

    if (hashPct(x, z, 11) < 45) {
        placeFlower(dimension, x + 1, z, "lumen_bell");
    }
    if (hashPct(x, z, 13) < 35) {
        placeFlower(dimension, x - 1, z + 1, "dewgrass");
    }
    return true;
}

async function buildForest(dimension) {
    if (!clipIntersects(-220, 220, -230, -70)) return;
    const giants = [
        [96, -136],
        [-72, -168],
        [24, -192],
        [160, -112],
    ];
    for (let x = -208; x <= 208; x += 8) {
        for (let z = -216; z <= -80; z += 8) {
            const jx = x + (hashPct(x, z, 1) % 5) - 2;
            const jz = z + (hashPct(x, z, 2) % 5) - 2;
            if (Math.hypot(jx, jz) > 208) continue;
            if (Math.hypot(jx - -136, jz - -48) < 80) continue;
            if (Math.hypot(jx, jz - 96) < 56) continue;
            if (hashPct(jx, jz, 3) < 24) continue;
            placeForestTree(dimension, jx, jz, false);
        }
        await tick();
    }
    for (const [x, z] of giants) {
        placeForestTree(dimension, x, z, true);
    }

    for (let i = 0; i < 216; i++) {
        const x = -200 + (hashPct(i, 17, 5) % 400);
        const z = -208 + (hashPct(i, 19, 6) % 128);
        if (Math.hypot(x, z) > 208) continue;
        const flower = ["lumen_bell", "moondrop", "skybell"][i % 3];
        placeFlower(dimension, x, z, flower);
        if (i % 3 === 0) placeFlower(dimension, x + 1, z, "dewgrass");
    }

    // Mossy, glowing patches in the deep shade.
    for (let i = 0; i < 40; i++) {
        const x = -200 + (hashPct(i, 23, 8) % 400);
        const z = -208 + (hashPct(i, 29, 9) % 128);
        if (typeAt(dimension, x, GROUND_Y, z) === "bl:petal_grass" && isAirType(typeAt(dimension, x, GROUND_Y + 1, z))) {
            fill(dimension, x, GROUND_Y + 1, z, x + 1, GROUND_Y + 1, z + 1, "bl:glowbud_leaves");
        }
    }
    await tick();
}

function placeGiantTree(dimension, x, z, variant) {
    const ground = typeAt(dimension, x, GROUND_Y, z);
    if (!isGround(ground) || ground === "bl:bloom_stone" || ground === "bl:petal_path") return false;
    if (!isAirType(typeAt(dimension, x, GROUND_Y + 1, z))) return false;

    const height = 8 + (hashPct(x, z, 31) % 6);
    const top = GROUND_Y + height;
    fill(dimension, x, GROUND_Y + 1, z, x, top, z, "bl:bloomwood_log");
    // A collar of glowing leaves around the trunk, leaving the centre free.
    for (const [dx, dz] of [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]]) {
        place(dimension, x + dx, top, z + dz, "bl:glowbud_leaves");
    }
    place(dimension, x, top + 1, z, `bl:giant_${variant}`);
    if (hashPct(x, z, 37) < 55) {
        placeFlower(dimension, x + 1, z, "lumen_bell");
    }
    placeFlower(dimension, x - 1, z + 1, "dewgrass");
    return true;
}

async function buildGarden(dimension) {
    if (!clipIntersects(72, 212, -70, 146)) return;
    const variants = ["sunflower", "rosequartz", "skybell", "amethyst", "emberbloom"];
    let index = 0;
    for (let x = 88; x <= 200; x += 8) {
        for (let z = -56; z <= 136; z += 8) {
            const jx = x + (hashPct(x, z, 41) % 5) - 2;
            const jz = z + (hashPct(x, z, 43) % 5) - 2;
            if (Math.hypot(jx, jz) > 208) continue;
            if (Math.hypot(jx, jz - 96) < 64) continue;
            if (hashPct(jx, jz, 47) < 18) continue;
            placeGiantTree(dimension, jx, jz, variants[index % variants.length]);
            index++;
        }
        await tick();
    }

    // A handful of giant blooms growing straight out of the garden floor.
    const groundBlooms = [
        [108, 65, 48, "giant_sunflower"],
        [152, 65, 80, "giant_rosequartz"],
        [120, 65, 120, "giant_skybell"],
        [176, 65, 8, "giant_amethyst"],
        [96, 65, -24, "giant_emberbloom"],
    ];
    for (const [x, y, z, type] of groundBlooms) {
        if (isGround(typeAt(dimension, x, 64, z)) && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, y, z, `bl:${type}`);
        }
    }

    for (let i = 0; i < 104; i++) {
        const x = 80 + (hashPct(i, 53, 12) % 128);
        const z = -48 + (hashPct(i, 59, 13) % 184);
        if (Math.hypot(x, z) > 208) continue;
        const flower = ["rosequartz", "sunpetal", "skybell", "amethyst_bell"][i % 4];
        placeFlower(dimension, x, z, flower);
        if (i % 5 === 0) placeFlower(dimension, x + 1, z, "lumen_bell");
    }
    await tick();
}

async function pathLine(dimension, points, width = 5) {
    for (let segment = 0; segment < points.length - 1; segment++) {
        const a = points[segment];
        const b = points[segment + 1];
        const distance = Math.hypot(b.x - a.x, b.z - a.z);
        const steps = Math.max(1, Math.ceil(distance * 2));
        for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            const x = Math.round(a.x + (b.x - a.x) * t);
            const z = Math.round(a.z + (b.z - a.z) * t);
            const ground = typeAt(dimension, x, GROUND_Y, z);
            if (!isGround(ground) || ground === "bl:bloom_stone") continue;
            const r = Math.floor(width / 2);
            fill(dimension, x - r, GROUND_Y, z - r, x + r, GROUND_Y, z + r, "bl:petal_path");
            if (hashPct(x, z, 61) < 11) {
                const side = hashPct(x, z, 67) < 50 ? -(r + 1) : (r + 1);
                placeFlower(dimension, x + side, z, hashPct(x, z, 71) < 50 ? "sunpetal" : "rosequartz");
            }
            if (i % 12 === 0) await tick();
        }
    }
}

async function buildPaths(dimension) {
    await disc(dimension, PORTAL.x, PORTAL.z, 6, 64, 64, "bl:petal_path");
    await pathLine(dimension, [
        { x: 0, z: 136 },
        { x: 0, z: 96 },
        { x: 0, z: 32 },
        { x: 0, z: -40 },
        { x: 0, z: -88 },
        { x: 0, z: -136 },
        { x: 0, z: -184 },
    ]);
    await pathLine(dimension, [
        { x: 0, z: 96 },
        { x: 40, z: 88 },
        { x: 80, z: 64 },
        { x: 120, z: 32 },
        { x: 152, z: 0 },
    ]);
    await pathLine(dimension, [
        { x: 0, z: 96 },
        { x: -40, z: 88 },
        { x: -80, z: 64 },
        { x: -104, z: 32 },
        { x: -124, z: 0 },
        { x: -132, z: -24 },
    ]);
    await pathLine(dimension, [
        { x: -40, z: 88 },
        { x: -80, z: 80 },
        { x: -96, z: 72 },
    ]);
    await pathLine(dimension, [
        { x: 0, z: 32 },
        { x: -32, z: 16 },
        { x: -64, z: 0 },
        { x: -84, z: -8 },
    ]);
    await pathLine(dimension, [
        { x: 120, z: 32 },
        { x: 136, z: -16 },
        { x: 144, z: -56 },
        { x: 152, z: -80 },
    ]);
    await tick();
}

async function buildMeadow(dimension) {
    if (!clipIntersects(-80, 96, -80, 240)) return;
    for (let x = -64; x <= 80; x += 4) {
        for (let z = -64; z <= 224; z += 4) {
            if (hashPct(x, z, 73) < 18) continue;
            if (Math.hypot(x, z - PORTAL.z) < 32) continue;
            if (Math.hypot(x, z - SPAWN.z) < 24) continue;
            const region = regionFor({ x, y: GROUND_Y, z });
            if (region !== "meadow") continue;
            const choices = FLOWERS.meadow;
            for (let dx = 0; dx < 2; dx++) {
                for (let dz = 0; dz < 2; dz++) {
                    const key = choices[hashPct(x + dx, z + dz, 79) % choices.length];
                    placeFlower(dimension, x + dx, z + dz, key);
                }
            }
        }
        await tick();
    }

    for (let i = 0; i < 32; i++) {
        const angle = (i / 32) * Math.PI * 2 + 0.4;
        const radius = 24 + (hashPct(i, 83, 14) % 22);
        const x = Math.round(Math.cos(angle) * radius);
        const z = Math.round(PORTAL.z + Math.sin(angle) * radius);
        if (regionFor({ x, y: GROUND_Y, z }) !== "meadow") continue;
        if (!isGround(typeAt(dimension, x, 64, z)) || !isAirType(typeAt(dimension, x, 65, z))) continue;
        const giant = ["giant_sunflower", "giant_rosequartz", "giant_skybell", "giant_emberbloom"][i % 4];
        place(dimension, x, 65, z, `bl:${giant}`);
    }

    for (let i = 0; i < 40; i++) {
        const x = -56 + (hashPct(i, 89, 15) % 136);
        const z = 0 + (hashPct(i, 97, 16) % 192);
        if (Math.hypot(x, z - PORTAL.z) < 34) continue;
        if (Math.hypot(x, z - SPAWN.z) < 26) continue;
        if (regionFor({ x, y: GROUND_Y, z }) !== "meadow") continue;
        placeFlower(dimension, x, z, "lumen_bell");
        if (i % 2 === 0) placeFlower(dimension, x + 1, z, "dewgrass");
    }
    await tick();
}

async function buildEdge(dimension) {
    for (let i = 0; i < 30; i++) {
        const angle = (i / 30) * Math.PI * 2;
        const radius = 204 + (hashPct(i, 101, 17) % 3);
        const x = Math.round(Math.cos(angle) * radius);
        const z = Math.round(Math.sin(angle) * radius);
        if (!isGround(typeAt(dimension, x, 64, z)) || !isAirType(typeAt(dimension, x, 65, z))) continue;
        const giant = ["giant_sunflower", "giant_rosequartz", "giant_skybell", "giant_lumen"][i % 4];
        place(dimension, x, 65, z, `bl:${giant}`);
        if (i % 2 === 0) placeFlower(dimension, x + 1, z, "lumen_bell");
    }
    for (let i = 0; i < 24; i++) {
        const angle = (i / 24) * Math.PI * 2 + 0.2;
        const x = Math.round(Math.cos(angle) * 228);
        const z = Math.round(Math.sin(angle) * 228);
        if (typeAt(dimension, x, 64, z) === "bl:bloom_stone" && isAirType(typeAt(dimension, x, 65, z))) {
            place(dimension, x, 65, z, "bl:lumen_bell");
        }
    }
    await tick();
}

async function buildFloatingIsland(dimension, cx, top, cz, radius, variant) {
    await disc(dimension, cx, cz, radius, top - 3, top - 1, "bl:bloom_stone", 0);
    await disc(dimension, cx, cz, radius, top, top, "bl:petal_grass", 0);
    for (let k = 1; k <= 4; k++) {
        const r = Math.max(1, radius - k * 1.6);
        await disc(dimension, cx, cz, r, top - 3 - k, top - 3 - k, "bl:bloom_stone", 0);
    }
    place(dimension, cx, top + 1, cz, `bl:giant_${variant}`);
    for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        const x = Math.round(cx + Math.cos(angle) * (radius - 2));
        const z = Math.round(cz + Math.sin(angle) * (radius - 2));
        placeFlowerAt(dimension, x, top, z, i % 2 ? "lumen_bell" : "skybell");
    }
    for (let i = 0; i < 4; i++) {
        const angle = Math.PI / 4 + (i * Math.PI) / 2;
        const x = Math.round(cx + Math.cos(angle) * (radius - 1));
        const z = Math.round(cz + Math.sin(angle) * (radius - 1));
        if (isAirType(typeAt(dimension, x, top + 1, z))) {
            place(dimension, x, top + 1, z, "bl:glowbud_leaves");
        }
    }
}

async function buildFloatingIslands(dimension) {
    await buildFloatingIsland(dimension, 104, 110, -80, 14, "lumen");
    await buildFloatingIsland(dimension, -72, 120, 80, 10, "skybell");
    await buildFloatingIsland(dimension, 176, 100, -136, 8, "amethyst");
    await tick();
}

function regionFor(location) {
    const distance = Math.hypot(location.x, location.z);
    if (distance > 192) return "edge";
    if (location.z < -80) return "canopy";
    if (location.x > 72 && location.z > -80) return "garden";
    if (location.x < -64 && location.z < 40) return "hills";
    if (location.x < -64) return "pool";
    return "meadow";
}

function setRegionFog(player, region) {
    try {
        player.fogSettings.remove(FOG_TAG);
        player.fogSettings.push(REGIONS[region].fog, FOG_TAG);
        return true;
    } catch {
        return false;
    }
}

function clearRegionFog(player) {
    try {
        player.fogSettings.remove(FOG_TAG);
    } catch {
        // Ignore.
    }
}

function spawnBurst(dimension, location) {
    try {
        dimension.spawnParticle("bl:portal_burst", location);
        dimension.spawnParticle("bl:portal_charge", {
            x: location.x,
            y: location.y + 0.4,
            z: location.z,
        });
    } catch {
        // Cosmetic.
    }
}

function playPortalSound(player) {
    sound(player, "block.amethyst_block.chime", 0.7, 1.4);
    sound(player, "random.orb", 0.6, 1.2);
}

function tileName(ix, iz) {
    return `blsetup${ix}${iz}`;
}

function tileArea(ix, iz) {
    const ox = TILE_ORIGINS[ix];
    const oz = TILE_ORIGINS[iz];
    return {
        minX: ox - TILE_MARGIN,
        maxX: ox + TILE_CORE - 1 + TILE_MARGIN,
        minZ: oz - TILE_MARGIN,
        maxZ: oz + TILE_CORE - 1 + TILE_MARGIN,
    };
}

function clearGenerationAreas(dimension) {
    removeTickingArea(dimension, "bloomsetup");
    removeTickingArea(dimension, "bloomspawn");
    for (let ix = 0; ix < TILE_ORIGINS.length; ix++) {
        for (let iz = 0; iz < TILE_ORIGINS.length; iz++) {
            removeTickingArea(dimension, tileName(ix, iz));
        }
    }
}

async function generateIsland() {
    const dimension = await requireDimension();
    clearGenerationAreas(dimension);

    const generated = world.getDynamicProperty(GENERATED_KEY);
    if (generated === true || generated === "true") {
        // The island is saved.  Only the arrival/return window needs to be
        // loaded, and rebuilding it is safe even if a player landscaped nearby.
        const spawnArea = {
            minX: SPAWN_AREA_FROM.x,
            maxX: SPAWN_AREA_TO.x,
            minZ: SPAWN_AREA_FROM.z,
            maxZ: SPAWN_AREA_TO.z,
        };
        const ready = await addTickingArea(dimension, "bloomspawn", SPAWN_AREA_FROM, SPAWN_AREA_TO);
        if (!ready) throw new Error("could not create the spawn ticking area");
        await waitForChunks(dimension, spawnArea);
        await ensureSpawnPlatform(dimension);
        await buildReturnPortal(dimension);
        return;
    }

    state.fillFailures = 0;
    const tiles = [];
    for (let ix = 0; ix < TILE_ORIGINS.length; ix++) {
        for (let iz = 0; iz < TILE_ORIGINS.length; iz++) {
            if (ix === 2 && iz === 2) continue;
            tiles.push([ix, iz]);
        }
    }
    // Finish with the central 8x8-chunk core so the arrival and return areas
    // are loaded while their ground probes are checked.
    tiles.push([2, 2]);

    for (const [ix, iz] of tiles) {
        const area = tileArea(ix, iz);
        const name = tileName(ix, iz);
        const ready = await addTickingArea(
            dimension,
            name,
            { x: area.minX, y: 0, z: area.minZ },
            { x: area.maxX, y: 128, z: area.maxZ },
        );
        if (!ready) throw new Error(`could not create ticking area ${name}`);
        await waitForChunks(dimension, area);
        state.genClip = area;
        try {
            await buildBase(dimension);
            await buildHills(dimension);
            await buildLake(dimension);
            await buildForest(dimension);
            await buildGarden(dimension);
            await buildPaths(dimension);
            await buildMeadow(dimension);
            await buildEdge(dimension);
            await buildFloatingIslands(dimension);
            await ensureSpawnPlatform(dimension);
            await buildReturnPortal(dimension);

            // Probe a point in every 8x8-chunk core that is guaranteed to be
            // inside the island. This catches a pass whose ticking area failed
            // to load, while the central probe below checks the arrival area.
            const ox = TILE_ORIGINS[ix];
            const oz = TILE_ORIGINS[iz];
            const px = Math.max(ox, Math.min(0, ox + TILE_CORE - 1));
            const pz = Math.max(oz, Math.min(0, oz + TILE_CORE - 1));
            const probe = typeAt(dimension, px, GROUND_Y, pz);
            if (probe === undefined || isAirType(probe)) {
                throw new Error(`generation probe ${px},${pz} is missing in tile ${name}`);
            }

            if (ix === 2 && iz === 2 && !isLandBuilt(dimension)) {
                throw new Error("central island ground probes are missing after generation");
            }
        } finally {
            state.genClip = null;
            removeTickingArea(dimension, name);
        }
        await system.waitTicks(2);
    }

    world.setDynamicProperty(GENERATED_KEY, true);

    const spawnArea = {
        minX: SPAWN_AREA_FROM.x,
        maxX: SPAWN_AREA_TO.x,
        minZ: SPAWN_AREA_FROM.z,
        maxZ: SPAWN_AREA_TO.z,
    };
    const spawnReady = await addTickingArea(dimension, "bloomspawn", SPAWN_AREA_FROM, SPAWN_AREA_TO);
    if (!spawnReady) throw new Error("could not create the spawn ticking area");
    await waitForChunks(dimension, spawnArea);
    await ensureSpawnPlatform(dimension);
    await buildReturnPortal(dimension);
    warn("island generation complete", `fill failures: ${state.fillFailures}`);
}

async function ensureIsland() {
    if (state.islandPromise) return state.islandPromise;
    state.islandPromise = generateIsland().catch((error) => {
        state.islandPromise = null;
        throw error;
    });
    return state.islandPromise;
}

function safeY(dimension, x, y, z) {
    const base = Math.floor(Number.isFinite(y) ? y : 64);
    for (let offset = 0; offset <= 12; offset++) {
        const yy = base + offset;
        const feet = typeAt(dimension, x, yy, z);
        const head = typeAt(dimension, x, yy + 1, z);
        if (feet !== undefined && head !== undefined && isAirType(feet) && isAirType(head)) {
            return yy + 0.1;
        }
    }
    return base + 2;
}

function loadReturn(player) {
    const raw = player.getDynamicProperty(RETURN_KEY);
    if (typeof raw === "string") {
        try {
            const parsed = JSON.parse(raw);
            if (
                parsed &&
                typeof parsed.dimension === "string" &&
                Number.isFinite(parsed.x) &&
                Number.isFinite(parsed.y) &&
                Number.isFinite(parsed.z)
            ) {
                return parsed;
            }
        } catch {
            // Fall through to the spawn point.
        }
    }

    try {
        const spawn = player.getSpawnPoint();
        if (spawn && spawn.dimension) {
            return {
                dimension: spawn.dimension.id,
                x: spawn.x + 0.5,
                y: spawn.y + 1,
                z: spawn.z + 0.5,
            };
        }
    } catch {
        // Fall through.
    }

    const spawn = world.getDefaultSpawnLocation();
    const y = Number.isFinite(spawn.y) && spawn.y < 300 ? spawn.y : 64;
    return {
        dimension: "minecraft:overworld",
        x: spawn.x + 0.5,
        y,
        z: spawn.z + 0.5,
    };
}

function saveReturn(player) {
    const location = player.location;
    const value = {
        dimension: player.dimension.id,
        x: location.x,
        y: location.y,
        z: location.z,
    };
    try {
        player.setDynamicProperty(RETURN_KEY, JSON.stringify(value));
    } catch {
        // Dynamic properties can fail if the player is leaving.
    }
}

async function enterBloomlands(player) {
    message(player, "bl.portal.enter");
    playPortalSound(player);
    // Remember where the player stood before any generation wait.
    saveReturn(player);

    let dimension;
    try {
        dimension = await requireDimension();
        await ensureIsland();
    } catch (error) {
        warn("unable to open dimension", String(error));
        message(player, "bl.portal.failed");
        return false;
    }

    try {
        player.teleport(
            SPAWN,
            {
                dimension,
                checkForBlocks: false,
                keepVelocity: false,
                facingLocation: {
                    x: PORTAL.x + 0.5,
                    y: 65,
                    z: PORTAL.z + 0.5,
                },
            },
        );
    } catch (error) {
        warn("teleport into Bloomlands failed", String(error));
        message(player, "bl.portal.failed");
        return false;
    }

    const stateValue = getPlayerState(player);
    stateValue.fogSet = false;
    stateValue.lastRegion = "";
    stateValue.heartDisarmed = true;
    stateValue.cooldownUntil = system.currentTick + 120;

    spawnBurst(dimension, { x: SPAWN.x, y: SPAWN.y + 0.2, z: SPAWN.z });
    title(player, "bl.title.bloomlands", "bl.subtitle.bloomlands");
    actionBar(player, "bl.portal.enter");
    sound(player, "random.orb", 0.8, 1.3);
    return true;
}

async function leaveBloomlands(player) {
    const saved = loadReturn(player);
    // A spawn point inside the dimension would otherwise send the player
    // straight back into the garden instead of home.
    if (saved.dimension === DIMENSION_ID) {
        saved.dimension = "minecraft:overworld";
    }
    let target;
    try {
        target = world.getDimension(saved.dimension);
    } catch {
        target = undefined;
    }
    if (!target) {
        message(player, "bl.portal.no_return");
        target = world.getDimension("minecraft:overworld");
    }

    const y = safeY(target, saved.x, saved.y, saved.z);
    try {
        player.teleport(
            { x: saved.x, y, z: saved.z },
            {
                dimension: target,
                checkForBlocks: false,
                keepVelocity: false,
            },
        );
    } catch (error) {
        warn("teleport home failed", String(error));
        message(player, "bl.portal.failed");
        return false;
    }

    const stateValue = getPlayerState(player);
    stateValue.cooldownUntil = system.currentTick + 120;
    stateValue.heartDisarmed = true;
    stateValue.lastRegion = "";
    stateValue.fogSet = false;
    clearRegionFog(player);

    actionBar(player, "bl.portal.return");
    playPortalSound(player);
    return true;
}

async function activatePortal(player) {
    if (state.teleporting.has(player.id)) return;

    const stateValue = getPlayerState(player);
    const now = system.currentTick;
    if (now < stateValue.cooldownUntil) {
        if (player.dimension.id === DIMENSION_ID) {
            actionBar(player, "bl.portal.cooldown");
        }
        return;
    }

    state.teleporting.add(player.id);
    stateValue.cooldownUntil = now + 140;
    stateValue.heartDisarmed = true;

    let arrived = false;
    try {
        if (player.dimension.id === DIMENSION_ID) {
            arrived = await leaveBloomlands(player);
        } else {
            arrived = await enterBloomlands(player);
        }
    } catch (error) {
        warn("portal activation failed", String(error));
        message(player, "bl.portal.failed");
        stateValue.cooldownUntil = system.currentTick + 40;
    } finally {
        if (!arrived) stateValue.heartDisarmed = false;
        // Keep the lock for the whole operation, including a long first-time
        // island build. The cooldown below is enough once the teleport ends.
        state.teleporting.delete(player.id);
    }
}

function consumePortalItem(player) {
    try {
        if (player.getGameMode() === "creative") return;
        const inventory = player.getComponent("minecraft:inventory");
        const container = inventory ? inventory.container : undefined;
        if (!container) return;
        for (let slot = 0; slot < container.size; slot++) {
            const item = container.getItem(slot);
            if (item && item.typeId === PORTAL_ITEM) {
                if (item.amount > 1) {
                    item.amount--;
                    container.setItem(slot, item);
                } else {
                    container.setItem(slot, undefined);
                }
                return;
            }
        }
    } catch {
        // If the inventory is unavailable the portal is still built.
    }
}

async function buildPortal(player, block) {
    if (state.building.has(player.id)) return;
    state.building.add(player.id);

    try {
        const dimension = player.dimension;
        const baseX = block.location.x;
        const baseY = block.location.y;
        const baseZ = block.location.z;

        for (let dx = -3; dx <= 3; dx++) {
            for (let dz = -3; dz <= 3; dz++) {
                const ground = typeAt(dimension, baseX + dx, baseY, baseZ + dz);
                if (ground === undefined) {
                    actionBar(player, "bl.portal.no_room");
                    return;
                }
                if (!isAirType(ground) && !PORTAL_GROUND.has(ground)) {
                    actionBar(player, "bl.portal.no_room");
                    return;
                }
                const above = typeAt(dimension, baseX + dx, baseY + 1, baseZ + dz);
                if (above === undefined || (!isAirType(above) && !isPlant(above))) {
                    actionBar(player, "bl.portal.no_room");
                    return;
                }
                const higher = typeAt(dimension, baseX + dx, baseY + 2, baseZ + dz);
                if (higher === undefined || (!isAirType(higher) && !isPlant(higher))) {
                    actionBar(player, "bl.portal.no_room");
                    return;
                }
            }
        }

        fill(dimension, baseX - 3, baseY, baseZ - 3, baseX + 3, baseY, baseZ + 3, "bl:petal_path");
        fill(dimension, baseX - 3, baseY + 1, baseZ - 3, baseX + 3, baseY + 1, baseZ + 3, "minecraft:air");

        for (const [dx, dz] of RING) {
            place(dimension, baseX + dx, baseY + 1, baseZ + dz, "bl:portal_flower");
        }
        place(dimension, baseX, baseY, baseZ, HEART);

        consumePortalItem(player);
        const stateValue = getPlayerState(player);
        stateValue.cooldownUntil = system.currentTick + 80;
        stateValue.heartDisarmed = false;

        spawnBurst(dimension, { x: baseX + 0.5, y: baseY + 1.2, z: baseZ + 0.5 });
        try {
            dimension.spawnParticle("bl:portal_aura", {
                x: baseX + 0.5,
                y: baseY + 1.8,
                z: baseZ + 0.5,
            });
        } catch {
            // Cosmetic.
        }
        playPortalSound(player);
        actionBar(player, "bl.portal.ready");
        sound(player, "block.amethyst_block.chime", 0.8, 1.2);
    } catch (error) {
        warn("portal build failed", String(error));
        actionBar(player, "bl.portal.failed");
    } finally {
        system.runTimeout(() => {
            state.building.delete(player.id);
        }, 20);
    }
}

function cleanupHostiles(dimension) {
    const entities = new Map();
    try {
        for (const entity of dimension.getEntities({ families: ["monster"] })) {
            entities.set(entity.id, entity);
        }
    } catch {
        // The family query can fail while chunks are unloading.
    }
    try {
        for (const entity of dimension.getEntities({})) {
            if (HOSTILE_TYPES.has(entity.typeId)) entities.set(entity.id, entity);
        }
    } catch {
        // Ignore.
    }
    for (const entity of entities.values()) {
        try {
            entity.remove();
        } catch {
            // It may already be gone.
        }
    }
}

function findGroundY(dimension, x, z, from = 118, to = 40) {
    const ix = Math.floor(x);
    const iz = Math.floor(z);
    for (let y = from; y >= to; y--) {
        const type = typeAt(dimension, ix, y, iz);
        if (type === "minecraft:water" || type === "minecraft:lava") return -1;
        if (type !== undefined && isGround(type)) return y;
    }
    return -1;
}

function clearForMob(dimension, x, y, z) {
    return isAirType(typeAt(dimension, x, y, z)) && isAirType(typeAt(dimension, x, y + 1, z));
}

function chooseMob(region) {
    const roll = Math.random();
    if (region === "canopy") {
        return roll < 0.5 ? "bl:mossling" : roll < 0.8 ? "bl:dewdrop_snail" : "bl:petalwing";
    }
    if (region === "pool") {
        return roll < 0.5 ? "bl:dewdrop_snail" : roll < 0.8 ? "bl:petalwing" : "bl:mossling";
    }
    if (region === "garden") {
        return roll < 0.5 ? "bl:petalwing" : roll < 0.75 ? "bl:mossling" : "bl:dewdrop_snail";
    }
    if (region === "hills") {
        return roll < 0.4 ? "bl:petalwing" : roll < 0.7 ? "bl:mossling" : "bl:dewdrop_snail";
    }
    return roll < 0.4 ? "bl:petalwing" : roll < 0.8 ? "bl:mossling" : "bl:dewdrop_snail";
}

function populateMobs(dimension) {
    const players = dimension.getPlayers();
    if (players.length === 0) return;
    let mobs;
    try {
        mobs = dimension.getEntities({ families: ["bloomling"] });
    } catch {
        return;
    }
    if (mobs.length >= 32) return;

    const player = players[Math.floor(Math.random() * players.length)];
    for (let attempt = 0; attempt < 20; attempt++) {
        const angle = Math.random() * Math.PI * 2;
        const distance = 12 + Math.random() * 48;
        const x = player.location.x + Math.cos(angle) * distance;
        const z = player.location.z + Math.sin(angle) * distance;
        const ground = findGroundY(dimension, x, z);
        if (ground < 0) continue;
        if (Math.abs(ground - player.location.y) > 32) continue;

        const type = chooseMob(regionFor({ x, y: ground, z }));
        let y;
        if (type === "bl:petalwing") {
            y = ground + 2 + Math.random() * 3;
        } else {
            y = ground + 1;
        }
        if (!clearForMob(dimension, x, y, z)) continue;

        try {
            const nearby = dimension.getEntities({
                location: { x, y, z },
                maxDistance: 3,
                families: ["bloomling"],
            });
            if (nearby.length > 0) continue;
        } catch {
            // Ignore a failed proximity query.
        }

        try {
            const entity = dimension.spawnEntity(type, { x, y, z });
            if (entity) {
                try {
                    entity.addTag("bl:wild");
                } catch {
                    // Tags are optional.
                }
                return;
            }
        } catch {
            // Try another spot.
        }
    }
}

function rescueMobs(dimension) {
    let mobs;
    try {
        mobs = dimension.getEntities({ families: ["bloomling"] });
    } catch {
        return;
    }
    for (const mob of mobs) {
        try {
            if (mob.location.y >= 24) continue;
            const isFlying = mob.typeId === "bl:petalwing";
            mob.teleport(
                {
                    x: SPAWN.x + (Math.random() - 0.5) * 6,
                    y: isFlying ? SPAWN.y + 3 : SPAWN.y,
                    z: SPAWN.z + (Math.random() - 0.5) * 6,
                },
                { dimension, checkForBlocks: false, keepVelocity: false },
            );
        } catch {
            // It may be invalid.
        }
    }
}

function ambientParticles(dimension) {
    const players = dimension.getPlayers();
    if (players.length === 0) return;

    for (const player of players) {
        const location = player.location;
        const region = regionFor(location);
        const def = REGIONS[region];
        let effect = def.particle;
        let x = location.x + (Math.random() - 0.5) * 12;
        let z = location.z + (Math.random() - 0.5) * 12;
        let y = location.y + 0.3 + Math.random() * 3.5;

        if (region === "pool") {
            // Find a nearby water surface for the ripple.
            let found = false;
            for (let attempt = 0; attempt < 5; attempt++) {
                const wx = Math.round(location.x + (Math.random() - 0.5) * 14);
                const wz = Math.round(location.z + (Math.random() - 0.5) * 14);
                if (typeAt(dimension, wx, 64, wz) === "minecraft:water" && isAirType(typeAt(dimension, wx, 65, wz))) {
                    x = wx + 0.5;
                    z = wz + 0.5;
                    y = 65.2;
                    found = true;
                    break;
                }
            }
            if (!found) effect = "bl:petal_mote";
        }

        if (region === "canopy" && Math.random() < 0.35) {
            effect = "bl:canopy_mote";
        }

        try {
            dimension.spawnParticle(effect, { x, y, z });
            if (region === "canopy" && Math.random() < 0.4) {
                dimension.spawnParticle("bl:firefly", {
                    x: location.x + (Math.random() - 0.5) * 10,
                    y: location.y + 1 + Math.random() * 3,
                    z: location.z + (Math.random() - 0.5) * 10,
                });
            }
        } catch {
            // Particles are cosmetic.
        }

        if (Math.hypot(location.x - PORTAL.x, location.z - PORTAL.z) < 34 && Math.random() < 0.45) {
            try {
                dimension.spawnParticle("bl:portal_aura", {
                    x: PORTAL.x + 0.5,
                    y: PORTAL.y + 1.4,
                    z: PORTAL.z + 0.5,
                });
            } catch {
                // Cosmetic.
            }
        }
    }
}

function rescuePlayerIfNeeded(player, dimension) {
    // The island surface is at Y=64. Catch falls before they become lethal.
    if (player.location.y >= 48) return false;
    const stateValue = getPlayerState(player);
    try {
        player.teleport(
            SPAWN,
            {
                dimension,
                checkForBlocks: false,
                keepVelocity: false,
                facingLocation: {
                    x: PORTAL.x + 0.5,
                    y: 65,
                    z: PORTAL.z + 0.5,
                },
            },
        );
        stateValue.fogSet = false;
        stateValue.lastRegion = "";
        stateValue.heartDisarmed = true;
        stateValue.cooldownUntil = system.currentTick + 80;
        actionBar(player, "bl.voidrescue");
        spawnBurst(dimension, { x: SPAWN.x, y: SPAWN.y + 0.2, z: SPAWN.z });
        sound(player, "random.orb", 0.6, 1.5);
    } catch {
        // It may be too late to save this tick.
    }
    return true;
}

function managePlayer(player, dimension) {
    const inBloomlands = player.dimension.id === DIMENSION_ID;
    const stateValue = getPlayerState(player);

    if (!inBloomlands) {
        if (stateValue.fogSet) {
            clearRegionFog(player);
            stateValue.fogSet = false;
        }
        stateValue.lastRegion = "";
        const heart = typeAt(
            player.dimension,
            Math.floor(player.location.x),
            Math.floor(player.location.y) - 1,
            Math.floor(player.location.z),
        );
        if (heart === HEART) {
            if (!stateValue.heartDisarmed && system.currentTick >= stateValue.cooldownUntil) {
                void activatePortal(player);
            }
        } else {
            stateValue.heartDisarmed = false;
        }
        return;
    }

    if (rescuePlayerIfNeeded(player, dimension)) return;

    const region = regionFor(player.location);
    if (!stateValue.fogSet || region !== stateValue.lastRegion) {
        const pushed = setRegionFog(player, region);
        if (pushed) stateValue.fogSet = true;
        const now = system.currentTick;
        if (region !== stateValue.lastRegion && now - stateValue.lastRegionAt > 40) {
            actionBar(player, REGIONS[region].title);
            stateValue.lastRegionAt = now;
        }
        stateValue.lastRegion = region;
    }

    const heart = typeAt(
        dimension,
        Math.floor(player.location.x),
        Math.floor(player.location.y) - 1,
        Math.floor(player.location.z),
    );
    if (heart === HEART) {
        if (!stateValue.heartDisarmed && system.currentTick >= stateValue.cooldownUntil) {
            void activatePortal(player);
        }
    } else {
        // Stepping off a Bloomheart re-arms it for the next visit.
        stateValue.heartDisarmed = false;
    }
}

function tickWorld() {
    const dimension = bloomDimension();
    if (!dimension) return;
    const now = system.currentTick;

    for (const player of world.getAllPlayers()) {
        try {
            managePlayer(player, dimension);
        } catch (error) {
            warn("player management failed", String(error));
        }
    }

    if (now - state.lastHostile >= 40) {
        state.lastHostile = now;
        cleanupHostiles(dimension);
    }
    if (now - state.lastMob >= 200) {
        state.lastMob = now;
        try {
            populateMobs(dimension);
        } catch (error) {
            warn("mob population failed", String(error));
        }
    }
    if (now - state.lastMobRescue >= 100) {
        state.lastMobRescue = now;
        rescueMobs(dimension);
    }
    if (now - state.lastAmbient >= 20) {
        state.lastAmbient = now;
        ambientParticles(dimension);
    }
}

async function initialize() {
    for (let attempt = 0; attempt < 3; attempt++) {
        try {
            await ensureIsland();
            return;
        } catch (error) {
            warn("island initialization failed", String(error));
            await system.waitTicks(200);
        }
    }
}

world.afterEvents.worldLoad.subscribe(() => {
    if (state.initialized) return;
    state.initialized = true;
    system.runTimeout(() => {
        void initialize();
    }, 20);
});

system.runTimeout(() => {
    if (state.initialized) return;
    state.initialized = true;
    void initialize();
}, 80);

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
    try {
        if (event.isFirstEvent === false) return;
        const player = event.player;
        const block = event.block;
        if (!player || !block) return;

        if (block.typeId === HEART) {
            const stateValue = getPlayerState(player);
            const standingOnHeart = typeAt(
                player.dimension,
                Math.floor(player.location.x),
                Math.floor(player.location.y) - 1,
                Math.floor(player.location.z),
            ) === HEART;
            if (standingOnHeart && stateValue.heartDisarmed) {
                actionBar(player, "bl.portal.rearm");
                return;
            }
            if (system.currentTick < stateValue.cooldownUntil) {
                actionBar(player, "bl.portal.cooldown");
                return;
            }
            void activatePortal(player);
            return;
        }

        if (event.itemStack && event.itemStack.typeId === PORTAL_ITEM) {
            if (String(event.blockFace).toLowerCase() !== "up") {
                actionBar(player, "bl.portal.ground");
                return;
            }
            void buildPortal(player, block);
        }
    } catch (error) {
        warn("interaction failed", String(error));
    }
});

// The return Bloomheart is the only guaranteed way home from the dimension.
// Keep it rooted so a curious player cannot strand themselves on the island.
world.beforeEvents.playerBreakBlock?.subscribe((event) => {
    try {
        if (event.block.typeId !== HEART) return;
        if (event.block.dimension.id !== DIMENSION_ID) return;
        const location = event.block.location;
        if (
            location.x !== PORTAL.x ||
            location.y !== PORTAL.y ||
            location.z !== PORTAL.z
        ) {
            return;
        }
        event.cancel = true;
        actionBar(event.player, "bl.portal.rooted");
    } catch {
        // Before-events can be unavailable while the world is shutting down.
    }
});

world.afterEvents.playerSpawn.subscribe((event) => {
    try {
        const stateValue = getPlayerState(event.player);
        stateValue.fogSet = false;
        stateValue.lastRegion = "";
        stateValue.heartDisarmed = false;
        stateValue.cooldownUntil = Math.max(stateValue.cooldownUntil, system.currentTick + 40);
    } catch {
        // Ignore.
    }
});

world.afterEvents.playerLeave.subscribe((event) => {
    state.players.delete(event.playerId);
    state.building.delete(event.playerId);
    state.teleporting.delete(event.playerId);
});

system.runInterval(() => {
    try {
        tickWorld();
    } catch (error) {
        warn("world tick failed", String(error));
    }
}, 10);
