"""Dev-only: before/after images for one pose: 1x, 8x and real-terminal (dark, light).

    python tools/miku/beforeafter.py P1 poses_prev.json poses.json findings/miku_v2/gate2_p1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tools/miku")]

import gate1b  # noqa: E402
import screenshot  # noqa: E402
import sheet  # noqa: E402
from cgviz import halfblock  # noqa: E402

REF = ROOT / "tools/miku/ref"
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)


def terminal_text(rows, pal):
    rows = gate1b.terminal_variant(rows)
    cells = halfblock.cells(rows, pal)
    out = []
    for row in cells:
        s = []
        for c in row:
            if c is None:
                s.append("\x1b[0m ")
            else:
                ch, fg, bg = c
                s.append("\x1b[0m\x1b[38;2;%d;%d;%dm" % fg + ("\x1b[48;2;%d;%d;%dm" % bg if bg else "") + ch)
        out.append("".join(s) + "\x1b[0m")
    return "\n".join(out), len(rows[0])


def shot(text, cols, rows, bg, fg, path):
    screenshot.BG, screenshot.FG = bg, fg
    sc = screenshot.screen_of(text.encode(), cols + 2, rows + 2)
    screenshot.render(sc, str(path), crop=False)
    return Image.open(path).convert("RGB")


def main(name, before_file, after_file, stem):
    pal = sheet.palette()
    before = json.loads((REF / before_file).read_text())[name]
    after = json.loads((REF / after_file).read_text())[name]
    stem = Path(stem)
    tiles = []
    for label, rows in (("before", before), ("after", after)):
        big = sheet.img(rows, pal, 8)
        one = sheet.img(rows, pal, 1)
        t, cols = terminal_text(rows, pal)
        nrows = len(t.splitlines())
        dark = shot(t, cols, nrows, (30, 30, 30), (210, 212, 216), Path(f"{stem}_{label}_dark.png"))
        light = shot(t, cols, nrows, (255, 255, 255), (20, 20, 20), Path(f"{stem}_{label}_light.png"))
        tiles.append((label, one, big, dark, light))
    W = 40 + sum(max(i.width for i in t[1:]) + 30 for t in tiles)
    H = 50 + tiles[0][2].height + 40 + tiles[0][3].height + 30 + tiles[0][4].height + 80
    out = Image.new("RGB", (W, H), (236, 236, 236))
    d = ImageDraw.Draw(out)
    x = 20
    for label, one, big, dark, light in tiles:
        d.text((x, 10), f"{name} {label}", font=F, fill=(20, 20, 20))
        y = 40
        out.paste(one, (x, y))
        out.paste(big, (x + one.width + 12, y))
        y += big.height + 20
        out.paste(dark, (x, y))
        y += dark.height + 10
        out.paste(light, (x, y))
        x += max(big.width + one.width + 12, dark.width) + 30
    out.save(f"{stem}_before_after.png")
    print(f"{stem}_before_after.png")


if __name__ == "__main__":
    main(*sys.argv[1:])
