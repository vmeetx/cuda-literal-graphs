"""Dev-only: the compact Miku tiers (size LOD). Redrawn small, not shrunk.

Hair masses come from primitives (allowed for hair, as in build.py) and are auto-outlined;
the face, top, arms, skirt and legs are hand-placed pixel rows. Spaces in a hand row are
transparent (the shape underneath shows), '.' clears.

    python tools/miku/compact.py out.png        # thumbnails of options A, B, C
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def blank(w, h):
    return [["."] * w for _ in range(h)]


def ellipse(g, cx, cy, rx, ry, ch):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                g[y][x] = ch


def poly(g, pts, ch):
    """Fill a polygon (even-odd, sampled at cell centres)."""
    n = len(pts)
    for y in range(len(g)):
        for x in range(len(g[0])):
            px, py, inside = x + 0.5, y + 0.5, False
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
                    inside = not inside
            if inside:
                g[y][x] = ch


def stamp(g, rows, x0=0, y0=0):
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != " " and 0 <= y0 + j < len(g) and 0 <= x0 + i < len(g[0]):
                g[y0 + j][x0 + i] = c


def outline(g, ch="B"):
    """Every empty cell touching the figure (4-neighbours) becomes outline."""
    h, w = len(g), len(g[0])
    add = []
    for y in range(h):
        for x in range(w):
            if g[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and g[yy][xx] not in ".BZ":
                    add.append((x, y))
                    break
    for x, y in add:
        g[y][x] = ch


def shade_hair(g, region, light_rows=(), dark_cols=()):
    for (x, y) in region:
        if g[y][x] == "A":
            if y in light_rows:
                g[y][x] = "G"
            elif x in dark_cols:
                g[y][x] = "C"


def rows_of(g):
    return ["".join(r) for r in g]


# ---------------------------------------------------------------- option A: 36 px, chibi
def head_ring(g, cx, cy, rx, ry, over="AC"):
    """Outline just outside the head ellipse, drawn over the tails, so head and tails part."""
    for y in range(len(g)):
        for x in range(len(g[0])):
            inside = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0
            if inside or g[y][x] not in over:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if ((x + dx - cx) / rx) ** 2 + ((y + dy - cy) / ry) ** 2 <= 1.0:
                    g[y][x] = "B"
                    break


def tails(g, left, shade_cols, light_cols, y_from):
    """Two mirrored tails (left given as polygon points; right mirrored about the canvas
    centre), with an inner shadow edge and an outer highlight streak."""
    W = len(g[0])
    poly(g, left, "A")
    poly(g, [(W - x, y) for x, y in left], "A")
    for y in range(y_from, len(g)):
        for x in range(W):
            if g[y][x] != "A":
                continue
            m = min(x, W - 1 - x)
            if m in shade_cols:
                g[y][x] = "C"
            elif m in light_cols and y % 7 not in (0, 1):
                g[y][x] = "G"


def option_a():
    W, H = 31, 39
    g = blank(W, H)
    # twin tails, behind everything: out from the ties, full in the middle, two points at the end
    tails(g, [(7, 2), (3, 6), (1, 13), (1, 24), (2, 31), (3, 35), (4, 32), (5, 35), (7, 28),
              (7, 18), (8, 8)], shade_cols=(6, 7), light_cols=(2,), y_from=8)
    # head
    cx, cy, rx, ry = 15, 8.5, 10.2, 8.6
    ellipse(g, cx, cy, rx, ry, "A")
    for x in range(W):               # highlight band across the crown
        for y in (2, 3):
            if g[y][x] == "A" and abs(x - 15) < 5 + (y - 2) * 2:
                g[y][x] = "G"
    head_ring(g, cx, cy, rx, ry)
    # hair ties where the tails leave the head: dark slate with a red stripe
    stamp(g, ["BBB", "BFSB", "BSFB", " BB"], 4, 2)
    stamp(g, [" BBB", "BSFB", "BFSB", " BB"], 23, 2)
    # face (cols 8..22, centre col 15): bangs, big eyes, blush, smile, side locks
    stamp(g, [
        "AAAAAACACAAAAAA",
        "AAACAEAAAEACAAA",
        "AAEECEEAEECEEAA",
        "ABBBEEEEEEEBBBA",
        "AFGFEEEEEEEFGFA",
        "AFCFEEEEEEEFCFA",
        "AEAEEEEEEEEEAEA",
        "AUUEEEPEPEEEUUA",
        "AEEEEEEVEEEEEEA",
        "A BEEEEEEEEEB A",
        "A  BBEEEEEBB  A",
        "     BPPPB     ",
    ], 8, 7)
    # body (centre col 15); a leek in her right hand, held low with its leaves out to the left
    stamp(g, [
        "           BNLLCLLNB           ",
        "         DDBNLLCLLNBDD         ",
        "        DDMBNLLALLNBMDD        ",
        "        DDMBKNLALNKBMDD        ",
        "        AAABBDDADDBBAAA        ",
        " BI    BEEEBDDDDDDBEEEB        ",
        "BIIBIIIIEEEBDKDDDKDDBEEB       ",
        "XIBIBbbbbLLBDKDDDKDDBEEB       ",
        "BXB BI   BBDDKDDDDKDDBB        ",
        " B   B   DDKDDDDDKDDDD         ",
        "         BAAAAAAAAAAAAB        ",
        "            EE    EE           ",
        "            EE    EE           ",
        "            FF    FF           ",
        "            FF    FF           ",
        "           FFF    FFF          ",
        "           BBB    BBB          ",
    ], 0, 19)
    outline(g)
    for x in range(8, 24):
        g[H - 1][x] = "Z"
    return trim(g)


def option_b():
    """30 px super-deformed: head about half her height."""
    W, H = 27, 30
    g = blank(W, H)
    tails(g, [(6, 2), (2, 6), (1, 12), (1, 20), (2, 25), (3, 28), (4, 26), (5, 28), (6, 23),
              (6, 14), (7, 7)], shade_cols=(5, 6), light_cols=(2,), y_from=7)
    cx, cy, rx, ry = 13, 7.5, 9.2, 7.6
    ellipse(g, cx, cy, rx, ry, "A")
    for x in range(W):
        for y in (1, 2):
            if g[y][x] == "A" and abs(x - 13) < 4 + (y - 1) * 2:
                g[y][x] = "G"
    head_ring(g, cx, cy, rx, ry)
    stamp(g, ["BBB", "BFSB", "BSFB", " BB"], 3, 1)
    stamp(g, [" BBB", "BSFB", "BFSB", " BB"], 20, 1)
    stamp(g, [
        "AAAAACACAAAAA",
        "AACAEAAAEACAA",
        "AEECEEAEECEEA",
        "ABBBEEEEEBBBA",
        "AFGFEEEEEFGFA",
        "AFCFEEEEEFCFA",
        "AUUEEPEPEEUUA",
        "A BEEEVEEEB A",
        "A  BBEEEBB  A",
        "    BPPPB    ",
    ], 7, 6)
    stamp(g, [
        "          BNLCLNB          ",
        "        DDBNLALNBDD        ",
        "       DDMBKLALKBMDD       ",
        "       AAABDDADDBAAA       ",
        "      BEEEBDDDDDBEEEB      ",
        "     bBEEEBDKDDKDBEEEB     ",
        "    bb BBDDKDDDKDDBB       ",
        "   IIB BAAAAAAAAAAAB       ",
        "  XIIB    EE   EE          ",
        " IBIXIB   EE   EE          ",
        " B BIB    FF   FF          ",
        "          FF   FF          ",
        "         BBB   BBB         ",
    ], 0, 16)
    outline(g)
    for x in range(6, 21):
        g[H - 1][x] = "Z"
    return trim(g)


def option_c():
    """22 px mini: the smallest that still reads as her (eyes, tails, ties, leek)."""
    W, H = 21, 22
    g = blank(W, H)
    tails(g, [(4, 1), (1, 4), (0, 9), (1, 15), (2, 18), (3, 16), (4, 18), (4, 12), (5, 4)],
          shade_cols=(4,), light_cols=(), y_from=5)
    cx, cy, rx, ry = 10, 5.5, 7.2, 5.6
    ellipse(g, cx, cy, rx, ry, "A")
    for x in range(W):
        if g[1][x] == "A" and abs(x - 10) < 4:
            g[1][x] = "G"
    head_ring(g, cx, cy, rx, ry)
    stamp(g, ["BB", "BSB", " B"], 2, 1)
    stamp(g, [" BB", "BSB", "B "], 16, 1)
    stamp(g, [
        "AAAACACAAAA",
        "AACEEAEECAA",
        "ABBEEEEEBBA",
        "AFGEEEEEFGA",
        "AUEEPVPEEUA",
        "A BEEEEEB A",
        "   BBPBB   ",
    ], 5, 4)
    stamp(g, [
        "        BLCLB        ",
        "      DDBLALBDD      ",
        "     BAABDADBAAB     ",
        "    bBEEBDDDBEEB     ",
        "   IB  BDKDKDB       ",
        "  XIB BAAAAAAAB      ",
        " IBI B  E   E        ",
        "  B     F   F        ",
        "       FF   FF       ",
    ], 0, 11)
    outline(g)
    for x in range(5, 16):
        g[H - 1][x] = "Z"
    return trim(g)


def trim(g):
    rows = rows_of(g)
    while rows and not rows[0].strip("."):
        rows.pop(0)
    return rows


OPTIONS = {"A": option_a, "B": option_b, "C": option_c}


# ---------------------------------------------------------------- preview
def palette():
    return {k: tuple(int(v["hex"][i:i + 2], 16) for i in (1, 3, 5))
            for k, v in json.loads((HERE / "ref/palette_v2.json").read_text()).items()}


def terminal_variant(rows):
    sys.path.insert(0, str(HERE.parents[1]))
    from cgviz import miku_assets
    return miku_assets.terminal_variant(rows)


def preview(out):
    from PIL import Image, ImageDraw, ImageFont

    pal = palette()
    font = ImageFont.load_default(size=16)
    full = json.loads((HERE.parents[1] / "cgviz/assets/miku/turn_to_side.json").read_text())
    full = full["frames"][0]["grid"]
    tiles = [("current (72 px)", full)] + [(f"Option {k}", f()) for k, f in OPTIONS.items()]

    def sprite(rows, s, bg):
        h, w = len(rows), len(rows[0])
        im = Image.new("RGB", (w, h), bg)
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != ".":
                    im.putpixel((x, y), pal[c])
        return im.resize((w * s, h * s), Image.NEAREST)

    def term80x24(rows, bg, fg):
        """An 80x24 terminal (cells 8x16 px, so one sprite pixel is 8x8) with a graph box
        and Miku standing on it; anything that doesn't fit is cut off, as it would be."""
        cw, chh = 8, 16
        im = Image.new("RGB", (80 * cw, 24 * chh), bg)
        d = ImageDraw.Draw(im)
        box_top = 24 - 6
        d.rectangle([4 * cw, box_top * chh + 8, 60 * cw, (box_top + 2) * chh + 8],
                    outline=(80, 220, 255), width=2)
        d.text((24 * cw, (box_top + 1) * chh), "gemm1 · out", font=font, fill=fg)
        spr = sprite(rows, 8, bg)
        y = (box_top * chh + 8) - spr.height + 8
        im.paste(spr, (8 * cw, y))
        d.text((2 * cw, 22 * chh), f"80x24 terminal: sprite {len(rows[0])}x{len(rows)} px "
               f"= {len(rows[0])}x{(len(rows) + 1) // 2} cells", font=font, fill=fg)
        return im

    cols = []
    for name, rows in tiles:
        tv = terminal_variant(rows)
        parts = [sprite(rows, 1, (255, 255, 255)), sprite(rows, 6, (255, 255, 255)),
                 term80x24(tv, (30, 30, 30), (230, 230, 230)),
                 term80x24(rows, (250, 250, 250), (40, 40, 40))]
        cols.append((name, parts))
    pad = 20
    W = sum(max(p.width for p in ps) + pad for _, ps in cols) + pad
    H = 30 + sum(max(ps[i].height for _, ps in cols) + pad for i in range(4))
    im = Image.new("RGB", (W, H), (60, 60, 64))
    d = ImageDraw.Draw(im)
    x = pad
    for name, ps in cols:
        d.text((x, 6), name, font=font, fill=(240, 240, 240))
        y = 30
        for i, p in enumerate(ps):
            im.paste(p, (x, y))
            y += max(q[i].height for _, q in cols) + pad
        x += max(p.width for p in ps) + pad
    im.save(out)
    print("ok", out)


if __name__ == "__main__":
    preview(sys.argv[1])
