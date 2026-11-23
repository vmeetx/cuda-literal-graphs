"""Dev-only: render cgviz walk frames straight to PNG / GIF, without recording a terminal.

The recorder (tools/record.py) plays the animation in real time and keeps every frame of the
terminal in memory before writing a GIF; at 220x70 that is gigabytes and many minutes. This
composes the frames the player would draw (show.Scene) and paints the cells directly.

    python tools/snap.py png  GRAPH.json COLSxROWS SIZE AT OUT.png  [--labels NAME] [--speed S]
    python tools/snap.py gif  GRAPH.json COLSxROWS SIZE STEP OUT.gif [--labels NAME] [--speed S]

AT is a fraction of the walk (0.5 = midway); STEP keeps every STEP-th frame in the GIF.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cgviz import draw, miku_walk, presets, show  # noqa: E402

BG, FG = (24, 26, 32), (200, 204, 210)
FONTS = ["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
BOLD = ["C:/Windows/Fonts/consolab.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]


def font(paths, size):
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def scene(path, cols, rows, size, speed, labels, whole=False):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    roles = presets.ROLES.get(labels) if labels else None
    lay0, *_ = draw.layout(data, roles, cols)
    lay, cn, frames, sp = miku_walk.walk(data, roles, cols, lay0.orient, cols, rows, speed, size,
                                         whole=whole)
    title = f"cgviz {labels or Path(path).stem} · captured graph"
    return show.Scene(lay, cn, frames, cols, rows, panel=False, title=title, sprites=sp)


def paint(grid, cw, ch, reg, bold):
    img = Image.new("RGB", (len(grid[0]) * cw, len(grid) * ch), BG)
    d = ImageDraw.Draw(img)
    for r, row in enumerate(grid):
        for c, (glyph, fg, bg, b) in enumerate(row):
            x, y = c * cw, r * ch
            fg = fg or FG
            if glyph in ("▀", "▄", "█"):
                top = fg if glyph in ("▀", "█") else (bg or BG)
                bot = fg if glyph in ("▄", "█") else (bg or BG)
                d.rectangle([x, y, x + cw - 1, y + ch // 2 - 1], fill=top)
                d.rectangle([x, y + ch // 2, x + cw - 1, y + ch - 1], fill=bot)
                continue
            if bg:
                d.rectangle([x, y, x + cw - 1, y + ch - 1], fill=bg)
            if glyph == "▶":                     # the font lacks the arrowheads
                d.polygon([(x + 1, y + ch // 4), (x + cw - 1, y + ch // 2),
                           (x + 1, y + 3 * ch // 4)], fill=fg)
            elif glyph == "▼":
                d.polygon([(x + 1, y + ch // 3), (x + cw - 1, y + ch // 3),
                           (x + cw // 2, y + 2 * ch // 3)], fill=fg)
            elif glyph != " ":
                box = "─" <= glyph <= "╿"         # the bold font lacks box lines
                d.text((x, y), glyph, fill=fg, font=bold if b and not box else reg)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("png", "gif"))
    ap.add_argument("graph")
    ap.add_argument("size_cells")
    ap.add_argument("miku_size")
    ap.add_argument("at")
    ap.add_argument("out")
    ap.add_argument("--labels")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--cell", type=int, default=8, help="cell width in px (height is 2x)")
    ap.add_argument("--whole", action="store_true", help="whole graph in view (compact/full)")
    a = ap.parse_args()
    cols, rows = map(int, a.size_cells.lower().split("x"))
    sc = scene(a.graph, cols, rows, a.miku_size, a.speed, a.labels, a.whole)
    cw, ch = a.cell, a.cell * 2
    reg, bold = font(FONTS, ch - 2), font(BOLD, ch - 2)
    n = len(sc.frames)
    if a.mode == "png":
        i = min(n - 1, int(n * float(a.at)))
        paint(sc.compose(i), cw, ch, reg, bold).save(a.out)
        print(f"frame {i} of {n} -> {a.out}")
        return
    step = int(a.at)
    idx = list(range(0, n, step))
    imgs = [paint(sc.compose(i), cw, ch, reg, bold).quantize(colors=128) for i in idx]
    ms = round(1000 * step / 12)
    imgs[0].save(a.out, save_all=True, append_images=imgs[1:], duration=ms, loop=0,
                 optimize=True)
    print(f"{len(idx)} of {n} frames, {ms} ms each -> {a.out}")


if __name__ == "__main__":
    main()
