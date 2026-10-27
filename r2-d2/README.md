# R2-D2 Droid

A Minecraft Bedrock resource/behavior add-on that adds a detailed R2-D2 style
astromech droid. The droid is spawnable, follows the nearest player, rolls along
on its feet, turns its dome, makes little electronic beeps, chirps and whistles,
and can project a cyan hologram from its dome-mounted holoprojector.

## Install

1. Download **`R2D2-1.2.0.mcaddon`**.
2. Open it with Minecraft Bedrock (double-click, or **Open with → Minecraft**).
3. Enable **R2-D2 Droid** under **Settings → World → Behavior Packs** and
   **Resource Packs**.
4. Spawn the droid from the Creative inventory spawn egg, or with
   `/summon r2d2:droid`.

## Controls

- **Interact / right-click** the droid to toggle its holoprojector on or off.
- On touch controls, use the **Interact** button while looking at the droid.
- The action bar confirms `R2-D2 hologram online` or `R2-D2 hologram offline`.
- The hologram stays active while the droid follows you and can be switched off
  at any time with another interaction.

## Behaviour

- The droid is tamed to the nearest player when it spawns.
- It follows its owner, looks at players and idles on its own.
- It plays random beeps, chirps and whistles every few seconds.
- It is fire-immune, knockback-resistant and cannot be pushed.
- An animation controller switches between an idle scan and a rolling/leg
  animation when the droid moves.
- A separate animation controller reads the synced `r2d2:holo_active` entity
  property and plays the hologram animation while the projector is on.
- The hologram is a client-side particle effect anchored to two locators on the
  rotating dome bone: a rising beam at `holo_projector` and a star-map orb at
  `holo_display`.

## Model

The model was built in **Blockbench** and exported as `geometry.r2d2`.

- 106 cubes across six bones: `root`, `body`, `dome`, `left_leg`, `right_leg`
  and `center_foot`.
- 256×256 colour atlas with separate material patches for white panels, R2
  blue, dark blue, silver, steel, black, red and cyan lights.
- Layered dome, radar eye, status lights, holoprojector, twin antennas,
  shoulder hubs, body vents, leg vents, feet and centre foot.
- Separate idle, move and hologram animations.
- The dome carries `holo_projector` and `holo_display` locators for the
  holoprojector beam and holographic orb.

The editable Blockbench source is at `tools/r2d2.bbmodel`.

## Sounds

Custom sounds are defined in `resource_pack/sounds/sound_definitions.json`:

- `mob.r2d2.beep`
- `mob.r2d2.chirp`
- `mob.r2d2.whistle`
- `mob.r2d2.holo_on`
- `mob.r2d2.holo_off`

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
│   ├── particles/holo_beam.json
│   ├── particles/holo_orb.json
│   ├── particles/holo_motes.json
│   ├── textures/entity/r2d2.png
│   ├── sounds/
│   ├── texts/
│   └── pack_icon.png
├── tools/
│   ├── r2d2.bbmodel
│   └── validate.py
└── R2D2-1.2.0.mcaddon
```

## Validation

```bash
python3 tools/validate.py
```

The validator checks manifests, entity/client references, geometry bones,
holoprojector locators and UV bounds, idle/move/hologram animations, the
holoprojector particle files, sound files, texture dimensions and the packaged
`.mcaddon`.

## Notes

- Requires Minecraft Bedrock **1.21.90+**.
- Uses stable Script API **2.0.0**; the hologram uses a client-synced entity
  property and does not require experiments.
- The hologram is visual only: it does not deal damage, modify blocks or affect
  gameplay.
- This addon has been structurally validated, but not yet play-tested in a live
  Bedrock client. Test it in a copy of a world first.
