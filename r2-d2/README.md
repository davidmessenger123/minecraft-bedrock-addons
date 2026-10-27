# R2-D2 Droid

A Minecraft Bedrock resource/behavior addon that adds an R2-D2 style astromech
droid. The droid is spawnable, follows the nearest player, rolls along on its
three feet, turns its dome, and makes little electronic beeps, chirps and
whistles.

## Install

1. Download **`R2D2-1.0.0.mcaddon`**.
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

## Model

The model was built in **Blockbench** (`tools/r2d2.bbmodel`) and exported as
`geometry.r2d2`. The dome, legs and centre foot have a looping idle animation.

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
│   ├── models/entity/r2d2.geo.json
│   ├── animations/r2d2.animation.json
│   ├── textures/entity/r2d2.png
│   ├── sounds/
│   ├── texts/
│   └── pack_icon.png
├── tools/
│   └── r2d2.bbmodel
└── R2D2-1.0.0.mcaddon
```

## Notes

- Requires Minecraft Bedrock **1.21.90+**.
- Uses stable Script API **2.0.0**.
- This addon has been structurally validated, but not yet play-tested in a live
  Bedrock client. Test it in a copy of a world first.
