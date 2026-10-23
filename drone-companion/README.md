# Drone Companion — Minecraft Bedrock Edition Add-On

A summonable quadcopter companion for Minecraft Bedrock. Use the **Drone
Controller** to call a small hovering drone, then give it orders from a form:
follow you, hold position, come back, scan for hostiles, light up the area, or
zap nearby monsters.

The drone is modelled in Blockbench, exported as Bedrock geometry, animated with
Molang, and flown by a Script API controller. It is a companion, not a vehicle:
it hovers near you and never needs to be fed, charged, or repaired.

## Features

| Feature | What it does |
|---------|--------------|
| **Summon** | Use the Drone Controller to spawn your drone. Each player can own one. |
| **Follow** | Hovers behind and above you, smoothly catching up when you move. |
| **Stay** | Holds its current position and turns to watch you. |
| **Come** | Flies to you quickly, then switches back to Follow. |
| **Scan** | Hovers and slowly rotates, highlighting hostile mobs within 12 blocks with Glowing and a ring of end-rod particles. |
| **Light** | Places a level-15 light block at the drone's position when that block is air. The light is removed when you toggle it off, dismiss the drone, or the drone moves to a different block. |
| **Defend** | Optional toggle. Once per second, zaps the nearest monster within 10 blocks for 4 damage with a critical-hit particle. Off by default. |
| **Recall / Dismiss** | Teleport the drone to you, or remove it and clear its light. |

The drone has 20 health, is persistent and fire-immune, ignores fall damage, and
has no gravity or collision. It can be named with a name tag; a new drone is
called **Drone** by default.

## Requirements

- Minecraft Bedrock **1.21.90 or newer**.
- Both the behavior pack and the resource pack enabled in the world.
- The behavior pack declares `@minecraft/server` **2.0.0** and
  `@minecraft/server-ui` **2.0.0**. If your game ships a different 2.x module
  version, change the matching entry under `dependencies` in
  `behavior_pack/manifest.json` to the version listed in the manifest generator
  for your game.
- No experiments are required by the pack itself. If your build only exposes
  Script API 2.0.0 behind the **Beta APIs** experiment, enable that experiment.

## Installation

1. Open **`DroneCompanion-1.0.1.mcaddon`** to import both packs at once.
   Alternatively, copy the `behavior_pack` and `resource_pack` folders into the
   world's `behavior_packs/` and `resource_packs/` folders, or zip each folder
   and import it as a `.mcpack`.
2. Enable **both** packs in the world settings.
3. Craft a Drone Controller, or give yourself one:

   ```
   /give @s drone:controller
   ```

4. Hold the controller and **use** it (right-click / tap) to summon the drone
   and open its menu.

## Crafting the Drone Controller

Craft it at a crafting table:

```
I R I
C A C
  E
```

| Key | Ingredient |
|-----|------------|
| `I` | Iron Ingot |
| `R` | Redstone Dust |
| `C` | Copper Ingot |
| `A` | Amethyst Shard |
| `E` | Ender Pearl |

The recipe yields one controller. The controller is not consumed when used and
stacks to one.

## Controls

| Input | Effect |
|-------|--------|
| Use the Drone Controller | Summon your drone if you do not have one, then open the control form |
| **Follow** | Follow behind and above you |
| **Stay** | Hold the current position |
| **Come** | Fly to you, then resume Follow |
| **Scan** | Hover, rotate, and highlight hostiles within 12 blocks |
| **Light: ON/OFF** | Toggle the drone's light block |
| **Defend: ON/OFF** | Toggle the defensive zap |
| **Summon to me** | Teleport the drone to your side |
| **Dismiss** | Remove the drone and its light |
| **Close** | Close the form |

Using the controller again reopens the form. If the drone is destroyed, use the
controller to summon a new one. The form is per-player: in multiplayer, each
player's controller controls their own drone.

## The drone model

Open `DroneCompanion.bbmodel` in Blockbench to edit the model. The project is a
Bedrock Entity project with a 64×64 texture. It contains:

- `body` (parent bone, pivot `[0, 6, 0]`) — 21 cubes: the central body, canopy,
  belly, two X-frame arms, two skids and four feet, front/side LEDs, antenna,
  antenna tip, battery, and four motor housings.
- `rotor_fl`, `rotor_fr`, `rotor_bl`, `rotor_br` (pivots at
  `[±5, 8.2, ±5]`) — three cubes each: motor, hub, and two crossed blades.
- `camera` (pivot `[0, 3.5, −4]`) — the gimbal housing and lens at the front.

That is **35 cubes** in **6 bones**. The model is **15.6 units wide** (0.975
blocks), **10 units tall** (0.625 blocks), and **8.95 units deep** (0.559
blocks). The four rotor centres sit 5 units from the centre line in both X and
Z, giving the X-frame its wide stance. The front of the drone is −Z, where the
camera lens and the cyan front LED are.

The `.bbmodel` also contains three numeric preview animations with the same IDs
as the shipped Molang animations. The **resource-pack** file
`resource_pack/animations/drone_companion.animation.json` is the source of truth
for the add-on; the previews are only for checking timing in Blockbench.

In Blockbench, frame the model with **F** (Frame Selection) if the camera is not
already centred on it.

## Folder layout

```
DroneCompanion/
├── DroneCompanion.bbmodel                       # Blockbench source project
├── DroneCompanion-1.0.1.mcaddon                 # packaged add-on
├── tools/
│   ├── generate_textures.py                     # 64×64 atlas + controller icon
│   ├── generate_pack_icon.py                    # 256×256 pack icons
│   └── validate.py                              # static pack/geometry checks
├── behavior_pack/
│   ├── manifest.json
│   ├── pack_icon.png
│   ├── entities/drone_companion.json            # entity components
│   ├── items/drone_controller.json              # controller item
│   ├── recipes/drone_controller.json            # crafting recipe
│   └── scripts/drone_companion.js               # summon, flight, modes, form
└── resource_pack/
    ├── manifest.json
    ├── pack_icon.png
    ├── animations/drone_companion.animation.json
    ├── entity/drone_companion.entity.json       # client entity + animations
    ├── models/entity/drone_companion.geo.json   # exported 35-cube geometry
    ├── texts/en_US.lang
    ├── texts/languages.json
    ├── textures/entity/drone_companion.png      # 64×64 entity atlas
    ├── textures/items/drone_controller.png      # 64×64 controller icon
    └── textures/item_texture.json
```

## Customising

- **Flight feel**: edit `HOVER_HEIGHT`, `FOLLOW_BACK`, `FOLLOW_SIDE`,
  `MAX_FOLLOW_DISTANCE`, `SCAN_RADIUS`, and `DEFEND_RADIUS` at the top of
  `behavior_pack/scripts/drone_companion.js`.
- **Drone stats**: edit `minecraft:health`, `minecraft:collision_box`, and the
  other components in `behavior_pack/entities/drone_companion.json`.
- **Model**: edit the cubes and bones in `DroneCompanion.bbmodel`, then
  `File → Export → Export Bedrock Model` and overwrite
  `resource_pack/models/entity/drone_companion.geo.json`.
- **Textures**: the entity atlas is
  `resource_pack/textures/entity/drone_companion.png`; the controller icon is
  `resource_pack/textures/items/drone_controller.png`. Both are 64×64. Run
  `python3 tools/generate_textures.py` to regenerate the current procedural art.
  The atlas is a 4×4 grid of 16×16 cells; the model uses 12 material swatches
  (body, canopy, belly, arms, rotor, motor, LED, lens, battery, camera, metal,
  accent).
- **Pack icon**: run `python3 tools/generate_pack_icon.py` to regenerate the
  256×256 icons in both pack roots.
- **Animations**: edit
  `resource_pack/animations/drone_companion.animation.json`. The rotor spin uses
  `math.mod(query.anim_time * 1440, 360)`; the hover and camera use
  `math.sin` with degrees. Keep `animation_length` in step with the sine
  frequencies for a clean loop.
- **Recipe**: edit `behavior_pack/recipes/drone_controller.json`; the result
  identifier must stay `drone:controller`.

## Notes and limitations

- The drone is **script-driven**. It has no navigation component and is moved by
  teleporting every two ticks, so it can clip through walls or low ceilings in
  tight spaces. It is a hovering companion, not a pathfinding mob.
- The drone does **not** have an inventory, chest, or item pickup. It is a scout
  and support companion.
- **Scan** applies Glowing to hostile mobs within 12 blocks and emits particles.
  It does not reveal mobs through walls in the same way as a player-applied
  Glowing effect; the drone itself can be behind a wall and still scan.
- **Defend** zaps the nearest monster within 10 blocks once per second. It is
  off by default because zapping a creeper near you can still be dangerous.
- The **light** is placed only when the block at the drone's position is air.
  It is not placed underwater or inside solid blocks. The light is removed when
  toggled off, when the drone is dismissed, or when the drone moves to a new
  block. If the drone's chunk unloads while the light is on, the light block may
  remain until the drone returns or you remove it.
- If the drone is left in an unloaded chunk, the controller cannot find it and
  may summon a replacement. The old drone can remain in the world; use
  `/kill @e[type=drone:companion]` if you need to clean up an orphan.
- If the controller form does not open, check that both packs are enabled and
  that your game provides the declared `@minecraft/server-ui` 2.0.0 module. If
  your game uses a different 2.x UI version, update the dependency version in
  `behavior_pack/manifest.json`.

## Validation

The project includes `tools/validate.py`, which parses every JSON file and
checks the manifest UUID wiring, entity/item/recipe identifiers, geometry
structure and UV bounds, animation references, texture paths, PNG dimensions,
and localisation keys. Run it after any edit:

```sh
python3 tools/validate.py
node --input-type=module --check < behavior_pack/scripts/drone_companion.js
```

The add-on has been **statically validated** with those checks and with a
TypeScript check against the `@minecraft/server` 2.0.0 and
`@minecraft/server-ui` 2.0.0 type definitions. A local API-mock smoke test
exercised summon, follow, stay, come, scan, light, defend, dismiss, and owner
re-binding. It has not been run in a Bedrock client in this environment, so
in-game behaviour should be checked on your device.

## Changelog

- **1.0.1** — fixed the controller's hotbar icon by switching to the modern
  string `minecraft:icon` component; version bump only, no behavior changes.
- **1.0.0** — initial release: 35-cube X-frame quadcopter, 64×64 procedural
  atlas, controller item and crafting recipe, Follow / Stay / Come / Scan /
  Light / Defend modes, ActionForm controller, owner binding, and a 256×256 pack
  icon.
