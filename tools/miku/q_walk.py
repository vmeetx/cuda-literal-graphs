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


def face_edits(src, face="cheery"):
    """Faces drawn on P1 before the turn. cheery: closed happy "^ ^" eyes, blush, open smile
    (approved). half: lids half down over a sliver of iris, small smile (transition).
    line: closed horizontal line eyes with a drooping outer lash, small tired open mouth."""
    g = [list(r) for r in src]
    for y in range(20, 27):                       # clear the open eyes to skin
        for x in list(range(27, 33)) + list(range(40, 47)):
            if g[y][x] not in "EP" and not (y == 20 and x in (27, 46)):
                g[y][x] = "E"
    for x in range(34, 39):                       # clear the small mouth
        for y in (29, 30):
            g[y][x] = "E"
    if face == "cheery":
        for cx in (30, 43):                       # ^ ^ closed eyes, lash flick at the outer corner
            for x in (cx - 1, cx, cx + 1):
                g[22][x] = "B"
            g[23][cx - 2] = "B"
            g[23][cx + 2] = "B"
        g[22][27] = "B"                           # outer lash (near eye)
        for x in (28, 29, 30):
            g[25][x] = "U"
        for x in (43, 44, 45):
            g[25][x] = "U"
        for x, c in zip(range(35, 40), "BBBBB"):  # open D-shaped smile
            g[28][x] = c
        for x, c in zip(range(35, 40), "BVVVB"):
            g[29][x] = c
        for x, c in zip(range(36, 39), "BUB"):
            g[30][x] = c
        return ["".join(r) for r in g]
    if face == "half":
        for cx in (30, 43):                       # heavy lid over a sliver of iris
            for x in range(cx - 2, cx + 3):
                g[22][x] = "B"
            for x in range(cx - 1, cx + 2):
                g[23][x] = "D"
            g[23][cx - 2] = g[23][cx + 2] = "B"
        for x in (28, 29):
            g[25][x] = "U"
        for x in (43, 44):
            g[25][x] = "U"
        for x in (36, 37, 38):                    # small smile
            g[29][x] = "B"
        g[30][37] = "U"
        return ["".join(r) for r in g]
    for cx, outer in ((30, -3), (43, 3)):         # line eyes, outer lash drooping
        for x in range(cx - 2, cx + 3):
            g[23][x] = "B"
        g[24][cx + outer] = "B"
    for x in (29, 30):
        g[25][x] = "U"
    for x in (43, 44):
        g[25][x] = "U"
    g[30][36] = "B"                               # flat, tired mouth
    g[30][37] = "B"
    return ["".join(r) for r in g]


def tired_front():
    """P1 for a tired rest and the tired turns: line eyes and a flat mouth (the leek already
    hangs low toward the ground in P1)."""
    return face_edits(p1(), "line")


def turned_head(face="cheery"):
    src = face_edits(p1(), face)
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

LEEK_ARM = (44, 26, [   # her left arm: upper arm out from the shoulder, elbow bend, forearm
    "................BBBB.",   # rising ~45 deg; detached sleeve tapers 5 -> 3 px to the cuff,
    "...............BEEEEB",   # then a small fist around the stalk
    "..............BAEEEEB",
    ".............BAABBBB.",
    "............BDDAB....",
    "...........BDDDMB....",
    "..........BDDDMB.....",
    ".........BDDDDMB.....",
    "........BDDDDMB......",
    ".....BBBDDDDMB.......",
    "...BBEEEBDDMB........",
    "BBBEEEEEBBB..........",
    "BEEEBBB..............",
    "..BB.................",
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
LEEK_STALK_X, LEEK_STALK_Y0, LEEK_STALK_Y1 = 60, 8, 29
LEEK_ROOT = (60, 30, ["BLLB", "BLLB", ".BB."])

# ---------------------------------------------------------------- skirt: waist + hem wave states
# The waist (rows 45-47) moves with the body. Below it the skirt is built from a hem STATE: the
# hem edge columns and a hand-drawn offset per column (how far each bit of the trim hangs below
# or above the rest line, row 52). States are keyframes of one travelling wave, all asymmetric
# (trailing side = left, behind her): the walk picks one by step phase, 1-2 drawings behind the
# hips, so the hem moves last. Rows between waist and hem ease from the waist edges to the hem
# edges (t^1.4: the wave travels down). Pleat lines bend toward the hem; the cyan trim follows
# the hem curve. At rest the skirt is the approved width (fill 28-49); flare only widens it.
WAIST = {45: (34, "BBBBBBBBBB"), 46: (33, "BDDDDKDDDDDB"), 47: (32, "BDDDDDKDDDDDMB")}
HEM_BASE = 52
OFF = {"b": -2, "a": -1, "0": 0, "1": 1, "2": 2}
HEM = {   # name: (first fill col, last fill col, per-column offset, pleat bend at the hem)
    "rest": (28, 49, "0001000010000100001000", 0),
    "S0": (26, 49, "aaa1" "00010000" "10010110" "2110", -1),    # contact: drops over the front leg
    "S1": (25, 50, "baaa" "a0010010" "01001010" "111100", -2),  # down: flares out behind
    "S2": (27, 49, "aa00" "01000010" "00010000" "011", -1),     # pass: swinging back to centre
    "S3": (28, 50, "0a00" "10000100" "00100001" "a0a", 0),      # up: settling, front flicks out
}
PHASE_STATE = {"contact": "S0", "down": "S1", "pass": "S2", "up": "S3"}
PLEATS = [(37, 35), (41, 41), (44, 45)]          # (x at row 48, x at the hem at rest)
for _n, (_l, _r, _s, _b) in HEM.items():
    assert len(_s) == _r - _l + 1, _n


def hem_for(order, k, lag):
    """The hem state shown at drawing k of a clip: the state of drawing k - lag (it trails)."""
    d = order[(k - lag) % len(order)]
    return PHASE_STATE.get(d.split("_")[0], "rest")


def _round(v):
    return int(math.floor(v + 0.5)) if v >= 0 else -int(math.floor(-v + 0.5))


def skirt(cv, state="rest", amp=1.0, sway=0, bob=0):
    """Paint the skirt; return its hem outline points (for the straight-run lint)."""
    hl, hr, offs, bend = HEM[state]
    hl2, hr2 = 28 + _round((hl - 28) * amp), 49 + _round((hr - 49) * amp)
    hl2, hr2 = hl2 + min(sway, 0), hr2 + max(sway, 0)    # sway flares that side out, never shifts
    span = [OFF[ch] for ch in offs]

    def off(x):
        if not hl2 <= x <= hr2:
            return 0
        i = round((x - hl2) / max(hr2 - hl2, 1) * (len(span) - 1))
        v = span[i]                                   # pleat tips always hang (>= 1 px);
        return max(1, _round(v * amp)) if v > 0 else _round(v * amp)   # only the swing scales

    def yt_hi(x):                                     # trim steps, never breaks: a dipped
        return min(HEM_BASE + off(x - 1), HEM_BASE + off(x + 1), HEM_BASE + off(x))   # column joins up

    layer = {}
    for y, (x0, row) in WAIST.items():
        for i, ch in enumerate(row):
            layer[(x0 + i, y)] = ch
    for y in range(48, HEM_BASE + 3):
        t = min(1.0, (y - 47) / (HEM_BASE - 47))
        e = t ** 1.4
        L, R = round(33 + (hl2 - 33) * e), round(44 + (hr2 - 44) * e)
        lifted = [x for x in range(hl2, hr2 + 1) if HEM_BASE + off(x) <= y]   # a lifted trim
        if lifted:                                          # reaches this row: the side follows it
            L, R = min(L, min(lifted)), max(R, max(lifted))
        for x in range(L, R + 1):
            yt = HEM_BASE + off(x)
            if y < yt:
                ch = "M" if x >= R - 1 else "D"
                for top, end in PLEATS:
                    end2 = end + _round(bend * amp)
                    sv = max(0.0, min(1.0, (y - 48) / max(yt - 49, 1)))
                    if round(top + (end2 - top) * sv ** 1.6) == x:
                        ch = "K"
            elif y == yt or (yt_hi(x) <= y < yt):
                ch = "C" if x >= R - 2 else "A"
            else:
                continue
            layer[(x, y)] = ch
    outline = []
    for (x, y), ch in list(layer.items()):
        if ch == "B":
            continue
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ddx, y + ddy)
            if q not in layer:
                layer[q] = "B"
                if ddy == 1:
                    outline.append(q)
    for (x, y), ch in layer.items():
        cv[(x, y + bob)] = ch
    return sorted((x, y + bob) for x, y in outline)


def straight_runs(points, limit=5):
    """Lint: horizontal runs longer than `limit` px on a hem outline (list of (x, y))."""
    ys = {}
    for x, y in points:
        ys[x] = max(y, ys.get(x, y))
    xs = sorted(ys)
    runs, start = [], 0
    for i in range(1, len(xs) + 1):
        if i == len(xs) or xs[i] != xs[i - 1] + 1 or ys[xs[i]] != ys[xs[i - 1]]:
            if i - start > limit:
                runs.append((xs[start], ys[xs[start]], i - start))
            start = i
    return runs


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
    "f2": (2, [  # tired: short shuffle forward, foot 2 px ahead
        "..BEEEB....", "..BEEEB....", "..BEEEB....", "...BFFFB...", "...BFFFB...",
        "...BFFFB...", "...BFFFB...", "....BFFFB..", "....BFFFB..", ".....BFFFB.",
        ".....BFFFB.", ".....BFFFFB", ".....BFFFFB", ".....BBBBBB"]),
    "k2": (3, [  # tired: just behind, foot flat (dragging, no toe-off)
        "...BEEEB...", "...BEEEB...", "...BEEEB...", "..BFFFB....", "..BFFFB....",
        "..BFFFB....", "..BFFFB....", ".BFFFB.....", ".BFFFB.....", "BFFFB......",
        "BFFFB......", "BFFFFB.....", "BFFFFB.....", "BBBBBB....."]),
    "k2h": (3, [  # tired: trailing foot peeling off, heel up 1 px
        "...BEEEB...", "...BEEEB...", "...BEEEB...", "..BFFFB....", "..BFFFB....",
        "..BFFFB....", "..BFFFB....", ".BFFFB.....", ".BFFFB.....", ".BFFFB.....",
        ".BFFFB.....", "BFFFFB.....", ".BFFFB.....", "..BBB......"]),
    "u2": (2, [  # tired: swinging foot just ahead, 1 px off the ground
        "..BEEEB....", "..BEEEB....", "..BEEEB....", "...BFFFB...", "...BFFFB...",
        "...BFFFB...", "...BFFFB...", "...BFFFB...", "...BFFFB...", "...BFFFB...",
        "...BFFFFB..", "...BFFFFB..", "...BBBBBB..", "..........."]),
    "p2": (2, [  # tired passing: the foot barely lifts (1 px), knee hardly forward
        "..BEEEB....", "..BEEEB....", "..BEEEB....", "..BFFFB....", "...BFFFB...",
        "...BFFFB...", "...BFFFB...", "...BFFFB...", "...BFFFB...", "...BFFFB...",
        "...BFFFFB..", "...BFFFFB..", "...BBBBBB..", "..........."]),
    "P": (2, [  # passing: knee forward, foot off the ground
        "..BEEEB....", "..BEEEB....", "..BEEEEB...", "...BEEEEB..", "....BFFFFB.",
        "....BFFFFB.", "....BFFFB..", "...BFFFB...", "..BFFFB....", "..BFFFFB...",
        "..BFFFFFB..", "..BBBBBBB.."]),
}
FAR_LEG = {"E": "P", "F": "Y"}                   # far leg: thigh in skin shade, far-side slate sock
HIP_X = {"near": 35, "far": 40}                  # first fill column of each hip

# drawing: (near-leg shape, far-leg shape, near grounded?, far grounded?, bob, hem sway,
#           back-arm swing)
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
    "stand_go":  ("S", "S", True, True, 0, 0, 0),
    "stand_settle": ("S", "S", True, True, 0, 0, 0),
}
TIRED_DRAW = {   # short shuffling steps, bob 0-1 px, no arm swing
    "contact_r": ("k2", "f2", True, True, 0, 0, 0),
    "down_r":    ("k2h", "S", True, True, 1, 0, 0),
    "pass_r":    ("p2", "S", False, True, 0, 0, 0),
    "up_r":      ("u2", "S", False, True, 0, 0, 0),
    "contact_l": ("f2", "k2", True, True, 0, 0, 0),
    "down_l":    ("S", "k2h", True, True, 1, 0, 0),
    "pass_l":    ("S", "p2", True, False, 0, 0, 0),
    "up_l":      ("S", "u2", True, False, 0, 0, 0),
    "stand":     ("S", "S", True, True, 0, 0, 0),
    "stand_go":  ("S", "S", True, True, 0, 0, 0),
    "stand_settle": ("S", "S", True, True, 0, 0, 0),
}
STAND_HEM = {"stand": ("rest", 1.0), "stand_go": ("S1", 0.6), "stand_settle": ("S2", 0.6)}

# ---------------------------------------------------------------- tired parts
TORSO_SLUMP = (32, 33, [   # rounded shoulders: collar lower, back bulging out behind (left)
    "................",
    "....BBLBBLBB....",
    "..BBLLLBAABNB...",
    ".BLLLLLBAABNNB..",
    ".BLLLLLLBACBNB..",
    "..BLLLLLBAACNB..",
    "..BNLLLLBAACNB..",
    "..BNLLLLLBACNB..",
    "..BNNLLLLBAKNB..",
    "...BNLLLLBACKB..",
    "...BNNLLLLBKKB..",
    "...BKNNNNNBKKB..",
])
LIMP_ARM = (29, 35, [      # near arm hanging limp in front: skin, sleeve tapering to the cuff, small
    "...BBB",                 # hand hanging below the waist, clear of the dark skirt
    "..BEEB",
    "..BEEB",
    "..BEEB",
    "..BEEB",
    ".BDDDB",
    ".BDDDB",
    ".BDDMB",
    ".BDDMB",
    ".BDDMB",
    ".BDDMB",
    ".BDDMB",
    ".BAAAB",
    ".BEEEB",
    ".BEEPB",
    "..BEB.",
    "...B..",
])
FAR_DRAG_HAND = [          # far arm reaching back behind her: shadow sleeve, teal cuff, shaded hand
    "...BMMB",
    "..BMMB.",
    "..BMMB.",
    "..BCCB.",
    "..BPPB.",
    "..BPPB.",
    "...BB..",
]
MID_ARM = (44, 33, [       # lowering, 1: arm out level, fist forward, leek tipping forward
    "............BBBB",
    "..........BBAEEB",
    "......BBBBDDAEEB",
    "...BBBEEDDDMABB.",
    "BBBEEEEBDDMMB...",
    "BEEEBBBBBBB.....",
    "..BB............",
])
LOW_ARM = (43, 35, [       # lowering, 2: arm hanging at her far side, leek pointing down and back
    "..BBB.",
    ".BEEEB",
    ".BEEB.",
    ".BEEB.",
    ".BDDDB",
    ".BDDMB",
    ".BDDMB",
    ".BDDMB",
    ".BAACB",
    "..BEEB",
    "..BEEB",
    "...BB.",
])
DRAG_LEAVES = [            # three blades scraping along the ground behind her, gaps between
    "..B.....B.......",
    ".BbB...BbB......",
    "..BIB..BIB...BB.",
    "...BIB.BXIB.BIIB",
    "BB..BIBBXIBBIXB.",
    "BIBBBIIBXIIIXBbb",
    ".BBBBBBBBBBBBBBB",
]
DRAG_LEAVES_2 = [          # scrape state 2: blades bent back a pixel
    ".B......B.......",
    "BbB....BbB......",
    ".BIB...BIB....B.",
    "..BIB..BXIB..BIB",
    "B..BIB.BXIBBBIB.",
    "BIBBBIIBXIIIXBbb",
    ".BBBBBBBBBBBBBBB",
]
TIRED_OPTS = {   # thumbnails for the tired contact key: head droop, leek drag geometry
    "A": dict(hdx=1, hdy=3, hand=(23, 44), stalk=((26, 50), (19, 64)), leaves=4,
              note="slouch: head 1 forward, 3 down; long drag, leaves well behind"),
    "B": dict(hdx=2, hdy=3, hand=(25, 46), stalk=((28, 52), (23, 64)), leaves=8,
              note="heavy droop: head 2 forward, 3 down; short drag, leaves close"),
    "C": dict(hdx=1, hdy=1, hand=(21, 42), stalk=((24, 48), (15, 64)), leaves=0,
              note="trudge: head 1 forward, 1 down; arm stretched back, leaves far behind"),
}
TIRED_PICK = "A"


def stalk(cv, a, b, bob, behind=False):
    """A leek stalk (a prop) from a to b: 2 px pale green with outline; with `behind`, drawn
    only into empty cells so it stays behind what is already there."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n) + bob
        f = i / n
        body = ("L", "L", "N") if f < 0.3 else ("b", "b", "I") if f < 0.45 else ("I", "I", "X")
        for dx, ch in ((-1, "B"), (0, body[0]), (1, body[1]), (2, body[2]), (3, "B")):
            if not behind or (x + dx, y) not in cv:
                cv[(x + dx, y)] = ch


def leek_stage(u):
    return "up" if u < 0.25 else "mid" if u < 0.45 else "low" if u < 0.7 else "drag"


def face_stage(u):
    return "cheery" if u < 0.25 else "half" if u < 0.7 else "line"


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
        while rows and not rows[-1].strip("."):
            rows = rows[:-1]
        rows = fit(rows, BASELINE - top + 1)
    else:
        rows = fit(rows, len(rows) - 1) if bob < 0 else rows
    paste(cv, (HIP_X[side] - hip - 1, top, rows), recolor=FAR_LEG if side == "far" else None)


def pose(drawing="contact_r", t=0, period=12, u=0.0, hem=None, opt=None, k=0):
    """One drawing. u = tiredness (0 cheerful, 1 tired); hem = the (lagged) hem state; opt =
    tired thumbnail option; k = drawing index (the dragged leaves scrape)."""
    tired_legs = u >= 0.5
    table = TIRED_DRAW if tired_legs else DRAW
    near, far, ng, fg, bob, sway_, arm = table[drawing]
    if not tired_legs and u >= 0.3 and bob < 0:
        bob = 0                                               # the up-bounce dies first
    o = TIRED_OPTS[opt or TIRED_PICK]
    hdx = round(o["hdx"] * min(1.0, u / 0.8))
    hdy = round(o["hdy"] * min(1.0, u / 0.8))
    if tired_legs and drawing.startswith("down"):
        hdy -= 1                                              # dip in the body only, not the head
    leek = leek_stage(u)
    face = face_stage(u)
    cv = {}
    left, right = tail_cells()
    phase = math.sin(4 * math.pi * (t - 1) / period)          # two flares per cycle, 1 tick behind the bob
    tamp = 1.0 - 0.75 * u                                     # tired: tails hang heavy, little sway
    far_tail = {kk: FAR_HAIR.get(v, v) for kk, v in
                sway(right, (0.5 + 1.8 * phase) * tamp, -3 - round(u)).items()}
    cv.update({(x + hdx, y + bob + hdy): c for (x, y), c in far_tail.items()})
    near_cells = sway(left, (-0.5 - 2.2 * phase) * tamp, 3 + round(u))
    cv.update({(x + hdx, y + bob + hdy): c for (x, y), c in near_cells.items()})
    if leek == "drag":   # far hand reaching back past the near tail, the leek trailing on the ground
        paste(cv, (o["leaves"] + (k % 2), 61, DRAG_LEAVES_2 if k % 2 else DRAG_LEAVES))   # scraping
        stalk(cv, o["stalk"][0], o["stalk"][1], bob)
        paste(cv, (o["hand"][0], o["hand"][1], FAR_DRAG_HAND), dy=bob)
    if u < 0.5:
        paste(cv, BACK_ARM, dy=bob, rows_shift=lambda j: (arm if j >= 5 else 0))
    if leek == "low":                                         # behind the legs and skirt
        stalk(cv, (46, 47), (33, 63), bob)
        paste(cv, (24, 61, DRAG_LEAVES))
    leg(cv, far, "far", bob, fg)
    leg(cv, near, "near", bob, ng)
    if drawing in STAND_HEM:
        state, hamp = STAND_HEM[drawing]
        hamp *= 1.0 - 0.5 * u
    else:
        state, hamp = (hem or PHASE_STATE[drawing.split("_")[0]]), 1.0 - 0.5 * u
    hem_line = skirt(cv, state, hamp, _round(sway_ * (1.0 - u)), bob)
    paste(cv, TORSO_SLUMP if u >= 0.6 else TORSO, dy=bob)
    if u >= 0.5:
        paste(cv, LIMP_ARM, dy=bob)
    head = turned_head(face)
    cv.update({(x + hdx, y + bob + hdy): c for (x, y), c in head.items()})
    if leek == "up":
        leek_dx = -arm if not drawing.startswith("stand") else 0   # leaves trail the arm by a pixel
        for y in range(LEEK_STALK_Y0, LEEK_STALK_Y1 + 1):
            pale = y >= 20
            cv.update({(LEEK_STALK_X, y + bob): "B", (LEEK_STALK_X + 1, y + bob): "b" if pale else "I",
                       (LEEK_STALK_X + 2, y + bob): "b" if pale else "X", (LEEK_STALK_X + 3, y + bob): "B"})
        paste(cv, LEEK_TOP, dy=bob, rows_shift=lambda j: (leek_dx if j < 3 else 0))
        paste(cv, LEEK_ROOT, dy=bob)
        paste(cv, LEEK_ARM, dy=bob)
    elif leek == "mid":
        stalk(cv, (57, 37), (55, 40), bob)                    # root end, below the fist
        stalk(cv, (58, 33), (66, 23), bob)                    # tipping forward
        paste(cv, (62, 18, LEEK_TOP[2][:5]), dy=bob)
        paste(cv, MID_ARM, dy=bob)
    elif leek == "low":
        paste(cv, LOW_ARM, dy=bob)
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
    hx = [x + hdx for (x, y) in head if 2 <= y <= 30]
    sx = [x0 + i for y, (x0, row) in WAIST.items() for i, ch in enumerate(row) if ch != "."]
    meta = {"view": "diagonal", "facing": "right", "drawing": drawing, "bob": bob,
            "u": round(u, 2), "face": face, "leek": leek, "hem": state,
            "head_cx": round(sum(hx) / len(hx), 2), "hip_cx": round(sum(sx) / len(sx), 2),
            "head_cols": [HEAD_X0 + 4 + hdx, HEAD_X1 - 4 + hdx], "head_dy": hdy,
            "hem_outline": [list(q) for q in hem_line]}
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
