"""Dev-only: the compact tier is the approved Miku at half size (37 x 36 px, 18 terminal rows),
so she looks the same at every size. Each approved drawing is rendered with even-pixel offsets
(q_walk even=True), reduced 2:1, then cleaned by hand-set rules:

- a 2x2 block keeps its most common colour; outline wins where a line crosses the block, so
  lines survive; it is transparent only when mostly empty;
- the outer silhouette is closed with outline;
- lone pixels (no same-colour neighbour, inside a solid area) take their surroundings' colour;
- the eyes are replaced with hand-drawn half-size eyes for each face (open, "^ ^", half-lidded,
  closed line), placed from the head's position.
"""

from __future__ import annotations

from collections import Counter

W, H, BASELINE = 37, 36, 33
KEEP = set("bIXSVUZ")      # small accents a fill vote must not wipe out


def half(rows):
    out = []
    for y in range(0, len(rows) - 1, 2):
        s = []
        for x in range(0, len(rows[0]) - 1, 2):
            px = [rows[y + j][x + i] for j in (0, 1) for i in (0, 1)]
            c = Counter(px)
            empty = c.pop(".", 0)
            if empty >= 3 or not c:
                s.append(".")
                continue
            b = c.get("B", 0) + c.get("O", 0)
            acc = [p for p in px if p in KEEP and p != "Z"]
            leek = [p for p in px if p in "bIX"]
            if len(leek) >= 2 or (leek and b <= 2 and empty == 0):
                s.append(Counter(leek).most_common(1)[0][0])   # the thin leek survives
            elif b >= 2 or (b == 1 and empty >= 1):
                s.append("B")
            elif acc and Counter(acc).most_common(1)[0][1] >= 2:
                s.append(Counter(acc).most_common(1)[0][0])
            else:
                c.pop("B", None)
                s.append(c.most_common(1)[0][0] if c else "B")
        out.append(s)
    return out


def close_outline(g):
    """A coloured pixel on the silhouette edge (touching transparency) becomes outline, except
    thin accents (leek, ground shadow) that would vanish."""
    h, w = len(g), len(g[0])
    edge = []
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c in ".BZ" or c in "bIX":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < w and 0 <= yy < h) or g[yy][xx] == ".":
                    edge.append((x, y))
                    break
    # only close where the outline is actually broken: a fill pixel touching transparency
    # whose diagonal neighbours outside are not already outline
    for x, y in edge:
        g[y][x] = "B"


def despeckle(g):
    h, w = len(g), len(g[0])
    src = [r[:] for r in g]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = src[y][x]
            if c in ".BZ" or c in KEEP:
                continue
            nb = [src[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if c in nb or "." in nb:
                continue
            m = Counter(n for n in nb if n != "B").most_common(1)
            if m and m[0][1] >= 3:
                g[y][x] = m[0][0]


# hand-drawn half-size eyes, placed at each eye's top-left; '.' is skin, ' ' keeps what's there.
# 3/4 view: the near eye is wide, the far eye narrower toward the far cheek.
EYES = {
    "open":       [["BBB", "FCG", "CAC"], ["BBB", "FCG", "CAC"]],      # front view
    "line_front": [["...", "BBB", "..."], ["...", "BBB", "..."]],
    "cheery":     [[".BBB.", "B...B"], [".B.", "B.B"]],
    "half":       [["BBBBB", ".FCF."], ["BBB", "FCF"]],
    "line":       [[".....", "BBBBB"], ["...", "BBB"]],
}
FRONT_EYES = [(13, 10), (21, 10)]
DIAG_EYES = [(14, 10), (22, 10)]         # with the head at its rest position


def put(g, x0, y0, rows):
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != " " and 0 <= y0 + j < len(g) and 0 <= x0 + i < len(g[0]):
                g[y0 + j][x0 + i] = "E" if c == "." else c


def eyes_for(meta):
    """(face, eye spots) for a full-size drawing's metadata."""
    if meta.get("view") == "front":
        return ("line_front" if meta.get("drawing") == "front_tired" else "open"), FRONT_EYES
    dx = (meta["head_cols"][0] - 26) // 2
    dy = (meta["bob"] + meta["head_dy"]) // 2
    return meta["face"], [(x + dx, y + dy) for x, y in DIAG_EYES]


# ---------------------------------------------------------------- hand-drawn half-size parts
# Halving keeps every 1 px line of the full drawing, so the torso, arms and leek turn into
# bars and mush. These parts are drawn by hand at half size instead (the full-size ones are
# left out before halving, q_walk skip=...). Coordinates are compact pixels with the body at
# rest (bob 0); ' ' is transparent. Each part gets a navy ring where it lies over something.

def paste_ring(g, x0, y0, rows, behind=False):
    cells = {}
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != " ":
                cells[(x0 + i, y0 + j)] = c
    h, w = len(g), len(g[0])
    ok = lambda x, y: 0 <= x < w and 0 <= y < h          # noqa: E731
    for (x, y), c in cells.items():
        if ok(x, y) and (not behind or g[y][x] in ".ACG"):
            g[y][x] = c
    for (x, y) in cells:
        if behind and not (ok(x, y) and g[y][x] == cells[(x, y)]):
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q in cells or not ok(*q) or q[1] > BASELINE:     # nothing below the soles
                continue
            cur = g[q[1]][q[0]]
            if cur not in "BZ" and (not behind or cur == "."):
                g[q[1]][q[0]] = "B"


FRONT_BODY = (11, 16, [          # front view, rows 16-33: jacket, tie, sleeves, skirt, legs
    "     BPPPB     ",
    "    BNLCLNB    ",
    "   BNLLALLNB   ",
    "  BDBNLALNBDB  ",
    "  BDBNLALNBDB  ",
    "  BDBKNANKBDB  ",
    " BDDBBDADBBDDB ",
    " BAABDDDDDBAAB ",
    "BEEBDKDDDKDBEEB",
    "BEEBDKDDDKDBEEB",
    " BBDKDDDDDKDBB ",
    " BAAAAAAAAAAAB ",
    "    BEB BEB    ",
    "    BEB BEB    ",
    "    BFB BFB    ",
    "    BFB BFB    ",
    "   BFFB BFFB   ",
    "   BBBB BBBB   ",
])
FRONT_LEEK = (1, 23, ["BIB        ",       # blades splay unevenly; white root at her hand
                      " BIIBBBBBBB",
                      "BXIIIbbbLLL",
                      "IIXBBBBBBBB",
                      "B  I       "])
FRONT_MOUTH = {"open": (17, 14, "SVS"), "line_front": (17, 14, "EBB")}

TORSO = (15, 16, ["   BPPB  ",
                  "  BNLCLB ",
                  " BNLLALB ",
                  " BNLLALNB",
                  " BKNLALNB",
                  "  BKNANB "])
TORSO_SLUMP = (15, 16, ["   BPPB  ",
                        "   BLCLB ",
                        " BNLLALB ",
                        " BNLLALNB",
                        " BKNLALNB",
                        "  BKNANB "])
NEAR_ARM = (11, 18, ["    DD",            # rows 2-3 (forearm) shift with the swing
                     "   DD ",
                     "  AA  ",
                     " EE   "])
LIMP_ARM = (14, 18, ["DD", "DD", "DD", "DD", "AA", "EE"])
LEEK_UP = (27, 0, ["I    I",
                   " I  I ",
                   "  IX  ",
                   "  IX  ",
                   "  IX  ",
                   "  IX  ",
                   "  IX  ",
                   "  IX  ",
                   "  IX  ",
                   "  bb  ",
                   "  bb  ",
                   "      ",
                   "      ",
                   "   L  "])
ARM_UP = (23, 11, ["      EE",
                   "      EE",
                   "     AA ",
                   "    DD  ",
                   "   DD   ",
                   "  DD    ",
                   "DDD     "])
ARM_MID = (22, 17, ["DDD     ",
                    "  DDAEE "])
LEEK_MID = (27, 11, ["  I  I",
                     "   IX ",
                     "   IX ",
                     "  IX  ",
                     "  Ib  ",
                     " bb   ",
                     "bb    "])
ARM_LOW = (23, 18, ["DD", "DD", "DD", "DD", "AA", "EE"])
LEEK_LOW = (13, 24, ["         bb",
                     "        bb ",
                     "       IX  ",
                     "      IX   ",
                     "     IX    ",
                     "    IX     ",
                     " I IX      ",
                     "IIIX       "])
DRAG_HAND = (11, 23, ["EE"])
DRAG_STALK = (8, 24, ["    bb",
                      "    bb",
                      "   bI ",
                      "   IX ",
                      "  IX  ",
                      "  IX  ",
                      " IX   ",
                      " IX   "])
DRAG_LEAVES = (3, 31, ["  II  ",
                       "IIXII ",
                       " I I  "])
MOUTH = {"cheery": "VS", "half": "SE", "line": "BB"}


def parts_front(g, drawing):
    x0, y0, rows = FRONT_BODY
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            g[y0 + j][x0 + i] = c if c != " " else "."
    for y in range(22, 31):                       # the old leek: back to the tail behind it
        for x in range(0, 12):
            if g[y][x] in "bIX":
                g[y][x] = "A"
    paste_ring(g, *FRONT_LEEK)
    x, y, m = FRONT_MOUTH["line_front" if drawing == "front_tired" else "open"]
    for i, c in enumerate(m):
        g[y][x + i] = c


def parts_diagonal(g, meta, arm, k):
    db = meta["bob"] // 2
    hx = (meta["head_cols"][0] - 26) // 2
    hy = (meta["bob"] + meta["head_dy"]) // 2
    u, leek = meta["u"], meta["leek"]
    sh = lambda part, dy=db: (part[0], part[1] + dy, part[2])        # noqa: E731
    if leek == "low":
        paste_ring(g, *sh(LEEK_LOW), behind=True)
    if leek == "drag":
        x0, y0, rows = DRAG_LEAVES
        paste_ring(g, x0, y0, rows)
        paste_ring(g, *sh(DRAG_STALK))
    paste_ring(g, *sh(TORSO_SLUMP if u >= 0.6 else TORSO))
    if u < 0.5:
        x0, y0, rows = NEAR_ARM
        rows = rows[:2] + [(" " + r[:-1]) if arm > 0 else (r[1:] + " ") if arm < 0 else r
                           for r in rows[2:]]
        paste_ring(g, x0, y0 + db, rows)
    else:
        paste_ring(g, *sh(LIMP_ARM))
    if leek == "drag":
        paste_ring(g, *sh(DRAG_HAND))
    elif leek == "low":
        paste_ring(g, *sh(ARM_LOW))
    elif leek == "mid":
        paste_ring(g, *sh(LEEK_MID))
        paste_ring(g, *sh(ARM_MID))
    elif leek == "up":
        x0, y0, rows = LEEK_UP
        paste_ring(g, x0 - arm, y0 + db, rows[:2])               # the leaves trail the arm
        paste_ring(g, x0, y0 + 2 + db, rows[2:])
        paste_ring(g, *sh(ARM_UP))
    m = MOUTH.get(meta["face"], "BB")
    for i, c in enumerate(m):
        g[14 + hy][20 + hx + i] = c


def compact(full_rows, eyes=None, meta=None, arm=0, k=0):
    """eyes = (face, [(x, y) of each eye's top-left in compact pixels]) or None. With `meta`,
    the hand-drawn half-size body parts go on top (front or 3/4)."""
    g = half(full_rows)
    despeckle(g)
    close_outline(g)
    if eyes:
        face, spots = eyes
        for (x, y), rows in zip(spots, EYES[face]):
            put(g, x, y, rows)
    if meta is not None:
        if meta.get("view") == "front":
            parts_front(g, meta.get("drawing"))
        else:
            parts_diagonal(g, meta, arm, k)
    return ["".join(r) for r in g]


SKIP = ("leek", "arm", "torso")


def drawing(d, t=0, period=12, u=0.0, hem=None, k=0):
    """One compact drawing (rows, full-size meta)."""
    import q_walk

    if d == "front":
        rows, meta = q_walk.p1(), {"view": "front", "facing": "front", "drawing": d}
        return compact(rows, eyes_for(meta), meta), meta
    if d == "front_tired":
        rows, meta = q_walk.tired_front(), {"view": "front", "facing": "front", "drawing": d}
        return compact(rows, eyes_for(meta), meta), meta
    rows, meta = q_walk.pose(d, t, period, u=u, hem=hem, k=k, even=True, skip=SKIP)
    table = q_walk.TIRED_DRAW if u >= 0.5 else q_walk.DRAW
    return compact(rows, eyes_for(meta), meta, arm=table[d][6], k=k), meta


def clip_frames(name):
    """A compact clip from the same exposure sheet and drawings as the full one."""
    import q_walk
    import xsheet

    xs = xsheet.load(name)
    order = [f["drawing"] for f in xs["frames"]]
    out, t = [], 0
    for k, f in enumerate(xs["frames"]):
        d, u = f["drawing"], f.get("u", 0.0)
        if d.startswith("front") or d.startswith("stand"):
            small, meta = drawing(d, u=u)
        else:
            hem = q_walk.hem_for(order, k, 1 if u < 0.5 else 2)
            small, meta = drawing(d, t, xs["ticks"], u=u, hem=hem, k=k)
        meta = dict(meta, tier="compact")
        if "hem_outline" in meta:
            meta["hem_outline"] = [[x // 2, y // 2] for x, y in meta["hem_outline"]]
        out.append({"drawing": d, "ticks": f["ticks"], "key": f.get("key", False),
                    "grid": small, "anchors": meta})
        t += f["ticks"]
    return xs, out
