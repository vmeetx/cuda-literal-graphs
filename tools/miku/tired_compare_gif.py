"""Dev-only: the tired 3/4 walk cycle for thumbnail options A, B and C side by side, as one
looping GIF (12 fps, each drawing held for its ticks), on a dark terminal background (top row,
terminal outline colours) and a light one (bottom row).

    python tools/miku/tired_compare_gif.py out.gif [scale] [cycles]
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

import clips  # noqa: E402
import q_walk  # noqa: E402
import sheet  # noqa: E402
from cgviz import miku_assets  # noqa: E402

F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
DARK, LIGHT = (30, 30, 30), (250, 250, 250)


def main(out, scale=4, cycles=3):
    scale, cycles = int(scale), int(cycles)
    pal = sheet.palette()
    opts = list(q_walk.TIRED_OPTS)
    runs = {o: clips.diagonal_frames("walk_tired", opt=o)[1] for o in opts}
    n = len(runs[opts[0]])
    w, h = 74 * scale, 72 * scale
    pad, top = 16, 30
    W = len(opts) * (w + pad) + pad
    H = top + 2 * (h + pad) + pad
    frames, durations = [], []
    for _ in range(cycles):
        for k in range(n):
            im = Image.new("RGB", (W, H), (60, 60, 64))
            d = ImageDraw.Draw(im)
            for i, o in enumerate(opts):
                x = pad + i * (w + pad)
                pick = "  (your pick)" if o == "B" else ""
                d.text((x, 6), f"Option {o}{pick}", font=F, fill=(255, 210, 90) if pick else (230, 230, 230))
                g = runs[o][k]["grid"]
                im.paste(sheet.img(miku_assets.terminal_variant(g), pal, scale, DARK), (x, top))
                im.paste(sheet.img(g, pal, scale, LIGHT), (x, top + h + pad))
            frames.append(im)
            durations.append(round(runs[opts[0]][k]["ticks"] * 1000 / 12))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   optimize=True)
    print("ok", out, len(frames), "frames")


if __name__ == "__main__":
    main(*sys.argv[1:])
