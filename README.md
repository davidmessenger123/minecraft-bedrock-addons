# Minecraft Bedrock Add-ons

Four add-ons for **Minecraft Bedrock Edition**:

| Add-on | Version | Download |
| --- | --- | --- |
| **Angel Wings** | 1.2.0 | [AngelWings-1.2.0.mcaddon](angel-wings/AngelWings-1.2.0.mcaddon) |
| **Mobile Phone** | 1.1.0 | [MobilePhone-1.1.0.mcaddon](mobile-phone/MobilePhone-1.1.0.mcaddon) |
| **Drone Companion** | 1.0.1 | [DroneCompanion-1.0.1.mcaddon](drone-companion/DroneCompanion-1.0.1.mcaddon) |
| **NZ Animals** | 1.1.0 | [NZ_Animals.mcaddon](nz-animals/NZ_Animals.mcaddon) |

## Install

1. Download the `.mcaddon` file for the add-on you want.
2. Open it with Minecraft Bedrock (double-click it, or use **Open with → Minecraft**).
   It imports the behavior and resource packs together.
3. Enable **both** packs for your world under **Settings → World → Behavior Packs** and
   **Resource Packs** (or Global Resources).
4. No experiments are required. The three scripted add-ons use stable Script API
   2.0.0 modules; if your build only exposes them behind **Beta APIs**, enable that
   experiment.
5. Reload the world.

## Angel Wings

A chest-slot angel-wing item with momentum-preserving, elytra-style flight.

- Item: `mod:angel_wings`
- Get it with `/give @s mod:angel_wings`, then equip it in the chest armor slot.
- Jump once to leave the ground, then jump again while airborne to deploy the wings.
- Hold jump to flap: each flap adds lift and a small forward boost.
- Look up/down to trade speed for height or height for speed; W/A/S/D gives air control.
- Sneak to fold the wings and fall normally.
- 432 durability, repaired with phantom membranes (one point per second of flight).
- 46-unit-wide, 40-cube layered feather model with a 128×128 cut-out atlas, rendered on
  the player's back through an attachable with grounded/airborne/flap animations.

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

## NZ Animals

29 New Zealand native species — birds, penguins, a tuatara, a weta, a huhu,
a Powelliphanta snail, seals and marine mammals — with custom models,
textures, spawn rules, animations and Creative spawn eggs.

- 29 species under the `nza:` namespace.
- Shared archetype builders give every species jointed wings and feathers,
  seal and penguin flippers, segmented swimmer bodies, six insect legs, and a
  flat spiral-disc snail shell.
- Per-profile walk and idle animations; collision boxes are body-only.
- Requires Bedrock **1.21.130+**.
- Summon with `/summon nza:kiwi`, or use the spawn eggs in the Creative inventory.

See [nz-animals/README.md](nz-animals/README.md) for the full roster,
measurements, model notes and build instructions. The
[contact sheet](nz-animals/preview/_contact_sheet.png) shows all 29 models.

## Requirements

- Minecraft Bedrock **1.21.90 or newer** for Angel Wings, Mobile Phone and Drone
  Companion; **1.21.130 or newer** for NZ Animals.
- The three scripted add-ons use stable Script API **2.0.0** modules (no experiments
  required; enable **Beta APIs** only if your build exposes those modules behind it).
  NZ Animals is data-only and has no Script API dependency.
- Angel Wings uses `@minecraft/server` **2.0.0**. If your game ships a newer 2.x module,
  update the version in `angel-wings/behavior_pack/manifest.json`.
- Mobile Phone and Drone Companion declare `@minecraft/server` **2.0.0** and
  `@minecraft/server-ui` **2.0.0**. If your game ships newer 2.x modules, update
  the versions in their `behavior_pack/manifest.json` (or `behaviour_pack/` for the
  phone).

## Source layout

| Folder | Contents |
| --- | --- |
| `angel-wings/` | Angel Wings behavior/resource packs, `.mcaddon`, Blockbench model, geometry and texture generators |
| `mobile-phone/` | Mobile Phone behavior/resource packs, `.mcaddon`, `.mcpack` alternatives, Blockbench model |
| `drone-companion/` | Drone Companion behavior/resource packs, `.mcaddon`, Blockbench model, texture and validation tools |
| `nz-animals/` | NZ Animals behavior/resource packs, `.mcaddon`, model/animation generators, validators and preview renders |

## Releases

- [Angel Wings 1.2.0](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/angel-wings-v1.2.0)
- [Mobile Phone 1.1.0](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/mobile-phone-v1.1.0)
- [Drone Companion 1.0.1](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/drone-companion-v1.0.1)
- [NZ Animals 1.1.0](https://github.com/davidmessenger123/minecraft-bedrock-addons/releases/tag/nz-animals-v1.1.0)
