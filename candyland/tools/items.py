"""Item-texture recipes (914 icons) built on the candy repaint."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import restyle  # noqa: E402
from candy import Canvas  # noqa: E402

OUTLINE = (48, 26, 42)


def item_canvas(name, e):
    # flat utility icons should keep their square silhouette
    if name.startswith("light_block") or name in (
            "chalkboard_large", "chalkboard_medium", "chalkboard_small"):
        return restyle.candy_paint(e, outline=None, contrast=0.68)
    if name == "potion_overlay":
        return restyle.candy_paint(e, outline=None, contrast=0.68)
    if name.startswith("record_") or name.startswith("music_disc_"):
        return restyle.candy_paint(e, outline=OUTLINE, contrast=0.68,
                                   sat_boost=1.2)
    return restyle.candy_paint(e, outline=OUTLINE, contrast=0.68)
