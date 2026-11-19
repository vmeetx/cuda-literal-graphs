"""Design-time (Pillow): draft the 32x48 portraits from flat shapes drawn at 8x, then
majority-downscale to the palette and print the pixel maps for hand finishing.

Proportions follow the provided silhouettes: twin tails flaring out to knee height in an
'A', narrow body, big head.
"""

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from cgviz.sprites import PALETTE  # noqa: E402

S = 8
W, H = 32 * S, 48 * S
INV = {v: k for k, v in PALETTE.items()}


def draw(victory=False):
    im = Image.new("RGB", (W, H), (255, 0, 255))
    d = ImageDraw.Draw(im)
    P = PALETTE
    # twin tails (behind everything): from the head sides, flaring out, ending at the knee
    d.polygon([(70, 60), (40, 90), (14, 250), (6, 330), (40, 336), (74, 200), (88, 110)], P["T"])
    d.polygon([(186, 60), (216, 90), (242, 250), (250, 330), (216, 336), (182, 200), (168, 110)], P["T"])
    d.line([(52, 120), (26, 320)], P["D"], 7)
    d.line([(204, 120), (230, 320)], P["D"], 7)
    # legs + boots
    d.rectangle([106, 262, 122, 300], P["S"])
    d.rectangle([134, 262, 150, 300], P["S"])
    d.rectangle([102, 300, 124, 360], P["K"])
    d.rectangle([132, 300, 154, 360], P["K"])
    d.rectangle([102, 300, 124, 308], P["T"])
    d.rectangle([132, 300, 154, 308], P["T"])
    # skirt
    d.polygon([(96, 214), (160, 214), (176, 266), (80, 266)], P["K"])
    d.rectangle([80, 258, 176, 266], P["T"])
    # top
    d.rectangle([98, 158, 158, 216], P["G"])
    d.polygon([(120, 158), (136, 158), (132, 206), (128, 214), (124, 206)], P["T"])
    # arms
    d.polygon([(98, 162), (78, 170), (70, 236), (90, 238), (98, 190)], P["K"])
    d.rectangle([70, 228, 90, 236], P["T"])
    d.ellipse([70, 236, 90, 254], P["S"])
    if victory:
        d.polygon([(160, 168), (208, 98), (218, 104), (170, 180)], P["K"])
        d.polygon([(204, 94), (216, 80), (230, 90), (222, 104)], P["T"])
        d.ellipse([212, 68, 234, 90], P["S"])
        d.line([(222, 80), (240, 30)], P["W"], 12)
        d.polygon([(232, 40), (226, 0), (240, 0), (244, 36)], P["L"])
        d.polygon([(236, 40), (252, 0), (256, 0), (256, 14), (246, 44)], P["L"])
    else:
        d.polygon([(158, 162), (178, 170), (186, 236), (166, 238), (158, 190)], P["K"])
        d.rectangle([166, 228, 186, 236], P["T"])
        d.ellipse([166, 236, 186, 254], P["S"])
        d.line([(176, 246), (222, 132)], P["W"], 10)
        d.polygon([(216, 140), (232, 70), (244, 76), (226, 146)], P["L"])
        d.polygon([(216, 140), (206, 80), (218, 78), (224, 136)], P["L"])
    # head
    d.ellipse([60, 24, 196, 160], P["T"])
    d.ellipse([78, 64, 178, 160], P["S"])
    # bangs: jagged fringe
    d.polygon([(70, 60), (186, 60), (182, 100), (164, 84), (150, 104), (134, 82), (120, 104),
               (106, 84), (92, 104), (74, 96)], P["T"])
    # eyes
    for cx in (106, 150):
        d.ellipse([cx - 9, 108, cx + 9, 134], P["D"])
        d.rectangle([cx - 5, 112, cx - 1, 118], P["W"])
    # headset
    d.rectangle([54, 92, 72, 128], P["K"])
    d.rectangle([184, 92, 202, 128], P["K"])
    d.line([(64, 128), (86, 148)], P["K"], 4)
    return im


def downscale(im):
    rows = []
    px = im.load()
    for by in range(48):
        row = []
        for bx in range(32):
            c = Counter(px[bx * S + x, by * S + y] for y in range(S) for x in range(S))
            col, n = c.most_common(1)[0]
            row.append(INV.get(col, "."))
        rows.append("".join(row))
    return rows


if __name__ == "__main__":
    for name, v in (("portrait_idle", False), ("portrait_victory", True)):
        print(f'    "{name}": [')
        rows = [list(r) for r in downscale(draw(v))]
        # hand fixes: matching highlight in the left eye, tie tip, clean neck
        for y, x, ch in [(14, 12, "W"), (14, 13, "D"), (15, 13, "D"), (16, 12, "S"), (16, 13, "D"),
                         (16, 18, "D"), (16, 19, "S"), (26, 16, "T"), (25, 15, "G"), (26, 15, "G"), (17, 15, "D")]:
            rows[y][x] = ch
        for r in ("".join(r) for r in rows):
            print(f'        "{r}",')
        print("    ],")
