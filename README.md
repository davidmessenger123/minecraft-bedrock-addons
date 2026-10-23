# Minecraft Bedrock Add-ons

Three add-ons for **Minecraft Bedrock Edition 1.21.80+**:

| Add-on | Version | Download |
| --- | --- | --- |
| **Angel Wings** | 1.1.1 | [AngelWings-1.1.1.mcaddon](angel-wings/AngelWings-1.1.1.mcaddon) |
| **Mobile Phone** | 1.0.0 | [MobilePhone-1.0.0.mcaddon](mobile-phone/MobilePhone-1.0.0.mcaddon) |
| **Drone Companion** | 1.0.0 | [DroneCompanion-1.0.0.mcaddon](drone-companion/DroneCompanion-1.0.0.mcaddon) |

## Install

1. Download the `.mcaddon` file for the add-on you want.
2. Open it with Minecraft Bedrock (double-click it, or use **Open with → Minecraft**).
   It imports the behavior and resource packs together.
3. Enable **both** packs for your world under **Settings → World → Behavior Packs** and
   **Resource Packs** (or Global Resources).
4. Enable **Beta APIs** / **Script APIs** for the world. All three add-ons use the Script API.
5. Reload the world.

## Angel Wings

A chest-slot angel-wing item with scripted elytra-style flight.

- Item: `mod:angel_wings`
- Get it with `/give @s mod:angel_wings`, then equip it in the chest armor slot.
- Jump while grounded to take off; look up/down to climb or dive; look around to steer;
  sneak to cancel flight.
- 432 durability, repaired with phantom membranes (one point per second of flight).
- 32-unit-wide layered wing model with tapered tips, rendered on the player's back
  through an attachable.

See [angel-wings/README.md](angel-wings/README.md) for the full controls, model details,
and Blockbench source.

## Mobile Phone

A hand-held phone item with a 3D model and a form-based phone UI for running admin commands.

- Item: `phone:mobile_phone`
- Craft it with glass panes, redstone, iron, and an amethyst shard (see the phone README).
- Right-click while holding it to open the phone screen.
- Commands run as the player, so Bedrock's own permission system decides who can use them.

See [mobile-phone/README.md](mobile-phone/README.md) for the recipe, apps, and model details.

## Drone Companion

A summonable quadcopter companion with a controller item and a form-based order menu.

- Item: `drone:controller`
- Craft it with iron, redstone, copper, amethyst, and an ender pearl (see the drone README).
- Use the controller to summon your drone and open its menu.
- Orders: **Follow**, **Stay**, **Come**, **Scan**, **Light**, and **Defend**.
- Scan highlights nearby monsters; Light places a level-15 light block; Defend zaps the nearest monster.
- The drone is script-driven and hovers near you. It has no inventory or chest.

See [drone-companion/README.md](drone-companion/README.md) for the recipe, controls, model details, and Blockbench source.

## Requirements

- Minecraft Bedrock **1.21.80 or newer**
- **Beta APIs** / **Script APIs** enabled in the world
- Angel Wings uses `@minecraft/server` **2.0.0**. If your game ships a newer 2.x module,
  update the version in `angel-wings/behavior_pack/manifest.json`.
- Drone Companion declares `@minecraft/server` **2.0.0** and
  `@minecraft/server-ui` **2.0.0**. If your game ships newer 2.x modules, update
  the versions in `drone-companion/behavior_pack/manifest.json`.

## Source layout

| Folder | Contents |
| --- | --- |
| `angel-wings/` | Angel Wings behavior/resource packs, `.mcaddon`, Blockbench model, texture generator |
| `mobile-phone/` | Mobile Phone behavior/resource packs, `.mcaddon`, `.mcpack` alternatives, Blockbench model |
| `drone-companion/` | Drone Companion behavior/resource packs, `.mcaddon`, Blockbench model, texture and validation tools |

## Releases

- [Angel Wings 1.1.1](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/angel-wings-v1.1.1)
- [Mobile Phone 1.0.0](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/mobile-phone-v1.0.0)
- [Drone Companion 1.0.0](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/drone-companion-v1.0.0)
