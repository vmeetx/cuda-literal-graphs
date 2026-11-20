"""Dev-only: before/after of one region of a clip (1x and 8x), drawing by drawing.

    python tools/miku/ba_crop.py old.json new.json out.png x0,y0,x1,y1 drawing [drawing ...]

Rows are BEFORE and AFTER; each drawing shows the whole figure at 1x, then the region at 8x.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheet  # noqa: E402

F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)


def frames(path):
    return {f["drawing"]: f["grid"] for f in json.loads(Path(path).read_text())["frames"]}


def main(old, new, out, box, *drawings):
    x0, y0, x1, y1 = map(int, box.split(","))
    pal = sheet.palette()
    rows = []
    for label, fr in (("BEFORE", frames(old)), ("AFTER", frames(new))):
        tiles = []
        for d in drawings:
            g = fr[d]
            one = sheet.img(g, pal, 2)
            dr = ImageDraw.Draw(one)
            dr.rectangle([x0 * 2, y0 * 2, x1 * 2, y1 * 2], outline=(230, 40, 40))
            big = sheet.img([r[x0:x1] for r in g[y0:y1]], pal, 8)
            t = Image.new("RGB", (one.width + big.width + 12, max(one.height, big.height) + 22),
                          (236, 236, 236))
            ImageDraw.Draw(t).text((2, 2), f"{label}  {d}", font=F, fill=(20, 20, 20))
            t.paste(one, (0, 22))
            t.paste(big, (one.width + 8, 22))
            tiles.append(t)
        row = Image.new("RGB", (sum(t.width + 16 for t in tiles), max(t.height for t in tiles)),
                        (236, 236, 236))
        x = 0
        for t in tiles:
            row.paste(t, (x, 0))
            x += t.width + 16
        rows.append(row)
    im = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 12 for r in rows)), (236, 236, 236))
    y = 0
    for r in rows:
        im.paste(r, (0, y))
        y += r.height + 12
    im.save(out)
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
