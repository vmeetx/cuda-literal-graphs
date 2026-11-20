"""Dev-only: approved Miku vs compact B vs a straight 2:1 reduction of the approved frames
(the reduction is a tracing base, not a finished drawing). All shown at the same pixel height.

    python tools/miku/half_compare.py out.png
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import compact  # noqa: E402

ASSETS = HERE.parents[1] / "cgviz/assets/miku"


def half(rows):
    """2:1: each 2x2 block takes its most common colour; outline wins over a single fill pixel
    so lines survive; transparency only when the block is mostly empty."""
    h, w = len(rows), len(rows[0])
    out = []
    for y in range(0, h - 1, 2):
        s = ""
        for x in range(0, w - 1, 2):
            c = Counter(rows[y + j][x + i] for j in (0, 1) for i in (0, 1))
            empty = c.pop(".", 0)
            if empty >= 3 or not c:
                s += "."
            elif c.get("B", 0) >= 2 or (c.get("B", 0) == 1 and empty >= 1):
                s += "B"
            else:
                s += c.most_common(1)[0][0]
        out.append(s)
    return out


def main(out):
    pal = compact.palette()
    font = ImageFont.load_default(size=16)
    front = json.loads((ASSETS / "turn_to_side.json").read_text())["frames"][0]["grid"]
    walk = json.loads((ASSETS / "walk.json").read_text())["frames"][0]["grid"]
    cols = [("approved (72 px)", [front, walk], 4),
            ("compact B (30 px)", [compact.option_b()], 8),
            ("approved, halved (36 px) - raw", [half(front), half(walk)], 8)]

    def img(rows, s):
        h, w = len(rows), len(rows[0])
        im = Image.new("RGB", (w, h), (250, 250, 250))
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != ".":
                    im.putpixel((x, y), pal[c])
        return im.resize((w * s, h * s), Image.NEAREST)

    tiles = [(n, [img(r, s) for r in rs]) for n, rs, s in cols]
    pad = 20
    W = sum(max(i.width for i in ims) * 2 + pad * 2 for _, ims in tiles) + pad
    H = 30 + max(i.height for _, ims in tiles for i in ims) + pad
    sheet = Image.new("RGB", (W, H), (60, 60, 64))
    d = ImageDraw.Draw(sheet)
    x = pad
    for n, ims in tiles:
        d.text((x, 6), n, font=font, fill=(240, 240, 240))
        for i in ims:
            sheet.paste(i, (x, 30))
            x += i.width + pad
        x += pad
    sheet.save(out)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1])
