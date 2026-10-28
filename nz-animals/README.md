# NZ Animals — a Minecraft Bedrock add-on

Adds New Zealand native animals that have **no equivalent mob in vanilla
Minecraft Bedrock**: 29 new species, each with its own model, texture, AI
profile, spawn rules and Creative-mode spawn egg.

## What changed in 1.1.8

- **Fixed the in-game animation failure.** Eight idle clips contained a
  trailing comma inside a Molang `position` expression
  (`"math.cos(...) * 0.6,"`). Bedrock rejected those clips, so the affected
  mobs stayed in their bind pose. The generator and validator now reject that
  pattern, and every animation expression parses cleanly.
- **Real-world sizing.** The roster now uses one real scale
  (**1 model unit = 6.25 cm**). Small birds, lizards and invertebrates are
  authored at a 24-unit internal resolution and rendered down with the
  client entity's `scripts.scale`, keeping their real size without collapsing
  their toes, eyes and feather tips into 1-unit blocks. Collision boxes are
  calculated at the displayed size.
- **Model detail pass.** Added bevel shading to the generated atlas, bird
  back-feather ridges, folded-wing feather tips, toe claws, a 24-unit detail
  pass for small species, and an octagonal, multi-stage Powelliphanta shell.
  The old z-fighting offset was reduced from 0.7 units to under 0.08 units so
  it cannot tear small models apart.
- Rebuilt all 29 models around the shared archetype builders: jointed wings
  with primary and secondary feathers, six insect legs, penguin and seal
  flippers, segmented swimmer bodies, and side-facing eyes.
- Walk and idle clips keep the per-profile motion; collision boxes exclude
  wings, fins, flippers, tails and antennae.

## Repository layout

```
nz-animals/
├── NZ_Animals.mcaddon      # packaged add-on
├── behavior_pack/          # generated behaviour pack
├── resource_pack/          # generated resource pack
├── tools/                  # generators, validators and audits
├── preview/                # offline isometric QA renders
└── README.md
```

The committed `behavior_pack/` and `resource_pack/` are the packs inside the
`.mcaddon`. `python3 tools/generate.py` rebuilds them into `build/` and
repackages the `.mcaddon`.

## Install

1. Copy `NZ_Animals.mcaddon` to your device (or open it directly).
2. In Minecraft Bedrock, open the pack — it imports both the behaviour and the
   resource pack.
3. Enable it for a world: **World Settings → Behaviour Packs / Resource Packs**.
4. `/summon nza:kiwi` to place one directly, or pick a spawn egg from the
   Creative inventory.

Requires Bedrock **1.21.130+**.

## The roster (29)

### Birds (12)

| id | Name | Spawns in | Notes |
|---|---|---|---|
| `nza:kiwi` | Kiwi | forest, plains | flightless, long bill, tiny vestigial wings |
| `nza:kakapo` | Kākāpō | forest | flightless nocturnal parrot |
| `nza:kea` | Kea | cold, hills | alpine parrot, red underwings |
| `nza:kaka` | Kākā | forest | forest parrot |
| `nza:tui` | Tūī | forest, plains | iridescent tui |
| `nza:hihi` | Hihi | forest | stitchbird, white wingbar |
| `nza:kereru` | Kererū | forest, plains | New Zealand pigeon |
| `nza:pukeko` | Pūkeko | swamp, river | swamphen, red wattles |
| `nza:morepork` | Morepork | forest | ruru, nocturnal owl |
| `nza:kotare` | Kōtare | river, beach | New Zealand kingfisher |
| `nza:tieke` | Tieke | forest | saddleback |
| `nza:whio` | Whio | river, swamp | blue duck |

### Penguins (3) — amphibious, walk and swim

| id | Name | Spawns in | Notes |
|---|---|---|---|
| `nza:rockhopper_penguin` | Rockhopper Penguin | cold, shore | yellow-crested, subantarctic |
| `nza:yellow_eyed_penguin` | Yellow-eyed Penguin | forest, beach, shore | nests in coastal forest |
| `nza:little_penguin` | Little Penguin | beach, shore | blue penguin |

### Land vertebrates & invertebrates (4)

| id | Name | Spawns in | Notes |
|---|---|---|---|
| `nza:tuatara` | Tuatara | forest, hills | last surviving rhynchocephalian |
| `nza:powelliphanta` | Powelliphanta | forest, swamp | giant land snail, *Powelliphanta* |
| `nza:weta` | Wētā | forest, plains | large flightless orthopteran |
| `nza:huhu` | Huhu | forest, plains | New Zealand beetle |

### Marine (7) — cool oceans only

| id | Name | Spawns in | Notes |
|---|---|---|---|
| `nza:nz_sea_lion` | New Zealand Sea Lion | shore, beach, ocean | amphibious |
| `nza:nz_fur_seal` | New Zealand Fur Seal | ocean, shore | amphibious |
| `nza:hectors_dolphin` | Hector's Dolphin | ocean | endangered, smallest dolphin |
| `nza:dusky_dolphin` | Dusky Dolphin | ocean | |
| `nza:orca` | Orca | ocean | black with white belly |
| `nza:sperm_whale` | Sperm Whale | ocean | square head, no dorsal fin |
| `nza:blue_shark` | Blue Shark | ocean | |

### Extinct (3)

| id | Name | Spawns in | Notes |
|---|---|---|---|
| `nza:moa` | Moa | forest, plains | giant flightless ratite, long neck |
| `nza:huia` | Huia | forest | extinct wattlebird, long curved bill and tail |
| `nza:haasts_eagle` | Haast's Eagle | forest, hills | extinct giant raptor, ~3 m wingspan |

### Deliberately excluded

Vanilla Bedrock already contains the only two New Zealand natives that have a
mob:

- `minecraft:turtle` **is** the green sea turtle (*Chelonia mydas*), and
  Bedrock's turtle has no variants.
- `minecraft:dolphin` **is** the bottlenose dolphin (*Tursiops truncatus*),
  also with no variants.

## Spawn biome tuning

Bedrock's `minecraft:biome_filter` matches biome **tags**, not biome names,
and the `conditions` array of a spawn rule holds **alternatives** while a
`biome_filter` array is **AND-ed**. The generator uses that to give each
species several valid biomes:

```json
"conditions": [
  { "...biome_filter": { "test": "has_biome_tag", "operator": "==", "value": "forest" }, ... },
  { "...biome_filter": { "test": "has_biome_tag", "operator": "==", "value": "plains" }, ... }
]
```

- **Land birds** are spread across `forest` and `plains` rather than forest
  only, so tūī, kererū and the moa are actually findable.
- **Wetland birds** use `swamp` and `river`; **riverside** birds use `river`
  and `beach`.
- **Alpine** species (kea) use `cold` and `hills`.
- **Marine** species are restricted to **cool** water by excluding the `warm`
  and `lukewarm` tags inside each filter:

  ```json
  "minecraft:biome_filter": [
    { "test": "has_biome_tag", "operator": "==",  "value": "ocean" },
    { "test": "has_biome_tag", "operator": "!=", "value": "warm" },
    { "test": "has_biome_tag", "operator": "!=", "value": "lukewarm" }
  ]
  ```

  so nothing turns up in a tropical sea.
- **Seals** and **penguins** are amphibious: they spawn on the surface (shore,
  beach) as well as in the water, and can swim.

## Creative-mode spawn eggs

Every one of the 29 species gets a spawn egg automatically. Bedrock
auto-generates the item; three pieces are required:

1. **Behaviour pack** `entities/<name>.json` — `"is_spawnable": true` (plus
   `is_summonable` and `is_experimental`).
2. **Resource pack** `entity/<name>.entity.json` — a `spawn_egg` block. The
   colours are derived from each species' own palette, so the egg matches the
   animal:
   ```json
   "spawn_egg": { "base_color": "#685A2F", "overlay_color": "#7A6438" }
   ```
   This produces the familiar speckled vanilla-style egg, tinted.
3. **Language file** — the egg's display name. Bedrock resolves entity names
   differently depending on the pack, so both the flattened and the namespaced
   key are written:
   ```
   entity.nza.kiwi.name=Kiwi
   entity.nza:kiwi.name=Kiwi
   item.spawn_egg.entity.nza.kiwi.name=Kiwi Spawn Egg
   item.spawn_egg.entity.nza:kiwi.name=Kiwi Spawn Egg
   ```

No `items/` folder, no `item_texture.json` entry and no egg PNG are needed —
Bedrock creates the item itself. `/give @s nza:kiwi_spawn_egg 1` also works.

## How it is built

```
build/
├── behavior_pack/          # manifest.json, entities, spawn_rules, loot_tables, texts
└── resource_pack/          # manifest.json, models, textures, entity, animations, ...
```

`build/` is generated; the top-level `behavior_pack/` and `resource_pack/`
are the committed copies of it, and are what the `.mcaddon` contains.

* **Namespace** `nza:` for every entity.
* **Manifests** use `format_version: 2` with `min_engine_version: [1, 21, 130]`.
  The resource pack declares a dependency on the behaviour pack's uuid.
* **Geometry** is Bedrock box-UV (`uv` offsets into the texture). 1 model unit
  = 1 texture pixel, so textures are 256×N power-of-two.
* **The root bone is named after the animal** (`kiwi`, `nz_sea_lion`, …) rather
  than the usual `root`. Bedrock does not require the name `root` — the
  geometry schema puts no constraint on bone names, and Blockbench's Bedrock
  codec exports whatever the group is called. The benefit is that the top of
  Blockbench's outliner says which animal you are looking at.
* **Animations** are shared by motion profile rather than per species, so each
  species only supplies geometry and a palette:
  `bird_fly`, `bird_ground`, `quadruped`, `seal`, `penguin`, `ratite`, `swim`,
  `insect`, `snail`. Each has one animation controller and a walk + idle pair.
* **Loot tables** use the array form of `pools` with `set_count`.

### The models are proportion-accurate

Every species is described in **real-world centimetres** in `tools/roster.py`,
and the builders lay the animal out in those centimetres — so the proportions
are literally correct rather than eyeballed. The generator now uses one shared
conversion for the whole roster: **1 Minecraft unit = 6.25 cm**. Very small
invertebrates receive a 3-unit floor so they remain visible at Minecraft's
resolution; everything else is scaled at real-world relative size.

The measurements are **sourced, not invented**:

| Source | What it provides |
|---|---|
| Te Papa Biostore | specimen medians for bill, tarsus, toe-and-claw, wing chord and tail (n = 23–168 per species) |
| NZ Birds Online | length and mass |
| DOC Sci-Tech Report 58 | a full morphometric set for the yellow-eyed penguin |
| Te Ara / DOC | tuatara, seal and invertebrate figures |
| Wikipedia | totals and mass for the remainder |

Torso and skull sub-dimensions are not published directly, so those are
**derived** by arithmetic from the published totals and are marked `D` in
`tools/roster.py`.

Those measurements are taken on the animal **lying down**, so the axis has to
be rotated for anything that stands: a penguin's torso is 19.5 cm *long* along
its back, which for a standing bird is a **vertical** axis. Species that
stand upright are marked `scale_by="height"` in the roster, and
`tools/validate.py` checks the proportion the right way round for each —
a horizontal torso must be longer than it is tall, an upright one deeper than
it is wide. That check is what caught the first penguins looking like
barrels.

The geometry is not traced pixel-for-pixel from art, but every colour and
marking is checked against a photograph (see below).

### No two boxes share a face plane

A Minecraft box model is made of overlapping boxes, and two boxes whose
faces lie in the same plane, point the same way and overlap are drawn at
exactly the same depth. The renderer has to pick one and alternates between
them every frame, so **the texture flickers**.

This was not a modelling mistake so much as a rounding one. The torso is
authored with a chest and a rump slightly narrower than the body, but after
scaling to Minecraft units those widths often round to the *same* integer,
and the flanks end up flush. The build had **591 coplanar face pairs across
the 29 models**.

The fix is applied after scaling, in `Model.deconflict()`: every box is
given its own small offset — the same offset on all three axes so the model
keeps its shape. The offsets are centred on zero, then the generator
re-grounds the model so its lowest box sits exactly at y=0. Because the
offsets are distinct and the largest is well under one unit, two boxes can
no longer share a face plane: their integer coordinates would have to differ
by exactly the offset between them, and no offset pair is a whole unit.

Overlaps do not matter — z-fighting needs coplanarity *and* overlap — and
the box **sizes never change**, so the texture layout is untouched. A box is
1/16 of a block, so the shift is invisible.

`tools/check_zfight.py` reports the count (now zero) and `validate.py` fails
the build if any pair ever reappears.

### The textures are grounded in reference photographs
Geometry comes from published measurements, but **colour and marking
placement** come from real photographs. `tools/fetch_refs.py` pulls one
reference image per species from Wikimedia Commons, searched by **scientific
name** (which is far more accurate than a common name, and for extinct
species returns the museum reconstructions):

```sh
python3 tools/fetch_refs.py     # -> refs/<species>.jpg
```

`tools/extract_palette.py` then samples a candidate palette out of each
photo — it drops the frame border as background and quantises what is left.
That extraction is only a starting point (photos are lit, and a studio sweep
beats the animal for most of the frame), so the shipped palettes are the
extraction **corrected by eye against the photograph**.

That pass changed a lot, and mostly in the direction of "the real animal is
not the colour I assumed":

| species | what the photograph corrected |
|---|---|
| `tui` | the bill is **black**, not orange; the wing coverts are iridescent blue |
| `pukeko` | the bill is **red**, not yellow |
| `kea` | the upper mandible is **black** over an orange lower mandible, the iris is **bright yellow**, and the crimson is the **undertail coverts** — not the whole tail |
| `kotare` | the breast is **orange-buff**, not white; the throat stays white |
| `whio` | the breast is **pinkish-buff**, not white |
| `hihi` | a **warm brown** bird, not a black one, with pink legs |
| `rockhopper_penguin` | a **red** iris, an **orange-red** bill, **pink** feet, a gold crest |
| `tieke` | the head is **black**; the chestnut belongs on the **throat** and the shoulder saddle |
| `huia` | glossy **black** throughout; the white is a thigh tuft and a tail band |
| `haasts_eagle` | a **dark** bill, not a yellow one |
| `kiwi` | **golden** brown with pinkish legs |
| `moa` | pale **brown** underparts, not sage green |
| `hectors_dolphin`, `dusky_dolphin`, `sperm_whale` | mid/warm greys, not washed-out or blue ones |

Run `python3 tools/fetch_refs.py` to download the reference photographs into
`refs/` if you want to re-check the colours against them.

The displayed size is the real-world size: a kiwi is about 0.45 blocks long,
a tui about 0.3 blocks, a moa about 2.6 blocks tall and an orca about 6.9
blocks long. Species below 24 model units are authored at 24 units and scaled
down on the client, so their geometry keeps useful detail at those small
sizes. The only deliberate exception is a **3-unit floor** for the tiniest
invertebrates, which would otherwise disappear below Minecraft's rendering
resolution. The files in `preview/` render that internal detail mesh, so they
show the modelling detail rather than the smaller in-game projection.

Each model is built from many small boxes rather than one blob:

| Part | Boxes |
|---|---|
| Body | belly + torso + chest + rump + shoulder/hip masses (counter-shaded) |
| Head | neck + skull + brow + beak/muzzle + optional crest |
| Legs | thigh + shank + foot (birds and quadrupeds); coxa + femur + knee + tibia + tarsus (insects) |
| Wings | three swept segments plus separated secondary and primary feathers |
| Flippers | swept base + mid + tip paddles, angled down and back |
| Penguins | upright torso + neck + three-segment flippers |
| Swimmers | segmented chest/mid/rear body + melon/rostrum + dorsal fin + flukes |
| Tuatara | a row of tapering dorsal crest spikes |
| Weta | six legs of coxa + femur + knee + tibia + tarsus, plus leg spines |
| Snail | flat spiral-disc shell + foot + eye stalks |
| Moa | a two-stage tapering neck that leans forward |

**1,280 boxes across the 29 models**, against 134 for the first pass.

The **collision box** is derived from the torso, head and leg bones, not from
the full model bounds. A kea's spread wings or an orca's flukes are part of
the render but not part of the hitbox, so a bird does not become a
three-block-wide obstacle when it flies.

### The textures

Each species has a **texture recipe** in `tools/textures_recipes.py` — a list of
markings painted onto the model's cubes. The painter supports:

| marking | what it does |
|---|---|
| `eye` | sclera, coloured iris, black pupil, white highlight |
| `oval` | a soft-edged patch (throat tuft, eye patch, saddle patch) |
| `rect` / `band` / `vband` | a rectangular patch, horizontal band or vertical band |
| `spots` / `speckle` | scattered spots or fine mottling |
| `scales` | overlapping arcs, for reptilian and fish skin |
| `streak` | fine directional strokes, for fur and feather |
| `spiral` | a square spiral line, for the flat spiral-disc shell |

Markings name a cube, and match it exactly or as a suffix — so `wing_upper`
hits both `left_wing_upper` and `right_wing_upper`. The face `outer` is
mirrored, putting a marking on whichever flank of a limb actually faces the
player; the face `sides` paints both east and west, which is what a
side-facing eye needs.

The recipes are what make each animal recognisable rather than a recoloured
blob: the tui's white throat tuft and wingbar, the hihi's wingbar and white
tail band, the kea and kaka's red underwings, the pukeko's red wattles and
legs, the tieke's chestnut shoulder flash, the morepork's pale facial disc,
the kakapo's green flecking, the orca's white eye patch and grey saddle, the
shark's countershading, the powelliphanta's painted spiral shell, the tuatara's pale
speckles.

Colours come from the species palette, so a marking can be a palette key
(`throat`, `pale`, `wattle`, `band`, `dark`) or a shade factor, which keeps
each marking in the animal's own colour family.

### How locomotion actually works

This is the part that is easy to get wrong, and it went wrong twice, so it is
worth spelling out.

### The controller

Every controller follows the vanilla pattern exactly — the walk animation is
always in the graph and its **weight** is a 6x multiple of the mob's move
speed, clamped to 1:

```json
"controller.animation.nza.bird_ground": {
  "initial_state": "default",
  "states": {
    "default": {
      "blend_transition": 0.2,
      "animations": [
        { "walk": "math.min(1.0, query.modified_move_speed * 6.0)" },
        "idle"
      ]
    }
  }
}
```

`query.modified_move_speed` is the same scalar vanilla Bedrock mobs use — the
sheep, spider, fox, goat and llama all drive their walk with
`{"walk": "query.modified_move_speed"}`. The 6x multiplier makes the legs
reach a readable stride as soon as the mob starts moving instead of
fading in only at full sprint.

An earlier revision of this pack used a **state machine** instead:

```json
"transitions": [ { "moving": "query.modified_move_speed > 0.01" } ]
```

which looks equivalent but is not. If that transition never fires, the mob is
left holding whatever the default state contains, and every mob in this pack
became a statue. A weight has no such failure mode: the walk is in the graph
from the first frame and is simply faded in and out with the speed.

`tools/validate.py` rejects any controller that uses `query.is_moving`, which
is used by no vanilla controller and never evaluates for a mob.

### The clock

The walk phase comes from **`query.life_time`**, the entity's age in seconds:

```json
"left_leg":  { "rotation": [ "math.cos(query.life_time * 8.0 * math.max(query.modified_move_speed, 0.25)) * 32.0", 0.0, 0.0 ] },
"right_leg": { "rotation": [ "math.cos(query.life_time * 8.0 * math.max(query.modified_move_speed, 0.25)) * -32.0", 0.0, 0.0 ] }
```

The second revision of this pack used vanilla's own distance-locked form:

```json
"anim_time_update": "query.modified_distance_moved",
"bones": { "left_leg": { "rotation": [ "math.cos(query.anim_time * 38.17) * 26.0", ... ] } }
```

`anim_time_update` re-bases `query.anim_time` onto a distance query. Vanilla
gets away with that because its mobs are native; for a data-driven entity the
distance query is not guaranteed to advance, and when it does not,
`query.anim_time` is pinned at 0 and **every bone driven by it holds one pose
forever**. The mobs appeared to slide with their legs locked in mid-stride.

`query.life_time` always advances, for every entity. The vanilla dolphin uses
nothing else. The cycle rate is scaled by the move speed so the stride keeps
up with the ground, with a floor so it can never be frozen solid:

```
math.cos(query.life_time * 8.0 * math.max(query.modified_move_speed, 0.25))
```

8 rad/s is about 1.3 strides a second — slow enough to read.

Rhythmic motion (wing flap, tail wag, fin stroke) has always been time-based.

### The idle

The walk and the idle deliberately drive **different bones**, so that blending
them together never double-drives a channel, and so that a standing mob is
never a statue either:

| profile | walk drives | idle drives |
|---|---|---|
| `bird_ground` | legs, body roll, tail | head, folded wings |
| `quadruped` | four legs, body | head, tail |
| `ratite` | legs, body, neck | head, tail |
| `seal` | four flippers, body | head, tail |
| `penguin` | feet, body, flippers | head, tail |
| `insect` | six legs, body, abdomen | head, antennae |
| `snail` | body, shell | head, tentacles |
| `bird_fly` | wings, body, tail | head, legs |
| `swim` | tail, body, fins | head |

`tools/validate.py` fails the build if the walk and the idle of one profile
share a bone, if any animation uses `anim_time_update` or `query.anim_time`,
or if a controller plays an alias the client entity does not define.

`tools/check_motion.py` goes one step further and *evaluates* every generated
Molang expression over four seconds, to prove each channel actually swings and
at a readable rate:

```
animation.nza.bird_ground.walk    left_leg    26.00 deg    1.00 cycles/s
animation.nza.quadruped.walk      left_front_leg  24.00 deg  1.00 cycles/s
```

## Reinstalling

The pack keeps the same UUIDs so it updates in place, and the **version is
bumped on every build** (`tools/VERSION`, incremented by the generator).
That matters: Bedrock identifies a pack by *(uuid, version)*, so a rebuild
that reuses the version can be silently ignored on import and the old files
stay installed — which looks exactly like the fix doing nothing.

To be sure you are running the current build:

1. Remove the existing **NZ Animals** behaviour and resource packs from the
   world (and from the global pack list).
2. Import `NZ_Animals.mcaddon` again.
3. Check the pack's version in the pack list — it should be higher than the
   one you had.

## Regenerating

```sh
python3 tools/generate.py     # writes build/ and NZ_Animals.mcaddon
python3 tools/validate.py     # cross-checks every identifier, bone and file
python3 tools/audit_textures.py  # checks textures are painted and UV-covered
python3 tools/check_motion.py     # evaluates the Molang and checks it swings
python3 tools/check_zfight.py     # counts coplanar faces that would z-fight
python3 tools/audit_behaviour.py  # components vs Mojang's own corpus
python3 tools/preview.py      # isometric previews -> preview/
python3 tools/preview.py --structure   # same, but colour-coded per cube
python3 tools/fetch_refs.py   # reference photographs -> refs/
python3 tools/extract_palette.py      # candidate palettes from those photos
```

| file | purpose |
|---|---|
| `tools/nzlib.py` | box-UV maths, texture packing and painting, geo export |
| `tools/nzarchetypes.py` | parametric body plans (bird, quadruped, swimmer, insect, snail, penguin, ratite) |
| `tools/roster.py` | the species roster: real measurements, palettes, behaviour |
| `tools/textures_recipes.py` | per-species texture markings, and the shared palette builder |
| `tools/generate.py` | the pack writer |
| `tools/validate.py` | dangling-reference and spawn-egg checker |
| `tools/audit_textures.py` | texture/UV coverage and animation-wiring audit |
| `tools/check_motion.py` | evaluates the generated Molang and checks it actually moves |
| `tools/check_zfight.py` | counts coplanar box faces that would z-fight |
| `tools/audit_behaviour.py` | checks every component and field against Mojang's own corpus |
| `tools/preview.py` | offline isometric renderer used for QA |
| `tools/fetch_refs.py` | downloads the Wikimedia Commons reference photographs |
| `tools/extract_palette.py` | samples candidate palettes out of those photographs |

To add a species, append an entry to `ROSTER` in `tools/roster.py` and
re-run the commands above. `validate.py` will tell you if the bone names in
the animation profile do not match the geometry.

## The checks that guard the build

The generators are only worth having if they fail loudly when something is
wrong, so `validate.py` and `audit_textures.py` carry a few deliberately
sharp checks:

| check | what it catches |
|---|---|
| `query.is_moving` is rejected outright | the animation bug that made every mob slide with frozen legs |
| `anim_time_update` and `query.anim_time` are rejected | the animation bug that froze every bone in one pose |
| the walk and the idle may not share a bone | two blended animations fighting over one channel |
| a controller may only play aliases the client entity defines | the layer that is easiest to get wrong: valid files that do nothing |
| every animated bone must exist in the geometry | an animation left over from a renamed model |
| `check_motion.py` evaluates every expression | a channel that technically animates but swings by 0.2° |
| a palette colour may not appear in a measurement call | a botched edit that writes `(146, 108, 58)` into the kiwi's body length instead of `(26.6, 14.0, 18.6)` |
| every model's longest axis must be ≤ 8 blocks, its shortest ≥ 0.06 | a nonsense measurement |
| every marking colour must resolve in the species palette | a marking silently painted in the cube's own colour, i.e. invisible |
| every cube's UV net must lie inside the texture | a face sampling past the edge of the bitmap |
| no two boxes may share a face plane | z-fighting, which shows up as a flickering texture |
| spawn eggs must exist for all 29 species, in both packs and the lang file | a species that cannot be spawned in Creative |

## Diagnosing a pack that will not load

If Minecraft reports that a pack failed to load, the exact reason is in the
**Content Log**: pause the game → *Content Log* (on Bedrock it is the
"Content Log" button in the pause menu, or the `/content` command on
desktop). It names the file and the reason — a JSON syntax error, an
unknown component, a bad value.

Two things to check first, because they are the common ones:

1. **Remove the old pack before importing the new one.** Bedrock identifies
   a pack by *(uuid, version)*; importing a rebuild over an installed copy
   can leave a mixture of old and new files. Delete both the behaviour and
   the resource pack, then import again.
2. **Check the version.** `tools/VERSION` is bumped on every build and
   stamped into both manifests, so the pack list shows which build is
   installed.

## Licence

MIT. Models and textures are original work generated by the scripts in
`tools/`.
