"""Dev-only: contact sheet of the mini tier against compact. python tools/miku/mini_sheet.py out.png"""

import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mini  # noqa: E402

CLIPS = ("walk", "turn_to_side", "turn_to_front", "walk_tired")


def img(rows, pal, scale):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGB", (w * scale, h * scale), (24, 26, 32))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                col = tuple(int(pal[c][i:i + 2], 16) for i in (1, 3, 5))
                for j in range(scale):
                    for i in range(scale):
                        px[x * scale + i, y * scale + j] = col
    return im


def main(out):
    tiles = []
    for clip in CLIPS:
        d = json.loads((mini.SRC / f"{clip}.json").read_text(encoding="utf-8"))
        row = []
        for f in d["frames"]:
            m = mini.mini(f["grid"], f["anchors"])
            row.append((img(f["grid"], d["palette"], 4), img(m, d["palette"], 8),
                        img(m, d["palette"], 1)))
        tiles.append(row)
    cw, ch = 37 * 4 + 8, 36 * 4 + 8 + 18 * 8 + 8 + 20
    sheet = Image.new("RGB", (cw * max(len(r) for r in tiles), ch * len(tiles)), (12, 12, 16))
    for j, row in enumerate(tiles):
        for i, (a, b, c) in enumerate(row):
            sheet.paste(a, (i * cw, j * ch))
            sheet.paste(b, (i * cw, j * ch + 36 * 4 + 8))
            sheet.paste(c, (i * cw + 18 * 8 + 4, j * ch + 36 * 4 + 8))
    sheet.save(out)


if __name__ == "__main__":
    main(sys.argv[1])
