"""
Audit the behaviour pack against the vanilla corpus.

Mojang's own bedrock-samples behaviour pack is the reference for which
component names and which field names Bedrock actually accepts. This walks
every component in our behaviour entities and reports any field that the
vanilla corpus never uses for that component - which is exactly how a
snake_case/camelCase slip gets caught.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict

VAN = "/tmp/opencode/van_bp"
OURS = "build/behavior_pack"


def strip_json_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        res, inq, i = "", False, 0
        while i < len(line):
            c = line[i]
            if c == '"':
                inq = not inq
                res += c
            elif not inq and line.startswith("//", i):
                break
            else:
                res += c
            i += 1
        out.append(res)
    return "\n".join(out)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.loads(strip_json_comments(fh.read()))


def collect(paths):
    """component name -> set of field names used for it"""
    fields = defaultdict(set)
    components = set()
    for p in paths:
        try:
            d = load(p)
        except Exception:
            continue
        ent = d.get("minecraft:entity")
        if not isinstance(ent, dict):
            continue
        # components live at the top level and inside component_groups
        groups = [ent.get("components", {})]
        for gname, g in (ent.get("component_groups") or {}).items():
            if not isinstance(g, dict):
                continue
            # a component group holds the components directly
            groups.append(g.get("components", g))
        for comps in groups:
            for name, body in comps.items():
                components.add(name)
                if isinstance(body, dict):
                    for k in body:
                        fields[name].add(k)
    return fields, components


def walk(node, prefix=()):
    """Yield (dotted name, value) for every dict in the document."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield ".".join(prefix + (k,)), v
            yield from walk(v, prefix + (k,))
    elif isinstance(node, list):
        for v in node:
            yield from walk(v, prefix)


def main() -> int:
    if not os.path.isdir(VAN):
        print("no vanilla corpus at", VAN)
        return 2

    van_files = [os.path.join(VAN, f) for f in os.listdir(VAN) if f.endswith(".json")]
    our_files = [os.path.join(OURS, "entities", f)
                 for f in sorted(os.listdir(os.path.join(OURS, "entities")))]

    van_fields, van_components = collect(van_files)
    our_fields, our_components = collect(our_files)

    print(f"vanilla components seen : {len(van_components)}")
    print(f"our components seen      : {len(our_components)}")

    problems = []

    # 1. component names vanilla never uses
    for c in sorted(our_components):
        if c.startswith("minecraft:") and c not in van_components:
            problems.append(f"component '{c}' does not appear in the vanilla corpus")

    # 2. field names vanilla never uses for that component
    for c in sorted(our_components):
        if c not in van_components:
            continue
        for f in sorted(our_fields[c]):
            if f not in van_fields[c]:
                problems.append(
                    f"{c}: field '{f}' is not used by vanilla for this component "
                    f"(vanilla uses: {sorted(van_fields[c])[:8]})")

    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nEvery component and field matches the vanilla corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
