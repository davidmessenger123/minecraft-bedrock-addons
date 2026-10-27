# R2-D2 Droid

A Minecraft Bedrock resource/behavior add-on that adds a detailed R2-D2 style
astromech droid. The droid is spawnable, follows the nearest player, rolls along
on its feet, turns its dome, and makes little electronic beeps, chirps and
whistles.

## Install

1. Download **`R2D2-1.1.0.mcaddon`**.
2. Open it with Minecraft Bedrock (double-click, or **Open with → Minecraft**).
3. Enable **R2-D2 Droid** under **Settings → World → Behavior Packs** and
   **Resource Packs**.
4. Spawn the droid from the Creative inventory spawn egg, or with
   `/summon r2d2:droid`.

## Behaviour

- The droid is tamed to the nearest player when it spawns.
- It follows its owner, looks at players and idles on its own.
- It plays random beeps, chirps and whistles every few seconds.
- It is fire-immune, knockback-resistant and cannot be pushed.
- An animation controller switches between an idle scan and a rolling/leg
  animation when the droid moves.

## Model

The model was built in **Blockbench** and exported as `geometry.r2d2`.

- 106 cubes across six bones: `root`, `body`, `dome`, `left_leg`, `right_leg`
  and `center_foot`.
- 256×256 colour atlas with separate material patches for white panels, R2
  blue, dark blue, silver, steel, black, red and cyan lights.
- Layered dome, radar eye, status lights, holoprojector, twin antennas,
  shoulder hubs, body vents, leg vents, feet and centre foot.
- Separate idle and move animations.

The editable Blockbench source is at `tools/r2d2.bbmodel`.

## Sounds

Custom sounds are defined in `resource_pack/sounds/sound_definitions.json`:

- `mob.r2d2.beep`
- `mob.r2d2.chirp`
- `mob.r2d2.whistle`

## Files

```text
r2-d2/
├── behavior_pack/
│   ├── manifest.json
│   ├── entities/r2d2_droid.json
│   ├── scripts/r2d2_droid.js
│   └── pack_icon.png
├── resource_pack/
│   ├── manifest.json
│   ├── animation_controllers/r2d2.animation_controllers.json
│   ├── animations/r2d2.animation.json
│   ├── entity/r2d2.entity.json
│   ├── models/entity/r2d2.geo.json
│   ├── textures/entity/r2d2.png
│   ├── sounds/
│   ├── texts/
│   └── pack_icon.png
├── tools/
│   ├── r2d2.bbmodel
│   └── validate.py
└── R2D2-1.1.0.mcaddon
```

## Validation

```bash
python3 tools/validate.py
```

The validator checks manifests, entity/client references, geometry bones and UV
bounds, animations, sound files, texture dimensions and the packaged `.mcaddon`.

## Notes

- Requires Minecraft Bedrock **1.21.90+**.
- Uses stable Script API **2.0.0**.
- This addon has been structurally validated, but not yet play-tested in a live
  Bedrock client. Test it in a copy of a world first.
