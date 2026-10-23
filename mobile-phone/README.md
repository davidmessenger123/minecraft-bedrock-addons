# Mobile Phone — Bedrock Edition add-on

The Bedrock version of the phone: a **Mobile Phone** item with a 3D model that shows in the
player's hand, and a phone GUI that runs admin commands.

Two packs are needed (a resource pack and a behaviour pack). The ready-to-install
**`MobilePhone-1.0.0.mcaddon`** contains both; the individual `.mcpack` files are also here.

## Install

1. Open **MobilePhone-1.0.0.mcaddon** to import both packs at once. Alternatively,
   install **MobilePhone-Resources-1.0.0.mcpack** and
   **MobilePhone-Behaviour-1.0.0.mcpack** separately.
2. Activate both packs for your world (Settings → Global Resources / World → Resource Packs).
   On a dedicated server put the unpacked folders into `behavior_packs/` and `resource_packs/`
   and reference them in `world_behavior_packs.json` / `world_resource_packs.json`.
3. Make sure **Beta APIs** or **Script APIs** are enabled in the world (experimental gameplay).

Needs Minecraft Bedrock **1.21.80+** (the `minecraft:attachable` item component).

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
| **World** | Dimension, time, weather, player count and shortcuts. |
| **Player** | Your health, position and shortcuts. |
| **Players** | Everyone online, with actions for the one you pick. |
| **Server** | World info and server wide actions. |

## Permissions

The command runs **as the player** that holds the phone (`player.runCommand`), so Bedrock's own
permission system decides what happens: only server operators can actually run admin commands,
everyone else gets a red failure message. Nothing in the script can escalate a player.

## How the model works

The phone is a Bedrock attachable, so it renders as a 3D model in the hand instead of a flat
icon:

* `resource_pack/models/entity/mobile_phone.geo.json` — the geometry, made in Blockbench
  (3 cubes: body, screen, camera bump, 4 × 8 × 0.6 units, standing on the hand).
* `resource_pack/textures/entity/mobile_phone.png` — the 32 × 32 model texture. The right half is
  the lit screen with a wallpaper, a grid of app icons, a notch and a home indicator.
* `resource_pack/attachables/mobile_phone.json` — binds geometry, texture and render controller.
* `resource_pack/animation_controllers/item.phone.animation_controllers.json` — the hand
  transform. Tweak `rotation` and `scale` there if you want a different grip.

`model/mobile_phone.bbmodel` is the Blockbench project, open it to edit the model and re-export
the geometry and the texture.

## Differences to the Java Edition mod

* Bedrock only offers form based UI, so the phone is a set of forms (title, body, buttons, text
  field, dropdown) instead of the hand drawn phone shell of the Java version.
* The Script API does not expose the output of a command, so the phone reports success or failure
  instead of printing the command output. The output still shows up in the chat of the player.
