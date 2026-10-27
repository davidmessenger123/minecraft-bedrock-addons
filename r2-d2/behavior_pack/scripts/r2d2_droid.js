import { world, system } from "@minecraft/server";

const DROID_ID = "r2d2:droid";
const SOUNDS = ["mob.r2d2.beep", "mob.r2d2.chirp", "mob.r2d2.whistle"];
const COOLDOWN_TICKS = 80;
const HOLO_PROPERTY = "r2d2:holo_active";
const HOLO_SOUND_ON = "mob.r2d2.holo_on";
const HOLO_SOUND_OFF = "mob.r2d2.holo_off";
const TOGGLE_COOLDOWN_TICKS = 10;
const lastSound = new Map();
const lastToggle = new Map();
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

function toggleHologram(droid, player) {
  const now = system.currentTick;
  const last = lastToggle.get(droid.id);
  if (last !== undefined && now - last < TOGGLE_COOLDOWN_TICKS) {
    return;
  }
  lastToggle.set(droid.id, now);

  let active = false;
  try {
    active = droid.getProperty(HOLO_PROPERTY) === true;
  } catch (error) {
    return;
  }

  const next = !active;
  try {
    droid.setProperty(HOLO_PROPERTY, next);
  } catch (error) {
    return;
  }

  const sound = next ? HOLO_SOUND_ON : HOLO_SOUND_OFF;
  const pitch = next ? 1.0 : 0.9;
  try {
    droid.playSound(sound, { volume: 0.7, pitch });
  } catch (error) {
    try {
      world.playSound(sound, droid.location, { volume: 0.7, pitch });
    } catch (innerError) {
      /* audio is optional */
    }
  }

  try {
    player.onScreenDisplay.setActionBar({
      translate: next ? "action.r2d2.holo_on" : "action.r2d2.holo_off"
    });
  } catch (error) {
    /* action bar feedback is optional */
  }
}

world.afterEvents.entitySpawn.subscribe((event) => {
  if (event.entity.typeId !== DROID_ID) {
    return;
  }
  tryTame(event.entity);
  playSound(event.entity);
});

world.afterEvents.playerInteractWithEntity.subscribe((event) => {
  if (event.target.typeId !== DROID_ID) {
    return;
  }
  toggleHologram(event.target, event.player);
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
        lastToggle.delete(droid.id);
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
