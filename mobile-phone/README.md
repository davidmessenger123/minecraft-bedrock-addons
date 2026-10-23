# Mobile Phone — Bedrock Edition Add-on

The Bedrock version of the phone: a **Mobile Phone** item with a 3D model that
shows in the player's hand, and a phone GUI that runs commands.

Two packs are needed (a resource pack and a behaviour pack). The ready-to-install
**`MobilePhone-1.1.0.mcaddon`** contains both; the individual `.mcpack` files are
also here.

Version **1.1.0** fixes the hand model and the hotbar icon. The item now uses the
modern string `minecraft:icon`, the geometry is bound to the player's item slot
with `q.item_slot_to_bone_name(context.item_slot)`, and the hand transforms live
in a proper animation file instead of an invalid animation controller.

## Install

1. Open **MobilePhone-1.1.0.mcaddon** to import both packs at once. Alternatively,
   install **MobilePhone-Resources-1.1.0.mcpack** and
   **MobilePhone-Behaviour-1.1.0.mcpack** separately.
2. Activate both packs for your world (Settings → Global Resources / World → Resource Packs).
   On a dedicated server put the unpacked folders into `behavior_packs/` and `resource_packs/`
   and reference them in `world_behavior_packs.json` / `world_resource_packs.json`.
3. No experiments are required; the packs use stable Script API 2.0.0 modules. If your
   build only exposes them behind **Beta APIs**, enable that experiment.

Needs Minecraft Bedrock **1.21.90+**. The behavior pack declares
`@minecraft/server` **2.0.0** and `@minecraft/server-ui` **2.0.0**. If your game
ships different 2.x module versions, change the matching entries under
`dependencies` in `behaviour_pack/manifest.json`.

## Using the phone

Craft it in a crafting table (glass pane, redstone, iron ingot, amethyst shard):

```
 G R G
 I A I
 . I .
```

Right click with the phone in your hand to open the phone screen. The apps:

| App | What it does |
| --- | --- |
| **Terminal** | Type a command and run it. |
| **Admin** | Pick one of twelve admin shortcuts (time, weather, gamemode, effects, …) and run it. |
| **World** | Dimension, day, time, player count and shortcuts. |
| **Player** | Your health, position, dimension and shortcuts. |
| **Players** | Everyone online, with actions for the one you pick. |
| **Server** | World info and server-wide actions. |

The **Terminal** and dropdown screens use `ModalFormData`. Close the form (the
X button) to go back to the main menu; after a command runs, the same screen
reopens so you can run another one.

## Permissions

The command runs **as the player** that holds the phone (`player.runCommand`), so
Bedrock's own permission system decides what happens: only server operators can
actually run admin commands, everyone else gets a red failure message. Nothing
in the script can escalate a player.

## How the model works

The phone is a Bedrock attachable, so it renders as a 3D model in the hand
instead of a flat icon:

* `resource_pack/models/entity/mobile_phone.geo.json` — the geometry, made in
  Blockbench (3 cubes: body, screen, camera bump, 4 × 8 × 0.6 units). The root
  bone uses the Bedrock 1.16 model-binding format:
  `"binding": "q.item_slot_to_bone_name(context.item_slot)"`.
* `resource_pack/textures/entity/mobile_phone.png` — the 32 × 32 model texture.
  The right half is the lit screen with a wallpaper, a grid of app icons, a
  notch and a home indicator.
* `resource_pack/attachables/mobile_phone.json` — binds geometry, texture,
  render controller and the first/third-person animations.
* `resource_pack/animations/mobile_phone.animation.json` — the hand transforms
  for first and third person, selected with `context.is_first_person`.

`model/mobile_phone.bbmodel` is the Blockbench project. Its `body` group already
has the item-slot binding, so a re-export keeps the model attached to the hand.
The grip can be adjusted in `mobile_phone.animation.json`; the first-person
transform is based on the vanilla spyglass grip, and the third-person transform
stands the phone upright at the hand.

## Differences to the Java Edition mod

* Bedrock only offers form-based UI, so the phone is a set of forms (title,
  body, buttons, text field, dropdown) instead of the hand-drawn phone shell of
  the Java version.
* The Script API does not expose the output of a command, so the phone reports
  success or failure instead of printing the command output. The output still
  shows up in the chat of the player.
* `/save-all` is a Java command and is not used. The server shortcuts use
  Bedrock commands such as `/setworldspawn`, `/list`, `/kill` and `/weather`.

## Folder layout

```
mobile-phone/
├── MobilePhone-1.1.0.mcaddon
├── MobilePhone-Behaviour-1.1.0.mcpack
├── MobilePhone-Resources-1.1.0.mcpack
├── model/mobile_phone.bbmodel
├── behaviour_pack/
│   ├── manifest.json
│   ├── pack_icon.png
│   ├── items/mobile_phone.json
│   ├── recipes/mobile_phone.json
│   └── scripts/main.js
└── resource_pack/
    ├── manifest.json
    ├── pack_icon.png
    ├── animations/mobile_phone.animation.json
    ├── attachables/mobile_phone.json
    ├── models/entity/mobile_phone.geo.json
    ├── texts/en_US.lang
    ├── texts/languages.json
    ├── textures/entity/mobile_phone.png
    ├── textures/items/mobile_phone.png
    └── textures/item_texture.json
```

## Changelog

- **1.1.0** — fixed the hotbar icon with the modern string
  `minecraft:icon`; removed the invalid `minecraft:attachable` item component;
  upgraded the geometry to the 1.16 binding format and bound it to the item
  slot; replaced the malformed inline animation controller with proper
  first/third-person hand animations; rewrote the UI for
  `@minecraft/server-ui` 2.0.0 (`ModalFormData` dropdowns, `formValues`,
  `effectiveMax`, no `DropdownFormData`, no weather/seed APIs); declared the
  missing `@minecraft/server` and `@minecraft/server-ui` dependencies.
- **1.0.0** — initial release.
