import { world, system } from "@minecraft/server";

const DROID_ID = "r2d2:droid";
const SOUNDS = ["mob.r2d2.beep", "mob.r2d2.chirp", "mob.r2d2.whistle"];
const COOLDOWN_TICKS = 80;
const lastSound = new Map();
let tick = 0;

function dimensions() {
  const result = [];
  const seen = new Set();
  for (const id of ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"]) {
    try {
      const dimension = world.getDimension(id);
      if (dimension && !seen.has(dimension.id)) {
        seen.add(dimension.id);
        result.push(dimension);
      }
    } catch (error) {
      /* dimension unavailable */
    }
  }
  return result;
}

function nearestPlayer(entity) {
  let best;
  let bestDistance = Infinity;
  for (const player of world.getPlayers()) {
    const distance = Math.hypot(
      entity.location.x - player.location.x,
      entity.location.y - player.location.y,
      entity.location.z - player.location.z
    );
    if (distance < bestDistance) {
      bestDistance = distance;
      best = player;
    }
  }
  return bestDistance <= 16 ? best : undefined;
}

function tryTame(entity) {
  const player = nearestPlayer(entity);
  if (!player) {
    return;
  }
  try {
    const tameable = entity.getComponent("minecraft:tameable");
    if (tameable && !tameable.isTamed) {
      tameable.tame(player);
    }
  } catch (error) {
    /* taming is optional; the droid still follows its owner if already tamed */
  }
}

function playSound(entity) {
  const sound = SOUNDS[Math.floor(Math.random() * SOUNDS.length)];
  try {
    entity.playSound(sound, { volume: 0.35, pitch: 0.9 + Math.random() * 0.2 });
  } catch (error) {
    try {
      world.playSound(sound, entity.location, { volume: 0.35, pitch: 0.9 + Math.random() * 0.2 });
    } catch (innerError) {
      /* audio is optional */
    }
  }
}

world.afterEvents.entitySpawn.subscribe((event) => {
  if (event.entity.typeId !== DROID_ID) {
    return;
  }
  tryTame(event.entity);
  playSound(event.entity);
});

system.runInterval(() => {
  tick += 1;
  for (const dimension of dimensions()) {
    let droids = [];
    try {
      droids = dimension.getEntities({ type: DROID_ID });
    } catch (error) {
      continue;
    }
    for (const droid of droids) {
      if (!droid.isValid) {
        lastSound.delete(droid.id);
        continue;
      }
      const last = lastSound.get(droid.id) || 0;
      if (tick - last < COOLDOWN_TICKS) {
        continue;
      }
      if (Math.random() < 0.35) {
        playSound(droid);
        lastSound.set(droid.id, tick);
      }
    }
  }
}, 20);
