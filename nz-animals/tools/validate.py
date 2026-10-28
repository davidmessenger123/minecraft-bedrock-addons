"""
Cross-reference validator for the NZ Animals add-on.

Checks that every identifier, animation, controller and bone reference
resolves, so the pack cannot load with dangling references.
"""

from __future__ import annotations

import json
import re
import os
import sys


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    build = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
    bp = os.path.join(build, "behavior_pack")
    rp = os.path.join(build, "resource_pack")

    problems: list[str] = []
    notes: list[str] = []

    # --- manifests ---
    bp_manifest = load(os.path.join(bp, "manifest.json"))
    rp_manifest = load(os.path.join(rp, "manifest.json"))
    if bp_manifest["modules"][0]["type"] != "data":
        problems.append("behaviour pack module type is not 'data'")
    if rp_manifest["modules"][0]["type"] != "resources":
        problems.append("resource pack module type is not 'resources'")
    deps = rp_manifest.get("dependencies", [])
    if not any(d["uuid"] == bp_manifest["header"]["uuid"] for d in deps):
        problems.append("resource pack does not depend on the behaviour pack uuid")

    # --- entities ---
    bp_ids, bp_loot = set(), set()
    for f in sorted(os.listdir(os.path.join(bp, "entities"))):
        d = load(os.path.join(bp, "entities", f))
        ident = d["minecraft:entity"]["description"]["identifier"]
        if ident in bp_ids:
            problems.append(f"duplicate behaviour entity {ident}")
        bp_ids.add(ident)
        loot = d["minecraft:entity"]["components"].get("minecraft:loot")
        if loot:
            bp_loot.add(loot["table"])

    rp_ids = set()
    for f in sorted(os.listdir(os.path.join(rp, "entity"))):
        d = load(os.path.join(rp, "entity", f))
        desc = d["minecraft:client_entity"]["description"]
        rp_ids.add(desc["identifier"])
        if desc["identifier"] not in bp_ids:
            problems.append(f"client entity {desc['identifier']} has no behaviour entity")
        for tex in desc["textures"].values():
            p = os.path.join(rp, tex + ".png")
            if not os.path.exists(p):
                problems.append(f"missing texture {tex}.png")
        for geo in desc["geometry"].values():
            pass  # resolved below

    for ident in bp_ids - rp_ids:
        problems.append(f"behaviour entity {ident} has no client entity (invisible)")

    # --- spawn rules ---
    for f in sorted(os.listdir(os.path.join(bp, "spawn_rules"))):
        d = load(os.path.join(bp, "spawn_rules", f))
        desc = d["minecraft:spawn_rules"]["description"]
        if desc["identifier"] not in bp_ids:
            problems.append(f"spawn rule {desc['identifier']} has no entity")
        pc = desc["population_control"]
        if pc not in ("animal", "water_animal", "monster", "cat", "ambient", "pillager"):
            problems.append(f"invalid population_control '{pc}' for {desc['identifier']}")
        for cond in d["minecraft:spawn_rules"]["conditions"]:
            bf = cond.get("minecraft:biome_filter")
            if bf:
                vals = bf if isinstance(bf, list) else [bf]
                for v in vals:
                    if v.get("test") != "has_biome_tag":
                        problems.append(f"bad biome_filter test for {desc['identifier']}")

    # --- loot tables ---
    for t in bp_loot:
        p = os.path.join(bp, t)
        if not os.path.exists(p):
            problems.append(f"missing loot table {t}")
        else:
            d = load(p)
            if not isinstance(d.get("pools"), list):
                problems.append(f"loot table {t}: 'pools' must be an array")

    # --- geometry, animations, controllers ---
    geo_bones: dict[str, set[str]] = {}
    for f in sorted(os.listdir(os.path.join(rp, "models", "entity"))):
        d = load(os.path.join(rp, "models", "entity", f))
        g = d["minecraft:geometry"][0]
        geo_bones[g["description"]["identifier"]] = {b["name"] for b in g["bones"]}

    anim_bones: dict[str, set[str]] = {}
    for f in sorted(os.listdir(os.path.join(rp, "animations"))):
        d = load(os.path.join(rp, "animations", f))
        for name, anim in d["animations"].items():
            anim_bones[name] = set(anim.get("bones", {}).keys())

    controllers = set()
    for f in sorted(os.listdir(os.path.join(rp, "animation_controllers"))):
        d = load(os.path.join(rp, "animation_controllers", f))
        controllers |= set(d["animation_controllers"].keys())

    render_controllers = set()
    for f in sorted(os.listdir(os.path.join(rp, "render_controllers"))):
        d = load(os.path.join(rp, "render_controllers", f))
        render_controllers |= set(d["render_controllers"].keys())

    for f in sorted(os.listdir(os.path.join(rp, "entity"))):
        d = load(os.path.join(rp, "entity", f))
        desc = d["minecraft:client_entity"]["description"]
        sid = desc["identifier"]
        for geo_key, geo_id in desc["geometry"].items():
            if geo_id not in geo_bones:
                problems.append(f"{sid}: geometry {geo_id} not found")
                continue
            for anim_key, anim_id in desc["animations"].items():
                if anim_id.startswith("controller."):
                    if anim_id not in controllers:
                        problems.append(f"{sid}: animation controller {anim_id} not found")
                    continue
                if anim_id not in anim_bones:
                    problems.append(f"{sid}: animation {anim_id} not found")
                    continue
                missing = anim_bones[anim_id] - geo_bones[geo_id]
                if missing:
                    problems.append(
                        f"{sid}: animation {anim_id} animates bones not in {geo_id}: {sorted(missing)}")
        for rc in desc.get("render_controllers", []):
            if rc not in render_controllers:
                problems.append(f"{sid}: render controller {rc} not found")
        for ac in desc.get("scripts", {}).get("animate", []):
            target = desc["animations"].get(ac)
            if target is None:
                problems.append(f"{sid}: script animates unknown '{ac}'")

    # --- Molang queries used in animation controllers ---
    # `query.is_moving` is used by no vanilla Bedrock controller and never
    # evaluates for a mob; using it leaves every mob sliding with frozen legs.
    BANNED_QUERIES = ("query.is_moving",)
    movement_queries: set[str] = set()
    for f in sorted(os.listdir(os.path.join(rp, "animation_controllers"))):
        raw = open(os.path.join(rp, "animation_controllers", f), encoding="utf-8").read()
        d = json.loads(raw)
        for cid, ctrl in d["animation_controllers"].items():
            for st in ctrl.get("states", {}).values():
                for tr in st.get("transitions", []):
                    for expr in tr.values():
                        for bad in BANNED_QUERIES:
                            if bad in expr:
                                problems.append(
                                    f"{cid}: transition uses {bad}, which never evaluates "
                                    f"for a mob (use query.modified_move_speed)")
                        for q in re.findall(r"query\.[a-z_]+", expr):
                            movement_queries.add(q)
            # animation weights inside a state
            for st in ctrl.get("states", {}).values():
                for a in st.get("animations", []):
                    if isinstance(a, dict):
                        for expr in a.values():
                            for bad in BANNED_QUERIES:
                                if bad in expr:
                                    problems.append(f"{cid}: animation weight uses {bad}")
                            for q in re.findall(r"query\.[a-z_]+", expr):
                                movement_queries.add(q)
    for q in sorted(movement_queries):
        notes.append(f"movement query in use: {q}")

    # --- the animation clock must never be able to freeze ---
    # `anim_time_update: "query.modified_distance_moved"` re-bases
    # `query.anim_time` on a distance query. If that query does not advance
    # for a custom entity, `query.anim_time` is pinned at 0 and every bone
    # driven by it holds one pose forever - the mob looks like a statue.
    # The walk phase therefore comes from `query.life_time`, which always
    # advances.
    for f in sorted(os.listdir(os.path.join(rp, "animations"))):
        raw = open(os.path.join(rp, "animations", f), encoding="utf-8").read()
        d = json.loads(raw)
        for aid, anim in d["animations"].items():
            if "anim_time_update" in anim:
                problems.append(
                    f"{aid}: uses anim_time_update, which can freeze query.anim_time "
                    f"for a custom entity - drive the phase from query.life_time")
            if "query.anim_time" in raw:
                problems.append(
                    f"{aid}: drives a bone from query.anim_time - use query.life_time")
            if not anim.get("loop", False):
                problems.append(f"{aid}: is not set to loop")
            # A trailing comma inside a Molang string makes the whole
            # expression invalid in Bedrock; this was the reason the 1.1.0
            # idle clips failed to play in game.
            for bone_name, channels in anim.get("bones", {}).items():
                for channel, values in channels.items():
                    if isinstance(values, str):
                        values = [values]
                    if not isinstance(values, list):
                        continue
                    for expr in values:
                        if isinstance(expr, str) and re.search(r",\s*$", expr):
                            problems.append(
                                f"{aid}/{bone_name}.{channel}: trailing comma in "
                                f"Molang expression {expr!r}")

    # --- the walk and the idle are blended together, so they must not both
    #     drive the same bone or they fight over the channel ---
    for f in sorted(os.listdir(os.path.join(rp, "animations"))):
        d = load(os.path.join(rp, "animations", f))
        sets = {aid: set(a.get("bones", {})) for aid, a in d["animations"].items()}
        walks = {k: v for k, v in sets.items() if k.endswith(".walk")}
        idles = {k: v for k, v in sets.items() if k.endswith(".idle")}
        for wname, wbones in walks.items():
            for iname, ibones in idles.items():
                shared = wbones & ibones
                if shared:
                    problems.append(
                        f"{wname} and {iname} both drive {sorted(shared)} - blended "
                        f"animations must not fight over the same bone")

    # --- the controller's animation aliases must exist in the client entity ---
    # This is the layer that is easiest to get wrong: a valid animation file
    # and a valid controller do nothing until the client entity maps the
    # aliases the controller uses.
    anim_by_id: dict[str, set[str]] = {}
    for f in sorted(os.listdir(os.path.join(rp, "animations"))):
        d = load(os.path.join(rp, "animations", f))
        for aid, a in d["animations"].items():
            anim_by_id[aid] = set(a.get("bones", {}))
    ctrl_by_id: dict[str, dict] = {}
    for f in sorted(os.listdir(os.path.join(rp, "animation_controllers"))):
        d = load(os.path.join(rp, "animation_controllers", f))
        ctrl_by_id.update(d["animation_controllers"])
    for f in sorted(os.listdir(os.path.join(rp, "entity"))):
        sp = f[:-len(".entity.json")]
        desc = load(os.path.join(rp, "entity", f))["minecraft:client_entity"]["description"]
        alias_map = desc.get("animations", {})
        for alias, target in alias_map.items():
            if target.startswith("controller."):
                if target not in ctrl_by_id:
                    problems.append(f"{sp}: controller '{target}' does not exist")
                    continue
                for st in ctrl_by_id[target].get("states", {}).values():
                    for a in st.get("animations", []):
                        name = a if isinstance(a, str) else next(iter(a))
                        if name not in alias_map:
                            problems.append(
                                f"{sp}: controller '{target}' plays '{name}', which the "
                                f"client entity does not define")
                        elif alias_map[name] not in anim_by_id:
                            problems.append(
                                f"{sp}: animation '{alias_map[name]}' does not exist")
            elif target not in anim_by_id:
                problems.append(f"{sp}: animation '{target}' does not exist")

    # --- every animated bone must exist in the geometry ---
    # (the per-entity check further up already covers this)

    # --- geometry root bone is named after the species ---
    # Bedrock does not require the root bone to be called "root" (the schema
    # puts no constraint on bone names), so it is named after the animal -
    # which is what shows at the top of Blockbench's outliner.
    for f in sorted(os.listdir(os.path.join(rp, "models", "entity"))):
        sp = f[:-len(".geo.json")]
        d = load(os.path.join(rp, "models", "entity", f))
        bones = d["minecraft:geometry"][0]["bones"]
        roots = [b for b in bones if "parent" not in b]
        if len(roots) != 1:
            problems.append(f"{sp}: expected exactly one parentless root bone, got {len(roots)}")
            continue
        if roots[0]["name"] != sp:
            problems.append(
                f"{sp}: root bone is named '{roots[0]['name']}', expected '{sp}'")
        if any(b["name"] == "root" for b in bones):
            problems.append(f"{sp}: a bone is still named 'root'")
        for b in bones:
            if "parent" in b and b["parent"] not in {x["name"] for x in bones}:
                problems.append(f"{sp}: bone '{b['name']}' has unknown parent '{b['parent']}'")

    # --- proportion sanity ---
    # A horizontal torso must be longer than it is tall; an upright one
    # (a standing bird) must be deeper than it is wide.
    from roster import ROSTER
    upright = {s["id"] for s in ROSTER if s.get("scale_by") == "height"}
    for f in sorted(os.listdir(os.path.join(rp, "models", "entity"))):
        sp = f[:-len(".geo.json")]
        d = load(os.path.join(rp, "models", "entity", f))
        bones = d["minecraft:geometry"][0]["bones"]
        for b in bones:
            if b["name"] != "body":
                continue
            cubes = b.get("cubes", [])
            if not cubes:
                continue
            def extent(i):
                return (max(c["origin"][i] + c["size"][i] for c in cubes)
                        - min(c["origin"][i] for c in cubes))
            w, h, l = extent(0), extent(1), extent(2)
            # Below six model pixels, integer rounding dominates the
            # proportions; a 3-unit bird cannot preserve a 2.1:2.0 ratio.
            if max(w, h, l) < 6:
                continue
            if sp in upright:
                if l < w * 0.92:
                    problems.append(
                        f"{sp}: upright torso is wider than deep ({w} wide x {l} deep) "
                        f"- check the measurements in tools/roster.py")
            elif h > l * 1.08:
                problems.append(
                    f"{sp}: torso is taller than long ({h} high x {l} long) "
                    f"- check the measurements in tools/roster.py")

    # --- plausible model size ---
    # A measurement accidentally replaced by a palette colour produces a wildly
    # wrong model, so bound every species' footprint.
    for f in sorted(os.listdir(os.path.join(rp, "models", "entity"))):
        sp = f[:-len(".geo.json")]
        d = load(os.path.join(rp, "models", "entity", f))
        cubes = [c for b in d["minecraft:geometry"][0]["bones"] for c in b.get("cubes", [])]
        if not cubes:
            problems.append(f"{sp}: geometry has no cubes")
            continue
        ext = []
        for i in range(3):
            lo = min(c["origin"][i] for c in cubes)
            hi = max(c["origin"][i] + c["size"][i] for c in cubes)
            ext.append((hi - lo) / 16.0)
        biggest, smallest = max(ext), min(ext)
        if biggest > 18.0:
            problems.append(
                f"{sp}: model is {biggest:.1f} blocks long - check the measurements "
                f"in tools/roster.py")
        if smallest < 0.06:
            problems.append(
                f"{sp}: model is only {smallest:.2f} blocks in its smallest axis - "
                f"check the measurements in tools/roster.py")
        if len(cubes) < 5:
            problems.append(f"{sp}: only {len(cubes)} cubes - the model is too simple")



    # --- coplanar faces would z-fight and make the texture flicker ---
    face_normal = {
        "up": (1, 1), "down": (1, -1),
        "east": (0, 1), "west": (0, -1),
        "north": (2, 1), "south": (2, -1),
    }

    def face_plane(cube, face):
        axis, sign = face_normal[face]
        o, s = cube["origin"], cube["size"]
        coord = o[axis] + s[axis] if sign > 0 else o[axis]
        other = [i for i in range(3) if i != axis]
        return axis, sign, coord, (o[other[0]], o[other[0]] + s[other[0]]), \
            (o[other[1]], o[other[1]] + s[other[1]])

    for f in sorted(os.listdir(os.path.join(rp, "models", "entity"))):
        sp = f[:-len(".geo.json")]
        d = load(os.path.join(rp, "models", "entity", f))
        cubes = []
        for bone in d["minecraft:geometry"][0]["bones"]:
            for c in bone.get("cubes", []):
                cubes.append(c)
        for i in range(len(cubes)):
            for j in range(i + 1, len(cubes)):
                for fi in face_normal:
                    ai, si, ci, loi, hii = face_plane(cubes[i], fi)
                    for fj in face_normal:
                        aj, sj, cj, loj, hij = face_plane(cubes[j], fj)
                        if ai != aj or si != sj or ci != cj:
                            continue
                        # two faces pointing the same way, in the same plane,
                        # overlapping in the other two axes: z-fighting
                        if (min(hii[0], hij[0]) - max(loi[0], loj[0]) > 0
                                and min(hii[1], hij[1]) - max(loi[1], loj[1]) > 0):
                            problems.append(
                                f"{sp}: two '{fi}' faces are coplanar and overlapping - "
                                f"they will z-fight and the texture will flicker")

    # --- spawn eggs: BP is_spawnable + RP spawn_egg + lang keys ---
    for f in sorted(os.listdir(os.path.join(bp, "entities"))):
        d = load(os.path.join(bp, "entities", f))
        desc = d["minecraft:entity"]["description"]
        if desc.get("is_spawnable") is not True:
            problems.append(f"{desc['identifier']}: is_spawnable is not true (no creative egg)")

    for f in sorted(os.listdir(os.path.join(rp, "entity"))):
        d = load(os.path.join(rp, "entity", f))
        desc = d["minecraft:client_entity"]["description"]
        egg = desc.get("spawn_egg")
        if not egg:
            problems.append(f"{desc['identifier']}: no spawn_egg block (no creative egg)")
            continue
        if "base_color" not in egg and "texture" not in egg:
            problems.append(f"{desc['identifier']}: spawn_egg needs base_color or texture")
        if "base_color" in egg and "texture" in egg:
            problems.append(f"{desc['identifier']}: spawn_egg mixes base_color and texture")
        for k in ("base_color", "overlay_color"):
            if k in egg and not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(egg[k])):
                problems.append(f"{desc['identifier']}: spawn_egg.{k} is not #RRGGBB: {egg[k]}")

    # --- lang file coverage ---
    for pack in (bp, rp):
        lang = os.path.join(pack, "texts", "en_US.lang")
        if not os.path.exists(lang):
            problems.append(f"missing {lang}")
        else:
            with open(lang, encoding="utf-8") as fh:
                keys = {line.split("=", 1)[0] for line in fh if "=" in line}
            for ident in bp_ids:
                # Bedrock lang keys use dots: entity.<namespace>.<entity>.name
                flat = "entity." + ident.replace(":", ".") + ".name"
                ns = "entity." + ident + ".name"
                if ident.startswith("nza:") and flat not in keys and ns not in keys:
                    problems.append(f"no display name for {ident}")
                egg_flat = "item.spawn_egg.entity." + ident.replace(":", ".") + ".name"
                egg_ns = "item.spawn_egg.entity." + ident + ".name"
                if egg_flat not in keys and egg_ns not in keys:
                    problems.append(f"no spawn egg name for {ident}")

    # --- the roster itself: a palette colour must not appear as a measurement ---
    roster_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roster.py")
    if os.path.exists(roster_src):
        text = open(roster_src, encoding="utf-8").read()
        for block in text.split('    dict(id="')[1:]:
            sid = block.split('"')[0]
            if "pal=dict(" not in block:
                continue
            head, tail = block.split("pal=dict(", 1)
            meas = set(re.findall(r"\(([\d.]+(?:,\s*[\d.]+)+)\)", head))
            pal_cols = set(re.findall(r"\(([\d]+,\s*[\d]+,\s*[\d]+)\)", tail))
            clash = meas & pal_cols
            if clash:
                problems.append(
                    f"{sid}: the measurement call contains a palette colour {sorted(clash)} - "
                    f"a colour was written into a measurement")

    print(f"behaviour entities : {len(bp_ids)}")
    print(f"client entities    : {len(rp_ids)}")
    print(f"geometries         : {len(geo_bones)}")
    print(f"animation sets     : {len(anim_bones)}")
    print(f"controllers        : {len(controllers)} anim, {len(render_controllers)} render")
    for n in notes:
        print(n)
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nNo dangling references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
