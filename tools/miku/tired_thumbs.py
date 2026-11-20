"""Dev-only: thumbnails of the tired 3/4 contact key, three options side by side at 1x, 8x and
in a real terminal (dark and light).

    python tools/miku/tired_thumbs.py out.png
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent), str(HERE)]

import beforeafter  # noqa: E402
import q_walk  # noqa: E402
import sheet  # noqa: E402

F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)


def main(out):
    pal = sheet.palette()
    tiles = []
    for name, o in q_walk.TIRED_OPTS.items():
        rows, _ = q_walk.pose("contact_r", u=1.0, opt=name, hem="S3")
        one = sheet.img(rows, pal, 1)
        big = sheet.img(rows, pal, 6)
        t, cols = beforeafter.terminal_text(rows, pal)
        n = len(t.splitlines())
        dark = beforeafter.shot(t, cols, n, (30, 30, 30), (210, 212, 216), Path(out).with_name(f"tired_{name}_dark.png"))
        light = beforeafter.shot(t, cols, n, (255, 255, 255), (20, 20, 20), Path(out).with_name(f"tired_{name}_light.png"))
        sc = big.height / dark.height
        dark = dark.resize((round(dark.width * sc), big.height))
        light = light.resize((round(light.width * sc), big.height))
        pick = " (PROVISIONAL PICK)" if name == q_walk.TIRED_PICK else ""
        W = one.width + big.width + dark.width + light.width + 40
        tile = Image.new("RGB", (W, big.height + 50), (236, 236, 236))
        d = ImageDraw.Draw(tile)
        d.text((4, 4), f"Option {name}{pick}: {o['note']}", font=F,
               fill=(200, 30, 30) if pick else (20, 20, 20))
        x = 4
        for im in (one, big, dark, light):
            tile.paste(im, (x, 28))
            x += im.width + 10
        tiles.append(tile)
    W = max(t.width for t in tiles)
    im = Image.new("RGB", (W, sum(t.height + 10 for t in tiles)), (236, 236, 236))
    y = 0
    for t in tiles:
        im.paste(t, (0, y))
        y += t.height + 10
    im.save(out)
    print("ok", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
