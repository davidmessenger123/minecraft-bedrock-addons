# Angel Wings — Minecraft Bedrock Edition Mod

A pair of elytra-style Angel Wings that let the player fly. The wing mesh is
modelled in Blockbench, exported as Bedrock geometry, rendered on the player's
back through an attachable, and driven by a Script API glide controller.

## Folder layout

```
AngelWingsMod/
├── AngelWings.bbmodel                       # Blockbench project (open this)
├── tools/generate_textures.py               # regenerates both PNGs (stdlib only)
├── behavior_pack/
│   ├── manifest.json
│   ├── items/angel_wings.json               # chest-slot wearable
│   └── scripts/angel_wings.js               # flight logic (Script API 2.x)
└── resource_pack/
    ├── manifest.json
    ├── texts/en_US.lang
    ├── attachables/angel_wings.json         # makes the wings render when worn
    ├── models/entity/angel_wings.geo.json   # exported wing geometry
    ├── animations/angel_wings.animation.json
    ├── textures/item_texture.json           # item icon registration
    ├── textures/items/angel_wings.png       # 64×64 inventory icon
    └── textures/entity/angel_wings.png      # 64×64 worn-wing feather texture
```

## The wing model

Open `AngelWings.bbmodel` in Blockbench to edit it. The project contains:

- `body` (parent bone, pivot `[0, 12, 0]`)
  - `left_wing` (pivot `[−1, 22.5, 2.9]`) — 17 layered feather cubes
  - `right_wing` (pivot `[1, 22.5, 2.9]`) — mirrored copy
  - `wing_spine` — central feather panel between the roots

The wings span **32 units** (2 blocks) from tip to tip (`x = −16…+16` before
the 8° sweep) and sit on the upper back (`y = 14…28`, `z = 2…4.2`).
Each wing has four feather layers plus a tapered tip: a leading-edge arm,
three covert feathers, four long primaries, four feather tips, and two small
tip feathers that finish the point. All 34 wing cubes are rotated 8° around
the wing root so the wings rest in a swept-up pose. The 64×64 entity texture
is a layered ivory/gold feather pattern; the inventory icon is a separate
transparent 64×64 image.

In Blockbench's viewport the model is at the back of the player, not at ground
level, so frame it with **F** (Frame Selection) if the camera is not already
centred on it.

## How to install

1. Open **`AngelWings-1.1.1.mcaddon`** to import both packs at once.
   Alternatively, copy the `behavior_pack` and `resource_pack` folders into the
   world's `behavior_packs/` and `resource_packs/` folders (or zip each folder
   and import it as `.mcpack`).
2. Enable **both** packs in the world settings.
3. Requirements:
   - Minecraft Bedrock **1.21.80 or newer** (Script API 2.x).
   - The behavior pack declares `@minecraft/server` `2.0.0`; if your game
     ships a newer 2.x module, change that version in
     `behavior_pack/manifest.json` to the one listed in the manifest generator.
4. Give yourself the wings:
   ```
   /give @s mod:angel_wings
   ```
5. Equip them in the **chest armor slot**. The attachable renders the wings on
   your back; the script starts running automatically.

## Controls

| Input | Effect |
|-------|--------|
| Jump while on the ground | Take off |
| Look up / down | Climb / dive |
| Look around | Steer |
| Sneak | Cancel flight and fall normally |

While airborne the script replaces your velocity every tick with a glide
vector based on your view direction. A point of durability is used once per
second of flight (432 total, like the elytra) and the wings can be repaired
with phantom membranes.

## Customising

- **Flight speed**: edit `GLIDE_SPEED`, `CLIMB_SPEED` and `LAUNCH_IMPULSE` in
  `behavior_pack/scripts/angel_wings.js`.
- **Wing shape**: edit the cubes in `AngelWings.bbmodel`, then
  `File → Export → Export Bedrock Model` and overwrite
  `resource_pack/models/entity/angel_wings.geo.json`.
- **Textures**: the worn wings use
  `resource_pack/textures/entity/angel_wings.png`; the inventory icon uses
  `resource_pack/textures/items/angel_wings.png`. Both are 64×64. Run
  `python3 tools/generate_textures.py` to regenerate the current art.
- **Durability / repair**: edit `minecraft:durability` and
  `minecraft:repairable` in `behavior_pack/items/angel_wings.json`.

## Notes and limitations

- Flight is script-driven (`clearVelocity` + `applyImpulse`), not vanilla
  elytra gliding. Firework-rocket boosting and the vanilla elytra pose are not
  included.
- `player.isGliding` is read-only in the Bedrock Script API, so the animation
  uses `!query.is_on_ground` as its flap condition instead.
- The wings flap only while you are airborne.
- The attachable uses the current armor render controller
  (`controller.render.armor.v2`). On older 1.21.x clients, change it to
  `controller.render.armor` if the wings do not appear in-game.
- The attachable hides the vanilla chest armor layer, but a cape can still
  clip with the inner wings; remove the cape if you see overlap.

## Changelog

- **1.1.1** — tapered wing tips: two 1-unit tip feathers per wing replace the
  flat outer edge; the model is now 35 cubes (17 per wing + spine), still
  32 units wide.
- **1.1.0** — 32-unit layered wings (leading-edge arm, coverts, primaries,
  feather tips, central spine), swept-up 8° rest pose, new 64×64 worn-wing
  feather texture, separate transparent inventory icon, and an 8° flap.
- **1.0.0** — initial release.
