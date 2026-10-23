/*
 * Drone Companion - Bedrock Edition
 * ================================
 * The Drone Controller summons a small hovering quadcopter.  The controller's
 * form gives the drone orders: Follow, Stay, Come, Scan, Light and Defend.
 *
 * The drone is script-driven: it has no gravity or collision, and its position
 * is updated every two ticks.  This keeps it stable around the player without
 * needing a custom navigation component.
 *
 * REQUIREMENTS
 *   Minecraft Bedrock 1.21.90+ (Script API 2.x).
 *   The behavior pack manifest declares @minecraft/server 2.0.0 and
 *   @minecraft/server-ui 2.0.0.
 */

import { world, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

const CONTROLLER_ID = "drone:controller";
const DRONE_ID = "drone:companion";
const OWNER_PROPERTY = "drone:owner";
const MODE_PROPERTY = "drone:mode";
const PLAYER_DRONE_PROPERTY = "drone:companion_id";

const HOVER_HEIGHT = 2.1;
const FOLLOW_BACK = 1.4;
const FOLLOW_SIDE = 0.9;
const MAX_FOLLOW_DISTANCE = 28;
const SCAN_RADIUS = 12;
const DEFEND_RADIUS = 10;
const LOOP_INTERVAL = 2; // game ticks between script updates
const TICKS_PER_SECOND = 10; // LOOP_INTERVAL increments per second
const USE_COOLDOWN = 3; // loop increments, not game ticks

const states = new Map(); // player.id -> drone state
const lastUse = new Map(); // player.id -> loop tick of last controller use
let loopTick = 0;

// --------------------------------------------------------------------------- //
// Small helpers
// --------------------------------------------------------------------------- //
function isEntityValid(entity) {
  if (!entity) {
    return false;
  }
  try {
    const valid = entity.isValid;
    if (typeof valid === "function") {
      return Boolean(valid.call(entity));
    }
    return valid === true;
  } catch (error) {
    return false;
  }
}

function getHealth(entity) {
  try {
    const health = entity.getComponent("minecraft:health");
    return health ? Number(health.currentValue) : 0;
  } catch (error) {
    return 0;
  }
}

function copyLocation(location) {
  return { x: location.x, y: location.y, z: location.z };
}

function distanceBetween(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

function lerpLocation(a, b, amount) {
  return {
    x: a.x + (b.x - a.x) * amount,
    y: a.y + (b.y - a.y) * amount,
    z: a.z + (b.z - a.z) * amount
  };
}

function getViewDirection(player) {
  try {
    const direction = player.getViewDirection();
    return {
      x: Number(direction.x) || 0,
      y: Number(direction.y) || 0,
      z: Number(direction.z) || 0
    };
  } catch (error) {
    return { x: 0, y: 0, z: 1 };
  }
}

function horizontalForward(player) {
  const direction = getViewDirection(player);
  const length = Math.hypot(direction.x, direction.z);
  if (length < 0.001) {
    return { x: 0, z: 1 };
  }
  return { x: direction.x / length, z: direction.z / length };
}

function yawFromVector(vector) {
  const degrees = (Math.atan2(-vector.x, vector.z) * 180) / Math.PI;
  return ((degrees % 360) + 360) % 360;
}

function yawToward(from, to) {
  return yawFromVector({ x: to.x - from.x, z: to.z - from.z });
}

function actionBar(player, text) {
  try {
    player.onScreenDisplay.setActionBar(text);
  } catch (error) {
    /* the player may have disconnected */
  }
}

function getDimensions() {
  const dimensions = [];
  const seen = new Set();
  const ids = [
    "minecraft:overworld",
    "minecraft:nether",
    "minecraft:the_end",
    "overworld",
    "nether",
    "the_end"
  ];
  for (const id of ids) {
    try {
      const dimension = world.getDimension(id);
      if (dimension && !seen.has(dimension.id)) {
        seen.add(dimension.id);
        dimensions.push(dimension);
      }
    } catch (error) {
      /* dimension not available */
    }
  }
  return dimensions;
}

function getEntityById(id) {
  if (!id) {
    return undefined;
  }
  try {
    return world.getEntity(id);
  } catch (error) {
    return undefined;
  }
}

function getOwnerId(entity) {
  try {
    const owner = entity.getDynamicProperty(OWNER_PROPERTY);
    return typeof owner === "string" ? owner : "";
  } catch (error) {
    return "";
  }
}

function getPlayerDroneId(player) {
  try {
    const id = player.getDynamicProperty(PLAYER_DRONE_PROPERTY);
    return typeof id === "string" ? id : "";
  } catch (error) {
    return "";
  }
}

function setPlayerDroneId(player, id) {
  try {
    player.setDynamicProperty(PLAYER_DRONE_PROPERTY, id || "");
  } catch (error) {
    /* dynamic properties may be unavailable in some worlds */
  }
}

function setDroneMode(state, mode) {
  state.mode = mode;
  if (mode !== "stay") {
    state.stayLocation = undefined;
  }
  try {
    state.entity.setDynamicProperty(MODE_PROPERTY, mode);
  } catch (error) {
    /* the entity may have been removed */
  }
}

// --------------------------------------------------------------------------- //
// Drone discovery and state
// --------------------------------------------------------------------------- //
function findOwnedDrone(player) {
  for (const dimension of getDimensions()) {
    let entities = [];
    try {
      entities = dimension.getEntities({ type: DRONE_ID });
    } catch (error) {
      continue;
    }
    for (const entity of entities) {
      if (isEntityValid(entity) && getOwnerId(entity) === player.id) {
        return entity;
      }
    }
  }
  return undefined;
}

function createState(player, drone) {
  const existing = states.get(player.id);
  if (existing && existing.entity && existing.entity.id === drone.id) {
    return existing;
  }
  if (existing) {
    removeLight(existing);
  }

  let mode = "follow";
  try {
    const savedMode = drone.getDynamicProperty(MODE_PROPERTY);
    if (savedMode === "follow" || savedMode === "stay" || savedMode === "come" || savedMode === "scan") {
      mode = savedMode;
    }
  } catch (error) {
    /* use the default */
  }

  const state = {
    ownerId: player.id,
    entity: drone,
    mode,
    stayLocation: mode === "stay" ? copyLocation(drone.location) : undefined,
    light: false,
    lightPos: undefined,
    lightDimension: undefined,
    lightType: undefined,
    defend: false,
    nextScanTick: 0,
    nextDefendTick: 0
  };

  states.set(player.id, state);
  setPlayerDroneId(player, drone.id);
  return state;
}

function ensureState(player) {
  let state = states.get(player.id);
  if (state && isEntityValid(state.entity)) {
    return state;
  }
  if (state) {
    removeLight(state);
    states.delete(player.id);
  }

  const storedId = getPlayerDroneId(player);
  const stored = getEntityById(storedId);
  if (stored && isEntityValid(stored) && getOwnerId(stored) === player.id) {
    return createState(player, stored);
  }
  if (storedId) {
    setPlayerDroneId(player, "");
  }

  const owned = findOwnedDrone(player);
  if (owned) {
    return createState(player, owned);
  }
  return undefined;
}

function rebuildStates() {
  const players = new Map(world.getPlayers().map((player) => [player.id, player]));
  for (const dimension of getDimensions()) {
    let entities = [];
    try {
      entities = dimension.getEntities({ type: DRONE_ID });
    } catch (error) {
      continue;
    }
    for (const entity of entities) {
      if (!isEntityValid(entity)) {
        continue;
      }
      const ownerId = getOwnerId(entity);
      if (!ownerId || states.has(ownerId)) {
        continue;
      }
      const player = players.get(ownerId);
      if (player) {
        createState(player, entity);
      }
    }
  }
}

// --------------------------------------------------------------------------- //
// Spawning and movement
// --------------------------------------------------------------------------- //
function isOpenSpace(dimension, location) {
  try {
    const block = dimension.getBlock({
      x: Math.floor(location.x),
      y: Math.floor(location.y),
      z: Math.floor(location.z)
    });
    if (!block) {
      return true;
    }
    return block.isAir || block.isLiquid || block.typeId.startsWith("minecraft:light_block");
  } catch (error) {
    return true;
  }
}

function findSpawnLocation(player) {
  const forward = horizontalForward(player);
  const base = {
    x: player.location.x + forward.x * 1.2,
    y: player.location.y + HOVER_HEIGHT,
    z: player.location.z + forward.z * 1.2
  };
  for (let index = 0; index < 6; index += 1) {
    const candidate = { x: base.x, y: base.y + index * 0.5, z: base.z };
    if (isOpenSpace(player.dimension, candidate)) {
      return candidate;
    }
  }
  return base;
}

function followTarget(player) {
  const forward = horizontalForward(player);
  const right = { x: -forward.z, z: forward.x };
  return {
    x: player.location.x - forward.x * FOLLOW_BACK + right.x * FOLLOW_SIDE,
    y: player.location.y + HOVER_HEIGHT,
    z: player.location.z - forward.z * FOLLOW_BACK + right.z * FOLLOW_SIDE
  };
}

function safeTeleport(entity, location, dimension, yaw) {
  if (!isEntityValid(entity)) {
    return;
  }
  const options = {
    rotation: { x: 0, y: yaw }
  };
  if (dimension) {
    options.dimension = dimension;
  }
  try {
    entity.teleport(location, options);
  } catch (error) {
    /* the target chunk may be unloaded */
  }
}

function summonDrone(player) {
  const location = findSpawnLocation(player);
  let drone;
  try {
    drone = player.dimension.spawnEntity(DRONE_ID, location);
  } catch (error) {
    player.sendMessage("§cThe Drone Companion could not be summoned here.");
    return undefined;
  }
  if (!drone) {
    player.sendMessage("§cThe Drone Companion could not be summoned here.");
    return undefined;
  }

  drone.nameTag = "Drone";
  try {
    drone.setDynamicProperty(OWNER_PROPERTY, player.id);
    drone.setDynamicProperty(MODE_PROPERTY, "follow");
  } catch (error) {
    /* dynamic properties are optional; the in-memory state still works */
  }

  const state = createState(player, drone);
  setDroneMode(state, "follow");
  player.sendMessage("§bDrone Companion summoned. §7Use the controller to give orders.");
  return state;
}

// --------------------------------------------------------------------------- //
// Light block
// --------------------------------------------------------------------------- //
function removeLight(state) {
  if (!state.lightPos || !state.lightDimension || !state.lightType) {
    state.lightPos = undefined;
    state.lightDimension = undefined;
    state.lightType = undefined;
    return;
  }
  try {
    const dimension = world.getDimension(state.lightDimension);
    const block = dimension.getBlock(state.lightPos);
    if (block && block.typeId === state.lightType) {
      block.setType("minecraft:air");
    }
  } catch (error) {
    /* the chunk may be unloaded or the block already changed */
  }
  state.lightPos = undefined;
  state.lightDimension = undefined;
  state.lightType = undefined;
}

function updateLight(state, drone) {
  if (!state.light) {
    removeLight(state);
    return;
  }
  if (!isEntityValid(drone)) {
    removeLight(state);
    return;
  }

  let dimension;
  let location;
  try {
    dimension = drone.dimension;
    location = drone.location;
  } catch (error) {
    return;
  }

  const position = {
    x: Math.floor(location.x),
    y: Math.floor(location.y),
    z: Math.floor(location.z)
  };
  if (
    state.lightPos &&
    state.lightDimension === dimension.id &&
    state.lightPos.x === position.x &&
    state.lightPos.y === position.y &&
    state.lightPos.z === position.z
  ) {
    return;
  }

  removeLight(state);
  try {
    const block = dimension.getBlock(position);
    if (!block) {
      return;
    }
    if (block.isAir) {
      block.setType("minecraft:light_block_15");
      state.lightPos = position;
      state.lightDimension = dimension.id;
      state.lightType = "minecraft:light_block_15";
    }
  } catch (error) {
    /* skip this position if the chunk or block is unavailable */
  }
}

// --------------------------------------------------------------------------- //
// Scan and defend
// --------------------------------------------------------------------------- //
function scanPulse(state, player) {
  if (!isEntityValid(state.entity)) {
    return;
  }
  let dimension;
  let location;
  try {
    dimension = state.entity.dimension;
    location = state.entity.location;
  } catch (error) {
    return;
  }

  try {
    for (let index = 0; index < 8; index += 1) {
      const angle = (index / 8) * Math.PI * 2;
      dimension.spawnParticle("minecraft:endrod", {
        x: location.x + Math.cos(angle) * 2.5,
        y: location.y + 0.3,
        z: location.z + Math.sin(angle) * 2.5
      });
    }
  } catch (error) {
    /* particles are decorative */
  }

  let targets = [];
  try {
    targets = dimension.getEntities({
      families: ["monster"],
      location,
      maxDistance: SCAN_RADIUS
    });
  } catch (error) {
    return;
  }

  for (const target of targets) {
    try {
      target.addEffect("minecraft:glowing", 80, { amplifier: 0, showParticles: false });
    } catch (error) {
      /* some entities cannot receive effects */
    }
  }

  if (targets.length > 0) {
    actionBar(player, `§bScan: §f${targets.length} hostile${targets.length === 1 ? "" : "s"} highlighted`);
  } else {
    actionBar(player, "§bScan: no hostiles nearby");
  }
}

function maybeDefend(state, player) {
  if (!state.defend || loopTick < state.nextDefendTick) {
    return;
  }
  state.nextDefendTick = loopTick + TICKS_PER_SECOND;

  if (!isEntityValid(state.entity)) {
    return;
  }
  let dimension;
  let location;
  try {
    dimension = state.entity.dimension;
    location = state.entity.location;
  } catch (error) {
    return;
  }

  let targets = [];
  try {
    targets = dimension.getEntities({
      families: ["monster"],
      location,
      maxDistance: DEFEND_RADIUS,
      closest: 1
    });
  } catch (error) {
    return;
  }
  if (targets.length === 0) {
    return;
  }

  const target = targets[0];
  try {
    target.applyDamage(4);
    dimension.spawnParticle("minecraft:critical_hit_emitter", {
      x: target.location.x,
      y: target.location.y + 0.8,
      z: target.location.z
    });
    actionBar(player, `§cDefense: zapped ${target.typeId.replace("minecraft:", "")}`);
  } catch (error) {
    /* the target may have died or moved to an unloaded chunk */
  }
}

// --------------------------------------------------------------------------- //
// Main update loop
// --------------------------------------------------------------------------- //
function updateDrone(state, player) {
  if (!isEntityValid(state.entity)) {
    removeLight(state);
    states.delete(state.ownerId);
    return;
  }

  if (state.mode === "stay") {
    if (!state.stayLocation) {
      state.stayLocation = copyLocation(state.entity.location);
    }
    safeTeleport(state.entity, state.stayLocation, undefined, yawToward(state.entity.location, player.location));
    updateLight(state, state.entity);
    maybeDefend(state, player);
    return;
  }

  const target = followTarget(player);
  const current = state.entity.location;
  const distance = distanceBetween(current, target);
  const droneDimension = state.entity.dimension;

  let next;
  if (droneDimension.id !== player.dimension.id) {
    next = target;
  } else if (state.mode === "come") {
    next = lerpLocation(current, target, 0.55);
    if (distance < 2.0) {
      setDroneMode(state, "follow");
      actionBar(player, "§bDrone arrived.");
    }
  } else if (state.mode === "scan") {
    next = lerpLocation(current, target, 0.18);
  } else if (distance > MAX_FOLLOW_DISTANCE) {
    next = target;
  } else {
    next = lerpLocation(current, target, 0.28);
  }

  let yaw;
  if (state.mode === "scan") {
    yaw = (loopTick * 3) % 360;
  } else {
    yaw = yawFromVector(horizontalForward(player));
  }
  safeTeleport(state.entity, next, player.dimension, yaw);
  updateLight(state, state.entity);

  if (state.mode === "scan" && loopTick >= state.nextScanTick) {
    scanPulse(state, player);
    state.nextScanTick = loopTick + TICKS_PER_SECOND;
  }
  maybeDefend(state, player);
}

// --------------------------------------------------------------------------- //
// Controller form
// --------------------------------------------------------------------------- //
function openMenu(player, state) {
  if (!state || !isEntityValid(state.entity)) {
    player.sendMessage("§7Your Drone Companion is no longer nearby. Use the controller to summon another.");
    return;
  }

  let distance = 0;
  let distanceLabel = "unknown";
  try {
    distance = distanceBetween(state.entity.location, player.location);
    distanceLabel =
      state.entity.dimension.id === player.dimension.id
        ? `${distance.toFixed(1)} blocks`
        : "different dimension";
  } catch (error) {
    distance = 0;
    distanceLabel = "unknown";
  }
  const health = Math.max(0, Math.ceil(getHealth(state.entity)));
  const modeLabel = state.mode.charAt(0).toUpperCase() + state.mode.slice(1);

  const form = new ActionFormData()
    .title("§bDrone Companion")
    .body(
      `§7Mode: §b${modeLabel}\n` +
        `§7Health: §a${health}/20\n` +
        `§7Distance: §f${distanceLabel}\n` +
        `§7Light: ${state.light ? "§aON" : "§cOFF"}\n` +
        `§7Defend: ${state.defend ? "§aON" : "§cOFF"}\n` +
        "§8──────────────────\n" +
        "§7Give your drone an order."
    )
    .button(state.mode === "follow" ? "§bFollow §7(active)" : "Follow")
    .button(state.mode === "stay" ? "§bStay §7(active)" : "Stay")
    .button(state.mode === "come" ? "§bCome §7(active)" : "Come")
    .button(state.mode === "scan" ? "§bScan §7(active)" : "Scan")
    .button(`Light: ${state.light ? "§aON" : "§cOFF"}`)
    .button(`Defend: ${state.defend ? "§aON" : "§cOFF"}`)
    .button("Summon to me")
    .button("§cDismiss")
    .button("Close");

  form
    .show(player)
    .then((result) => {
      if (result.canceled) {
        return;
      }

      switch (result.selection) {
        case 0:
          setDroneMode(state, "follow");
          actionBar(player, "§bDrone: Follow");
          break;
        case 1:
          state.stayLocation = copyLocation(state.entity.location);
          setDroneMode(state, "stay");
          actionBar(player, "§bDrone: Stay");
          break;
        case 2:
          setDroneMode(state, "come");
          actionBar(player, "§bDrone: Coming to you");
          break;
        case 3:
          setDroneMode(state, "scan");
          state.nextScanTick = 0;
          actionBar(player, "§bDrone: Scanning");
          break;
        case 4:
          state.light = !state.light;
          if (state.light) {
            updateLight(state, state.entity);
            actionBar(player, "§bDrone light enabled");
          } else {
            removeLight(state);
            actionBar(player, "§7Drone light disabled");
          }
          break;
        case 5:
          state.defend = !state.defend;
          actionBar(player, state.defend ? "§cDrone defense enabled" : "§7Drone defense disabled");
          break;
        case 6:
          safeTeleport(
            state.entity,
            followTarget(player),
            player.dimension,
            yawFromVector(horizontalForward(player))
          );
          setDroneMode(state, "follow");
          actionBar(player, "§bDrone recalled");
          break;
        case 7:
          dismissDrone(state, player);
          return;
        default:
          return;
      }

      system.run(() => openMenu(player, state));
    })
    .catch(() => {
      /* the player closed the form */
    });
}

function dismissDrone(state, player) {
  removeLight(state);
  try {
    state.entity.remove();
  } catch (error) {
    /* already gone */
  }
  states.delete(state.ownerId);
  setPlayerDroneId(player, "");
  player.sendMessage("§7Drone Companion dismissed.");
}

function handleController(player) {
  const last = lastUse.get(player.id) ?? -999;
  if (loopTick - last < USE_COOLDOWN) {
    return;
  }
  lastUse.set(player.id, loopTick);

  let state = ensureState(player);
  if (!state) {
    state = summonDrone(player);
    if (!state) {
      return;
    }
  }
  openMenu(player, state);
}

// --------------------------------------------------------------------------- //
// Events and startup
// --------------------------------------------------------------------------- //
world.afterEvents.itemUse.subscribe((event) => {
  const player = event.source;
  if (!player || player.typeId !== "minecraft:player") {
    return;
  }
  if (!event.itemStack || event.itemStack.typeId !== CONTROLLER_ID) {
    return;
  }
  system.run(() => handleController(player));
});

system.runInterval(() => {
  try {
    loopTick += 1;
    const players = new Map(world.getPlayers().map((player) => [player.id, player]));
    for (const [ownerId, state] of Array.from(states)) {
      if (!isEntityValid(state.entity)) {
        removeLight(state);
        states.delete(ownerId);
        continue;
      }
      const player = players.get(ownerId);
      if (!player) {
        continue;
      }
      try {
        updateDrone(state, player);
      } catch (error) {
        console.warn(`[Drone Companion] update failed: ${error}`);
      }
    }
  } catch (error) {
    console.warn(`[Drone Companion] loop failed: ${error}`);
  }
}, LOOP_INTERVAL);

system.runTimeout(() => {
  try {
    rebuildStates();
  } catch (error) {
    console.warn(`[Drone Companion] startup scan failed: ${error}`);
  }
}, 40);
