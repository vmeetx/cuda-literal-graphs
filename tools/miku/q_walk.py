"""Dev-only: the cheerful walk in a 3/4 ("diagonal") view, facing right (left = mirror).

Study: anime chibi Miku strolling while she shops: body turned a little toward the viewer, head
stacked over the hips, arms open wide (the leek held up in the travel-side hand, the other arm
out low and back, palm down), small crossing steps, tails swinging wide, closed happy eyes and
an open smile. Nothing traced; the head is the approved front pose (P1) turned by a column warp.

Parts, back to front: far tail (one shade darker), near tail, back arm, far leg (darker), near
leg, skirt, torso, head, leek, leek arm. Every part is a hand-placed letter grid; the only
procedural steps are the column warp of the head (turn), a per-row sway of the hand-drawn tails,
and the bob (body up and down while the planted foot stays on the ground).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H, BASELINE = 74, 72, 67


def p1():
    return json.loads((HERE / "ref/poses.json").read_text())["P1"]


# ---------------------------------------------------------------- head (P1 turned 3/4 right)
HEAD_X0, HEAD_X1, HEAD_ROWS = 22, 52, 33        # head box columns (inclusive) and rows 0..32
TURN = 1.7                                        # >1: left half stretched, right half squeezed


def face_edits(src):
    """Closed happy eyes, blush and an open smile, drawn on P1 before the turn."""
    g = [list(r) for r in src]
    for y in range(20, 27):                       # clear the open eyes to skin
        for x in list(range(27, 33)) + list(range(40, 47)):
            if g[y][x] not in "EP" and not (y == 20 and x in (27, 46)):
                g[y][x] = "E"
    for x in range(34, 39):                       # clear the small mouth
        for y in (29, 30):
            g[y][x] = "E"
    for cx in (30, 43):                           # ^ ^ closed eyes, lash flick at the outer corner
        for x in (cx - 1, cx, cx + 1):
            g[22][x] = "B"
        g[23][cx - 2] = "B"
        g[23][cx + 2] = "B"
    g[22][27] = "B"                               # outer lash (near eye)
    for x in (28, 29, 30):
        g[25][x] = "U"
    for x in (43, 44, 45):
        g[25][x] = "U"
    for x, c in zip(range(35, 40), "BBBBB"):      # open D-shaped smile
        g[28][x] = c
    for x, c in zip(range(35, 40), "BVVVB"):
        g[29][x] = c
    for x, c in zip(range(36, 39), "BUB"):
        g[30][x] = c
    return ["".join(r) for r in g]


def turned_head():
    src = face_edits(p1())
    n = HEAD_X1 - HEAD_X0
    k = HEAD_X0 + 6                               # outline and near tie stay 1:1 (no smear)
    m = HEAD_X1 - k
    cols = [x if x < k else k + round(m * ((x - k) / m) ** TURN) for x in range(HEAD_X0, HEAD_X1 + 1)]
    out = {}
    for y in range(HEAD_ROWS):
        for i, sx in enumerate(cols):
            c = src[y][sx]
            if c != ".":
                out[(HEAD_X0 + i, y)] = c
    return out


# ---------------------------------------------------------------- tails (P1's right tail, both sides)
FAR_HAIR = {"G": "A", "A": "C", "C": "C"}         # the far tail one step darker on the hair ramp
TIE_Y, TIP_Y = 12, 62


def tail_cells():
    src = p1()
    right = {}
    for y in range(2, 66):
        for x in range(53, W):
            c = src[y][x]
            if c not in ".Z":
                right[(x, y)] = c
    left = {(W - 1 - x, y): c for (x, y), c in right.items()}     # mirrored: no leek over it
    return left, right


def sway(cells, amp, dx0):
    out = {}
    for (x, y), c in cells.items():
        t = max(0.0, min(1.0, (y - TIE_Y) / (TIP_Y - TIE_Y)))
        out[(x + dx0 + round(amp * t ** 1.6), y)] = c
    return out


# ---------------------------------------------------------------- body parts (x0, y0, rows)
TORSO = (32, 33, [
    "......BEPB......",
    "....BBLBBLBB....",
    "...BLLLBAABNB...",
    "..BLLLLBAABNNB..",
    "..BLLLLLBACBNB..",
    "..BLLLLLBAACNB..",
    "..BNLLLLBAACNB..",
    "..BNLLLLLBACNB..",
    "..BNNLLLLBAKNB..",
    "...BNLLLLBACKB..",
    "...BNNLLLLBKKB..",
    "...BKNNNNNBKKB..",
])

BACK_ARM = (18, 35, [   # her right arm, out low and back, palm down (in front of the near tail)
    "...............BB",
    ".............BBEB",
    "...........BBEEB.",
    ".........BBDEEB..",
    ".......BBDDDDBB..",
    ".....BBDDDDDMB...",
    "....BDDDDDDMB....",
    "...BDDDDDMMB.....",
    "..BAADDMMBB......",
    ".BEAAAABB........",
    "BEEEEBB..........",
    "BEEEB............",
    ".BBB.............",
])

LEEK_ARM = (44, 27, [   # her left arm, raised out and forward, fist around the leek
    "................BBBB.",
    "..............BBAEEB.",
    "............BBDDAEEB.",
    "..........BBDDDDABB..",
    "........BBDDDDDMB....",
    "......BBDDDDDMMB.....",
    ".....BEDDDDMMB.......",
    "....BEEBBBBB.........",
    "..BBEEB..............",
    "BBEEEB...............",
    "BEEEB................",
])

LEEK_TOP = (56, 1, [    # leaves, swaying a pixel behind the arm
    "B.........BB",
    "BB.......BIB",
    ".BIB....BIB.",
    "..BIB..BIXB.",
    "..BIIB.BIB..",
    "...BIIBIXB..",
    "....BIXB....",
])
LEEK_STALK_X, LEEK_STALK_Y0, LEEK_STALK_Y1 = 60, 8, 30
LEEK_ROOT = (60, 31, ["BLLB", "BLLB", ".BB."])

SKIRT = (27, 45, [
    ".......BBBBBBBBBB.......",
    "......BDDDDKDDDDDB......",
    ".....BDDDDDKDDDDDMB.....",
    "....BDDDDDKDDDDDDKMB....",
    "...BDDDDDDKDDDDDDKMMB...",
    "..BDDDDDDKDDDDDDDKDMMB..",
    ".BDDDDDDKDDDDDDDDKDDMMB.",
    "BAAAAAAAAAAAAAAAAAAACCCB",
    ".BBBBBBBBBBBBBBBBBBBBBB.",
])

# legs: (hip column inside the box, rows); hips meet the skirt at row 54
LEGS = {
    "S": (2, [  # planted, straight under the body
        "..BEEEB....", "..BEEEB....", "..BEEEB....", "..BFFFB....", "..BFFFB....",
        "..BFFFB....", "..BFFFB....", "..BFFFB....", "..BFFFB....", "..BFFFB....",
        "..BFFFB....", "..BFFFB....", "..BFFFFB...", "..BBBBBB..."]),
    "F": (2, [  # reaching forward, heel down
        "..BEEEB....", "..BEEEB....", "...BEEEB...", "...BFFFB...", "...BFFFB...",
        "....BFFFB..", "....BFFFB..", "....BFFFB..", ".....BFFFB.", ".....BFFFB.",
        ".....BFFFB.", ".....BFFFFB", ".....BFFFFB", ".....BBBBBB"]),
    "K": (4, [  # behind, on the toe
        "....BEEEB..", "....BEEEB..", "...BEEEB...", "...BFFFB...", "...BFFFB...",
        "..BFFFB....", "..BFFFB....", "..BFFFB....", ".BFFFB.....", ".BFFFB.....",
        ".BFFFB.....", "BFFFFB.....", "BFFFB......", ".BBB......."]),
    "P": (2, [  # passing: knee forward, foot off the ground
        "..BEEEB....", "..BEEEB....", "..BEEEEB...", "...BEEEEB..", "....BFFFFB.",
        "....BFFFFB.", "....BFFFB..", "...BFFFB...", "..BFFFB....", "..BFFFFB...",
        "..BFFFFFB..", "..BBBBBBB.."]),
}
FAR_LEG = {"E": "P", "F": "Y"}                   # far leg: thigh in skin shade, far-side slate sock
HIP_X = {"near": 35, "far": 40}                  # first fill column of each hip

# drawing: (near-leg shape, far-leg shape, near grounded?, far grounded?, bob, skirt sway,
#           back-arm swing, tail amplitude phase)
DRAW = {
    "contact_r": ("K", "F", True, True, 1, 0, 1),
    "down_r":    ("K", "S", True, True, 1, -1, 1),
    "pass_r":    ("P", "S", False, True, -1, -1, 0),
    "up_r":      ("F", "S", False, True, -1, 0, -1),
    "contact_l": ("F", "K", True, True, 1, 0, -1),
    "down_l":    ("S", "K", True, True, 1, 1, -1),
    "pass_l":    ("S", "P", True, False, -1, 1, 0),
    "up_l":      ("S", "F", True, False, -1, 0, 1),
    "stand":     ("S", "S", True, True, 0, 0, 0),
}


def fit(rows, n):
    rows = list(rows)
    while len(rows) > n:
        rows.pop(8)
    while len(rows) < n:
        rows.insert(7, rows[7])
    return rows


def paste(cv, part, dx=0, dy=0, recolor=None, rows_shift=None):
    x0, y0, rows = part
    for j, r in enumerate(rows):
        sx = rows_shift(j) if rows_shift else 0
        for i, c in enumerate(r):
            if c != ".":
                cv[(x0 + i + dx + sx, y0 + j + dy)] = recolor.get(c, c) if recolor else c


def leg(cv, shape, side, bob, grounded):
    hip, rows = LEGS[shape]
    top = 54 + bob
    if grounded:
        rows = fit(rows, BASELINE - top + 1)
    else:
        rows = fit(rows, len(rows) - 1) if bob < 0 else rows
    paste(cv, (HIP_X[side] - hip - 1, top, rows), recolor=FAR_LEG if side == "far" else None)


def pose(drawing="contact_r", t=0, period=12):
    near, far, ng, fg, bob, skirt, arm = DRAW[drawing]
    cv = {}
    left, right = tail_cells()
    phase = math.sin(4 * math.pi * (t - 1) / period)          # two flares per cycle, 1 tick behind the bob
    paste_cells = lambda cells: cv.update({k: v for k, v in cells.items()})
    far_tail = {k: FAR_HAIR.get(v, v) for k, v in sway(right, 0.5 + 1.8 * phase, -3).items()}
    paste_cells({(x, y + bob): c for (x, y), c in far_tail.items()})
    paste_cells({(x, y + bob): c for (x, y), c in sway(left, -0.5 - 2.2 * phase, 3).items()})
    paste(cv, BACK_ARM, dy=bob, rows_shift=lambda j: (arm if j >= 5 else 0))
    leg(cv, far, "far", bob, fg)
    leg(cv, near, "near", bob, ng)
    paste(cv, SKIRT, dy=bob, rows_shift=lambda j: (skirt if j >= 6 else round(skirt / 2) if j >= 4 else 0))
    paste(cv, TORSO, dy=bob)
    head = turned_head()
    cv.update({(x, y + bob): c for (x, y), c in head.items()})
    leek_dx = -arm if drawing != "stand" else 0                 # leaves trail the arm by a pixel
    for y in range(LEEK_STALK_Y0, LEEK_STALK_Y1 + 1):
        pale = y >= 22
        cv.update({(LEEK_STALK_X, y + bob): "B", (LEEK_STALK_X + 1, y + bob): "b" if pale else "I",
                   (LEEK_STALK_X + 2, y + bob): "b" if pale else "X", (LEEK_STALK_X + 3, y + bob): "B"})
    paste(cv, LEEK_TOP, dy=bob, rows_shift=lambda j: (leek_dx if j < 3 else 0))
    paste(cv, LEEK_ROOT, dy=bob)
    paste(cv, LEEK_ARM, dy=bob)
    grid = [["."] * W for _ in range(H)]
    for (x, y), c in cv.items():
        if 0 <= x < W and 0 <= y < H:
            grid[y][x] = c
    shadow = p1()
    for y in (68, 69, 70):
        for x in range(W):
            if shadow[y][x] == "Z" and grid[y][x] == ".":
                grid[y][x] = "Z"
    rows = ["".join(r) for r in grid]
    hx = [x for (x, y) in head if 2 <= y <= 30]
    sx = [x for j, r in enumerate(SKIRT[2][:4]) for x, c in enumerate(r, SKIRT[0]) if c != "."]
    meta = {"view": "diagonal", "facing": "right", "drawing": drawing, "bob": bob,
            "head_cx": round(sum(hx) / len(hx), 2), "hip_cx": round(sum(sx) / len(sx), 2),
            "head_cols": [HEAD_X0 + 4, HEAD_X1 - 4]}
    return rows, meta


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    import sheet
    from PIL import Image
    pal = sheet.palette()
    names = [d for d in DRAW]
    ims = [sheet.img(pose(d, t)[0], pal, int(sys.argv[2]) if len(sys.argv) > 2 else 6)
           for t, d in enumerate(names)]
    out = Image.new("RGB", (sum(i.width + 8 for i in ims), ims[0].height), (236, 236, 236))
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + 8
    out.save(sys.argv[1])
    for d in names:
        print(d, pose(d)[1])
