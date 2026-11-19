"""Dev-only: hand corrections to the auto-cleaned front frame (see MIKU_V2_REFERENCE.md).

Each correction is a named function so the reference doc can list it with a before/after.
Coordinates are cells of the cropped front grid (x = column, y = row).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE / "ref"

# palette names (letters come from the study; W was added for enclosed whites)
NAMES = {
    "A": "hair cyan", "B": "outline navy", "C": "pale grey (stalk, ground shadow)",
    "D": "hair shadow teal", "E": "skin", "F": "hair highlight", "G": "skirt grey",
    "H": "dark slate (iris, inner hair line)", "I": "leek green", "J": "skin shade",
    "K": "pleat / top shading grey-blue", "L": "hair-tie red", "M": "blush pink",
    "W": "top white",
}


def load():
    rows = [list(r) for r in (REF / "front_auto.txt").read_text().split()]
    pal = json.loads((REF / "palette_auto.json").read_text())
    return rows, pal


def put(g, x, y, ch):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = ch


def fix_background_gaps(g):
    """Enclosed whites that are really background: between the boots, inside the tail curl."""
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] == "W" and not (18 <= y <= 40 and 22 <= x <= 44):
                g[y][x] = "."


TORSO = {  # rows 32-40, columns 24..42
    32: "......BJJJJJB......",
    33: "....BWWWAAAWWWB....",
    34: "...BEBWWWADWWWBEB..",
    35: "...BEBWWWADWWKBEB..",
    36: "..BEEBWWWADWWKBEEB.",
    37: "..BEEBWWWADWWKBEEB.",
    38: "..BEEBWWWADWWKBEEB.",
    39: "..BEEBWWWADWKKBEEB.",
    40: "..BEEBKWWAWWKKBEEB.",
}


def fix_torso(g):
    """Neck, collar points, tie knot and tie, white top with shading, bare arms."""
    for y, row in TORSO.items():
        for i, ch in enumerate(row):
            x = 24 + i
            if ch == ".":
                if g[y][x] not in ("A", "D", "F", "H") or 25 <= x <= 41:
                    # inside the torso span the old pixels are replaced; keep tail pixels outside
                    if 26 <= x <= 41:
                        g[y][x] = "."
                continue
            g[y][x] = ch


def fix_skirt_legs_leek(g):
    """Skirt, hem, legs and leek rebuilt from primitives; the reference leaves are kept."""
    # clear the old skirt / hem / stalk / hand area (tails and leaves lie outside it)
    for y in range(41, 59):
        for x in range(21, 47):
            g[y][x] = "."
        # leftover outline of the old stalk tip: an outline cell with nothing to its right
        # (the tail's own outline always has hair to its right)
        for x in (47, 48):
            if g[y][x] == "B" and g[y][x + 1] == ".":
                g[y][x] = "."
    top, bot = 41, 56
    edges = {}
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        left = round(28 - t * 5)
        right = round(40 + t * 5)
        edges[y] = (left, right)
        for x in range(left, right + 1):
            g[y][x] = "G"
        g[y][left] = g[y][right] = "B"
    for x in range(edges[bot][0], edges[bot][1] + 1):
        g[bot][x] = "B"
    # pleat lines fan out from the waist
    for x_top, x_bot in ((31, 27), (34, 34), (37, 41)):
        for y in range(top + 1, bot - 2):
            t = (y - top) / (bot - top)
            x = round(x_top + (x_bot - x_top) * t)
            if g[y][x] == "G":
                g[y][x] = "K"
    # cyan trim band just above the hem
    for y in (bot - 2, bot - 1):
        lo, hi = edges[y]
        for x in range(lo + 1, hi):
            g[y][x] = "A"
    # legs down to the reference boots (boots start at row 59)
    for lx in (25, 35):
        for y in (57, 58):
            g[y][lx - 1] = "B"
            g[y][lx] = "E"
            g[y][lx + 1] = "J"
            g[y][lx + 2] = "B"
    # stalk: a diagonal from the leaves (21, 53) up to the right hand (40, 43)
    x0, y0, x1, y1 = 21, 53, 40, 43
    n = x1 - x0
    for i in range(n + 1):
        x = x0 + i
        y = round(y0 + (y1 - y0) * i / n)
        put(g, x, y - 1, "B")
        put(g, x, y, "W")
        put(g, x, y + 1, "C")
        put(g, x, y + 2, "B")
    # hands: the right hand grips the stalk end, the left hand rests at her side
    for y, row in {42: "BBBB", 43: "BEJB", 44: "BEJB", 45: "BBBB"}.items():
        for i, ch in enumerate(row):
            g[y][39 + i] = ch
    for y, row in {41: "BEB", 42: "BEB", 43: "BJB", 44: "BBB"}.items():
        for i, ch in enumerate(row):
            g[y][25 + i] = ch


def main(out=REF):
    g, pal = load()
    fix_background_gaps(g)
    fix_torso(g)
    fix_skirt_legs_leek(g)
    rows = ["".join(r) for r in g]
    Path(out, "front.txt").write_text("\n".join(rows) + "\n")
    Path(out, "palette.json").write_text(json.dumps(
        {k: {"hex": v, "name": NAMES.get(k, "")} for k, v in pal.items()}, indent=1))
    for i, r in enumerate(rows):
        print(f"{i:2d} {r}")


if __name__ == "__main__":
    main(*sys.argv[1:])
