/*
 * Angel Wings - Bedrock Edition glide controller
 * ===============================================
 * Equip the wings in the chest slot, jump from a height (or jump and then
 * press jump again in the air) to deploy them.  The wings preserve the
 * player's momentum instead of pulling them forward every tick, so steering
 * and speed are under the player's control.
 *
 * Controls
 *   Jump in the air : deploy the wings / flap
 *   Hold jump       : keep flapping (climb and gain speed)
 *   Look around     : steer the glide
 *   Look down       : dive and trade height for speed
 *   Look up         : trade speed for lift
 *   WASD            : air control
 *   Sneak           : fold the wings and fall
 *
 * The behavior pack manifest declares @minecraft/server 2.0.0.
 */

import {
  world,
  system,
  EquipmentSlot,
  InputButton,
  ButtonState,
} from "@minecraft/server";

const WINGS_ID = "mod:angel_wings";
const DEG = Math.PI / 180;

// Flight tuning (blocks per tick; 20 ticks = 1 second).
const GRAVITY = 0.045;
const DRAG = 0.994;
const MAX_HORIZONTAL_SPEED = 1.45;
const MAX_VERTICAL_SPEED = 1.1;
const GLIDE_LIFT = 0.055;
const MAX_GLIDE_LIFT = 0.1;
const DIVE_ACCEL = 0.035;
const CLIMB_LIFT = 0.035;
const FLAP_LIFT = 0.42;
const FLAP_FORWARD = 0.1;
const FLAP_COOLDOWN_TICKS = 7;
const DURABILITY_INTERVAL = 20;

/** @type {Map<string, {gliding: boolean, jumpPressed: boolean, jumpHeld: boolean, wasJumping: boolean, flapCooldown: number, ticks: number}>} */
const states = new Map();

function getState(player) {
  let state = states.get(player.id);
  if (!state) {
    state = {
      gliding: false,
      jumpPressed: false,
      jumpHeld: false,
      wasJumping: false,
      flapCooldown: 0,
      ticks: 0,
    };
    states.set(player.id, state);
  }
  return state;
}

function read(player, getter, fallback) {
  try {
    return getter();
  } catch (error) {
    return fallback;
  }
}

function getChestItem(player) {
  try {
    const equippable = player.getComponent("minecraft:equippable");
    return equippable ? equippable.getEquipment(EquipmentSlot.Chest) : undefined;
  } catch (error) {
    return undefined;
  }
}

function setVelocity(player, x, y, z) {
  try {
    player.clearVelocity();
    player.applyImpulse({ x, y, z });
  } catch (error) {
    // The player may have left the world between the tick and this call.
  }
}

function clamp(value, min, max) {
  return value < min ? min : value > max ? max : value;
}

function playFlapSound(player) {
  try {
    player.playSound("mob.phantom.flap", { volume: 0.35, pitch: 1.35 });
  } catch (error) {
    // Sound events are cosmetic; never let one break flight.
  }
}

function startGlide(player, state) {
  state.gliding = true;
  state.ticks = 0;
  state.flapCooldown = 0;
  try {
    player.onScreenDisplay.setActionBar("§bAngel Wings deployed");
  } catch (error) {}
}

function stopGlide(player, state, landed) {
  state.gliding = false;
  state.ticks = 0;
  state.flapCooldown = 0;
  if (landed) {
    try {
      player.removeEffect("slow_falling");
    } catch (error) {}
  }
}

function damageWings(player, item, state) {
  try {
    const durability = item.getComponent("minecraft:durability");
    const equippable = player.getComponent("minecraft:equippable");
    if (!durability || !equippable) return;

    durability.damage += 1;
    if (durability.damage >= durability.maxDurability) {
      equippable.setEquipment(EquipmentSlot.Chest, undefined);
      stopGlide(player, state, false);
      player.sendMessage("§cYour Angel Wings have worn out.");
    } else {
      equippable.setEquipment(EquipmentSlot.Chest, item);
    }
  } catch (error) {
    // Ignore transient inventory errors; flight continues.
  }
}

function applyGlidePhysics(player, state, flapNow) {
  const rotation = player.getRotation();
  const yaw = rotation.y * DEG;
  const pitch = rotation.x * DEG;
  const cosPitch = Math.cos(pitch);

  // Horizontal heading, normalized for steering.
  const headingX = -Math.sin(yaw);
  const headingZ = Math.cos(yaw);
  const rightX = Math.cos(yaw);
  const rightZ = Math.sin(yaw);

  const velocity = player.getVelocity();
  let vx = velocity.x;
  let vy = velocity.y;
  let vz = velocity.z;

  // Player-driven air control.  The wings do not push the player forward on
  // their own; holding W adds speed, strafing adds a little side control.
  const input = read(
    player,
    () => player.inputInfo.getMovementVector(),
    { x: 0, y: 0 }
  );
  const forwardInput = clamp(Number(input.y) || 0, -1, 1);
  const strafeInput = clamp(Number(input.x) || 0, -1, 1);
  vx += headingX * forwardInput * 0.035;
  vz += headingZ * forwardInput * 0.035;
  vx += rightX * strafeInput * 0.025;
  vz += rightZ * strafeInput * 0.025;

  // Lift grows with horizontal speed.  A slow or stationary player still
  // falls; the wings only carry you once you have some momentum.
  const horizontalSpeed = Math.hypot(vx, vz);
  const lift = Math.min(horizontalSpeed * GLIDE_LIFT, MAX_GLIDE_LIFT);
  vy -= GRAVITY;
  vy += lift;

  // Pitch trades height for speed, like an elytra.
  if (pitch > 0) {
    const dive = Math.sin(pitch);
    vy -= dive * 0.03;
    vx += headingX * dive * DIVE_ACCEL;
    vz += headingZ * dive * DIVE_ACCEL;
  } else {
    const climb = -Math.sin(pitch);
    vy += climb * CLIMB_LIFT * Math.min(horizontalSpeed, 1.2);
    vx *= 1 - 0.006 * climb;
    vz *= 1 - 0.006 * climb;
  }

  if (flapNow) {
    vx += headingX * FLAP_FORWARD;
    vz += headingZ * FLAP_FORWARD;
    vy += FLAP_LIFT;
    playFlapSound(player);
  }

  vx *= DRAG;
  vz *= DRAG;

  const newSpeed = Math.hypot(vx, vz);
  if (newSpeed > MAX_HORIZONTAL_SPEED) {
    const scale = MAX_HORIZONTAL_SPEED / newSpeed;
    vx *= scale;
    vz *= scale;
  }
  vy = clamp(vy, -MAX_VERTICAL_SPEED, MAX_VERTICAL_SPEED);

  setVelocity(player, vx, vy, vz);

  // Refresh slow falling while gliding so a hard landing does not hurt.  The
  // effect is short and refreshed periodically rather than stacked forever.
  if (state.ticks % 30 === 0) {
    try {
      player.addEffect("slow_falling", 60, { showParticles: false });
    } catch (error) {}
  }
}

function tickPlayer(player) {
  const state = getState(player);
  const item = getChestItem(player);
  const hasWings = item !== undefined && item.typeId === WINGS_ID;

  if (!hasWings) {
    if (state.gliding) stopGlide(player, state, false);
    state.jumpPressed = false;
    state.jumpHeld = false;
    state.wasJumping = false;
    return;
  }

  const grounded = read(player, () => player.isOnGround, true);
  const inWater = read(player, () => player.isInWater, false);
  const flying = read(player, () => player.isFlying, false);
  const sneaking = read(player, () => player.isSneaking, false);
  const jumpHeld = read(player, () => player.isJumping, state.jumpHeld);
  const jumpPressed = state.jumpPressed || (jumpHeld && !state.wasJumping);

  state.jumpPressed = false;
  state.jumpHeld = jumpHeld;
  state.wasJumping = jumpHeld;

  if (grounded || inWater || flying || sneaking) {
    if (state.gliding) stopGlide(player, state, grounded);
    return;
  }

  if (!state.gliding) {
    // Deploy on a fresh jump press while airborne.  A normal ground jump does
    // not deploy the wings; release and press jump again in the air.
    if (jumpPressed) {
      startGlide(player, state);
      state.flapCooldown = 0;
    }
    return;
  }

  if (state.flapCooldown > 0) state.flapCooldown -= 1;
  const flapNow = (jumpPressed || jumpHeld) && state.flapCooldown <= 0;
  if (flapNow) state.flapCooldown = FLAP_COOLDOWN_TICKS;

  applyGlidePhysics(player, state, flapNow);

  state.ticks += 1;
  if (state.ticks % DURABILITY_INTERVAL === 0) {
    damageWings(player, item, state);
  }
}

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    tickPlayer(player);
  }
}, 1);

// The button event gives a clean rising edge for jump.  If the API is not
// available on an older client, the isJumping edge check above still works.
try {
  world.afterEvents.playerButtonInput.subscribe((event) => {
    if (event.button !== InputButton.Jump) return;
    const state = getState(event.player);
    if (event.newButtonState === ButtonState.Pressed) {
      state.jumpPressed = true;
      state.jumpHeld = true;
    } else {
      state.jumpHeld = false;
    }
  });
} catch (error) {
  console.warn("[Angel Wings] playerButtonInput is unavailable; using jump polling.");
}

try {
  world.afterEvents.playerLeave.subscribe((event) => {
    states.delete(event.playerId);
  });
} catch (error) {}
