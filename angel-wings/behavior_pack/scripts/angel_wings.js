/*
 * Angel Wings - Bedrock Edition flight script
 * ============================================
 * Gives the player elytra-style flight while Angel Wings are equipped in the
 * chest slot.
 *
 * CONTROLS
 *   Jump (on the ground) : take off
 *   Look up / down       : climb / dive
 *   Look around          : steer
 *   Sneak                : stop flying and drop normally
 *
 * REQUIREMENTS
 *   Minecraft Bedrock 1.21.80+ (Script API 2.x).
 *   The behavior pack manifest declares the @minecraft/server dependency.
 */

import { world, system, EquipmentSlot } from "@minecraft/server";

const ANGEL_WINGS_ID = "mod:angel_wings";

// Movement tuning (blocks per tick; 20 ticks = 1 second)
const GLIDE_SPEED = 0.35;
const CLIMB_SPEED = 0.25;
const LAUNCH_IMPULSE = 0.55;

// Wear one durability point per second of flight
const DURABILITY_INTERVAL = 20;

let tickCounter = 0;

function getChestItem(player) {
  try {
    const equippable = player.getComponent("minecraft:equippable");
    return equippable ? equippable.getEquipment(EquipmentSlot.Chest) : undefined;
  } catch (e) {
    return undefined;
  }
}

function damageWings(player, item) {
  try {
    const durability = item.getComponent("minecraft:durability");
    const equippable = player.getComponent("minecraft:equippable");
    if (!durability || !equippable) return;

    durability.damage += 1;
    if (durability.damage >= durability.maxDurability) {
      equippable.setEquipment(EquipmentSlot.Chest, undefined);
    } else {
      equippable.setEquipment(EquipmentSlot.Chest, item);
    }
  } catch (e) {
    // Ignore transient inventory errors.
  }
}

system.runInterval(() => {
  tickCounter += 1;

  for (const player of world.getAllPlayers()) {
    const item = getChestItem(player);
    if (!item || item.typeId !== ANGEL_WINGS_ID) continue;

    // Sneak to cancel flight and fall normally.
    if (player.isSneaking) continue;

    if (player.isOnGround) {
      // Jump to take off; normal walking/jumping is unaffected.
      if (player.isJumping) {
        try {
          player.clearVelocity();
          player.applyImpulse({ x: 0, y: LAUNCH_IMPULSE, z: 0 });
        } catch (e) {}
      }
      continue;
    }

    // Glide forward along the view direction.
    const rot = player.getRotation();
    const pitch = (rot.x * Math.PI) / 180;
    const yaw = (rot.y * Math.PI) / 180;
    const cosPitch = Math.cos(pitch);

    const vx = -Math.sin(yaw) * cosPitch * GLIDE_SPEED;
    const vz = Math.cos(yaw) * cosPitch * GLIDE_SPEED;
    const vy = -Math.sin(pitch) * CLIMB_SPEED - 0.02;

    try {
      player.clearVelocity();
      player.applyImpulse({ x: vx, y: vy, z: vz });
      player.addEffect("slow_falling", 10, { showParticles: false });
    } catch (e) {}

    if (tickCounter % DURABILITY_INTERVAL === 0) {
      damageWings(player, item);
    }
  }
}, 1);
