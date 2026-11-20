"""Dev-only: quick preview strips of q_walk drawings.

    python tools/miku/q_preview.py out.png scale spec [spec ...]

spec = drawing[:u[:opt[:hem]]], e.g. contact_r  contact_r:1:B  pass_r:0:A:S1
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q_walk  # noqa: E402
import sheet  # noqa: E402

F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)


def main(out, scale, *specs):
    pal = sheet.palette()
    ims = []
    for k, sp in enumerate(specs):
        p = sp.split(":") + [None] * 4
        d, u, opt, hem = p[0], float(p[1] or 0), p[2] or None, p[3] or None
        rows, meta = q_walk.pose(d, t=k, u=u, opt=opt, hem=hem, k=k)
        im = sheet.img(rows, pal, int(scale))
        tile = Image.new("RGB", (im.width, im.height + 20), (236, 236, 236))
        tile.paste(im, (0, 20))
        runs = q_walk.straight_runs([tuple(q) for q in meta["hem_outline"]])
        ImageDraw.Draw(tile).text((2, 2), f"{sp}  hem {meta['hem']}{'  RUN!' if runs else ''}",
                                  font=F, fill=(200, 30, 30) if runs else (20, 20, 20))
        ims.append(tile)
    sheetim = Image.new("RGB", (sum(i.width + 8 for i in ims), max(i.height for i in ims)), (236, 236, 236))
    x = 0
    for i in ims:
        sheetim.paste(i, (x, 0))
        x += i.width + 8
    sheetim.save(out)
    print("ok")


if __name__ == "__main__":
    main(*sys.argv[1:])
