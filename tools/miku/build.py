"""Dev-only: the single source of truth for Miku v2 sprite frames.

Front poses come from the approved model (tools/miku/ref/poses.json). New views are built here:
  - hair masses from primitives (allowed for hair), auto-outlined;
  - faces, cloth, limbs and hands from hand-placed pixel patches (never primitives);
  - twin tails procedurally (tails.py), anchored at the hair-tie blocks.
A frame is a function call, e.g. side_head(face="A") or pose(view="side", legs="pass_r").
"""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE / "ref"
W, H = 74, 72          # shared canvas (same as the approved poses)
BASELINE = 67          # row of the boot soles


class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.g = [["."] * w for _ in range(h)]

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else "."

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def patch(self, x0, y0, rows, keep="."):
        """Hand-placed pixels: one string per row; `keep` leaves what is underneath;
        '-' forces background."""
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                if c == keep:
                    continue
                self.set(x0 + i, y0 + j, "." if c == "-" else c)

    def ellipse(self, cx, cy, rx, ry, c, only=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    if only is None or self.get(x, y) in only:
                        self.set(x, y, c)

    def outline(self, colours, line="B"):
        """1-px outline around every pixel of `colours` that touches background."""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] != ".":
                    continue
                if any(self.get(x + dx, y + dy) in colours for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    add.append((x, y))
        for x, y in add:
            self.g[y][x] = line

    def rows(self):
        return ["".join(r) for r in self.g]

    def mirror(self):
        c = Canvas(self.w, self.h)
        c.g = [list(reversed(r)) for r in self.g]
        return c


# ----------------------------------------------------------------------------- side head
# Facing right. Local head box origin (hx, hy) on the canvas. The head is 34 wide like P1's
# hair mass minus the tails, and spans rows 2..33 like P1 (chin at row 32).

HAIR_TIE = [            # dark block with red diagonal stripes, at the back of the head
    "BBBB",
    "BSBB",
    "BBSB",
    "BSBS",
    "BBSB",
    "BSBB",
    "BBBB",
]

HIGHLIGHTS = [          # hand-placed highlight strokes on the dome (G), shadow sweeps (C)
    (12, 3, "GGGG"), (10, 4, "GG"), (9, 5, "G"), (21, 7, "GG"), (23, 8, "GG"),
    (5, 9, "C"), (5, 10, "C"), (4, 11, "CC"), (4, 12, "C"), (4, 13, "C"), (4, 14, "C"),
]

SIDE_LOCK = [           # hangs in front of the ear down to the jaw (cols 15-19 of the head box)
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAAB",
    "BCAB.",
    "BCAB.",
    ".BAB.",
    ".BB..",
]

# Face variants for the thumbnail round: each is a patch over head-box columns 18..33,
# rows 15..33 (bang tips, eye, blush, nose, mouth, jaw, neck). '.' keeps the hair/background.
FACES = {
    # A: P1's big round eye turned to profile: 5-wide iris, thick upper lash, flat lower lid
    "A": [
        "..AAACAAAACAAAB.",
        "..AAAEEEAAEEAAB.",
        "..EAEEEEEAEEEAB.",
        "..EEEBBBBBBBEEB.",
        "..EEEBFFFFFBEEB.",
        "..EEEEFGCCFEEEB.",
        "..EEEEFCCCFEEEB.",
        "..EEEEFCAAFEEEEB",
        "..EEEEFAAAFEEEB.",
        "..EEEEEBBBEEEEB.",
        "..EEUUUEEEEEEEB.",
        "..EEEEEEEEEESEB.",
        "..EEEEEEEEEEEB..",
        "..EEEEEEEEEEB...",
        "..EEEEEEEEB.....",
        "..EEBBBBBB......",
        ".BEEB...........",
        ".BEEB...........",
        ".BEEB...........",
    ],
    # B: narrower almond eye (4-wide iris) set further forward, lash flick at the outer corner
    "B": [
        "..AAACAAAACAAAB.",
        "..AAAEEEAAEEAAB.",
        "..EAEEEEEAEEEAB.",
        "..EEEEBBBBBBBBB.",
        "..EEEEBFFFFBEEB.",
        "..EEEEEFGCFEEEB.",
        "..EEEEEFCCFEEEB.",
        "..EEEEEFCAFEEEEB",
        "..EEEEEEBBBEEEB.",
        "..EEEEEEEEEEEEB.",
        "..EEUUUEEEEEEEB.",
        "..EEEEEEEEEESEB.",
        "..EEEEEEEEEEEB..",
        "..EEEEEEEEEEB...",
        "..EEEEEEEEB.....",
        "..EEBBBBBB......",
        ".BEEB...........",
        ".BEEB...........",
        ".BEEB...........",
    ],
    # C: tall eye like P5's excited face (6 rows of iris), smaller nose, mouth slightly open
    "C": [
        "..AAACAAAACAAAB.",
        "..AAAEEEAAEEAAB.",
        "..EAEEEEEAEEEAB.",
        "..EEBBBBBBBBEEB.",
        "..EEBFFFFFFBEEB.",
        "..EEEFGGCCFEEEB.",
        "..EEEFGCCCFEEEB.",
        "..EEEFCCCCFEEEB.",
        "..EEEFCAAAFEEEB.",
        "..EEEFAAAAFEEEB.",
        "..EEUBBBBBBUEEB.",
        "..EEEEEEEEEESSB.",
        "..EEEEEEEEEEVB..",
        "..EEEEEEEEEEB...",
        "..EEEEEEEEB.....",
        "..EEBBBBBB......",
        ".BEEB...........",
        ".BEEB...........",
        ".BEEB...........",
    ],
    # D: long bangs covering the top of the eye (more hair, softer), eye half-hidden, blush wider
    "D": [
        "..AAACAAAACAAAB.",
        "..AAACAAAACAAAB.",
        "..AACEEEACEEAAB.",
        "..AEBBBBBBBBEAB.",
        "..EEBFFFFFFBEEB.",
        "..EEEFGCCCFEEEB.",
        "..EEEFCCCCFEEEB.",
        "..EEEFCAAAFEEEEB",
        "..EEEFAAAAFEEEB.",
        "..EEEEBBBBEEEEB.",
        "..EUUUUEEEEEEEB.",
        "..EEEEEEEEEESEB.",
        "..EEEEEEEEEEEB..",
        "..EEEEEEEEEEB...",
        "..EEEEEEEEB.....",
        "..EEBBBBBB......",
        ".BEEB...........",
        ".BEEB...........",
        ".BEEB...........",
    ],
}


def side_head(c: Canvas, hx: int, hy: int, face: str = "A"):
    """Draw the side-view head (facing right) with its head box at (hx, hy)."""
    # hair dome (primitive: allowed for hair), then outline
    c.ellipse(hx + 17, hy + 14, 15.5, 14.0, "A")
    c.ellipse(hx + 10, hy + 20, 8.5, 8.0, "A")        # back of the head down to the nape
    c.outline(set("A"))
    for x, y, s in HIGHLIGHTS:
        c.patch(hx + x, hy + y, [s])
    # hair tie block at the back-top of the head (the tail anchor)
    c.patch(hx + 1, hy + 5, HAIR_TIE)
    # face (hand-placed) over the front-lower quadrant
    c.patch(hx + 18, hy + 15, FACES[face])
    # side lock in front of the ear, drawn last so it overlaps the face edge
    c.patch(hx + 15, hy + 14, SIDE_LOCK)
    return {"tie_anchor": (hx + 2, hy + 11)}


def save_rows(path, rows):
    Path(path).write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    import sheet

    pal = sheet.palette()
    from PIL import Image

    tiles = []
    for k in "ABCD":
        cv = Canvas(40, 38)
        side_head(cv, 2, 1, k)
        tiles.append((k, cv.rows()))
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[1] / ".wsl/side_heads.png"
    ims = [(k, sheet.img(r, pal, 8), sheet.img(r, pal, 1)) for k, r in tiles]
    W2 = sum(i[1].width + 20 for i in ims) + 20
    sheetim = Image.new("RGB", (W2, ims[0][1].height + 80), (236, 236, 236))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(sheetim)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    x = 20
    for k, big, small in ims:
        d.text((x, 4), k, font=f, fill=(20, 20, 20))
        sheetim.paste(big, (x, 28))
        sheetim.paste(small, (x, 28 + big.height + 10))
        x += big.width + 20
    sheetim.save(out)
    for k, r in tiles:
        print(k)
        print("\n".join(r))
