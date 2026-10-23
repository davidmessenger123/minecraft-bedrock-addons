# Angel Wings — Minecraft Bedrock Edition Add-on

A pair of elytra-style Angel Wings that let the player glide. The wing mesh is
modelled in Blockbench, exported as Bedrock geometry, rendered on the player's
back through an attachable, and driven by a Script API glide controller.

Version **1.2.0** adds a new 46-unit layered feather model, a 128×128 cut-out
texture, a grounded / airborne / flap animation controller, and
momentum-preserving flight. The wings no longer push you forward every tick:
you keep the speed you build up, and pressing jump flaps the wings for lift and
a small forward boost.

## Folder layout

```
angel-wings/
├── AngelWings-1.2.0.mcaddon                  # packaged add-on
├── AngelWings.bbmodel                        # Blockbench source project
├── tools/
│   ├── generate_geometry.py                  # regenerates the wing geometry
│   └── generate_textures.py                  # regenerates the atlas, icon and pack icons
├── behavior_pack/
│   ├── manifest.json
│   ├── pack_icon.png
│   ├── items/angel_wings.json                # chest-slot wearable
│   └── scripts/angel_wings.js                # flight logic (Script API 2.x)
└── resource_pack/
    ├── manifest.json
    ├── pack_icon.png
    ├── animation_controllers/
    │   └── angel_wings.animation_controllers.json
    ├── animations/angel_wings.animation.json
    ├── attachables/angel_wings.json          # renders the wings when worn
    ├── models/entity/angel_wings.geo.json    # exported wing geometry
    ├── texts/en_US.lang
    ├── texts/languages.json
    ├── textures/item_texture.json            # item icon registration
    ├── textures/items/angel_wings.png        # 64×64 inventory icon
    └── textures/entity/angel_wings.png       # 128×128 worn-wing feather atlas
```

## The wing model

Open `AngelWings.bbmodel` in Blockbench to edit it. The project contains:

- `body` (root bone, pivot `[0, 24, 0]`, 6 cubes) — the back plate and clasp
- `left_wing` / `right_wing` (pivots `[±1.5, 23, 2.8]`, 6 cubes each)
- `left_wing_mid` / `right_wing_mid` (5 cubes each)
- `left_wing_tip` / `right_wing_tip` (6 cubes each)

That is **40 cubes in 7 bones**. The wings span **46 units** (2.875 blocks)
from tip to tip (`x = −23…+23`), are **11 units** tall (`y = 15…26`), and sit
**2–4.5 units behind the torso** (`z = 2…4.5`). The feather plates use
transparent cut-outs on the large faces and gold trim on the thin edges, so the
attachable uses the `entity_alphatest` material.

The `.bbmodel` contains numeric preview animations with the same IDs as the
shipped Molang animations. The resource-pack file
`resource_pack/animations/angel_wings.animation.json` is the source of truth for
the add-on; the previews are only for checking timing in Blockbench.

In Blockbench's viewport the model is at the back of the player, not at ground
level, so frame it with **F** (Frame Selection) if the camera is not already
centred on it.

## How to install

1. Open **`AngelWings-1.2.0.mcaddon`** to import both packs at once.
   Alternatively, copy the `behavior_pack` and `resource_pack` folders into the
   world's `behavior_packs/` and `resource_packs/` folders (or zip each folder
   and import it as `.mcpack`).
2. Enable **both** packs in the world settings.
3. Requirements:
   - Minecraft Bedrock **1.21.90 or newer** (Script API 2.x).
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
| Jump while on the ground | Normal jump; the wings stay folded |
| Jump again while airborne | Deploy the wings and start gliding |
| Hold jump while gliding | Flap continuously: lift plus a small forward boost |
| Look up / down | Trade speed for height / height for speed |
| Look around | Steer the glide |
| W / A / S / D | Air control; holding W adds speed |
| Sneak | Fold the wings and fall normally |

The glide preserves your momentum. There is no per-tick forward push: if you
stop steering you keep your current velocity and gradually lose height. A point
of durability is used once per second of flight (432 total, like the elytra)
and the wings can be repaired with phantom membranes. Slow falling is refreshed
while gliding so a hard landing does not hurt.

## How the animations work

`resource_pack/animation_controllers/angel_wings.animation_controllers.json`
switches between three states:

- **grounded** — plays `animation.angel_wings.idle` (folded V pose)
- **airborne** — plays `animation.angel_wings.glide` (spread, swept wings)
- **flap** — plays `animation.angel_wings.flap` while jump is held

The controller uses `query.is_on_ground` and `query.is_jumping`, so it needs no
script-side Molang variables. The attachable maps the short names `idle`,
`glide` and `flap` to the animation IDs and plays the controller through
`scripts.animate`.

The attachable uses the vanilla armor pattern:

```json
"scripts": {
  "parent_setup": "variable.chest_layer_visible = 0.0;",
  "animate": ["controller"]
},
"render_controllers": ["controller.render.armor"]
```

`controller.render.armor` (not `armor.v2`) is the controller used by vanilla
armor attachables. The material is `entity_alphatest` so the transparent feather cut-outs
render correctly, and `entity_alphatest_glint` provides the enchantment glint.

## Customising

- **Flight speed**: edit `GRAVITY`, `DRAG`, `MAX_HORIZONTAL_SPEED`,
  `GLIDE_LIFT`, `FLAP_LIFT`, `FLAP_FORWARD` and the other tuning constants at
  the top of `behavior_pack/scripts/angel_wings.js`.
- **Wing shape**: edit `tools/generate_geometry.py`, run
  `python3 tools/generate_geometry.py`, then import the exported geometry into
  `AngelWings.bbmodel` (or edit the cubes directly in Blockbench and
  `File → Export → Export Bedrock Model`).
- **Animations**: edit `resource_pack/animations/angel_wings.animation.json`;
  the Blockbench preview animations use the same names and values.
- **Textures**: the worn wings use
  `resource_pack/textures/entity/angel_wings.png` (128×128); the inventory icon
  uses `resource_pack/textures/items/angel_wings.png` (64×64). Run
  `python3 tools/generate_textures.py` to regenerate both, plus the 128×128
  pack icons.
- **Durability / repair**: edit `minecraft:durability` and
  `minecraft:repairable` in `behavior_pack/items/angel_wings.json`.

## Notes and limitations

- Flight is script-driven (`clearVelocity` + `applyImpulse`), not vanilla
  elytra gliding. Firework-rocket boosting and the vanilla elytra pose are not
  included.
- `player.isGliding` is read-only in the Bedrock Script API, so the animation
  controller uses `!query.is_on_ground` for the airborne state. The wings
  therefore also spread during a normal fall; the script only applies glide
  physics after you deploy them with a second jump.
- The wings flap while jump is held. Because `query.is_jumping` remains true
  while the jump action is held, holding jump gives continuous flapping.
- The attachable hides the vanilla chest armor layer, but a cape can still
  clip with the inner wings; remove the cape if you see overlap.
- The add-on has been statically validated (JSON, geometry, animation and
  texture references) but not run in a Bedrock client in this environment, so
  in-game behaviour should be checked on your device.

## Changelog

- **1.2.0** — new 40-cube / 7-bone wing model with a 46-unit wingspan, 128×128
  cut-out feather atlas, grounded / airborne / flap animation controller,
  momentum-preserving glide with WASD air control and pitch steering, jump-edge
  deployment, flap boost, new pack icons, and modern string item icons.
- **1.1.1** — tapered wing tips: two 1-unit tip feathers per wing replace the
  flat outer edge; the model is now 35 cubes (17 per wing + spine), still
  32 units wide.
- **1.1.0** — 32-unit layered wings (leading-edge arm, coverts, primaries,
  feather tips, central spine), swept-up 8° rest pose, new 64×64 worn-wing
  feather texture, separate transparent inventory icon, and an 8° flap.
- **1.0.0** — initial release.
