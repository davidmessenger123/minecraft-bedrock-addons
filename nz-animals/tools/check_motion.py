"""
Evaluate the generated Molang animation expressions over time.

This is a sanity check that the walk cycle really does swing, and by how
much: it samples the leg rotation the generator produced and reports the
peak-to-peak amplitude and the cycle rate.

Usage: python3 tools/check_motion.py
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "build", "resource_pack")


def evaluate(expr: str, life_time: float, move_speed: float) -> float:
    """Evaluate the subset of Molang the generator emits."""
    e = expr
    e = e.replace("query.life_time", repr(life_time))
    e = e.replace("query.modified_move_speed", repr(move_speed))
    e = e.replace("math.max", "max").replace("math.min", "min")
    e = e.replace("math.cos", "math.cos").replace("math.sin", "math.sin")
    e = re.sub(r"\bmath\.(abs|sqrt|floor|round)\b", r"\1", e)
    return float(eval(e, {"math": math, "max": max, "min": min}))


def main() -> int:
    problems: list[str] = []
    print(f"{'animation':46s} {'bone':16s} {'amp':>7s} {'cycle/s':>8s}")

    for f in sorted(os.listdir(os.path.join(RP, "animations"))):
        d = json.load(open(os.path.join(RP, "animations", f), encoding="utf-8"))
        for aid, anim in d["animations"].items():
            for bone, chans in anim.get("bones", {}).items():
                for axis, val in enumerate(chans.get("rotation", [])):
                    if not isinstance(val, str):
                        continue
                    samples = [evaluate(val, t / 60.0, 0.4) for t in range(0, 240)]
                    amp = (max(samples) - min(samples)) / 2.0
                    # count zero crossings to get the cycle rate
                    crossings = sum(
                        1 for a, b in zip(samples, samples[1:]) if a <= 0 < b)
                    rate = crossings / 4.0
                    print(f"{aid:46s} {bone:16s} {amp:7.2f} {rate:8.2f}")
                    if amp < 1.0:
                        problems.append(
                            f"{aid} / {bone} axis {axis}: amplitude {amp:.2f} deg is "
                            f"too small to see")
                    if rate > 6.0:
                        problems.append(
                            f"{aid} / {bone} axis {axis}: {rate:.1f} cycles per second "
                            f"is too fast to read")

    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nEvery animated channel swings visibly, at a readable rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
