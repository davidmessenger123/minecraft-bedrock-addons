#!/usr/bin/env python3
"""Rebuild the editable AngelWings.bbmodel from the generated geometry.

The shipped geometry is the source of truth.  This script replaces the cube and
bone layout in the existing Blockbench project while preserving the project's
embedded texture, preview animations and metadata.  Open the resulting
AngelWings.bbmodel in Blockbench to inspect or continue editing the mesh.

Run from the project root:

    python3 tools/generate_geometry.py
    python3 tools/generate_textures.py
    python3 tools/rebuild_bbmodel.py
"""
import base64
import json
import os
import uuid


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BBMODEL = os.path.join(ROOT, "AngelWings.bbmodel")
GEO = os.path.join(ROOT, "resource_pack", "models", "entity",
                   "angel_wings.geo.json")
TEXTURE = os.path.join(ROOT, "resource_pack", "textures", "entity",
                       "angel_wings.png")
ANIMATIONS = os.path.join(ROOT, "resource_pack", "animations",
                          "angel_wings.animation.json")
NS = uuid.UUID("7c1e4d18-7b0e-4d71-9d97-6f6b1e8caf10")


def stable(prefix, name):
    return str(uuid.uuid5(NS, prefix + "/" + name))


def build_animations(group_uuids):
    """Create Blockbench preview animators from the shipped Molang clips.

    Blockbench animations target group UUIDs, not bone names.  Rebuilding the
    groups without refreshing these keys is why the previous project appeared
    to lose its animations.
    """
    data = json.load(open(ANIMATIONS, encoding="utf-8"))["animations"]
    out = []
    for name, clip in data.items():
        bones = clip.get("bones", {})
        animators = {}
        for bone_name, channels in bones.items():
            group_uuid = group_uuids.get(bone_name)
            if not group_uuid:
                continue
            keyframes = []
            for channel, times in channels.items():
                if channel != "rotation":
                    continue
                for time_text, values in times.items():
                    keyframes.append({
                        "channel": "rotation",
                        "data_points": [{
                            "x": str(values[0]),
                            "y": str(values[1]),
                            "z": str(values[2]),
                        }],
                        "uuid": stable("key", name + "/" + bone_name + "/" + time_text),
                        "time": float(time_text),
                        "color": -1,
                        "interpolation": "linear",
                    })
            keyframes.sort(key=lambda key: key["time"])
            if keyframes:
                animators[group_uuid] = {
                    "name": bone_name,
                    "type": "bone",
                    "rotation_global": False,
                    "quaternion_interpolation": False,
                    "keyframes": keyframes,
                }
        out.append({
            "uuid": stable("animation", name),
            "name": name,
            "loop": "loop" if clip.get("loop", True) else "once",
            "override": False,
            "length": clip.get("animation_length", 4.0),
            "snapping": 10,
            "selected": False,
            "saved": False,
            "path": "",
            "scope": 0,
            "anim_time_update": "",
            "blend_weight": "",
            "start_delay": "",
            "loop_delay": "",
            "animators": animators,
        })
    return out


def face_entry(face, texture_id=0):
    uv = face["uv"]
    size = face["uv_size"]
    return {
        "uv": [uv[0], uv[1], uv[0] + size[0], uv[1] + size[1]],
        "texture": texture_id,
    }


def cube_entry(cube, parent_name, index):
    origin = cube["origin"]
    size = cube["size"]
    pivot = cube.get("pivot", [0, 0, 0])
    rotation = cube.get("rotation", [0, 0, 0])
    entry = {
        "name": "%s_%02d" % (parent_name, index + 1),
        "box_uv": False,
        "render_order": "default",
        "locked": False,
        "export": True,
        "scope": 0,
        "allow_mirror_modeling": True,
        "from": [round(v, 3) for v in origin],
        "to": [round(origin[i] + size[i], 3) for i in range(3)],
        "autouv": 0,
        "color": 0,
        "origin": [round(v, 3) for v in pivot],
        "faces": {name: face_entry(face) for name, face in cube["uv"].items()},
        "type": "cube",
        "uuid": stable("cube", "%s/%d" % (parent_name, index)),
    }
    if any(abs(v) > 0.0001 for v in rotation):
        entry["rotation"] = [round(v, 3) for v in rotation]
    return entry


def main():
    with open(BBMODEL, encoding="utf-8") as fh:
        doc = json.load(fh)
    with open(GEO, encoding="utf-8") as fh:
        geo = json.load(fh)["minecraft:geometry"][0]
    with open(TEXTURE, "rb") as fh:
        texture_b64 = base64.b64encode(fh.read()).decode("ascii")

    bones = geo["bones"]
    groups = {}
    elements = []
    cube_ids_by_bone = {}

    for bone in bones:
        name = bone["name"]
        group = {
            "name": name,
            "uuid": stable("group", name),
            "export": True,
            "locked": False,
            "scope": 0,
            "selected": False,
            "visibility": True,
            "_static": {"properties": {}, "temp_data": {}},
            "origin": [round(v, 3) for v in bone.get("pivot", [0, 0, 0])],
            "rotation": [round(v, 3) for v in bone.get("rotation", [0, 0, 0])],
            "bedrock_binding": "",
            "color": len(groups) % 7,
            "children": [],
            "reset": False,
            "shade": True,
            "mirror_uv": False,
            "autouv": 0,
            "isOpen": False,
            "primary_selected": False,
        }
        groups[name] = group
        cube_ids_by_bone[name] = []
        for i, cube in enumerate(bone.get("cubes", [])):
            element = cube_entry(cube, name, i)
            elements.append(element)
            cube_ids_by_bone[name].append(element["uuid"])

    # Root bone children, plus nested wing chains.  The body group is the only
    # root entry, matching the existing project and the Bedrock bone hierarchy.
    body_children = list(cube_ids_by_bone["body"])
    for wing_name in ("left_wing", "right_wing"):
        mid_name = wing_name + "_mid"
        tip_name = wing_name + "_tip"
        wing_node = {
            "uuid": groups[wing_name]["uuid"],
            "isOpen": False,
            "children": list(cube_ids_by_bone[wing_name]) + [{
                "uuid": groups[mid_name]["uuid"],
                "isOpen": False,
                "children": list(cube_ids_by_bone[mid_name]) + [{
                    "uuid": groups[tip_name]["uuid"],
                    "isOpen": False,
                    "children": list(cube_ids_by_bone[tip_name]),
                }],
            }],
        }
        body_children.append(wing_node)

    body_node = {
        "uuid": groups["body"]["uuid"],
        "isOpen": False,
        "children": body_children,
    }

    doc["name"] = "AngelWings"
    doc["model_identifier"] = geo["description"]["identifier"]
    doc["visible_box"] = [
        geo["description"].get("visible_bounds_width", 5.5),
        geo["description"].get("visible_bounds_height", 4.0),
        geo["description"].get("visible_bounds_offset", [0, 1.5, 0])[1],
    ]
    doc["resolution"] = {
        "width": geo["description"]["texture_width"],
        "height": geo["description"]["texture_height"],
    }
    doc["elements"] = elements
    doc["groups"] = [groups[name] for name in (
        "body", "left_wing", "left_wing_mid", "left_wing_tip",
        "right_wing", "right_wing_mid", "right_wing_tip")]
    doc["outliner"] = [body_node]
    doc["animations"] = build_animations({
        group["name"]: group["uuid"] for group in doc["groups"]
    })

    texture = doc["textures"][0]
    texture["name"] = "angel_wings"
    texture["path"] = TEXTURE
    texture["width"] = geo["description"]["texture_width"]
    texture["height"] = geo["description"]["texture_height"]
    texture["source"] = "data:image/png;base64," + texture_b64
    texture["saved"] = True

    with open(BBMODEL, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    print("wrote", BBMODEL)
    print("cubes", len(elements), "groups", len(doc["groups"]))


if __name__ == "__main__":
    main()
