"""Pattern preview helpers: render named tiles and contact sheets."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from candy import Canvas, get_ramp, dye_ramp, DYE_COLORS  # noqa: E402
import pnglib  # noqa: E402

OUT = "/tmp/opencode/view"


def save(c, name, scale=1):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    if scale == 1:
        pnglib.png_write(path, c.w, c.h, c.px)
    else:
        big = Canvas(c.w * scale, c.h * scale)
        for y in range(c.h * scale):
            for x in range(c.w * scale):
                cc = c.get(x // scale, y // scale)
                big.set(x, y, cc, cc[3])
        pnglib.png_write(path, big.w, big.h, big.px)
    return path


def contact(names, out="sheet", scale=4, cols=8):
    files = [os.path.join(OUT, n + ".png") for n in names]
    args = ["magick", "montage"]
    for f in files:
        args += ["-label", os.path.basename(f)[:-4], f]
    args += ["-tile", "%dx" % cols, "-geometry", "+4+4", "-pointsize", "11",
             "-background", "#1b1b22", "-fill", "#e8e8f0",
             "-font", "Adwaita-Sans", os.path.join(OUT, out + ".png")]
    subprocess.run(args, check=True)
    return os.path.join(OUT, out + ".png")
