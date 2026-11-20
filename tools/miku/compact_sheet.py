"""Dev-only: contact sheet of the compact tier drawings (1x and 6x, light and dark).

    python tools/miku/compact_sheet.py out.png [u]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import compact  # noqa: E402
import halve  # noqa: E402
import q_walk  # noqa: E402
from cgviz import miku_assets  # noqa: E402

NAMES = ["front", "stand", "contact_r", "down_r", "pass_r", "up_r", "contact_l", "down_l",
         "pass_l", "up_l", "front_tired"]


def main(out, u="0"):
    u = float(u)
    pal = compact.palette()
    font = ImageFont.load_default(size=14)

    def img(rows, s, bg):
        h, w = len(rows), len(rows[0])
        im = Image.new("RGB", (w, h), bg)
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != ".":
                    im.putpixel((x, y), pal[c])
        return im.resize((w * s, h * s), Image.NEAREST)

    tiles = []
    for t, n in enumerate(NAMES):
        tiles.append((n, halve.drawing(n, t, 12, u=u)[0]))
    s = 6
    w, h = halve.W * s, halve.H * s
    W = len(tiles) * (w + 10) + 10
    im = Image.new("RGB", (W, 24 + 2 * (h + 10) + 40), (60, 60, 64))
    d = ImageDraw.Draw(im)
    for i, (n, rows) in enumerate(tiles):
        x = 10 + i * (w + 10)
        d.text((x, 4), n, font=font, fill=(235, 235, 235))
        im.paste(img(rows, s, (250, 250, 250)), (x, 24))
        im.paste(img(miku_assets.terminal_variant(rows), s, (30, 30, 30)), (x, 34 + h))
        im.paste(img(rows, 1, (250, 250, 250)), (x, 44 + 2 * h))
    im.save(out)
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
